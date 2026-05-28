## ADDED Requirements

### Requirement: `meta.json` inclui campo `source`
O sistema SHALL incluir um campo `source` em todo `meta.json` produzido, com valor `"youtube"` (para transcrições produzidas por `yt-transcribe`) ou `"local"` (para transcrições produzidas por `local-transcribe`). Esse campo SHALL ser estável e permitir que readers downstream diferenciem a origem da transcrição.

#### Scenario: meta.json de transcrição YouTube
- **WHEN** o `yt-transcribe` completa uma transcrição e escreve `meta.json`
- **THEN** o arquivo contém `"source": "youtube"`

#### Scenario: meta.json de transcrição local
- **WHEN** o `local-transcribe` completa uma transcrição e escreve `meta.json`
- **THEN** o arquivo contém `"source": "local"`

### Requirement: `meta.json` em transcrições locais inclui `source_path` no lugar de `url`/`channel`
Para `meta.json` com `source: "local"`, o sistema SHALL incluir o campo `source_path` contendo o caminho absoluto do arquivo de origem (`.mp4`/`.mov`/`.mkv`/`.m4a`/`.mp3`/`.wav`). O sistema SHALL OMITIR os campos `url` e `channel` (específicos do fluxo YouTube) em transcrições locais.

#### Scenario: source_path absoluto
- **WHEN** o `local-transcribe` processa `./aula01.mp4` (path relativo)
- **THEN** `meta.json` contém `"source_path"` com o caminho absoluto resolvido (ex: `/Users/robert/Cursos/aula01.mp4`)

#### Scenario: Ausência de url e channel em fonte local
- **WHEN** se inspeciona o `meta.json` de uma transcrição local
- **THEN** as chaves `url` e `channel` NÃO estão presentes no JSON

### Requirement: meta.json YouTube preserva shape existente
O sistema SHALL preservar todos os campos atualmente escritos no `meta.json` do `yt-transcribe` (`title`, `channel`, `url`, `duration_seconds`, `language`, `transcribed_at`, `model_used`), adicionando apenas o novo campo `source: "youtube"`. Nenhum campo existente SHALL ser removido nem renomeado.

#### Scenario: Compatibilidade do shape
- **WHEN** o `yt-transcribe` escreve `meta.json` após esta mudança
- **THEN** todas as chaves anteriores estão presentes com a mesma semântica, e a única adição é `source: "youtube"`
