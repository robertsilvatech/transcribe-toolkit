## 1. Implementação no run.sh

- [x] 1.1 Declarar três variáveis de estado no topo do script (após `BROWSER`): `FORCE_YT=0`, `FORCE_TRANSLATE=0`, `FORCE_VAULT_IMPORT=0`
- [x] 1.2 Adicionar três cases no parser de args: `--force-translate)` seta `FORCE_TRANSLATE=1`; `--force-vault-import)` seta `FORCE_VAULT_IMPORT=1`; `--force)` seta as três (`FORCE_YT=1`, `FORCE_TRANSLATE=1`, `FORCE_VAULT_IMPORT=1`). Cada case dá `shift` (sem valor)
- [x] 1.3 Na montagem de `YT_ARGS`, adicionar `--force` quando `FORCE_YT=1`
- [x] 1.4 No bloco da etapa 2, alterar a condição para `if [[ -f "$DIR/raw_pt-br.md" && "$FORCE_TRANSLATE" -eq 0 ]]`
- [x] 1.5 No bloco da etapa 3, alterar a condição para `if [[ -f "$VAULT/raw/$SLUG.md" && "$FORCE_VAULT_IMPORT" -eq 0 ]]`. Quando NÃO pular, invocar `uv run vault-import "$DIR" --force` se `FORCE_VAULT_IMPORT=1` (caso contrário sem `--force`, mantendo comportamento atual)
- [x] 1.6 Atualizar a função `usage()` para listar as três novas flags com descrição curta

## 2. Documentação

- [x] 2.1 Atualizar a seção "Pipeline end-to-end (run.sh)" em `AGENT.md` com exemplos das três flags

## 3. Verificação manual

- [x] 3.1 Em pasta com pipeline já completado, rodar `./run.sh -u <url> --force-vault-import` e confirmar que etapa 3 re-executa (sobrescrevendo o destino) enquanto etapas 1 e 2 pulam
- [x] 3.2 Rodar `./run.sh -u <url> --force-translate` e confirmar que etapa 2 re-traduz (sobrescrevendo `raw_pt-br.md`) enquanto etapas 1 e 3 se comportam normalmente
- [x] 3.3 Rodar `./run.sh -u <url>` sem flags e confirmar que skip automático segue funcionando
- [x] 3.4 Rodar `./run.sh -h` e confirmar que as três flags aparecem no usage
