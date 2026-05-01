---
name: translate
description: Traduz um arquivo .md para outro idioma usando o próprio Claude como engine. Recebe o path do arquivo e opcionalmente o idioma alvo.
---

Traduz o conteúdo de um arquivo .md e salva o resultado na mesma pasta.

**Input**: `/translate <path> [idioma]`
- `<path>`: caminho do arquivo a traduzir (obrigatório)
- `[idioma]`: idioma alvo (opcional, default: pt-br)

**Steps**

1. Parse o argumento: extrair o path do arquivo e o idioma alvo (default `pt-br`)
2. Verificar que o arquivo existe usando Read. Se não existir, informar o erro.
3. Ler o conteúdo completo do arquivo com Read.
4. Traduzir o conteúdo para o idioma alvo seguindo estas regras:
   - Manter o tom original (conversacional, técnico, etc.)
   - Manter jargão técnico que é comumente usado em inglês na comunidade tech (ex: "API", "framework", "deploy", "prompt", "context window", "agent")
   - Produzir texto natural e fluente — não tradução literal palavra por palavra
   - Preservar quebras de parágrafo e formatação
   - Quebrar o texto traduzido em parágrafos naturais separados por linhas em branco
   - NÃO adicionar explicações, notas ou comentários — apenas o texto traduzido
5. Salvar o texto traduzido com Write no mesmo diretório do arquivo original, com nome `{nome_original}_{idioma}.md` (ex: `raw.md` → `raw_pt-br.md`, `ppt.md` → `ppt_pt-br.md`)
6. Informar o path do arquivo gerado

**Output**: `{nome_original}_{idioma}.md` na mesma pasta do arquivo de input.

**Example**:
```
/translate /Users/user/transcricao/2026-04-11_video/raw.md
→ salva raw_pt-br.md na mesma pasta

/translate /Users/user/docs/ppt.md es
→ salva ppt_es.md na mesma pasta
```
