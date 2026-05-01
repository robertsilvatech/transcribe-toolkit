"""Config loader for vault_import — reads `vault_import:` section of config.yaml."""

from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def _load_config() -> dict:
    """Return the vault_import: section of config.yaml, or {} if absent."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
        return data.get("vault_import", {})
    return {}


def resolve_vault_path(cli_vault: str | None) -> Path:
    """Resolve the destination vault path.

    Cascade: CLI flag > config.yaml `default_vault` > raise.
    Tilde (`~`) is expanded; the path is resolved to an absolute path.
    """
    cfg = _load_config()
    raw = cli_vault or cfg.get("default_vault")
    if not raw:
        raise ValueError(
            "No vault path provided. Pass --vault <path> or set "
            "vault_import.default_vault in config.yaml."
        )
    return Path(raw).expanduser().resolve()
