## Why

O `raw.md` gerado pelo yt-transcribe é um bloco de texto contínuo sem quebras de parágrafo porque o Whisper retorna o campo `text` como string única. Isso torna o arquivo ilegível no Obsidian e gera traduções igualmente sem estrutura. O Whisper já fornece dados de timing por segmento (`start`, `end`) que permitem detectar pausas naturais e criar parágrafos.

## What Changes

- Alterar `formatter.py` para construir `raw.md` a partir dos segments do Whisper em vez do campo `text` direto
- Usar gaps entre segments (pausa > 2 segundos) como heurística para quebra de parágrafo
- `raw_timestamps.md`, `raw_whisper.json` e `meta.json` não mudam

## Capabilities

### New Capabilities

### Modified Capabilities

- `output-formatting`: `raw.md` passa a ter parágrafos baseados em pausas do Whisper

## Impact

- **yt_transcribe/formatter.py**: lógica de construção do `raw.md` muda de `result.get("text")` para iteração sobre segments com detecção de gaps
- Sem impacto em outros módulos — `raw_timestamps.md` e `raw_whisper.json` permanecem inalterados
