## ADDED Requirements

### Requirement: Criação da pasta de output com nome padronizado
O sistema SHALL criar uma subpasta dentro do diretório `--output` com formato `YYYY-MM-DD_slug-do-titulo`.

#### Scenario: Pasta criada corretamente
- **WHEN** o pipeline conclui a transcrição
- **THEN** uma pasta no formato `2026-04-10_titulo-do-video` é criada dentro do diretório de output

### Requirement: Salvar raw.txt
O sistema SHALL salvar o texto transcrito completo sem timestamps em `raw.txt`.

#### Scenario: Arquivo gerado
- **WHEN** a transcrição é concluída
- **THEN** `raw.txt` contém apenas o texto limpo, sem marcações de tempo, em UTF-8

### Requirement: Salvar raw_timestamps.txt
O sistema SHALL salvar o texto transcrito com timestamps por segmento em `raw_timestamps.txt`.

#### Scenario: Arquivo com timestamps
- **WHEN** a transcrição é concluída
- **THEN** `raw_timestamps.txt` contém cada segmento prefixado com timestamp no formato `[HH:MM:SS]`

### Requirement: Salvar raw_whisper.json
O sistema SHALL salvar a resposta completa do Whisper (verbose JSON) em `raw_whisper.json`.

#### Scenario: Source of truth persistido
- **WHEN** a transcrição é concluída
- **THEN** `raw_whisper.json` contém a resposta completa incluindo segments com start, end e text

### Requirement: Salvar meta.json
O sistema SHALL salvar metadata do vídeo em `meta.json`.

#### Scenario: Metadata completo
- **WHEN** o pipeline conclui
- **THEN** `meta.json` contém: `title`, `channel`, `url`, `duration_seconds`, `language`, `transcribed_at`, `model_used`
