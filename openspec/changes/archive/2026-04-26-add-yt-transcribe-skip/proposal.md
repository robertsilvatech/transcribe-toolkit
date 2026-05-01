## Why

Hoje o `yt-transcribe` sempre baixa e transcreve, mesmo quando o vídeo já foi processado em uma execução anterior. Isso desperdiça tempo (download + transcrição podem levar minutos) e consumo de API (Whisper) sempre que o usuário re-executa — cenário comum durante iteração no `run.sh` ou ao retomar após falha intermediária. A change `add-pipeline-script` deixou explícito: a etapa 1 do pipeline é o único ponto sem idempotência, e essa lacuna agora é a única razão pela qual `./run.sh <url>` repetido não é totalmente "free".

## What Changes

- `yt-transcribe` consulta metadata leve do vídeo (`extract_info(download=False)`) antes de baixar áudio.
- Se já existir uma subpasta `<output>/*_<slug>/` (qualquer data) com `raw.md` + `meta.json` cuja `url` casa com a URL solicitada, o sistema imprime mensagem de skip e retorna sem baixar nem transcrever.
- A pasta detectada tem seu mtime atualizado (`touch`) ao pular, garantindo que `ls -td` no `run.sh` continue identificando a pasta correta.
- Adicionar flag `--force` em `yt-transcribe` para desabilitar o skip e forçar re-download/re-transcrição.
- Documentar comportamento no `AGENT.md` e `README.md`.
- Atualizar a seção 3 de `tasks.md` da change `add-pipeline-script` (limitação conhecida) e a seção "Pipeline end-to-end" do AGENT.md, removendo a nota "etapa 1 sempre roda".

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `audio-download`: passa a checar pasta existente antes de baixar; pula download/transcrição se já houver transcrição válida para a URL.
- `cli-interface`: ganha flag `--force` para sobrepor o skip.

## Impact

- Código: `yt_transcribe/cli.py` (flag + check de skip), `yt_transcribe/downloader.py` (função para pegar metadata sem download + função para encontrar pasta existente).
- Dependências: nenhuma nova — `yt-dlp` já suporta `download=False`.
- Custo de rede: 1 request adicional de metadata por execução (rápido). Pode-se otimizar depois reusando o info entre as duas chamadas.
- Docs: `AGENT.md` e `README.md` ganham nota sobre `--force` e comportamento idempotente.
