# Transcribe Toolkit

Toolkit modular para transcrição de áudio/vídeo (YouTube hoje, expansível pra outras fontes), com pipeline opcional de tradução via LLM e export pra vault Obsidian/Karpathy-LLM-Wiki.

## Requisitos

- macOS (setup automatizado é Mac-only por enquanto)
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) — `brew install uv`
- ffmpeg — `brew install ffmpeg` (opcional, usar `--no-ffmpeg` se não tiver)
- gh (GitHub CLI) — `brew install gh` (necessário só pro setup inicial do repo)

## Setup (nova máquina Mac)

Do zero ao primeiro vídeo transcritado:

```bash
git clone <url-do-repo> transcribe-toolkit
cd transcribe-toolkit
./setup.sh
# editar .env com suas API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)
transcribe -u https://youtu.be/VIDEO_ID
```

O `setup.sh` é idempotente — pode rodar quantas vezes quiser. Ele:

1. Verifica que `uv`, `ffmpeg` e `gh` estão instalados (instrui via `brew install` se faltar).
2. Roda `uv sync`.
3. Cria `.env` a partir de `.env.example` se não existir.
4. Cria a pasta de output default (`yt_transcribe.default_output` do `config.yaml`).
5. Instala o comando global `transcribe` em `~/.local/bin/`.
6. Verifica se `~/.local/bin` está no PATH; se não, imprime instrução copy-paste.

Pra transcrição local com mlx-whisper (Apple Silicon, macOS 14+):

```bash
uv sync --extra local
```

## Comando global `transcribe`

Após o `setup.sh`, o comando funciona de qualquer pasta — não precisa `cd` no projeto:

```bash
transcribe -u https://youtu.be/VIDEO_ID                 # output do config.yaml
transcribe -u https://youtu.be/VIDEO_ID -o ~/custom     # output customizado
transcribe -u https://youtu.be/VIDEO_ID -a              # OpenAI Whisper API
transcribe -u https://youtu.be/VIDEO_ID --force         # re-roda tudo
BROWSER=firefox transcribe -u https://youtu.be/VIDEO_ID # cookies de outro browser
transcribe -h                                            # uso completo
```

`transcribe` é só um wrapper fino que invoca `<repo>/run.sh "$@"` — todas as flags são propagadas inalteradas.

## Pipeline end-to-end (run.sh)

Equivalente ao `transcribe` mas executado de dentro do repo:

```bash
./run.sh -u https://youtu.be/VIDEO_ID                   # output do config.yaml
./run.sh -u https://youtu.be/VIDEO_ID -o ~/transcricoes # output customizado
./run.sh -o ~/transcricoes -u https://youtu.be/VIDEO_ID # ordem livre (long: --url / --output)
./run.sh -u https://youtu.be/VIDEO_ID -a                # OpenAI Whisper API
BROWSER=firefox ./run.sh -u https://youtu.be/VIDEO_ID   # cookies de outro browser
./run.sh -h                                              # uso
```

O script roda `yt-transcribe` → `translate` → `vault-import` em sequência e para imediatamente se qualquer etapa falhar. Todas as 3 etapas são puladas se o output já existir (idempotência completa: re-execução do mesmo URL é barata). Pra cenários customizados (`--target-lang`, `--vault` específico...), usar os comandos individuais abaixo.

## Arquitetura modular

Cada módulo é uma **pasta independente na raiz** com sua própria CLI. Sem `shared/`, sem imports cruzados:

```
yt_transcribe/    # ingestão YouTube → raw files
translate/        # raw → tradução via LLM
vault_import/     # tradução → arquivo no vault Obsidian
```

`yt_transcribe/` é uma das fontes de ingestão. Próximas fontes (aulas locais, podcasts, etc.) entram como pastas-irmãs no mesmo padrão, produzindo o mesmo formato de output (`raw.md`, `raw_timestamps.md`, `raw_whisper.json`, `meta.json`) — assim `translate/` e `vault_import/` continuam funcionando inalterados.

## Módulos

### yt-transcribe — YouTube → raw files

