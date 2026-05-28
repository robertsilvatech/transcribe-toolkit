## ADDED Requirements

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
