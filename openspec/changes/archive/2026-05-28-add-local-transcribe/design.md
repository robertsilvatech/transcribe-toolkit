## Context

O toolkit nasceu YouTube-first. `yt_transcribe/` empacota três responsabilidades:

1. **Ingestão** (yt-dlp + cookies + metadata) — específico de YouTube.
2. **Transcrição** (mlx-whisper local OU OpenAI API + chunking >24MB) — agnóstico de fonte.
3. **Formatação** (raw.md, raw_timestamps.md, raw_whisper.json, meta.json + slugify) — agnóstico de fonte.

A regra do `AGENT.md` é forte: "Cada módulo é autônomo — sem pasta `shared/`, sem imports cruzados". Essa regra existe porque tradução, importação para vault e download YouTube são domínios distintos sem sobreposição de lógica.

A entrada de um segundo ingestor (arquivos locais) muda o cálculo: duas implementações de chunking e formatação são duplicação real, não independência saudável. O usuário concordou em relaxar a regra explicitamente — apenas para criar `transcribe_core/`, não para qualquer compartilhamento futuro.

Downstream, `vault_import/` exige `meta.json["url"]` ([importer.py:64](../../../vault_import/importer.py#L64)) e hard-coda `tags: [transcript, youtube]` no frontmatter. Isso fica fora de escopo desta mudança — `local_transcribe` não usa `vault_import` no pipeline atual.

## Goals / Non-Goals

**Goals:**

- Transcrever arquivos locais de mídia (`.mp4 .mov .mkv .m4a .mp3 .wav`) com a mesma qualidade e shape de output do `yt_transcribe`.
- Permitir batch (positional files OU `--dir <path>` recursivo) com skip por arquivo já transcrito.
- Reaproveitar 100% da lógica de transcrição/chunking/formatação já existente, eliminando duplicação.
- Preservar o CLI atual de `yt-transcribe` (zero quebra de compatibilidade).
- Output organizado por `--subfolder` espelhando a árvore do source.
- Pipeline integrado (`run-local.sh`) para o caminho feliz: local → traduzido pt-br.

**Non-Goals:**

- Suporte de `vault_import` a transcrições locais. Permanece YouTube-only nesta change.
- Modificações no `run.sh` atual.
- Detecção automática de duplicatas por hash de conteúdo (skip é por path em meta.json).
- Suporte a fontes além de arquivos locais e YouTube (ex: Vimeo, Drive, podcasts URL).
- Wrapper de aliases via shell (`alias` em `~/.zshrc`). Apenas wrapper executável em `~/.local/bin/`.
- Paralelização de batch (sequencial por enquanto).

## Decisions

### Decision 1: Criar `transcribe_core/` em vez de duplicar

**Escolha:** Mover `transcriber.py`, `formatter.py` e `_slugify` para um módulo compartilhado `transcribe_core/`. Ambos `yt_transcribe/` e `local_transcribe/` importam de lá.

**Alternativas consideradas:**

- **(A) Duplicar código no novo módulo.** Respeita a regra atual do `AGENT.md`. Custo: ~210 linhas duplicadas; bugfix de chunking precisa ser feito em dois lugares.
- **(B) Estender `yt_transcribe/` para aceitar paths locais.** Quebra a semântica do nome do módulo (não é mais "yt" only), mistura ingestão YouTube com ingestão local na mesma CLI.
- **(C — escolhido) Extrair `transcribe_core/`.** Viola a regra antiga, mas o usuário concordou em relaxá-la explicitamente. Sem duplicação; futura ingestão (Vimeo, podcast) também aproveita.

**Por que (C):** A duplicação de chunking é frágil — o código teve um bugfix recente (chunk size baseado em ms/MB) que se duplicado tem 50% de chance de divergir. O custo de relaxar a regra é local e bem delimitado (apenas `transcribe_core/`; não abre caminho para `utils/` genérico).

### Decision 2: Caching do `.mp3` extraído ao lado do source

**Escolha:** Extração de áudio de `.mp4`/`.mov`/`.mkv` grava `<source>.mp3` no mesmo diretório do arquivo de origem. Em runs subsequentes, se `<source>.mp3` existe, reusa sem re-extrair (mesmo com `--force`, que só re-transcreve).

**Alternativas consideradas:**

- **Temp + cleanup** (igual `yt_transcribe`): zero clutter, mas `--force` paga ffmpeg de novo, e usuário não consegue ouvir o áudio extraído.
- **Audio dentro do output folder**: tudo num lugar, mas se transcreve duas vezes com paths diferentes (`--output`), duplica o `.mp3`.
- **Sibling (escolhido)**: previsível, cacheado, e usuário pode `mpv aula01.mp3` pra escutar trecho.

**Trade-off:** Se a pasta do source é `read-only` (mount externo, Dropbox congelado), `local_transcribe` falha rápido com mensagem clara. Não há fallback automático para `/tmp` — explicitamente uma escolha pra evitar comportamento mágico/surpreendente.

**Determinismo:** `.mp3` é determinístico do `.mp4` (mesmos bitrate/codec). `--force` re-transcreve mas não re-extrai. Se o usuário precisa re-extrair, deleta o `.mp3` manualmente.

### Decision 3: Shape do `meta.json` — aditivo, não repurposing

**Escolha:** Adicionar campo `source: "youtube" | "local"`. Para `source: "local"`, escrever `source_path: <abs-path>` em vez de `url`/`channel` (omitir esses campos).

```json
// YouTube (existente + source novo)
{
  "title": "...", "source": "youtube", "url": "...",
  "channel": "...", "duration_seconds": N, "language": "...",
  "transcribed_at": "...", "model_used": "..."
}

// Local
{
  "title": "...", "source": "local", "source_path": "/abs/path/aula01.mp4",
  "duration_seconds": N, "language": "...",
  "transcribed_at": "...", "model_used": "..."
}
```

**Alternativas consideradas:**

- **Repurpose `url` pra guardar o path** (`url: "file:///..."`). Mantém shape igual, mas `vault_import` lê `url` esperando YouTube e quebra; `extract_video_id` retorna `None` graciosamente, mas o frontmatter fica com `url: "file:///..."`.
- **Aditivo (escolhido)**: campos novos, semânticos. `vault_import` quebra com mensagem clara (`url` ausente), o que é o resultado correto até alguém estender o importer.

### Decision 4: `--subfolder` é manual, sem auto-derivação

**Escolha:** Quando o usuário roda `local-transcribe --dir ~/Cursos/devin-mastering --subfolder devin-mastering`, o output vai pra `<out>/devin-mastering/<relative-path>/YYYY-MM-DD_<slug>/`. Sem flag `--subfolder`, output vai flat em `<out>/YYYY-MM-DD_<slug>/` (risco de colisão de slug se houver `intro.mp4` em pastas diferentes).

**Alternativas consideradas:**

- **Auto-derivar de `basename(--dir)`**: zero flag pra caso comum, mas frágil (renomear pasta → reprocessa tudo). Mágico/surpreendente.
- **Sempre exigir `--subfolder` com `--dir`**: força disciplina, mas verboso para casos simples (uma pasta só).
- **Manual + skip silencioso** (escolhido): consistente com pattern do `vault_import` que também usa `--subfolder`. Colisão em modo flat é responsabilidade do usuário (mesma estória do `yt_transcribe` hoje).

### Decision 5: Pipeline `run-local.sh` não inclui `vault_import`

**Escolha:** `run-local.sh` encadeia `local-transcribe → translate`. Para. Não chama `vault-import`.

**Por quê:** `vault_import` exige `url` no `meta.json` ([importer.py:64](../../../vault_import/importer.py#L64)). Adicionar suporte a `source: "local"` no importer é uma decisão de produto separada (precisa decidir como o vault representa transcrições não-YouTube — tags, frontmatter, etc.). Fora de escopo. `run-local.sh` é honesto sobre o que faz.

### Decision 6: Nomes

- Módulo Python: `local_transcribe/` (espelha `yt_transcribe/`)
- Script CLI: `local-transcribe` (espelha `yt-transcribe`)
- Wrapper: `~/.local/bin/transcribe-local` (não `local-transcribe` pra manter agrupamento por prefixo: `transcribe`, `transcribe-local`)
- Pipeline script: `run-local.sh`

## Risks / Trade-offs

- **[Refactor toca código testado]** → Movimentação de `transcriber.py` e `formatter.py` para `transcribe_core/` preserva comportamento, mas qualquer typo no import quebra `yt-transcribe`. **Mitigação:** rodar `uv run yt-transcribe <url-conhecida>` end-to-end pós-refactor antes de fechar o PR; git permite rollback.

- **[`AGENT.md` perde clareza]** → A regra "sem `shared/`" era um princípio limpo. Relaxar abre brecha pra abuso futuro. **Mitigação:** atualizar `AGENT.md` explicitando que `transcribe_core/` é a *única* exceção autorizada, e que outras seriam novas decisões.

- **[Source read-only falha sem fallback]** → Usuário com mount externo ou pasta sync'ada cloud pode hitar isso. **Mitigação:** mensagem de erro explícita ("source folder is not writable; copy files to a writable location or open an issue if you need /tmp fallback"). Adicionar fallback é trivial depois se realmente surgir.

- **[`vault_import` quebra com `source: "local"`]** → Se o usuário tentar `vault-import` numa pasta produzida por `local_transcribe`, recebe `ImporterError: meta.json is missing required key 'url'`. **Mitigação:** mensagem do importer já é clara. `run-local.sh` não chama `vault-import` — só vai acontecer se o usuário invocar manualmente.

- **[Batch em pasta grande sem feedback]** → 50 arquivos num `--dir` viram 50 transcrições sequenciais. Sem barra de progresso geral. **Mitigação:** logs por arquivo (`[3/50] aula03.mp4 → ...`) deixam o estado óbvio. Paralelização fica pra depois.

- **[Slug derivado só de filename é frágil]** → `aula.mp4` em duas pastas diferentes geram o mesmo slug `aula`. **Mitigação:** modo `--subfolder` (espelha árvore) resolve. Modo flat fica como "responsabilidade do usuário" — mesma postura do `yt_transcribe`.

## Migration Plan

Não há migração de dados — o `meta.json` antigo (sem `source`) continua válido. Apenas vai faltar o campo em transcrições já existentes; readers tolerantes (`vault_import` lê `.get("source")` na futura adaptação) não quebram.

**Ordem de implementação:**

1. Criar `transcribe_core/` movendo `transcriber.py`, `formatter.py`, `slugify.py`. `yt_transcribe/` imports atualizados.
2. Validar `yt-transcribe` funciona idêntico (manual: rodar com URL conhecida, conferir os 4 arquivos).
3. Adicionar campo `source: "youtube"` em `formatter.save_outputs` quando chamado pelo `yt_transcribe`.
4. Criar `local_transcribe/` (CLI, extractor, config).
5. Criar `config.yaml` seção `local_transcribe.default_output`.
6. Criar `run-local.sh` e `setup.sh` install do wrapper.
7. Atualizar `AGENT.md`.

**Rollback:** `git revert` da merge commit. Nenhum dado externo afetado.

## Open Questions

Nenhuma. Todas as decisões foram discutidas e fechadas antes desta proposta.
