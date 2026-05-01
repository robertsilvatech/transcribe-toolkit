## Context

`translate/translator.py` faz uma única chamada à API do provider (Anthropic ou OpenAI) com o texto inteiro do `raw.md`. No caminho Anthropic, o cliente é instanciado com `max_tokens=16384`. Para vídeos de ~80 min, o input em inglês ocupa ~17k tokens e a tradução para pt-br gera ~22-25k tokens (PT é ~1.3x mais verboso). A API retorna o que cabe nesses 16k e marca `stop_reason="max_tokens"`. A função atual lê `response.content[0].text`, valida apenas se está vazio, e devolve o texto truncado como sucesso. O CLI grava o arquivo e termina com código 0.

O bug é silencioso porque nenhum sinal observável (exceção, exit code, mensagem) indica que houve corte. O usuário só descobre ao abrir o `.md` traduzido e ver que termina no meio de uma frase.

## Goals / Non-Goals

**Goals:**
- Eliminar truncamento silencioso no caminho Anthropic.
- Cobrir, sem chunking, os vídeos longos típicos do uso atual (~3h ou menos).
- Falhar de forma alta e acionável quando o limite for atingido, em vez de gravar arquivo corrompido.

**Non-Goals:**
- Implementar chunking ou streaming. O bug imediato é o limite mal calibrado e a falta de detecção de truncamento; chunking seria sobre-engenharia para o uso atual.
- Mudar o caminho OpenAI. O `_translate_openai` não passa `max_tokens` (usa default do modelo), e o bug reportado é específico do Anthropic. Tratamento simétrico pode entrar em proposta separada se o problema aparecer.
- Adicionar retry automático, fallback para outro modelo, ou seleção dinâmica de `max_tokens` por tamanho de input.

## Decisions

### Decisão 1: `max_tokens=64000` (constante hardcoded)

Subir o limite para o teto de output do Sonnet 4.6 (64k). Cobre vídeos de até ~3h em uma chamada.

**Alternativa considerada**: calcular `max_tokens` dinamicamente a partir do tamanho do input (ex.: `len(input_tokens) * 1.5`). Rejeitada — adiciona complexidade (precisa contar tokens, conhecer fator de expansão por par de idiomas) sem benefício prático: usar 64k fixo não custa mais (a Anthropic cobra por tokens gerados, não por `max_tokens` reservado) e resolve o caso geral.

**Alternativa considerada**: tornar `max_tokens` configurável via `config.yaml`. Rejeitada por ora — YAGNI. Se aparecer caso de uso, é fácil adicionar depois.

### Decisão 2: Detectar `stop_reason == "max_tokens"` e levantar `RuntimeError`

A SDK da Anthropic expõe `response.stop_reason`. Valores possíveis incluem `"end_turn"` (sucesso normal), `"max_tokens"` (cortou no limite), `"stop_sequence"`, `"tool_use"`, etc. Após `max_tokens=64000`, qualquer `stop_reason="max_tokens"` indica que o vídeo é grande demais para o pipeline atual e o usuário precisa saber.

Mensagem do erro deve incluir: tamanho do input em chars, `max_tokens` configurado, e sugestão de ação ("vídeo provavelmente excede ~3h; considere quebrar o input").

**Alternativa considerada**: continuar a tradução com uma segunda chamada usando o texto truncado como prefixo. Rejeitada — vira chunking pela porta dos fundos, sem desenho adequado de fronteiras de chunk e merge.

### Decisão 3: Usar `client.messages.stream()` em vez de `client.messages.create()`

Descoberto durante implementação: a SDK Anthropic recusa requests não-streaming que possam exceder 10 minutos, e com `max_tokens=64000` ela rejeita a chamada de cara com `Streaming is required for operations that may take longer than 10 minutes`. A solução é usar o context manager `client.messages.stream(...)` e coletar o resultado final via `stream.get_final_message()`, que retorna o mesmo objeto `Message` (com `stop_reason`, `content`, etc.) que `create` retornaria.

**Alternativa considerada**: manter `create()` e baixar `max_tokens` para algo que não dispare o limite (ex.: ~16-32k). Rejeitada — derrota o propósito da Decisão 1 e traz de volta o bug de truncamento.

**Alternativa considerada**: streaming "real" com callback por chunk pra mostrar progresso ao usuário. Rejeitada por ora — o CLI atual já é fire-and-forget; adicionar UX de streaming é fora de escopo.

## Risks / Trade-offs

- **Risco**: vídeos > ~3h vão passar a falhar onde antes "funcionavam" (com arquivo truncado). → Mitigação: a falha é o comportamento correto. A mensagem de erro vai dizer ao usuário exatamente o que aconteceu, em vez de deixá-lo descobrir lendo o `.md`. Se for dor real e recorrente, abrir uma proposta de chunking.
- **Risco**: 64k de output reserva bastante quota; em organizações com rate limits apertados, pode contar contra throughput. → Mitigação: quota é cobrada por tokens *gerados*, não reservados. Sem custo adicional.
- **Trade-off**: caminho OpenAI fica assimétrico (sem detecção de truncamento). → Aceito. O bug reportado é Anthropic; consertar OpenAI sem evidência de problema seria especulativo.

## Migration Plan

Sem migration. Mudança de comportamento puramente interna ao módulo `translate`. Nenhum arquivo de saída precisa ser regerado proativamente — usuário re-roda o `translate` para os arquivos truncados que tiver.
