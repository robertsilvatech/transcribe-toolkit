## Why

O projeto está pronto pra virar repositório oficial, mas tem quatro bloqueadores:

1. O nome no `pyproject.toml` (`yt-transcribe`) confunde o módulo de ingestão com o toolkit inteiro — que vai crescer pra outras fontes além de YouTube (aulas próprias, podcasts, etc.).
2. O output default está hardcoded em `./out` no `run.sh`, com bug correlato no `.gitignore` (que ignora `output/` em vez de `out/`).
3. O usuário precisa fazer `cd` na pasta do projeto pra rodar `./run.sh` — quer invocar de qualquer lugar (`transcribe -u <URL>`).
4. Não existe setup automatizado pra reproduzir o ambiente em outra máquina (nova máquina = lembrar de rodar `uv sync` + criar `.env` + criar pasta de output + configurar PATH manualmente).

## What Changes

### Renomeação e identidade

- **BREAKING**: Renomear projeto pra `transcribe-toolkit` no `pyproject.toml` (entry point CLI `yt-transcribe` permanece — só o nome do package muda, refletindo que o repo é um toolkit modular).
- Reescrever `README.md`: título "Transcribe Toolkit", introdução refletindo expansão futura além de YouTube, seção **Setup** com instalação one-shot, nota sobre arquitetura modular.

### Output configurável (sem hardcode)

- **BREAKING**: `--output` deixa de ser obrigatório no CLI `yt-transcribe`. Resolução cascata: flag `--output` > `config.yaml` (`yt_transcribe.default_output`) > **erro explícito**. Mesmo padrão de `vault_import.default_vault`.
- Adicionar seção `yt_transcribe:` ao `config.yaml` com `default_output: ~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw`.
- Criar `yt_transcribe/config.py` com `resolve_output_path(cli_value)` espelhando `vault_import/config.py`.
- Atualizar `run.sh` pra não hardcodar `OUT_BASE`: quando `-o` não vier, não passa `--output` pro CLI; resolve `OUT_BASE` via `uv run python -c "from yt_transcribe.config import resolve_output_path; print(resolve_output_path(None))"`.
- Corrigir `.gitignore`: remover `output/`, adicionar `out/`, `.DS_Store`, `.idea/`, `.vscode/`, `*.swp`, `build/`, `*.log`.

### Comando global e setup automatizado (escopo novo)

- Adicionar `setup.sh` na raiz que prepara uma máquina do zero (Mac):
  - Verifica dependências (`uv`, `ffmpeg`, `gh` — avisa o que falta com instruções `brew install`).
  - Roda `uv sync` (e oferece `--extra local` opcional pra mlx-whisper).
  - Cria `.env` a partir do `.env.example` se não existir; pede pra editar com API keys.
  - Cria a pasta de output default (`~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw/`) se não existir.
  - Instala wrapper executável em `~/.local/bin/transcribe` que faz `exec <repo>/run.sh "$@"` (caminho absoluto resolvido em tempo de install).
  - Verifica se `~/.local/bin` está no PATH; se não, imprime instrução pra adicionar ao `~/.zshrc`.
  - Idempotente: rodar de novo não quebra nada (skip de cada etapa se já feita; sobrescrita controlada do wrapper).
- Após `./setup.sh`, o usuário roda de qualquer pasta:
  ```
  transcribe -u https://youtu.be/VIDEO_ID
  transcribe --api -u https://youtu.be/VIDEO_ID
  transcribe -u https://youtu.be/VIDEO_ID -o /caminho/custom
  ```
- README documenta o fluxo "nova máquina": clone → `./setup.sh` → editar `.env` → `transcribe -u <URL>` de qualquer lugar.

### Operacionalização one-shot (não-código)

- Mover `out/` atual (~15MB) pra `~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw/`.
- `git init`, commit inicial.
- `gh repo create transcribe-toolkit --private --source=. --remote=origin --push`.

## Capabilities

### New Capabilities
- `installation-setup`: setup automatizado one-shot pra nova máquina (deps check, env, output dir, wrapper global em PATH).

### Modified Capabilities
- `cli-interface`: `--output` torna-se opcional; resolução cascata (CLI > `config.yaml` > erro).
- `pipeline-orchestration`: `run.sh` deixa de hardcodar `./out`; passa a ser invocável globalmente via wrapper `transcribe` instalado em `~/.local/bin/`.

## Impact

- **Código modificado**: `pyproject.toml`, `config.yaml`, `run.sh`, `yt_transcribe/cli.py`, `README.md`, `.gitignore`.
- **Código novo**: `yt_transcribe/config.py`, `setup.sh`.
- **Dados**: pasta `out/` (15MB) → `~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw/`.
- **Infra**: repo privado `transcribe-toolkit` no GitHub; wrapper `transcribe` em `~/.local/bin/`.
- **Quebra de compatibilidade**: invocações de `uv run yt-transcribe <url>` sem `--output` e sem `default_output` no config passam a falhar com erro explícito (alinhado com `vault_import`).
- **Sem impacto**: módulos `translate/` e `vault_import/` não são tocados; entry points (`yt-transcribe`, `translate`, `vault-import`) permanecem.
- **Plataforma**: setup hoje cobre Mac (zsh, brew). Linux não está em escopo desta change.
