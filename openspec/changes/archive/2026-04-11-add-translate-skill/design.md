## Context

Skills no Claude Code são arquivos `.md` em `.github/skills/` ou `.claude/skills/` com frontmatter YAML. São invocadas com `/nome-da-skill` no chat. O Claude Code lê as instruções e executa usando suas ferramentas nativas (Read, Write, Bash, etc.).

O projeto já tem skills do OpenSpec em `.github/skills/`. A nova skill `/translate` segue o mesmo padrão.

## Goals / Non-Goals

**Goals:**
- Skill `/translate <path>` que traduz arquivo .md usando o próprio Claude como LLM
- Salva output como `raw_<lang>.md` na mesma pasta do input
- Idioma alvo padrão: pt-br, configurável via argumento
- Usa mesmas regras de tradução do módulo CLI (manter tom, jargão técnico, etc.)

**Non-Goals:**
- Substituir o módulo `translate/` (CLI serve para automação)
- Batch de múltiplos arquivos na skill
- Integração com config.yaml (skill é simples, sem config externo)

## Decisions

### 1. Skill como SKILL.md simples

**Decisão:** Um único arquivo `SKILL.md` com instruções de tradução. O Claude Code lê o arquivo input com Read, traduz internamente, e escreve com Write.

**Rationale:** Skills são prompts, não código. Não precisa de Python, dependências, ou API keys. O Claude é o engine.

### 2. Idioma via argumento, default pt-br

**Decisão:** `/translate raw.md` traduz para pt-br. `/translate raw.md es` traduz para espanhol.

**Rationale:** Simples, sem flags complexas. A maioria do uso será pt-br.

### 3. Local em .github/skills/

**Decisão:** `.github/skills/translate/SKILL.md` seguindo o padrão existente do projeto.

## Risks / Trade-offs

- **Contexto longo**: arquivos muito grandes podem ocupar muito do context window do Claude → Trade-off aceito: para arquivos grandes, usar o CLI
