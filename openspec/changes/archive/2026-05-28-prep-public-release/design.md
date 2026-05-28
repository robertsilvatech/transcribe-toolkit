## Context

O repo foi escrito como ferramenta pessoal e acumulou paths do autor em vários lugares: `config.yaml` aponta pra `~/Dropbox/00-PARA/3_RECURSOS/...` e `~/Repos/gh-robertsilvatech/second-brain-obsidian`, `README.md` repete `~/Dropbox/SECOND-BRAIN-OBSIDIAN` em exemplos, e `cursos/` é um script de batch com URLs específicas do curso "Mastering Devin". Nenhum `LICENSE` foi adicionado.

Funcionalmente, dois problemas atrapalham terceiros:

1. **`run.sh` força vault-import.** [run.sh:170-198](../../../run.sh#L170-L198) sempre chama `vault-import`, que [exige `default_vault` configurado](../../../vault_import/config.py). Quem não tem vault Obsidian não consegue rodar o pipeline.
2. **`setup.sh` é Mac-only.** Sugere `brew install` pra deps faltantes; Linux/Windows ficam sem orientação.

Já existem boas bases pra resolver isso:

- `run-local.sh` já pula `vault-import` (não chama) — pattern a replicar.
- `*.config.py` já tem cascata `CLI > config.yaml > erro` que aceita um nível intermediário.
- `setup.sh` é idempotente; adicionar um `case "$(uname)" in ...` cobre Linux com pouco custo.

## Goals / Non-Goals

**Goals:**

- Repo tornável público sem vazar paths/dados pessoais.
- Usuário Mac (M ou Intel) consegue clonar e rodar com `setup.sh` em < 5 min.
- Usuário Linux consegue clonar e rodar com `setup.sh` em < 5 min (apenas API mode; mlx-whisper fica fora).
- `vault-import` é opt-in: quem só quer transcrever + traduzir não precisa configurar vault.
- Override de paths via env var pra automações (CI, scripts).
- README serve como first-impression decente, sem assumir background.

**Non-Goals:**

- Testes automatizados / CI (próxima rodada).
- Suporte a Windows nativo (sem WSL).
- Tradução de mensagens de erro pra inglês.
- PyPI distribution.
- README bilíngue.
- Suporte a Intel Mac com mlx-whisper (mlx é Apple Silicon only).

## Decisions

### Decision 1: `config.yaml.example` committed + `config.yaml` gitignored

**Escolha:** Renomear o `config.yaml` atual pra `config.yaml.example`, sanitizar pra paths genéricos (`~/Documents/transcribe-toolkit/...`), e gitignorar `config.yaml` real. `setup.sh` copia `.example` → real se não existe.

**Alternativas consideradas:**

- **(A) `config.yaml` committed com tudo `null`/comentado.** Mantém o arquivo único, mas qualquer commit local do usuário (mudou o path) cria conflito com pulls futuros. Quebra fluxo do autor que já tem paths locais.
- **(B — escolhido) `config.yaml.example` committed + real gitignored.** Espelha pattern do `.env`/`.env.example` já em uso. Sem conflict, sem fricção.
- **(C) Sem config.yaml; tudo via env var.** Mais "cloud-native" mas remove a ergonomia de "edita um arquivo e esquece".

**Trade-off:** Usuários atuais (incluindo o autor) precisam copiar example → real após pull. Mitigado: `setup.sh` faz isso automaticamente; quem já tem config funcionando não perde nada (gitignore não remove arquivo existente).

### Decision 2: Env vars como nível intermediário na cascata

**Escolha:** Cascata vira `CLI flag > env var > config.yaml > erro`. Nomes curtos casados com o CLI: `YT_TRANSCRIBE_OUTPUT`, `LOCAL_TRANSCRIBE_OUTPUT`, `VAULT_PATH`.

**Alternativas consideradas:**

- **`TRANSCRIBE_TOOLKIT_*` prefix unificado:** mais "namespaced" mas chato de digitar; `TRANSCRIBE_TOOLKIT_YT_TRANSCRIBE_OUTPUT` é redundante.
- **Reutilizar nomes do config.yaml (`YT_TRANSCRIBE_DEFAULT_OUTPUT`):** mais explícito mas verboso.
- **Escolhido (curto):** ergonomia ganha. Colisão com env vars de terceiros é improvável (`VAULT_PATH` é o único potencialmente genérico, mas o `vault_import` é o único consumidor).

**Implementação:** Cada `config.py` ganha leitura de `os.environ.get("<NAME>")` entre o `cli_value` e o config dict. Padrão idêntico nos três módulos.

### Decision 3: Vault opcional via detecção de configuração

**Escolha:** `run.sh` pula etapa 3 silenciosamente se `vault_import.default_vault` é null/ausente (e nem env var `VAULT_PATH` nem flag `--vault` foram passados). Se `-s` ou `-p` foram passados sem vault configurado, falha com erro claro.

**Por quê:** o `vault-import` continua exigindo vault — ele É o bridge pra vault. O que muda é o `run.sh`, que hoje força a 3ª etapa. Pra terceiros sem Obsidian, o pipeline natural é `yt-transcribe → translate`, idêntico ao `run-local.sh`.

**Alternativas consideradas:**

- **Adicionar flag `--no-vault` explícita.** Pior: usuário tem que lembrar de passar. Defaults certos > flags explícitas.
- **Sempre executar mas suprimir erro.** Pior: erros silenciosos confundem.
- **Aviso ("skipping vault-import") sempre que pular.** Considerado: pode ser barulhento. Por enquanto sem aviso quando vault genuinamente não configurado; aviso quando flags vault-specific foram passadas.

### Decision 4: Linux support via OS detection no setup.sh

**Escolha:** `setup.sh` detecta OS via `uname -s`:

```bash
case "$(uname -s)" in
  Darwin) BREW_HINT="brew install $dep" ;;
  Linux)  BREW_HINT="(use apt/dnf/pacman) install: $dep" ;;
  *)      BREW_HINT="install $dep manually" ;;
esac
```

Mensagens de install variam por OS; resto do script (`uv sync`, criação de pastas, wrappers, PATH check) já é cross-platform.

**Alternativas consideradas:**

- **Scripts separados `setup-mac.sh` / `setup-linux.sh`.** Pior: duplicação, divergência ao longo do tempo.
- **Detectar gerenciador (apt vs dnf vs pacman) e sugerir comando exato.** Mais útil mas mais complexo. Por enquanto orientar pelo nome do pacote sem comando exato — usuário Linux já está acostumado.

**Limite:** mlx-whisper continua Apple Silicon only. Linux/Intel Mac usam `--api`. Documentado claramente.

### Decision 5: LICENSE MIT

**Escolha:** MIT.

**Por quê:** padrão pra dev tools; permissivo; zero fricção pra contribuidores; compatível com todos os usos previstos (pessoal, profissional, derivativo, comercial).

### Decision 6: gitignore additions

**Escolha:** adicionar `config.yaml`, `cursos/`, `transcricoes/`, `*.mp3`.

**Por quê cada um:**

- `config.yaml`: paths pessoais. Pareado com `config.yaml.example`.
- `cursos/`: pasta de batch scripts pessoais (existe hoje só com `mastering-devin.sh` privado). Permite ao usuário criar scripts seus sem committar.
- `transcricoes/`: caminho default que o `config.yaml.example` vai sugerir; se alguém configurar dentro do repo por engano, não polui o git.
- `*.mp3`: protege contra committar arquivos extraídos por `local_transcribe` (se alguém testar com arquivo no repo).

### Decision 7: README estrutura

**Escolha:** README ganha 3 seções novas no topo, antes da árvore de módulos:

1. **Quick Start** (clone → primeiro vídeo em <60s, comandos copy-paste).
2. **Compatibilidade** (matriz Mac M / Mac Intel / Linux / Windows).
3. **Costs & Privacy** (custos OpenAI/Anthropic, dados enviados).

Exemplos com paths genéricos: `~/Documents/transcribe-toolkit/...` em vez de `~/Dropbox/SECOND-BRAIN-OBSIDIAN`.

## Risks / Trade-offs

- **[Migração silenciosa pra usuários atuais]** → Após pull desta change, quem tinha `config.yaml` committed vai ver o arquivo virar `config.yaml.example`. Se eles `git pull` com mudanças locais no `config.yaml`, conflito. **Mitigação:** documentar no commit message + README; o autor (único usuário hoje) tem `config.yaml` local que será preservado (gitignore só age em arquivos novos, não remove tracking de existentes — mas como o arquivo está sendo renomeado, é uma migração explícita).

- **[Linux mlx-whisper limita modo local]** → Usuários Linux só podem usar `--api`. **Mitigação:** documentado na matriz de compatibilidade. mlx-whisper como `optional-dependency` separado já existe.

- **[Env var collisions]** → `VAULT_PATH` é genérico o suficiente pra colidir com outro projeto. **Mitigação:** documentar; aceitar risco baixo. Se virar problema, renomear pra `TRANSCRIBE_VAULT_PATH`.

- **[`setup.sh` em Linux pode falhar silenciosamente se `uv` não estiver]** → Mesmo problema do Mac hoje. Não regride.

- **[Vault opcional pode confundir usuários]** → "Por que minha etapa 3 não rodou?". **Mitigação:** quando ausente, `run.sh` imprime "ℹ vault não configurado, pulando vault-import. Configure `vault_import.default_vault` em config.yaml ou exporte `VAULT_PATH` pra ativar." — aviso explícito, uma vez.

## Migration Plan

**Single commit, no data migration needed.**

1. Rename `config.yaml` → `config.yaml.example`, sanitizando paths.
2. Add `config.yaml` ao `.gitignore`.
3. Add cursos/, transcricoes/, *.mp3 ao `.gitignore`.
4. Add LICENSE (MIT).
5. Modificar `*/config.py` (3 módulos) pra ler env var entre CLI e config.
6. Modificar `run.sh` pra detectar vault e pular etapa 3.
7. Modificar `setup.sh` pra OS detection + bootstrap de config.yaml.
8. Reescrever README com Quick Start / Compatibilidade / Costs & Privacy + paths genéricos.

**Para o autor pós-merge:**

- O `config.yaml` local (não rastreado após gitignore) permanece intocado. Tudo continua funcionando.
- Pra um novo clone, rodar `setup.sh` cria o `config.yaml` a partir do example.

**Rollback:** `git revert` da merge commit. Nenhum dado externo afetado.

## Open Questions

Nenhuma. Decisões fechadas em conversa: opção B pra config (example + gitignored), env vars curtos, Linux via setup.sh OS-aware, MIT, vault opcional silencioso, escopo via itens 1-10 da audit (testes/CI/EN/PyPI fora).
