## 1. Implementação

- [x] 1.1 Em `translate/translator.py`, alterar `max_tokens=16384` para `max_tokens=64000` em `_translate_anthropic`
- [x] 1.2 Após receber `response`, antes de extrair `response.content[0].text`, verificar `response.stop_reason`. Se for `"max_tokens"`, lançar `RuntimeError` com mensagem incluindo: tamanho do input em caracteres, valor de `max_tokens` configurado, e sugestão de que o vídeo provavelmente excede ~3h e precisa ser quebrado
- [x] 1.3 Manter a checagem existente de resposta vazia (após a checagem de `stop_reason`)
- [x] 1.4 Trocar `client.messages.create(...)` por `with client.messages.stream(...) as stream: response = stream.get_final_message()`. Motivo: SDK Anthropic exige streaming para requests que podem exceder 10min, e `max_tokens=64000` dispara essa restrição

## 2. Verificação manual

- [x] 2.1 Re-rodar o pipeline no vídeo que truncou anteriormente (`./run.sh --api -u https://youtu.be/gLJdrXPn0ns`) e confirmar que o `raw_pt-br.md` é gerado completo (último parágrafo corresponde ao final do `raw.md`)
- [x] 2.2 Conferir que rodar `translate` em um arquivo curto (ex.: qualquer transcrição existente < 30 min) continua funcionando sem regressão
