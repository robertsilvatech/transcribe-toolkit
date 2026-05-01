## 1. translator.py

- [x] 1.1 Adicionar `temperature=0` em `_translate_openai()` e `_translate_anthropic()`
- [x] 1.2 Reduzir `MAX_TEXT_CHARS` de 100_000 para 40_000
- [x] 1.3 Adicionar instrução de quebra de parágrafos no `SYSTEM_PROMPT`
- [x] 1.4 Validar resposta vazia em ambos providers antes de retornar
- [x] 1.5 Validar `target_lang` não é None/vazio em `translate_text()`

## 2. Skill /translate

- [x] 2.1 Atualizar `.github/skills/translate/SKILL.md` com instrução de quebra de parágrafos
- [x] 2.2 Atualizar `.claude/skills/translate/SKILL.md` com mesma instrução
