## MODIFIED Requirements

### Requirement: Tradução via Anthropic API
O sistema SHALL traduzir texto usando a API da Anthropic quando o provider for `anthropic`, com `temperature=0` e `max_tokens` suficiente para acomodar traduções longas (atualmente `64000`, o teto de output do Claude Sonnet 4.6). O sistema SHALL inspecionar `response.stop_reason` e tratar `"max_tokens"` como falha.

#### Scenario: Tradução bem-sucedida
- **WHEN** o provider é `anthropic`, a `ANTHROPIC_API_KEY` está configurada e a resposta retorna com `stop_reason="end_turn"`
- **THEN** o sistema envia o texto com system prompt de tradução, `temperature=0`, `max_tokens=64000`, e retorna o texto traduzido

#### Scenario: Resposta vazia
- **WHEN** a API retorna resposta vazia ou None
- **THEN** o sistema lança erro informando que a resposta foi vazia

#### Scenario: Resposta truncada por max_tokens
- **WHEN** a API retorna `stop_reason="max_tokens"`
- **THEN** o sistema lança erro informando que a tradução foi truncada, incluindo o tamanho do input em caracteres e sugestão de que o vídeo excede o limite de uma única chamada
- **AND** o sistema NÃO grava o texto truncado em disco
