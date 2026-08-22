import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

MAX_API_SIZE_MB = 24  # margem de segurança abaixo do limite de 25MB da OpenAI

# whisperx exige Python >=3.10,<3.14 (torch não publica wheels cp314), e o
# venv deste projeto roda 3.14+. Por isso o engine whisperx é executado num
# subprocess com ambiente efêmero do uv (cacheado após a primeira resolução),
# nunca importado neste processo.
WHISPERX_PYTHON = "3.12"
WHISPERX_SPEC = "whisperx>=3.8,<4"


# Parâmetros anti-alucinação para mlx_whisper.transcribe.
#
# Whisper, em trechos silenciosos/musicais, costuma "preencher" com frases muito
# frequentes no treino (ex.: "Legenda Adriana Zanotto" em datasets pt-br de
# legendas, "Thanks for watching" em en, "♪♪♪" em música). Os defaults da
# openai-whisper não filtram essas alucinações de forma confiável.
#
# - `condition_on_previous_text=False`: cada janela de 30s decodifica de zero,
#   sem ver o texto da anterior. Evita que uma alucinação puxe a próxima (loop
#   em cadeia repetindo a mesma frase por minutos).
# - `no_speech_threshold=0.4` (default 0.6): janela é marcada como silêncio
#   quando `no_speech_prob > 0.4` (mais agressivo → mais janelas silenciosas
#   detectadas).
# - `logprob_threshold=-0.5` (default −1.0): se a decodificação tem
#   `avg_logprob < −0.5` (baixa confiança), a janela é descartada mesmo que o
#   `no_speech_prob` esteja alto. Pega alucinações "confiantes" em silêncio.
#
# Trade-off: pode descartar fala genuína muito baixinha. Pra gravações de
# reunião com fala clara isso é aceitável; pra áudio sussurrado pode dropar
# falsos positivos.
_ANTI_HALLUCINATION_KWARGS = {
    "condition_on_previous_text": False,
    "no_speech_threshold": 0.4,
    "logprob_threshold": -0.5,
}


def _check_mlx_whisper() -> bool:
    try:
        import mlx_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def _file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def _normalize_mlx_model_dir(model_dir: Path) -> None:
    """Garante que o diretório de modelo MLX tenha um arquivo de pesos com o
    nome esperado pelo `mlx_whisper.load_models.load_model`
    (`weights.safetensors` ou `weights.npz`).

    Versões recentes do `convert.py` (mlx-examples) salvam os pesos como
    `model.safetensors`. Quando só existe esse arquivo, criamos um symlink
    relativo `weights.safetensors -> model.safetensors` pra evitar renomeação
    manual a cada modelo convertido.
    """
    if (model_dir / "weights.safetensors").exists() or (model_dir / "weights.npz").exists():
        return
    legacy = model_dir / "model.safetensors"
    if legacy.exists():
        try:
            (model_dir / "weights.safetensors").symlink_to(legacy.name)
        except FileExistsError:
            pass


def _resolve_mlx_repo(model: str) -> str:
    """Resolve `model` (nome curto ou caminho local) para o argumento
    `path_or_hf_repo` esperado pelo mlx-whisper."""
    model_dir = Path(model).expanduser()
    if model_dir.is_dir():
        _normalize_mlx_model_dir(model_dir)
        return str(model_dir)
    return f"mlx-community/whisper-{model}-mlx"


def _transcribe_local(
    audio_path: Path,
    model: str,
    language: str | None = None,
    multilang: bool = False,
    word_timestamps: bool = False,
) -> dict:
    """Single-pass: detecta (ou força) um idioma e transcreve a chamada inteira
    nele. Se `multilang=True`, despacha para a versão chunked que re-detecta o
    idioma por janela (útil para reuniões com troca de PT/EN/ES no meio).
    """
    if multilang:
        return _transcribe_local_chunked(
            audio_path, model, word_timestamps=word_timestamps
        )

    import mlx_whisper

    # `model` pode ser um nome curto (ex: 'medium', 'large-v3') OU um caminho
    # para um diretório local de modelo MLX já convertido (config.json +
    # weights.{safetensors,npz}). Útil em redes que bloqueiam o Hugging Face.
    path_or_hf_repo = _resolve_mlx_repo(model)

    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=path_or_hf_repo,
        verbose=True,
        # `language=None` deixa o Whisper detectar o idioma nos primeiros 30s.
        # Passar "pt"/"en"/"es" força e melhora qualidade quando você sabe.
        language=language,
        # Com word_timestamps=True o mlx grava segments[i]["words"] e reajusta
        # o start/end de cada segment pros bounds da primeira/última word.
        word_timestamps=word_timestamps,
        **_ANTI_HALLUCINATION_KWARGS,
    )
    return result


