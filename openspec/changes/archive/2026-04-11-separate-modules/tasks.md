## 1. Criar pacote translate/

- [x] 1.1 Criar `translate/__init__.py`
- [x] 1.2 Mover `yt_transcribe/translate_cli.py` → `translate/cli.py` (ajustar imports)
- [x] 1.3 Mover `yt_transcribe/translator.py` → `translate/translator.py` (ajustar imports)
- [x] 1.4 Mover `yt_transcribe/config.py` → `translate/config.py` (ajustar path do config.yaml)

## 2. Limpar yt_transcribe/

- [x] 2.1 Remover `translate_cli.py`, `translator.py` e `config.py` de `yt_transcribe/`

## 3. Atualizar pyproject.toml

- [x] 3.1 Alterar entry point `translate` de `yt_transcribe.translate_cli:main` para `translate.cli:main`
- [x] 3.2 Rodar `uv sync` e verificar `uv run translate --help`

## 4. Atualizar documentação

- [x] 4.1 Reescrever `AGENT.md` com visão modular: cada módulo é pasta na raiz, regra de questionar se feature é módulo novo ou existente
- [x] 4.2 Reescrever `README.md` com estrutura modular e uso de cada CLI
