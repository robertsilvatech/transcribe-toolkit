## Why

Após testes reais de tradução, foram identificados problemas de qualidade e robustez: output sem quebras de parágrafo (wall of text), temperatura não-zero gerando variações desnecessárias, limite de caracteres alto demais para o Haiku, e falta de validação de respostas vazias e parâmetros.

## What Changes

- Adicionar `temperature=0` nas chamadas OpenAI e Anthropic
- Reduzir `MAX_TEXT_CHARS` de 100k para 40k
- Adicionar instrução de quebra de parágrafos no system prompt
- Validar resposta vazia da API antes de retornar
- Validar `target_lang` não é None/vazio
- Atualizar skill `/translate` com mesma instrução de parágrafos

## Capabilities

### New Capabilities

### Modified Capabilities

- `translate-engine`: Adicionar temperature=0, reduzir limite de chars, validar resposta vazia, system prompt com quebra de parágrafos
- `translate-skill`: Adicionar instrução de quebra de parágrafos

## Impact

- **translate/translator.py**: temperature, MAX_TEXT_CHARS, SYSTEM_PROMPT, validações
- **`.github/skills/translate/SKILL.md`** e **`.claude/skills/translate/SKILL.md`**: instrução de parágrafos
