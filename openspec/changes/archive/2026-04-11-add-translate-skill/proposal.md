## Why

O módulo `translate/` usa APIs pagas (OpenAI/Anthropic) para traduzir texto. O usuário já tem plano Claude Max, que permite usar Claude Code como LLM interativo sem custo adicional por token. Uma skill `/translate` no Claude Code permite traduzir arquivos diretamente no contexto de trabalho, usando o próprio Claude como engine de tradução — zero custo extra, mesmo resultado.

## What Changes

- Criar skill `/translate` em `.github/skills/translate/SKILL.md`
- A skill recebe um path de arquivo `.md`, lê o conteúdo, traduz para pt-br (ou idioma configurado), e salva como `raw_<lang>.md` na mesma pasta
- Atualizar `AGENT.md` e `README.md` com documentação da skill

## Capabilities

### New Capabilities

- `translate-skill`: Skill do Claude Code que traduz arquivos .md usando o próprio Claude como engine, sem custo de API

### Modified Capabilities

## Impact

- **Novo arquivo**: `.github/skills/translate/SKILL.md`
- **Sem dependências Python**: a skill usa apenas as ferramentas nativas do Claude Code (Read, Write)
- **Complementa o módulo `translate/`**: skill para uso interativo, CLI para automação/scripts
