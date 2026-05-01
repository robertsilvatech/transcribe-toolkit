## 1. CLI

- [x] 1.1 Adicionar argumento `--cookies-from-browser` em `yt_transcribe/cli.py` (type=str, default=None, help explicando uso)
- [x] 1.2 Repassar o valor para a função de download

## 2. Downloader

- [x] 2.1 Em `yt_transcribe/downloader.py`, aceitar novo parâmetro `cookies_from_browser: str | None`
- [x] 2.2 Quando não-None, adicionar `"cookiesfrombrowser": (cookies_from_browser,)` ao dict de opções do yt-dlp
- [x] 2.3 No handler de exceção do download, detectar substring "Sign in to confirm" e adicionar hint sugerindo `--cookies-from-browser chrome` (ou similar) na mensagem de erro

## 3. Docs

- [x] 3.1 Atualizar `AGENT.md` com exemplo: `uv run yt-transcribe <url> --output <dir> --cookies-from-browser chrome`
- [x] 3.2 Adicionar nota sobre quando usar (vídeos não listados / erro de bot-check)

## 4. Validação manual

- [ ] 4.1 Testar com o vídeo que falhou (`YTUywmN2N4s`) usando `--cookies-from-browser chrome`
- [ ] 4.2 Confirmar que execução sem a flag continua funcionando normalmente em vídeo público
