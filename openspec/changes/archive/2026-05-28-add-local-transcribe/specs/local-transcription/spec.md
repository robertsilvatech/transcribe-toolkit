## ADDED Requirements

### Requirement: CLI `local-transcribe` aceita arquivos posicionais e/ou flag `--dir`
O sistema SHALL fornecer um CLI `local-transcribe` que aceita um ou mais arquivos posicionais E/OU uma flag `--dir <path>`. Quando `--dir` é fornecido, o sistema SHALL varrer o diretório recursivamente. O sistema SHALL aceitar as extensões `.mp4`, `.mov`, `.mkv`, `.m4a`, `.mp3` e `.wav` (case-insensitive). Arquivos com outras extensões SHALL ser ignorados (em modo `--dir`) ou produzir erro (em modo posicional).

#### Scenario: Arquivo único posicional
- **WHEN** o usuário executa `local-transcribe aula01.mp4`
- **THEN** o sistema processa apenas `aula01.mp4` e produz um output em `<default_output>/YYYY-MM-DD_aula01/`

#### Scenario: Múltiplos arquivos posicionais
- **WHEN** o usuário executa `local-transcribe aula01.mp4 aula02.mp4`
- **THEN** o sistema processa ambos em sequência (na ordem fornecida); cada um gera sua subpasta `YYYY-MM-DD_<slug>/`

#### Scenario: Glob expandido pelo shell
- **WHEN** o usuário executa `local-transcribe ./curso/*.mp4` (shell expande para vários arquivos)
- **THEN** o sistema processa cada arquivo da lista expandida, equivalente ao caso de múltiplos posicionais

#### Scenario: Modo `--dir` recursivo
- **WHEN** o usuário executa `local-transcribe --dir ~/Cursos/devin-mastering`
- **THEN** o sistema varre `~/Cursos/devin-mastering/` recursivamente, encontra todos os arquivos com extensões suportadas em qualquer profundidade, e processa cada um

#### Scenario: Modo `--dir` ignora extensões não suportadas
- **WHEN** o usuário executa `--dir <path>` e o diretório contém `aula01.mp4`, `notas.txt` e `slides.pdf`
- **THEN** apenas `aula01.mp4` é processado; `.txt` e `.pdf` são silenciosamente ignorados

#### Scenario: Posicional com extensão não suportada
- **WHEN** o usuário executa `local-transcribe notas.txt`
- **THEN** o sistema imprime erro listando as extensões aceitas e termina com exit code não-zero

#### Scenario: Arquivo posicional inexistente
- **WHEN** o usuário executa `local-transcribe nao-existe.mp4`
- **THEN** o sistema imprime erro indicando que o arquivo não foi encontrado e termina com exit code não-zero

#### Scenario: `--dir` aponta para path inexistente
- **WHEN** o usuário executa `local-transcribe --dir /nao/existe`
- **THEN** o sistema imprime erro indicando que o diretório não existe e termina com exit code não-zero

#### Scenario: Nenhum input fornecido
- **WHEN** o usuário executa `local-transcribe` sem argumentos posicionais nem `--dir`
- **THEN** o sistema imprime uso e termina com exit code não-zero

### Requirement: Extração de áudio cacheada ao lado do source
O sistema SHALL extrair o áudio dos arquivos de vídeo (`.mp4`, `.mov`, `.mkv`) para `.mp3` via ffmpeg, salvando o arquivo `.mp3` no MESMO diretório do arquivo de origem (sibling). Se já existir um `.mp3` com o nome esperado ao lado do source, o sistema SHALL reusá-lo sem re-extrair. A flag `--force` SHALL re-transcrever mas NÃO SHALL re-extrair (o `.mp3` é considerado determinístico do source). Arquivos de áudio (`.m4a`, `.mp3`, `.wav`) SHALL ser usados diretamente sem extração.

#### Scenario: Primeira extração
- **WHEN** o usuário executa `local-transcribe aula01.mp4` e `aula01.mp3` não existe no diretório do source
- **THEN** o sistema invoca ffmpeg para extrair o áudio de `aula01.mp4` para `aula01.mp3` no mesmo diretório, e usa esse `.mp3` para a transcrição

#### Scenario: Reuso de `.mp3` existente
- **WHEN** o usuário executa `local-transcribe aula01.mp4` e `aula01.mp3` já existe ao lado do source
- **THEN** o sistema NÃO invoca ffmpeg; usa o `.mp3` existente diretamente para a transcrição

