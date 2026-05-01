## MODIFIED Requirements

### Requirement: Salvar raw.md
O sistema SHALL salvar o texto transcrito completo sem timestamps em `raw.md`.

#### Scenario: Arquivo gerado
- **WHEN** a transcrição é concluída
- **THEN** `raw.md` contém apenas o texto limpo, sem marcações de tempo, em UTF-8

### Requirement: Salvar raw_timestamps.md
O sistema SHALL salvar o texto transcrito com timestamps por segmento em `raw_timestamps.md`.

#### Scenario: Arquivo com timestamps
- **WHEN** a transcrição é concluída
- **THEN** `raw_timestamps.md` contém cada segmento prefixado com timestamp no formato `[HH:MM:SS]`
