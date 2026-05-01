## MODIFIED Requirements

### Requirement: Download de áudio de URL do YouTube
O sistema SHALL baixar apenas o stream de áudio do vídeo (sem vídeo completo) via yt-dlp e salvar como arquivo temporário. O formato depende da flag `--no-ffmpeg`: mp3 (padrão com ffmpeg) ou formato nativo do YouTube (com `--no-ffmpeg`).

#### Scenario: Download bem-sucedido com ffmpeg (padrão)
- **WHEN** uma URL válida do YouTube é fornecida sem `--no-ffmpeg`
- **THEN** o sistema baixa o áudio e converte para mp3 via ffmpeg

#### Scenario: Download bem-sucedido sem ffmpeg
- **WHEN** uma URL válida do YouTube é fornecida com `--no-ffmpeg`
- **THEN** o sistema baixa o áudio no formato nativo (webm) sem conversão

#### Scenario: Cleanup do arquivo temporário
- **WHEN** o pipeline conclui (com sucesso ou erro)
- **THEN** o arquivo de áudio temporário é deletado
