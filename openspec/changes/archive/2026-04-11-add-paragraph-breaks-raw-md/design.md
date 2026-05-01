## Context

O Whisper retorna `text` como string contínua e `segments` como lista de objetos com `start`, `end` e `text`. Hoje o `formatter.py` usa `result.get("text")` direto para o `raw.md`, gerando um bloco único. Os segments já contêm timing suficiente para detectar pausas naturais.

## Goals / Non-Goals

**Goals:**
- `raw.md` com parágrafos naturais baseados em pausas do áudio
- Heurística simples usando gap entre segments

**Non-Goals:**
- Análise semântica do conteúdo para decidir parágrafos
- Alterar `raw_timestamps.md` ou `raw_whisper.json`

## Decisions

### 1. Heurística de gap > 2 segundos

**Decisão:** Se o gap entre `segments[i-1]["end"]` e `segments[i]["start"]` for maior que 2 segundos, inserir quebra de parágrafo (`\n\n`).

**Rationale:** Pausas de 2+ segundos em speech geralmente indicam mudança de tópico ou respiração significativa. É uma heurística simples que funciona bem para podcasts, talks e aulas. O valor pode ser ajustado depois se necessário.

**Alternativas consideradas:**
- Agrupar por N segments fixos (ex: cada 10 segments = parágrafo): não respeita a estrutura natural da fala
- Usar pontuação (ponto final) como trigger: Whisper nem sempre pontua corretamente

### 2. Fallback para result.get("text") se segments estiver vazio

**Decisão:** Se `segments` estiver vazio ou ausente, usar `result.get("text")` como antes.

**Rationale:** Robustez — não quebrar se o Whisper retornar formato inesperado.

## Risks / Trade-offs

- **2 segundos pode ser muito ou pouco dependendo do speaker** → Trade-off aceito: funciona bem para a maioria dos casos. Pode expor como configurável no futuro se necessário.
