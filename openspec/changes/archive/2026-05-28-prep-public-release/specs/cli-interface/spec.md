## ADDED Requirements

### Requirement: Variáveis de ambiente como nível intermediário na cascata de paths
O sistema SHALL aceitar variáveis de ambiente como fonte intermediária para resolver paths de output e vault. A cascata efetiva SHALL ser `CLI flag > env var > config.yaml > erro`. Os nomes SHALL ser:
- `YT_TRANSCRIBE_OUTPUT` para `yt_transcribe.default_output`
- `LOCAL_TRANSCRIBE_OUTPUT` para `local_transcribe.default_output`
- `VAULT_PATH` para `vault_import.default_vault`

Quando a variável está definida e não é vazia, ela SHALL ter precedência sobre o `config.yaml` mas SHALL ser sobrescrita por flag de CLI explícita. Tilde (`~`) e expansão de path SHALL ser aplicados igualmente, independente da fonte.

#### Scenario: YT_TRANSCRIBE_OUTPUT define output quando config ausente
- **WHEN** `YT_TRANSCRIBE_OUTPUT=~/meu-out` está definida no ambiente, `config.yaml` não define `yt_transcribe.default_output` e o usuário roda `yt-transcribe <url>` sem `--output`
- **THEN** o sistema resolve o output como `~/meu-out` (expandido para absoluto)

#### Scenario: --output sobrescreve env var
- **WHEN** `YT_TRANSCRIBE_OUTPUT=~/env-out` está definida e o usuário roda `yt-transcribe <url> --output ~/cli-out`
- **THEN** o sistema usa `~/cli-out`, ignorando a env var

#### Scenario: env var sobrescreve config.yaml
- **WHEN** `YT_TRANSCRIBE_OUTPUT=~/env-out` está definida e `config.yaml` define `yt_transcribe.default_output: ~/config-out`
- **THEN** o sistema usa `~/env-out`

#### Scenario: env var vazia é tratada como ausente
- **WHEN** `YT_TRANSCRIBE_OUTPUT=""` está definida e `config.yaml` define um valor
- **THEN** o sistema usa o valor do `config.yaml` (env var vazia não conta)

#### Scenario: LOCAL_TRANSCRIBE_OUTPUT funciona análogo
- **WHEN** `LOCAL_TRANSCRIBE_OUTPUT=~/local-out` está definida e o usuário roda `local-transcribe aula.mp4` sem `--output`
- **THEN** o sistema resolve o output como `~/local-out`

#### Scenario: VAULT_PATH funciona análogo
- **WHEN** `VAULT_PATH=~/meu-vault` está definida e o usuário roda `vault-import <input>` sem `--vault`
- **THEN** o sistema resolve o vault como `~/meu-vault`

#### Scenario: Nenhuma fonte fornece valor
- **WHEN** nenhuma flag CLI passa o valor, env var está ausente/vazia, e `config.yaml` não tem a chave
- **THEN** o sistema imprime erro mencionando as três opções (flag, env var, config) e termina com exit code não-zero
