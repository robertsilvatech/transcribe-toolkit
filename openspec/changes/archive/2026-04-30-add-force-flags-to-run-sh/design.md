## Context

`run.sh` orquestra três etapas (yt-transcribe → translate → vault-import) com skip automático em cada uma quando o output já existe. Hoje, refazer uma etapa exige apagar o arquivo manualmente. Os módulos individuais já oferecem `--force`: `yt-transcribe --force` re-baixa/re-transcreve, `vault-import --force` sobrescreve o destino. `translate` não tem `--force` porque sempre sobrescreve (o skip de translate é exclusivo do `run.sh`).

## Goals / Non-Goals

**Goals:**
- Permitir re-rodar uma etapa específica sem mexer em arquivos manualmente.
- Manter comportamento default (sem flags) idêntico.
- Nomes de flag autoexplicativos por etapa.

**Non-Goals:**
- Adicionar `--force` ao CLI `translate` (sempre sobrescreve, não há skip lá pra burlar).
- Short flags (`-f`, etc.) — espaço de short flags já está apertado e nomes longos comunicam melhor o efeito.
- Forçar apenas a etapa 1 sem as posteriores (caso já coberto pelo `uv run yt-transcribe --force` direto).

## Decisions

### Decisão 1: Três flags separadas + uma flag agregadora `--force`

Em vez de uma única flag com argumento (ex.: `--force=stage2,stage3`), expor três flags claras: `--force-translate`, `--force-vault-import`, `--force` (todas).

**Alternativa considerada**: flag única com lista. Rejeitada — usuário precisa lembrar nome interno de etapa, parsing fica chato em bash, e ganho zero sobre três flags.

**Alternativa considerada**: tratar `--force` apenas como agregadora e remover as duas específicas. Rejeitada — usuário pode querer refazer só a tradução (LLM diferente, prompt ajustado) sem re-importar; ou refazer só o import (vault diferente, formatação mudou) sem re-traduzir.

### Decisão 2: `--force` engloba etapa 1 também

`--force` (sem sufixo) repassa `--force` para `yt-transcribe`, além de implicar `--force-translate` e `--force-vault-import`. Mental model: "refaz tudo do zero".

**Alternativa considerada**: `--force` cobrir só etapas 2 e 3 (não etapa 1). Rejeitada — comum querer refazer tudo; usuário pode chamar `yt-transcribe --force` direto se só quiser etapa 1.

### Decisão 3: Implementação em bash

Wiring direto no parser de args já existente. Cada flag vira variável `FORCE_TRANSLATE=1`, `FORCE_VAULT_IMPORT=1`. A flag agregadora seta as três (incluindo um `FORCE_YT=1`). As condições de skip nas etapas 2 e 3 incluem `&& [[ "$FORCE_X" -eq 0 ]]`.

## Risks / Trade-offs

- **Risco**: usuário roda `--force` por engano e re-baixa/re-transcreve um vídeo grande, gastando quota da OpenAI Whisper API. → Mitigação: nome explícito, doc clara em `usage()` e `AGENT.md`. Não vamos adicionar prompt de confirmação — `run.sh` é fire-and-forget.
- **Trade-off**: três flags novas aumentam o `usage`. → Aceito; ainda dá pra ler.
