"""Cliente da API do HeyGen — **v3**.

Escopo: subir asset (áudio/imagem), gerar vídeo de avatar (TTS **ou** lip-sync
em áudio gravado), montar vídeo multi-cena, acompanhar e baixar.

AIDEV-NOTE: nasceu em /v2 e foi migrado. O v2 responde com o aviso
"Legacy … will be removed on 2026-10-31 … If you are an AI agent or LLM, do not
use it". Não voltar pro v2. Diferenças que motivaram a migração:
  - v2: POST /v2/video/generate, status em GET /v1/video_status.get
  - v3: POST /v3/videos,          status em GET /v3/videos/{id}
  - v3 tem `caption`, `background.asset_id` e o tipo `studio` (multi-cena)

Autenticação: header `X-Api-Key` (HEYGEN_API_KEY no .env).

Consumo: ~1,02 crédito por segundo de vídeo renderizado — medido, não
documentado. Um teste de 15s custa ~15 créditos. Job criado e deletado antes de
renderizar não cobra.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

BASE = "https://api.heygen.com"

ASPECT_PORTRAIT = "9:16"  # reels/stories
ASPECT_SQUARE = "1:1"
ASPECT_LANDSCAPE = "16:9"

AUDIO_EXTS = {".mp3", ".wav", ".m4a"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
MAX_ASSET_MB = 32  # limite documentado do POST /v3/assets

MIME_BY_EXT = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".mp4": "video/mp4",
    ".srt": "application/x-subrip",
}


class HeyGenError(Exception):
    """Falha de chamada à API, de upload ou de renderização."""


@dataclass
class VideoJob:
    video_id: str
    status: str = "pending"
    video_url: str | None = None
    subtitle_url: str | None = None
    thumbnail_url: str | None = None
    video_page_url: str | None = None
    duration: float | None = None
    error: str | None = None
    raw: dict = field(default_factory=dict)

    @property
    def done(self) -> bool:
        return self.status in ("completed", "failed")


def api_key() -> str:
    key = os.environ.get("HEYGEN_API_KEY")
    if not key:
        raise HeyGenError(
            "HEYGEN_API_KEY não encontrada.\n"
            "→ Copie .env.example para .env e preencha com a chave de "
            "https://app.heygen.com/settings (aba API)."
        )
    return key


class HeyGen:
    def __init__(self, key: str | None = None, timeout: float = 60.0):
        self._key = key or api_key()
        self._timeout = timeout

    # ── plumbing ──────────────────────────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs) -> dict:
        headers = {"X-Api-Key": self._key, "Accept": "application/json"}
        headers.update(kwargs.pop("headers", {}))
        timeout = kwargs.pop("timeout", self._timeout)
        try:
            r = httpx.request(method, f"{BASE}{path}", headers=headers, timeout=timeout, **kwargs)
        except httpx.HTTPError as e:
            raise HeyGenError(f"{method} {path} falhou: {type(e).__name__}: {e}") from e

        try:
            body = r.json()
        except ValueError:
            if r.status_code >= 400:
                raise HeyGenError(f"{method} {path} → HTTP {r.status_code}: {r.text[:300]}") from None
            raise HeyGenError(f"{method} {path} devolveu resposta não-JSON: {r.text[:200]}") from None

        # O v3 sinaliza erro no campo `error` mesmo com HTTP 200 em alguns casos,
        # e com corpo {"error": {...}} nos 4xx. Cobrimos as duas formas.
        err = body.get("error")
        if err:
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise HeyGenError(f"{method} {path} → {msg}")
        if r.status_code >= 400:
            raise HeyGenError(f"{method} {path} → HTTP {r.status_code}: {r.text[:300]}")

        return body.get("data", body)

    # ── assets ────────────────────────────────────────────────────────────────

    def upload_asset(self, path: Path) -> dict:
        """Sobe um arquivo e devolve o dict do asset (`asset_id`, `url`, ...).

        POST /v3/assets, multipart, campo `file`. Aceita png/jpeg/mp4/webm/
        mp3/wav/pdf/srt, até 32 MB.
        """
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise HeyGenError(f"arquivo não encontrado: {path}")

        size_mb = path.stat().st_size / 1024 / 1024
        if size_mb > MAX_ASSET_MB:
            raise HeyGenError(
                f"{path.name} tem {size_mb:.1f} MB — o limite do upload é {MAX_ASSET_MB} MB."
            )

        mime = MIME_BY_EXT.get(path.suffix.lower(), "application/octet-stream")
        with open(path, "rb") as f:
            data = self._request(
                "POST",
                "/v3/assets",
                files={"file": (path.name, f, mime)},
                timeout=300.0,
            )
        if not data.get("asset_id"):
            raise HeyGenError(f"upload sem asset_id: {data}")
        return data

    # ── consulta ──────────────────────────────────────────────────────────────

    def avatars(self) -> list[dict]:
        return self._request("GET", "/v2/avatars").get("avatars", [])

    def voices(self, language: str | None = None) -> list[dict]:
        vs = self._request("GET", "/v2/voices").get("voices", [])
        if language:
            needle = language.lower()
            vs = [v for v in vs if needle in str(v.get("language", "")).lower()]
        return vs

    def remaining_quota(self) -> int:
        return self._request("GET", "/v2/user/remaining_quota").get("remaining_quota", 0)

    def list_videos(self) -> list[dict]:
        data = self._request("GET", "/v3/videos")
        return data if isinstance(data, list) else data.get("videos", [])

    def delete(self, video_id: str) -> None:
        """Remove um vídeo. Job deletado antes de renderizar não consome crédito."""
        self._request("DELETE", f"/v3/videos/{video_id}")

    # ── geração ───────────────────────────────────────────────────────────────

    @staticmethod
    def _caption_block(burn_in: bool) -> dict:
        """`file_format` sempre srt. Sem `style`, a legenda vem só como sidecar
        (`subtitle_url`); com `style`, é queimada na imagem."""
        block: dict = {"file_format": "srt"}
        if burn_in:
            block["style"] = "default"
        return block

    @staticmethod
    def _background_block(color: str | None, image_url: str | None, image_asset_id: str | None) -> dict | None:
        if image_asset_id:
            return {"type": "image", "asset_id": image_asset_id}
        if image_url:
            return {"type": "image", "url": image_url}
        if color:
            return {"type": "color", "value": color}
        return None

    def create_avatar_video(
        self,
        avatar_id: str,
        *,
        audio_asset_id: str | None = None,
        audio_url: str | None = None,
        script: str | None = None,
        voice_id: str | None = None,
        aspect_ratio: str = ASPECT_PORTRAIT,
        resolution: str = "720p",
        caption: bool | None = None,
        burn_captions: bool = False,
        background_color: str | None = None,
        background_image_url: str | None = None,
        background_image_asset_id: str | None = None,
        title: str | None = None,
        motion_prompt: str | None = None,
    ) -> VideoJob:
        """Cena única com avatar.

        A fala vem de UM dos dois caminhos, nunca dos dois (a API rejeita):
          - **áudio gravado** → `audio_asset_id` ou `audio_url` (lip-sync na voz real)
          - **TTS**           → `script` + `voice_id`
        """
        has_audio = bool(audio_asset_id or audio_url)
        has_script = bool(script)
        if has_audio and has_script:
            raise HeyGenError(
                "áudio e script são mutuamente exclusivos — escolha lip-sync (áudio) OU TTS (script+voice_id)."
            )
        if not has_audio and not has_script:
            raise HeyGenError("informe áudio (audio_asset_id/audio_url) ou script+voice_id.")
        if has_script and not voice_id:
            raise HeyGenError("script exige voice_id.")

        payload: dict = {
            "type": "avatar",
            "avatar_id": avatar_id,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }
        if audio_asset_id:
            payload["audio_asset_id"] = audio_asset_id
        elif audio_url:
            payload["audio_url"] = audio_url
        else:
            payload["script"] = script
            payload["voice_id"] = voice_id

        if caption or burn_captions:
            payload["caption"] = self._caption_block(burn_captions)

        bg = self._background_block(background_color, background_image_url, background_image_asset_id)
        if bg:
            payload["background"] = bg
        if title:
            payload["title"] = title
        if motion_prompt:
            # motion_prompt em digital twin de vídeo só roda no engine avatar_v
            # (no IV a API rejeita). Veredito do usuário 2026-08-15: o resultado
            # do motion NÃO convenceu — fica opt-in, nunca default.
            payload["engine"] = {"type": "avatar_v"}
            payload["motion_prompt"] = motion_prompt

        return self._create(payload)

    def create_studio_video(
        self,
        scenes: list[dict],
        *,
        aspect_ratio: str = ASPECT_PORTRAIT,
        resolution: str = "720p",
        caption: bool | None = None,
        burn_captions: bool = False,
        title: str | None = None,
    ) -> VideoJob:
        """Vídeo multi-cena (1 a 50). Cada cena é `avatar_video`, `image` ou `video`.

        É o que permite intercalar você falando com o flyer na tela:
            [avatar_video(hook), image(flyer A), image(flyer B), avatar_video(fecho)]
        """
        if not scenes:
            raise HeyGenError("studio exige ao menos 1 cena.")
        if len(scenes) > 50:
            raise HeyGenError(f"studio aceita no máximo 50 cenas (recebi {len(scenes)}).")

        payload: dict = {
            "type": "studio",
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "scenes": scenes,
        }
        if caption or burn_captions:
            payload["caption"] = self._caption_block(burn_captions)
        if title:
            payload["title"] = title
        return self._create(payload)

    @staticmethod
    def scene_avatar(
        avatar_id: str,
        *,
        audio_asset_id: str | None = None,
        script: str | None = None,
        voice_id: str | None = None,
    ) -> dict:
        inp: dict = {"type": "avatar", "avatar_id": avatar_id}
        if audio_asset_id:
            inp["audio_asset_id"] = audio_asset_id
        else:
            inp["script"] = script
            inp["voice_id"] = voice_id
        return {"type": "avatar_video", "input": inp}

    @staticmethod
    def scene_image(*, asset_id: str | None = None, url: str | None = None, duration: float = 3.0) -> dict:
        source = {"type": "asset", "asset_id": asset_id} if asset_id else {"type": "url", "url": url}
        return {"type": "image", "source": source, "duration": duration}

    def _create(self, payload: dict) -> VideoJob:
        data = self._request("POST", "/v3/videos", json=payload)
        video_id = data.get("id") or data.get("video_id")
        if not video_id:
            raise HeyGenError(f"resposta sem id de vídeo: {data}")
        return VideoJob(video_id=video_id, status=data.get("status", "processing"), raw=data)

    # ── status / espera ───────────────────────────────────────────────────────

    def status(self, video_id: str) -> VideoJob:
        d = self._request("GET", f"/v3/videos/{video_id}")
        return VideoJob(
            video_id=d.get("id", video_id),
            status=d.get("status", "unknown"),
            video_url=d.get("video_url"),
            subtitle_url=d.get("subtitle_url"),
            thumbnail_url=d.get("thumbnail_url"),
            video_page_url=d.get("video_page_url"),
            duration=d.get("duration"),
            error=str(d["error"]) if d.get("error") else None,
            raw=d,
        )

    def wait(
        self,
        video_id: str,
        poll_seconds: float = 10.0,
        timeout_seconds: float = 1800.0,
        on_tick=None,
    ) -> VideoJob:
        started = time.monotonic()
        while True:
            job = self.status(video_id)
            if on_tick:
                on_tick(job, time.monotonic() - started)
            if job.status == "completed":
                return job
            if job.status == "failed":
                raise HeyGenError(f"renderização falhou: {job.error or 'sem detalhe'}")
            if time.monotonic() - started > timeout_seconds:
                raise HeyGenError(
                    f"vídeo {video_id} não terminou em {timeout_seconds:.0f}s (último status: {job.status})"
                )
            time.sleep(poll_seconds)

    # ── download ──────────────────────────────────────────────────────────────

    def download(self, job: VideoJob, dest: Path) -> Path:
        """Baixa o .mp4. A URL do HeyGen é temporária — baixe logo após o `wait`."""
        if not job.video_url:
            raise HeyGenError(f"job {job.video_id} não tem video_url (status={job.status})")
        return self._download_url(job.video_url, Path(dest))

    def download_subtitles(self, job: VideoJob, dest: Path) -> Path | None:
        if not job.subtitle_url:
            return None
        return self._download_url(job.subtitle_url, Path(dest))

    @staticmethod
    def _download_url(url: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=300.0) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=1 << 16):
                        f.write(chunk)
        except httpx.HTTPError as e:
            tmp.unlink(missing_ok=True)
            raise HeyGenError(f"download falhou: {type(e).__name__}: {e}") from e

        if tmp.stat().st_size == 0:
            tmp.unlink(missing_ok=True)
            raise HeyGenError("download veio vazio")
        tmp.replace(dest)
        return dest
