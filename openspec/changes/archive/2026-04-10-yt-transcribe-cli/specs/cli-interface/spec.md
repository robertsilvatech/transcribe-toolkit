## ADDED Requirements

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

### Requirement: Feedback de progresso ao usuário
O sistema SHALL exibir feedback de progresso em cada etapa do pipeline.

#### Scenario: Progresso durante execução
- **WHEN** o pipeline está em execução
- **THEN** o sistema exibe mensagens indicando: download concluído, transcrição em andamento, arquivos salvos

#### Scenario: Erro na URL
- **WHEN** a URL fornecida é inválida ou o vídeo está indisponível
- **THEN** o sistema exibe mensagem de erro clara e encerra sem criar diretório de output

### Requirement: Flag --model para escolha do modelo Whisper
O sistema SHALL aceitar flag opcional `--model` para selecionar o modelo do mlx-whisper.

#### Scenario: Modelo padrão
- **WHEN** `--model` não é especificado
- **THEN** o sistema usa o modelo `medium` por padrão

#### Scenario: Modelo customizado
- **WHEN** o usuário passa `--model large-v3`
- **THEN** o sistema usa o modelo especificado para transcrição
