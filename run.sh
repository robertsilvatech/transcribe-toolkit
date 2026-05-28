#!/usr/bin/env bash
#
# run.sh — pipeline end-to-end: URL do YouTube → arquivo no vault.
#
# Uso:
#   ./run.sh -u <url> [-o <dir>] [-a]
#   ./run.sh --url <url> [--output <dir>] [--api]
#
# Exemplos:
#   ./run.sh -u https://youtu.be/VIDEO_ID                     # output do config.yaml
#   ./run.sh -u https://youtu.be/VIDEO_ID -o ~/transcricoes   # output customizado
#   ./run.sh -o ~/transcricoes -u https://youtu.be/VIDEO_ID   # ordem livre
#   ./run.sh -u https://youtu.be/VIDEO_ID -a                  # OpenAI Whisper API
#   BROWSER=firefox ./run.sh --url https://youtu.be/VIDEO_ID
#
# Variáveis de ambiente:
#   BROWSER    Navegador para --cookies-from-browser do yt-transcribe (default: chrome).
#
# Comportamento:
#   1) yt-transcribe       — pula se já existe transcrição válida pra URL.
#   2) translate           — pula se raw_pt-br.md já existe na subpasta.
#   3) vault-import        — pula se <vault>/raw/<slug>.md já existe.
# Para qualquer cenário customizado (--api, --target-lang, --vault, etc.),
# usar os comandos individuais (ver AGENT.md / README.md).

set -euo pipefail

# Resolve o diretório do próprio script — necessário pra que `uv run` encontre
# o projeto mesmo quando o usuário invoca via wrapper (~/.local/bin/transcribe)
# de uma pasta arbitrária. Sem isso, `uv` procura pyproject.toml no CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

URL=""
OUT_BASE=""
SUBFOLDER=""
PREFIX=""
USE_API=0
BROWSER="${BROWSER:-chrome}"
FORCE_YT=0
FORCE_TRANSLATE=0
FORCE_VAULT_IMPORT=0

usage() {
    cat <<EOF
uso: ./run.sh -u <url> [-o <dir>] [-s <subfolder>] [-p <prefix>] [-a] [--force | --force-translate | --force-vault-import]

Flags:
  -u, --url <url>         URL do vídeo do YouTube (obrigatório)
  -o, --output <dir>      Diretório base de output (default: yt_transcribe.default_output do config.yaml)
  -s, --subfolder <name>  Subpasta dentro de raw/ no vault (ex: curso-mastering-devin).
                          Criada sob demanda. Sem flag, escreve direto em raw/.
  -p, --prefix <value>    Prefixo do filename (ex: A01, M01A10). Strip do YYYY-MM-DD_ do slug.
                          Final: raw/[<sub>/]<prefix>_<slug-sem-data>.md
  -a, --api               Usar OpenAI Whisper API (em vez de mlx-whisper local)
  --force                 Re-roda todas as etapas (yt-transcribe + translate + vault-import)
  --force-translate       Re-roda só a etapa 2 (sobrescreve raw_pt-br.md)
  --force-vault-import    Re-roda só a etapa 3 (sobrescreve <vault>/raw/[<sub>/][<prefix>_]<slug>.md)
  -h, --help              Mostra esta mensagem

Variáveis de ambiente:
  BROWSER                 Browser para cookies do yt-transcribe (default: chrome)
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -u|--url)
            if [[ $# -lt 2 ]]; then
                echo "Erro: $1 exige um valor" >&2
                exit 1
            fi
            URL="$2"
            shift 2
            ;;
        -o|--output)
            if [[ $# -lt 2 ]]; then
                echo "Erro: $1 exige um valor" >&2
                exit 1
            fi
            OUT_BASE="$2"
            shift 2
            ;;
        -s|--subfolder)
            if [[ $# -lt 2 ]]; then
                echo "Erro: $1 exige um valor" >&2
                exit 1
            fi
            SUBFOLDER="$2"
            shift 2
            ;;
        -p|--prefix)
            if [[ $# -lt 2 ]]; then
                echo "Erro: $1 exige um valor" >&2
                exit 1
            fi
            PREFIX="$2"
            shift 2
            ;;
        -a|--api)
            USE_API=1
            shift
            ;;
        --force-translate)
            FORCE_TRANSLATE=1
            shift
            ;;
        --force-vault-import)
            FORCE_VAULT_IMPORT=1
            shift
            ;;
        --force)
            FORCE_YT=1
            FORCE_TRANSLATE=1
            FORCE_VAULT_IMPORT=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Erro: argumento desconhecido: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ -z "$URL" ]]; then
    echo "Erro: --url é obrigatório" >&2
    usage >&2
    exit 1
