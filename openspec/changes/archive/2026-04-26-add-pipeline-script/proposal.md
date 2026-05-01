## Why

Hoje o fluxo end-to-end (URL do YouTube → arquivo no vault) exige 3 comandos manuais: `yt-transcribe`, `translate`, `vault-import`. Entre cada etapa, o usuário precisa copiar/colar manualmente o caminho da pasta gerada — que tem slug dinâmico baseado no título do vídeo. Isso é repetitivo e quebra o fluxo, especialmente quando uma das etapas finais falha (ex: API key da tradução faltando) e o usuário precisa retomar.

## What Changes

- Adicionar `run.sh` na raiz do projeto, um shell script que orquestra os 3 módulos em sequência no caminho feliz (URL → vault).
- Aceitar flags `-u`/`--url <url>` (obrigatório) e `-o`/`--output <dir>` (opcional, default `./out`) em qualquer ordem. Flag `-h`/`--help` imprime uso.
- Aceitar variável de ambiente `BROWSER` (default `chrome`) para passar `--cookies-from-browser` ao `yt-transcribe`.
- Usar `set -euo pipefail` para parar imediatamente se qualquer etapa falhar.
- Pular etapas 2 e 3 quando o output já existe (idempotência parcial — etapa 1 sempre roda nesta change).
- Atualizar `AGENT.md` e `README.md` com referência ao novo script.

## Capabilities

### New Capabilities
- `pipeline-orchestration`: novo capability para o script `run.sh` que coordena os 3 módulos existentes via subprocess, sem importá-los.

### Modified Capabilities
<!-- none -->

## Impact

- Código: novo arquivo `run.sh` na raiz. Nenhuma mudança em `yt_transcribe/`, `translate/`, `vault_import/`.
- Dependências: nenhuma nova — usa apenas `bash`, `uv`, e os módulos existentes.
- Docs: `AGENT.md` ganha seção sobre `run.sh`; `README.md` (se existir) ganha exemplo de uso.
- Idempotência da etapa 1 (yt-transcribe) fica fora do escopo — proposta separada `add-yt-transcribe-skip` cobrirá.
