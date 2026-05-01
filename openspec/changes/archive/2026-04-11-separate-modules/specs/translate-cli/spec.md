## MODIFIED Requirements

### Requirement: CLI aceita path de arquivo texto
O sistema SHALL aceitar um caminho de arquivo `.md` como argumento posicional e traduzir seu conteúdo. O CLI reside no pacote `translate/` (entry point `translate.cli:main`).

#### Scenario: Tradução com defaults
- **WHEN** o usuário executa `translate /path/to/raw.md`
- **THEN** o sistema traduz usando o provider e modelo definidos no `config.yaml` (ou fallback) e salva `raw_pt-br.md` na mesma pasta

#### Scenario: Override de provider
- **WHEN** o usuário executa `translate /path/to/raw.md --provider openai`
- **THEN** o sistema usa OpenAI com o modelo default desse provider

#### Scenario: Override de modelo
- **WHEN** o usuário executa `translate /path/to/raw.md --model claude-haiku-4-5`
- **THEN** o sistema usa o modelo especificado em vez do default do provider

#### Scenario: Override de idioma alvo
- **WHEN** o usuário executa `translate /path/to/raw.md --target-lang es`
- **THEN** o sistema traduz para espanhol e salva como `raw_es.md`

#### Scenario: Arquivo não encontrado
- **WHEN** o path fornecido não existe
- **THEN** o sistema exibe mensagem de erro clara e encerra

### Requirement: Feedback de progresso
O sistema SHALL exibir feedback durante a tradução.

#### Scenario: Progresso durante execução
- **WHEN** a tradução está em andamento
- **THEN** o sistema exibe: provider/modelo sendo usado, idioma alvo, e confirmação quando salvo

### Requirement: API key ausente
O sistema SHALL validar que a API key do provider está disponível antes de traduzir.

#### Scenario: Key não configurada
- **WHEN** a variável de ambiente da API key do provider não está definida
- **THEN** o sistema exibe erro indicando qual variável é necessária (ex: `ANTHROPIC_API_KEY`)
