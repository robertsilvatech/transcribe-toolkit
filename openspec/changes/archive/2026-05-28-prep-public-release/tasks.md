## 1. Sanitização do repo

- [x] 1.1 `git mv config.yaml config.yaml.example`
- [x] 1.2 Editar `config.yaml.example`: substituir paths pessoais por genéricos (`~/Documents/transcribe-toolkit/youtube`, `~/Documents/transcribe-toolkit/local`); `vault_import.default_vault` → `null` com comentário explicando que é opcional
- [x] 1.3 Adicionar ao `.gitignore`: `config.yaml`, `cursos/`, `transcricoes/`, `*.mp3`
- [x] 1.4 Recriar `config.yaml` local (não-rastreado) com os paths atuais do autor, pra preservar o ambiente de trabalho do autor

## 2. LICENSE

- [x] 2.1 Criar `LICENSE` na raiz com texto canônico da MIT License, preenchendo copyright `2026 Robert Silva` (ou nome preferido)

## 3. Sanitização do README

- [x] 3.1 Substituir todos os exemplos com `~/Dropbox/SECOND-BRAIN-OBSIDIAN` por path genérico (ex: `~/Documents/my-vault` ou `<vault>`)
- [x] 3.2 Substituir `~/Dropbox/00-PARA/3_RECURSOS/...` por `~/Documents/transcribe-toolkit/...` nos exemplos de config
- [x] 3.3 Adicionar seção **Quick Start** no topo do README (antes de "Arquitetura modular") com 4-6 comandos copy-paste cobrindo: clone, setup, edit config, primeiro vídeo
- [x] 3.4 Adicionar seção **Compatibilidade** com tabela: Mac M-series (mlx + API), Mac Intel (só API), Linux (só API), Windows (WSL ou só API). Documentar que mlx-whisper é Apple Silicon only
- [x] 3.5 Adicionar seção **Costs & Privacy**: custos das APIs (linkar OpenAI/Anthropic pricing), e disclaimer de que áudio (`--api`) e texto (translate) são enviados pra terceiros
- [x] 3.6 Conferir que não restam `gh-robertsilvatech` ou `Dropbox` em arquivos rastreáveis (excluindo `openspec/`)

## 4. Env var support nos três módulos

- [x] 4.1 `yt_transcribe/config.py`: em `resolve_output_path`, adicionar leitura de `os.environ.get("YT_TRANSCRIBE_OUTPUT")` entre `cli_output` e `cfg.get("default_output")`. Valor vazio (`""`) trata como ausente.
- [x] 4.2 `local_transcribe/config.py`: análogo com `LOCAL_TRANSCRIBE_OUTPUT`
- [x] 4.3 `vault_import/config.py`: em `resolve_vault_path`, adicionar leitura de `os.environ.get("VAULT_PATH")` entre `cli_vault` e `cfg.get("default_vault")`
- [x] 4.4 Atualizar mensagens de erro nos três módulos para mencionar a env var como uma das opções (além da flag CLI e config.yaml)

## 5. Vault opcional em `run.sh`

- [x] 5.1 Antes da etapa 1, computar `VAULT_RESOLVED`: tenta env `VAULT_PATH`, depois subprocess Python chamando `vault_import.config.resolve_vault_path(None)` (capturando o erro silenciosamente); se nenhum, marca como ausente.
- [x] 5.2 Se `-s/--subfolder` ou `-p/--prefix` foram passados E `VAULT_RESOLVED` é ausente: imprimir erro claro e exit 1, antes de qualquer etapa
- [x] 5.3 Após etapa 2, se `VAULT_RESOLVED` é ausente: imprimir aviso ("vault-import skipped — configure VAULT_PATH or vault_import.default_vault") e exit 0 sem invocar `vault-import`
- [x] 5.4 Se `VAULT_RESOLVED` está presente: comportamento atual da etapa 3 preservado

## 6. OS detection em `setup.sh`

- [x] 6.1 No início do `setup.sh`, detectar OS: `OS=$(uname -s)` e definir helper function `install_hint(dep)` que retorna mensagem específica por OS (`brew install` no Darwin, `apt/dnf/pacman` no Linux, genérico no resto)
- [x] 6.2 Substituir a mensagem hardcoded `brew install $dep` no check de dependências por chamada a `install_hint`
- [x] 6.3 Confirmar que o resto do script (`uv sync`, `mkdir -p`, escrita dos wrappers, check de `PATH`) é cross-platform (já é por construção, mas validar mentalmente)

## 7. Bootstrap do `config.yaml` no `setup.sh`

- [x] 7.1 Adicionar etapa **0** (antes do check de dependências, ou logo após) em `setup.sh`: se `config.yaml` não existe e `config.yaml.example` existe, copiar e instruir o usuário a editar
- [x] 7.2 Se `config.yaml` já existe: imprimir mensagem de preservação
- [x] 7.3 Se `config.yaml.example` está ausente: imprimir erro e abortar
- [x] 7.4 Atualizar o comentário inicial do `setup.sh` para mencionar a etapa de bootstrap do config

## 8. Validação manual

- [x] 8.1 Conferir que `git status` após esta change mostra `config.yaml` como deletado (renomeado para example) e `config.yaml.example` como novo arquivo
- [x] 8.2 Rodar `./setup.sh` em um clone fresco (ou diretório temporário simulando) e confirmar que `config.yaml` é criado a partir do example
- [x] 8.3 Rodar `./run.sh -u <url-conhecida>` com `vault_import.default_vault` configurado (caminho atual do autor) e confirmar que comportamento atual é preservado
- [x] 8.4 Rodar `./run.sh -u <url-conhecida>` em um cenário sem vault (temporariamente comentar a chave em `config.yaml`) e confirmar que etapas 1+2 rodam e etapa 3 é pulada com aviso
- [x] 8.5 Rodar `./run.sh -u <url> -s curso-x` sem vault configurado e confirmar erro claro antes da etapa 1
- [x] 8.6 Exportar `YT_TRANSCRIBE_OUTPUT=/tmp/yt-env-test` e rodar `yt-transcribe <url>` sem `--output` e sem chave no config; confirmar que usa `/tmp/yt-env-test`
- [x] 8.7 Análogo pra `LOCAL_TRANSCRIBE_OUTPUT` e `VAULT_PATH`
- [x] 8.8 Conferir que `grep -rn 'Dropbox\|gh-robertsilvatech\|second-brain' . --exclude-dir=openspec --exclude-dir=.git --exclude-dir=.venv` não retorna nada em arquivos rastreáveis
- [x] 8.9 Em uma máquina Linux (ou via Docker/WSL), rodar `./setup.sh` e confirmar que mensagens de install referem-se a apt/dnf, não brew (validado via install_hint isolado com OS=Linux; teste em Linux real fica como verificação opcional)
