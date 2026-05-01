## ADDED Requirements

### Requirement: Módulo autônomo na raiz do projeto

O módulo SHALL viver em `vault_import/` na raiz do projeto, alongside `yt_transcribe/` e `translate/`. O módulo MUST seguir o mesmo padrão modular: CLI próprio em `cli.py`, módulos auxiliares (`importer.py`, `config.py`), `__init__.py` com versão. O módulo MUST NOT importar de `yt_transcribe/` ou `translate/`.

#### Scenario: Estrutura modular

- **WHEN** o desenvolvedor inspeciona o projeto após esta change ser aplicada
- **THEN** existe a pasta `vault_import/` na raiz com pelo menos `__init__.py`, `cli.py`, `importer.py`, `config.py`, e nenhum dos arquivos importa de `yt_transcribe/` ou `translate/`

### Requirement: Entry point CLI

O sistema SHALL registrar o entry point `vault-import` em `pyproject.toml` apontando para `vault_import.cli:main` (ou função equivalente). O CLI MUST estar disponível via `uv run vault-import`.

#### Scenario: Comando reconhecido

- **WHEN** o usuário executa `uv run vault-import --help`
- **THEN** o CLI imprime usage e sai com código 0

### Requirement: CLI aceita pasta de input e flags

O CLI SHALL aceitar a pasta produzida por `yt-transcribe`+`translate` como argumento posicional. Flags suportadas: `--vault <path>` (override do destino), `--force` (permite overwrite), `--help`.

#### Scenario: Uso básico com vault explícito

- **WHEN** o usuário executa `uv run vault-import ~/transcricoes/2026-04-11_some-slug --vault ~/Dropbox/SECOND-BRAIN-OBSIDIAN`
- **THEN** o sistema lê a pasta input, valida, e escreve `~/Dropbox/SECOND-BRAIN-OBSIDIAN/raw/2026-04-11_some-slug.md`

#### Scenario: Uso com vault default do config.yaml

- **WHEN** `config.yaml` tem `vault_import.default_vault: ~/Dropbox/SECOND-BRAIN-OBSIDIAN` e o usuário executa `uv run vault-import ~/transcricoes/2026-04-11_some-slug` (sem `--vault`)
- **THEN** o sistema usa o vault default e procede normalmente

#### Scenario: Sem vault definido em lugar nenhum

- **WHEN** `config.yaml` não tem `vault_import.default_vault` e o usuário não passa `--vault`
- **THEN** o sistema imprime erro instruindo a configurar `vault_import.default_vault` em `config.yaml` ou usar `--vault <path>`, e sai com código não-zero

### Requirement: Validação de input

Antes de escrever qualquer arquivo, o sistema SHALL validar:

- A pasta input existe.
- Contém `raw_pt-br.md`.
- Contém `meta.json` parseável.
- O `meta.json` contém os campos mínimos: `title`, `url`.

Se qualquer validação falhar, o sistema MUST imprimir erro descritivo (incluindo path absoluto e qual passo do pipeline parece estar faltando) e sair com código não-zero. **Nenhum arquivo de destino MUST ser criado em caso de falha.**

#### Scenario: Pasta input não existe

- **WHEN** o usuário executa `uv run vault-import /caminho/inexistente --vault ~/SB`
- **THEN** o sistema imprime erro mencionando o path absoluto e sai com código não-zero, sem criar arquivos

#### Scenario: raw_pt-br.md ausente

- **WHEN** a pasta input existe mas não tem `raw_pt-br.md`
- **THEN** o sistema imprime erro instruindo a rodar `translate` primeiro e sai com código não-zero

#### Scenario: meta.json ausente

- **WHEN** a pasta input tem `raw_pt-br.md` mas não tem `meta.json`
- **THEN** o sistema imprime erro instruindo a rodar `yt-transcribe` primeiro e sai com código não-zero

#### Scenario: meta.json malformado

- **WHEN** o `meta.json` está presente mas não é JSON válido ou faltam campos obrigatórios (`title`, `url`)
- **THEN** o sistema imprime erro nomeando o problema (parse error ou campo ausente) e sai com código não-zero

### Requirement: Validação de destino

Antes de escrever, o sistema SHALL validar:

- O vault path existe e é diretório.
- `<vault>/raw/` existe e é diretório.

Se inválido, o sistema MUST imprimir erro sugerindo bootstrap ou criação de `raw/` e sair com código não-zero.

#### Scenario: Vault path inexistente

- **WHEN** `--vault /vault/que/nao/existe` é passado
- **THEN** o sistema imprime erro com path absoluto e sai com código não-zero

#### Scenario: Vault sem subpasta raw/

- **WHEN** o vault existe mas não tem `raw/` subpasta
- **THEN** o sistema imprime erro instruindo a criar `<vault>/raw/` ou rodar bootstrap do destino, e sai com código não-zero

### Requirement: Geração de frontmatter

O arquivo escrito em `<vault>/raw/<slug>.md` SHALL ter YAML frontmatter no topo com os seguintes campos derivados de `meta.json`:

