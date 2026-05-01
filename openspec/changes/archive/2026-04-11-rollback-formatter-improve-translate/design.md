## Context

A change `add-paragraph-breaks-raw-md` adicionou heurística de gap temporal no formatter.py para quebrar parágrafos. Testes mostraram que a Whisper API retorna segments com gaps < 1s, tornando a heurística ineficaz. A quebra de parágrafos via LLM (no translate) é superior pois usa compreensão semântica.

## Goals / Non-Goals

**Goals:**
- `raw.md` volta a ser output fiel do Whisper (`result.get("text")`)
- Parágrafos ficam como responsabilidade do translate (system prompt já instruído)

**Non-Goals:**
- Alterar o módulo translate (já está correto)

## Decisions

### 1. raw.md como source of truth sem manipulação

**Decisão:** `raw.md` salva `result.get("text").strip()` direto, sem heurísticas.

**Rationale:** O Whisper API não fornece dados de timing úteis para detecção de parágrafos. Tentar manipular o raw gera resultado artificial. O LLM no translate entende semântica e quebra parágrafos naturalmente.

## Risks / Trade-offs

- **raw.md continua wall of text** → Aceito: o raw.md é source of truth do Whisper. Para leitura formatada, usar `raw_pt-br.md` (traduzido) ou `raw_timestamps.md`.
