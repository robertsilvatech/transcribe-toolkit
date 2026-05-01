## Context

O projeto `202604_yt_transcribe` é uma toolkit modular: cada módulo (yt_transcribe, translate) vive numa pasta independente na raiz, com sua própria CLI, sem cross-imports. A regra fundamental no `AGENT.md`:

> Se a feature é algo diferente (insights, RAG, Q&A) → criar nova pasta na raiz.

`vault_import` segue essa regra. É o terceiro módulo, dedicado a transportar a saída do pipeline para um Second Brain externo.

O destino é um vault Karpathy-LLM-Wiki em `~/Dropbox/SECOND-BRAIN-OBSIDIAN`. As specs desse vault impõem:

- **R1 — `raw/` é IMUTÁVEL** (do `vault-structure` capability): nada é escrito ou modificado em `raw/` pelo destino; só inputs externos.
- **R5 — Frontmatter mandatório** dentro de `wiki/`. Para arquivos em `raw/`, o destino aceita arquivos com frontmatter mínimo (`title`, `source_type`) — o `vault_import` deposita já com frontmatter rico para o `ingest` do destino aproveitar.
- **`raw/` flat** (decisão do destino): um arquivo direto em `raw/<slug>.md`, sem subpastas por tipo.

## Goals / Non-Goals

**Goals:**

- Eliminar o passo manual "copiar transcrição traduzida para o Second Brain".
- Gerar frontmatter rico automaticamente, sem o humano ter que lembrar dos campos do schema do destino.
- Falhar de forma segura: nunca sobrescrever sem `--force`, nunca escrever em vault inexistente, nunca tocar `raw.md`/`raw_timestamps.md`/`raw_whisper.json` no origem.
- Manter o módulo autônomo: zero imports de `yt_transcribe/` ou `translate/`.

**Non-Goals:**

- Não orquestra o pipeline (não chama `yt-transcribe` nem `translate` por baixo).
- Não classifica em temas — isso é responsabilidade do `ingest` do vault destino.
- Não modifica os arquivos da pasta de origem (origem é read-only).
- Não suporta outros formatos de origem (ex: arquivos avulsos, outras línguas além de `raw_pt-br.md`).
- Não faz watch nem auto-trigger no final do `translate`.

## Decisions

### D1. Módulo separado, não flag em `translate`

**Decisão:** novo módulo `vault_import/` com CLI própria.

**Alternativa descartada:** flag `--export-to-vault` no `translate`. Mais conveniente, mas viola o princípio modular do projeto e mistura responsabilidades (translate vira responsável por destino externo).

**Por que:** segue o `AGENT.md`; pipeline coeso (`yt-transcribe → translate → vault-import`) com cada passo manual e revisável.

### D2. Manual trigger only, sem watch

**Decisão:** o humano roda `uv run vault-import` quando quer. Sem daemon, sem hook.

**Alternativa descartada:** watch mode (`watchdog` lib observando o output dir). Auto-export quando aparecer novo `raw_pt-br.md`.

**Por que:** controle do humano. Pipeline é manual em todas as etapas; consistência > automação parcial. Watch pode vir numa change futura (`add-vault-import-watch`).

### D3. Frontmatter gerado, não copiado

**Decisão:** `vault_import` constrói o frontmatter do zero a partir do `meta.json`. Não copia frontmatter pré-existente do `raw_pt-br.md` (caso houvesse — atualmente o `translate` produz arquivo sem frontmatter).

**Alternativa descartada:** mesclar frontmatter existente + meta. Mais flexível, mas adiciona complexidade de merge e potencial conflito.

**Por que:** simples, previsível, idempotente. Re-rodar `vault-import` no mesmo input sempre produz o mesmo output (com `--force`).

### D4. Validações estritas antes de escrever

**Decisão:** validar tudo antes de tocar disco. Erros explícitos pra cada classe:

- Pasta input não existe → erro com path absoluto.
- `raw_pt-br.md` ausente → erro mencionando que `translate` precisa ter rodado primeiro.
- `meta.json` ausente → erro mencionando que `yt-transcribe` precisa ter rodado primeiro.
- `meta.json` malformado → erro com indicação do campo faltando.
- Vault path não existe ou não tem `raw/` → erro sugerindo bootstrap.
- Destino `<vault>/raw/<slug>.md` já existe sem `--force` → erro listando o caminho conflitante.

**Por que:** falha cedo > falha no meio. Cada erro orienta como resolver.

### D5. Slug do destino derivado da pasta input

