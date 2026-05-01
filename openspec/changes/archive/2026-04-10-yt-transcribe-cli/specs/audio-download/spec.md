## ADDED Requirements

### Requirement: Download de áudio de URL do YouTube
O sistema SHALL baixar apenas o stream de áudio do vídeo (sem vídeo completo) via yt-dlp e salvar como arquivo temporário `.mp3`.

#### Scenario: Download bem-sucedido
- **WHEN** uma URL válida do YouTube é fornecida
- **THEN** o sistema baixa o áudio e salva como arquivo temporário em formato MP3

#### Scenario: Cleanup do arquivo temporário
- **WHEN** o pipeline conclui (com sucesso ou erro)
- **THEN** o arquivo de áudio temporário é deletado

### Requirement: Extração de metadata do vídeo
O sistema SHALL extrair metadata do vídeo durante o download via yt-dlp.

#### Scenario: Metadata disponível
- **WHEN** o download é concluído
- **THEN** o sistema extrai: título, nome do canal, duração em segundos, URL original e idioma (se disponível)

### Requirement: Geração de slug para nome da pasta
O sistema SHALL gerar um slug a partir do título do vídeo para nomear a pasta de output.

#### Scenario: Título com caracteres especiais
- **WHEN** o título do vídeo contém acentos, espaços ou caracteres especiais
- **THEN** o slug é gerado em lowercase, sem acentos, espaços substituídos por hífens, limitado a 60 caracteres
