import argparse
import sys
from pathlib import Path

from .config import resolve_config
from .generator import generate_study_material

OUTPUT_NAME = "study.md"


def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _collect_inputs(positional: list[str], dir_path: str | None) -> list[Path]:
    """Resolve inputs numa lista de arquivos de transcrição.

    Posicionais: qualquer .md explícito (ex: raw.md, raw_pt-br.md).
    --dir: varre recursivamente por `raw.md` (uma transcrição por subpasta).
    """
    inputs: list[Path] = []

    for raw in positional:
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {raw}")
        if not p.is_file():
            raise ValueError(f"Não é um arquivo: {raw}")
        inputs.append(p)

    if dir_path:
        base = Path(dir_path).expanduser().resolve()
        if not base.is_dir():
            raise FileNotFoundError(f"Diretório não encontrado: {dir_path}")
        inputs.extend(sorted(base.rglob("raw.md")))

    return inputs


def _process_one(
    input_path: Path, cfg: dict, force: bool, output_dir: Path | None = None
) -> tuple[str, str]:
    """Retorna (status, detail) com status 'ok' | 'skip' | 'error'.

    Sem `output_dir`: escreve study.md ao lado do input. Com `output_dir`:
    escreve <nome-da-aula>.md dentro dele (nome da aula = nome da pasta da
    transcrição, que no fluxo de curso é o slug do vídeo).
    """
    if output_dir is not None:
        output_path = output_dir / f"{input_path.parent.name}.md"
    else:
        output_path = input_path.parent / OUTPUT_NAME
    if output_path.exists() and not force:
        return ("skip", str(output_path))

    text = input_path.read_text(encoding="utf-8")

    try:
        material = generate_study_material(
            text,
            provider=cfg["provider"],
            model=cfg["model"],
            api_key_env=cfg["api_key_env"],
        )
    except (EnvironmentError, ValueError) as e:
        return ("error", str(e))
    except Exception as e:
        return ("error", f"Erro durante a geração: {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(material, encoding="utf-8")
    return ("ok", str(output_path))


def main():
    _load_env()

    parser = argparse.ArgumentParser(
        prog="study-material",
        description=(
            "Gera material didático organizado (tópicos/subtópicos) a partir de "
            "transcrições brutas, via LLM API. Output: study.md ao lado do input."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Arquivos de transcrição (ex: raw.md ou raw_pt-br.md).",
    )
    parser.add_argument(
        "--dir",
        default=None,
        metavar="PATH",
        help="Diretório com transcrições (varre recursivamente por raw.md).",
    )
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
        "--output-dir",
        default=None,
        metavar="DIR",
        help=(
            "Grava os materiais como <nome-da-aula>.md dentro deste diretório "
            "(nome da aula = nome da pasta da transcrição), em vez de study.md "
            "ao lado de cada raw.md. Útil pra juntar tudo numa pasta única "
            "pronta pra upload."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Para depois de gerar N materiais (skips não contam).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-gera mesmo se study.md já existe.",
    )

    args = parser.parse_args()

    if not args.files and not args.dir:
        parser.print_usage(sys.stderr)
        print(
            "Erro: passe pelo menos um arquivo posicional ou --dir <path>.",
            file=sys.stderr,
        )
        sys.exit(2)

    if args.limit is not None and args.limit < 1:
        print("Erro: --limit deve ser >= 1.", file=sys.stderr)
        sys.exit(2)

    try:
        inputs = _collect_inputs(args.files, args.dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    if not inputs:
        print("Nenhuma transcrição encontrada.", file=sys.stderr)
        sys.exit(1)

    cfg = resolve_config(provider=args.provider, model=args.model)
    print(f"🧠  Engine: {cfg['provider']}/{cfg['model']}")

    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()

    total = len(inputs)
    stats = {"ok": 0, "skip": 0, "error": 0}
    processed = 0  # gerações efetivas (ok/error) — skips não contam pro --limit

    for i, input_path in enumerate(inputs, 1):
        print(f"[{i}/{total}] {input_path.parent.name}/{input_path.name}")
        status, detail = _process_one(input_path, cfg, args.force, output_dir=output_dir)
        stats[status] += 1
        if status == "ok":
            print(f"    ✓ {detail}")
        elif status == "skip":
            print(f"    ⏭  já gerado: {detail}")
        else:
            print(f"    ✗ {detail}", file=sys.stderr)

        if status != "skip":
            processed += 1
            if args.limit is not None and processed >= args.limit:
                remaining = total - i
                print(f"\n[limit] --limit {args.limit} atingido, parando "
                      f"({remaining} arquivo(s) restante(s) na fila).")
                break

    print()
    print(
        f"Resumo: {stats['ok']} gerados, {stats['skip']} pulados, "
        f"{stats['error']} com erro."
    )

    sys.exit(1 if stats["error"] > 0 else 0)


if __name__ == "__main__":
    main()
