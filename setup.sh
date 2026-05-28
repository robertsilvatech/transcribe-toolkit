#!/usr/bin/env bash
#
# setup.sh — prepara uma máquina (Mac ou Linux) pra rodar o transcribe-toolkit do zero.
#
# O que faz (idempotente):
#   0) Cria config.yaml a partir de config.yaml.example se não existir
#   1) Verifica deps do sistema (uv, ffmpeg, gh) — instrui via gerenciador apropriado (brew/apt/dnf/etc)
#   2) uv sync (instala deps Python)
#   3) Cria .env a partir de .env.example se não existir
#   4) Cria as pastas de output default (yt_transcribe e local_transcribe, se definidas)
#   5) Instala wrappers executáveis em ~/.local/bin/transcribe e ~/.local/bin/transcribe-local
#   6) Verifica se ~/.local/bin está no PATH; instrui se faltar
#
# Uso:
#   ./setup.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER_DIR="$HOME/.local/bin"
WRAPPER_PATH="$WRAPPER_DIR/transcribe"
WRAPPER_LOCAL_PATH="$WRAPPER_DIR/transcribe-local"

OS="$(uname -s)"

# Retorna comando de install sugerido pra <dep> conforme o OS detectado.
install_hint() {
    local dep="$1"
    case "$OS" in
        Darwin) echo "brew install $dep" ;;
        Linux)  echo "use o gerenciador do seu sistema (apt/dnf/pacman) para instalar '$dep'" ;;
        *)      echo "instale '$dep' manualmente — consulte a documentação oficial" ;;
    esac
}

echo "==> Setup do transcribe-toolkit"
echo "    Repo: $REPO_ROOT"
echo "    OS:   $OS"
echo

# 0. Bootstrap do config.yaml
echo "==> Configurando config.yaml"
if [[ -f "$REPO_ROOT/config.yaml" ]]; then
    echo "  ✓ config.yaml já existe — preservado"
elif [[ -f "$REPO_ROOT/config.yaml.example" ]]; then
    cp "$REPO_ROOT/config.yaml.example" "$REPO_ROOT/config.yaml"
    echo "  ✓ config.yaml criado a partir de config.yaml.example"
    echo "    ⚠  Edite $REPO_ROOT/config.yaml com os paths que fazem sentido pra você."
else
    echo "  ✗ config.yaml.example não encontrado — abortando." >&2
    exit 1
fi
echo

# 1. Check de dependências do sistema
echo "==> Verificando dependências do sistema"
missing=0
for dep in uv ffmpeg gh; do
    if ! command -v "$dep" >/dev/null 2>&1; then
        echo "  ✗ $dep não encontrado — $(install_hint "$dep")" >&2
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

# 4. Pasta de output (yt_transcribe — obrigatório)
echo "==> Criando pasta de output default (yt_transcribe)"
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

# 4b. Pasta de output (local_transcribe — opcional; skip silencioso se não definido)
echo "==> Criando pasta de output default (local_transcribe)"
if OUTPUT_LOCAL=$(uv run python -c "from local_transcribe.config import resolve_output_path; print(resolve_output_path(None))" 2>/dev/null); then
    if [[ -d "$OUTPUT_LOCAL" ]]; then
        echo "  ✓ $OUTPUT_LOCAL já existe"
    else
        mkdir -p "$OUTPUT_LOCAL"
        echo "  ✓ $OUTPUT_LOCAL criado"
    fi
else
    echo "  ⏭  local_transcribe.default_output não definido em config.yaml — pulando"
fi
echo

# 5. Wrappers globais
echo "==> Instalando comandos globais"
mkdir -p "$WRAPPER_DIR"
cat > "$WRAPPER_PATH" <<EOF
#!/usr/bin/env bash
exec "$REPO_ROOT/run.sh" "\$@"
EOF
chmod +x "$WRAPPER_PATH"
echo "  ✓ $WRAPPER_PATH → $REPO_ROOT/run.sh"
cat > "$WRAPPER_LOCAL_PATH" <<EOF
#!/usr/bin/env bash
exec "$REPO_ROOT/run-local.sh" "\$@"
EOF
chmod +x "$WRAPPER_LOCAL_PATH"
echo "  ✓ $WRAPPER_LOCAL_PATH → $REPO_ROOT/run-local.sh"
echo

# 6. Check de PATH
echo "==> Verificando PATH"
if [[ ":$PATH:" == *":$WRAPPER_DIR:"* ]]; then
    echo "  ✓ $WRAPPER_DIR já está no PATH"
else
    cat <<EOF
  ⚠  $WRAPPER_DIR NÃO está no seu PATH.
     Adicione a linha abaixo ao seu shell config (~/.zshrc ou ~/.bashrc) e abra uma nova aba:

       export PATH="\$HOME/.local/bin:\$PATH"

EOF
fi
echo

echo "==> Setup completo."
echo
echo "Próximos passos:"
echo "  1) Edite $REPO_ROOT/config.yaml com os paths que você quer usar"
echo "  2) Edite $REPO_ROOT/.env com suas API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)"
echo "  3) Se PATH foi atualizado acima, abra uma nova aba do terminal"
echo "  4) Teste YouTube: transcribe -u https://youtu.be/VIDEO_ID"
echo "  5) Teste local:   transcribe-local -f /caminho/aula.mp4"