def _format_chunk_time(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _transcribe_local_chunked(
    audio_path: Path,
    model: str,
    chunk_seconds: int = 30,
    word_timestamps: bool = False,
) -> dict:
    """Transcrição com detecção de idioma **por janela** (não trava o idioma na
    chamada inteira). Quebra o áudio em janelas de `chunk_seconds` (default 30s,
    mesmo tamanho da janela interna do Whisper), roda transcribe em cada uma com
    `language=None` (forçando re-detecção) e concatena os `segments` com offsets
    corretos.

    Cada segmento retornado ganha um campo `language` (código ISO-639-1) que o
    formatter usa para anotar `[pt]/[en]/[es]` no `raw_timestamps.md`. O campo
    top-level `language` retorna o idioma **dominante** por duração agregada.
    """
    import mlx_whisper
    from mlx_whisper import audio as mlx_audio

    SAMPLE_RATE = 16000  # mlx_whisper.audio.SAMPLE_RATE
    audio = mlx_audio.load_audio(str(audio_path))
    total_samples = len(audio)
    if total_samples == 0:
        return {"text": "", "segments": [], "language": None}

    chunk_samples = chunk_seconds * SAMPLE_RATE
    chunks_total = (total_samples + chunk_samples - 1) // chunk_samples
    path_or_hf_repo = _resolve_mlx_repo(model)

    all_segments: list[dict] = []
    text_parts: list[str] = []
    duration_per_lang: dict[str, float] = {}

    print(f"  [multilang] {chunks_total} janelas de {chunk_seconds}s")
    for idx, start in enumerate(range(0, total_samples, chunk_samples)):
        end = min(start + chunk_samples, total_samples)
        chunk = audio[start:end]
        offset = start / SAMPLE_RATE
        chunk_dur = (end - start) / SAMPLE_RATE

        result = mlx_whisper.transcribe(
            chunk,
            path_or_hf_repo=path_or_hf_repo,
            verbose=False,  # ruidoso demais com N janelas; usamos nossa progress line
            language=None,  # re-detecta por janela — esse é o ponto do modo multilang
            word_timestamps=word_timestamps,
            **_ANTI_HALLUCINATION_KWARGS,
        )

        lang = result.get("language")
        print(
            f"    [{idx + 1:>{len(str(chunks_total))}}/{chunks_total}] "
            f"{_format_chunk_time(offset)}-{_format_chunk_time(end / SAMPLE_RATE)}  "
            f"lang={lang or '?'}"
        )

        duration_per_lang[lang or ""] = duration_per_lang.get(lang or "", 0.0) + chunk_dur

        for seg in result.get("segments", []):
            seg_out = dict(seg)
            seg_out["start"] = seg.get("start", 0.0) + offset
            seg_out["end"] = seg.get("end", 0.0) + offset
            if seg.get("words"):
                # words vêm relativas ao chunk — soma o offset copiando cada
                # word (dict(seg) é shallow; mutar aqui contaminaria o original)
                seg_out["words"] = [
                    {**w, "start": w["start"] + offset, "end": w["end"] + offset}
                    for w in seg["words"]
                ]
            if lang:
                seg_out["language"] = lang
            all_segments.append(seg_out)

        chunk_text = (result.get("text") or "").strip()
        if chunk_text:
            text_parts.append(chunk_text)

    # idioma dominante = maior duração agregada
    dominant = None
    if duration_per_lang:
        dominant = max(
            (lang for lang in duration_per_lang if lang),
            key=lambda l: duration_per_lang[l],
            default=None,
        )

    return {
        "text": " ".join(text_parts).strip(),
        "segments": all_segments,
        "language": dominant,
    }


def _transcribe_whisperx(
    audio_path: Path,
    model: str = "large-v3-turbo",
    language: str | None = None,
    word_timestamps: bool = False,
) -> dict:
    """Transcreve via WhisperX (faster-whisper/CTranslate2 + VAD pyannote) num
    subprocess isolado — ver comentário em WHISPERX_PYTHON e o docstring de
    `whisperx_worker.py`. O worker herda stdout/stderr pra mostrar progresso;
    o resultado volta por arquivo JSON temporário (evita poluição de stdout).

    Primeira execução resolve o ambiente e baixa o modelo do Hugging Face
    (cacheados pelo uv e pelo HF nas execuções seguintes).
    """
    uv = shutil.which("uv")
    if uv is None:
        raise EnvironmentError(
            "uv não encontrado no PATH — o engine whisperx roda via "
            "`uv run --with whisperx`. Instale o uv ou use o engine mlx/--api."
        )
    worker = Path(__file__).with_name("whisperx_worker.py")

    with tempfile.TemporaryDirectory() as tmp:
        out_json = Path(tmp) / "result.json"
        cmd = [
            uv, "run", "--quiet", "--no-project",
            "--python", WHISPERX_PYTHON,
            "--with", WHISPERX_SPEC,
            str(worker),
            str(audio_path),
            "--output", str(out_json),
            "--model", model,
        ]
        if language:
            cmd += ["--language", language]
        if word_timestamps:
            cmd += ["--word-timestamps"]

        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            raise RuntimeError(
                f"whisperx worker falhou (exit {proc.returncode}) — "
                "ver mensagens acima."
            )
        return json.loads(out_json.read_text(encoding="utf-8"))


def _distribute_api_words(result: dict) -> None:
    """Distribui a lista top-level `words` da API (verbose_json com
    granularidade word) para dentro de cada segment, casando por janela de
    tempo (word.start < seg.end; o último segment recebe o resto). Remove a
    chave top-level após distribuir, normalizando pro mesmo shape do mlx
    (`segments[i]["words"]`). Se `segments` ou `words` vierem vazios/ausentes,
    não faz nada (mantém o fallback top-level). In-place.
    """
    words = result.get("words")
    segments = result.get("segments")
    if not words or not segments:
        return
    wi, n = 0, len(words)
    last = len(segments) - 1
    for i, seg in enumerate(segments):
        seg_words = []
        while wi < n and (i == last or words[wi]["start"] < seg["end"]):
            seg_words.append(dict(words[wi]))
            wi += 1
        seg["words"] = seg_words  # sempre presente (lista vazia em silêncio)
    result.pop("words", None)


def _transcribe_api(audio_path: Path, word_timestamps: bool = False) -> dict:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY não encontrada. "
            "Defina a variável de ambiente ou crie um arquivo .env com OPENAI_API_KEY=..."
        )

    client = OpenAI(api_key=api_key)

    size_mb = _file_size_mb(audio_path)
    if size_mb > MAX_API_SIZE_MB:
        return _transcribe_api_chunked(
            audio_path, client, word_timestamps=word_timestamps
        )

    extra_kwargs = {}
    if word_timestamps:
        # granularidade word tem custo de latência na API; só pedimos com a
        # flag. "segment" junto pra não perder os segments do verbose_json.
        extra_kwargs["timestamp_granularities"] = ["word", "segment"]

    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            **extra_kwargs,
        )
    result = response.model_dump()
    if word_timestamps:
        _distribute_api_words(result)
    return result


