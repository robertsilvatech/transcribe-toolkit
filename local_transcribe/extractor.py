"""Audio extraction — turns video files into sibling .mp3 via ffmpeg.

Audio files (.mp3/.m4a/.wav) are returned as-is. Video files (.mp4/.mov/.mkv)
get a sibling .mp3 extracted next to the source. The .mp3 is cached: if it
already exists, it is reused without re-extracting.

Read-only source directories cause a clear error rather than silently falling
back to /tmp.
"""

import os
import shutil
import subprocess
from pathlib import Path

VIDEO_EXTS = {".mp4", ".mov", ".mkv"}
AUDIO_EXTS = {".mp3", ".m4a", ".wav"}
SUPPORTED_EXTS = VIDEO_EXTS | AUDIO_EXTS


class ExtractorError(Exception):
    """Raised when audio extraction fails or the source folder is not writable."""


def extract_audio(source: Path) -> Path:
    """Return path to an audio file usable by `transcribe()`.

    For audio inputs, returns the source itself. For video inputs, extracts
    a sibling .mp3 (reusing if already present) and returns its path.
    """
    source = source.expanduser().resolve()
    ext = source.suffix.lower()

    if ext in AUDIO_EXTS:
        return source

    if ext not in VIDEO_EXTS:
        raise ExtractorError(
            f"Unsupported extension {ext!r} for {source.name}. "
            f"Supported: {sorted(SUPPORTED_EXTS)}"
        )

    mp3_path = source.with_suffix(".mp3")
    if mp3_path.exists():
        return mp3_path

    if not os.access(source.parent, os.W_OK):
        raise ExtractorError(
            f"Source folder is not writable: {source.parent}\n"
            "Cannot extract audio next to the source file. "
            "Move the file to a writable location and retry."
        )

    if not shutil.which("ffmpeg"):
        raise ExtractorError(
            "ffmpeg not found in PATH. Install with: brew install ffmpeg"
        )

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(source),
                "-vn",
                "-acodec",
                "libmp3lame",
                "-b:a",
                "64k",
                str(mp3_path),
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
        raise ExtractorError(
            f"ffmpeg failed to extract audio from {source}:\n{stderr}"
        ) from e

    return mp3_path
