"""Config loader for yt_transcribe — reads `yt_transcribe:` section of config.yaml."""

from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def _load_config() -> dict:
    """Return the yt_transcribe: section of config.yaml, or {} if absent."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
        return data.get("yt_transcribe", {})
    return {}


def resolve_output_path(cli_output: str | None) -> Path:
    """Resolve the base output directory for transcriptions.

    Cascade: CLI flag > config.yaml `default_output` > raise.
    Tilde (`~`) is expanded; the path is resolved to an absolute path.
    """
    cfg = _load_config()
    raw = cli_output or cfg.get("default_output")
    if not raw:
        raise ValueError(
            "No output path provided. Pass --output <dir> or set "
            "yt_transcribe.default_output in config.yaml."
        )
    return Path(raw).expanduser().resolve()
