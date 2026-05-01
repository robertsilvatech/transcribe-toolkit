## 1. Module skeleton

- [x] 1.1 Criar pasta `vault_import/` na raiz do projeto.
- [x] 1.2 Adicionar `vault_import/__init__.py` com `__version__ = "0.1.0"` (mesmo padrão de `yt_transcribe/__init__.py` e `translate/__init__.py`).
- [x] 1.3 Criar arquivos vazios: `vault_import/cli.py`, `vault_import/importer.py`, `vault_import/config.py`. Adicionar docstring de módulo em cada um (1 linha).

## 2. Config integration

- [x] 2.1 Implementar `vault_import/config.py` com função `load_config()` que lê `config.yaml` na raiz do projeto e retorna dict da seção `vault_import:`. Cascata: arquivo presente + chave presente → retorna; ausente → retorna `{}`. Reusar pattern do `translate/config.py` se aplicável (sem importar).
- [x] 2.2 Adicionar seção `vault_import:` no `config.yaml` da raiz com `default_vault: ~/Dropbox/SECOND-BRAIN-OBSIDIAN` comentada (template, não default ativo). Documentar a chave em comentário acima.

## 3. Importer engine

- [x] 3.1 Implementar `vault_import/importer.py` com função `validate_input(input_dir: Path) -> dict` que retorna o `meta.json` parseado se válido, ou `raise` com mensagem descritiva se faltar `raw_pt-br.md`, `meta.json`, ou campos obrigatórios.
- [x] 3.2 Implementar `validate_destination(vault: Path, slug: str, force: bool)` que valida vault e `<vault>/raw/` existem, e que o destino não existe a menos que `force=True`. Levantar erro descritivo se falhar.
- [x] 3.3 Implementar `extract_video_id(url: str) -> str | None` para extrair video_id de URLs do YouTube (suporta watch?v=, youtu.be/, embed/). Regex simples; testes pontuais.
- [x] 3.4 Implementar `build_frontmatter(meta: dict, slug: str) -> str` que monta o YAML frontmatter com os 11 campos definidos no spec (`title`, `type: source`, `source_type: transcript`, `url`, `channel`, `duration`, `language: pt-br`, `original_language`, `youtube_video_id`, `ingested`, `tags`). Retorna a string completa com delimitadores `---`.
- [x] 3.5 Implementar `import_to_vault(input_dir: Path, vault: Path, force: bool) -> Path` que orquestra: validate input → validate dest → read raw_pt-br body → build frontmatter → escrever atomicamente em `<vault>/raw/<slug>.md` (write to temp + rename). Retorna o path do arquivo escrito.

## 4. CLI

- [x] 4.1 Implementar `vault_import/cli.py` com `argparse` aceitando: argumento posicional `input_dir`, flags `--vault PATH`, `--force`, `--help`. Resolver vault default via `config.load_config()` se `--vault` ausente; se nenhum, sair com erro.
- [x] 4.2 Implementar função `main()` que: chama `import_to_vault()` em try/except, imprime progresso ao stdout, captura erros e imprime ao stderr com exit code não-zero.
- [x] 4.3 Garantir output: feedback "✓ Validating input...", "✓ Reading meta.json...", "→ Writing <path>...", "✓ Done." em sucesso; mensagens de erro descritivas em falha.

## 5. Pyproject + entry point

- [x] 5.1 Adicionar `vault-import = "vault_import.cli:main"` na seção `[project.scripts]` do `pyproject.toml`.
- [x] 5.2 Verificar se `pyyaml` já é dependência (provável, via `translate`); se não, adicionar em `[project.dependencies]`.
- [x] 5.3 Rodar `uv sync` para registrar o novo entry point.

## 6. Smoke test manual

- [x] 6.1 Identificar uma transcrição existente em `~/Dropbox/OBSIDIAN-ROBERTSILVATECH/03-RECURSOS/transcricoes/` que tenha `raw_pt-br.md` + `meta.json`.
- [x] 6.2 Rodar `uv run vault-import <pasta> --vault ~/Dropbox/SECOND-BRAIN-OBSIDIAN` (sem `--force`).
- [x] 6.3 Verificar: arquivo criado em `~/Dropbox/SECOND-BRAIN-OBSIDIAN/raw/<slug>.md`, frontmatter completo, body é cópia do `raw_pt-br.md`.
- [x] 6.4 Verificar idempotência: rodar de novo o mesmo comando deve falhar com mensagem clara sobre destino existente.
- [x] 6.5 Rodar com `--force` e verificar que sobrescreve sem perda de dados na origem.
- [x] 6.6 Rodar `uv run tools/lint.py` no vault destino para confirmar que continua limpa.

## 7. Documentation

- [x] 7.1 Atualizar `README.md` da raiz do projeto com seção "### vault-import — texto traduzido → vault destino" descrevendo: comando, output esperado, exemplo de pipeline completo (`yt-transcribe` → `translate` → `vault-import`).
- [x] 7.2 Atualizar `AGENT.md` da raiz: adicionar `vault_import/` à árvore de módulos e ao item "Se a feature é diferente → criar nova pasta na raiz".

## 8. Validation

- [x] 8.1 Rodar `uv run vault-import --help` → deve imprimir usage e sair 0.
- [x] 8.2 Rodar `uv run vault-import` (sem args) → deve falhar com mensagem clara sobre argumento posicional.
- [x] 8.3 Rodar `uv run vault-import /caminho/inexistente --vault ~/SB` → deve falhar com mensagem citando o path absoluto.
- [x] 8.4 Confirmar que `yt_transcribe/` e `translate/` continuam funcionando intactos após o apply (smoke test do pipeline existente).
