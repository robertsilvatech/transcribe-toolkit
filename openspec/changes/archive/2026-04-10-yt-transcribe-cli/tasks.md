## 1. Estrutura do Projeto

- [x] 1.1 Criar `pyproject.toml` com dependências: yt-dlp, mlx-whisper, openai, python-dotenv, pydub
- [x] 1.2 Criar estrutura de módulos: `yt_transcribe/downloader.py`, `transcriber.py`, `formatter.py`, `cli.py`
- [x] 1.3 Criar `.env.example` com `OPENAI_API_KEY=`

## 2. Download de Áudio (audio-download)

- [x] 2.1 Implementar `downloader.py`: função que recebe URL e retorna caminho do áudio temporário + metadata via yt-dlp
- [x] 2.2 Implementar geração de slug a partir do título (lowercase, sem acentos, hífens, máx 60 chars)
- [x] 2.3 Garantir cleanup do arquivo temporário em `try/finally`

## 3. Transcrição (transcription)

- [x] 3.1 Implementar `transcriber.py`: função de transcrição local via mlx-whisper com retorno em verbose JSON
- [x] 3.2 Implementar fallback via OpenAI Whisper API (flag `--api`) com carregamento de `OPENAI_API_KEY` do ambiente
- [x] 3.3 Implementar chunking automático do áudio quando > 25MB para uso com `--api`, concatenando timestamps corretamente
- [x] 3.4 Verificar presença do mlx-whisper no startup e exibir mensagem clara se não encontrado

## 4. Formatação de Output (output-formatting)

- [x] 4.1 Implementar `formatter.py`: criação da pasta `YYYY-MM-DD_slug/` dentro do diretório `--output`
- [x] 4.2 Escrever `raw.txt` com texto limpo (sem timestamps)
- [x] 4.3 Escrever `raw_timestamps.txt` com segmentos prefixados por `[HH:MM:SS]`
- [x] 4.4 Escrever `raw_whisper.json` com resposta completa do Whisper
- [x] 4.5 Escrever `meta.json` com: title, channel, url, duration_seconds, language, transcribed_at, model_used

## 5. CLI (cli-interface)

- [x] 5.1 Implementar `cli.py` com argparse: argumento posicional `url`, flags `--output` (obrigatório), `--api`, `--model` (default: `medium`)
- [x] 5.2 Criar diretório `--output` automaticamente se não existir
- [x] 5.3 Adicionar feedback de progresso nas etapas: download, transcrição, escrita dos arquivos
- [x] 5.4 Tratar erros de URL inválida/vídeo indisponível com mensagem clara ao usuário
