## ADDED Requirements

### Requirement: Flag --force para forçar re-download e re-transcrição
O sistema SHALL aceitar flag opcional `--force` que desabilita a detecção de transcrição existente, fazendo com que `yt-transcribe` execute o pipeline completo (download + transcrição + escrita) mesmo quando uma pasta correspondente já existir em `<output>`.

#### Scenario: Uso com --force quando transcrição existe
- **WHEN** existe pasta `*_<slug>` com `raw.md` e `meta.json` casando a URL, e o usuário executa `yt-transcribe <url> --output <dir> --force`
- **THEN** o sistema ignora a pasta existente, baixa o áudio, transcreve, e escreve os arquivos (sobrescrevendo `raw.md`, `raw_timestamps.md`, `raw_whisper.json`, `meta.json` se a pasta destino coincidir)

#### Scenario: Default sem --force
- **WHEN** o usuário executa `yt-transcribe <url> --output <dir>` sem `--force` e existe transcrição correspondente
- **THEN** o sistema pula download e transcrição, conforme o comportamento de skip definido na capability `audio-download`

#### Scenario: --force sem transcrição existente
- **WHEN** o usuário passa `--force` e não existe pasta correspondente
- **THEN** o sistema procede normalmente (sem efeito observável da flag); nenhum erro é emitido por causa da flag
