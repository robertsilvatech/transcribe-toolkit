from pathlib import Path

import yaml

DEFAULTS = {
    "default_provider": "anthropic",
    "target_language": "pt-br",
    "providers": {
        "openai": {
            "model": "gpt-4.1-mini",
            "api_key_env": "OPENAI_API_KEY",
        },
        "anthropic": {
            "model": "claude-sonnet-4-6",
            "api_key_env": "ANTHROPIC_API_KEY",
        },
    },
}

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
        return data.get("translate", {})
    return {}


def resolve_config(
    provider: str | None = None,
    model: str | None = None,
    target_lang: str | None = None,
) -> dict:
    cfg = _load_config()

    resolved_provider = provider or cfg.get("default_provider") or DEFAULTS["default_provider"]
    resolved_lang = target_lang or cfg.get("target_language") or DEFAULTS["target_language"]

    cfg_providers = cfg.get("providers", {})
    provider_cfg = cfg_providers.get(resolved_provider, {})
    default_provider_cfg = DEFAULTS["providers"].get(resolved_provider, {})

    resolved_model = model or provider_cfg.get("model") or default_provider_cfg.get("model", "")
    api_key_env = provider_cfg.get("api_key_env") or default_provider_cfg.get("api_key_env", "")

    return {
        "provider": resolved_provider,
        "model": resolved_model,
        "target_lang": resolved_lang,
        "api_key_env": api_key_env,
    }
