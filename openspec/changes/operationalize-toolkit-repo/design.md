## Context

Hoje o projeto roda só de dentro da pasta `1_PROJETOS/202604_yt_transcribe/` via `./run.sh`. Cada novo vídeo gera ~MB em `./out/`, dentro do repo, e o `.gitignore` tem `output/` (errado — deveria ser `out/`), então tudo acabaria entrando no commit. Os outputs também não têm sync claro com o vault Obsidian (que vive em outra árvore Dropbox).

O projeto é modular: `yt_transcribe/`, `translate/`, `vault_import/` são pastas raiz independentes, sem código compartilhado. `vault_import/` já estabeleceu um padrão sólido pra cascata de config (CLI > `config.yaml` > erro), com `resolve_vault_path()` em `vault_import/config.py`. Vamos espelhar exatamente esse padrão pra `yt_transcribe/`.

O usuário (Robert, Mac M1, zsh) quer:
- Subir como repo privado oficial (`transcribe-toolkit`).
- Invocar `transcribe -u <URL>` de qualquer pasta.
- Ter um setup automatizado pra reproduzir em outra máquina Mac sem decorar passos.

## Goals / Non-Goals

**Goals:**
- Renomear o package pra `transcribe-toolkit` (entry points permanecem).
- Output default vem do `config.yaml`; sem fallback silencioso.
- Comando `transcribe` funciona de qualquer pasta.
- `./setup.sh` em uma máquina Mac limpa deixa tudo pronto (deps + env + alias + pasta de output).
- Idempotência: rodar `./setup.sh` duas vezes não quebra nada.

**Non-Goals:**
- Suporte a Linux/Windows neste change (Mac-only por enquanto; Linux fica pra change futura).
- Empacotar/publicar no PyPI.
- Substituir os 3 entry points atuais (`yt-transcribe`, `translate`, `vault-import`) por um único — eles continuam existindo lado a lado com o novo `transcribe`.
- Migrar configs antigas pra novo formato (não há base instalada além do próprio Robert).
- Auto-update do wrapper quando o repo move de lugar (re-rodar `setup.sh` é a solução).

## Decisions

### Decisão 1: Comando global via wrapper script em `~/.local/bin/transcribe`

**Escolha:** O `setup.sh` instala um shell script em `~/.local/bin/transcribe` que faz `exec "<repo-abs-path>/run.sh" "$@"`. O caminho do repo é resolvido em tempo de install (`$(cd "$(dirname "$0")" && pwd)`), gravado no wrapper.

**Alternativas consideradas:**
- **Alias em `~/.zshrc`** (`alias transcribe='cd /path && ./run.sh'`): polui o shell rc, depende de `cd` (quebra paths relativos passados pelo usuário), não funciona em scripts não-interativos.
- **Entry point Python via `uv tool install`**: faria sentido se `run.sh` fosse Python. Mas `run.sh` orquestra 3 entry points + lógica bash de skip — converter pra Python é fora de escopo.
- **Symlink `~/.local/bin/transcribe → run.sh`**: parecido com wrapper, mas symlinks podem confundir `set -euo pipefail` quando `run.sh` referencia `$0`/dirname pra encontrar arquivos locais. Wrapper com `exec` é mais explícito e robusto.

**Por que `~/.local/bin/`:** Convenção de fato no Mac/Linux pra binários do usuário; muitos setups (incluindo `pip install --user`, `uv tool install`) já usam. Não exige sudo.

### Decisão 2: `setup.sh` faz check de deps mas NÃO instala automaticamente

**Escolha:** O script verifica `uv`, `ffmpeg`, `gh` e imprime instruções claras (`brew install ffmpeg`) se faltar. NÃO roda `brew install` por conta própria.

**Por quê:**
- Instalações silenciosas surpreendem o usuário (especialmente com `sudo` ou Homebrew em paths não-padrão).
- Deps externas (Homebrew) podem estar em estados inconsistentes — diagnóstico humano é mais seguro.
- Mantém o script previsível: ele só toca arquivos do projeto e do `$HOME` do usuário.

**Trade-off:** usuário precisa rodar `brew install ...` antes de tentar `./setup.sh` de novo. Aceito — instruções claras compensam.

### Decisão 3: Wrapper resolve PATH absoluto do repo, não usa env var

**Escolha:** O wrapper instalado em `~/.local/bin/transcribe` tem o caminho absoluto do repo embutido em texto (`exec /Users/.../transcribe-toolkit/run.sh "$@"`).

**Alternativa considerada:** `export TRANSCRIBE_TOOLKIT_HOME=...` no `~/.zshrc` + wrapper genérico que lê a env var.

**Por que caminho absoluto:**
- KISS: zero estado em shell rc.
- Se o usuário move o repo, ele re-roda `./setup.sh` no novo lugar — re-escreve o wrapper.
- Não polui o ambiente com env vars custom.

