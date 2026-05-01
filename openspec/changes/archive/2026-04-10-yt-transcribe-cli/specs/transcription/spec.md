## ADDED Requirements

### Requirement: Transcrição local via mlx-whisper
O sistema SHALL transcrever o áudio usando mlx-whisper localmente quando `--api` não for especificado.

#### Scenario: Transcrição local bem-sucedida
- **WHEN** mlx-whisper está instalado e `--api` não foi passado
- **THEN** o sistema transcreve o áudio localmente e retorna resposta com segments (start, end, text)

#### Scenario: mlx-whisper não disponível
- **WHEN** mlx-whisper não está instalado
- **THEN** o sistema exibe mensagem sugerindo instalação ou uso de `--api` e encerra

### Requirement: Transcrição via OpenAI Whisper API
O sistema SHALL usar a OpenAI Whisper API quando a flag `--api` for passada.

#### Scenario: API key configurada
- **WHEN** `--api` é passado e `OPENAI_API_KEY` está definida no ambiente
- **THEN** o sistema transcreve via API e retorna resposta verbose_json com segments

#### Scenario: API key ausente
- **WHEN** `--api` é passado mas `OPENAI_API_KEY` não está definida
- **THEN** o sistema exibe mensagem de erro indicando que a variável de ambiente é necessária

### Requirement: Chunking automático para OpenAI API
O sistema SHALL dividir o áudio em chunks menores que 25MB quando usar `--api`.

#### Scenario: Áudio dentro do limite
- **WHEN** o áudio é menor que 25MB e `--api` é usado
- **THEN** o sistema envia o arquivo inteiro sem chunking

#### Scenario: Áudio acima do limite
- **WHEN** o áudio é maior que 25MB e `--api` é usado
- **THEN** o sistema divide o áudio em chunks, transcreve cada um e concatena os resultados mantendo timestamps corretos
