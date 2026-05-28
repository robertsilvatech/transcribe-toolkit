## ADDED Requirements

### Requirement: `config.yaml.example` committed; `config.yaml` gitignored
O sistema SHALL fornecer um arquivo `config.yaml.example` na raiz do repo contendo a estrutura completa de configuração com paths genéricos (não-pessoais). O arquivo `config.yaml` SHALL estar listado no `.gitignore` — é o arquivo local do usuário, derivado do example via `setup.sh`. Nenhum path pessoal do autor SHALL aparecer em arquivos rastreados pelo git.

#### Scenario: config.yaml.example presente e sanitizado
- **WHEN** se inspeciona o repo após esta change
- **THEN** existe `config.yaml.example` na raiz com `yt_transcribe.default_output: ~/Documents/transcribe-toolkit/youtube` (ou path genérico equivalente), `local_transcribe.default_output: ~/Documents/transcribe-toolkit/local` e `vault_import.default_vault: null` (ou comentado)

#### Scenario: config.yaml está no gitignore
- **WHEN** se inspeciona `.gitignore`
- **THEN** o arquivo contém uma linha matching `config.yaml` (não `config.yaml.example`)

#### Scenario: Nenhum path pessoal em arquivos rastreados
- **WHEN** se busca por `Dropbox`, `second-brain` ou `gh-robertsilvatech` em arquivos rastreados (excluindo `openspec/`)
- **THEN** nenhum match é encontrado em `config.yaml.example`, `README.md` ou outros arquivos públicos

### Requirement: `LICENSE` MIT na raiz
O sistema SHALL incluir um arquivo `LICENSE` na raiz do repo com o texto da licença MIT, incluindo copyright do autor e ano atual.

#### Scenario: LICENSE presente
- **WHEN** se inspeciona a raiz do repo
- **THEN** existe um arquivo `LICENSE` cujo conteúdo é o texto canônico da MIT License, com linha de copyright preenchida

### Requirement: `.gitignore` cobre pastas/arquivos locais comuns
O sistema SHALL ignorar via `.gitignore` os seguintes patterns adicionais (além dos atuais):
- `config.yaml` (arquivo local do usuário)
- `cursos/` (pasta de batch scripts pessoais)
- `transcricoes/` (caminho default sugerido no example; protege contra commit acidental)
- `*.mp3` (protege contra commit de áudio extraído por `local_transcribe`)

#### Scenario: Patterns presentes no .gitignore
- **WHEN** se inspeciona `.gitignore`
- **THEN** contém linhas matching `config.yaml`, `cursos/`, `transcricoes/` e `*.mp3`

#### Scenario: cursos/ não rastreado mesmo se existir
- **WHEN** o usuário cria `cursos/algum-script.sh` localmente
- **THEN** `git status` não lista o arquivo

### Requirement: README com Quick Start, Compatibilidade e Costs/Privacy
O `README.md` SHALL conter, próximo ao topo (antes da árvore de módulos):
1. Uma seção **Quick Start** com 4-6 comandos copy-paste para clonar, configurar e rodar o primeiro vídeo em menos de 60 segundos.
2. Uma seção **Compatibilidade** com tabela cobrindo Mac M-series, Mac Intel, Linux, Windows (WSL), indicando para cada um: status, modo de transcrição disponível (mlx local vs --api).
3. Uma seção **Costs & Privacy** com disclaimers sobre: custos das APIs (OpenAI Whisper + Anthropic/OpenAI translate), e que dados (áudio com `--api`, texto no translate) são enviados pra provedores externos.

#### Scenario: Quick Start no topo do README
- **WHEN** se abre `README.md` e procura a primeira ocorrência de "Quick Start" (ou equivalente)
- **THEN** aparece antes da seção "Arquitetura modular"

#### Scenario: Matriz de compatibilidade explícita
- **WHEN** se lê a seção Compatibilidade
- **THEN** existe uma tabela ou lista que diferencia: "Apple Silicon (M1+) — mlx local + API ambos", "Intel Mac — só API", "Linux — só API", "Windows — usar WSL ou só API"

#### Scenario: Disclaimer de custos e privacidade
- **WHEN** se lê a seção Costs & Privacy
- **THEN** está documentado que (a) APIs cobram por uso, (b) áudio é enviado pra OpenAI quando `--api`, (c) texto é enviado pro provider escolhido em translate

#### Scenario: Exemplos sem paths pessoais
- **WHEN** se lê todos os exemplos do README
- **THEN** nenhum usa `~/Dropbox/SECOND-BRAIN-OBSIDIAN` ou path com `gh-robertsilvatech`; paths são genéricos (`~/Documents/...`, `~/transcricoes`, `<vault>`)
