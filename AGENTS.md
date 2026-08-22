# Transcribe Toolkit

Projeto modular para transcrição e processamento de vídeos/áudios (YouTube e arquivos locais) para uso com LLMs.

## Arquitetura modular

Módulos **ingestores** (yt_transcribe, local_transcribe) são pastas independentes na raiz com sua própria CLI. Todos compartilham lógica de transcrição/formatação via `transcribe_core/`.

```
transcribe_core/   # núcleo compartilhado entre ingestores (transcrição + formatação)
├── transcriber.py     # transcribe(audio_path, use_api, model, engine) — mlx-whisper, whisperx ou OpenAI API + chunking
├── whisperx_worker.py # worker standalone do engine whisperx (roda em subprocess via uv, Python 3.12)
├── formatter.py       # save_outputs() — escreve raw.md, raw_timestamps.md, raw_whisper.json, meta.json
└── slugify.py         # slugify(text) — normaliza títulos pra nomes de pasta

yt_transcribe/     # ingestor 1: YouTube → raw files
├── cli.py
├── downloader.py
└── config.py

local_transcribe/  # ingestor 2: arquivos de mídia locais → raw files
├── cli.py
├── extractor.py       # ffmpeg: mp4/mov/mkv → .mp3 sibling cacheado
└── config.py

translate/         # módulo: texto → tradução via LLM
├── cli.py
├── config.py
└── translator.py

study_material/    # módulo: raw.md → material didático organizado via LLM
├── cli.py
├── config.py
├── generator.py
└── prompt.md          # system prompt (tópicos/subtópicos, dicas, erros comuns)

vault_import/      # módulo: pasta transcrita → vault destino (bridge, YouTube-only por enquanto)
├── cli.py
├── config.py
└── importer.py

runbooks/          # procedimentos passo-a-passo (transcrição de curso, material didático)
config.yaml        # config do projeto, cada módulo lê sua seção
pyproject.toml     # entry points pra todos os módulos
```

## Regra fundamental

**Antes de adicionar qualquer feature, perguntar: isso pertence a um módulo existente ou é um módulo novo?**

