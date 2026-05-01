## MODIFIED Requirements

### Requirement: Skill traduz arquivo .md para idioma alvo
A skill SHALL ler o arquivo no path fornecido, traduzir o conteúdo completo, e salvar como `{nome_original}_{lang}.md` na mesma pasta.

#### Scenario: Tradução de raw.md
- **WHEN** o usuário executa `/translate /path/to/raw.md`
- **THEN** a skill salva como `raw_pt-br.md`

#### Scenario: Tradução de arquivo com outro nome
- **WHEN** o usuário executa `/translate /path/to/ppt.md`
- **THEN** a skill salva como `ppt_pt-br.md`
