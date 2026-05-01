## MODIFIED Requirements

### Requirement: Tradução via OpenAI API
O sistema SHALL traduzir texto usando a API da OpenAI quando o provider for `openai`, com `temperature=0`.

#### Scenario: Tradução bem-sucedida
- **WHEN** o provider é `openai` e a `OPENAI_API_KEY` está configurada
- **THEN** o sistema envia o texto com system prompt de tradução, temperature=0, e retorna o texto traduzido

#### Scenario: Resposta vazia
- **WHEN** a API retorna resposta vazia ou None
- **THEN** o sistema lança erro informando que a resposta foi vazia

### Requirement: Tradução via Anthropic API
O sistema SHALL traduzir texto usando a API da Anthropic quando o provider for `anthropic`, com `temperature=0`.

#### Scenario: Tradução bem-sucedida
- **WHEN** o provider é `anthropic` e a `ANTHROPIC_API_KEY` está configurada
- **THEN** o sistema envia o texto com system prompt de tradução, temperature=0, e retorna o texto traduzido

#### Scenario: Resposta vazia
- **WHEN** a API retorna resposta vazia ou None
- **THEN** o sistema lança erro informando que a resposta foi vazia

### Requirement: System prompt de tradução
O sistema SHALL usar um system prompt que instrua o LLM a traduzir mantendo tom conversacional, jargão técnico, naturalidade no idioma alvo, e quebrando o texto em parágrafos naturais separados por linhas em branco.

#### Scenario: Qualidade da tradução
- **WHEN** o texto contém termos técnicos em inglês (ex: "agents", "context window", "prompt")
- **THEN** o LLM mantém termos técnicos que são comumente usados em inglês no meio tech e traduz o restante naturalmente

#### Scenario: Formatação com parágrafos
- **WHEN** o texto de input é um bloco contínuo sem quebras
- **THEN** o output é formatado com parágrafos naturais separados por linhas em branco

### Requirement: Validação de tamanho do texto
O sistema SHALL verificar o tamanho do texto antes de enviar para a API.

#### Scenario: Texto dentro do limite
- **WHEN** o texto tem menos de 40.000 caracteres
- **THEN** o sistema envia normalmente

#### Scenario: Texto excede limite
- **WHEN** o texto tem mais de 40.000 caracteres
- **THEN** o sistema exibe erro com o tamanho e sugere que o texto é grande demais para tradução em uma chamada

### Requirement: Validação de target_lang
O sistema SHALL verificar que target_lang não é None ou vazio antes de traduzir.

#### Scenario: target_lang vazio
- **WHEN** target_lang é None ou string vazia
- **THEN** o sistema lança erro informando que o idioma alvo é obrigatório
