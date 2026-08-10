# Runbook 03 — Curso gravado por você (ciclo de gravação)

**Objetivo:** conforme você grava e exporta aulas do seu próprio curso, gerar transcrição + material de estudo incrementalmente, deixando `material-de-estudo/` sempre pronta pra subir na plataforma.

**Diferença pros Runbooks 01/02:** lá o curso já está completo (baixado); aqui o curso cresce aula a aula. O mesmo comando roda após cada sessão de edição — só o que é novo é processado.

---

## Estrutura esperada

```
<curso>/                        # ex: ~/0_PARA/1_PROJETOS/k8s-admin-v2
├── 00-screenflow/              # projetos de gravação/edição (ignorado pelo toolkit)
├── 01-exportadas/              # mp4 finais exportados ← fonte
│   └── m01a01-slug-da-aula.mp4
├── transcriptions/             # criada automaticamente
└── material-de-estudo/         # criada automaticamente — pasta de upload
    └── m01a01-slug-da-aula.md  # mesmo nome do vídeo
```

Convenção de nome dos exports: `mXXaYY-slug-descritivo.mp4` (o nome do arquivo vira o nome da pasta de transcrição e do `.md` final).

## Setup (uma vez por curso)

```bash
CURSO="$HOME/0_PARA/1_PROJETOS/k8s-admin-v2"   # ajuste pro curso atual
```

Nada mais — as pastas de saída são criadas na primeira execução.

## O ciclo (após cada sessão de edição/export)

```bash
# 1. Exportou a(s) aula(s) nova(s) pra 01-exportadas/ no ScreenFlow

# 2. Transcrever (só as novas — as anteriores são puladas)
task transcribe-course-api SRCDIR=01-exportadas -- "$CURSO"

# 3. Material de estudo (idem, incremental)
task study-course -- "$CURSO"

# 4. Conferir e subir
ls "$CURSO/material-de-estudo"
head -30 "$CURSO/material-de-estudo/<aula-nova>.md"
```

Custo por aula de ~10min: ~$0.06 (transcrição) + ~$0.06 (material) ≈ **$0.12**.

## Verificação (a qualquer momento)

```bash
# Os três números devem bater (exportadas == transcritas == materiais)
find "$CURSO/01-exportadas" -name "*.mp4" | wc -l
ls "$CURSO/transcriptions"/*/raw.md 2>/dev/null | wc -l
ls "$CURSO/material-de-estudo"/*.md 2>/dev/null | wc -l
```

## Regravou/re-exportou uma aula?

O skip casa pelo caminho do vídeo — sobrescrever o mp4 com o mesmo nome **não** dispara re-transcrição. Force a aula específica:

```bash
uv run local-transcribe "$CURSO/01-exportadas/<aula>.mp4" --api --no-date \
    --output "$CURSO/transcriptions" --force
rm "$CURSO/material-de-estudo/<aula>.md"    # apagar o .md força o study-course a regerar
task study-course -- "$CURSO"
```

## Notas

- Os `.mp3` extraídos ficam ao lado dos `.mp4` em `01-exportadas/` (cache — evita re-extração). Pode apagar quando o curso estiver concluído.
- Timestamps por palavra pra legendagem/corte: adicionar `WORDS=1` na etapa 2.
- Poucos arquivos por rodada → `WORKERS` raramente necessário aqui; se acumular muitas aulas, `WORKERS=5`.
- Troubleshooting geral (erros de API, ffmpeg, idioma): tabelas dos Runbooks [01](01-transcricao-curso.md) e [02](02-material-didatico.md).
