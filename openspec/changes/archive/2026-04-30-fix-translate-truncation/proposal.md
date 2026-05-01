## Why

O módulo `translate` está salvando arquivos truncados como se fossem traduções bem-sucedidas. Para vídeos longos (ex.: 80 min, ~17k tokens em inglês → ~22-25k tokens em pt-br), a saída ultrapassa o `max_tokens=16384` configurado no cliente Anthropic, e a API corta no meio. A função só checa se o conteúdo está vazio — não inspeciona `stop_reason` — então o texto cortado é gravado em disco sem aviso. Usuário só percebe ao abrir o arquivo e ver que falta metade.

## What Changes

- Aumentar `max_tokens` do cliente Anthropic de `16384` para `64000` (limite de output do Claude Sonnet 4.6), permitindo traduzir vídeos de até ~3h em uma única chamada.
- Detectar `response.stop_reason == "max_tokens"` no caminho Anthropic e lançar erro explícito em vez de retornar texto truncado.
- **Fora de escopo**: estratégia de chunking para vídeos > 3h. Bug imediato primeiro; chunking pode virar uma proposta futura se necessário.
- **Fora de escopo**: caminho OpenAI. O bug reportado é no Anthropic (provider default). OpenAI pode ganhar tratamento equivalente em proposta separada se aparecer o mesmo problema.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities
- `translate-engine`: requisito de "Tradução via Anthropic API" passa a exigir (a) `max_tokens` suficiente para traduções longas e (b) detecção de truncamento via `stop_reason`.

## Impact

- Código afetado: `translate/translator.py` (apenas a função `_translate_anthropic`).
- APIs externas: nenhuma mudança de contrato — apenas parâmetro `max_tokens` enviado à Anthropic e leitura de campo já existente da resposta.
- Dependências: nenhuma nova.
- Comportamento observável: traduções que antes truncavam silenciosamente vão (a) completar com sucesso na maioria dos casos e (b) falhar de forma alta e clara nos raros casos restantes (vídeos > ~3h), em vez de gerar arquivo corrompido.
