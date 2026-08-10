"""CLI for local_transcribe — transcribes local media files into raw/meta outputs."""

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from transcribe_core import save_outputs, slugify, transcribe
from transcribe_core.silence import shift_segments, trim_leading_trailing_silence

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
    """Procura subpasta `*_<slug>` (layout com data) ou `<slug>` (layout
    --no-date) em `target_dir` com `meta.json["source_path"] == source_abs`.

    Retorna o Path da subpasta mais recente que casa, ou None.
    """
    if not target_dir.is_dir():
        return None
    candidates = sorted(target_dir.glob(f"*_{slug}"), reverse=True)
    # layout --no-date: pasta com o slug puro (o glob `*_{slug}` nunca casa
    # com ela, então não há risco de candidato duplicado)
    exact = target_dir / slug
    if exact.is_dir():
        candidates.append(exact)
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
    trim_silence_minutes: float | None = None,
    no_date: bool = False,
    word_timestamps: bool = False,
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

    leading_offset_seconds = 0.0
    transcription_audio_path = audio_path
    if trim_silence_minutes is not None and not use_api:
        # API path tem chunking próprio e custo de I/O na rede; aplicamos o trim
        # apenas no caminho local (mlx-whisper), onde o benefício é maior
        # (evita decodificar horas de silêncio).
        try:
            trim_result = trim_leading_trailing_silence(
                audio_path,
                min_silence_seconds=trim_silence_minutes * 60.0,
            )
        except subprocess.CalledProcessError as e:
            return ("error", f"Falha ao cortar silêncio com ffmpeg: {e}")
        leading_offset_seconds = trim_result.leading_offset_seconds
        transcription_audio_path = trim_result.audio_path
        cut_total = (
            trim_result.original_duration_seconds
            - trim_result.trimmed_duration_seconds
        )
        if cut_total > 0:
            print(
                f"    [trim] cortado {cut_total / 60.0:.1f}min de silêncio "
                f"({trim_result.original_duration_seconds / 60.0:.1f}min "
                f"→ {trim_result.trimmed_duration_seconds / 60.0:.1f}min)"
            )

    try:
        result = transcribe(
            transcription_audio_path,
            use_api=use_api,
            model=model,
            language=language,
            multilang=multilang,
            word_timestamps=word_timestamps,
        )
    except (ImportError, EnvironmentError) as e:
        return ("error", str(e))
    except Exception as e:
        return ("error", f"Erro durante a transcrição: {e}")

    # Mapeia os timestamps de volta pro tempo original do vídeo (somando o
    # silêncio inicial cortado). Os timestamps do meio/fim já estão corretos
    # porque preservamos silêncios intermediários no trim.
    if leading_offset_seconds > 0:
        shift_segments(result, leading_offset_seconds)

    duration = _audio_duration_seconds(audio_path)
    metadata = {
        "title": title,
        "source": "local",
        "source_path": source_abs,
        "duration_seconds": duration,
        "language": result.get("language"),
    }
    if word_timestamps:
        # registro pra auditoria: só aparece quando a flag foi usada, pra não
        # mudar o shape do meta.json das transcrições existentes
        metadata["word_timestamps"] = True

    folder_name = slug if no_date else f"{date.today().isoformat()}_{slug}"
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
        "--trim-silence",
        nargs="?",
        const=10.0,
        type=float,
        default=None,
        metavar="MINUTES",
        help=(
            "Corta silêncio inicial e/ou final maior que MINUTES (default: 10 "
            "quando a flag é usada sem valor). Útil pra gravações de reunião "
            "onde ninguém parou a gravação (ex: KT de 1h30 em vídeo de 4h). "
            "Silêncios intermediários são preservados — timestamps do "
            "raw_timestamps.md continuam batendo com o tempo original do "
            "vídeo. Ignorado com --api."
        ),
    )
    parser.add_argument(
        "--no-date",
        action="store_true",
        help=(
            "Nomeia a pasta de output apenas com o slug do arquivo "
            "(ex: 'aula01/' em vez de '2026-08-08_aula01/'). Útil pra "
            "materiais de curso onde a data de transcrição não agrega."
        ),
    )
    parser.add_argument(
        "--word-timestamps",
        action="store_true",
        help=(
            "Grava timestamps por palavra dentro de cada segmento no "
            "raw_whisper.json (segments[i].words). Funciona no engine local "
            "E com --api (na API adiciona latência à chamada). raw.md e "
            "raw_timestamps.md não mudam."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Para depois de transcrever N arquivos (skips não contam). "
            "Útil pra testar 1 aula antes de rodar um lote inteiro: "
            "--dir ~/curso --limit 1."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Transcreve até N arquivos em paralelo. Só faz sentido com --api "
            "(limitado por rede); o engine local (mlx) compartilha a GPU e "
            "roda sequencial. Ex: --dir ~/curso --api --workers 10."
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

    if args.limit is not None and args.limit < 1:
        print("Erro: --limit deve ser >= 1.", file=sys.stderr)
        sys.exit(2)

    if args.workers < 1:
        print("Erro: --workers deve ser >= 1.", file=sys.stderr)
        sys.exit(2)
    workers = args.workers
    if workers > 1 and not args.api:
        print(
            "[workers] engine local (mlx) compartilha a GPU — paralelismo não "
            "ajuda; usando --workers 1. Use --api pra paralelizar."
        )
        workers = 1

    total = len(inputs)
    stats = {"ok": 0, "skip": 0, "error": 0}

    jobs = []
    for source, rel_dir in inputs:
        target_dir = output_base
        if sub:
            target_dir = target_dir / sub
        if str(rel_dir) and str(rel_dir) != ".":
            target_dir = target_dir / rel_dir
        jobs.append((source, target_dir))

    def _run(source: Path, target_dir: Path) -> tuple[str, str]:
        return _process_one(
            source,
            target_dir,
            args.api,
            args.model,
            args.force,
            engine,
            language=args.language,
            multilang=args.multilang,
            trim_silence_minutes=args.trim_silence,
            no_date=args.no_date,
            word_timestamps=args.word_timestamps,
        )

    if workers > 1:
        # Resolve skips ANTES de paralelizar: é barato (só lê meta.json) e
        # preserva a semântica do --limit (N transcrições efetivas).
        pending = []
        for source, target_dir in jobs:
            existing = None
            if not args.force:
                existing = _find_existing(
                    target_dir, slugify(source.stem), str(source)
                )
            if existing:
                existing.touch()
                stats["skip"] += 1
                print(f"⏭  já transcrito: {existing}")
            else:
                pending.append((source, target_dir))

        if args.limit is not None and len(pending) > args.limit:
            print(
                f"[limit] --limit {args.limit}: processando {args.limit} de "
                f"{len(pending)} pendentes."
            )
            pending = pending[: args.limit]

        if pending:
            print(
                f"[workers] {len(pending)} arquivo(s), até {workers} em paralelo",
                flush=True,
            )

        def _run_announced(source: Path, target_dir: Path) -> tuple[str, str, float]:
            # marca o início na hora que o worker pega o arquivo — sem isso a
            # saída fica muda até a primeira transcrição terminar
            print(f"▶  {source.name}", flush=True)
            t0 = time.monotonic()
            status, detail = _run(source, target_dir)
            return status, detail, time.monotonic() - t0

        done = 0
        total_pending = len(pending)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_run_announced, source, target_dir): source
                for source, target_dir in pending
            }
            for future in as_completed(futures):
                source = futures[future]
                done += 1
                try:
                    status, detail, elapsed = future.result()
                except Exception as e:  # falha inesperada no worker
                    status, detail, elapsed = "error", str(e), 0.0
                stats[status] += 1
                if status == "ok":
                    print(
                        f"[{done}/{total_pending}] ✓ {source.name} "
                        f"({elapsed:.0f}s) → {detail}",
                        flush=True,
                    )
                elif status == "skip":
                    print(
                        f"[{done}/{total_pending}] ⏭  {source.name}: já transcrito",
                        flush=True,
                    )
                else:
                    print(
                        f"[{done}/{total_pending}] ✗ {source.name}: {detail}",
                        file=sys.stderr,
                    )
    else:
        processed = 0  # transcrições efetivas (ok/error) — skips não contam pro --limit
        for i, (source, target_dir) in enumerate(jobs, 1):
            print(f"[{i}/{total}] {source.name}")
            status, detail = _run(source, target_dir)
            stats[status] += 1
            if status == "ok":
                print(f"    ✓ {detail}")
            elif status == "skip":
                print(f"    ⏭  já transcrito: {detail}")
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
        f"Resumo: {stats['ok']} transcritos, {stats['skip']} pulados, "
        f"{stats['error']} com erro."
    )

    sys.exit(1 if stats["error"] > 0 else 0)


if __name__ == "__main__":
    main()
