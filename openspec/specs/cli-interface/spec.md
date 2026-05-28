## ADDED Requirements

### Requirement: CLI aceita URL e diretório de output
O sistema SHALL aceitar uma URL do YouTube como argumento posicional e um diretório de destino via flag `--output`. A flag `--output` SHALL ser opcional; quando ausente, o sistema SHALL resolver o destino via `config.yaml` (`yt_transcribe.default_output`). Quando nem a flag nem o config fornecerem um valor, o sistema SHALL falhar com mensagem de erro explícita instruindo o usuário sobre as opções (passar `--output` ou definir `default_output` no `config.yaml`).

#### Scenario: Uso básico com mlx-whisper local
- **WHEN** o usuário executa `python cli.py <url> --output ~/transcricoes`
- **THEN** o sistema executa o pipeline completo e salva os arquivos em `~/transcricoes/YYYY-MM-DD_titulo-do-video/`

#### Scenario: Uso com OpenAI Whisper API
- **WHEN** o usuário executa `python cli.py <url> --output ~/transcricoes --api`
- **THEN** o sistema usa a OpenAI Whisper API para transcrição em vez do mlx-whisper local

#### Scenario: Output directory não existe
- **WHEN** o diretório passado em `--output` (ou resolvido via config) não existe
- **THEN** o sistema cria o diretório automaticamente antes de prosseguir

#### Scenario: Uso sem ffmpeg
- **WHEN** o usuário executa com `--no-ffmpeg`
- **THEN** o sistema baixa o áudio no formato nativo do YouTube sem conversão e executa o pipeline normalmente

#### Scenario: --no-ffmpeg com --api e áudio grande
- **WHEN** o usuário usa `--no-ffmpeg` com `--api` e o áudio é maior que 25MB
- **THEN** o sistema exibe erro informando que chunking requer ffmpeg e encerra

#### Scenario: --output ausente, config.yaml define default_output
- **WHEN** o usuário executa `yt-transcribe <url>` sem `--output` e `config.yaml` contém `yt_transcribe.default_output: <path>`
- **THEN** o sistema resolve o output como `<path>` (com expansão de `~`) e cria a subpasta `YYYY-MM-DD_slug` dentro dele

#### Scenario: --output sobrescreve config
- **WHEN** o usuário executa `yt-transcribe <url> --output /caminho/cli` e `config.yaml` define `yt_transcribe.default_output: /caminho/config`
- **THEN** o sistema usa `/caminho/cli`, ignorando o config

#### Scenario: --output ausente e config sem default_output
- **WHEN** o usuário executa `yt-transcribe <url>` sem `--output` e `config.yaml` não contém `yt_transcribe.default_output` (ou a chave está vazia)
- **THEN** o sistema imprime mensagem de erro instruindo a passar `--output <path>` ou definir `yt_transcribe.default_output` em `config.yaml`, e termina com exit code não-zero sem baixar nada

### Requirement: Feedback de progresso ao usuário
O sistema SHALL exibir feedback de progresso em cada etapa do pipeline.

#### Scenario: Progresso durante execução
- **WHEN** o pipeline está em execução
- **THEN** o sistema exibe mensagens indicando: download concluído, transcrição em andamento, arquivos salvos

#### Scenario: Erro na URL
- **WHEN** a URL fornecida é inválida ou o vídeo está indisponível
- **THEN** o sistema exibe mensagem de erro clara e encerra sem criar diretório de output

### Requirement: Flag --model para escolha do modelo Whisper
O sistema SHALL aceitar flag opcional `--model` para selecionar o modelo do mlx-whisper.

#### Scenario: Modelo padrão
- **WHEN** `--model` não é especificado
- **THEN** o sistema usa o modelo `medium` por padrão

#### Scenario: Modelo customizado
- **WHEN** o usuário passa `--model large-v3`
- **THEN** o sistema usa o modelo especificado para transcrição