**Trade-off:** múltiplas cópias do repo em pastas diferentes podem confundir (qual `transcribe` é o ativo?). Aceito — caso de uso real é raro (Robert tem uma cópia).

### Decisão 4: `yt_transcribe/config.py` espelha `vault_import/config.py` exatamente

**Escolha:** Função `resolve_output_path(cli_value: str | None) -> Path`. Cascata: CLI > `config.yaml` `yt_transcribe.default_output` > `ValueError`. Sem fallback silencioso.

**Por quê:** consistência arquitetural. Já existe um padrão validado no projeto; replicar é zero-risco. Também: `vault_import` errar quando faltava config foi uma decisão deliberada do Robert — manter o mesmo comportamento aqui evita "magia" diferente entre módulos.

**Implementação no CLI:** `--output` deixa de ter `required=True`. Após `parse_args()`, chama `resolve_output_path(args.output)`. Erro de resolução é capturado e impresso como mensagem amigável (não stack trace).

### Decisão 5: `run.sh` não muda de localização, só o ponto de entrada externo (wrapper) muda

**Escolha:** `run.sh` continua na raiz do repo, continua sendo invocável diretamente (`./run.sh ...`). O wrapper `transcribe` é só uma fachada.

**Por quê:**
- Quem desenvolve o projeto continua com o fluxo de hoje.
- Reduz superfície de mudança (menos coisa pra quebrar).
- Quem cloná-lo no futuro pode escolher: usa `transcribe` global ou `./run.sh` local.

### Decisão 6: Renomeação `yt-transcribe` (package) → `transcribe-toolkit` é só metadata

**Escolha:** Mudar `name` no `[project]` do `pyproject.toml`. Os entry points (`yt-transcribe = "yt_transcribe.cli:main"`, etc.) NÃO mudam.

**Por quê:**
- O usuário pode continuar invocando `uv run yt-transcribe`, `uv run translate`, `uv run vault-import`.
- O nome do package só aparece no GitHub, em `pyproject.toml`, e em `pip show`.
- Refatorar entry points seria mudança breaking sem benefício real (são todos consistentes com seus módulos).

### Decisão 7: `setup.sh` é idempotente via checks "se já existe, skip"

**Lógica de cada etapa:**
- `uv sync`: sempre roda (uv já é idempotente, é rápido se nada mudou).
- `.env`: cria de `.env.example` se não existe; pula se existe.
- Pasta de output: `mkdir -p` (idempotente por natureza).
- Wrapper `~/.local/bin/transcribe`: sempre re-escreve (o caminho do repo pode ter mudado entre runs).
- PATH check: só verifica e imprime aviso; não modifica `~/.zshrc` automaticamente (modificar shell rc do usuário é invasivo).

## Risks / Trade-offs

- **[Risco] Usuário esquece de rodar `setup.sh` após mover o repo** → wrapper aponta pra path antigo, dá erro confuso. **Mitigação:** README na seção "Setup" enfatiza re-run; mensagem do `setup.sh` no fim diz "se você mover o repo, rode `./setup.sh` de novo".
- **[Risco] Conflito de nomes: usuário já tem outro comando `transcribe` em PATH** → wrapper sobrescreve / é sobrescrito conforme PATH order. **Mitigação:** `setup.sh` faz `command -v transcribe` antes de instalar; se encontrar algo que não é o nosso, avisa e pede confirmação (ou pede pra rodar com `--force`).
- **[Risco] `~/.local/bin` não está no PATH em zsh** → instalação silenciosa, comando não funciona. **Mitigação:** `setup.sh` checa `[[ ":$PATH:" == *":$HOME/.local/bin:"* ]]` e imprime bloco copy-paste pra adicionar ao `~/.zshrc` se faltar.
- **[Trade-off] Quebra `uv run yt-transcribe <url>` (sem `--output`)** sem `default_output` no config → erro explícito. Aceito (alinhado com `vault_import`); README documenta.
- **[Trade-off] Mac-only no setup.sh** → outras máquinas precisam de adaptação. Aceito como escopo desta change; Linux é change futura se/quando necessário.

## Migration Plan

1. Implementar código na ordem da `tasks.md`.
2. Em paralelo (não-código): mover `out/` → `~/Dropbox/00-PARA/3_RECURSOS/yt-transcribe-raw/`. Pode ser feito antes do commit inicial pra não inflar o histórico do git.
3. Verificar que o pipeline antigo (`./run.sh -u <url>`) continua funcionando.
4. Rodar `./setup.sh` na própria máquina do Robert pra validar o fluxo end-to-end.
5. Validar `transcribe -u <URL>` de uma pasta arbitrária.
6. `git init` + commit inicial + `gh repo create transcribe-toolkit --private --source=. --push`.
7. **Rollback:** `git` é o backstop; se algo quebrar, `git revert` da change. O wrapper pode ser removido manualmente: `rm ~/.local/bin/transcribe`.

## Open Questions

- Nenhuma — escopo confirmado com o usuário antes da proposta.
