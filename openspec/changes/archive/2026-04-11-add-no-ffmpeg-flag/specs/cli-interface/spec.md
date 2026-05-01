## MODIFIED Requirements

### Requirement: CLI aceita URL e diretório de output
O sistema SHALL aceitar uma URL do YouTube como argumento posicional e um diretório de destino via flag `--output`.

#### Scenario: Uso básico com mlx-whisper local
- **WHEN** o usuário executa `python cli.py <url> --output ~/transcricoes`
- **THEN** o sistema executa o pipeline completo e salva os arquivos em `~/transcricoes/YYYY-MM-DD_titulo-do-video/`

#### Scenario: Uso com OpenAI Whisper API
- **WHEN** o usuário executa `python cli.py <url> --output ~/transcricoes --api`
- **THEN** o sistema usa a OpenAI Whisper API para transcrição em vez do mlx-whisper local

#### Scenario: Output directory não existe
- **WHEN** o diretório passado em `--output` não existe
- **THEN** o sistema cria o diretório automaticamente antes de prosseguir

#### Scenario: Uso sem ffmpeg
- **WHEN** o usuário executa com `--no-ffmpeg`
- **THEN** o sistema baixa o áudio no formato nativo do YouTube sem conversão e executa o pipeline normalmente

#### Scenario: --no-ffmpeg com --api e áudio grande
- **WHEN** o usuário usa `--no-ffmpeg` com `--api` e o áudio é maior que 25MB
- **THEN** o sistema exibe erro informando que chunking requer ffmpeg e encerra
