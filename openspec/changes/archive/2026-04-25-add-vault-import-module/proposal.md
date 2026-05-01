## Why

Hoje o pipeline `yt-transcribe → translate` gera transcrições em pt-BR (`raw_pt-br.md`) numa pasta de saída — mas levar essas transcrições para um Second Brain LLM-Wiki (padrão Andrej Karpathy) ainda é manual: o usuário copia o arquivo, renomeia, escreve frontmatter à mão, decide onde dropar.

Esse passo manual quebra o fluxo. Pior: o frontmatter precisa casar com o schema do destino (`source_type`, `url`, `channel`, etc.) — fácil esquecer um campo e atrapalhar o `ingest` do destino depois.

Esta change adiciona um terceiro módulo `vault_import/` que fecha a ponte: pega uma pasta de saída do `yt-transcribe`, lê o `raw_pt-br.md` + `meta.json`, escreve um único arquivo no `raw/` do vault destino com frontmatter completo. CLI manual, sem watch — o humano controla quando acionar.

## What Changes

- **NEW** `vault_import/` no projeto root, alongside `yt_transcribe/` e `translate/`. Mesmo padrão modular: CLI próprio, módulos auxiliares, autônomo, sem cross-imports.
- **NEW** entry point `vault-import` em `pyproject.toml`. CLI: `uv run vault-import <slug-folder> --vault <path-to-vault> [--force]`.
- **NEW** seção `vault_import:` em `config.yaml` para default vault path. Cascata: CLI flags > config.yaml > erro se nada definido.
- **NEW** validação de input: a pasta passada deve conter `raw_pt-br.md` e `meta.json`; o destino `<vault>/raw/` deve existir; recusa overwrite sem `--force`.
- **NEW** geração de frontmatter no destino contendo: `title` (do meta.json), `type: source`, `source_type: transcript`, `url`, `channel`, `duration`, `language: pt-br`, `youtube_video_id`, `ingested: <hoje>`, `tags: [transcript, youtube]`. Apenas o body do `raw_pt-br.md` é copiado — `raw.md`, `raw_timestamps.md`, `raw_whisper.json` ficam na pasta de origem.

## Capabilities

### New Capabilities

- `vault-import`: o módulo bridge `transcribe → vault`. Cobre: CLI flags, leitura da pasta input, validações, geração de frontmatter, escrita atômica em `<vault>/raw/<slug>.md`, integração com config.yaml. **Inspirações:** Karpathy LLM-Wiki pattern (define a forma do destino — `raw/` imutável + frontmatter mandatório); Second Brain vault em `~/Dropbox/SECOND-BRAIN-OBSIDIAN/openspec/specs/vault-structure/spec.md` (R1: raw imutável; R5: frontmatter mandatório).

### Modified Capabilities

Nenhuma. O módulo é puramente aditivo. O `cli-interface` existente é específico do yt_transcribe — não é a CLI compartilhada do projeto inteiro. `vault-import` ganha sua própria spec independente.

## Non-goals

- Sem auto-trigger ao final do `translate` (uma change futura `add-translate-vault-handoff` pode plugar isso).
- Sem watch mode / daemon (over-engineering pra v1).
- Sem clean-up de markdown além do mínimo (não corta cabeçalhos do translate, não normaliza headings).
- Sem suporte a outras fontes além de `raw_pt-br.md` (nem `raw.md` original em outras línguas, nem outros nomes).
- Sem download/transcrição/tradução — esses módulos já existem e ficam intocados.
- Sem classificação de tema no destino — a vault destino tem seu próprio `ingest` workflow que faz isso. `vault-import` é one-way bridge: deposita o arquivo bruto + frontmatter; o `ingest` do destino é quem classifica em temas e gera summaries.

## Impact

- 1 nova spec: `openspec/specs/vault-import/spec.md` após archive.
- ~6 arquivos novos no projeto: `vault_import/{__init__.py, cli.py, config.py, importer.py}`, mais entry-point em `pyproject.toml` e seção `vault_import:` em `config.yaml`.
- Sem breaking changes nos módulos existentes — `yt_transcribe` e `translate` ficam inalterados.
- Nova dependência runtime: `pyyaml` (provável já presente via `translate`); confirmar em `pyproject.toml` durante implementation.
- Documentação: README.md ganha uma seção curta sobre o terceiro módulo + exemplo de pipeline completo.
