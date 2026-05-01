## Why

O projeto depende do ffmpeg para converter áudio do YouTube para mp3, mas o YouTube serve áudio nativo em webm/opus que o Whisper aceita diretamente. Adicionar `--no-ffmpeg` permite usar o projeto sem ffmpeg instalado.

## What Changes

- Nova flag `--no-ffmpeg` no CLI
- Quando ativa: yt-dlp baixa áudio no formato nativo (webm) sem postprocessors
- Quando inativa: comportamento atual (converte para mp3 via ffmpeg)
- Erro claro se `--no-ffmpeg` + `--api` + áudio > 25MB (chunking requer ffmpeg)

## Capabilities

### New Capabilities

### Modified Capabilities

- `cli-interface`: Nova flag `--no-ffmpeg`
- `audio-download`: Suporte a download sem conversão ffmpeg

## Impact

- **cli.py**: novo argumento `--no-ffmpeg`, validação antes da transcrição
- **downloader.py**: condicional nos postprocessors do yt-dlp
