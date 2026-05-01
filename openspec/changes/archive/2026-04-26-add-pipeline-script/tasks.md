## 1. Script

- [x] 1.1 Criar `run.sh` na raiz com shebang `#!/usr/bin/env bash` e `set -euo pipefail`
- [x] 1.2 Parser de flags `-u/--url` (obrigatória), `-o/--output` (opcional, default `./out`), `-a/--api` (opcional, repassa `--api` ao yt-transcribe); `-h/--help` imprime uso; argumento desconhecido erra com exit 1
- [x] 1.3 Ler variável de ambiente `BROWSER` (default `chrome`)
- [x] 1.4 Etapa 1: invocar `uv run yt-transcribe "$URL" --output "$OUT_BASE" --cookies-from-browser "$BROWSER"`, adicionando `--api` quando `USE_API=1`
- [x] 1.5 Descobrir subpasta criada via `ls -td "$OUT_BASE"/*/ | head -1` e remover trailing slash
- [x] 1.6 Etapa 2: se `$DIR/raw_pt-br.md` existe, imprimir mensagem de skip; caso contrário invocar `uv run translate "$DIR/raw.md"`
- [x] 1.7 Etapa 3: descobrir `VAULT` via `uv run python -c "from vault_import.config import resolve_vault_path; print(resolve_vault_path(None))"`
- [x] 1.8 Etapa 3: extrair `SLUG=$(basename "$DIR")`. Se `$VAULT/raw/$SLUG.md` existe, imprimir mensagem de skip; caso contrário invocar `uv run vault-import "$DIR"`
- [x] 1.9 Adicionar comentários no início do script explicando uso e variáveis suportadas
- [x] 1.10 Tornar executável: `chmod +x run.sh`

## 2. Docs

- [x] 2.1 Atualizar `AGENT.md` adicionando seção sobre `run.sh` (uso básico, variável `BROWSER`, comportamento de skip)
- [x] 2.2 Atualizar `README.md` (se existir) com exemplo de uso do `run.sh` no quick-start
- [x] 2.3 Documentar a limitação conhecida: etapa 1 sempre roda; idempotência completa virá com `add-yt-transcribe-skip`

## 3. Validação manual

- [x] 3.1 Rodar `./run.sh -u <url-de-teste>` em pasta limpa e validar que os 3 outputs aparecem (raw_pt-br.md na pasta de transcrição + arquivo no vault)
- [x] 3.2 Rodar de novo a mesma URL e confirmar que etapas 2 e 3 imprimem mensagem de skip (e nenhuma chamada de API/escrita acontece)
- [x] 3.3 Forçar falha na etapa 2 (ex: variável `ANTHROPIC_API_KEY` vazia), validar que script para com exit != 0 e que rodada subsequente (com a key correta) só roda etapas 2 e 3
- [x] 3.4 Rodar com `BROWSER=firefox ./run.sh -u <url>` e confirmar que o yt-transcribe usa cookies do Firefox
- [x] 3.5 Rodar com URL inválida e confirmar que falha imediatamente sem tentar etapas 2 e 3
- [x] 3.6 Rodar `./run.sh -o ~/transcricoes -u <url>` (ordem invertida) e confirmar que funciona igual a `./run.sh -u <url> -o ~/transcricoes`
- [x] 3.7 Rodar `./run.sh` sem args e `./run.sh --foo bar` e confirmar mensagens de erro claras com exit != 0
- [x] 3.8 Rodar `./run.sh -u <url> -a` e confirmar que yt-transcribe foi invocado com `--api` (uso da OpenAI Whisper API)
