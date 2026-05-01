## ADDED Requirements

### Requirement: Autenticação via cookies do browser
O sistema SHALL aceitar opcionalmente uma fonte de cookies de browser e repassar para o yt-dlp, permitindo baixar vídeos que exigem login (não listados, com restrição de idade, ou bloqueados por anti-bot).

#### Scenario: Download de vídeo protegido por bot-check usando cookies
- **WHEN** o usuário fornece a opção de cookies de browser (ex: `chrome`) e a URL é de um vídeo que exige autenticação
- **THEN** o sistema passa `cookiesfrombrowser=("chrome",)` ao yt-dlp e o download é concluído com sucesso

#### Scenario: Download sem cookies (padrão)
- **WHEN** o usuário não fornece fonte de cookies
- **THEN** o sistema executa o yt-dlp sem opções de cookies, mantendo o comportamento atual
