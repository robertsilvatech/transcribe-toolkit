"""CLI do laboratório HeyGen (API v3) — upload de áudio/imagem e geração de vídeo.

Fluxo principal (voz gravada → avatar com lip-sync):
    heygen-lab generate --audio gravacao.m4a --captions
    heygen-lab generate --audio fala.mp3 --avatar <id> --output ./out

Fluxo TTS (texto → voz clonada):
    heygen-lab generate --text-file narracao.txt

.m4a (gravador do iPhone) é convertido pra .mp3 automaticamente via ffmpeg —
o upload do HeyGen aceita mp3/wav, não m4a.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from .client import (
    ASPECT_LANDSCAPE,
    ASPECT_PORTRAIT,
    HeyGen,
    HeyGenError,
)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    here = Path(__file__).resolve().parent.parent
    for candidate in (here / ".env", here.parent / ".env"):
        if candidate.exists():
            load_dotenv(candidate)
            return


def _ensure_uploadable_audio(path: Path) -> Path:
    """Devolve um caminho .mp3/.wav aceito pelo upload.

    Gravador do iPhone salva .m4a; o POST /v3/assets só aceita mp3/wav.
    Convertemos via ffmpeg pra um tmp — o original não é tocado.
    """
    ext = path.suffix.lower()
    if ext in (".mp3", ".wav"):
        return path
    if ext != ".m4a":
        raise HeyGenError(f"formato de áudio não suportado: {ext} (use .mp3, .wav ou .m4a)")
    if not shutil.which("ffmpeg"):
        raise HeyGenError("preciso do ffmpeg pra converter .m4a → .mp3 (brew install ffmpeg)")

    dest = Path(tempfile.gettempdir()) / f"{path.stem}_heygen.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(path), "-vn", "-acodec", "libmp3lame", "-b:a", "128k", str(dest)],
        check=True,
        capture_output=True,
    )
    print(f"🔄  {path.name} → {dest.name} (m4a não é aceito no upload)")
    return dest



def _elevenlabs_tts(text: str, voice_id: str) -> Path:
    """Gera o áudio no ElevenLabs (voz profissional) e devolve um .mp3 temporário.

    É o passo que torna o pipeline texto→vídeo automático: ninguém grava nada.
    Cobra caracteres do plano ElevenLabs do usuário (centavos por reel).
    """
    import httpx

    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise HeyGenError("ELEVENLABS_API_KEY não encontrada no .env")
    dest = Path(tempfile.gettempdir()) / "el_tts_heygen.mp3"
    r = httpx.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": key},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.3},
        },
        timeout=120.0,
    )
    if r.status_code != 200:
        raise HeyGenError(f"ElevenLabs TTS → HTTP {r.status_code}: {r.text[:200]}")
    dest.write_bytes(r.content)
    return dest



def _apply_pronuncia(text: str) -> str:
    """Aplica o pronuncia.yaml (termo real → grafia fonética) no texto do TTS.

    Só toca a fala — roteiro e legenda ficam com a grafia verdadeira. Palavra
    inteira, case-insensitive. Termo digitado errado de propósito (piada de
    typo) não está no mapa, então passa intacto.
    """
    import re

    import yaml

    mapa_path = Path(__file__).resolve().parent.parent / "pronuncia.yaml"
    if not mapa_path.exists():
        return text
    mapa = yaml.safe_load(mapa_path.read_text(encoding="utf-8")) or {}
    aplicados = []
    for termo, fala in mapa.items():
        novo = re.sub(rf"\b{re.escape(str(termo))}\b", str(fala), text, flags=re.IGNORECASE)
        if novo != text:
            aplicados.append(termo)
            text = novo
    if aplicados:
        print(f"🔤  pronúncia aplicada: {', '.join(aplicados)}")
    return text


def cmd_avatars(hg: HeyGen, args) -> int:
    avatars = hg.avatars()
    if args.mine:
        avatars = [a for a in avatars if "_" not in a["avatar_id"]]
    seen = set()
    for a in avatars[: args.limit]:
        if a["avatar_id"] in seen:
            continue
        seen.add(a["avatar_id"])
        print(f"{a['avatar_id']}  {a.get('avatar_name')}")
    return 0


def cmd_voices(hg: HeyGen, args) -> int:
    for v in hg.voices(language=args.language)[: args.limit]:
        print(f"{v['voice_id']}  {v.get('name'):<28} {v.get('language'):<12} {v.get('gender')}")
    return 0


def cmd_quota(hg: HeyGen, args) -> int:
    print(f"Créditos restantes: {hg.remaining_quota()}")
    return 0


def cmd_upload(hg: HeyGen, args) -> int:
    path = Path(args.file).expanduser()
    if path.suffix.lower() == ".m4a":
        path = _ensure_uploadable_audio(path)
    asset = hg.upload_asset(path)
    print(f"asset_id: {asset['asset_id']}")
    print(f"mime:     {asset.get('mime_type')}  ({asset.get('size_bytes', 0) / 1024:.0f} KB)")
    return 0


def cmd_generate(hg: HeyGen, args) -> int:
    if not args.audio and not (args.text or args.text_file):
        print("Erro: informe --audio OU --text/--text-file.", file=sys.stderr)
        return 2

    quota = hg.remaining_quota()
    print(f"💳  {quota} crédito(s) antes de gerar")

    audio_asset_id = None
    script = None
    if args.el and (args.text or args.text_file):
        text = (
            Path(args.text_file).expanduser().read_text(encoding="utf-8").strip()
            if args.text_file
            else args.text
        )
        voice = os.environ.get("ELEVENLABS_VOICE_ID")
        if not voice:
            print("Erro: defina ELEVENLABS_VOICE_ID no .env.", file=sys.stderr)
            return 2
        text = _apply_pronuncia(text)
        print(f"🗣  ElevenLabs TTS ({len(text)} chars, voz {voice[:8]}...)")
        if args.dry_run:
            # placeholder com sufixo válido — upload nem roda no dry-run
            args.audio = str(Path(tempfile.gettempdir()) / "el_tts_heygen.mp3")
        else:
            args.audio = str(_elevenlabs_tts(text, voice))
        args.text = args.text_file = None
    if args.audio:
        audio_path = _ensure_uploadable_audio(Path(args.audio).expanduser())
        print(f"⬆️   subindo {audio_path.name}...")
        if not args.dry_run:
            audio_asset_id = hg.upload_asset(audio_path)["asset_id"]
            print(f"    asset_id: {audio_asset_id}")
    else:
        script = (
            Path(args.text_file).expanduser().read_text(encoding="utf-8").strip()
            if args.text_file
            else args.text
        )
        print(f"📝  {len(script)} caracteres (TTS voz {args.voice})")

    print(f"🧑  avatar {args.avatar}")
    print(f"📐  {'9:16' if not args.landscape else '16:9'} · {args.resolution}"
          + (" · legendas queimadas" if args.captions else ""))
    if args.motion:
        print(f"🕺  motion: {args.motion[:60]}...")

    if args.dry_run:
        print("\n[dry-run] nada foi gerado.")
        return 0

    job = hg.create_avatar_video(
        avatar_id=args.avatar,
        audio_asset_id=audio_asset_id,
        script=script,
        voice_id=args.voice if script else None,
        aspect_ratio=ASPECT_LANDSCAPE if args.landscape else ASPECT_PORTRAIT,
        resolution=args.resolution,
        caption=True,
        burn_captions=args.captions,
        background_color=args.background,
        title=args.title,
        motion_prompt=args.motion,
    )
    print(f"\n🚀  video_id: {job.video_id}")

    job = hg.wait(
        job.video_id,
        poll_seconds=args.poll,
        on_tick=lambda j, t: print(f"    [{t:5.0f}s] {j.status}", flush=True),
    )
    print(f"✓   {job.duration or '?'}s de vídeo")

    out = Path(args.output).expanduser()
    if out.is_dir() or not out.suffix:
        out = out / f"{date.today().isoformat()}_{job.video_id[:8]}.mp4"
    hg.download(job, out)
    print(f"💾  {out}  ({out.stat().st_size / 1024 / 1024:.1f} MB)")

    srt = hg.download_subtitles(job, out.with_suffix(".srt"))
    if srt:
        print(f"💾  {srt}")

    print(f"💳  {hg.remaining_quota()} crédito(s) restante(s)")
    return 0


def main() -> None:
    _load_env()

    p = argparse.ArgumentParser(
        prog="heygen-lab",
        description="Laboratório da API v3 do HeyGen: assets, avatares e geração de vídeo.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("avatars", help="Lista avatares")
    pa.add_argument("--mine", action="store_true")
    pa.add_argument("--limit", type=int, default=20)
    pa.set_defaults(func=cmd_avatars)

    pv = sub.add_parser("voices", help="Lista vozes")
    pv.add_argument("--language", default="Portuguese")
    pv.add_argument("--limit", type=int, default=20)
    pv.set_defaults(func=cmd_voices)

    pq = sub.add_parser("quota", help="Créditos restantes")
    pq.set_defaults(func=cmd_quota)

    pu = sub.add_parser("upload", help="Sobe um asset (áudio/imagem) e imprime o asset_id")
    pu.add_argument("file")
    pu.set_defaults(func=cmd_upload)

    pg = sub.add_parser("generate", help="Gera vídeo de avatar (áudio gravado OU texto)")
    pg.add_argument("--motion", default=None, metavar="PROMPT",
                    help="Opcional: prompt de movimento (liga o engine avatar_v). "
                         "Sem a flag, avatar com movimento natural do footage — o padrão.")
    pg.add_argument("--el", action="store_true",
                    help="Gera o áudio da fala no ElevenLabs (ELEVENLABS_VOICE_ID) a partir do texto — pipeline texto→vídeo sem gravar nada")
    pg.add_argument("--audio", default=None, metavar="PATH",
                    help="Áudio gravado (.mp3/.wav/.m4a) — lip-sync na voz real. Exclui --text.")
    pg.add_argument("--text", default=None, help="Texto pro TTS (voz clonada)")
    pg.add_argument("--text-file", default=None, metavar="PATH")
    pg.add_argument("--avatar", default=os.environ.get("HEYGEN_AVATAR_ID"), metavar="ID")
    pg.add_argument("--voice", default=os.environ.get("HEYGEN_VOICE_ID"), metavar="ID",
                    help="Só usado com --text/--text-file")
    pg.add_argument("--captions", action="store_true", help="Queima legendas no vídeo (o .srt sempre vem junto)")
    pg.add_argument("--resolution", default="720p", choices=["720p", "1080p", "4k"])
    pg.add_argument("--landscape", action="store_true")
    pg.add_argument("--background", default=None, metavar="HEX")
    pg.add_argument("--title", default=None)
    pg.add_argument("--output", default="./out", metavar="PATH")
    pg.add_argument("--poll", type=float, default=15.0, metavar="SEC")
    pg.add_argument("--dry-run", action="store_true")
    pg.set_defaults(func=cmd_generate)

    args = p.parse_args()

    if args.cmd == "generate" and not args.avatar:
        print("Erro: informe --avatar ou defina HEYGEN_AVATAR_ID no .env.", file=sys.stderr)
        sys.exit(2)

    try:
        hg = HeyGen()
        sys.exit(args.func(hg, args))
    except HeyGenError as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