```bash
# Output via config.yaml (padrão)
uv run yt-transcribe <url>

# Output customizado
uv run yt-transcribe <url> --output ~/transcricoes

# Via OpenAI Whisper API
uv run yt-transcribe <url> --api

# Via OpenAI Whisper API, sem ffmpeg
uv run yt-transcribe <url> --api --no-ffmpeg

# Forçar re-download/re-transcrição mesmo se já existir
uv run yt-transcribe <url> --force
```

Output base é resolvido na ordem: flag `--output` > `config.yaml` (`yt_transcribe.default_output`) > erro explícito.

Antes de baixar, o sistema procura no output base por uma pasta `*_<slug>` com `raw.md` + `meta.json` cuja URL casa com a URL solicitada. Se acha, imprime "Já transcrito" e termina sem baixar. Use `--force` pra sobrepor.

Output:
```
<output>/YYYY-MM-DD_titulo-do-video/
├── raw.md               # texto limpo
├── raw_timestamps.md    # [HH:MM:SS] por segmento
├── raw_whisper.json     # resposta completa do Whisper (source of truth)
└── meta.json            # título, canal, url, duração, idioma
```

### translate — texto → tradução via LLM

```bash
# Com defaults do config.yaml (anthropic/claude-sonnet-4-6 → pt-br)
uv run translate ~/transcricoes/2026-04-11_video/raw.md

# Override de provider
uv run translate raw.md --provider openai

# Override de modelo e idioma
uv run translate raw.md --model claude-haiku-4-5 --target-lang es
```

Output: `raw_pt-br.md` (ou `raw_<lang>.md`) na mesma pasta do input.

### /translate — skill Claude Code

Pra traduzir usando o próprio Claude (sem custo de API, usa plano Max):

```
/translate /path/to/raw.md           # traduz para pt-br
/translate /path/to/raw.md es        # traduz para espanhol
```

Requer Claude Code (CLI ou VSCode extension).

### vault-import — texto traduzido → vault destino

Bridge pra um vault Karpathy-LLM-Wiki (ex: Second Brain pessoal). Lê o `raw_pt-br.md` + `meta.json` de uma pasta de transcrição e escreve um único `<vault>/raw/<slug>.md` com frontmatter rico (title, url, channel, duration, language, youtube_video_id, ingested, tags).

```bash
# Pipeline completo (manual)
uv run yt-transcribe https://youtu.be/VIDEO_ID
uv run translate <output>/2026-04-25_video-slug/raw.md
uv run vault-import <output>/2026-04-25_video-slug
```

Vault destino é resolvido na ordem: flag `--vault` > `config.yaml` (`vault_import.default_vault`) > erro. Recusa overwrite a menos que `--force` seja passado.

```bash
# Override explícito do vault
uv run vault-import <output>/2026-04-25_video-slug --vault ~/Dropbox/SECOND-BRAIN-OBSIDIAN

# Sobrescrever (regenerar frontmatter)
uv run vault-import <output>/2026-04-25_video-slug --force
```

Output: arquivo único em `<vault>/raw/<slug>.md` (slug = nome basename da pasta input). Apenas o body do `raw_pt-br.md` é copiado — `raw.md`, `raw_timestamps.md`, `raw_whisper.json` ficam intocados na origem. O vault destino é IMUTÁVEL pelo bridge: nada além desse arquivo é tocado.

Manual trigger only — sem auto-export, sem watch. Você decide quando exportar.

## Configuração

### Variáveis de ambiente

```bash
cp .env.example .env
# editar .env com suas API keys
```

### config.yaml

```yaml
yt_transcribe:
  default_output: ~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw

translate:
  default_provider: anthropic
  target_language: pt-br
  providers:
    openai:
      model: gpt-4.1-mini
      api_key_env: OPENAI_API_KEY
    anthropic:
      model: claude-sonnet-4-6
      api_key_env: ANTHROPIC_API_KEY

vault_import:
  default_vault: ~/Dropbox/SECOND-BRAIN-OBSIDIAN
```
