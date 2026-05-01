## Why

A heurística de gap > 2s no formatter não funciona com a OpenAI Whisper API (gaps máximos de 0.88s). A melhor forma de quebrar parágrafos é via LLM na tradução — o system prompt do translate já instrui o LLM a criar parágrafos naturais. O `raw.md` deve permanecer fiel ao output do Whisper (sem manipulação), e a formatação com parágrafos acontece na etapa de tradução.

## What Changes

- **Rollback** do `formatter.py`: remover `_build_raw_text()` e `GAP_THRESHOLD_SECONDS`, voltar a usar `result.get("text")` direto
- **Rollback** do spec `output-formatting`: reverter para versão sem menção a parágrafos

## Capabilities

### New Capabilities

### Modified Capabilities

- `output-formatting`: Reverter para `raw.md` como texto fiel ao Whisper, sem quebra de parágrafos

## Impact

- **yt_transcribe/formatter.py**: remover função `_build_raw_text()` e constante, voltar para `result.get("text")`
- **openspec/specs/output-formatting/spec.md**: reverter spec
- Sem impacto no módulo translate — o system prompt já cuida dos parágrafos na tradução
