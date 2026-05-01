## Why

Criar uma ferramenta CLI local para baixar e transcrever vídeos do YouTube, gerando arquivos raw estruturados que sirvam como source of truth para módulos futuros (RAG, geração de conteúdo, Q&A, resumos). O foco deste módulo é exclusivamente capturar e persistir a transcrição — consumir e derivar formatos fica para módulos separados.

## What Changes

- Novo projeto Python do zero (greenfield)
- CLI: `python cli.py <url> --output <dir>`
- Download de áudio via yt-dlp
- Transcrição local via mlx-whisper (otimizado para Apple Silicon M1)
- Flag `--api` para usar OpenAI Whisper API como alternativa
- Output em pasta nomeada `YYYY-MM-DD_titulo-do-video/` dentro do diretório configurável
- Arquivo `raw_whisper.json` como source of truth para módulos downstream

## Capabilities

### New Capabilities

- `audio-download`: Download e extração de áudio de URLs do YouTube via yt-dlp
- `transcription`: Transcrição de áudio para texto com timestamps via mlx-whisper (local M1) ou OpenAI Whisper API (flag `--api`)
- `output-formatting`: Escrita dos arquivos raw de saída (`.txt`, `_timestamps.txt`, `_whisper.json`, `meta.json`)
- `cli-interface`: Interface de linha de comando que orquestra o fluxo completo com flag `--output`

### Modified Capabilities

## Impact

- **Dependências Python**: yt-dlp, mlx-whisper, openai (opcional, só com `--api`), ffmpeg (sistema)
- **Hardware**: Otimizado para Mac Apple Silicon (M1/M2/M3) via mlx-whisper; OpenAI API como fallback
- **Storage**: Áudio temporário baixado + arquivos raw permanentes por vídeo
- **Módulos futuros**: `raw_whisper.json` é o contrato de saída — módulos de RAG, formatação e geração de conteúdo consomem a partir deste arquivo
