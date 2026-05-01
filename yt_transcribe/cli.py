import argparse
import shutil
import sys
from pathlib import Path

import yt_dlp

from .config import resolve_output_path
from .downloader import (
    download_audio,
    find_existing_transcription,
    get_video_metadata,
    make_output_folder_name,
)
from .formatter import save_outputs
from .transcriber import transcribe


def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def main():
    _load_env()

    parser = argparse.ArgumentParser(
        prog="yt-transcribe",
        description="Transcreve vídeos do YouTube e salva arquivos raw para uso com LLMs.",
    )
    parser.add_argument("url", help="URL do vídeo do YouTube")
    parser.add_argument(
        "--output",
        default=None,
        metavar="DIR",
        help=(
            "Diretório base onde a pasta de output será criada. "
            "Se omitido, lê de config.yaml (yt_transcribe.default_output)."
        ),
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Usar OpenAI Whisper API em vez do mlx-whisper local (requer OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--model",
        default="medium",
        metavar="MODEL",
        help="Modelo mlx-whisper a usar (padrão: medium). Ex: large-v3. Ignorado com --api.",
    )
    parser.add_argument(
        "--cookies-from-browser",
        default=None,
        metavar="BROWSER",
        help=(
            "Usar cookies do browser para autenticar no YouTube "
            "(ex: chrome, firefox, safari, brave, edge). "
            "Útil para vídeos não listados ou quando ocorrer erro de bot-check."
        ),
    )
    parser.add_argument(
        "--no-ffmpeg",
        action="store_true",
        help="Baixar áudio no formato nativo (webm) sem converter via ffmpeg.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Re-baixa e re-transcreve mesmo se transcrição existente for "
            "encontrada em --output."
        ),
    )

    args = parser.parse_args()

    try:
        output_dir = resolve_output_path(args.output)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = "openai-whisper-api" if args.api else f"mlx-whisper/{args.model}"

    # Skip check: se já existe pasta com transcrição válida pra essa URL, retorna.
    if not args.force:
        try:
            preview_meta = get_video_metadata(
                args.url, cookies_from_browser=args.cookies_from_browser
            )
        except yt_dlp.utils.DownloadError as e:
            print(f"Erro ao consultar metadata do vídeo: {e}", file=sys.stderr)
            if "Sign in to confirm" in str(e) and not args.cookies_from_browser:
                print(
                    "\nDica: o YouTube exigiu login. Tente novamente com "
                    "`--cookies-from-browser chrome` (ou firefox/safari/brave/edge).",
                    file=sys.stderr,
                )
            sys.exit(1)
        existing = find_existing_transcription(
            output_dir, args.url, preview_meta.get("title", "")
        )
        if existing:
            existing.touch()
            print(f"✓  Já transcrito: {existing}")
            print("    (use --force para re-baixar e re-transcrever)")
            return

    audio_path = None
    try:
        # Etapa 1: Download
        print(f"⬇  Baixando áudio de: {args.url}")
        try:
            audio_path, metadata = download_audio(
                args.url,
                no_ffmpeg=args.no_ffmpeg,
                cookies_from_browser=args.cookies_from_browser,
            )
        except yt_dlp.utils.DownloadError as e:
            print(f"Erro ao baixar o vídeo: {e}", file=sys.stderr)
            if "Sign in to confirm" in str(e) and not args.cookies_from_browser:
                print(
                    "\nDica: o YouTube exigiu login. Tente novamente com "
                    "`--cookies-from-browser chrome` (ou firefox/safari/brave/edge).",
                    file=sys.stderr,
                )
            sys.exit(1)
        except Exception as e:
            print(f"Erro inesperado no download: {e}", file=sys.stderr)
            sys.exit(1)

        title = metadata.get("title") or "video"
        print(f"✓  Download concluído: {title}")

        # Validação: --no-ffmpeg + --api + áudio grande
        if args.no_ffmpeg and args.api:
            size_mb = audio_path.stat().st_size / (1024 * 1024)
            if size_mb > 24:
                print(
                    f"Erro: áudio tem {size_mb:.0f}MB (limite da API: 25MB). "
                    "Chunking requer ffmpeg. Remova --no-ffmpeg ou use transcrição local.",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Etapa 2: Transcrição
        print(f"🎙  Transcrevendo com {engine}...")
        try:
            result = transcribe(audio_path, use_api=args.api, model=args.model)
        except ImportError as e:
            print(f"\nErro: {e}", file=sys.stderr)
            sys.exit(1)
        except EnvironmentError as e:
            print(f"\nErro de configuração: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Erro durante a transcrição: {e}", file=sys.stderr)
            sys.exit(1)

        print("✓  Transcrição concluída")

        # Etapa 3: Salvar arquivos
        folder_name = make_output_folder_name(title)
        print(f"💾  Salvando arquivos em: {output_dir / folder_name}")
        dest = save_outputs(output_dir, folder_name, result, metadata, engine)

        print(f"\n✅  Pronto! Arquivos salvos em:\n    {dest}")
        print("    raw.md")
        print("    raw_timestamps.md")
        print("    raw_whisper.json")
        print("    meta.json")

    finally:
        # Cleanup do áudio temporário
        if audio_path and audio_path.exists():
            tmp_dir = audio_path.parent
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
