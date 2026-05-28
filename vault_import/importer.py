"""Importer engine — copy a transcribed folder's pt-br markdown into a vault's raw/."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path

YOUTUBE_VIDEO_ID_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|embed/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)

DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_")


def build_dest_filename(slug: str, prefix: str | None) -> str:
    """Compose the destination filename. With prefix, strips `YYYY-MM-DD_` from slug."""
    if not prefix:
        return f"{slug}.md"
    cleaned = DATE_PREFIX_RE.sub("", slug)
    return f"{prefix}_{cleaned}.md"


class ImporterError(Exception):
    """Raised when input or destination validation fails, or write conflicts."""


def validate_input(input_dir: Path) -> dict:
    """Validate the transcribed folder and return parsed meta.json.

    Raises ImporterError if the folder is missing required files or meta.json
    is malformed.
    """
    if not input_dir.exists():
        raise ImporterError(f"Input folder does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise ImporterError(f"Input path is not a directory: {input_dir}")

    raw_pt = input_dir / "raw_pt-br.md"
    meta = input_dir / "meta.json"

    if not raw_pt.exists():
        raise ImporterError(
            f"raw_pt-br.md not found in {input_dir}. "
            "Did you run `uv run translate` on this folder first?"
        )
    if not meta.exists():
        raise ImporterError(
            f"meta.json not found in {input_dir}. "
            "Did you run `uv run yt-transcribe` to produce this folder?"
        )

    try:
        meta_data = json.loads(meta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ImporterError(f"meta.json is not valid JSON ({e}): {meta}") from e

    if not isinstance(meta_data, dict):
        raise ImporterError(f"meta.json is not a JSON object: {meta}")

    for required_key in ("title", "url"):
        if not meta_data.get(required_key):
            raise ImporterError(
                f"meta.json is missing required key '{required_key}': {meta}"
            )

    return meta_data


def validate_destination(
    vault: Path,
    slug: str,
    force: bool,
    subfolder: str | None = None,
    prefix: str | None = None,
) -> Path:
    """Validate vault and raw/, return the destination file path.

    If `subfolder` is provided, the destination becomes `<vault>/raw/<subfolder>/<slug>.md`
    and the subfolder is created on demand (mkdir -p).

    If `prefix` is provided, the filename becomes `<prefix>_<slug-without-date>.md`.

    Raises ImporterError if vault or raw/ are missing, the subfolder/prefix is invalid,
    or the destination file already exists without force=True.
    """
    if not vault.exists():
        raise ImporterError(f"Vault path does not exist: {vault}")
    if not vault.is_dir():
        raise ImporterError(f"Vault path is not a directory: {vault}")

    raw_dir = vault / "raw"
    if not raw_dir.exists():
        raise ImporterError(
            f"Vault has no raw/ subfolder: {raw_dir}. "
            "Bootstrap the vault first or create raw/ manually."
        )
    if not raw_dir.is_dir():
        raise ImporterError(f"{raw_dir} exists but is not a directory.")

    dest_dir = raw_dir
    if subfolder:
        sub = subfolder.strip().strip("/")
        if not sub or sub.startswith(".") or "/" in sub or "\\" in sub:
            raise ImporterError(
                f"Invalid subfolder name: {subfolder!r}. "
                "Use a single path segment without slashes or leading dots."
            )
        dest_dir = raw_dir / sub
        dest_dir.mkdir(parents=True, exist_ok=True)
        if not dest_dir.is_dir():
            raise ImporterError(f"{dest_dir} exists but is not a directory.")

    if prefix is not None:
        pfx = prefix.strip()
        if not pfx or "/" in pfx or "\\" in pfx or pfx.startswith("."):
            raise ImporterError(
                f"Invalid prefix: {prefix!r}. "
                "Use a non-empty string without slashes or leading dots."
            )
    else:
        pfx = None

    dest = dest_dir / build_dest_filename(slug, pfx)
    if dest.exists() and not force:
        raise ImporterError(
            f"Destination already exists: {dest}\n"
            "Pass --force to overwrite."
        )
    return dest


def extract_video_id(url: str) -> str | None:
    """Extract a YouTube video id from common URL formats, or None."""
    if not url:
        return None
    m = YOUTUBE_VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def _yaml_quote(value) -> str:
    """Render a value for inline YAML — quotes strings, leaves numbers/null bare."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value).replace('"', '\\"')
    return f'"{s}"'


def build_frontmatter(meta: dict, slug: str) -> str:
    """Build the YAML frontmatter block (with `---` delimiters) for a vault file.

    Maps meta.json fields to the destination vault's source-side schema.
    """
    title = meta.get("title", "")
    url = meta.get("url", "")
    channel = meta.get("channel", "")
    # yt_transcribe writes `duration_seconds`; accept legacy `duration` too.
    duration = meta.get("duration_seconds") or meta.get("duration")
    original_language = meta.get("language")
    video_id = meta.get("video_id") or extract_video_id(url)
    today = date.today().isoformat()

    lines = [
        "---",
        f"title: {_yaml_quote(title)}",
        "type: source",
        "source_type: transcript",
        f"url: {_yaml_quote(url)}",
        f"channel: {_yaml_quote(channel)}",
        f"duration: {_yaml_quote(duration) if duration is not None else 'null'}",
        "language: pt-br",
        f"original_language: {_yaml_quote(original_language) if original_language else 'null'}",
        f"youtube_video_id: {_yaml_quote(video_id) if video_id else 'null'}",
        f"ingested: {today}",
        "tags: [transcript, youtube]",
        "---",
    ]
    return "\n".join(lines) + "\n"


def import_to_vault(
    input_dir: Path,
    vault: Path,
    force: bool,
    subfolder: str | None = None,
    prefix: str | None = None,
) -> Path:
    """Validate input + destination, then write `<vault>/raw/[<sub>/][<prefix>_]<slug>.md` atomically.

    Returns the absolute path of the file written.
    """
    input_dir = input_dir.expanduser().resolve()
    vault = vault.expanduser().resolve()
    slug = input_dir.name

    meta = validate_input(input_dir)
    dest = validate_destination(vault, slug, force, subfolder, prefix)

    body = (input_dir / "raw_pt-br.md").read_text(encoding="utf-8").strip()
    frontmatter = build_frontmatter(meta, slug)
    content = frontmatter + "\n" + body + "\n"

    # Atomic write: write to temp file in the same directory, then rename.
    raw_dir = dest.parent
    fd, tmp_name = tempfile.mkstemp(prefix=f".{slug}.", suffix=".md.tmp", dir=raw_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_name, dest)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    return dest