**Decisão:** `<vault>/raw/<slug>.md` onde `<slug>` é o basename da pasta input. Pasta `2026-04-11_karpathy-s-llm-wiki/` → arquivo `2026-04-11_karpathy-s-llm-wiki.md`.

**Alternativa descartada:** `<slug>` derivado do `meta.json["title"]` via slugify. Mais "correto" semanticamente, mas o folder name já é o slug oficial (criado pelo `yt-transcribe`).

**Por que:** consistência com a estrutura existente; idempotência; o `yt-transcribe` já gera slugs ASCII kebab-case.

### D6. Config cascata: CLI > config.yaml > erro

**Decisão:** flag `--vault <path>` tem precedência. Sem flag, lê de `config.yaml` seção `vault_import:` chave `default_vault`. Se nenhum definido, erro pedindo configuração.

**Alternativa descartada:** fallback hardcoded. Cria magic path; pior pra debugging.

**Por que:** consistente com o pattern do `translate` (CLI > config > fallback). Sem fallback hardcoded porque vault path é fortemente pessoal.

### D7. Frontmatter usa `type: source`, não `type: raw-source`

**Decisão:** o campo `type:` no frontmatter dos arquivos depositados em `<vault>/raw/` será `source` (genérico).

**Por que:** o destino vault tem 5 types canônicos (`concept`, `summary`, `moc`, `meta`, `raw-sidecar`). Arquivos em `raw/` não estão dentro de `wiki/` (onde frontmatter é obrigatório por R5), então o type aqui é livre. `source` é descritivo e não colide com nenhum dos 5 types do `wiki/`. Se no futuro o destino vault formalizar um type específico para arquivos em `raw/`, fazemos `MODIFIED` aqui.

## Risks / Trade-offs

- **Risco:** mudanças no schema do destino quebram `vault_import` silenciosamente. **Mitigação:** documentar a versão do schema do destino no proposal; quando o destino mudar, abrir nova change para o `vault_import` se ajustar.
- **Risco:** usuário roda `vault_import` apontando pra vault errado e dropa transcript no lugar errado. **Mitigação:** validação de `<vault>/raw/` exists; mostrar path absoluto antes de escrever; pedir `--force` para overwrite.
- **Risco:** `meta.json` futuramente ganha campos novos que poderiam enriquecer o frontmatter. **Mitigação:** o módulo lê apenas os campos conhecidos hoje (title, channel, url, duration, language, video_id); campos extras são ignorados silenciosamente até uma change futura adicioná-los ao mapping.
- **Trade-off:** sem watch mode, o humano precisa lembrar de rodar `vault-import`. **Aceito** pra v1; controle > automação.

## Migration Plan

Greenfield módulo — não há migração de código existente. Onboarding após apply:

1. Adicionar `default_vault: ~/Dropbox/SECOND-BRAIN-OBSIDIAN` na seção `vault_import:` do `config.yaml` (opcional; CLI flag funciona sem).
2. Rodar pipeline completo manualmente em uma transcrição existente:
   ```
   uv run vault-import ~/Dropbox/OBSIDIAN-ROBERTSILVATECH/03-RECURSOS/transcricoes/2026-04-11_some-slug
   ```
3. Verificar no destino: `~/Dropbox/SECOND-BRAIN-OBSIDIAN/raw/2026-04-11_some-slug.md` deve existir com frontmatter completo.
4. Rodar `uv run tools/lint.py` no vault destino — deve continuar limpa.

Rollback: deletar o arquivo gerado em `<vault>/raw/`. O módulo nunca toca a fonte original.

## Open Questions

- **Q1.** Ao depositar em `<vault>/raw/`, deveria também já popular `<vault>/raw/_INDEX.md`? Atualmente não — esse índice é mantido pelo `ingest` do destino. Mas `vault_import` poderia adicionar uma linha "pendente de ingest" para visibilidade. Decidir em uma change futura.
- **Q2.** Suporte a `raw_<other-lang>.md` (espanhol, inglês, etc.)? Hoje só `raw_pt-br.md`. Adicionar flag `--source-lang pt-br` futuramente.
- **Q3.** Anexar timestamps em formato simplificado no body do arquivo destino (ex: marcadores `[12:34]` a cada N parágrafos)? Hoje não; arquivo destino é texto puro pt-BR. Pode virar `add-timestamp-markers` change.
- **Q4.** Quando o destino vault evoluir e formalizar um `type:` próprio pra arquivos em `raw/`, o `vault-import` precisa de MODIFIED Requirement. Catalogar isso como follow-up.
