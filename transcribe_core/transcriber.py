import os
from pathlib import Path

MAX_API_SIZE_MB = 24  # margem de segurança abaixo do limite de 25MB da OpenAI


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
) -> dict:
    """Single-pass: detecta (ou força) um idioma e transcreve a chamada inteira
    nele. Se `multilang=True`, despacha para a versão chunked que re-detecta o
    idioma por janela (útil para reuniões com troca de PT/EN/ES no meio).
    """
    if multilang:
        return _transcribe_local_chunked(audio_path, model)

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


def _transcribe_api(audio_path: Path) -> dict:
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
        return _transcribe_api_chunked(audio_path, client)

    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
        )
    return response.model_dump()


def _transcribe_api_chunked(audio_path: Path, client) -> dict:
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

        try:
            with open(chunk_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                )
            result = response.model_dump()

            if language is None:
                language = result.get("language")

            text_parts.append(result.get("text", ""))

            for seg in result.get("segments", []):
                adjusted = dict(seg)
                adjusted["start"] = seg["start"] + offset_s
                adjusted["end"] = seg["end"] + offset_s
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
) -> dict:
    """
    Transcreve o áudio e retorna verbose JSON com segments.

    Args:
        audio_path: Caminho para o arquivo de áudio .mp3
        use_api: Se True, usa OpenAI Whisper API. Caso contrário, mlx-whisper local.
        model: Modelo mlx-whisper (ex: 'medium', 'large-v3'). Ignorado com --api.
        language: Código de idioma ISO-639-1 (ex: 'pt', 'en', 'es') para forçar
            o idioma. None deixa o Whisper detectar nos primeiros 30s. Ignorado
            com --api (a API detecta automaticamente) e com `multilang=True`.
        multilang: Se True, ativa modo chunked com re-detecção de idioma por
            janela de 30s. Útil para reuniões com troca de idiomas no meio
            (PT/EN/ES). Cada segmento recebe um campo `language`. Mutuamente
            exclusivo com `language`. Ignorado com --api.

    Returns:
        dict com keys: text, segments (list com start/end/text), language
    """
    if use_api:
        return _transcribe_api(audio_path)

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
    )
