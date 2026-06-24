"""CLI for local_transcribe — transcribes local media files into raw/meta outputs."""

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from transcribe_core import save_outputs, slugify, transcribe

from .config import resolve_output_path
from .extractor import SUPPORTED_EXTS, ExtractorError, extract_audio


def _load_env():
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _audio_duration_seconds(audio_path: Path) -> int:
    """Return duration in seconds via ffprobe. Returns 0 if ffprobe unavailable/fails."""
    try:
        out = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return int(float(out.stdout.strip()))
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return 0


def _find_existing(target_dir: Path, slug: str, source_abs: str) -> Path | None:
    """Procura subpasta `*_<slug>` em `target_dir` com `meta.json["source_path"] == source_abs`.

    Retorna o Path da subpasta mais recente que casa, ou None.
    """
    if not target_dir.is_dir():
        return None
    candidates = sorted(target_dir.glob(f"*_{slug}"), reverse=True)
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        meta_path = candidate / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if meta.get("source_path") == source_abs:
            return candidate
    return None


def _collect_inputs(
    positional: list[str], dir_path: str | None
) -> list[tuple[Path, Path]]:
    """Resolve inputs into a list of (source_abs, rel_dir) tuples.

    For positional files, rel_dir is Path("") (flat). For --dir mode, rel_dir
    is the parent of source.relative_to(dir_base), preserving the source tree.
    """
    pairs: list[tuple[Path, Path]] = []

    for raw in positional:
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {raw}")
        if not p.is_file():
            raise ValueError(f"Não é um arquivo: {raw}")
        if p.suffix.lower() not in SUPPORTED_EXTS:
            raise ValueError(
                f"Extensão não suportada: {p.suffix} ({p.name}). "
                f"Aceitas: {sorted(SUPPORTED_EXTS)}"
            )
        pairs.append((p, Path("")))

    if dir_path:
        base = Path(dir_path).expanduser().resolve()
        if not base.exists():
            raise FileNotFoundError(f"Diretório não encontrado: {dir_path}")
        if not base.is_dir():
            raise ValueError(f"Não é um diretório: {dir_path}")
        found = []
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                # Skip sibling .mp3 cached files (they were extracted from a video next to them)
                if p.suffix.lower() == ".mp3":
                    siblings_video = any(
                        (p.with_suffix(ext)).exists() for ext in (".mp4", ".mov", ".mkv")
                    )
                    if siblings_video:
                        continue
                rel = p.relative_to(base).parent
                found.append((p, rel))
        found.sort(key=lambda t: str(t[0]))
        pairs.extend(found)

    return pairs


def _process_one(
    source: Path,
    target_dir: Path,
    use_api: bool,
    model: str,
    force: bool,
    engine: str,
    language: str | None = None,
    multilang: bool = False,
) -> tuple[str, str]:
    """Process a single input. Returns (status, detail) where status is
    'ok' | 'skip' | 'error'.
    """
    source_abs = str(source)
    title = source.stem
    slug = slugify(title)

    if not force:
        existing = _find_existing(target_dir, slug, source_abs)
        if existing:
            existing.touch()
            return ("skip", str(existing))

    try:
        audio_path = extract_audio(source)
    except ExtractorError as e:
        return ("error", str(e))

    try:
        result = transcribe(
            audio_path,
            use_api=use_api,
            model=model,
            language=language,
            multilang=multilang,
        )
    except (ImportError, EnvironmentError) as e:
        return ("error", str(e))
    except Exception as e:
        return ("error", f"Erro durante a transcrição: {e}")

    duration = _audio_duration_seconds(audio_path)
    metadata = {
        "title": title,
        "source": "local",
        "source_path": source_abs,
        "duration_seconds": duration,
        "language": result.get("language"),
    }

    folder_name = f"{date.today().isoformat()}_{slug}"
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = save_outputs(target_dir, folder_name, result, metadata, engine)
    return ("ok", str(dest))


