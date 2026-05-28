## Why

Hoje o toolkit só ingere vídeos do YouTube via `yt-transcribe`. O usuário tem material gravado localmente (aulas em `.mp4` que não foram publicadas) e precisa transcrever esses arquivos para alimentar o mesmo pipeline downstream (translate, RAG, vault). Sem um caminho de ingestão local, ele teria que subir cada aula no YouTube só pra transcrever — fluxo absurdo.

Esta mudança adiciona um módulo `local_transcribe` para arquivos de mídia locais, e aproveita pra extrair em `transcribe_core/` a lógica de transcrição/formatação que hoje vive em `yt_transcribe/` mas é totalmente agnóstica de fonte.

## What Changes

- **NOVO** módulo `local_transcribe/` com CLI `local-transcribe`:
  - Aceita arquivos posicionais (`.mp4 .mov .mkv .m4a .mp3 .wav`) **ou** `--dir <path>` (recursivo).
  - Extrai `.mp3` ao lado do source via ffmpeg (cacheado: reusa se existir; não re-extrai em `--force`).
  - Reutiliza chunking e backends (mlx-whisper local / OpenAI API) já existentes.
  - Título derivado do filename (slugified). Sem flag `--title` override.
  - `--subfolder <name>` espelha a árvore do `--dir` dentro do output.
  - Source read-only → fail fast.
- **NOVO** módulo `transcribe_core/` agrupando lógica compartilhada:
  - `transcriber.py` (movido de `yt_transcribe/`)
  - `formatter.py` (movido de `yt_transcribe/`)
  - `slugify.py` (extraído de `yt_transcribe/downloader.py`)
- **MODIFICADO** `yt_transcribe/` passa a importar de `transcribe_core/`. Comportamento e CLI preservados.
- **MODIFICADO** `meta.json` ganha campo `source` (`"youtube"` ou `"local"`); arquivos locais escrevem `source_path` em vez de `url`/`channel`.
- **NOVO** `config.yaml` seção `local_transcribe.default_output`.
- **NOVO** `run-local.sh` na raiz: pipeline `local-transcribe → translate` (sem `vault-import`).
- **NOVO** wrapper `~/.local/bin/transcribe-local` apontando pra `run-local.sh`.
- **MODIFICADO** `AGENT.md`: relaxa a regra "sem pasta `shared/`, sem imports cruzados" pra permitir `transcribe_core/`.
- **FORA DE ESCOPO**: `vault_import` continua exigindo `url` (não suporta transcrições locais ainda). O `run.sh` atual não é alterado.

## Capabilities

### New Capabilities
- `local-transcription`: Transcrever arquivos de mídia locais (vídeo/áudio) com extração de áudio cacheada ao lado do source, batch via `--dir` recursivo, e output espelhando a árvore via `--subfolder`.
- `transcribe-core`: Módulo compartilhado entre ingestores YouTube e locais — transcrição (mlx/API + chunking), formatação de outputs (raw.md, raw_timestamps.md, raw_whisper.json, meta.json), slugify.

### Modified Capabilities
- `output-formatting`: `meta.json` ganha campo `source` (`"youtube"` ou `"local"`). Para `source: "local"`, troca `url`/`channel` por `source_path`.
- `installation-setup`: `setup.sh` passa a instalar também `~/.local/bin/transcribe-local`.
- `pipeline-orchestration`: novo script `run-local.sh` para pipeline `local-transcribe → translate`.

## Impact

**Código**
- Novo: `transcribe_core/`, `local_transcribe/`, `run-local.sh`.
- Movido: `yt_transcribe/transcriber.py`, `yt_transcribe/formatter.py`, helper `_slugify` de `downloader.py`.
- Modificado: `yt_transcribe/cli.py`, `yt_transcribe/downloader.py`, `yt_transcribe/formatter.py` chamadas, `pyproject.toml` (entry point + packages), `config.yaml`, `setup.sh`, `AGENT.md`.

**APIs/CLIs**
- Novo CLI: `uv run local-transcribe ...`.
- Novo wrapper: `~/.local/bin/transcribe-local`.
- CLI existente `yt-transcribe` permanece com mesma assinatura.

**Dependências**
- Nenhuma nova: `pydub` (chunking) e `ffmpeg` (extração) já são deps do projeto.

**Downstream**
- `translate/` funciona transparente (lê `raw.md`, idem).
- `vault_import/` **não** suporta `source: "local"` ainda — exige `url` no meta. Fora de escopo desta mudança.

**Risco**
- Refactor toca `yt_transcribe` (movimentação de arquivos). Mitigação: comportamento preservado por testes manuais; git permite rollback rápido.
