#!/usr/bin/env bash
# deploy_to_pi.sh — Deploy Sign Language Translator to Raspberry Pi
# Usage: bash deploy/deploy_to_pi.sh <pi-hostname> [remote-dir]
set -euo pipefail

PI_HOST="${1:?Usage: deploy_to_pi.sh <pi-hostname> [remote-dir]}"
REMOTE_DIR="${2:-/home/pi/Projects/SignLanguage}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Deploying to $PI_HOST:$REMOTE_DIR ==="

# Sync project files (exclude venv, __pycache__, .env, data, large models)
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '.env' \
    --exclude 'data/sign_language.db' \
    --exclude 'data/training_data/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    "$PROJECT_DIR/" "$PI_HOST:$REMOTE_DIR/"

echo ""
echo "Setting up Python environment on Pi..."
ssh "$PI_HOST" bash -s << EOF
cd "$REMOTE_DIR"

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Copy .env.default to .env if .env doesn't exist
if [ ! -f ".env" ]; then
    cp .env.default .env
    echo "Created .env from .env.default — edit it with your settings!"
fi

# Create data directory
mkdir -p data

# Setup systemd service
SERVICE_FILE="/etc/systemd/system/sign-language.service"
if [ ! -f "\$SERVICE_FILE" ]; then
    sudo tee "\$SERVICE_FILE" > /dev/null << 'SERVICE'
[Unit]
Description=Sign Language Translator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=$REMOTE_DIR
ExecStart=$REMOTE_DIR/venv/bin/python app.py
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE
    sudo systemctl daemon-reload
    sudo systemctl enable sign-language.service
    echo "systemd service installed and enabled."
fi

echo "Restarting service..."
sudo systemctl restart sign-language.service
sudo systemctl status sign-language.service --no-pager
EOF

echo ""
echo "=== Deployment complete ==="
echo "Access: http://$PI_HOST:5000"
