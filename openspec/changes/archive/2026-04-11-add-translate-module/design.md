## Context

O módulo yt-transcribe gera `raw.md` em inglês. Para consumo com LLMs em português, precisamos de tradução. Este módulo é independente — recebe um path de arquivo texto e gera a tradução na mesma pasta. Usa LLM APIs (OpenAI e Anthropic) para tradução com contexto, mantendo qualidade superior a tradutores literais.

## Goals / Non-Goals

**Goals:**
- CLI `translate <path>` que traduz qualquer arquivo `.md` usando LLM API
- Suporte a OpenAI e Anthropic como providers
- `config.yaml` com defaults (provider, modelo, idioma) para não hardcodar
- Flags CLI para override de qualquer default
- Output `raw_pt-br.md` (ou `raw_<lang>.md`) na mesma pasta do input

**Non-Goals:**
- Traduzir `raw_timestamps.md` ou `raw_whisper.json` (futuro, se necessário)
- Suporte a outros providers (DeepL, Google) por enquanto
- Tradução em batch de múltiplos arquivos
- Chunking de textos longos (tratar como limitação conhecida por ora)

## Decisions

### 1. config.yaml como fonte de defaults

**Decisão:** Arquivo `config.yaml` na raiz do projeto com estrutura:

```yaml
translate:
  default_provider: anthropic
  target_language: pt-br
  providers:
    openai:
      model: gpt-4.1-mini
      api_key_env: OPENAI_API_KEY
    anthropic:
      model: claude-sonnet-4-6
      api_key_env: ANTHROPIC_API_KEY
```

**Rationale:** YAML é legível e editável. O config fica compartilhável entre módulos futuros (insights, Q&A). API keys vêm do `.env` via nome da variável — nunca ficam no config.

**Alternativas consideradas:**
- JSON: menos legível para humanos
- TOML no pyproject.toml: mistura config de app com config de build

### 2. Prioridade de configuração: CLI > config > fallback

**Decisão:** Cascata de prioridade:
1. Flags CLI (`--provider`, `--model`, `--target-lang`)
2. `config.yaml`
3. Fallback hardcoded (`anthropic`, `claude-sonnet-4-6`, `pt-br`)

**Rationale:** Permite uso zero-config (fallbacks funcionam), configuração persistente (config.yaml), e override pontual (flags CLI).

### 3. Dois providers iniciais: OpenAI e Anthropic

**Decisão:** Implementar como funções separadas (`_translate_openai`, `_translate_anthropic`) no `translator.py`, selecionadas por string do provider.

**Rationale:** Simples, sem abstrações prematuras. Quando/se vier DeepL ou outro, adiciona mais uma função. Não precisa de interface/protocol por enquanto — são só 2 providers.

### 4. System prompt específico para tradução

**Decisão:** Usar system prompt que instrui o LLM a traduzir mantendo tom, jargão técnico e naturalidade no idioma alvo. Não é tradução literal — é adaptação.

### 5. Nome do arquivo de output baseado no idioma alvo

**Decisão:** Output é `raw_<lang>.md` (ex: `raw_pt-br.md`), salvo na mesma pasta do input.

**Rationale:** Permite múltiplas traduções do mesmo texto (pt-br, es, fr) sem conflito.

## Risks / Trade-offs

- **Texto longo excede contexto do modelo** → Mitigation: para v1, avisar e sair se o texto exceder um limite seguro (~100k chars). Chunking com overlap fica como melhoria futura.
- **Custo inesperado** → Mitigation: exibir estimativa de tokens antes de chamar a API e pedir confirmação? Ou apenas informar após. Para v1, apenas informar.
- **config.yaml não existe** → Mitigation: funcionar com fallbacks hardcoded se config não existir.
