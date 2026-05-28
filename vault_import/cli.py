"""vault-import CLI — bridge transcribed folders into a vault's raw/."""

import argparse
import sys
from pathlib import Path

from .config import resolve_vault_path
from .importer import ImporterError, import_to_vault


def main():
    parser = argparse.ArgumentParser(
        prog="vault-import",
        description=(
            "Copy a transcribed folder's pt-br markdown into a Karpathy-LLM-Wiki vault. "
            "Reads raw_pt-br.md + meta.json from the input folder and writes "
            "<vault>/raw/<slug>.md with rich YAML frontmatter."
        ),
    )
    parser.add_argument(
        "input_dir",
        help="Path to the folder produced by yt-transcribe + translate "
        "(must contain raw_pt-br.md and meta.json)",
    )
    parser.add_argument(
        "--vault",
        metavar="PATH",
        help="Destination vault path (overrides config.yaml's vault_import.default_vault)",
    )
    parser.add_argument(
        "-s", "--subfolder",
        metavar="NAME",
        help="Subfolder inside raw/ to write into (e.g. 'curso-mastering-devin'). "
        "Created on demand. Without this flag, writes directly to raw/.",
    )
    parser.add_argument(
        "-p", "--prefix",
        metavar="VALUE",
        help="Prefix prepended to the filename, e.g. 'A01' or 'M01A10'. "
        "Strips the YYYY-MM-DD_ from the slug. Final: <prefix>_<slug-no-date>.md",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the destination file if it already exists",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()

    try:
        vault = resolve_vault_path(args.vault)
    except ValueError as e:
        print(f"Erro de configuração: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"📖  Input:  {input_dir}")
    print(f"📁  Vault:  {vault}")
    if args.subfolder:
        print(f"📂  Subfolder: raw/{args.subfolder}/")
    if args.prefix:
        print(f"🔖  Prefix: {args.prefix}")

    try:
        dest = import_to_vault(
            input_dir, vault, args.force, args.subfolder, args.prefix
        )
    except ImporterError as e:
        print(f"\nErro: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nErro inesperado: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✅  Escrito: {dest}")


if __name__ == "__main__":
    main()
