## 1. Download

- [x] 1.1 Adicionar parâmetro `no_ffmpeg=False` em `download_audio()` no `downloader.py`
- [x] 1.2 Quando `no_ffmpeg=True`: remover postprocessors e buscar arquivo de áudio por glob `audio.*`

## 2. CLI

- [x] 2.1 Adicionar flag `--no-ffmpeg` (store_true) no argparse em `cli.py`
- [x] 2.2 Passar `no_ffmpeg` para `download_audio()`
- [x] 2.3 Validar antes da transcrição: se `--no-ffmpeg` + `--api` + áudio > 25MB, exibir erro e sair