- Se a feature é sobre download/transcrição de YouTube → `yt_transcribe/`
- Se a feature é sobre transcrição de arquivos de mídia locais (.mp4/.mov/.mkv/.m4a/.mp3/.wav) → `local_transcribe/`
- Se a feature é lógica de transcrição/formatação compartilhada entre múltiplos ingestores → `transcribe_core/`
- Se a feature é sobre tradução de texto → `translate/`
- Se a feature é sobre gerar material didático a partir de transcrições → `study_material/`
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
uv run yt-transcribe <url> --output <dir> --engine whisperx   # faster-whisper/CTranslate2 em CPU (ver local_transcribe)
```

Use `--cookies-from-browser <browser>` quando o yt-dlp retornar "Sign in to confirm you're not a bot" (comum em vídeos não listados ou com restrição). Valores aceitos: `chrome`, `firefox`, `safari`, `brave`, `edge`, etc.

Skip automático: antes de baixar, o sistema procura em `<dir>` por uma pasta `*_<slug>` (qualquer data) com `raw.md` + `meta.json` cuja `url` casa com a URL solicitada. Se acha, imprime "Já transcrito" e termina sem baixar. Use `--force` para sobrepor.

Output:
```
<dir>/YYYY-MM-DD_slug/
├── raw.md               # texto limpo
├── raw_timestamps.md    # [HH:MM:SS] por segmento
├── raw_whisper.json     # resposta completa do Whisper (source of truth)
└── meta.json            # title, source=youtube, channel, url, duration, language
```

### local_transcribe

```bash
uv run local-transcribe aula01.mp4                            # arquivo único
uv run local-transcribe aula01.mp4 aula02.mp4                 # múltiplos posicionais
uv run local-transcribe ./curso/*.mp4                         # glob (expandido pelo shell)
uv run local-transcribe --dir ~/curso                         # recursivo
uv run local-transcribe --dir ~/curso --subfolder curso-x     # espelha árvore em <out>/curso-x/...
uv run local-transcribe aula01.mp4 --api                      # OpenAI Whisper API
uv run local-transcribe aula01.mp4 --force                    # re-transcreve (não re-extrai .mp3)
uv run local-transcribe --dir ~/curso --no-date               # pasta sem prefixo de data (só o slug)
uv run local-transcribe call.mp4 --word-timestamps            # timestamps por palavra no raw_whisper.json
uv run local-transcribe --dir ~/curso --limit 1               # testa 1 aula e para (skips não contam)
uv run local-transcribe --dir ~/curso --api --workers 10      # até 10 em paralelo (só com --api)
uv run local-transcribe --dir ~/curso --engine whisperx       # faster-whisper/CTranslate2 em CPU (sem API)
uv run local-transcribe aula01.mp4 --engine whisperx --model large-v3   # reusa modelo já cacheado no HF
```

Engines: `mlx` (padrão, GPU via mlx-whisper), `whisperx` (CPU via faster-whisper/CTranslate2) e `--api` (OpenAI). O engine whisperx roda num subprocess isolado (`uv run --python 3.12 --with whisperx`) porque o whisperx exige Python <3.14 e o venv do projeto roda 3.14+ — a primeira execução resolve o ambiente e baixa o modelo (cacheados depois). Vantagens: VAD pyannote (pré-segmenta fala e pula silêncio → rápido e sem alucinações de silêncio) e, com `--word-timestamps`, alinhamento forçado wav2vec2 (bordas de palavra medidas contra o áudio; cada word ganha `score` em vez de `probability`). Default de `--model` no whisperx: `large-v3-turbo` (nomes faster-whisper). Não suporta `--multilang`; `--workers` roda sequencial como no mlx. Avisos de `torchcodec/libavutil` no load são inofensivos (fallback interno do whisperx).

**WhisperX em Apple Silicon (M1+):** roda sempre em **CPU com quantização int8** — o CTranslate2 (backend do faster-whisper) não tem caminho Metal, e pedir `mps` falha no load em vez de cair pra CPU (é daí que vem o mito de "whisperx não funciona no Mac"). A seleção de device (`cuda/float16` se houver, senão `cpu/int8`) e o `batch_size=8` já estão resolvidos em `transcribe_core/whisperx_worker.py` (`_device()`), no mesmo padrão da skill edvid; a velocidade em CPU vem do int8 + decodificação em batch dos trechos de fala pré-segmentados pelo VAD (~tempo real ou melhor com large-v3; custo fixo ~18s de load de modelo por arquivo). Não tentar forçar GPU/MPS nem instalar whisperx no venv do projeto — o subprocess via uv é o caminho suportado.

Extensões aceitas: `.mp4`, `.mov`, `.mkv` (vídeo, extrai áudio via ffmpeg), `.m4a`, `.mp3`, `.wav` (áudio, sem extração).

Áudio extraído: `aula01.mp4` → `aula01.mp3` ao lado do source. Cacheado: se `.mp3` já existe, reusa. `--force` re-transcreve mas NÃO re-extrai. Pasta de source read-only → erro claro (sem fallback automático para /tmp).

Skip automático: procura subpasta `*_<slug>/meta.json` (layout com data) ou `<slug>/meta.json` (layout `--no-date`) cujo `source_path` casa com o caminho absoluto do arquivo. Use `--force` para ignorar.

`--no-date`: nomeia a pasta de output só com o slug do arquivo (ex: `aula01/` em vez de `2026-08-08_aula01/`). Útil pra materiais de curso.

`--word-timestamps`: grava timestamps por palavra em `segments[i].words` no `raw_whisper.json` (`{word, start, end, probability?}` — `probability` só no engine local). Funciona no engine local E com `--api`. `raw.md` e `raw_timestamps.md` não mudam. Marca `word_timestamps: true` no `meta.json`.

Output:
```
<out>/[<sub>/]<rel-path>/YYYY-MM-DD_slug/    # ou <slug>/ com --no-date
├── raw.md
├── raw_timestamps.md
├── raw_whisper.json
└── meta.json            # title, source=local, source_path, duration, language
```

Em modo `--dir`, `<rel-path>` espelha a estrutura do diretório varrido (ex: `modulo01/` é preservado dentro de `<out>/<sub>/modulo01/...`).

### translate

```bash
uv run translate raw.md                               # usa config.yaml defaults
uv run translate raw.md --provider openai              # override provider
uv run translate raw.md --model claude-haiku-4-5       # override modelo
uv run translate raw.md --target-lang es               # override idioma
```

Output: `raw_<lang>.md` na mesma pasta do input.

Config em `config.yaml`, seção `translate:`. Cascata: CLI flags > config.yaml > fallback hardcoded.

### study_material

```bash
uv run study-material raw.md                          # arquivo único → study.md ao lado
uv run study-material --dir <curso>/transcriptions    # batch: varre por raw.md, pula os que já têm study.md
uv run study-material --dir ... --output-dir <curso>/material-de-estudo   # um <aula>.md por aula numa pasta única (upload)
uv run study-material --dir ... --limit 1             # testa 1 e para
uv run study-material raw.md --provider openai        # override provider
uv run study-material raw.md --force                  # re-gera
```

Transforma transcrição bruta em documento de estudo Markdown (tópicos/subtópicos numerados, cada conceito técnico como subtópico autossuficiente, blocos de código, destaques 💡 dica / ⚠️ erro comum / 🗣️ relato do professor). System prompt em `study_material/prompt.md` — editável sem tocar em código.

Output: `study.md` na mesma pasta do input, ou — com `--output-dir` — `<nome-da-pasta-da-transcrição>.md` dentro do diretório indicado (a task `study-course` usa esse modo: `<curso>/material-de-estudo/<aula>.md`, um arquivo por aula com o nome do vídeo, pronto pra upload). Config em `config.yaml`, seção `study_material:`. Cascata: CLI flags > config.yaml > fallback hardcoded.

## Pipeline end-to-end (run.sh)

Para o caminho feliz (URL → vault em pt-br) com um único comando:

```bash
./run.sh -u <url>                              # output em ./out, cookies do chrome
./run.sh -u <url> -o ~/transcricoes            # output customizado
./run.sh -o ~/transcricoes -u <url>            # ordem livre (long: --url / --output)
./run.sh -u <url> -s curso-mastering-devin     # vault em raw/curso-mastering-devin/<slug>.md
./run.sh -u <url> -s curso-x -p A01            # raw/curso-x/A01_<slug-sem-data>.md
./run.sh -u <url> -a                           # OpenAI Whisper API (em vez de mlx local)
./run.sh -u <url> --force                      # re-roda tudo (yt-transcribe + translate + vault-import)
./run.sh -u <url> --force-translate            # re-roda só a etapa 2
./run.sh -u <url> --force-vault-import         # re-roda só a etapa 3
BROWSER=firefox ./run.sh -u <url>              # cookies de outro browser
./run.sh -h                                    # uso
```

Para um curso com várias aulas, loop em bash:

```bash
for n in 01 02 03 04 05; do
    transcribe -u "https://youtu.be/AULA_${n}" -s curso-mastering-devin -p "A${n}"
done
```

O script roda em sequência: `yt-transcribe` → `translate` → `vault-import`. Para imediatamente se qualquer etapa falhar (`set -euo pipefail`).

Skip automático (idempotência completa):
- Etapa 1 (yt-transcribe) pula se já existir pasta `*_<slug>` com `raw.md` e `meta.json` cuja URL casa.
- Etapa 2 (translate) pula se `raw_pt-br.md` já existe na subpasta gerada.
- Etapa 3 (vault-import) pula se `<vault>/raw/[<sub>/][<prefix>_]<slug>.md` já existe (caminho calculado a partir de `-s` e `-p`).

Para forçar re-execução de uma etapa específica sem apagar arquivos manualmente, usar `--force-translate`, `--force-vault-import`, ou `--force` (todas).

Para cenários customizados (`--api`, `--target-lang`, `--vault`, etc.), usar os comandos individuais dos módulos.

## Pipeline para arquivos locais (run-local.sh)

Para o caminho feliz com arquivos locais (`<file>` ou `<dir>` → `raw_pt-br.md`):

```bash
./run-local.sh -f aula01.mp4                                  # arquivo único
./run-local.sh -f aula01.mp4 -f aula02.mp4                    # múltiplos -f
./run-local.sh --dir ~/curso -s curso-mastering-devin         # batch recursivo
./run-local.sh -f aula01.mp4 -a                               # OpenAI Whisper API
./run-local.sh --dir ~/curso --force                          # re-roda local-transcribe + translate
./run-local.sh --dir ~/curso --force-translate                # re-roda só etapa 2
./run-local.sh -h                                             # uso
```

O script roda em sequência: `local-transcribe` → `translate` (varre subpastas geradas). **Não invoca `vault-import`** — `vault_import` exige `url` no `meta.json`, suporte a transcrições locais é fora de escopo (deferred).

Skip automático:
- Etapa 1 (local-transcribe): pula se subpasta `*_<slug>/meta.json` com `source_path` casando já existe.
- Etapa 2 (translate): pula se `raw_pt-br.md` já existe na subpasta. Idioma já em pt → copia `raw.md` direto.

Para forçar re-execução, usar `--force-translate` ou `--force` (todas as etapas).

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
- yt-dlp, mlx-whisper (opcional, macOS 14+), whisperx (opcional, via subprocess `uv run` — não é dependência do venv), OpenAI API, Anthropic API, pydub, pyyaml

## Convenções

- uv para gerenciamento de pacotes
- `.env` para API keys (nunca commitar)
- Módulos **não-core** são autônomos — sem imports cruzados entre `translate/`, `vault_import/`, etc. **Exceção autorizada:** `transcribe_core/` é o único módulo compartilhado, usado pelos ingestores (`yt_transcribe/`, `local_transcribe/`). Não criar outros módulos compartilhados sem decisão explícita.
- `config.yaml` é do projeto, não de um módulo. Cada módulo lê sua seção
- Output em `.md` (compatível com Obsidian, LLM wiki, etc.)
- `meta.json` traz o campo `source` (`"youtube"` ou `"local"`) e — para fonte local — `source_path` no lugar de `url`/`channel`
