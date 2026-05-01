# Transcribe Toolkit

Projeto modular para transcrição e processamento de vídeos do YouTube para uso com LLMs.

## Arquitetura modular

Cada módulo é uma **pasta independente na raiz** com sua própria CLI. Módulos não dependem uns dos outros.

```
yt_transcribe/     # módulo 1: YouTube → raw files
├── cli.py
├── downloader.py
├── transcriber.py
└── formatter.py

translate/         # módulo 2: texto → tradução via LLM
├── cli.py
├── config.py
└── translator.py

vault_import/      # módulo 3: pasta transcrita → vault destino (bridge)
├── cli.py
├── config.py
└── importer.py

config.yaml        # config do projeto, cada módulo lê sua seção
pyproject.toml     # entry points pra todos os módulos
```

## Regra fundamental

**Antes de adicionar qualquer feature, perguntar: isso pertence a um módulo existente ou é um módulo novo?**

- Se a feature é sobre download/transcrição de YouTube → `yt_transcribe/`
- Se a feature é sobre tradução de texto → `translate/`
- Se a feature é sobre exportar transcrições para um vault Karpathy-LLM-Wiki → `vault_import/`
- Se a feature é algo diferente (insights, RAG, Q&A) → criar nova pasta na raiz

## Módulos

### yt_transcribe

```bash
uv run yt-transcribe <url> --output <dir>
uv run yt-transcribe <url> --output <dir> --api        # via OpenAI Whisper API
uv run yt-transcribe <url> --output <dir> --no-ffmpeg   # sem ffmpeg
uv run yt-transcribe <url> --output <dir> --cookies-from-browser chrome   # vídeos não listados / bot-check
uv run yt-transcribe <url> --output <dir> --force       # ignora skip e re-baixa/re-transcreve
```

Use `--cookies-from-browser <browser>` quando o yt-dlp retornar "Sign in to confirm you're not a bot" (comum em vídeos não listados ou com restrição). Valores aceitos: `chrome`, `firefox`, `safari`, `brave`, `edge`, etc.

Skip automático: antes de baixar, o sistema procura em `<dir>` por uma pasta `*_<slug>` (qualquer data) com `raw.md` + `meta.json` cuja `url` casa com a URL solicitada. Se acha, imprime "Já transcrito" e termina sem baixar. Use `--force` para sobrepor.

Output:
```
<dir>/YYYY-MM-DD_slug/
├── raw.md               # texto limpo
├── raw_timestamps.md    # [HH:MM:SS] por segmento
├── raw_whisper.json     # resposta completa do Whisper (source of truth)
└── meta.json            # title, channel, url, duration, language
```

### translate

```bash
uv run translate raw.md                               # usa config.yaml defaults
uv run translate raw.md --provider openai              # override provider
uv run translate raw.md --model claude-haiku-4-5       # override modelo
uv run translate raw.md --target-lang es               # override idioma
```

Output: `raw_<lang>.md` na mesma pasta do input.

Config em `config.yaml`, seção `translate:`. Cascata: CLI flags > config.yaml > fallback hardcoded.

## Pipeline end-to-end (run.sh)

Para o caminho feliz (URL → vault em pt-br) com um único comando:

```bash
./run.sh -u <url>                              # output em ./out, cookies do chrome
./run.sh -u <url> -o ~/transcricoes            # output customizado
./run.sh -o ~/transcricoes -u <url>            # ordem livre (long: --url / --output)
./run.sh -u <url> -a                           # OpenAI Whisper API (em vez de mlx local)
./run.sh -u <url> --force                      # re-roda tudo (yt-transcribe + translate + vault-import)
./run.sh -u <url> --force-translate            # re-roda só a etapa 2
./run.sh -u <url> --force-vault-import         # re-roda só a etapa 3
BROWSER=firefox ./run.sh -u <url>              # cookies de outro browser
./run.sh -h                                    # uso
```

O script roda em sequência: `yt-transcribe` → `translate` → `vault-import`. Para imediatamente se qualquer etapa falhar (`set -euo pipefail`).

Skip automático (idempotência completa):
- Etapa 1 (yt-transcribe) pula se já existir pasta `*_<slug>` com `raw.md` e `meta.json` cuja URL casa.
- Etapa 2 (translate) pula se `raw_pt-br.md` já existe na subpasta gerada.
- Etapa 3 (vault-import) pula se `<vault>/raw/<slug>.md` já existe.

Para forçar re-execução de uma etapa específica sem apagar arquivos manualmente, usar `--force-translate`, `--force-vault-import`, ou `--force` (todas).

Para cenários customizados (`--api`, `--target-lang`, `--vault`, etc.), usar os comandos individuais dos módulos.

## Skills (Claude Code)

### /translate

Traduz arquivos .md usando o próprio Claude como engine — sem custo de API (usa plano Max).

```
/translate /path/to/raw.md           # traduz para pt-br
/translate /path/to/raw.md es        # traduz para espanhol
```

Output: `raw_<lang>.md` na mesma pasta. Usar para tradução interativa. Para automação/scripts, usar o CLI `uv run translate`.

## Stack

- Python 3.13+, uv
- yt-dlp, mlx-whisper (opcional, macOS 14+), OpenAI API, Anthropic API, pydub, pyyaml

## Convenções

- uv para gerenciamento de pacotes
- `.env` para API keys (nunca commitar)
- Cada módulo é autônomo — sem pasta `shared/`, sem imports cruzados
- `config.yaml` é do projeto, não de um módulo. Cada módulo lê sua seção
- Output em `.md` (compatível com Obsidian, LLM wiki, etc.)
