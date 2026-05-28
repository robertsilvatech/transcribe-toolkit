## Why

O repo `transcribe-toolkit` está pronto pra ser tornado público em https://github.com/robertsilvatech/transcribe-toolkit, mas hoje vaza paths pessoais (`~/Dropbox/00-PARA/...`, `~/Repos/gh-robertsilvatech/...`) no `config.yaml` e `README.md`, não tem `LICENSE`, e `run.sh` quebra pra quem não tem um vault Obsidian configurado. Esta mudança remove essas barreiras e dá um onboarding decente pra novos usuários — incluindo Linux, não só Mac.

## What Changes

- **MODIFICADO** `config.yaml` vira `config.yaml.example` com paths genéricos (`~/Documents/transcribe-toolkit/...`). O `config.yaml` real é gitignored; `setup.sh` copia example → real se não existe.
- **NOVO** `LICENSE` (MIT) na raiz.
- **MODIFICADO** `.gitignore` ganha entradas: `config.yaml`, `cursos/`, `transcricoes/`, `*.mp3`.
- **MODIFICADO** `run.sh` pula etapa 3 (`vault-import`) silenciosamente quando `vault_import.default_vault` é null/ausente. Falha com mensagem clara apenas se `-s`/`-p` foram passados sem vault configurado.
- **NOVO** suporte a variáveis de ambiente para paths, com cascata `CLI flag > env var > config.yaml > erro`:
  - `YT_TRANSCRIBE_OUTPUT` em `yt_transcribe/config.py`
  - `LOCAL_TRANSCRIBE_OUTPUT` em `local_transcribe/config.py`
  - `VAULT_PATH` em `vault_import/config.py`
- **MODIFICADO** `setup.sh` detecta o OS (`uname`) e mostra comando de install apropriado por dependência faltante (`brew` no Mac, `apt`/`dnf` no Linux). Resto do script (uv sync, criação de pastas, instalação de wrappers) já é cross-platform.
- **MODIFICADO** `README.md` recebe:
  - Seção **Quick Start** no topo (clone → primeiro vídeo em 60s).
  - **Compatibilidade** explícita: matriz Mac M / Mac Intel / Linux / Windows (WSL).
  - **Costs & Privacy**: disclaimers sobre custos das APIs (OpenAI/Anthropic) e privacidade (áudio enviado pra OpenAI com `--api`; texto enviado pro LLM em `translate`).
  - Remoção de `~/Dropbox/SECOND-BRAIN-OBSIDIAN` dos exemplos (paths genéricos).
- **FORA DE ESCOPO** (próximas rodadas): testes automatizados, CI, `CONTRIBUTING.md`, README em inglês, demo gif, distribuição via PyPI.

## Capabilities

### New Capabilities
- `public-release-readiness`: sanitização do repo (config template + gitignore + LICENSE + documentação) e remoção de dependências pessoais que bloqueiam uso por terceiros.

### Modified Capabilities
- `cli-interface`: cascata de resolução de paths ganha env vars (`YT_TRANSCRIBE_OUTPUT`).
- `pipeline-orchestration`: `run.sh` torna `vault-import` opcional baseado na configuração; comportamento de `run-local.sh` (que já pula vault) é o padrão consistente.
- `installation-setup`: `setup.sh` detecta OS e mostra comandos apropriados; copia `config.yaml.example` → `config.yaml` na primeira execução.

## Impact

**Código**
- Modificado: `yt_transcribe/config.py`, `local_transcribe/config.py`, `vault_import/config.py` (adicionar leitura de env var).
- Modificado: `run.sh` (vault opcional).
- Modificado: `setup.sh` (OS detection + config.yaml bootstrap).
- Modificado: `.gitignore`, `README.md`.
- Renomeado: `config.yaml` → `config.yaml.example` (com paths sanitizados).
- Novo: `LICENSE`.

**APIs/CLIs**
- Comportamento dos CLIs preservado — apenas a resolução de paths ganha um nível (env var) entre CLI flag e config.yaml.
- `run.sh` continua aceitando os mesmos flags, mas `-s`/`-p` agora têm validação explícita contra `default_vault` ausente.

**Migração**
- Usuários existentes (incluindo o autor): após pull desta change, vão precisar copiar `config.yaml.example` → `config.yaml` (ou rodar `./setup.sh`) e editar com seus paths. O `setup.sh` faz isso automaticamente.

**Risco**
- `run.sh` mudar comportamento pra usuários atuais que dependem do vault-import sempre rodar — mitigado por: comportamento idêntico quando `default_vault` está configurado (o caso comum hoje). Skip silencioso só ativa se config é null/ausente.

**Dependências**
- Nenhuma nova dependência runtime.
