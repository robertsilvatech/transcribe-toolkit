## MODIFIED Requirements

### Requirement: Qualidade da tradução
A skill SHALL traduzir mantendo tom conversacional, jargão técnico em inglês quando comum na área, naturalidade no idioma alvo, e quebrando o texto em parágrafos naturais separados por linhas em branco.

#### Scenario: Texto com termos técnicos
- **WHEN** o texto contém termos como "context window", "prompt", "API", "deploy"
- **THEN** a skill mantém os termos técnicos em inglês e traduz o restante naturalmente

#### Scenario: Formatação com parágrafos
- **WHEN** o texto de input é um bloco contínuo sem quebras de parágrafo
- **THEN** o output é formatado com parágrafos naturais separados por linhas em branco
