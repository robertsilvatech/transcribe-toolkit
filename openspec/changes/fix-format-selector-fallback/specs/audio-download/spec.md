## MODIFIED Requirements

### Requirement: Download de áudio de URL do YouTube
O sistema SHALL baixar apenas o stream de áudio do vídeo (sem vídeo completo) via yt-dlp, usando uma cadeia de fallback de formatos que prioriza streams audio-only conhecidos (m4a itag 140, webm opus itag 251) antes de recorrer ao seletor genérico. Isso evita falhas quando o YouTube exige resolução de "n challenge" para o seletor padrão. O formato final em disco depende da flag `--no-ffmpeg`: mp3 (com ffmpeg) ou formato nativo (com `--no-ffmpeg`).

#### Scenario: Download bem-sucedido com ffmpeg (padrão)
- **WHEN** uma URL válida do YouTube é fornecida sem `--no-ffmpeg`
- **THEN** o sistema baixa o áudio usando a cadeia de fallback e converte para mp3 via ffmpeg

#### Scenario: Download bem-sucedido sem ffmpeg
- **WHEN** uma URL válida do YouTube é fornecida com `--no-ffmpeg`
- **THEN** o sistema baixa o áudio no formato nativo (m4a/webm) sem conversão

#### Scenario: Vídeo exige n-challenge para bestaudio genérico
- **WHEN** o YouTube não entrega o seletor genérico sem resolver JS challenge
- **THEN** o sistema ainda obtém sucesso pelo fallback explícito a formatos audio-only conhecidos (ex: itag 140)

#### Scenario: Cleanup do arquivo temporário
- **WHEN** o pipeline conclui (com sucesso ou erro)
- **THEN** o arquivo de áudio temporário é deletado
