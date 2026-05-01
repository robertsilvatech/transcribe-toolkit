## 1. Downloader

- [x] 1.1 Em `yt_transcribe/downloader.py`, adicionar função `get_video_metadata(url, cookies_from_browser)` que invoca `yt_dlp.YoutubeDL(opts).extract_info(url, download=False)` e retorna o dict (mesmo shape de metadata atual: title, channel, url, duration_seconds, language)
- [x] 1.2 Adicionar função `find_existing_transcription(output_dir: Path, url: str, title: str) -> Path | None`:
  - Calcula `slug = _slugify(title)`
  - `glob(f"*_{slug}")` em `output_dir`, ordena por nome decrescente (data mais recente primeiro)
  - Para cada candidato: exige `raw.md` + `meta.json` válido com `meta["url"] == url`
  - Retorna `Path` do primeiro match ou `None`
- [x] 1.3 Reusar lógica de `player_clients` (tv/web/mweb com cookies, android_vr sem) em `get_video_metadata`

## 2. CLI

- [x] 2.1 Em `yt_transcribe/cli.py`, adicionar argumento `--force` (action="store_true", help: "Re-baixa e re-transcreve mesmo se transcrição existente for encontrada.")
- [x] 2.2 Após `output_dir.mkdir(...)` e antes da etapa de download:
  - Se `not args.force`: chamar `get_video_metadata(args.url, cookies_from_browser=args.cookies_from_browser)` (com try/except apropriado)
  - Chamar `find_existing_transcription(output_dir, args.url, metadata["title"])`
  - Se retornar Path: imprimir `✓  Já transcrito: <path>` (sem baixar), fazer `Path.touch()` na pasta para atualizar mtime, e `sys.exit(0)`
- [x] 2.3 Garantir que mensagens de erro do `extract_info(download=False)` reusem o mesmo handler atual (DownloadError + hint de cookies)

## 3. Integração com run.sh

- [x] 3.1 Verificar manualmente que `./run.sh <url>` em re-execução pula a etapa 1 corretamente: yt-transcribe imprime "Já transcrito", a pasta tem mtime atualizado, e `ls -td` no run.sh ainda identifica a pasta certa
- [x] 3.2 Verificar que com `--force` (cenário fora do run.sh) o yt-transcribe ignora pasta existente e re-baixa

## 4. Docs

- [x] 4.1 Atualizar `AGENT.md` (seção `yt_transcribe`): adicionar exemplo `uv run yt-transcribe <url> --output <dir> --force` e nota sobre skip automático
- [x] 4.2 Atualizar `AGENT.md` (seção `Pipeline end-to-end`): remover a frase "Etapa 1 (yt-transcribe) sempre roda — idempotência completa virá em change futura" e substituir por descrição do skip atual
- [x] 4.3 Atualizar `README.md` (seção `yt-transcribe`): mencionar `--force` no quick-start
- [x] 4.4 Atualizar `README.md` (seção `Pipeline end-to-end`): remover/ajustar a nota sobre etapa 1 sempre rodando

## 5. Validação manual

- [x] 5.1 Rodar `uv run yt-transcribe <url> --output ./out` em pasta limpa → produz pasta com `raw.md` e `meta.json`
- [x] 5.2 Rodar de novo o mesmo URL → imprime "Já transcrito: ..." e termina rapidamente sem download/transcrição
- [x] 5.3 Confirmar que a pasta detectada teve mtime atualizado (comparar `stat` antes/depois)
- [x] 5.4 Rodar com `--force` → re-baixa e re-transcreve (sobrescrevendo arquivos existentes)
- [x] 5.5 Criar pasta legada sem `meta.json` (apenas `raw.md`) → próxima execução procede normal (não pula)
- [x] 5.6 Rodar com URL diferente que tenha slug colidente (forçar artificialmente) → URL match impede skip incorreto
- [x] 5.7 Re-executar `./run.sh <url>` após esta change → confirmar que TODAS as 3 etapas pulam (idempotência completa)
