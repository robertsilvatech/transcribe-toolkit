## 0. Migração .txt → .md

- [x] 0.1 Alterar `formatter.py`: `raw.txt` → `raw.md`, `raw_timestamps.txt` → `raw_timestamps.md`
- [x] 0.2 Atualizar `cli.py`: mensagens de feedback com nomes `.md`
- [x] 0.3 Atualizar `README.md`, `AGENT.md` com referências `.md`

## 1. Setup

- [x] 1.1 Adicionar dependências `anthropic` e `pyyaml` no `pyproject.toml`
- [x] 1.2 Adicionar `ANTHROPIC_API_KEY=` no `.env.example`
- [x] 1.3 Criar `config.yaml` na raiz com defaults: provider anthropic, modelo claude-sonnet-4-6, idioma pt-br, providers openai e anthropic
- [x] 1.4 Rodar `uv sync` para instalar novas dependências

## 2. Config

- [x] 2.1 Criar `yt_transcribe/config.py`: carrega `config.yaml`, aplica cascata CLI > config > fallback

## 3. Engine de Tradução

- [x] 3.1 Criar `yt_transcribe/translator.py`: função `translate_text(text, provider, model, target_lang)` que despacha para o provider correto
- [x] 3.2 Implementar `_translate_openai(text, model, target_lang)` com system prompt de tradução
- [x] 3.3 Implementar `_translate_anthropic(text, model, target_lang)` com system prompt de tradução
- [x] 3.4 Validação de API key antes de chamar e validação de tamanho do texto (limite 100k chars)

## 4. CLI

- [x] 4.1 Criar `yt_transcribe/translate_cli.py`: argparse com argumento `path`, flags `--provider`, `--model`, `--target-lang`
- [x] 4.2 Integrar com `config.py` para resolver defaults
- [x] 4.3 Ler arquivo input, chamar `translate_text()`, salvar output como `raw_<lang>.md` na mesma pasta
- [x] 4.4 Adicionar feedback de progresso e tratamento de erros
- [x] 4.5 Adicionar entry point `translate` no `pyproject.toml` e rodar `uv sync`
