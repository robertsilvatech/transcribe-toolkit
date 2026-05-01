## Why

Os módulos `yt_transcribe` e `translate` estão misturados no mesmo pacote Python (`yt_transcribe/`). Cada módulo deve ser uma pasta independente na raiz com sua própria CLI. Isso reforça separação de responsabilidades e facilita decidir se uma nova feature pertence a um módulo existente ou a um novo.

## What Changes

- **Criar pacote `translate/`** na raiz com `cli.py`, `translator.py` e `config.py` (movidos de `yt_transcribe/`)
- **Remover** `translate_cli.py`, `translator.py` e `config.py` de `yt_transcribe/`
- **Atualizar** entry points no `pyproject.toml` para apontar para os novos paths
- **Reescrever** `AGENT.md` com visão modular clara: cada módulo é uma pasta independente, regra de sempre questionar se feature pertence a módulo existente ou novo
- **Reescrever** `README.md` com estrutura modular e uso de cada CLI

## Capabilities

### New Capabilities

### Modified Capabilities

- `translate-cli`: Path do módulo muda de `yt_transcribe/translate_cli.py` para `translate/cli.py`
- `translate-config`: Path muda de `yt_transcribe/config.py` para `translate/config.py`. Cada módulo lê sua própria seção do `config.yaml`

## Impact

- **Movimentação de arquivos**: 3 arquivos saem de `yt_transcribe/` para `translate/`
- **pyproject.toml**: entry point `translate` muda de `yt_transcribe.translate_cli:main` para `translate.cli:main`
- **AGENT.md e README.md**: reescritos com visão modular
- **Sem mudança funcional**: comportamento dos CLIs permanece idêntico
