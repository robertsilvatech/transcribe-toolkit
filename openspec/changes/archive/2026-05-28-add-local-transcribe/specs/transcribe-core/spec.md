## ADDED Requirements

### Requirement: Módulo `transcribe_core` agrupa lógica compartilhada entre ingestores
O sistema SHALL fornecer um pacote Python `transcribe_core/` na raiz do projeto contendo a lógica de transcrição, formatação de outputs e slugify que é compartilhada entre múltiplos ingestores (`yt_transcribe`, `local_transcribe`, e futuros). Cada ingestor SHALL importar dele via `from transcribe_core import ...`. O `transcribe_core/` NÃO SHALL importar de nenhum ingestor.

#### Scenario: yt_transcribe importa de transcribe_core
- **WHEN** o código de `yt_transcribe/cli.py` é examinado
- **THEN** as funções `transcribe()`, `save_outputs()` e `slugify()` são importadas de `transcribe_core` (não definidas localmente em `yt_transcribe/`)

#### Scenario: local_transcribe importa de transcribe_core
- **WHEN** o código de `local_transcribe/cli.py` é examinado
- **THEN** as funções `transcribe()`, `save_outputs()` e `slugify()` são importadas de `transcribe_core` (mesmo módulo usado por `yt_transcribe`)

#### Scenario: transcribe_core não importa de ingestores
- **WHEN** o código de `transcribe_core/` é examinado
- **THEN** não há nenhum `from yt_transcribe ...` nem `from local_transcribe ...`

### Requirement: `transcribe_core.transcribe()` agnóstica de fonte
O sistema SHALL expor uma função `transcribe(audio_path: Path, use_api: bool = False, model: str = "medium") -> dict` que aceita o caminho de um arquivo de áudio (mp3/m4a/wav) e retorna um dict com chaves `text`, `segments` (lista com `start`/`end`/`text`) e `language`. A função SHALL suportar mlx-whisper local (default) e OpenAI Whisper API (com `use_api=True`), com chunking automático para arquivos `> 24MB` no caminho API.

#### Scenario: Transcrição local
- **WHEN** a função é chamada com `use_api=False` e mlx-whisper instalado
- **THEN** retorna dict com `text`, `segments`, `language` produzidos pelo mlx-whisper

#### Scenario: Transcrição via API
- **WHEN** a função é chamada com `use_api=True` e `OPENAI_API_KEY` definida no ambiente
- **THEN** retorna dict com mesmo shape, produzido pela OpenAI API

#### Scenario: Chunking transparente em arquivos grandes
- **WHEN** a função é chamada com `use_api=True` em um arquivo `> 24MB`
- **THEN** o sistema divide o áudio em chunks, transcreve cada um, e retorna um dict consolidado com `segments` ajustados pelo offset acumulado de cada chunk

#### Scenario: Erro quando mlx-whisper ausente e `use_api=False`
- **WHEN** a função é chamada com `use_api=False` mas mlx-whisper não está instalado
- **THEN** levanta `ImportError` com mensagem indicando a opção `pip install mlx-whisper` ou usar `--api`

#### Scenario: Erro quando `OPENAI_API_KEY` ausente e `use_api=True`
- **WHEN** a função é chamada com `use_api=True` mas a variável de ambiente não está definida
- **THEN** levanta `EnvironmentError` com mensagem clara

### Requirement: `transcribe_core.save_outputs()` agnóstica de fonte
O sistema SHALL expor uma função `save_outputs(output_dir: Path, folder_name: str, result: dict, metadata: dict, model_used: str) -> Path` que cria a subpasta `<output_dir>/<folder_name>/` e escreve os arquivos `raw.md`, `raw_timestamps.md`, `raw_whisper.json` e `meta.json`. O `meta.json` SHALL conter exatamente os campos presentes em `metadata` (mais `transcribed_at` e `model_used` adicionados pela função). A função NÃO SHALL forçar a presença de `url` ou `channel` (campos específicos do YouTube).

#### Scenario: Outputs para fonte YouTube
- **WHEN** `save_outputs` é chamada com `metadata = {"title": "...", "source": "youtube", "url": "...", "channel": "...", "duration_seconds": N, "language": "..."}`
- **THEN** `meta.json` contém todos os campos do `metadata` mais `transcribed_at` (ISO 8601 UTC) e `model_used`

#### Scenario: Outputs para fonte local
- **WHEN** `save_outputs` é chamada com `metadata = {"title": "...", "source": "local", "source_path": "/abs/path", "duration_seconds": N, "language": "..."}`
- **THEN** `meta.json` contém esses campos mais `transcribed_at` e `model_used`, e NÃO contém `url` ou `channel`

#### Scenario: Quatro arquivos sempre gerados
- **WHEN** `save_outputs` completa com sucesso
- **THEN** existem `raw.md`, `raw_timestamps.md`, `raw_whisper.json` e `meta.json` na subpasta criada

### Requirement: `transcribe_core.slugify()` reutilizável
O sistema SHALL expor uma função `slugify(text: str, max_len: int = 60) -> str` que normaliza texto (remove acentos, lowercase, substitui não-alfanuméricos por hífen, trunca em `max_len` caracteres). Essa função SHALL ser usada por todos os ingestores para derivar nomes de pasta a partir de títulos.

#### Scenario: Slug com acentos
- **WHEN** `slugify("Introdução à IA")` é chamado
- **THEN** retorna `"introducao-a-ia"`

#### Scenario: Slug com caracteres especiais
- **WHEN** `slugify("Aula #01 — Conceitos!")` é chamado
- **THEN** retorna `"aula-01-conceitos"` (sem hífens duplicados, sem hífen inicial/final)

#### Scenario: Truncamento em max_len
- **WHEN** `slugify("a" * 100, max_len=60)` é chamado
- **THEN** retorna uma string de até 60 caracteres