### Requirement: Flag --force para forçar re-download e re-transcrição
O sistema SHALL aceitar flag opcional `--force` que desabilita a detecção de transcrição existente, fazendo com que `yt-transcribe` execute o pipeline completo (download + transcrição + escrita) mesmo quando uma pasta correspondente já existir em `<output>`.

#### Scenario: Uso com --force quando transcrição existe
- **WHEN** existe pasta `*_<slug>` com `raw.md` e `meta.json` casando a URL, e o usuário executa `yt-transcribe <url> --output <dir> --force`
- **THEN** o sistema ignora a pasta existente, baixa o áudio, transcreve, e escreve os arquivos (sobrescrevendo `raw.md`, `raw_timestamps.md`, `raw_whisper.json`, `meta.json` se a pasta destino coincidir)

#### Scenario: Default sem --force
- **WHEN** o usuário executa `yt-transcribe <url> --output <dir>` sem `--force` e existe transcrição correspondente
- **THEN** o sistema pula download e transcrição, conforme o comportamento de skip definido na capability `audio-download`

#### Scenario: --force sem transcrição existente
- **WHEN** o usuário passa `--force` e não existe pasta correspondente
- **THEN** o sistema procede normalmente (sem efeito observável da flag); nenhum erro é emitido por causa da flag

### Requirement: Variáveis de ambiente como nível intermediário na cascata de paths
O sistema SHALL aceitar variáveis de ambiente como fonte intermediária para resolver paths de output e vault. A cascata efetiva SHALL ser `CLI flag > env var > config.yaml > erro`. Os nomes SHALL ser:
- `YT_TRANSCRIBE_OUTPUT` para `yt_transcribe.default_output`
- `LOCAL_TRANSCRIBE_OUTPUT` para `local_transcribe.default_output`
- `VAULT_PATH` para `vault_import.default_vault`

Quando a variável está definida e não é vazia, ela SHALL ter precedência sobre o `config.yaml` mas SHALL ser sobrescrita por flag de CLI explícita. Tilde (`~`) e expansão de path SHALL ser aplicados igualmente, independente da fonte.

#### Scenario: YT_TRANSCRIBE_OUTPUT define output quando config ausente
- **WHEN** `YT_TRANSCRIBE_OUTPUT=~/meu-out` está definida no ambiente, `config.yaml` não define `yt_transcribe.default_output` e o usuário roda `yt-transcribe <url>` sem `--output`
- **THEN** o sistema resolve o output como `~/meu-out` (expandido para absoluto)

#### Scenario: --output sobrescreve env var
- **WHEN** `YT_TRANSCRIBE_OUTPUT=~/env-out` está definida e o usuário roda `yt-transcribe <url> --output ~/cli-out`
- **THEN** o sistema usa `~/cli-out`, ignorando a env var

#### Scenario: env var sobrescreve config.yaml
- **WHEN** `YT_TRANSCRIBE_OUTPUT=~/env-out` está definida e `config.yaml` define `yt_transcribe.default_output: ~/config-out`
- **THEN** o sistema usa `~/env-out`

#### Scenario: env var vazia é tratada como ausente
- **WHEN** `YT_TRANSCRIBE_OUTPUT=""` está definida e `config.yaml` define um valor
- **THEN** o sistema usa o valor do `config.yaml` (env var vazia não conta)

#### Scenario: LOCAL_TRANSCRIBE_OUTPUT funciona análogo
- **WHEN** `LOCAL_TRANSCRIBE_OUTPUT=~/local-out` está definida e o usuário roda `local-transcribe aula.mp4` sem `--output`
- **THEN** o sistema resolve o output como `~/local-out`

#### Scenario: VAULT_PATH funciona análogo
- **WHEN** `VAULT_PATH=~/meu-vault` está definida e o usuário roda `vault-import <input>` sem `--vault`
- **THEN** o sistema resolve o vault como `~/meu-vault`

#### Scenario: Nenhuma fonte fornece valor
- **WHEN** nenhuma flag CLI passa o valor, env var está ausente/vazia, e `config.yaml` não tem a chave
- **THEN** o sistema imprime erro mencionando as três opções (flag, env var, config) e termina com exit code não-zero
