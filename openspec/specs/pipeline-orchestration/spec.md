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

### Requirement: Configuração de cookies do browser
O sistema SHALL passar `--cookies-from-browser` para o `yt-transcribe` por padrão, usando o navegador definido pela variável de ambiente `BROWSER` (default `chrome`), para reduzir falhas por bot-check do YouTube.

#### Scenario: Default chrome
- **WHEN** o usuário executa `./run.sh -u <url>` sem definir `BROWSER`
- **THEN** o sistema invoca `yt-transcribe` com `--cookies-from-browser chrome`

#### Scenario: Override via variável de ambiente
- **WHEN** o usuário executa `BROWSER=firefox ./run.sh -u <url>`
- **THEN** o sistema invoca `yt-transcribe` com `--cookies-from-browser firefox`

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

### Requirement: `vault-import` é opcional em `run.sh`
O `run.sh` SHALL detectar se um vault está configurado (via `VAULT_PATH` env var, ou `vault_import.default_vault` em `config.yaml`, ou flag `--vault` se houver) e SHALL pular a etapa 3 quando nenhuma fonte fornecer um vault. Quando o vault está configurado, o comportamento atual (etapa 3 invoca `vault-import`) SHALL ser preservado integralmente.

#### Scenario: Vault não configurado, pipeline para após translate
- **WHEN** o usuário executa `./run.sh -u <url>` e nem `VAULT_PATH` nem `vault_import.default_vault` estão definidos
- **THEN** o script executa etapas 1 e 2 (yt-transcribe + translate) e termina com exit 0; etapa 3 não é invocada; uma mensagem informa que vault-import foi pulado por configuração ausente

#### Scenario: Vault configurado via config.yaml, comportamento preservado
- **WHEN** o usuário executa `./run.sh -u <url>` com `vault_import.default_vault` definido em `config.yaml`
- **THEN** o script executa as 3 etapas (incluindo vault-import) idêntico ao comportamento atual

#### Scenario: Vault configurado via VAULT_PATH
- **WHEN** o usuário executa `VAULT_PATH=~/meu-vault ./run.sh -u <url>` e `config.yaml` NÃO define `vault_import.default_vault`
- **THEN** o script executa as 3 etapas, usando `~/meu-vault` como destino

### Requirement: Flags vault-specific exigem vault configurado
Quando o usuário passa `-s/--subfolder` ou `-p/--prefix` no `run.sh` mas nenhuma fonte de vault está configurada (env var nem config.yaml), o script SHALL falhar com mensagem de erro clara antes de executar qualquer etapa.

#### Scenario: -s sem vault configurado
- **WHEN** o usuário executa `./run.sh -u <url> -s curso-x` e nem `VAULT_PATH` nem `vault_import.default_vault` estão definidos
- **THEN** o script imprime erro indicando que `-s/--subfolder` requer um vault configurado (sugere `VAULT_PATH` ou `vault_import.default_vault`) e termina com exit code não-zero antes da etapa 1

#### Scenario: -p sem vault configurado
- **WHEN** o usuário executa `./run.sh -u <url> -p A01` e nenhuma fonte de vault está definida
- **THEN** o script imprime erro análogo ao caso `-s` e termina com exit code não-zero

#### Scenario: -s com vault configurado funciona normal
- **WHEN** o usuário executa `./run.sh -u <url> -s curso-x` com `VAULT_PATH` definido
- **THEN** o script procede normalmente (não falha pela validação)

### Requirement: Script orquestrador `run-local.sh`
O sistema SHALL fornecer um shell script `run-local.sh` na raiz do projeto que executa em sequência `local-transcribe → translate` a partir de um ou mais arquivos de mídia locais (ou um diretório), parando imediatamente se qualquer etapa falhar. O `run-local.sh` NÃO SHALL invocar `vault-import` (fora de escopo desta change).

#### Scenario: Execução do caminho feliz com arquivo único
- **WHEN** o usuário executa `./run-local.sh -f aula01.mp4` (ou equivalente positional)
- **THEN** o sistema transcreve `aula01.mp4`, traduz para pt-br; ao final existem `raw.md`, `raw_pt-br.md`, `meta.json` (com `source: "local"`) na subpasta de output

