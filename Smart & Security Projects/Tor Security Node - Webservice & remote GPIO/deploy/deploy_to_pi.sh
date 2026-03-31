#!/usr/bin/env bash
# =============================================================================
# deploy_to_pi.sh — Deploy Tor Security Node to Raspberry Pi via rsync + SSH
#
# Usage:
#   bash deploy/deploy_to_pi.sh [SSH_HOST] [REMOTE_DIR]
#
# Defaults:
#   SSH_HOST  = rasp-pi   (from ~/.ssh/config)
#   REMOTE_DIR = /home/pi/Projects/TorSecurityNode
# =============================================================================
set -euo pipefail

SSH_HOST="${1:-rasp-pi}"
REMOTE_DIR="${2:-/home/pi/Projects/TorSecurityNode}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Deploying Tor Security Node ==="
echo "  Host:   $SSH_HOST"
echo "  Remote: $REMOTE_DIR"
echo ""

# 1. Create remote directory
echo "[1/4] Creating remote directory..."
ssh "$SSH_HOST" "mkdir -p $REMOTE_DIR"

# 2. Sync project files (exclude dev/temp stuff)
echo "[2/4] Syncing files..."
rsync -avz --delete \
  --exclude='node_modules/' \
  --exclude='.env' \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache/' \
  --exclude='.git/' \
  --exclude='tor-data/' \
  --exclude='sessions/' \
  --exclude='coverage/' \
  "$PROJECT_DIR/" \
  "$SSH_HOST:$REMOTE_DIR/"

# 3. Install dependencies on Pi
echo "[3/4] Installing Node.js dependencies on Pi..."
ssh "$SSH_HOST" "cd $REMOTE_DIR && npm install --production"

# 4. Copy .env.default to .env if .env doesn't exist
echo "[4/4] Setting up .env..."
ssh "$SSH_HOST" "cd $REMOTE_DIR && [ ! -f .env ] && cp .env.default .env && echo 'Created .env from .env.default — edit it with your settings!' || echo '.env already exists'"

echo ""
echo "=== Deploy Complete ==="
echo ""
echo "Next steps on the Pi:"
echo "  1. SSH in:  ssh $SSH_HOST"
echo "  2. Edit:    cd $REMOTE_DIR && nano .env"
echo "  3. Run:     node server.js"
echo ""
echo "Optional — set up Tor Hidden Service:"
echo "  sudo bash $REMOTE_DIR/scripts/setup-tor.sh"
echo ""
echo "Optional — set up Tor Access Point:"
echo "  sudo bash $REMOTE_DIR/scripts/setup-ap.sh"
echo ""
