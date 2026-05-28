# Transcribe Toolkit

Toolkit modular para transcrição de áudio/vídeo (YouTube e arquivos locais), com pipeline opcional de tradução via LLM e export opcional pra vault Obsidian/Karpathy-LLM-Wiki.

## Quick Start

```bash
git clone https://github.com/robertsilvatech/transcribe-toolkit.git
cd transcribe-toolkit
./setup.sh

# 1) Edite as API keys (necessário pra modo --api e pro translate)
$EDITOR .env

# 2) (opcional) ajuste os paths de output
$EDITOR config.yaml

# 3) Primeiro vídeo:
transcribe -u https://youtu.be/VIDEO_ID

# 4) Primeira aula local:
transcribe-local -f /caminho/aula.mp4
```

Saída: `raw.md` (texto), `raw_timestamps.md`, `raw_whisper.json`, `meta.json`, e — se `translate` rodar — `raw_pt-br.md`.

## Compatibilidade

| Plataforma | Modo local (mlx-whisper) | Modo `--api` (OpenAI Whisper) | Setup automatizado |
|---|---|---|---|
| **Mac Apple Silicon** (M1/M2/M3/M4) | ✅ | ✅ | ✅ `./setup.sh` |
| **Mac Intel** | ❌ (mlx requer Apple Silicon) | ✅ | ✅ `./setup.sh` |
| **Linux** | ❌ (mlx é macOS-only) | ✅ | ✅ `./setup.sh` (detecta OS, sugere apt/dnf) |
| **Windows** | ❌ | ✅ (via WSL) | Use WSL + setup.sh |

Modo local (mlx-whisper) é gratuito mas exige Apple Silicon. Modo API funciona em qualquer máquina com Python 3.13+ mas cobra por uso.

## Costs & Privacy

**Custos das APIs** (você paga direto pra cada provider):

