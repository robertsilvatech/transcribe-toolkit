## ADDED Requirements

### Requirement: Download de áudio de URL do YouTube
O sistema SHALL baixar apenas o stream de áudio do vídeo (sem vídeo completo) via yt-dlp e salvar como arquivo temporário. O formato depende da flag `--no-ffmpeg`: mp3 (padrão com ffmpeg) ou formato nativo do YouTube (com `--no-ffmpeg`).

#### Scenario: Download bem-sucedido com ffmpeg (padrão)
- **WHEN** uma URL válida do YouTube é fornecida sem `--no-ffmpeg`
- **THEN** o sistema baixa o áudio e converte para mp3 via ffmpeg

#### Scenario: Download bem-sucedido sem ffmpeg
- **WHEN** uma URL válida do YouTube é fornecida com `--no-ffmpeg`
- **THEN** o sistema baixa o áudio no formato nativo (webm) sem conversão

#### Scenario: Cleanup do arquivo temporário
- **WHEN** o pipeline conclui (com sucesso ou erro)
- **THEN** o arquivo de áudio temporário é deletado

### Requirement: Extração de metadata do vídeo
O sistema SHALL extrair metadata do vídeo durante o download via yt-dlp.

#### Scenario: Metadata disponível
- **WHEN** o download é concluído
- **THEN** o sistema extrai: título, nome do canal, duração em segundos, URL original e idioma (se disponível)

### Requirement: Geração de slug para nome da pasta
O sistema SHALL gerar um slug a partir do título do vídeo para nomear a pasta de output.

#### Scenario: Título com caracteres especiais
- **WHEN** o título do vídeo contém acentos, espaços ou caracteres especiais
- **THEN** o slug é gerado em lowercase, sem acentos, espaços substituídos por hífens, limitado a 60 caracteres

### Requirement: Skip de download e transcrição quando transcrição já existe
O sistema SHALL verificar, antes de baixar áudio, se já existe uma subpasta em `<output>` que corresponda ao vídeo solicitado e contenha transcrição válida. Quando encontrada, o sistema SHALL pular o download e a transcrição, imprimir o caminho da pasta detectada, e atualizar o mtime da pasta para preservar a integração com scripts que usam `ls -td`.

A detecção SHALL ser baseada em duas condições:
1. Pasta cujo nome bate o glob `*_<slug>`, onde `<slug>` é derivado do título atual do vídeo via a mesma lógica de `_slugify`.
2. A pasta contém `raw.md` e `meta.json` com a chave `url` igual à URL solicitada.

#### Scenario: Re-execução com transcrição existente
- **WHEN** o usuário executa `yt-transcribe <url> --output <dir>` e existe `<dir>/<qualquer-data>_<slug>/` com `raw.md` e `meta.json` cuja `url` casa com `<url>`
- **THEN** o sistema imprime mensagem indicando "Já transcrito: <path>", atualiza o mtime da pasta detectada, e termina com exit code 0 sem baixar áudio nem invocar transcrição

#### Scenario: Slug colide entre vídeos diferentes
- **WHEN** existe uma pasta `*_<slug>` cuja `meta.json["url"]` é diferente da URL solicitada
- **THEN** o sistema NÃO pula; procede com download e transcrição normais (criando nova pasta se necessário)

#### Scenario: Pasta legada sem meta.json
- **WHEN** existe uma pasta `*_<slug>` com `raw.md` mas sem `meta.json` (ou com JSON inválido)
- **THEN** o sistema NÃO pula; procede com download e transcrição normais

#### Scenario: Múltiplas pastas candidatas com URL match
- **WHEN** existem múltiplas pastas `*_<slug>` em `<output>` cujas `meta.json["url"]` casam com a URL solicitada (ex: execuções em dias diferentes)
- **THEN** o sistema escolhe a pasta com nome lexicograficamente maior (data mais recente) e pula

### Requirement: Consulta de metadata sem download
O sistema SHALL fornecer um modo de consulta de metadata do vídeo que não baixa áudio (`extract_info(download=False)` no yt-dlp), reusando configurações relevantes (`cookiesfrombrowser`, `player_client`).

#### Scenario: Metadata consultada com cookies
- **WHEN** o usuário passou `--cookies-from-browser <browser>`
- **THEN** a consulta de metadata é feita com a mesma fonte de cookies, garantindo acesso a vídeos não listados

#### Scenario: Metadata sem cookies
- **WHEN** o usuário não passou `--cookies-from-browser`
- **THEN** a consulta de metadata usa o mesmo `player_client` default (`android_vr`) usado no download
