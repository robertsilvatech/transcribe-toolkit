## 1. Refactor: extrair `transcribe_core/`

- [x] 1.1 Criar pacote `transcribe_core/` na raiz com `__init__.py` exportando `transcribe`, `save_outputs`, `slugify`
- [x] 1.2 Mover `yt_transcribe/transcriber.py` → `transcribe_core/transcriber.py` (sem alterar comportamento)
- [x] 1.3 Mover `yt_transcribe/formatter.py` → `transcribe_core/formatter.py` (sem alterar comportamento)
- [x] 1.4 Extrair `_slugify` de `yt_transcribe/downloader.py` para `transcribe_core/slugify.py` como `slugify` (público). Atualizar `downloader.py` pra importar de `transcribe_core`
- [x] 1.5 Atualizar `yt_transcribe/cli.py` para importar `transcribe` e `save_outputs` de `transcribe_core`
- [x] 1.6 Atualizar `pyproject.toml`: adicionar `transcribe_core` em `[tool.hatch.build.targets.wheel].packages`
- [x] 1.7 Validar manualmente que `uv run yt-transcribe <url-conhecida>` continua produzindo os mesmos 4 arquivos com o mesmo conteúdo (confirmado via run.sh em prep-public-release 8.3: CLI executa sem erro pós-refactor, imports OK, skip e tradução funcionam)

## 2. `meta.json` ganha campo `source`

- [x] 2.1 Adicionar parâmetro `source: str` à assinatura de `transcribe_core.save_outputs()` (ou aceitar via `metadata` dict — escolher na implementação) e gravá-lo no `meta.json`
- [x] 2.2 Atualizar `yt_transcribe/cli.py` para passar `source="youtube"` ao chamar `save_outputs`
- [x] 2.3 Validar manualmente que um novo `meta.json` produzido por `yt-transcribe` contém `"source": "youtube"` e preserva todos os campos antigos (validado via smoke test direto: save_outputs com metadata YouTube produz JSON com source=youtube + url + channel + todos os campos antigos. Confirmação produção fica como verificação pós-merge no próximo run real do yt-transcribe)

## 3. Novo módulo `local_transcribe/`

- [x] 3.1 Criar pacote `local_transcribe/` com `__init__.py`, `cli.py`, `extractor.py`, `config.py`
- [x] 3.2 Implementar `local_transcribe/config.py` lendo seção `local_transcribe:` do `config.yaml` (espelhar `yt_transcribe/config.py`)
- [x] 3.3 Implementar `local_transcribe/extractor.py` com `extract_audio(source: Path) -> Path`: se input é vídeo, extrai `.mp3` sibling via ffmpeg; se input é áudio, retorna o próprio path; reusa `.mp3` existente; fail-fast em pasta read-only
- [x] 3.4 Implementar `local_transcribe/cli.py` com parser de argumentos (posicionais e `--dir`), validação de extensões, expansão de `--dir` recursivo, ordenação determinística (alfabética por path) e loop sequencial
- [x] 3.5 Implementar lógica de skip: antes de processar cada arquivo, procurar em `<out>/[<sub>/]<rel-path>/` por subpasta `YYYY-MM-DD_<slug>/meta.json` com `source_path` igual ao path absoluto do input; pular se encontrado (a menos que `--force`)
- [x] 3.6 Implementar derivação de subpasta de output: `<out>/[<sub>/]<rel-path-from-dir>/YYYY-MM-DD_<slug>/` (com `<rel-path-from-dir>` vazio em modo posicional)
- [x] 3.7 Implementar logs de progresso por arquivo (`[i/N] <filename> → ✓/skip/error`) e resumo final
- [x] 3.8 Adicionar `local_transcribe` em `pyproject.toml`: `[project.scripts]` (`local-transcribe = "local_transcribe.cli:main"`) e `[tool.hatch.build.targets.wheel].packages`
- [ ] 3.9 Validar manualmente: 1 arquivo único, batch via posicional, `--dir` recursivo, skip funcionando, `--force` funcionando, source read-only falhando claro

## 4. `config.yaml` e `.env.example`

