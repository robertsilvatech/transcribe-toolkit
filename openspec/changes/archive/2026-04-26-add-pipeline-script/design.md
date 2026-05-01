## Context

O projeto segue arquitetura modular estrita: cada feature é uma pasta independente na raiz com sua própria CLI, sem imports cruzados (ver `AGENT.md`). Os 3 módulos existentes (`yt_transcribe`, `translate`, `vault_import`) já cobrem o caminho completo de URL → vault, mas exigem invocação manual sequencial.

Uma feature de orquestração não pertence a nenhum dos 3 módulos — não é sobre download, tradução, ou import. A regra fundamental do projeto diz que features que não pertencem a um módulo existente devem virar módulo novo na raiz. Um shell script único atende esse caso sem o overhead de criar um módulo Python completo.

## Goals / Non-Goals

**Goals:**
- Um único comando que faz URL → vault no caminho feliz.
- Falha imediata e clara se qualquer etapa falhar (`set -euo pipefail`).
- Skip automático nas etapas 2 e 3 quando o output já existe — permite retomada após falha intermediária (ex: API key errada na etapa 2).
- Zero acoplamento com os módulos: invocação via `uv run <cli>`, não via import.
- Cobrir cenário de bot-check do YouTube por padrão (cookies do Chrome).

**Non-Goals:**
- Idempotência da etapa 1 (yt-transcribe). Fica para a change `add-yt-transcribe-skip`.
- Flags pass-through (`--api`, `--target-lang`, `--vault`, etc.). Cenários customizados continuam usando os comandos individuais.
- Paralelização das etapas. As 3 são naturalmente sequenciais (etapa N consome output da N-1).
- Suporte a Windows / outras shells. Bash em macOS/Linux é suficiente para o uso do projeto.
- Logging estruturado, retry, ou observability — escopo é "script de conveniência", não pipeline industrial.

## Decisions

**Decisão 1: shell script, não módulo Python.**
Rationale: o trabalho é puramente coordenação de subprocesses + checagem de arquivos. Bash faz isso em ~25 linhas. Um módulo Python adicionaria boilerplate (cli.py, pyproject entry point, testes) sem ganho — o script não tem lógica de negócio própria.

**Decisão 2: invocação via subprocess (`uv run`), não import.**
Rationale: respeita a regra "sem imports cruzados" do `AGENT.md`. Cada módulo continua autônomo. Custo (overhead de start de processo) é desprezível comparado ao tempo de download/transcrição/tradução.

**Decisão 3: descobrir a subpasta criada via `ls -td $OUT_BASE/*/ | head -1`.**
Rationale: o slug é gerado dinamicamente dentro do `yt-transcribe` a partir do título do vídeo, não dá pra prever. Alternativas consideradas:
- Parsear stdout do `yt-transcribe`: frágil (mudança de UI quebra).
- Snapshot antes/depois (`comm`): mais robusto contra race, mas no uso single-user nada mais escreve em `$OUT_BASE` em paralelo.
- Modo machine-readable (`--print-json`): exige modificar `yt-transcribe`, fora do escopo desta change.

`ls -td | head -1` é pragmático e funciona em uso pessoal. Race teórica aceita.

**Decisão 4: skip automático apenas nas etapas 2 e 3.**
Rationale: a etapa 1 produz a pasta cujo nome só é conhecido após o download (slug do título). Não dá pra checar "essa URL já foi transcrita?" sem antes baixar metadata. Idempotência completa requer modificar `yt-transcribe` — proposta separada (`add-yt-transcribe-skip`).

Critérios de skip:
- Etapa 2 (translate): pula se `$DIR/raw_pt-br.md` já existe.
- Etapa 3 (vault-import): pula se `$VAULT/raw/$SLUG.md` já existe (slug = nome da subpasta = `input_dir.name` no importer).

**Decisão 5: descobrir o vault via Python inline.**
Rationale: `vault_import` lê o vault default de `config.yaml`. Replicar a lógica de leitura YAML em bash + expansão de `~` seria frágil. Chamar `uv run python -c "from vault_import.config import resolve_vault_path; print(resolve_vault_path(None))"` reusa a lógica existente em uma linha. É o único ponto onde o script "conhece" um módulo, mas é via subprocess Python — não import direto.

**Decisão 6: `BROWSER=chrome` por padrão, override via env var.**
Rationale: o usuário confirmou que cookies por padrão é desejável (reduz fricção em vídeos não listados / bot-check). `chrome` é o navegador padrão na maioria dos setups. Override via `BROWSER=firefox ./run.sh ...` é o idioma shell esperado e não polui a interface de flags.

**Decisão 7: flags `-u/--url` e `-o/--output` em vez de argumentos posicionais.**
Rationale: o usuário re-edita o último argumento no histórico do shell e quer ordem livre entre URL e output. Posicionais forçam ordem fixa; flags resolvem isso de forma idiomática Unix. Decisão também abre porta para flags futuras (ex: `--force`, `--browser`) sem reorganizar a interface. Custo: usuário digita 4 chars a mais por chamada (`-u `, `-o `). Aceitável dado o ganho de previsibilidade. Parser feito com `while/case` (em vez de `getopts` builtin) para suportar both short e long flags.

## Risks / Trade-offs

- **Risco:** `ls -td | head -1` pega a pasta errada se outra coisa criar pasta em `$OUT_BASE` durante a execução. **Mitigação:** uso single-user; documentar a suposição. Se virar problema real, migra para snapshot.
- **Risco:** se o usuário rodar o mesmo URL duas vezes em dias diferentes, a etapa 1 sempre re-baixa (slug muda por causa da data). **Mitigação:** é o comportamento esperado nesta change; `add-yt-transcribe-skip` cobrirá.
- **Risco:** dependência do `vault_import.config.resolve_vault_path` — se a função for renomeada, o script quebra. **Mitigação:** acoplamento mínimo (uma linha), fácil de atualizar; documentar nos comentários do script.
- **Trade-off:** sem flags pass-through, cenários como `--api` exigem invocar os comandos manualmente. **Aceitável:** o caso 80% é o caminho feliz; complexidade extra não compensa.
- **Trade-off:** skip por presença de arquivo é aproximação — não detecta arquivo corrompido/parcial. **Aceitável:** as etapas escrevem arquivos completos ou falham (translate escreve no fim; vault-import usa rename atômico).
