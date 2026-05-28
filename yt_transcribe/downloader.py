import json
import tempfile
from pathlib import Path

import yt_dlp

from transcribe_core import slugify


def download_audio(
    url: str,
    no_ffmpeg: bool = False,
    cookies_from_browser: str | None = None,
) -> tuple[Path, dict]:
    """
    Baixa o áudio de uma URL do YouTube e retorna o caminho temporário + metadata.

    Returns:
        (audio_path, metadata) onde metadata contém title, channel, url,
        duration_seconds, language.

    O chamador é responsável por deletar o arquivo temporário.
    """
    tmp_dir = Path(tempfile.mkdtemp())
    output_template = str(tmp_dir / "audio.%(ext)s")

    metadata: dict = {}

    # ios/android_vr não suportam cookies; quando cookies são passados usar
    # clients web que aceitam cookies. tv é preferível pois não exige JS runtime.
    player_clients = ["tv", "web", "mweb"] if cookies_from_browser else ["android_vr"]

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/140/251/bestaudio/best",
        "outtmpl": output_template,
        "quiet": False,
        "no_warnings": False,
        "verbose": True,
        "extractor_args": {"youtube": {"player_client": player_clients}},
        # padrão do yt-dlp é só deno; forçar node (disponível via nvm)
        "js_runtimes": {"node": {}, "bun": {}, "deno": {}},
    }

    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

    if not no_ffmpeg:
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }
        ]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        metadata = {
            "title": info.get("title", ""),
            "channel": info.get("uploader") or info.get("channel", ""),
            "url": url,
            "duration_seconds": info.get("duration", 0),
            "language": info.get("language"),
        }

    # Busca por glob — extensão varia conforme no_ffmpeg (mp3 vs webm/etc)
    candidates = list(tmp_dir.glob("audio.*"))
    if not candidates:
        raise FileNotFoundError(f"Arquivo de áudio não encontrado em {tmp_dir}")
    audio_path = candidates[0]

    return audio_path, metadata


def make_output_folder_name(title: str) -> str:
    """Retorna nome de pasta no formato YYYY-MM-DD_slug."""
    from datetime import date

    today = date.today().isoformat()
    slug = slugify(title)
    return f"{today}_{slug}"


def get_video_metadata(url: str, cookies_from_browser: str | None = None) -> dict:
    """Consulta metadata do vídeo sem baixar áudio.

    Reusa a mesma lógica de player_clients e cookies do download_audio.
    Retorna dict com mesmo shape do metadata produzido por download_audio.
    """
    player_clients = ["tv", "web", "mweb"] if cookies_from_browser else ["android_vr"]

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extractor_args": {"youtube": {"player_client": player_clients}},
        "js_runtimes": {"node": {}, "bun": {}, "deno": {}},
    }
    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", ""),
            "channel": info.get("uploader") or info.get("channel", ""),
            "url": url,
            "duration_seconds": info.get("duration", 0),
            "language": info.get("language"),
        }


def find_existing_transcription(
    output_dir: Path, url: str, title: str
) -> Path | None:
    """Procura pasta `*_<slug>` existente em output_dir com transcrição válida.

    Critério: pasta contém `raw.md` e `meta.json` cujo `url` casa com `url`.
    Retorna o Path da pasta mais recente que casa, ou None.
    """
    slug = slugify(title)
    candidates = sorted(output_dir.glob(f"*_{slug}"), reverse=True)
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        if not (candidate / "raw.md").exists():
            continue
        meta_path = candidate / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if meta.get("url") == url:
            return candidate
    return None
