## ADDED Requirements

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
