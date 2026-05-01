## ADDED Requirements

### Requirement: Skill traduz arquivo .md para idioma alvo
A skill SHALL ler o arquivo no path fornecido, traduzir o conteúdo completo, e salvar como `raw_<lang>.md` na mesma pasta.

#### Scenario: Tradução para pt-br (default)
- **WHEN** o usuário executa `/translate /path/to/raw.md`
- **THEN** a skill lê raw.md, traduz para pt-br, e salva como `raw_pt-br.md` na mesma pasta

#### Scenario: Tradução para outro idioma
- **WHEN** o usuário executa `/translate /path/to/raw.md es`
- **THEN** a skill traduz para espanhol e salva como `raw_es.md`

### Requirement: Qualidade da tradução
A skill SHALL traduzir mantendo tom conversacional, jargão técnico em inglês quando comum na área, e naturalidade no idioma alvo.

#### Scenario: Texto com termos técnicos
- **WHEN** o texto contém termos como "context window", "prompt", "API", "deploy"
- **THEN** a skill mantém os termos técnicos em inglês e traduz o restante naturalmente

### Requirement: Feedback ao usuário
A skill SHALL informar o que está fazendo e confirmar quando concluir.

#### Scenario: Execução com sucesso
- **WHEN** a tradução é concluída
- **THEN** a skill informa o path do arquivo gerado