#### Scenario: `--force` não re-extrai
- **WHEN** o usuário executa `local-transcribe aula01.mp4 --force` e `aula01.mp3` já existe ao lado do source
- **THEN** o sistema reusa o `.mp3` existente (não invoca ffmpeg) mas força re-transcrição

#### Scenario: Input já é áudio
- **WHEN** o usuário executa `local-transcribe aula01.mp3` (ou `.m4a`, `.wav`)
- **THEN** o sistema NÃO invoca ffmpeg; usa o arquivo de áudio diretamente para a transcrição

#### Scenario: Source em diretório read-only
- **WHEN** o usuário executa `local-transcribe /readonly/aula01.mp4` em um diretório onde não tem permissão de escrita, e `aula01.mp3` não existe ao lado
- **THEN** o sistema imprime erro claro indicando que o diretório do source não é gravável e termina com exit code não-zero, SEM extrair para `/tmp` automaticamente

### Requirement: Skip por arquivo já transcrito
O sistema SHALL pular o processamento de arquivos cujo output já existe no destino esperado, permitindo retomar batches após falhas ou re-execuções sem repetir trabalho. O sistema SHALL detectar o output esperado consultando o caminho `<out>/[<sub>/]<rel-path>/YYYY-MM-DD_<slug>/meta.json` cujo `source_path` casa com o caminho absoluto do arquivo de entrada. A flag `--force` SHALL ignorar o skip e re-transcrever.

#### Scenario: Skip de arquivo já transcrito
- **WHEN** o usuário executa `local-transcribe aula01.mp4` e existe uma subpasta `YYYY-MM-DD_aula01/` no output cujo `meta.json` tem `source_path` igual ao caminho absoluto de `aula01.mp4`
- **THEN** o sistema imprime mensagem de skip e não invoca transcrição; exit code 0

#### Scenario: Skip em batch
- **WHEN** o usuário executa `local-transcribe --dir ~/curso` onde alguns arquivos já foram transcritos e outros não
- **THEN** o sistema pula os já transcritos (mensagem de skip por arquivo) e processa os pendentes; ao final, exit code 0 se todos os pendentes processaram

#### Scenario: `--force` ignora skip
- **WHEN** o usuário executa `local-transcribe aula01.mp4 --force` e já existe transcrição para esse arquivo
- **THEN** o sistema re-transcreve, sobrescrevendo a transcrição anterior

### Requirement: Output organizado via `--subfolder` espelhando árvore do source
O sistema SHALL aceitar uma flag `--subfolder <name>` que cria um nível de pasta dentro do output base. Em modo `--dir`, o caminho relativo do arquivo dentro do diretório varrido SHALL ser espelhado dentro do subfolder. Sem `--subfolder`, o output SHALL ir flat em `<out>/YYYY-MM-DD_<slug>/`.

#### Scenario: Output com `--subfolder` em modo `--dir`
- **WHEN** o usuário executa `local-transcribe --dir ~/Cursos/devin-mastering --subfolder devin-mastering` e o source tem `modulo01/aula01.mp4`
- **THEN** o output vai para `<out>/devin-mastering/modulo01/YYYY-MM-DD_aula01/`

#### Scenario: Output sem `--subfolder`
- **WHEN** o usuário executa `local-transcribe aula01.mp4`
- **THEN** o output vai flat para `<out>/YYYY-MM-DD_aula01/`

#### Scenario: `--subfolder` em modo posicional
- **WHEN** o usuário executa `local-transcribe aula01.mp4 --subfolder devin-mastering`
- **THEN** o output vai para `<out>/devin-mastering/YYYY-MM-DD_aula01/` (sem `rel-path` porque não há `--dir`)

### Requirement: Resolução do output base via config.yaml
O sistema SHALL resolver o diretório base de output via cascata `--output` CLI > `config.yaml` seção `local_transcribe.default_output` > erro. O tilde (`~`) e variáveis SHALL ser expandidas; o path SHALL ser resolvido para absoluto.

#### Scenario: `--output` CLI tem precedência
- **WHEN** o usuário executa `local-transcribe aula01.mp4 --output ./meu-out` e `config.yaml` define outro `default_output`
- **THEN** o sistema usa `./meu-out` (resolvido para absoluto)

