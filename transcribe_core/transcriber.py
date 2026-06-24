import os
from pathlib import Path

MAX_API_SIZE_MB = 24  # margem de segurança abaixo do limite de 25MB da OpenAI


def _check_mlx_whisper() -> bool:
    try:
        import mlx_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def _file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def _transcribe_local(audio_path: Path, model: str) -> dict:
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=f"mlx-community/whisper-{model}-mlx",
        verbose=True,
    )
    return result


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


def transcribe(audio_path: Path, use_api: bool = False, model: str = "medium") -> dict:
    """
    Transcreve o áudio e retorna verbose JSON com segments.

    Args:
        audio_path: Caminho para o arquivo de áudio .mp3
        use_api: Se True, usa OpenAI Whisper API. Caso contrário, mlx-whisper local.
        model: Modelo mlx-whisper (ex: 'medium', 'large-v3'). Ignorado com --api.

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

    return _transcribe_local(audio_path, model)
