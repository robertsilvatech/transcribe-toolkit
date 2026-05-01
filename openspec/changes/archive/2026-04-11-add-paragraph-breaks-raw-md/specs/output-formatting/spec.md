## MODIFIED Requirements

### Requirement: Salvar raw.md
O sistema SHALL salvar o texto transcrito completo sem timestamps em `raw.md`, com quebras de parágrafo baseadas em pausas do áudio (gap > 2 segundos entre segments).

#### Scenario: Arquivo com parágrafos
- **WHEN** a transcrição é concluída e segments contêm gaps maiores que 2 segundos
- **THEN** `raw.md` contém o texto com parágrafos separados por linhas em branco nos pontos de pausa

#### Scenario: Segments sem gaps significativos
- **WHEN** a transcrição é concluída e não há gaps maiores que 2 segundos
- **THEN** `raw.md` contém o texto como bloco único (comportamento natural)

#### Scenario: Segments ausentes
- **WHEN** a transcrição é concluída mas segments está vazio ou ausente
- **THEN** `raw.md` usa o campo text direto como fallback
