## Context

Ao testar com cookies em 2026-04-14, o YouTube retornou "Requested format is not available" para `bestaudio/best` porque o extractor usou clientes (`tv downgraded`, `web creator`) que exigem resolução de n-challenge JS. Pedir `-f 140` explicitamente baixou sem problema. Os itags 140 (m4a/AAC) e 251 (webm/opus) são audio-only estáveis do YouTube há anos.

## Goals / Non-Goals

**Goals:**
- Maximizar probabilidade de sucesso do download sem instalar JS runtime.
- Manter compatibilidade com `--no-ffmpeg` (que hoje aceita webm/etc).

**Non-Goals:**
- Adicionar detecção/configuração de JS runtime.
- Expor flag CLI para format selector — usuário não deve precisar pensar nisso.

## Decisions

**Decisão: usar cadeia `bestaudio[ext=m4a]/140/251/bestaudio/best`.**
Rationale: prioriza audio-only m4a (melhor compatibilidade com ffmpeg/Whisper), cai para itags explícitos se o selector por atributo falhar, e só então tenta o genérico. Alternativa `140/bestaudio/best` foi rejeitada por ser frágil se o YouTube mudar itags.

## Risks / Trade-offs

- **Risco:** YouTube eventualmente deprecar itags 140/251. Mitigação: fallback final `bestaudio/best` preserva comportamento atual.
- **Trade-off:** cadeia fixa, não configurável. Aceitável — se precisar override, usuário pode usar yt-dlp direto.
