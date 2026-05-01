## Context

Hoje `translate_cli.py` usa `output_name = f"raw_{target_lang}.md"` hardcoded. Precisa usar o stem do arquivo de input.

## Goals / Non-Goals

**Goals:**
- `ppt.md` → `ppt_pt-br.md`
- `raw.md` → `raw_pt-br.md` (continua funcionando igual)

**Non-Goals:**
- Mudar diretório de saída (continua na mesma pasta do input)

## Decisions

### 1. Usar `input_path.stem`

**Decisão:** `output_name = f"{input_path.stem}_{target_lang}.md"`

**Rationale:** `Path.stem` retorna o nome sem extensão. Simples, sem edge cases.
