## MODIFIED Requirements

### Requirement: Salvar raw.md
O sistema SHALL salvar o texto transcrito completo sem timestamps em `raw.md`, fiel ao output do Whisper sem manipulação de parágrafos.

#### Scenario: Arquivo gerado
- **WHEN** a transcrição é concluída
- **THEN** `raw.md` contém o texto completo do campo `text` do Whisper, sem marcações de tempo, em UTF-8
