## MODIFIED Requirements

### Requirement: Parser de flags com ordem livre
O sistema SHALL aceitar flags `-u`/`--url` (obrigatória), `-o`/`--output` (opcional, default `./out`), `-a`/`--api` (opcional, sem valor), `--force-translate` (opcional, sem valor), `--force-vault-import` (opcional, sem valor) e `--force` (opcional, sem valor) em qualquer ordem, e flag `-h`/`--help` que imprime uso e termina com exit 0. Argumentos desconhecidos ou flags sem valor SHALL resultar em mensagem de erro e exit code não-zero.

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

### Requirement: Skip automático de etapas concluídas
O sistema SHALL pular as etapas 2 (translate) e 3 (vault-import) se o output esperado já existir, permitindo retomar o pipeline após falhas intermediárias sem repetir trabalho concluído. O sistema SHALL permitir que o usuário ignore o skip por etapa via flags de force.

#### Scenario: Re-execução após sucesso completo
- **WHEN** o usuário executa `./run.sh -u <url>` uma segunda vez (mesma URL, mesmo dia, mesmo `OUT_BASE`)
- **THEN** etapa 1 roda normalmente (idempotência fora do escopo desta spec); etapas 2 e 3 imprimem mensagem de skip e não invocam `translate` nem `vault-import`

#### Scenario: Retomada após falha na tradução
- **WHEN** a etapa 2 falhou em uma execução anterior (ex: API key faltando), e o usuário corrigiu o ambiente e re-executou
- **THEN** etapa 1 roda, etapa 2 executa a tradução pendente, etapa 3 executa o import; nenhum trabalho da etapa 2 é repetido em execuções futuras enquanto `raw_pt-br.md` existir

#### Scenario: Detecção do output da etapa 3
- **WHEN** `<vault>/raw/<slug>.md` já existe (onde `<slug>` é o nome da subpasta gerada pela etapa 1)
- **THEN** etapa 3 imprime mensagem de skip e não invoca `vault-import`

#### Scenario: --force-vault-import ignora skip da etapa 3
- **WHEN** o usuário executa `./run.sh -u <url> --force-vault-import` e `<vault>/raw/<slug>.md` já existe
- **THEN** etapa 3 NÃO pula; o sistema invoca `vault-import` com a flag `--force` para sobrescrever o destino

#### Scenario: --force-translate ignora skip da etapa 2
- **WHEN** o usuário executa `./run.sh -u <url> --force-translate` e `raw_pt-br.md` já existe na subpasta
- **THEN** etapa 2 NÃO pula; o sistema invoca `translate` (que sempre sobrescreve `raw_pt-br.md`)

#### Scenario: --force agrega todas as flags de force
- **WHEN** o usuário executa `./run.sh -u <url> --force`
- **THEN** o sistema invoca `yt-transcribe` com `--force`, ignora o skip da etapa 2 e invoca `translate`, e ignora o skip da etapa 3 e invoca `vault-import` com `--force`

#### Scenario: --force combinada com --force-translate é idempotente
- **WHEN** o usuário executa `./run.sh -u <url> --force --force-translate`
- **THEN** o comportamento é idêntico a `--force` sozinho — nenhum erro, nenhuma duplicação de trabalho

#### Scenario: Sem flags de force, comportamento default preservado
- **WHEN** o usuário executa `./run.sh -u <url>` sem nenhuma flag de force
- **THEN** o sistema mantém o skip automático nas etapas 2 e 3 quando os outputs já existem
