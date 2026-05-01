#!/usr/bin/env bash
#
# setup.sh — prepara uma máquina Mac pra rodar o transcribe-toolkit do zero.
#
# O que faz (idempotente):
#   1) Verifica deps do sistema (uv, ffmpeg, gh) — instrui se faltar
#   2) uv sync (instala deps Python)
#   3) Cria .env a partir de .env.example se não existir
#   4) Cria a pasta de output default (definida em config.yaml)
#   5) Instala wrapper executável em ~/.local/bin/transcribe
#   6) Verifica se ~/.local/bin está no PATH; instrui se faltar
#
# Uso:
#   ./setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_DIR="$HOME/.local/bin"
WRAPPER_PATH="$WRAPPER_DIR/transcribe"

echo "==> Setup do transcribe-toolkit"
echo "    Repo: $REPO_ROOT"
echo

# 1. Check de dependências do sistema
echo "==> Verificando dependências do sistema"
missing=0
for dep in uv ffmpeg gh; do
    if ! command -v "$dep" >/dev/null 2>&1; then
        echo "  ✗ $dep não encontrado — instale com: brew install $dep" >&2
        missing=1
    else
        echo "  ✓ $dep"
    fi
done
if [[ "$missing" -eq 1 ]]; then
    echo
    echo "Erro: instale as dependências faltantes e rode ./setup.sh novamente." >&2
    exit 1
fi
echo

# 2. uv sync
echo "==> uv sync"
uv sync
echo

# 3. .env
echo "==> Configurando .env"
if [[ -f "$REPO_ROOT/.env" ]]; then
    echo "  ✓ .env já existe — preservado"
else
    if [[ -f "$REPO_ROOT/.env.example" ]]; then
        cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
        echo "  ✓ .env criado a partir de .env.example"
        echo "    ⚠  Edite $REPO_ROOT/.env com suas API keys antes de usar."
    else
        echo "  ✗ .env.example não encontrado — pulando"
    fi
fi
echo

# 4. Pasta de output
echo "==> Criando pasta de output default"
if ! OUTPUT_DIR=$(uv run python -c "from yt_transcribe.config import resolve_output_path; print(resolve_output_path(None))" 2>&1); then
    echo "  ✗ Não foi possível resolver a pasta de output." >&2
    echo "    Verifique se config.yaml contém yt_transcribe.default_output." >&2
    echo "    Detalhes: $OUTPUT_DIR" >&2
    exit 1
fi
if [[ -d "$OUTPUT_DIR" ]]; then
    echo "  ✓ $OUTPUT_DIR já existe"
else
    mkdir -p "$OUTPUT_DIR"
    echo "  ✓ $OUTPUT_DIR criado"
fi
echo

# 5. Wrapper global
echo "==> Instalando comando global \`transcribe\`"
mkdir -p "$WRAPPER_DIR"
cat > "$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
exec "$REPO_ROOT/run.sh" "\$@"
EOF
chmod +x "$WRAPPER_PATH"
echo "  ✓ $WRAPPER_PATH → $REPO_ROOT/run.sh"
echo

# 6. Check de PATH
echo "==> Verificando PATH"
if [[ ":$PATH:" == *":$WRAPPER_DIR:"* ]]; then
    echo "  ✓ $WRAPPER_DIR já está no PATH"
else
    cat <<EOF
  ⚠  $WRAPPER_DIR NÃO está no seu PATH.
     Adicione a linha abaixo ao seu ~/.zshrc e abra uma nova aba do terminal:

       export PATH="\$HOME/.local/bin:\$PATH"

EOF
fi
echo

echo "==> Setup completo."
echo
echo "Próximos passos:"
echo "  1) Edite $REPO_ROOT/.env com suas API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)"
echo "  2) Se PATH foi atualizado acima, abra uma nova aba do terminal"
echo "  3) Teste: transcribe -u https://youtu.be/VIDEO_ID"
