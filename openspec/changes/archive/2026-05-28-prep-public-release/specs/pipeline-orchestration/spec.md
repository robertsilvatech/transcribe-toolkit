## ADDED Requirements

### Requirement: `vault-import` é opcional em `run.sh`
O `run.sh` SHALL detectar se um vault está configurado (via `VAULT_PATH` env var, ou `vault_import.default_vault` em `config.yaml`, ou flag `--vault` se houver) e SHALL pular a etapa 3 quando nenhuma fonte fornecer um vault. Quando o vault está configurado, o comportamento atual (etapa 3 invoca `vault-import`) SHALL ser preservado integralmente.

#### Scenario: Vault não configurado, pipeline para após translate
- **WHEN** o usuário executa `./run.sh -u <url>` e nem `VAULT_PATH` nem `vault_import.default_vault` estão definidos
- **THEN** o script executa etapas 1 e 2 (yt-transcribe + translate) e termina com exit 0; etapa 3 não é invocada; uma mensagem informa que vault-import foi pulado por configuração ausente

#### Scenario: Vault configurado via config.yaml, comportamento preservado
- **WHEN** o usuário executa `./run.sh -u <url>` com `vault_import.default_vault` definido em `config.yaml`
- **THEN** o script executa as 3 etapas (incluindo vault-import) idêntico ao comportamento atual

#### Scenario: Vault configurado via VAULT_PATH
- **WHEN** o usuário executa `VAULT_PATH=~/meu-vault ./run.sh -u <url>` e `config.yaml` NÃO define `vault_import.default_vault`
- **THEN** o script executa as 3 etapas, usando `~/meu-vault` como destino

### Requirement: Flags vault-specific exigem vault configurado
Quando o usuário passa `-s/--subfolder` ou `-p/--prefix` no `run.sh` mas nenhuma fonte de vault está configurada (env var nem config.yaml), o script SHALL falhar com mensagem de erro clara antes de executar qualquer etapa.

#### Scenario: -s sem vault configurado
- **WHEN** o usuário executa `./run.sh -u <url> -s curso-x` e nem `VAULT_PATH` nem `vault_import.default_vault` estão definidos
- **THEN** o script imprime erro indicando que `-s/--subfolder` requer um vault configurado (sugere `VAULT_PATH` ou `vault_import.default_vault`) e termina com exit code não-zero antes da etapa 1

#### Scenario: -p sem vault configurado
- **WHEN** o usuário executa `./run.sh -u <url> -p A01` e nenhuma fonte de vault está definida
- **THEN** o script imprime erro análogo ao caso `-s` e termina com exit code não-zero

#### Scenario: -s com vault configurado funciona normal
- **WHEN** o usuário executa `./run.sh -u <url> -s curso-x` com `VAULT_PATH` definido
- **THEN** o script procede normalmente (não falha pela validação)
