## MODIFIED Requirements

### Requirement: CLI aceita path de arquivo texto
O sistema SHALL aceitar um caminho de arquivo `.md` como argumento posicional e traduzir seu conteúdo. O arquivo de saída usa o nome do input como base.

#### Scenario: Tradução de raw.md
- **WHEN** o usuário executa `translate raw.md`
- **THEN** o sistema salva como `raw_pt-br.md` na mesma pasta

#### Scenario: Tradução de arquivo com outro nome
- **WHEN** o usuário executa `translate ppt.md`
- **THEN** o sistema salva como `ppt_pt-br.md` na mesma pasta

#### Scenario: Override de idioma com arquivo nomeado
- **WHEN** o usuário executa `translate aula.md --target-lang es`
- **THEN** o sistema salva como `aula_es.md` na mesma pasta
