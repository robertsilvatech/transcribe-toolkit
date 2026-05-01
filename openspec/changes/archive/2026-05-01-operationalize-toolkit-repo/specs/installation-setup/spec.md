## ADDED Requirements

### Requirement: Script de setup automatizado para Mac
O sistema SHALL fornecer um shell script `setup.sh` na raiz do projeto que prepara uma máquina Mac para uso end-to-end do toolkit. O script SHALL ser idempotente: rodar múltiplas vezes não SHALL produzir erros nem corromper estado prévio.

#### Scenario: Setup em máquina limpa
- **WHEN** o usuário clona o repo em uma máquina Mac onde `uv`, `ffmpeg` e `gh` já estão instalados, sem `.env`, sem pasta de output, sem wrapper instalado, e executa `./setup.sh`
- **THEN** o script roda `uv sync`, copia `.env.example` para `.env`, cria a pasta de output default (definida em `config.yaml`), instala o wrapper em `~/.local/bin/transcribe`, e imprime instruções finais (editar `.env` com API keys, adicionar `~/.local/bin` ao PATH se faltar)

#### Scenario: Setup re-executado sem mudanças
- **WHEN** o usuário executa `./setup.sh` uma segunda vez sem alterar nada do ambiente
- **THEN** o script completa com sucesso (exit 0); etapas já feitas (`.env` existente, pasta criada) são puladas com mensagem; o wrapper é re-escrito (sobrescrita controlada, sempre o caminho atual do repo)

#### Scenario: Setup detecta dependência faltando
- **WHEN** o usuário executa `./setup.sh` em uma máquina sem `uv` (ou sem `ffmpeg`, ou sem `gh`)
- **THEN** o script imprime mensagem clara indicando qual dependência falta e o comando `brew install` correspondente, e termina com exit code não-zero sem fazer nenhuma alteração

#### Scenario: .env já existe
- **WHEN** o usuário executa `./setup.sh` e `.env` já existe na raiz
- **THEN** o script NÃO sobrescreve `.env` e imprime mensagem indicando que está sendo preservado

### Requirement: Wrapper executável global
O sistema SHALL instalar um wrapper executável em `~/.local/bin/transcribe` que invoca `<repo>/run.sh` com todos os argumentos propagados. O wrapper SHALL ter o caminho absoluto do repo embutido em tempo de instalação (via `setup.sh`).

#### Scenario: Wrapper instalado é executável
- **WHEN** `./setup.sh` termina com sucesso
- **THEN** o arquivo `~/.local/bin/transcribe` existe, tem permissão de execução (`+x`) e contém uma linha `exec` apontando para o caminho absoluto de `run.sh` no repo onde `setup.sh` foi executado

#### Scenario: Re-instalação atualiza o caminho
- **WHEN** o usuário move o repo para outra pasta e executa `./setup.sh` novamente da nova localização
- **THEN** o wrapper em `~/.local/bin/transcribe` é re-escrito com o novo caminho absoluto, sobrescrevendo o anterior

#### Scenario: PATH check
- **WHEN** `./setup.sh` é executado e `~/.local/bin` NÃO está no PATH do usuário
- **THEN** o script imprime aviso destacado com o bloco copy-paste pra adicionar ao `~/.zshrc` (ex: `export PATH="$HOME/.local/bin:$PATH"`), mas NÃO modifica `~/.zshrc` automaticamente

#### Scenario: PATH já configurado
- **WHEN** `./setup.sh` é executado e `~/.local/bin` já está no PATH
- **THEN** o script confirma com mensagem positiva e não imprime instruções de PATH

### Requirement: Criação da pasta de output default
O sistema SHALL criar a pasta de output definida em `config.yaml` (`yt_transcribe.default_output`) durante o setup, se ela não existir. O script SHALL expandir `~` e variáveis de ambiente no caminho.

#### Scenario: Pasta não existe
- **WHEN** `./setup.sh` é executado e a pasta `~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw/` (ou outro caminho definido em config) não existe
- **THEN** o script cria a pasta (incluindo pais se necessário, equivalente a `mkdir -p`) e imprime mensagem de confirmação

#### Scenario: Pasta já existe
- **WHEN** `./setup.sh` é executado e a pasta de output já existe
- **THEN** o script não toca o conteúdo existente e imprime mensagem indicando que a pasta já está pronta
