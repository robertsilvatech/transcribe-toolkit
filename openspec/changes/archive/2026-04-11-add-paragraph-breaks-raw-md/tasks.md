## 1. formatter.py

- [x] 1.1 Criar função `_build_raw_text(segments, fallback_text)` que itera sobre segments e insere `\n\n` quando gap > 2s
- [x] 1.2 Substituir `result.get("text")` por chamada a `_build_raw_text()` na escrita do `raw.md`
- [x] 1.3 Manter fallback para `result.get("text")` se segments estiver vazio
