## Why

Hoje, pra re-rodar uma etapa do pipeline (porque o output ficou ruim, ou porque algo mudou no módulo) o usuário precisa apagar manualmente o arquivo gerado para fugir do skip automático do `run.sh`. Isso é cerimonial e propenso a erro (apagar arquivo errado, esquecer de qual etapa precisa repetir). Cada etapa já tem o seu mecanismo de force interno (`yt-transcribe --force`, `vault-import --force`), mas o `run.sh` não os expõe.

## What Changes

- Adicionar flag `--force-vault-import` ao `run.sh`. Quando presente, ignora o skip da etapa 3 e passa `--force` para o `vault-import`.
- Adicionar flag `--force-translate` ao `run.sh`. Quando presente, ignora o skip da etapa 2 (o CLI `translate` não tem skip próprio — ele já sobrescreve, então basta pular o `if [[ -f ... ]]`).
- Adicionar flag `--force` (sem sufixo) ao `run.sh` como atalho. Equivale a `--force-translate --force-vault-import` *e* repassa `--force` ao `yt-transcribe` (que já suporta).
- Atualizar `usage()` para listar as três flags novas.
- Atualizar `AGENT.md` na seção do pipeline para documentar as flags.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities
- `pipeline-orchestration`: o requisito "Skip automático de etapas concluídas" passa a ser bypass-able via flags; o requisito "Parser de flags com ordem livre" ganha três flags novas.

## Impact

- Código afetado: `run.sh` (parser de args, etapa 2, etapa 3, `usage`).
- Documentação: `AGENT.md` — seção "Pipeline end-to-end (run.sh)".
- Sem mudanças em código Python: `vault-import` já tem `--force`; `translate` já sempre sobrescreve.
- Comportamento default (sem flags) permanece idêntico.
