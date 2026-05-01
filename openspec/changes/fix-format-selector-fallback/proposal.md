## Why

O YouTube passou a exigir resolução de "n challenge" (JS) para entregar o seletor genérico `bestaudio/best`. Sem um JS runtime configurado, o yt-dlp falha com "Requested format is not available" mesmo em vídeos acessíveis. Pedir explicitamente um formato audio-only comum (m4a/itag 140) contorna o challenge e funciona de imediato.

## What Changes

- Trocar o format selector do downloader de `"bestaudio/best"` para uma cadeia com fallback robusto que prioriza formatos audio-only conhecidos (`bestaudio[ext=m4a]/140/251/bestaudio/best`).
- Forçar `player_client=["android_vr"]` via `extractor_args` para evitar clientes (tv/web_creator) que exigem resolução de n-challenge JS para expor formatos audio-only.

## Capabilities

### Modified Capabilities
- `audio-download`: requisito de seleção de formato passa a usar cadeia de fallback.

## Impact

- Código: `yt_transcribe/downloader.py` (uma linha).
- Dependências: nenhuma.
- Sem mudança de CLI.
