## MODIFIED Requirements

### Requirement: Arquivo config.yaml com defaults
O sistema SHALL ler configurações de `config.yaml` na raiz do projeto para definir defaults de tradução. O config loader reside no pacote `translate/` (`translate/config.py`), é autônomo e não depende de outros módulos.

#### Scenario: Config existe
- **WHEN** `config.yaml` existe com seção `translate`
- **THEN** o sistema usa `default_provider`, `target_language` e `providers.<name>.model` como defaults

#### Scenario: Config não existe
- **WHEN** `config.yaml` não existe
- **THEN** o sistema funciona com fallbacks hardcoded: provider `anthropic`, modelo `claude-sonnet-4-6`, idioma `pt-br`

### Requirement: Cascata de prioridade
O sistema SHALL aplicar configurações na ordem: flags CLI > config.yaml > fallback hardcoded.

#### Scenario: Flag CLI tem prioridade
- **WHEN** config.yaml define `default_provider: anthropic` e CLI recebe `--provider openai`
- **THEN** o sistema usa `openai`

#### Scenario: Config tem prioridade sobre fallback
- **WHEN** config.yaml define `default_provider: openai` e nenhuma flag CLI é passada
- **THEN** o sistema usa `openai` (não o fallback hardcoded)

### Requirement: API keys via variável de ambiente
O sistema SHALL ler API keys do `.env` usando o nome da variável definido em `config.yaml` (campo `api_key_env`).

#### Scenario: Key configurada via .env
- **WHEN** config.yaml define `api_key_env: ANTHROPIC_API_KEY` e essa variável existe no ambiente
- **THEN** o sistema usa o valor da variável para autenticação