- `title`: do campo `meta.json["title"]`.
- `type: source` (literal).
- `source_type: transcript` (literal).
- `url`: do campo `meta.json["url"]`.
- `channel`: do campo `meta.json["channel"]` (ou string vazia se ausente).
- `duration`: do campo `meta.json["duration"]` (em segundos, integer; ou null se ausente).
- `language: pt-br` (literal — sempre, dado que só importa `raw_pt-br.md`).
- `original_language`: do campo `meta.json["language"]` (idioma original do vídeo; ou null).
- `youtube_video_id`: extraído da `url` ou de `meta.json["video_id"]` se presente.
- `ingested`: data de hoje em formato `YYYY-MM-DD`.
- `tags: [transcript, youtube]` (literal — array YAML).

Após o frontmatter (delimitado por `---`), o body MUST ser exatamente o conteúdo do `raw_pt-br.md` (preservando quebras de linha, sem modificações além de strip de whitespace nas extremidades do arquivo).

#### Scenario: Frontmatter completo gerado

- **WHEN** `meta.json` contém `{"title": "Karpathy LLM Wiki", "url": "https://youtube.com/watch?v=ABC123", "channel": "AI Explained", "duration": 3600, "language": "en"}` e a pasta é `2026-04-11_karpathy-llm-wiki`
- **THEN** o frontmatter do arquivo destino contém: `title: "Karpathy LLM Wiki"`, `type: source`, `source_type: transcript`, `url: "https://youtube.com/watch?v=ABC123"`, `channel: "AI Explained"`, `duration: 3600`, `language: pt-br`, `original_language: en`, `youtube_video_id: ABC123`, `ingested: <data-de-hoje>`, `tags: [transcript, youtube]`

#### Scenario: meta.json com campos opcionais ausentes

- **WHEN** `meta.json` tem só `title` e `url`
- **THEN** o frontmatter ainda é gerado, com campos opcionais como string vazia ou `null`, e o sistema NÃO sai com erro

### Requirement: Escrita atômica e refusal de overwrite

O sistema SHALL recusar overwrite se `<vault>/raw/<slug>.md` já existe, a menos que `--force` seja passado. A escrita MUST ser atômica: se o processo for interrompido, o arquivo destino MUST estar ou totalmente escrito ou inexistente — nunca parcial.

#### Scenario: Destino já existe sem force

- **WHEN** `<vault>/raw/2026-04-11_some-slug.md` já existe e o usuário roda `vault-import` sem `--force`
- **THEN** o sistema imprime erro listando o caminho conflitante, sugere `--force` para sobrescrever, e sai com código não-zero sem modificar o arquivo existente

#### Scenario: Destino já existe com force

- **WHEN** `<vault>/raw/2026-04-11_some-slug.md` já existe e o usuário roda com `--force`
- **THEN** o sistema sobrescreve o arquivo destino com o conteúdo regenerado e sai com código 0

#### Scenario: Pasta origem nunca é modificada

- **WHEN** uma execução completa, com sucesso ou falha
- **THEN** os arquivos `raw_pt-br.md`, `raw.md`, `raw_timestamps.md`, `raw_whisper.json`, `meta.json` na pasta origem permanecem byte-identical ao estado pré-execução

### Requirement: Slug derivation

O nome do arquivo destino SHALL ser derivado do nome basename da pasta input. Pasta `2026-04-11_some-slug/` produz arquivo `2026-04-11_some-slug.md`.

#### Scenario: Slug preserva nome da pasta

- **WHEN** a pasta input é `~/transcricoes/2026-04-11_karpathy-s-llm-wiki/`
- **THEN** o arquivo destino é `<vault>/raw/2026-04-11_karpathy-s-llm-wiki.md`

### Requirement: Configuração via config.yaml

O sistema SHALL ler defaults de `config.yaml` na seção `vault_import:`. Chaves suportadas:

- `default_vault`: path absoluto ou com `~` para o vault default.

A cascata de precedência MUST ser: CLI flag > config.yaml > erro (sem fallback hardcoded).

#### Scenario: Config define default_vault

- **WHEN** `config.yaml` contém:
  ```yaml
  vault_import:
    default_vault: ~/Dropbox/SECOND-BRAIN-OBSIDIAN
  ```
  e o usuário executa `uv run vault-import <pasta>` sem `--vault`
- **THEN** o sistema resolve o `~` para o home do usuário e usa esse path como destino

### Requirement: Output de progresso

O sistema SHALL imprimir feedback de progresso conciso ao stdout durante a execução: validações realizadas, path destino sendo escrito, sucesso/falha final. Em caso de sucesso, o sistema MUST imprimir o path absoluto do arquivo escrito.

#### Scenario: Execução bem-sucedida

- **WHEN** uma execução completa com sucesso
- **THEN** stdout contém pelo menos: confirmação de input válido, path absoluto do arquivo destino escrito, e "✓ done" (ou equivalente)

#### Scenario: Execução com falha

- **WHEN** uma validação falha
- **THEN** stderr contém o erro descritivo e o exit code é não-zero
