## 1. Renomeação e metadata do projeto

- [x] 1.1 Mudar `name = "yt-transcribe"` → `name = "transcribe-toolkit"` em `pyproject.toml` (campo `[project].name`); manter os entry points `yt-transcribe`, `translate`, `vault-import` inalterados
- [x] 1.2 Verificar que `uv sync` continua funcionando após a renomeação (regenera `uv.lock` se necessário)

## 2. Output configurável (yt_transcribe)

- [x] 2.1 Criar `yt_transcribe/config.py` com função `resolve_output_path(cli_value: str | None) -> Path` espelhando `vault_import/config.py` (cascata: CLI > `config.yaml` `yt_transcribe.default_output` > `ValueError` com mensagem instrucional)
- [x] 2.2 Adicionar seção `yt_transcribe:` ao `config.yaml` na raiz com `default_output: ~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw`
- [x] 2.3 Em `yt_transcribe/cli.py`: remover `required=True` do argumento `--output`; após `parse_args()`, substituir `Path(args.output).expanduser().resolve()` por `resolve_output_path(args.output)`; capturar `ValueError` e imprimir mensagem amigável + `sys.exit(1)`
- [x] 2.4 Validar manualmente: `uv run yt-transcribe <url>` (sem `--output`) usa o caminho do config; `uv run yt-transcribe <url> --output /tmp/x` sobrescreve
- [x] 2.5 Validar manualmente: temporariamente remover a seção `yt_transcribe:` do config e rodar `uv run yt-transcribe <url>` sem `--output` — deve falhar com mensagem clara

## 3. Atualização do run.sh

- [x] 3.1 Remover `OUT_BASE="./out"` (default hardcoded); inicializar como `OUT_BASE=""`
- [x] 3.2 Construir `YT_ARGS` sem `--output` quando `OUT_BASE` estiver vazio; com `--output "$OUT_BASE"` quando o usuário passou `-o`
- [x] 3.3 Após etapa 1, se `OUT_BASE` estiver vazio, resolver via `OUT_BASE=$(uv run python -c "from yt_transcribe.config import resolve_output_path; print(resolve_output_path(None))")` antes do `ls -td "$OUT_BASE"/*/`
- [x] 3.4 Atualizar `usage()` em `run.sh` removendo `default: ./out` da descrição de `-o`/`--output`; documentar que default vem do `config.yaml`
- [x] 3.5 Validar manualmente: `./run.sh -u <url>` (sem `-o`) usa pasta do config; `./run.sh -u <url> -o /tmp/x` usa `/tmp/x`

## 4. Setup automatizado (setup.sh)

- [x] 4.1 Criar `setup.sh` na raiz com `#!/usr/bin/env bash` + `set -euo pipefail` + permissão `+x`
- [x] 4.2 Implementar check de deps: `command -v uv` / `command -v ffmpeg` / `command -v gh`; se faltar qualquer um, imprimir comando `brew install <dep>` e `exit 1`
- [x] 4.3 Rodar `uv sync` (sempre); imprimir mensagem antes/depois pra feedback
- [x] 4.4 Se `.env` não existir e `.env.example` existir, copiar `.env.example` → `.env` e imprimir aviso "edite com suas API keys"; se `.env` já existe, imprimir "preservado"
- [x] 4.5 Resolver pasta de output via `uv run python -c "from yt_transcribe.config import resolve_output_path; print(resolve_output_path(None))"` e fazer `mkdir -p` nela; tratar erro se config não tiver `default_output` (instruir usuário a editar config primeiro)
- [x] 4.6 Resolver path absoluto do repo: `REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`
- [x] 4.7 Garantir que `~/.local/bin` existe (`mkdir -p ~/.local/bin`)
- [x] 4.8 Escrever wrapper em `~/.local/bin/transcribe` com conteúdo `#!/usr/bin/env bash\nexec "<REPO_ROOT>/run.sh" "$@"` (interpolação literal do path); `chmod +x` no wrapper
- [x] 4.9 Verificar se `~/.local/bin` está no PATH (`[[ ":$PATH:" == *":$HOME/.local/bin:"* ]]`); se não, imprimir bloco copy-paste pra adicionar `export PATH="$HOME/.local/bin:$PATH"` ao `~/.zshrc` (não modificar shell rc automaticamente)
- [x] 4.10 Imprimir mensagem final: "Setup completo. Próximos passos: 1) editar `.env` com suas API keys; 2) (se necessário) atualizar PATH e abrir nova aba do terminal; 3) testar: `transcribe -u <url>`"
- [x] 4.11 Validar idempotência: rodar `./setup.sh` duas vezes consecutivas — segunda execução deve completar sem erros, pulando ou re-aplicando conforme apropriado

## 5. Correção do .gitignore

- [x] 5.1 Remover linha `output/` (errada — pasta nunca se chamou assim)
- [x] 5.2 Adicionar: `out/`, `.DS_Store`, `.idea/`, `.vscode/`, `*.swp`, `build/`, `*.log`
- [x] 5.3 Confirmar que `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `*.egg-info/`, `dist/` continuam presentes

## 6. README

- [x] 6.1 Trocar título "# Transcribe Toolkit" mantendo descrição "Projeto modular para transcrição de áudio/vídeo (YouTube hoje, expansível pra outras fontes), com pipeline opcional de tradução via LLM e export pra vault Obsidian/Karpathy-LLM-Wiki"
- [x] 6.2 Adicionar seção **Setup (nova máquina Mac)** logo após Requisitos: clone do repo → `./setup.sh` → editar `.env` → `transcribe -u <url>`
- [x] 6.3 Adicionar seção **Comando global `transcribe`** explicando que após o setup o comando funciona de qualquer pasta, com mesmos args do `./run.sh`
- [x] 6.4 Atualizar exemplos do `run.sh` removendo menções a `./out` como default; mencionar que default vem do `config.yaml`
- [x] 6.5 Atualizar bloco de `config.yaml` na seção "Configuração" pra incluir a nova seção `yt_transcribe.default_output`
- [x] 6.6 Adicionar nota "## Arquitetura modular" curta: cada módulo é pasta raiz independente, sem `shared/`, sem imports cruzados; `yt_transcribe/` é uma das fontes de ingestão (futuras: aulas locais, podcasts, etc.)
- [x] 6.7 Manter intactas as seções já existentes: módulos individuais, `/translate` skill, `vault-import`

## 7. Operacionalização (one-shot, fora do código)

- [x] 7.1 Mover conteúdo de `out/` (15MB) pra `~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw/` via `mkdir -p ~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw && mv out/* ~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw/ && rmdir out`
- [ ] 7.2 Validar end-to-end pré-commit: `./run.sh -u <url-teste-curto>` deve usar a nova pasta de output
- [x] 7.3 Rodar `./setup.sh` na própria máquina pra validar o fluxo
- [x] 7.4 Validar comando global: `cd ~ && transcribe -h` (deve imprimir help do `run.sh`)
- [x] 7.5 `git init` na raiz do projeto
- [x] 7.6 Verificar `git status` — confirmar que `.env`, `.venv/`, `out/` (caso ainda exista por engano) NÃO aparecem como untracked
- [x] 7.7 `git add .` + `git commit -m "Initial commit: transcribe-toolkit"` (commit message a confirmar com o usuário antes)
- [x] 7.8 `gh repo create transcribe-toolkit --private --source=. --remote=origin --push`
- [ ] 7.9 Confirmar visualmente no GitHub que o repo foi criado privado e que `.env` não está no histórico