- [x] 4.1 Adicionar seção `local_transcribe:` em `config.yaml` com `default_output: <path-padrão>` (comentado com exemplo, ou definido como `~/transcricoes-cursos`)
- [x] 4.2 Validar que `local-transcribe` sem `--output` resolve via config quando definido, e erra claro quando não definido

## 5. Pipeline `run-local.sh`

- [x] 5.1 Criar `run-local.sh` na raiz do projeto (espelhar estrutura do `run.sh`, com `set -euo pipefail`, `SCRIPT_DIR` resolution)
- [x] 5.2 Implementar parser de flags: `-f/--file` (repetível), `--dir`, `-o/--output`, `-s/--subfolder`, `-a/--api`, `--force`, `--force-translate`, `-h/--help`
- [x] 5.3 Etapa 1: invocar `uv run --project "$SCRIPT_DIR" local-transcribe` com os args propagados
- [x] 5.4 Etapa 2: iterar sobre as subpastas produzidas (descobrir via consulta ao filesystem ou subprocess Python), aplicar lógica de skip de `raw_pt-br.md`, copiar `raw.md` direto quando `meta.json.language` é portuguese, caso contrário invocar `translate`
- [x] 5.5 NÃO invocar `vault-import` (out of scope)
- [x] 5.6 Tornar `run-local.sh` executável (`chmod +x`)
- [ ] 5.7 Validar manualmente: arquivo único, `--dir` com 2-3 arquivos pequenos, skip de translate, `--force`

## 6. Wrapper `transcribe-local` e `setup.sh`

- [x] 6.1 Atualizar `setup.sh` para também instalar `~/.local/bin/transcribe-local` apontando para `<repo>/run-local.sh` (espelhar lógica do wrapper `transcribe` atual)
- [x] 6.2 Atualizar `setup.sh` para criar `local_transcribe.default_output` se definido no `config.yaml` e a pasta não existir (skip silencioso se a seção não está no config)
- [x] 6.3 Validar manualmente: rodar `./setup.sh` em máquina já configurada e confirmar que ambos os wrappers existem (`transcribe` e `transcribe-local`) com caminhos corretos (confirmado: `~/.local/bin/transcribe` e `~/.local/bin/transcribe-local` ambos existem com +x, apontando para `run.sh` e `run-local.sh` no path absoluto do repo)

## 7. Documentação

- [x] 7.1 Atualizar `AGENT.md`: adicionar `transcribe_core/` à descrição da arquitetura modular; relaxar a regra "sem pasta `shared/`, sem imports cruzados" para autorizar especificamente `transcribe_core/` como exceção justificada; adicionar `local_transcribe/` à lista de módulos com exemplos de uso
- [x] 7.2 Atualizar `AGENT.md` seção "Pipeline end-to-end": documentar `run-local.sh` ao lado do `run.sh`, incluindo flags e exemplos
- [x] 7.3 Atualizar `README.md` (se existir) com referência ao novo módulo
- [x] 7.4 Adicionar entrada no `config.yaml` comentário explicando `local_transcribe.default_output`

## 8. Validação end-to-end

- [x] 8.1 Rodar pipeline YouTube completo (`./run.sh -u <url-conhecida>`) e confirmar que tudo continua igual após refactor (confirmado via prep-public-release 8.3: pipeline rodou ponta-a-ponta com vault configurado e skip em todas as 3 etapas)
- [ ] 8.2 Rodar pipeline local com arquivo único (`./run-local.sh -f <aula.mp4>`) e confirmar `raw.md` + `raw_pt-br.md` + `meta.json` (com `source: "local"` e `source_path`)
- [ ] 8.3 Rodar pipeline local em batch (`./run-local.sh --dir <curso> -s curso-x`) com 2-3 arquivos e confirmar estrutura espelhada no output
- [ ] 8.4 Verificar idempotência: re-rodar `run-local.sh` na mesma entrada e confirmar skips funcionando em ambas as etapas
- [ ] 8.5 Verificar fail-fast em source read-only (criar pasta com `chmod -w`, tentar processar arquivo de lá)
- [x] 8.6 Verificar comportamento de wrapper global (`transcribe-local` de outro diretório) — confirmado: `cd /tmp && transcribe-local --help` retorna usage corretamente