def main():
    _load_env()

    parser = argparse.ArgumentParser(
        prog="local-transcribe",
        description=(
            "Transcreve arquivos de mídia locais (.mp4/.mov/.mkv/.m4a/.mp3/.wav). "
            "Aceita arquivos posicionais e/ou --dir para varrer recursivamente."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Arquivos de mídia para transcrever (posicionais).",
    )
    parser.add_argument(
        "--dir",
        default=None,
        metavar="PATH",
        help="Diretório com arquivos de mídia (varre recursivamente).",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="DIR",
        help=(
            "Diretório base onde as subpastas de output serão criadas. "
            "Se omitido, lê de config.yaml (local_transcribe.default_output)."
        ),
    )
    parser.add_argument(
        "--subfolder",
        default=None,
        metavar="NAME",
        help=(
            "Subpasta dentro do output base. Em modo --dir, a árvore do source "
            "é espelhada dentro dessa subpasta."
        ),
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Usar OpenAI Whisper API em vez do mlx-whisper local (requer OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--model",
        default="medium",
        metavar="MODEL",
        help=(
            "Modelo mlx-whisper a usar. Pode ser um nome curto "
            "('tiny', 'base', 'small', 'medium', 'large-v3') OU um caminho "
            "para um diretório local de modelo MLX já convertido. "
            "Padrão: medium. Ignorado com --api."
        ),
    )
    lang_group = parser.add_mutually_exclusive_group()
    lang_group.add_argument(
        "--language",
        default=None,
        metavar="CODE",
        help=(
            "Força o idioma do áudio (código ISO-639-1: 'pt', 'en', 'es', etc). "
            "Sem essa flag, o Whisper detecta automaticamente nos primeiros 30s "
            "e mantém o idioma na chamada inteira. Útil quando você sabe o "
            "idioma e quer evitar erros de detecção. Ignorado com --api. "
            "Mutuamente exclusivo com --multilang."
        ),
    )
    lang_group.add_argument(
        "--multilang",
        action="store_true",
        help=(
            "Modo chunked com re-detecção de idioma por janela de 30s. Útil "
            "para reuniões com troca de idiomas no meio (PT/EN/ES). Cada "
            "segmento ganha marcação [<lang>] no raw_timestamps.md. "
            "Mais lento que single-pass. Ignorado com --api. "
            "Mutuamente exclusivo com --language."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-transcreve mesmo se transcrição existente for encontrada.",
    )

    args = parser.parse_args()

    if not args.files and not args.dir:
        parser.print_usage(sys.stderr)
        print(
            "Erro: passe pelo menos um arquivo posicional ou --dir <path>.",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        output_base = resolve_output_path(args.output)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
    output_base.mkdir(parents=True, exist_ok=True)

    try:
        inputs = _collect_inputs(args.files, args.dir)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)

    if not inputs:
        print("Nenhum arquivo de mídia suportado encontrado.", file=sys.stderr)
        sys.exit(1)

    if args.api:
        engine = "openai-whisper-api"
    else:
        engine = f"mlx-whisper/{args.model}"
        if args.multilang:
            engine += "+multilang"
        elif args.language:
            engine += f"+lang={args.language}"

    sub = args.subfolder.strip().strip("/") if args.subfolder else None
    if sub and ("/" in sub or "\\" in sub or sub.startswith(".")):
        print(
            f"Erro: --subfolder inválido: {args.subfolder!r}. "
            "Use um único segmento de path sem barras ou pontos iniciais.",
            file=sys.stderr,
        )
        sys.exit(1)

    total = len(inputs)
    stats = {"ok": 0, "skip": 0, "error": 0}

    for i, (source, rel_dir) in enumerate(inputs, 1):
        target_dir = output_base
        if sub:
            target_dir = target_dir / sub
        if str(rel_dir) and str(rel_dir) != ".":
            target_dir = target_dir / rel_dir

        print(f"[{i}/{total}] {source.name}")
        status, detail = _process_one(
            source,
            target_dir,
            args.api,
            args.model,
            args.force,
            engine,
            language=args.language,
            multilang=args.multilang,
        )
        stats[status] += 1
        if status == "ok":
            print(f"    ✓ {detail}")
        elif status == "skip":
            print(f"    ⏭  já transcrito: {detail}")
        else:
            print(f"    ✗ {detail}", file=sys.stderr)

    print()
    print(
        f"Resumo: {stats['ok']} transcritos, {stats['skip']} pulados, "
        f"{stats['error']} com erro."
    )

    sys.exit(1 if stats["error"] > 0 else 0)


if __name__ == "__main__":
    main()
