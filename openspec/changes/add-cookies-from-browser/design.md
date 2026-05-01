## Context

O `yt_transcribe/downloader.py` usa yt-dlp via Python API (`YoutubeDL(opts)`). A CLI em `yt_transcribe/cli.py` monta o dicionário de opções e chama o downloader. O yt-dlp já suporta nativamente `cookiesfrombrowser` — o trabalho é apenas expor e repassar.

## Goals / Non-Goals

**Goals:**
- Expor `--cookies-from-browser <browser>` na CLI.
- Repassar valor como tupla `(browser,)` para yt-dlp via chave `cookiesfrombrowser`.
- Melhorar mensagem de erro quando o download falha por bot-check, sugerindo a flag.

**Non-Goals:**
- Suporte a arquivo cookies.txt (`--cookies`). Pode ser adicionado depois se necessário.
- Gerenciamento/persistência de cookies fora do browser.
- Detecção automática de browser instalado.

## Decisions

**Decisão 1: usar nome idêntico ao yt-dlp (`--cookies-from-browser`).**
Rationale: usuários que já conhecem yt-dlp têm familiaridade imediata. Alternativa considerada (`--browser`) foi rejeitada por ser ambígua.

**Decisão 2: aceitar apenas nome do browser como string, sem parsing de perfil/container.**
Rationale: cobre o caso >95%. O yt-dlp aceita formas avançadas (`chrome:Profile 1`), mas adicionar validação/parsing aumenta superfície sem ganho claro. Passar a string crua já funciona — yt-dlp faz o parse.

**Decisão 3: detectar erro de bot-check no except e sugerir a flag.**
Rationale: sem isso o usuário fica sem saber que a solução existe. Basta checar substring "Sign in to confirm" na mensagem.

## Risks / Trade-offs

- **Risco:** usuário passa browser não instalado → yt-dlp lança erro claro. Mitigação: repassar erro como está.
- **Trade-off:** não validamos o nome do browser — delegamos ao yt-dlp. Aceitável: evita acoplar nossa CLI à lista suportada pelo yt-dlp (que muda).