fi

# Detecta se vault está configurado (env var VAULT_PATH > config.yaml).
# Vazio = vault não configurado → etapa 3 será pulada.
VAULT=$(uv run --project "$SCRIPT_DIR" python -c "
try:
    from vault_import.config import resolve_vault_path
    print(resolve_vault_path(None))
except ValueError:
    pass
" 2>/dev/null || true)

# Flags vault-specific (-s/-p) exigem vault configurado.
if [[ -z "$VAULT" ]] && [[ -n "$SUBFOLDER" || -n "$PREFIX" ]]; then
    echo "Erro: -s/--subfolder e -p/--prefix exigem um vault configurado." >&2
    echo "       Defina VAULT_PATH no ambiente ou vault_import.default_vault em config.yaml." >&2
    exit 1
fi

# Etapa 1: yt-transcribe
YT_ARGS=("$URL" --cookies-from-browser "$BROWSER")
if [[ -n "$OUT_BASE" ]]; then
    YT_ARGS+=(--output "$OUT_BASE")
fi
if [[ "$USE_API" -eq 1 ]]; then
    YT_ARGS+=(--api)
fi
if [[ "$FORCE_YT" -eq 1 ]]; then
    YT_ARGS+=(--force)
fi
uv run --project "$SCRIPT_DIR" yt-transcribe "${YT_ARGS[@]}"

# Resolve OUT_BASE via config se o usuário não passou -o (espelha cascata do CLI).
if [[ -z "$OUT_BASE" ]]; then
    OUT_BASE=$(uv run --project "$SCRIPT_DIR" python -c "from yt_transcribe.config import resolve_output_path; print(resolve_output_path(None))")
fi

# Subpasta gerada = mais recente em $OUT_BASE (slug é dinâmico, derivado do título).
DIR=$(ls -td "$OUT_BASE"/*/ | head -1)
DIR="${DIR%/}"

# Etapa 2: translate
if [[ -f "$DIR/raw_pt-br.md" && "$FORCE_TRANSLATE" -eq 0 ]]; then
    echo "⏭  translate: $DIR/raw_pt-br.md já existe, pulando"
else
    SRC_LANG=$(python3 -c "import json; d=json.load(open('$DIR/meta.json')); print(d.get('language','').lower())" 2>/dev/null || echo "")
    if [[ "$SRC_LANG" == "portuguese" || "$SRC_LANG" == "pt" || "$SRC_LANG" == "pt-br" ]]; then
        echo "⏭  translate: conteúdo já em português ($SRC_LANG), copiando raw.md → raw_pt-br.md"
        cp "$DIR/raw.md" "$DIR/raw_pt-br.md"
    else
        uv run --project "$SCRIPT_DIR" translate "$DIR/raw.md"
    fi
fi

# Etapa 3: vault-import (opcional — pula se vault não configurado)
if [[ -z "$VAULT" ]]; then
    echo "ℹ  vault-import: pulado (vault não configurado). Configure VAULT_PATH ou vault_import.default_vault em config.yaml para habilitar."
    exit 0
fi

SLUG=$(basename "$DIR")
if [[ -n "$PREFIX" ]]; then
    # Strip YYYY-MM-DD_ do slug pra casar com a lógica do importer
    SLUG_NO_DATE=$(echo "$SLUG" | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}_//')
    FILENAME="${PREFIX}_${SLUG_NO_DATE}.md"
else
    FILENAME="${SLUG}.md"
fi
if [[ -n "$SUBFOLDER" ]]; then
    DEST="$VAULT/raw/$SUBFOLDER/$FILENAME"
else
    DEST="$VAULT/raw/$FILENAME"
fi
if [[ -f "$DEST" && "$FORCE_VAULT_IMPORT" -eq 0 ]]; then
    echo "⏭  vault-import: $DEST já existe, pulando"
else
    VI_ARGS=("$DIR")
    if [[ -n "$SUBFOLDER" ]]; then
        VI_ARGS+=(--subfolder "$SUBFOLDER")
    fi
    if [[ -n "$PREFIX" ]]; then
        VI_ARGS+=(--prefix "$PREFIX")
    fi
    if [[ "$FORCE_VAULT_IMPORT" -eq 1 ]]; then
        VI_ARGS+=(--force)
    fi
    uv run --project "$SCRIPT_DIR" vault-import "${VI_ARGS[@]}"
fi