def _transcribe_api_chunked(
    audio_path: Path, client, word_timestamps: bool = False
) -> dict:
    """Divide o áudio em chunks < 25MB, transcreve cada um e concatena."""
    from pydub import AudioSegment

    audio = AudioSegment.from_mp3(str(audio_path))
    duration_ms = len(audio)

    # Estima tamanho por ms para calcular chunk seguro
    size_mb = _file_size_mb(audio_path)
    ms_per_mb = duration_ms / size_mb
    chunk_ms = int(ms_per_mb * MAX_API_SIZE_MB * 0.9)  # 90% do limite

    segments_all = []
    text_parts = []
    language = None
    offset_s = 0.0

    chunk_index = 0
    for start_ms in range(0, duration_ms, chunk_ms):
        chunk = audio[start_ms : start_ms + chunk_ms]
        chunk_path = audio_path.parent / f"chunk_{chunk_index:03d}.mp3"
        chunk.export(str(chunk_path), format="mp3", bitrate="64k")

        extra_kwargs = {}
        if word_timestamps:
            extra_kwargs["timestamp_granularities"] = ["word", "segment"]

        try:
            with open(chunk_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    **extra_kwargs,
                )
            result = response.model_dump()

            if word_timestamps:
                # normaliza ANTES do offset: words e segments ainda no mesmo
                # referencial (relativo ao chunk). Chunk sem segments é caso
                # degenerado — o fallback top-level é descartado no concat.
                _distribute_api_words(result)

            if language is None:
                language = result.get("language")

            text_parts.append(result.get("text", ""))

            for seg in result.get("segments", []):
                adjusted = dict(seg)
                adjusted["start"] = seg["start"] + offset_s
                adjusted["end"] = seg["end"] + offset_s
                if seg.get("words"):
                    # mesmo cuidado do modo multilang: copia as words somando
                    # o offset (dict(seg) é shallow)
                    adjusted["words"] = [
                        {
                            **w,
                            "start": w["start"] + offset_s,
                            "end": w["end"] + offset_s,
                        }
                        for w in seg["words"]
                    ]
                segments_all.append(adjusted)

            # Duração real do chunk para ajustar offset
            offset_s += len(chunk) / 1000.0
        finally:
            chunk_path.unlink(missing_ok=True)

        chunk_index += 1

    return {
        "text": " ".join(text_parts),
        "segments": segments_all,
        "language": language,
    }