- **OpenAI Whisper API** (`--api`): cobrança por minuto de áudio. Veja [pricing](https://openai.com/api/pricing/).
- **OpenAI ou Anthropic** (no `translate`): cobrança por token. Veja [OpenAI pricing](https://openai.com/api/pricing/) ou [Anthropic pricing](https://www.anthropic.com/pricing#anthropic-api).

Modo local (mlx-whisper) é gratuito após instalação.

**Privacidade — dados enviados pra terceiros:**

- `--api`: o **áudio inteiro** é enviado pra OpenAI Whisper.
- `translate`: o **texto transcrito** é enviado pro provider escolhido (Anthropic por padrão, OpenAI opcional).
- Modo local (mlx-whisper) processa 100% offline.

Se o conteúdo é sensível, prefira modo local; se for usar APIs, leia as policies do provider.

## Requisitos

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) — `brew install uv` (Mac) ou via [instaladores](https://docs.astral.sh/uv/getting-started/installation/) (Linux)
- ffmpeg — `brew install ffmpeg` (Mac) ou `apt install ffmpeg` (Linux). Opcional pro YouTube (use `--no-ffmpeg`), obrigatório pra local-transcribe processar `.mp4`/`.mov`/`.mkv`.
- gh (GitHub CLI) — opcional, apenas se quiser clonar via `gh repo clone`

Pra transcrição local com mlx-whisper (Apple Silicon, macOS 14+):

```bash
uv sync --extra local
```

## Setup (qualquer máquina)

```bash
git clone https://github.com/robertsilvatech/transcribe-toolkit.git
cd transcribe-toolkit
./setup.sh
```

O `setup.sh` é idempotente — pode rodar quantas vezes quiser. Ele:

1. Copia `config.yaml.example` → `config.yaml` se não existir.
2. Verifica que `uv`, `ffmpeg` e `gh` estão instalados (sugere `brew install` no Mac, `apt`/`dnf`/`pacman` no Linux).
3. Roda `uv sync`.
4. Cria `.env` a partir de `.env.example` se não existir.
5. Cria as pastas de output default (paths do `config.yaml`).
6. Instala os comandos globais `transcribe` e `transcribe-local` em `~/.local/bin/`.
7. Verifica se `~/.local/bin` está no PATH; se não, imprime instrução copy-paste.

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

**Vault opcional:** se `vault_import.default_vault` (ou env var `VAULT_PATH`) não estiver configurado, o `transcribe` roda só `yt-transcribe → translate` e pula `vault-import` com aviso. Pra ativar a etapa 3, configure o vault.

## Comando global `transcribe-local`

Pra arquivos de mídia que você já tem localmente (aulas gravadas, vídeos próprios, podcasts baixados):

```bash
transcribe-local -f aula01.mp4                                # arquivo único
transcribe-local -f aula01.mp4 -f aula02.mp4                  # múltiplos
transcribe-local --dir ~/curso -s nome-do-curso               # batch recursivo
transcribe-local -f aula01.mp4 -a                             # OpenAI Whisper API
transcribe-local --dir ~/curso --force                        # re-roda transcribe + translate
transcribe-local -h                                            # uso completo
```

Extensões aceitas: `.mp4`, `.mov`, `.mkv`, `.m4a`, `.mp3`, `.wav`. Vídeos têm o `.mp3` extraído via ffmpeg ao lado do source (cacheado). Pipeline: `local-transcribe → translate`. **Não invoca `vault-import`** (suporte a fontes locais no vault é deferred).

`transcribe-local` é um wrapper fino que invoca `<repo>/run-local.sh "$@"`.

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

O script roda `yt-transcribe` → `translate` → `vault-import` (esta última só se vault configurado) e para imediatamente se qualquer etapa falhar. Etapas com output existente são puladas (idempotência completa: re-execução do mesmo URL é barata). Pra cenários customizados (`--target-lang`, etc.), usar os comandos individuais abaixo.

## Arquitetura modular

Módulos **ingestores** (`yt_transcribe`, `local_transcribe`) são pastas independentes na raiz com sua própria CLI. Eles compartilham lógica de transcrição/formatação via `transcribe_core/`.

```
transcribe_core/   # núcleo compartilhado: transcribe(), save_outputs(), slugify()
yt_transcribe/     # ingestão YouTube → raw files
local_transcribe/  # ingestão arquivos locais (.mp4/.mov/.mkv/.m4a/.mp3/.wav) → raw files
translate/         # raw → tradução via LLM
vault_import/      # tradução → arquivo no vault Obsidian (YouTube-only)
```

Os ingestores produzem o mesmo formato de output (`raw.md`, `raw_timestamps.md`, `raw_whisper.json`, `meta.json`) — assim `translate/` funciona para qualquer fonte. O `meta.json` traz um campo `source` (`"youtube"` ou `"local"`) para que readers downstream possam diferenciar.

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

Output base é resolvido na ordem: flag `--output` > env var `YT_TRANSCRIBE_OUTPUT` > `config.yaml` (`yt_transcribe.default_output`) > erro explícito.

Antes de baixar, o sistema procura no output base por uma pasta `*_<slug>` com `raw.md` + `meta.json` cuja URL casa com a URL solicitada. Se acha, imprime "Já transcrito" e termina sem baixar. Use `--force` pra sobrepor.

Output:
```
<output>/YYYY-MM-DD_titulo-do-video/
├── raw.md               # texto limpo
├── raw_timestamps.md    # [HH:MM:SS] por segmento
├── raw_whisper.json     # resposta completa do Whisper (source of truth)
└── meta.json            # source=youtube, título, canal, url, duração, idioma
```

### local-transcribe — arquivos de mídia locais → raw files

```bash
# Arquivo único
uv run local-transcribe aula01.mp4

# Batch posicional (ou via shell glob)
uv run local-transcribe aula01.mp4 aula02.mp4
uv run local-transcribe ./curso/*.mp4

# Diretório recursivo + subpasta espelhando árvore do source
uv run local-transcribe --dir ~/curso --subfolder curso-x

# Via OpenAI Whisper API
uv run local-transcribe aula01.mp4 --api

# Forçar re-transcrição (não re-extrai .mp3)
uv run local-transcribe aula01.mp4 --force
```

Extensões aceitas: `.mp4`, `.mov`, `.mkv` (vídeo, extrai áudio via ffmpeg), `.m4a`, `.mp3`, `.wav` (áudio, sem extração). Output base resolvido na ordem: flag `--output` > env var `LOCAL_TRANSCRIBE_OUTPUT` > `config.yaml` (`local_transcribe.default_output`) > erro explícito.

Áudio extraído fica como `.mp3` sibling do source (ex: `aula01.mp4` → `aula01.mp3`). Cacheado: se `.mp3` já existe, reusa sem invocar ffmpeg. `--force` re-transcreve mas NÃO re-extrai. Pasta de source read-only → erro claro (sem fallback automático para /tmp).

Skip automático: procura subpasta `*_<slug>/meta.json` cujo `source_path` casa com o caminho absoluto do arquivo. Use `--force` pra ignorar.

Output:
```
<output>/[<subfolder>/]<rel-path>/YYYY-MM-DD_slug/
├── raw.md
├── raw_timestamps.md
├── raw_whisper.json
└── meta.json            # source=local, source_path, título, duração, idioma
```

Em modo `--dir`, `<rel-path>` espelha a estrutura do diretório varrido.

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

Pra traduzir usando o próprio Claude (sem custo de API se você tem plano Max):

```
/translate /path/to/raw.md           # traduz para pt-br
/translate /path/to/raw.md es        # traduz para espanhol
```

Requer Claude Code (CLI ou VSCode extension).

### vault-import — texto traduzido → vault destino (opcional)

Bridge opcional pra um vault Karpathy-LLM-Wiki (Second Brain pessoal em Obsidian, por exemplo). Lê o `raw_pt-br.md` + `meta.json` de uma pasta de transcrição e escreve um único `<vault>/raw/<slug>.md` com frontmatter rico (title, url, channel, duration, language, youtube_video_id, ingested, tags).

```bash
# Pipeline completo (manual)
uv run yt-transcribe https://youtu.be/VIDEO_ID
uv run translate <output>/2026-04-25_video-slug/raw.md
uv run vault-import <output>/2026-04-25_video-slug
```

Vault destino é resolvido na ordem: flag `--vault` > env var `VAULT_PATH` > `config.yaml` (`vault_import.default_vault`) > erro. Recusa overwrite a menos que `--force` seja passado.

```bash
# Override explícito do vault
uv run vault-import <output>/2026-04-25_video-slug --vault ~/Documents/my-vault

# Sobrescrever (regenerar frontmatter)
uv run vault-import <output>/2026-04-25_video-slug --force
```

Output: arquivo único em `<vault>/raw/<slug>.md` (slug = nome basename da pasta input). Apenas o body do `raw_pt-br.md` é copiado — `raw.md`, `raw_timestamps.md`, `raw_whisper.json` ficam intocados na origem. O vault destino é IMUTÁVEL pelo bridge: nada além desse arquivo é tocado.

Manual trigger only — sem auto-export, sem watch. Você decide quando exportar.

**Vault desabilitado:** se você não usa Obsidian/vault, simplesmente deixe `vault_import.default_vault: null` no `config.yaml` (default do `config.yaml.example`). O `transcribe` e o `transcribe-local` continuam funcionando — apenas pulam a etapa 3.

## Configuração

### Cascata de resolução de paths

Pra cada path configurável, a ordem de precedência é:

```
CLI flag > env var > config.yaml > erro
```

Env vars suportadas:

| Variável | Override de |
|---|---|
| `YT_TRANSCRIBE_OUTPUT` | `yt_transcribe.default_output` |
| `LOCAL_TRANSCRIBE_OUTPUT` | `local_transcribe.default_output` |
| `VAULT_PATH` | `vault_import.default_vault` |

Útil pra CI, scripts, ou setups multi-projeto.

### Variáveis de ambiente (API keys)

```bash
cp .env.example .env
# editar .env com suas API keys
```

### config.yaml

Copie o template e edite:

```bash
cp config.yaml.example config.yaml
$EDITOR config.yaml
```

Estrutura:

```yaml
yt_transcribe:
  default_output: ~/Documents/transcribe-toolkit/youtube

local_transcribe:
  default_output: ~/Documents/transcribe-toolkit/local

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

# Opcional: deixe null pra desabilitar vault-import
vault_import:
  default_vault: null
```

## License

[MIT](LICENSE) — Robert Silva
