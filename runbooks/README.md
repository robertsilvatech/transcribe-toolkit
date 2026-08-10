# Runbooks

Procedimentos passo-a-passo para operar o toolkit. Cada runbook é autocontido: pré-requisitos, execução por etapas, verificação e troubleshooting.

| Runbook | Quando usar |
|---|---|
| [01 — Transcrição de curso](01-transcricao-curso.md) | Curso EAD baixado no Dropbox (`<curso>/videos/`) → transcrições em `<curso>/transcriptions/` |
| [02 — Material didático](02-material-didatico.md) | Transcrições prontas → `material-de-estudo/<aula>.md` (pasta única pra upload) |
| [03 — Curso gravado por você](03-curso-gravado.md) | Você está gravando o curso: ciclo incremental export → transcrição → material → upload |

## Convenções

- `$CURSO` nos comandos = caminho absoluto da **raiz** do curso (a pasta que contém `videos/`, `resources/`, `transcriptions/`). Ex:

  ```bash
  CURSO="/Users/robertsilvatech/Dropbox/00-PARA/3_RECURSOS/rst-study-videos/kubernetes-para-iniciantes"
  ```

- Todos os comandos rodam **da raiz do repo** `transcribe-toolkit` (as tasks usam `uv run` com o venv do projeto).
- Tudo é **idempotente**: re-executar qualquer etapa pula o que já foi feito. Nunca há custo duplicado por rodar de novo.
- Regra de ouro: **teste com `LIMIT=1` antes de rodar o lote inteiro.** Uma aula custa centavos; o lote inteiro custa dólares.

## Pré-requisitos gerais (uma vez por máquina)

```bash
task setup            # config.yaml + .env + uv sync + wrappers
task --list-all       # confirma que as tasks aparecem
```

`.env` na raiz do repo precisa de:

- `OPENAI_API_KEY` — transcrição via API (whisper-1)
- `ANTHROPIC_API_KEY` — geração de material didático / tradução
