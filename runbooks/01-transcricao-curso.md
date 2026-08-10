# Runbook 01 — Transcrição de curso EAD

**Objetivo:** transcrever todas as aulas de um curso baixado (`$CURSO/videos/*.mp4`) para `$CURSO/transcriptions/<slug-da-aula>/` com `raw.md`, `raw_timestamps.md`, `raw_whisper.json` e `meta.json`.

**Duração típica:** ~1-2 min por hora de vídeo (via API). **Custo:** ~$0.36/hora de vídeo (whisper-1, $0.006/min).

---

## Etapa 0 — Pré-checagens

```bash
CURSO="/caminho/da/raiz/do/curso"   # a pasta que contém videos/ e transcriptions/

# 0.1 Estrutura esperada existe?
ls "$CURSO/videos" | head          # deve listar os .mp4
ls -d "$CURSO/transcriptions"      # deve existir (o downloader cria vazia)

# 0.2 Arquivos estão baixados de verdade? (Dropbox online-only quebra o ffmpeg)
# Se algum arquivo listar tamanho ~0 ou o Finder mostrar ícone de nuvem,
# marque a pasta como "Disponível offline" no Dropbox antes de continuar.
du -sh "$CURSO/videos"

# 0.3 Estimar duração total e custo antes de gastar
total=0
for f in "$CURSO/videos"/*.mp4; do
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
  total=$(echo "$total + ${d:-0}" | bc)
done
echo "Total: $(echo "scale=1; $total/60" | bc) min — custo API ≈ \$$(echo "scale=2; ($total/60)*0.006" | bc)"
```

## Etapa 1 — Testar com 1 aula

```bash
task transcribe-course-api LIMIT=1 -- "$CURSO"
```

O que a task faz: `local-transcribe --api --no-date --limit 1 --dir "$CURSO/videos" --output "$CURSO/transcriptions"`.

**Verificar o resultado:**

```bash
ls "$CURSO/transcriptions"                          # 1 pasta com o slug da aula (sem data)
SUB=$(ls "$CURSO/transcriptions" | head -1)
head -5 "$CURSO/transcriptions/$SUB/raw.md"          # texto faz sentido?
python3 -c "import json; m=json.load(open('$CURSO/transcriptions/$SUB/meta.json')); print(m['language'], m['duration_seconds'])"
```

Critérios de aceite: texto legível no idioma certo, `language` correto, `duration_seconds` > 0.

## Etapa 2 — Rodar o lote inteiro

```bash
task transcribe-course-api WORKERS=10 -- "$CURSO"
```

- `WORKERS=10` transcreve até 10 aulas em paralelo (só no modo API, que é limitado por rede — um curso de ~6h cai de ~40min pra ~5min). Omitir = sequencial.
- A aula da Etapa 1 será **pulada** (skip por `source_path` no meta.json).
- Pode interromper (Ctrl+C) e re-rodar à vontade: continua de onde parou.
- Saída esperada ao final: `Resumo: N transcritos, M pulados, 0 com erro.`

## Etapa 3 — Verificação final

```bash
# Nº de transcrições == nº de vídeos?
ls "$CURSO/videos"/*.mp4 | wc -l
ls -d "$CURSO/transcriptions"/*/ | wc -l

# Alguma pasta sem raw.md? (indica falha parcial)
for d in "$CURSO/transcriptions"/*/; do [ -f "$d/raw.md" ] || echo "INCOMPLETA: $d"; done
```

---

## Variantes

| Cenário | Comando |
|---|---|
| Curso gravado por você (vídeos fora de `videos/`, ex: `aulas-editadas/`) | `task transcribe-course-api SRCDIR=aulas-editadas -- "$CURSO"` — cria `transcriptions/` na raiz do curso, espelhando os módulos |
| Transcrever local (mlx, sem custo de API, PT forçado) | `task transcribe-course -- "$CURSO"` |
| Pasta avulsa fora da convenção de curso | `task transcribe-local-batch-api NODATE=1 -- "/caminho/pasta"` (sai no `default_output` do config.yaml) |
| Timestamps por palavra (calls/reuniões) | adicionar `WORDS=1` a qualquer task acima |
| Paralelizar (só tasks `*-api`) | adicionar `WORKERS=10` — skips resolvidos antes, `LIMIT` continua valendo |
| Re-transcrever uma aula específica | `uv run local-transcribe "$CURSO/videos/<aula>.mp4" --api --no-date --output "$CURSO/transcriptions" --force` |

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---|---|---|
| `task: Task "..." does not exist` | Faltou o `--` antes do caminho | `task transcribe-course-api -- "$CURSO"` |
| Erro do ffmpeg logo no início | Vídeo online-only no Dropbox | Marcar pasta como disponível offline e re-rodar |
| `OPENAI_API_KEY não encontrada` | `.env` ausente/incompleto | Adicionar a chave no `.env` da raiz do repo |
| Transcrição em idioma errado | whisper-1 detectou errado (raro) | Re-rodar a aula via mlx local forçando idioma: `uv run local-transcribe <aula> --language pt --no-date --output "$CURSO/transcriptions" --force` |
| Aula não é pulada apesar de transcrita | `source_path` mudou (arquivo movido/renomeado) | Esperado — o skip casa pelo caminho absoluto do vídeo |
| `.mp3` acumulando em `videos/` | Cache de extração (comportamento normal) | Deixar (evita re-extração) ou limpar depois do curso concluído |
