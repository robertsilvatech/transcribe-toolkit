## Why

As transcrições geradas pelo yt-transcribe vêm no idioma original do vídeo (geralmente inglês). Para extrair insights, estudar e gerar conteúdo em português, é necessário traduzir o texto. Um módulo de tradução independente permite transformar `raw.md` em `raw_pt-br.md` usando LLM APIs, com suporte a múltiplos providers e configuração flexível.

Além disso, os arquivos de output do yt-transcribe mudam de `.txt` para `.md` — compatível com Obsidian, LLM wiki e qualquer ferramenta que consuma markdown.

## What Changes

- Novo comando CLI: `translate <path> [--provider] [--model] [--target-lang]`
- Arquivo de configuração `config.yaml` na raiz do projeto com defaults para providers, modelos e idioma alvo
- Suporte a dois providers: OpenAI e Anthropic
- Cada provider com modelo default configurável (ex: `gpt-4.1-mini`, `claude-sonnet-4-6`)
- Flags CLI para override de provider, modelo e idioma
- Output: `raw_pt-br.md` (ou `raw_<lang>.md`) salvo na mesma pasta do arquivo de input
- Renomear outputs existentes do yt-transcribe: `raw.txt` → `raw.md`, `raw_timestamps.txt` → `raw_timestamps.md`
- Dependências: `openai` (já existe), `anthropic` (nova)

## Capabilities

### New Capabilities

- `translate-cli`: Comando CLI para tradução com flags `--provider`, `--model`, `--target-lang`
- `translate-engine`: Engine de tradução multi-provider (OpenAI e Anthropic) com chamada à API
- `translate-config`: Arquivo `config.yaml` com defaults de provider, modelo e idioma alvo

### Modified Capabilities

- `output-formatting`: Extensão dos arquivos raw muda de `.txt` para `.md`

## Impact

- **Nova dependência**: `anthropic` SDK no `pyproject.toml`
- **Novos arquivos**: `yt_transcribe/translator.py`, `yt_transcribe/config.py`, `yt_transcribe/translate_cli.py`
- **config.yaml**: novo arquivo de configuração na raiz
- **pyproject.toml**: novo entry point `translate` + dependência `anthropic` + `pyyaml`
- **`.env.example`**: adicionar `ANTHROPIC_API_KEY=`
