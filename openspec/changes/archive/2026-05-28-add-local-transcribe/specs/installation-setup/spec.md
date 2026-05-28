## ADDED Requirements

### Requirement: Wrapper executável `transcribe-local`
O sistema SHALL instalar um wrapper executável em `~/.local/bin/transcribe-local` que invoca `<repo>/run-local.sh` com todos os argumentos propagados. O wrapper SHALL ter o caminho absoluto do repo embutido em tempo de instalação (via `setup.sh`). O wrapper `~/.local/bin/transcribe` (apontando para `run.sh`) SHALL continuar sendo instalado, sem alterações.

#### Scenario: Wrapper transcribe-local instalado é executável
- **WHEN** `./setup.sh` termina com sucesso
- **THEN** o arquivo `~/.local/bin/transcribe-local` existe, tem permissão de execução (`+x`) e contém uma linha `exec` apontando para o caminho absoluto de `run-local.sh` no repo onde `setup.sh` foi executado

#### Scenario: Ambos wrappers convivem
- **WHEN** `./setup.sh` é executado
- **THEN** `~/.local/bin/transcribe` (para o fluxo YouTube) E `~/.local/bin/transcribe-local` (para o fluxo de arquivos locais) ambos existem e apontam respectivamente para `run.sh` e `run-local.sh`

#### Scenario: Re-instalação atualiza o caminho de transcribe-local
- **WHEN** o usuário move o repo para outra pasta e executa `./setup.sh` novamente da nova localização
- **THEN** o wrapper em `~/.local/bin/transcribe-local` é re-escrito com o novo caminho absoluto, sobrescrevendo o anterior (mesmo comportamento de `~/.local/bin/transcribe`)

### Requirement: Criação da pasta de output default de `local_transcribe`
O sistema SHALL criar a pasta de output definida em `config.yaml` (`local_transcribe.default_output`) durante o setup, se ela for definida e não existir. Se `local_transcribe.default_output` não estiver definida em `config.yaml`, o setup SHALL pular silenciosamente essa etapa (compatível com instalações que só usam `yt_transcribe`).

#### Scenario: Pasta de local_transcribe não existe
- **WHEN** `./setup.sh` é executado, `config.yaml` define `local_transcribe.default_output: <path>` e a pasta não existe
- **THEN** o script cria a pasta (mkdir -p) e imprime mensagem de confirmação

#### Scenario: Pasta de local_transcribe já existe
- **WHEN** `./setup.sh` é executado e a pasta `local_transcribe.default_output` já existe
- **THEN** o script não toca o conteúdo existente e imprime mensagem indicando que a pasta já está pronta

#### Scenario: local_transcribe.default_output não definido
- **WHEN** `./setup.sh` é executado e `config.yaml` NÃO define `local_transcribe.default_output`
- **THEN** o script pula essa etapa sem erro (a etapa equivalente para `yt_transcribe.default_output` continua normal)