def transcribe(
    audio_path: Path,
    use_api: bool = False,
    model: str = "medium",
    language: str | None = None,
    multilang: bool = False,
    word_timestamps: bool = False,
    engine: str | None = None,
) -> dict:
    """
    Transcreve o áudio e retorna verbose JSON com segments.

    Args:
        audio_path: Caminho para o arquivo de áudio .mp3
        use_api: Se True, usa OpenAI Whisper API. Caso contrário, mlx-whisper local.
        model: Modelo Whisper. No engine mlx aceita nome curto ('medium',
            'large-v3') ou caminho local de modelo MLX; no whisperx, nome
            faster-whisper ('large-v3-turbo', 'large-v3', 'medium').
            Ignorado com engine api.
        language: Código de idioma ISO-639-1 (ex: 'pt', 'en', 'es') para forçar
            o idioma. None deixa o Whisper detectar nos primeiros 30s. Ignorado
            com --api (a API detecta automaticamente) e com `multilang=True`.
        multilang: Se True, ativa modo chunked com re-detecção de idioma por
            janela de 30s. Útil para reuniões com troca de idiomas no meio
            (PT/EN/ES). Cada segmento recebe um campo `language`. Mutuamente
            exclusivo com `language`. Ignorado com --api.
        word_timestamps: Se True, grava timestamps por palavra dentro de cada
            segment (`segments[i]["words"] = [{word, start, end, probability?}]`).
            Funciona no engine local (mlx) E na API (`probability` só existe no
            mlx). Na API adiciona latência à chamada. Nota: no mlx, o start/end
            de cada segment é reajustado pros bounds da primeira/última word.
            No whisperx, ativa a passada de alinhamento forçado (wav2vec2) e
            cada word ganha `score` em vez de `probability`.
        engine: 'mlx' (default), 'whisperx' ou 'api'. None deriva de
            `use_api` (backcompat com chamadores antigos). 'whisperx' roda
            faster-whisper/CTranslate2 em subprocess isolado via uv — rápido
            em CPU, não suporta `multilang`.

    Returns:
        dict com keys: text, segments (list com start/end/text), language
    """
    if engine is None:
        engine = "api" if use_api else "mlx"

    if engine == "api":
        return _transcribe_api(audio_path, word_timestamps=word_timestamps)

    if engine == "whisperx":
        if multilang:
            raise ValueError(
                "multilang não é suportado no engine whisperx — use o engine mlx."
            )
        return _transcribe_whisperx(
            audio_path,
            model=model,
            language=language,
            word_timestamps=word_timestamps,
        )

    if engine != "mlx":
        raise ValueError(f"Engine desconhecido: {engine!r} (use 'mlx', 'whisperx' ou 'api')")

    if not _check_mlx_whisper():
        raise ImportError(
            "mlx-whisper não está instalado.\n"
            "Instale com: pip install mlx-whisper\n"
            "Ou use a flag --api para transcrever via OpenAI Whisper API."
        )

    return _transcribe_local(
        audio_path,
        model,
        language=language,
        multilang=multilang,
        word_timestamps=word_timestamps,
    )
