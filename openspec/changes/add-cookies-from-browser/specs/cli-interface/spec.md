## ADDED Requirements

### Requirement: Flag --cookies-from-browser para autenticação no YouTube
O sistema SHALL aceitar flag opcional `--cookies-from-browser <browser>` que é repassada ao yt-dlp para usar cookies do browser especificado (ex: `chrome`, `firefox`, `safari`, `brave`, `edge`).

#### Scenario: Uso com cookies do Chrome
- **WHEN** o usuário executa `yt-transcribe <url> --output <dir> --cookies-from-browser chrome`
- **THEN** o sistema baixa o áudio usando cookies do Chrome e executa o pipeline normalmente

#### Scenario: Flag omitida
- **WHEN** o usuário não passa `--cookies-from-browser`
- **THEN** o sistema baixa o vídeo sem cookies (comportamento padrão)

#### Scenario: Erro de bot-check sem cookies
- **WHEN** o download falha com erro de "Sign in to confirm you're not a bot"
- **THEN** a mensagem de erro do sistema orienta o usuário a tentar novamente com `--cookies-from-browser <browser>`