#### Scenario: Execução com `--dir`
- **WHEN** o usuário executa `./run-local.sh --dir ~/curso -s nome-do-curso`
- **THEN** o sistema processa todos os arquivos suportados em `~/curso` recursivamente, traduzindo cada um após transcrever; em caso de batch, falhas individuais são reportadas mas não interrompem o batch (consistente com o comportamento do `local-transcribe` em batch)

#### Scenario: Falha em etapa intermediária para o pipeline em modo single
- **WHEN** o usuário processa um arquivo único e a etapa de transcrição falha
- **THEN** o script termina com o mesmo exit code, sem executar a etapa de tradução

#### Scenario: Skip da etapa translate se raw_pt-br.md já existe
- **WHEN** o usuário re-executa `./run-local.sh -f aula01.mp4` e `raw_pt-br.md` já existe na subpasta
- **THEN** a etapa 2 imprime mensagem de skip e não invoca `translate` (consistente com `run.sh`)

#### Scenario: Skip quando fonte já está em pt-br
- **WHEN** o `meta.json` da transcrição indica `language` em português (`pt`, `pt-br`, `portuguese`)
- **THEN** o script copia `raw.md` para `raw_pt-br.md` sem invocar o tradutor (mesma lógica do `run.sh`)

### Requirement: Parser de flags do `run-local.sh`
O sistema SHALL aceitar flags `-f`/`--file <path>` (arquivo único; pode repetir), `--dir <path>` (recursivo), `-o`/`--output <dir>` (opcional, delegado ao CLI), `-s`/`--subfolder <name>` (opcional), `-a`/`--api` (opcional, sem valor), `--force` (re-roda transcribe e translate), `--force-translate` (só etapa 2), e `-h`/`--help`. O parser SHALL aceitar flags em qualquer ordem e SHALL exigir pelo menos um `--file` OU `--dir`.

#### Scenario: --help
- **WHEN** o usuário executa `./run-local.sh -h` ou `./run-local.sh --help`
- **THEN** o sistema imprime uso (flags suportadas) e termina com exit 0 sem executar nenhuma etapa

#### Scenario: Argumento desconhecido
- **WHEN** o usuário executa `./run-local.sh --foo bar`
- **THEN** o sistema imprime mensagem indicando o argumento desconhecido, imprime uso, e termina com exit 1

#### Scenario: Sem --file nem --dir
- **WHEN** o usuário executa `./run-local.sh -o ./out` (sem nenhum input)
- **THEN** o sistema imprime mensagem de erro indicando que é obrigatório passar `--file` ou `--dir`, e termina com exit 1

#### Scenario: --file repetido
- **WHEN** o usuário executa `./run-local.sh -f aula01.mp4 -f aula02.mp4`
- **THEN** o sistema processa ambos os arquivos em batch

#### Scenario: --force propagado para local-transcribe e translate
- **WHEN** o usuário executa `./run-local.sh -f aula01.mp4 --force`
- **THEN** o sistema invoca `local-transcribe` com `--force` E re-executa `translate` mesmo se `raw_pt-br.md` já existir

### Requirement: Pipeline `run-local.sh` invocável globalmente via `transcribe-local`
O sistema SHALL ser invocável a partir de qualquer diretório do usuário através do comando `transcribe-local`, instalado em `~/.local/bin/transcribe-local`. O comando SHALL aceitar exatamente as mesmas flags e argumentos que `./run-local.sh`, propagando-os transparentemente, incluindo exit code e variáveis de ambiente.

#### Scenario: Invocação de qualquer pasta
- **WHEN** o usuário, em qualquer diretório, executa `transcribe-local -f ~/aulas/aula01.mp4`
- **THEN** o pipeline executa exatamente como `./run-local.sh -f ~/aulas/aula01.mp4` rodando da raiz do projeto

#### Scenario: Propagação de flags
- **WHEN** o usuário executa `transcribe-local --dir ~/curso -s curso-x --api --force`
- **THEN** todas as flags são propagadas inalteradas para `run-local.sh`

#### Scenario: Exit code propagado
- **WHEN** `run-local.sh` termina com exit code N (zero ou não-zero)
- **THEN** `transcribe-local` termina com o mesmo exit code N
