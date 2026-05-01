## Why

O nome do arquivo de saída do translate está hardcoded como `raw_<lang>.md`. Ao traduzir qualquer arquivo que não se chame `raw.md` (ex: `ppt.md`, `aula.md`), o output sempre gera `raw_pt-br.md`, perdendo a referência ao arquivo original.

## What Changes

- Output do translate CLI muda de `raw_<lang>.md` para `{nome_original}_{lang}.md`
- Output da skill `/translate` segue a mesma lógica

## Capabilities

### New Capabilities

### Modified Capabilities

- `translate-cli`: Nome do arquivo de saída baseado no nome do input
- `translate-skill`: Mesma lógica de nomeação

## Impact

- **translate/cli.py**: uma linha — `output_name = f"raw_{target_lang}.md"` → `f"{input_path.stem}_{target_lang}.md"`
- **`.github/skills/translate/SKILL.md`** e **`.claude/skills/translate/SKILL.md`**: atualizar instrução de nomeação
