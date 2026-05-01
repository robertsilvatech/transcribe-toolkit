## Context

Projeto greenfield. Não há código existente neste repositório. Existe um projeto anterior (`transcribe-class`) com lógica de transcrição e formatação em notebooks/utils, mas a arquitetura era voltada para cursos com estrutura de módulo/aula. O novo projeto é independente, focado em YouTube, com saída configurável e estrutura modular pensada para consumo por módulos downstream.

Hardware alvo: Mac Apple Silicon M1 Air.

## Goals / Non-Goals

**Goals:**
- CLI simples: `python cli.py <url> --output <dir>`
- Download de áudio de URLs do YouTube via yt-dlp
- Transcrição com mlx-whisper (local, otimizado M1) como padrão
- Flag `--api` para usar OpenAI Whisper API como alternativa
- Salvar 4 arquivos raw em `<output>/YYYY-MM-DD_titulo-do-video/`
- `raw_whisper.json` como source of truth para módulos futuros

**Non-Goals:**
- Consumir ou derivar formatos a partir de `raw_whisper.json` (módulo futuro)
- RAG, chunking, embeddings, geração de conteúdo (módulos futuros)
- Interface web ou GUI
- Processamento em batch de múltiplas URLs
- Suporte a outras fontes além do YouTube

## Decisions

### 1. mlx-whisper como engine padrão

**Decisão:** mlx-whisper local como padrão, OpenAI Whisper API via `--api`.

**Rationale:** mlx-whisper é otimizado para Apple Silicon via Metal Performance Shaders, roda em ~1x realtime no M1 com modelo `medium`. É gratuito, privado (áudio não sai da máquina) e sem limite de tamanho de arquivo. A API OpenAI tem limite de 25MB e custo por minuto — útil como fallback mas não como padrão.

**Alternativas consideradas:**
- `openai-whisper` (CPU puro): muito lento no M1 Air sem GPU NVIDIA
- `faster-whisper`: boa opção, mas mlx-whisper tem integração nativa com Apple Neural Engine

### 2. yt-dlp para download

**Decisão:** yt-dlp extrai apenas o áudio (sem baixar vídeo completo).

**Rationale:** yt-dlp é o padrão da indústria para download de YouTube, mantido ativamente, suporta extração de áudio direto como `.mp3`/`.m4a`. Evita baixar vídeo completo (GB desnecessários). Também provê metadata (título, canal, duração) em uma única chamada.

**Alternativas consideradas:**
- `pytube`: menos mantido, quebra com frequência em mudanças da API do YouTube

### 3. Chunking automático para flag --api

**Decisão:** quando `--api` é usado, dividir áudio em chunks de <25MB antes de enviar.

**Rationale:** OpenAI Whisper API tem limite hard de 25MB. Compressão de áudio de speech a 32kbps mono dá ~14MB/hora — a maioria dos vídeos passa direto, mas chunking automático garante funcionamento para vídeos longos sem intervenção manual.

**Reutilização:** lógica de `split_audio_to_chunks()` do projeto `transcribe-class` pode ser portada.

### 4. raw_whisper.json como contrato de saída

**Decisão:** salvar a resposta completa do Whisper (verbose JSON com segments) como arquivo primário.

**Rationale:** o JSON verbose do Whisper contém tudo: texto, timestamps por segmento (start/end), idioma detectado, confidence. Qualquer formato derivado (SRT, JSONL chunks, markdown) pode ser gerado a partir deste arquivo sem retranscrever. Isso mantém este módulo simples e os módulos downstream independentes.

### 5. Estrutura de diretório configurável via --output

**Decisão:** flag `--output` obrigatória que define o diretório base. Subpasta criada automaticamente como `YYYY-MM-DD_titulo-do-video/`.

**Rationale:** o usuário define onde salvar (ex: `~/transcricoes`, `~/Dropbox/transcricoes`). O slug do título é gerado a partir do título do vídeo (lowercase, sem acentos, espaços → hífens). Data prefixada para ordenação cronológica natural.

## Risks / Trade-offs

- **mlx-whisper não disponível** → Mitigation: verificar instalação no startup e sugerir `--api` se não encontrado
- **Título do vídeo com caracteres especiais** → Mitigation: sanitizar slug (remover acentos, limitar a 60 chars, substituir caracteres inválidos por hífen)
- **Áudio temporário não limpo em caso de erro** → Mitigation: usar `try/finally` para garantir cleanup do arquivo temporário
- **Vídeo privado ou indisponível** → Mitigation: capturar erro do yt-dlp e exibir mensagem clara ao usuário
- **M1 Air pode throttle térmico em vídeos muito longos** → Trade-off aceito: usuário pode usar `--api` nesses casos

## Open Questions

- Manter áudio temporário (`.mp3`) ou deletar após transcrição? Por ora: deletar.
- Modelo padrão do mlx-whisper: `medium` ou `large-v3`? `medium` é mais rápido no Air, `large` mais preciso. Expor como flag `--model`?
