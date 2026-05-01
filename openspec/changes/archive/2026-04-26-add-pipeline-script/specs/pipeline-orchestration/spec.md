## ADDED Requirements

### Requirement: Script orquestrador end-to-end
O sistema SHALL fornecer um shell script `run.sh` na raiz do projeto que executa em sequência os 3 módulos (`yt-transcribe` → `translate` → `vault-import`) a partir de uma URL do YouTube, parando imediatamente se qualquer etapa falhar.

#### Scenario: Execução do caminho feliz
- **WHEN** o usuário executa `./run.sh -u <url>` em pasta limpa
- **THEN** o sistema baixa e transcreve o vídeo, traduz para pt-br, e importa para o vault default; ao final, existem `raw.md`, `raw_pt-br.md` e `meta.json` na subpasta de output e `<vault>/raw/<slug>.md` no vault

#### Scenario: Output dir customizado
- **WHEN** o usuário executa `./run.sh -u <url> -o ./minha-pasta`
- **THEN** a subpasta gerada pelo `yt-transcribe` é criada dentro de `./minha-pasta` e as etapas seguintes operam sobre ela

#### Scenario: Falha em etapa intermediária para o pipeline
- **WHEN** qualquer etapa retorna exit code não-zero
- **THEN** o script termina imediatamente com o mesmo exit code, sem executar etapas subsequentes

### Requirement: Parser de flags com ordem livre
O sistema SHALL aceitar flags `-u`/`--url` (obrigatória), `-o`/`--output` (opcional, default `./out`) e `-a`/`--api` (opcional, sem valor) em qualquer ordem, e flag `-h`/`--help` que imprime uso e termina com exit 0. Argumentos desconhecidos ou flags sem valor SHALL resultar em mensagem de erro e exit code não-zero.

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

### Requirement: Skip automático de etapas concluídas
O sistema SHALL pular as etapas 2 (translate) e 3 (vault-import) se o output esperado já existir, permitindo retomar o pipeline após falhas intermediárias sem repetir trabalho concluído.

#### Scenario: Re-execução após sucesso completo
- **WHEN** o usuário executa `./run.sh -u <url>` uma segunda vez (mesma URL, mesmo dia, mesmo `OUT_BASE`)
- **THEN** etapa 1 roda normalmente (idempotência fora do escopo desta spec); etapas 2 e 3 imprimem mensagem de skip e não invocam `translate` nem `vault-import`

#### Scenario: Retomada após falha na tradução
- **WHEN** a etapa 2 falhou em uma execução anterior (ex: API key faltando), e o usuário corrigiu o ambiente e re-executou
- **THEN** etapa 1 roda, etapa 2 executa a tradução pendente, etapa 3 executa o import; nenhum trabalho da etapa 2 é repetido em execuções futuras enquanto `raw_pt-br.md` existir

#### Scenario: Detecção do output da etapa 3
- **WHEN** `<vault>/raw/<slug>.md` já existe (onde `<slug>` é o nome da subpasta gerada pela etapa 1)
- **THEN** etapa 3 imprime mensagem de skip e não invoca `vault-import`

### Requirement: Configuração de cookies do browser
O sistema SHALL passar `--cookies-from-browser` para o `yt-transcribe` por padrão, usando o navegador definido pela variável de ambiente `BROWSER` (default `chrome`), para reduzir falhas por bot-check do YouTube.

#### Scenario: Default chrome
- **WHEN** o usuário executa `./run.sh -u <url>` sem definir `BROWSER`
- **THEN** o sistema invoca `yt-transcribe` com `--cookies-from-browser chrome`

#### Scenario: Override via variável de ambiente
- **WHEN** o usuário executa `BROWSER=firefox ./run.sh -u <url>`
- **THEN** o sistema invoca `yt-transcribe` com `--cookies-from-browser firefox`

### Requirement: Descoberta da subpasta gerada e do vault
O sistema SHALL determinar dinamicamente a subpasta criada pelo `yt-transcribe` e o caminho do vault default sem importar código dos módulos diretamente.

#### Scenario: Identificação da subpasta criada
- **WHEN** o `yt-transcribe` termina com sucesso e cria uma subpasta `<YYYY-MM-DD>_<slug>` dentro de `OUT_BASE`
- **THEN** o sistema identifica essa subpasta como a mais recente em `OUT_BASE` (via `ls -td` ou equivalente) e usa-a como input das etapas seguintes

#### Scenario: Resolução do vault default
- **WHEN** as etapas anteriores concluíram e o sistema precisa determinar o destino do `vault-import`
- **THEN** o sistema invoca um subprocess Python que chama `vault_import.config.resolve_vault_path(None)` e usa o caminho retornado para verificar se `<vault>/raw/<slug>.md` já existe
