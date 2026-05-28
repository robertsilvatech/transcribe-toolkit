"""Config loader for local_transcribe — reads `local_transcribe:` section of config.yaml."""

import os
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"
ENV_VAR = "LOCAL_TRANSCRIBE_OUTPUT"


def _load_config() -> dict:
    """Return the local_transcribe: section of config.yaml, or {} if absent."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
        return data.get("local_transcribe", {})
    return {}


def resolve_output_path(cli_output: str | None) -> Path:
    """Resolve the base output directory for transcriptions.

    Cascade: CLI flag > env var LOCAL_TRANSCRIBE_OUTPUT > config.yaml `default_output` > raise.
    Tilde (`~`) is expanded; the path is resolved to an absolute path.
    """
    cfg = _load_config()
    env_value = os.environ.get(ENV_VAR) or None
    raw = cli_output or env_value or cfg.get("default_output")
    if not raw:
        raise ValueError(
            "No output path provided. Pass --output <dir>, "
            f"export {ENV_VAR}=<dir>, or set "
            "local_transcribe.default_output in config.yaml."
        )
    return Path(raw).expanduser().resolve()
