## Why

YouTube bloqueia downloads anônimos de vários vídeos (não listados, restritos por idade, ou aleatoriamente via anti-bot) com o erro "Sign in to confirm you're not a bot". Hoje o `yt_transcribe` falha nesses casos sem oferecer saída. O yt-dlp suporta nativamente `--cookies-from-browser`, então expor isso na CLI resolve o problema sem complexidade adicional.

## What Changes

- Adicionar flag `--cookies-from-browser <browser>` à CLI do `yt_transcribe` (ex: `chrome`, `firefox`, `safari`, `brave`).
- Passar o valor diretamente para o yt-dlp via opção `cookiesfrombrowser` do Python API.
- Documentar no AGENT.md quando usar a flag (erro de bot-check).

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `audio-download`: aceitar fonte de cookies de browser opcional para autenticar no YouTube.
- `cli-interface`: expor a nova flag `--cookies-from-browser`.

## Impact

- Código: `yt_transcribe/cli.py` (nova flag), `yt_transcribe/downloader.py` (repassar para yt-dlp).
- Dependências: nenhuma nova — yt-dlp já suporta.
- Docs: AGENT.md ganha exemplo de uso.
