## Context

Testes reais de tradução revelaram que o output da API vem como wall of text (sem parágrafos), enquanto a skill do Claude Code naturalmente produz texto com quebras. Além disso, o limite de 100k caracteres é alto demais para o Haiku (max output ~8k tokens) e não há validação de respostas vazias.

## Goals / Non-Goals

**Goals:**
- Tradução determinística (temperature=0)
- Output com parágrafos naturais
- Limite seguro para Haiku
- Validações básicas de robustez

**Non-Goals:**
- Chunking de textos longos (futuro)
- Ajuste dinâmico de max_tokens por modelo (futuro)

## Decisions

### 1. temperature=0 em ambos providers

**Decisão:** Adicionar `temperature=0` nas chamadas OpenAI e Anthropic.

**Rationale:** Tradução é tarefa determinística. Variações não são desejáveis.

### 2. System prompt com instrução de parágrafos

**Decisão:** Adicionar ao SYSTEM_PROMPT: "Break the translated text into natural paragraphs separated by blank lines."

**Rationale:** O raw.md do Whisper vem como bloco contínuo. Sem instrução explícita, a API mantém o formato. Com a instrução, o output fica legível e compatível com Obsidian.

### 3. MAX_TEXT_CHARS = 40_000

**Decisão:** Reduzir de 100k para 40k caracteres.

**Rationale:** 40k chars ≈ ~10k tokens de input. Haiku tem output max ~8k tokens. Isso dá margem segura. Textos maiores precisarão de chunking (melhoria futura).

### 4. Validação de resposta vazia e target_lang

**Decisão:** Checar se a resposta da API não é vazia/None antes de retornar. Checar se target_lang não é None/vazio antes de chamar.

## Risks / Trade-offs

- **40k chars pode ser restritivo pra vídeos longos (2h+)** → Trade-off aceito: melhor falhar com mensagem clara do que truncar silenciosamente. Chunking fica pra depois.
