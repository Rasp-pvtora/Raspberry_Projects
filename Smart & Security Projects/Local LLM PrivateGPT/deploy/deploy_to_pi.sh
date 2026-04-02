#!/usr/bin/env bash
# ─── Deploy Local LLM PrivateGPT to Raspberry Pi ────────────────
# Usage: bash deploy/deploy_to_pi.sh <ssh-host> <remote-dir>
# Example: bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/PrivateGPT

set -euo pipefail

SSH_HOST="${1:?Usage: deploy_to_pi.sh <ssh-host> <remote-dir>}"
REMOTE_DIR="${2:?Usage: deploy_to_pi.sh <ssh-host> <remote-dir>}"

echo "==> Deploying to ${SSH_HOST}:${REMOTE_DIR}"

# ── Sync files (exclude runtime data) ──
rsync -avz --delete \
    --exclude='venv/' \
    --exclude='.env' \
    --exclude='.git/' \
    --exclude='data/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    ./ "${SSH_HOST}:${REMOTE_DIR}/"

echo "==> Files synced."

# ── Remote setup ──
ssh "${SSH_HOST}" bash -s "${REMOTE_DIR}" <<'REMOTE_SCRIPT'
    REMOTE_DIR="$1"
    cd "$REMOTE_DIR"

    # Check Ollama
    if ! command -v ollama &>/dev/null; then
        echo "WARNING: Ollama is not installed. Install it with:"
        echo "  curl -fsSL https://ollama.com/install.sh | sh"
    else
        echo "==> Ollama found: $(ollama --version)"
    fi

    # Create venv if missing
    if [ ! -d "venv" ]; then
        echo "==> Creating virtual environment..."
        python3 -m venv venv
    fi

    # Install dependencies
    echo "==> Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    # Create .env from template if missing
    if [ ! -f ".env" ]; then
        echo "==> Creating .env from .env.default..."
        cp .env.default .env
        echo "NOTE: Edit .env to set SESSION_SECRET and ADMIN_PASSWORD before running."
    fi

    # Create data directories
    mkdir -p data/uploads data/chroma

    echo "==> Deployment complete."
    echo "    Start with: cd ${REMOTE_DIR} && source venv/bin/activate && python app.py"
REMOTE_SCRIPT
