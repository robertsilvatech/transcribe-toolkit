# Runbook 02 — Material didático

**Objetivo:** gerar, para cada aula transcrita, um material de estudo organizado em tópicos/subtópicos (com 💡 dicas, ⚠️ erros comuns, 🗣️ relatos do professor) em `$CURSO/material-de-estudo/<nome-da-aula>.md` — um arquivo por aula, com o mesmo nome do vídeo, pronto pra subir na plataforma.

**Pré-requisito:** Runbook 01 concluído (`$CURSO/transcriptions/*/raw.md` existem).

**Duração típica:** ~30-60s por aula. **Custo:** ~$0.05-0.10/aula (claude-sonnet-5).

---

## Etapa 0 — Pré-checagens

```bash
CURSO="/caminho/da/raiz/do/curso"

# Quantas aulas têm transcrição pronta?
ls "$CURSO/transcriptions"/*/raw.md | wc -l

# Engine configurada (config.yaml, seção study_material)
grep -A2 "^study_material:" config.yaml
```

## Etapa 1 — Testar com 1 aula

```bash
task study-course LIMIT=1 -- "$CURSO"
```

O que a task faz: `study-material --limit 1 --dir "$CURSO/transcriptions" --output-dir "$CURSO/material-de-estudo"` — varre por `raw.md` e grava `<nome-da-aula>.md` na pasta única.

**Verificar o resultado:**

```bash
ls "$CURSO/material-de-estudo"          # 1 arquivo com o nome do vídeo
head -40 "$CURSO/material-de-estudo"/*.md
```

Critérios de aceite: título coerente com a aula, seções numeradas, comandos citados em blocos de código, sem texto de comentário fora do documento (tipo "Aqui está o material...").

**Não gostou do formato?** Edite o prompt em [study_material/prompt.md](../study_material/prompt.md) (não precisa mexer em código), apague o `.md` gerado e re-rode a task. Repita até aprovar, só então rode o lote.

## Etapa 2 — Rodar o lote inteiro

```bash
task study-course -- "$CURSO"
```

- A aula da Etapa 1 será pulada (o `.md` dela já existe em `material-de-estudo/`).
- Interrompível e re-executável sem custo duplicado.
- Saída esperada: `Resumo: N gerados, M pulados, 0 com erro.`

## Etapa 3 — Verificação final

```bash
# Nº de materiais == nº de transcrições?
ls "$CURSO/transcriptions"/*/raw.md | wc -l
ls "$CURSO/material-de-estudo"/*.md | wc -l

# Amostragem de qualidade: abrir 2-3 no Obsidian/editor e ler o Objetivo + Conclusão
```

Pronto: a pasta `material-de-estudo/` inteira pode ser enviada pra plataforma.

---

## Variantes

| Cenário | Comando |
|---|---|
| Uma aula avulsa (sem pasta única — study.md ao lado do raw.md) | `uv run study-material /caminho/raw.md` |
| Gerar a partir da tradução (curso em EN já traduzido) | `uv run study-material /caminho/raw_pt-br.md` |
| Provider mais barato (gpt-4.1-mini) | `task study-course` não expõe; usar `uv run study-material --dir "$CURSO/transcriptions" --output-dir "$CURSO/material-de-estudo" --provider openai` |
| Re-gerar tudo (após mudar o prompt) | `uv run study-material --dir "$CURSO/transcriptions" --output-dir "$CURSO/material-de-estudo" --force` |

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---|---|---|
| `ANTHROPIC_API_KEY não encontrada` | `.env` incompleto | Adicionar a chave no `.env` da raiz do repo |
| `Material truncado: API atingiu max_tokens` | Aula muito longa (>~3h de fala) | Gerar por partes: dividir o raw.md e rodar `uv run study-material` em cada parte |
| `Texto tem N caracteres (limite: 300.000)` | Transcrição gigante | Mesmo tratamento acima |
| study.md genérico / raso | Transcrição ruim na origem | Verificar o raw.md; se a transcrição estiver ruim, re-transcrever (Runbook 01, variante `--force`) antes de re-gerar |
| Erro 400 mencionando `temperature` | Código antigo com `temperature=0` em modelo Sonnet 5+ | Atualizar o repo (`git pull`) — corrigido na migração pro Sonnet 5 |
