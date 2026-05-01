## Context

O `yt-transcribe` cria uma subpasta `<YYYY-MM-DD>_<slug>` dentro de `--output`, onde o slug é derivado do título do vídeo (`yt_transcribe/downloader.py:_slugify`). Como o slug só é conhecido após o download de metadata, não é possível saber a pasta destino sem antes consultar o YouTube.

A change `add-pipeline-script` (já implementada) reconheceu essa limitação e deixou a etapa 1 do `run.sh` sempre rodando — essa change resolve o gap, fechando o ciclo de idempotência completa.

## Goals / Non-Goals

**Goals:**
- Re-execução do mesmo URL é barata: nada além de uma consulta leve de metadata.
- Manter o `run.sh` funcionando sem alterações: se yt-transcribe pular, a pasta detectada continua sendo identificável via `ls -td`.
- Detecção robusta: usar URL match no `meta.json` para evitar colisão de slug entre vídeos diferentes.
- Permitir override explícito (`--force`) para forçar reprocessamento.

**Non-Goals:**
- Cache estruturado de metadata. Toda execução faz 1 request leve a YouTube — aceitável e simples.
- Cobrir o caso "metadata mudou no YouTube" (título renomeado pelo uploader). Skip baseado em URL match é suficiente; usuário pode usar `--force` se quiser regerar.
- Reorganizar pastas pré-existentes que não têm `meta.json` (legado). Tratadas como "não encontradas" e processadas normalmente.
- Detectar transcrição parcial/corrompida. Se `raw.md` existe, considera-se válida (mesma política do `run.sh` para etapa 2/3).

## Decisions

**Decisão 1: glob `*_<slug>` (qualquer data) em vez de `<hoje>_<slug>`.**
Rationale: o nome de pasta inclui a data de hoje. Re-executar amanhã o mesmo URL geraria pasta nova mesmo com transcrição existente. Glob por slug isola da data e captura execuções anteriores. Trade-off: aumenta superfície de colisão de slug, mitigado pela checagem de URL no `meta.json`.

**Decisão 2: validação dupla (slug + URL no meta.json).**
Rationale: o slug é truncado a 60 chars e usa apenas alfanuméricos+hífen. Dois vídeos com títulos similares podem colidir. URL match no `meta.json` desambigua de forma definitiva. Custo: 1 leitura de JSON por candidata (irrisório).

**Decisão 3: fazer `touch` na pasta detectada ao pular.**
Rationale: o `run.sh` (change 1) descobre a subpasta via `ls -td $OUT_BASE/*/ | head -1`. Se yt-transcribe pular sem tocar a pasta, ela pode não ser a mais recente quando há outras pastas no `$OUT_BASE` — o `ls -td` retornaria a pasta errada e quebraria as etapas 2 e 3.

`touch <dir>` é um one-liner que resolve a integração sem exigir contrato machine-readable entre yt-transcribe e run.sh. Alternativa considerada: yt-transcribe imprimir o path em formato consumível e run.sh parsear. Fica mais limpo arquiteturalmente, mas exige modificar duas coisas (CLI contract + run.sh) e foi explicitamente fora do escopo da change 1. `touch` mantém integração frouxa e cumpre o objetivo.

**Decisão 4: skip default-on, `--force` para opt-out.**
Rationale: o caso 95% é "se já tá feito, pula". Default explícito de skip = comportamento intuitivo. `--force` (consistente com `vault-import --force`) cobre o cenário de regeneração — debugar transcrição ruim, mudar de modelo Whisper, etc.

**Decisão 5: 2 chamadas a `extract_info` no caso miss (1 só metadata, depois 1 com download).**
Rationale: a primeira chamada (`download=False`) só pega título/metadata pra calcular slug. Se não houver pasta existente, a função `download_audio` original é chamada e ela faz seu próprio `extract_info(download=True)`. Duplicação: 1 request leve adicional. Aceitável pra MVP — yt-dlp é rápido em modo metadata-only. Otimização futura: refatorar `download_audio` para aceitar `info` pré-fetched.

**Decisão 6: cookies repassados também na consulta de metadata.**
Rationale: vídeos não listados ou com restrição podem exigir auth até pra pegar título. Reusar `--cookies-from-browser` na chamada `extract_info(download=False)` mantém comportamento consistente com o download.

## Risks / Trade-offs

- **Risco:** dois vídeos diferentes com títulos cujo slug colide e mesmo URL — impossível por construção (URL é única). **Mitigação:** comparação direta de URL.
- **Risco:** `meta.json` legado sem chave `url` (improvável — sempre foi gravada). **Mitigação:** se `meta.url` ausente ou JSON inválido, ignora candidata e segue procurando.
- **Risco:** request de metadata falha antes do download principal (rede flaky). **Mitigação:** mensagem de erro clara; usuário pode usar `--force` (que ainda assim faz extract_info no path de download principal — não ganha nada nesse cenário, mas não piora).
- **Trade-off:** `touch` é workaround para acoplamento implícito com `run.sh`. **Aceitável:** custo zero, comentado no código, e não afeta uso direto do `yt-transcribe` (CLI fora do pipeline).
- **Trade-off:** sem cache de metadata persistente. **Aceitável:** request leve, complexidade extra não justificada.
