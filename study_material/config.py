from pathlib import Path

import yaml

DEFAULTS = {
    "default_provider": "anthropic",
    "providers": {
        "openai": {
            "model": "gpt-4.1-mini",
            "api_key_env": "OPENAI_API_KEY",
        },
        "anthropic": {
            "model": "claude-sonnet-5",
            "api_key_env": "ANTHROPIC_API_KEY",
        },
    },
}

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
        return data.get("study_material", {})
    return {}


def resolve_config(
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    cfg = _load_config()

    resolved_provider = provider or cfg.get("default_provider") or DEFAULTS["default_provider"]

    cfg_providers = cfg.get("providers", {})
    provider_cfg = cfg_providers.get(resolved_provider, {})
    default_provider_cfg = DEFAULTS["providers"].get(resolved_provider, {})

    resolved_model = model or provider_cfg.get("model") or default_provider_cfg.get("model", "")
    api_key_env = provider_cfg.get("api_key_env") or default_provider_cfg.get("api_key_env", "")

    return {
        "provider": resolved_provider,
        "model": resolved_model,
        "api_key_env": api_key_env,
    }
