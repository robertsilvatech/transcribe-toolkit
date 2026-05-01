## Context

O projeto usa ffmpeg via yt-dlp postprocessors para converter áudio do YouTube de webm para mp3. O YouTube serve áudio nativo em webm/opus que o Whisper aceita diretamente. Nem todos os ambientes têm ffmpeg instalado.

## Goals / Non-Goals

**Goals:**
- Flag `--no-ffmpeg` que desativa conversão via postprocessors do yt-dlp
- Download em formato nativo quando flag ativa
- Erro claro quando `--no-ffmpeg` + `--api` + áudio > 25MB

**Non-Goals:**
- Mudar o comportamento padrão (mp3 via ffmpeg continua default)

## Decisions

### 1. Remover postprocessors condicionalmente

**Decisão:** Quando `no_ffmpeg=True`, `download_audio()` não inclui postprocessors no yt-dlp opts. O arquivo baixado fica no formato nativo do YouTube (geralmente webm).

**Alternativa considerada:** Converter para m4a sem ffmpeg — não é possível, yt-dlp precisa de ffmpeg para qualquer conversão.

### 2. Busca por glob em vez de extensão fixa

**Decisão:** Ao buscar o arquivo de áudio baixado, usar glob `audio.*` em vez de hardcodar `.mp3` ou `.webm`, pois a extensão varia conforme o formato nativo disponível.

## Risks / Trade-offs

- **Chunking indisponível sem ffmpeg** → Mitigation: erro claro antes de tentar transcrever, indicando que o usuário precisa de ffmpeg para áudios grandes com --api
