import argparse
import sys
from pathlib import Path

from .config import resolve_config
from .translator import translate_text


def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def main():
    _load_env()

    parser = argparse.ArgumentParser(
        prog="translate",
        description="Traduz arquivos de texto usando LLM APIs (OpenAI ou Anthropic).",
    )
    parser.add_argument("path", help="Caminho do arquivo a traduzir (ex: raw.md)")
    parser.add_argument(
        "--provider",
        metavar="PROVIDER",
        help="Provider de LLM: openai ou anthropic (default: config.yaml ou anthropic)",
    )
    parser.add_argument(
        "--model",
        metavar="MODEL",
        help="Modelo a usar (default: config.yaml ou default do provider)",
    )
    parser.add_argument(
        "--target-lang",
        metavar="LANG",
        help="Idioma alvo (default: config.yaml ou pt-br)",
    )

    args = parser.parse_args()

    input_path = Path(args.path).expanduser().resolve()
    if not input_path.exists():
        print(f"Erro: arquivo não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    cfg = resolve_config(
        provider=args.provider,
        model=args.model,
        target_lang=args.target_lang,
    )

    provider = cfg["provider"]
    model = cfg["model"]
    target_lang = cfg["target_lang"]
    api_key_env = cfg["api_key_env"]

    print(f"📖  Lendo: {input_path}")
    text = input_path.read_text(encoding="utf-8")
    print(f"🌐  Traduzindo para {target_lang} com {provider}/{model}...")

    try:
        translated = translate_text(text, provider, model, target_lang, api_key_env)
    except EnvironmentError as e:
        print(f"\nErro de configuração: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\nErro: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nErro durante a tradução: {e}", file=sys.stderr)
        sys.exit(1)

    output_name = f"{input_path.stem}_{target_lang}.md"
    output_path = input_path.parent / output_name
    output_path.write_text(translated, encoding="utf-8")

    print(f"✅  Salvo em: {output_path}")


if __name__ == "__main__":
    main()
