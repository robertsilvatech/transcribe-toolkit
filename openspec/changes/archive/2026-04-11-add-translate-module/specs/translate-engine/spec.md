## ADDED Requirements

### Requirement: Tradução via OpenAI API
O sistema SHALL traduzir texto usando a API da OpenAI quando o provider for `openai`.

#### Scenario: Tradução bem-sucedida
- **WHEN** o provider é `openai` e a `OPENAI_API_KEY` está configurada
- **THEN** o sistema envia o texto com system prompt de tradução e retorna o texto traduzido

### Requirement: Tradução via Anthropic API
O sistema SHALL traduzir texto usando a API da Anthropic quando o provider for `anthropic`.

#### Scenario: Tradução bem-sucedida
- **WHEN** o provider é `anthropic` e a `ANTHROPIC_API_KEY` está configurada
- **THEN** o sistema envia o texto com system prompt de tradução e retorna o texto traduzido

### Requirement: System prompt de tradução
O sistema SHALL usar um system prompt que instrua o LLM a traduzir mantendo tom conversacional, jargão técnico e naturalidade no idioma alvo.

#### Scenario: Qualidade da tradução
- **WHEN** o texto contém termos técnicos em inglês (ex: "agents", "context window", "prompt")
- **THEN** o LLM mantém termos técnicos que são comumente usados em inglês no meio tech e traduz o restante naturalmente

### Requirement: Validação de tamanho do texto
O sistema SHALL verificar o tamanho do texto antes de enviar para a API.

#### Scenario: Texto dentro do limite
- **WHEN** o texto tem menos de 100.000 caracteres
- **THEN** o sistema envia normalmente

#### Scenario: Texto excede limite
- **WHEN** o texto tem mais de 100.000 caracteres
- **THEN** o sistema exibe aviso com o tamanho e sugere que o texto pode ser grande demais para tradução em uma chamada
