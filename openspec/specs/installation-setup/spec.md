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

### Requirement: `setup.sh` faz bootstrap do `config.yaml` a partir do example
O `setup.sh` SHALL, antes de criar pastas ou wrappers, copiar `config.yaml.example` para `config.yaml` se este último não existir. Se `config.yaml` já existe, SHALL preservá-lo intocado (mensagem informativa). Se `config.yaml.example` não existir, SHALL imprimir erro e abortar com exit code não-zero.

#### Scenario: Primeiro setup, config.yaml não existe
- **WHEN** o usuário executa `./setup.sh` em um clone fresco, `config.yaml.example` existe e `config.yaml` não existe
- **THEN** o script copia `config.yaml.example` → `config.yaml`, imprime mensagem informativa, e instrui o usuário a editar `config.yaml` com seus paths

#### Scenario: config.yaml já existe, preservar
- **WHEN** o usuário executa `./setup.sh` e `config.yaml` já existe (de um setup anterior ou edição manual)
- **THEN** o script NÃO sobrescreve `config.yaml` e imprime mensagem indicando que está sendo preservado

#### Scenario: config.yaml.example ausente
- **WHEN** o usuário executa `./setup.sh` sem `config.yaml.example` no repo
- **THEN** o script imprime erro indicando que o arquivo template está ausente e termina com exit code não-zero

### Requirement: `setup.sh` detecta OS e ajusta mensagens de install
O `setup.sh` SHALL detectar o sistema operacional via `uname -s` e ajustar as mensagens de install de dependências (uv, ffmpeg, gh) conforme o OS:
- **Darwin (macOS):** sugere `brew install <dep>`
- **Linux:** sugere instalar via gerenciador do sistema (ex: "use apt/dnf/pacman para instalar <dep>")
- **Outros:** mensagem genérica orientando consultar o site oficial da ferramenta

A lógica de checagem (`command -v <dep>`) e o restante do script (uv sync, criação de pastas, instalação de wrappers, check de PATH) SHALL funcionar igual em Mac e Linux.

#### Scenario: Setup em macOS com dep faltando
- **WHEN** `setup.sh` é executado em macOS (`uname -s` = `Darwin`) e `ffmpeg` está faltando
- **THEN** a mensagem de erro sugere `brew install ffmpeg`

#### Scenario: Setup em Linux com dep faltando
- **WHEN** `setup.sh` é executado em Linux (`uname -s` = `Linux`) e `ffmpeg` está faltando
- **THEN** a mensagem de erro orienta usar o gerenciador de pacotes do sistema (apt/dnf/pacman) para instalar `ffmpeg`

#### Scenario: Setup em Linux com todas as deps presentes
- **WHEN** `setup.sh` é executado em Linux com `uv`, `ffmpeg` e `gh` instalados
- **THEN** o script completa todas as etapas (uv sync, criar pastas, instalar wrappers, check PATH) sem erro, idêntico ao comportamento em Mac

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