#### Scenario: Fallback para config.yaml
- **WHEN** o usuário executa `local-transcribe aula01.mp4` sem `--output` e `config.yaml` define `local_transcribe.default_output: ~/transcricoes-cursos`
- **THEN** o sistema usa `~/transcricoes-cursos` (expandindo `~`)

#### Scenario: Sem `--output` e sem config
- **WHEN** o usuário executa `local-transcribe aula01.mp4` sem `--output` e `config.yaml` não tem `local_transcribe.default_output` (ou o arquivo não existe)
- **THEN** o sistema imprime erro instruindo o usuário (passar `--output` ou definir em `config.yaml`) e termina com exit code não-zero

### Requirement: Backends de transcrição reutilizam `transcribe_core`
O sistema SHALL suportar as mesmas flags `--api` (OpenAI Whisper API) e `--model <name>` (mlx-whisper local) que o `yt-transcribe`, reusando a função `transcribe()` do módulo `transcribe_core`. Comportamento de chunking, fallback e mensagens de erro SHALL ser idêntico ao `yt-transcribe`.

#### Scenario: Transcrição local via mlx-whisper
- **WHEN** o usuário executa `local-transcribe aula01.mp4` (sem `--api`)
- **THEN** o sistema transcreve via mlx-whisper local com o modelo default; comportamento idêntico ao `yt-transcribe` sem `--api`

#### Scenario: Transcrição via OpenAI API
- **WHEN** o usuário executa `local-transcribe aula01.mp4 --api`
- **THEN** o sistema usa a OpenAI Whisper API; arquivos `> 24MB` são chunked transparentemente (reusando lógica do `transcribe_core`)

#### Scenario: Modelo customizado
- **WHEN** o usuário executa `local-transcribe aula01.mp4 --model large-v3`
- **THEN** o sistema usa `large-v3` no mlx-whisper

### Requirement: `meta.json` com `source: "local"`
Para cada arquivo processado, o sistema SHALL escrever um `meta.json` com os campos `title`, `source: "local"`, `source_path` (path absoluto do arquivo de origem), `duration_seconds`, `language`, `transcribed_at` e `model_used`. Os campos `url` e `channel` (usados no fluxo YouTube) SHALL ser omitidos.

#### Scenario: meta.json shape
- **WHEN** o sistema processa `aula01.mp4` com sucesso
- **THEN** `meta.json` na subpasta de output contém `{"title": "aula01", "source": "local", "source_path": "<abs-path>/aula01.mp4", "duration_seconds": <int>, "language": "<detected>", "transcribed_at": "<iso>", "model_used": "<engine>"}`, SEM as chaves `url` ou `channel`

### Requirement: Logs de progresso em batch
O sistema SHALL imprimir, antes de processar cada arquivo em batch, uma linha indicando o índice atual e o total (ex: `[3/50] aula03.mp4`), seguida das mensagens de progresso de cada etapa (extração se necessária, transcrição, salvamento). No final do batch, o sistema SHALL imprimir um resumo (quantos processados, quantos pulados, quantos com erro).

#### Scenario: Batch com mix de skip e processamento
- **WHEN** o usuário executa `local-transcribe --dir ~/curso` com 5 arquivos, dos quais 2 já foram transcritos
- **THEN** o output mostra `[1/5] ... ✓` ou `[1/5] ... skip` por arquivo, e ao final imprime "3 transcritos, 2 pulados, 0 erros" (ou equivalente)

#### Scenario: Erro em um arquivo não interrompe o batch
- **WHEN** o batch processa 5 arquivos e um deles falha (ex: ffmpeg não consegue extrair áudio corrompido)
- **THEN** o sistema imprime o erro daquele arquivo, continua processando os demais, e ao final imprime o resumo refletindo a falha; exit code é não-zero se houve qualquer erro

### Requirement: Título derivado do filename
O sistema SHALL derivar o título de cada arquivo do nome base do arquivo (sem extensão), usando a mesma função de slugify do módulo `transcribe_core`. O sistema NÃO SHALL aceitar uma flag `--title` para override.

#### Scenario: Slug a partir do filename
- **WHEN** o sistema processa `Aula 01 - Introdução.mp4`
- **THEN** o `title` em `meta.json` é `"Aula 01 - Introdução"` (filename sem extensão); o slug usado no nome da pasta é `aula-01-introducao` (normalizado pela função `slugify`)
