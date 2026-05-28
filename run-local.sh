#!/usr/bin/env bash
#
# run-local.sh — pipeline pra arquivos de mídia locais: <file>/<dir> → raw_pt-br.md.
#
# Uso:
#   ./run-local.sh -f aula01.mp4 [-o <dir>] [-s <sub>] [-a]
#   ./run-local.sh -f aula01.mp4 -f aula02.mp4 [outras flags]
#   ./run-local.sh --dir ~/curso -s curso-x [outras flags]
#
# Exemplos:
#   ./run-local.sh -f aula01.mp4                     # output do config.yaml
#   ./run-local.sh --dir ~/curso -s nome-do-curso    # batch recursivo
#   ./run-local.sh -f aula01.mp4 -a                  # OpenAI Whisper API
#   ./run-local.sh --dir ~/curso --force             # re-roda tudo
#   ./run-local.sh --dir ~/curso --force-translate   # re-roda só etapa 2
#
# Comportamento:
#   1) local-transcribe  — pula por arquivo já transcrito (skip via meta.source_path).
#   2) translate         — pula por subpasta com raw_pt-br.md já presente.
#
# Não invoca vault-import (fora de escopo nesta change).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FILES=()
DIR=""
OUT_BASE=""
SUBFOLDER=""
USE_API=0
FORCE_LOCAL=0
FORCE_TRANSLATE=0

usage() {
    cat <<EOF
uso: ./run-local.sh (-f <file> | --dir <path>) [-o <dir>] [-s <sub>] [-a] [--force | --force-translate]

Flags:
  -f, --file <file>       Arquivo de mídia local (.mp4/.mov/.mkv/.m4a/.mp3/.wav). Pode repetir.
  --dir <path>            Diretório (varre recursivamente arquivos suportados).
  -o, --output <dir>      Diretório base de output (default: local_transcribe.default_output do config.yaml).
  -s, --subfolder <name>  Subpasta dentro do output base; em modo --dir, a árvore do source é espelhada.
  -a, --api               Usar OpenAI Whisper API (em vez de mlx-whisper local).
  --force                 Re-roda transcribe e translate (sobrescreve outputs).
  --force-translate       Re-roda só a etapa 2 (sobrescreve raw_pt-br.md).
  -h, --help              Mostra esta mensagem.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--file)
            if [[ $# -lt 2 ]]; then
                echo "Erro: $1 exige um valor" >&2
                exit 1
            fi
            FILES+=("$2")
            shift 2
            ;;
        --dir)
            if [[ $# -lt 2 ]]; then
                echo "Erro: $1 exige um valor" >&2
                exit 1
            fi
            DIR="$2"
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
        -a|--api)
            USE_API=1
            shift
            ;;
        --force-translate)
            FORCE_TRANSLATE=1
            shift
            ;;
        --force)
            FORCE_LOCAL=1
            FORCE_TRANSLATE=1
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

if [[ ${#FILES[@]} -eq 0 && -z "$DIR" ]]; then
    echo "Erro: passe pelo menos um -f/--file ou --dir <path>." >&2
    usage >&2
    exit 1
fi

# Etapa 1: local-transcribe
LT_ARGS=()
for f in "${FILES[@]}"; do
    LT_ARGS+=("$f")
done
if [[ -n "$DIR" ]]; then
    LT_ARGS+=(--dir "$DIR")
fi
if [[ -n "$OUT_BASE" ]]; then
    LT_ARGS+=(--output "$OUT_BASE")
fi
if [[ -n "$SUBFOLDER" ]]; then
    LT_ARGS+=(--subfolder "$SUBFOLDER")
fi
if [[ "$USE_API" -eq 1 ]]; then
    LT_ARGS+=(--api)
fi
if [[ "$FORCE_LOCAL" -eq 1 ]]; then
    LT_ARGS+=(--force)
fi

uv run --project "$SCRIPT_DIR" local-transcribe "${LT_ARGS[@]}"

# Resolve OUT_BASE via config se o usuário não passou -o.
if [[ -z "$OUT_BASE" ]]; then
    OUT_BASE=$(uv run --project "$SCRIPT_DIR" python -c "from local_transcribe.config import resolve_output_path; print(resolve_output_path(None))")
fi

# Determina onde varrer subpastas geradas: <OUT_BASE>/[<SUBFOLDER>]
SCAN_BASE="$OUT_BASE"
if [[ -n "$SUBFOLDER" ]]; then
    SCAN_BASE="$OUT_BASE/$SUBFOLDER"
fi

if [[ ! -d "$SCAN_BASE" ]]; then
    echo "Aviso: $SCAN_BASE não existe — nada para traduzir." >&2
    exit 0
fi

# Etapa 2: translate por subpasta
# Encontra todas as subpastas com raw.md + meta.json (qualquer profundidade).
# `-print0` + `read -d ''` pra suportar paths com espaços.
while IFS= read -r -d '' META; do
    SUBDIR="$(dirname "$META")"
    if [[ ! -f "$SUBDIR/raw.md" ]]; then
        continue
    fi
    if [[ -f "$SUBDIR/raw_pt-br.md" && "$FORCE_TRANSLATE" -eq 0 ]]; then
        echo "⏭  translate: $SUBDIR/raw_pt-br.md já existe, pulando"
        continue
    fi
    SRC_LANG=$(uv run --project "$SCRIPT_DIR" python -c "import json,sys; d=json.load(open(sys.argv[1])); print(str(d.get('language','')).lower())" "$META" 2>/dev/null || echo "")
    if [[ "$SRC_LANG" == "portuguese" || "$SRC_LANG" == "pt" || "$SRC_LANG" == "pt-br" ]]; then
        echo "⏭  translate: conteúdo já em português ($SRC_LANG), copiando raw.md → raw_pt-br.md em $SUBDIR"
        cp "$SUBDIR/raw.md" "$SUBDIR/raw_pt-br.md"
    else
        uv run --project "$SCRIPT_DIR" translate "$SUBDIR/raw.md"
    fi
done < <(find "$SCAN_BASE" -type f -name meta.json -print0)
