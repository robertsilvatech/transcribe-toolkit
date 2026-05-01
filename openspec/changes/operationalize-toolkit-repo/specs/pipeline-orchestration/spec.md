## MODIFIED Requirements

### Requirement: Parser de flags com ordem livre
O sistema SHALL aceitar flags `-u`/`--url` (obrigatória), `-o`/`--output` (opcional, sem default hardcoded), `-a`/`--api` (opcional, sem valor), `--force-translate` (opcional, sem valor), `--force-vault-import` (opcional, sem valor) e `--force` (opcional, sem valor) em qualquer ordem, e flag `-h`/`--help` que imprime uso e termina com exit 0. Argumentos desconhecidos ou flags sem valor SHALL resultar em mensagem de erro e exit code não-zero. Quando `-o`/`--output` não é fornecido, o sistema SHALL delegar a resolução do output ao CLI `yt-transcribe` (que lê `config.yaml`); o `run.sh` NÃO SHALL fornecer um default hardcoded como `./out`.

#### Scenario: Ordem URL primeiro
- **WHEN** o usuário executa `./run.sh -u https://youtu.be/X -o ~/transcricoes`
- **THEN** o sistema interpreta corretamente URL e output e procede

#### Scenario: Ordem output primeiro
- **WHEN** o usuário executa `./run.sh -o ~/transcricoes -u https://youtu.be/X`
- **THEN** o sistema interpreta exatamente como no caso "URL primeiro"

#### Scenario: Long flags
- **WHEN** o usuário executa `./run.sh --url https://youtu.be/X --output ~/transcricoes`
- **THEN** o sistema interpreta exatamente como no caso de short flags

#### Scenario: --url ausente
- **WHEN** o usuário executa `./run.sh` sem `-u`/`--url`, ou apenas com `-o <dir>`
- **THEN** o sistema imprime mensagem de erro indicando que `--url` é obrigatório, imprime uso, e termina com exit 1

#### Scenario: Argumento desconhecido
- **WHEN** o usuário executa `./run.sh --foo bar`
- **THEN** o sistema imprime mensagem indicando o argumento desconhecido, imprime uso, e termina com exit 1

#### Scenario: Flag sem valor
- **WHEN** o usuário executa `./run.sh -u` (sem URL após a flag)
- **THEN** o sistema imprime mensagem indicando que a flag exige um valor, e termina com exit 1

#### Scenario: Flag --api repassada ao yt-transcribe
- **WHEN** o usuário executa `./run.sh -u <url> -a` (ou `--api` em qualquer posição)
- **THEN** o sistema invoca `yt-transcribe` adicionando `--api` aos argumentos, fazendo a transcrição via OpenAI Whisper API em vez de mlx-whisper local

#### Scenario: --api ausente
- **WHEN** o usuário executa `./run.sh -u <url>` sem `-a`/`--api`
- **THEN** o sistema invoca `yt-transcribe` sem `--api`, mantendo o comportamento default (mlx-whisper local)

#### Scenario: --help
- **WHEN** o usuário executa `./run.sh -h` ou `./run.sh --help`
- **THEN** o sistema imprime uso (flags suportadas, defaults, env vars) e termina com exit 0 sem executar nenhuma etapa

#### Scenario: --help lista flags de force
- **WHEN** o usuário executa `./run.sh -h`
- **THEN** o output de uso menciona `--force`, `--force-translate` e `--force-vault-import` com breve descrição de cada uma

#### Scenario: --output ausente é delegado ao CLI
- **WHEN** o usuário executa `./run.sh -u <url>` sem `-o`/`--output`
- **THEN** o sistema NÃO passa `--output` para `yt-transcribe`; o CLI resolve o output via `config.yaml` (`yt_transcribe.default_output`) e o `run.sh` descobre o caminho resolvido para localizar a subpasta gerada

#### Scenario: --output explícito é propagado
- **WHEN** o usuário executa `./run.sh -u <url> -o /caminho/custom`
- **THEN** o sistema invoca `yt-transcribe <url> --output /caminho/custom ...` e usa `/caminho/custom` como base para descobrir a subpasta gerada

### Requirement: Descoberta da subpasta gerada e do vault
O sistema SHALL determinar dinamicamente a subpasta criada pelo `yt-transcribe`, o caminho base de output (quando vindo do config) e o caminho do vault default sem importar código dos módulos diretamente.

#### Scenario: Identificação da subpasta criada
- **WHEN** o `yt-transcribe` termina com sucesso e cria uma subpasta `<YYYY-MM-DD>_<slug>` dentro do output base
- **THEN** o sistema identifica essa subpasta como a mais recente no output base (via `ls -td` ou equivalente) e usa-a como input das etapas seguintes

#### Scenario: Resolução do output base via config quando -o ausente
- **WHEN** o usuário executa `./run.sh -u <url>` sem `-o` e `config.yaml` define `yt_transcribe.default_output: <path>`
- **THEN** o sistema invoca um subprocess Python que chama `yt_transcribe.config.resolve_output_path(None)` para descobrir `<path>` e usa-o como base para encontrar a subpasta gerada

#### Scenario: Resolução do vault default
- **WHEN** as etapas anteriores concluíram e o sistema precisa determinar o destino do `vault-import`
- **THEN** o sistema invoca um subprocess Python que chama `vault_import.config.resolve_vault_path(None)` e usa o caminho retornado para verificar se `<vault>/raw/<slug>.md` já existe

## ADDED Requirements

### Requirement: Pipeline invocável globalmente via comando `transcribe`
O sistema SHALL ser invocável a partir de qualquer diretório do usuário através do comando `transcribe`, instalado em `~/.local/bin/transcribe`. O comando `transcribe` SHALL aceitar exatamente as mesmas flags e argumentos que `./run.sh`, propagando-os transparentemente.

#### Scenario: Invocação básica de qualquer pasta
- **WHEN** o usuário, em qualquer diretório (ex: `~/Downloads/`), executa `transcribe -u <url>`
- **THEN** o pipeline executa exatamente como `./run.sh -u <url>` rodando da raiz do projeto, com a mesma resolução de output via `config.yaml`

#### Scenario: Propagação de flags
- **WHEN** o usuário executa `transcribe --api -u <url> -o /caminho/custom --force`
- **THEN** todas as flags são propagadas inalteradas para `run.sh` e produzem o mesmo resultado de invocação direta

#### Scenario: Variáveis de ambiente são propagadas
- **WHEN** o usuário executa `BROWSER=firefox transcribe -u <url>`
- **THEN** o `run.sh` recebe `BROWSER=firefox` no ambiente e usa firefox para cookies, idêntico à invocação direta

#### Scenario: Exit code propagado
- **WHEN** `run.sh` termina com exit code N (zero ou não-zero)
- **THEN** `transcribe` termina com o mesmo exit code N
