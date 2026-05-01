## 1. Fix

- [x] 1.1 Em `yt_transcribe/downloader.py`, alterar `"format": "bestaudio/best"` para `"bestaudio[ext=m4a]/140/251/bestaudio/best"`

## 2. Validação manual

- [ ] 2.1 Rodar `uv run yt-transcribe https://www.youtube.com/watch?v=YTUywmN2N4s --output <dir> --cookies-from-browser chrome` e confirmar sucesso
- [ ] 2.2 Rodar contra um vídeo público qualquer sem cookies e confirmar que nada quebrou
