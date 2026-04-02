#!/bin/bash
# ──────────────────────────────────────
# WiFi Extender & Access Point Manager
# Deployment Script for Raspberry Pi
# ──────────────────────────────────────

set -e

APP_DIR="/opt/Raspberry_Projects/Hardware & Networking Projects/WiFi Extender & Access Point Manager"
SERVICE_NAME="wifi-extender"
VENV_DIR="$APP_DIR/venv"

echo "═══════════════════════════════════"
echo " WiFi Extender — Deployment Script"
echo "═══════════════════════════════════"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo)"
    exit 1
fi

# Step 1: Install system dependencies
echo "[1/8] Installing system dependencies..."
apt update
apt install -y hostapd dnsmasq iptables iw wireless-tools python3 python3-venv python3-pip

# Stop services so our app can manage them
systemctl stop hostapd dnsmasq 2>/dev/null || true
systemctl unmask hostapd 2>/dev/null || true

# Step 2: Create virtual environment
echo "[2/8] Setting up Python virtual environment..."
cd "$APP_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Create .env from template
echo "[3/8] Creating configuration..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.default" "$APP_DIR/.env"
    # Generate a random secret key
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/change-me-to-random-string/$SECRET/" "$APP_DIR/.env"
    echo "  .env created with random secret key"
else
    echo "  .env already exists, skipping"
fi

# Step 4: Set file permissions
echo "[4/8] Setting file permissions..."
chmod 600 "$APP_DIR/.env"
chmod 755 "$APP_DIR/setup_ap.py"
chmod 755 "$APP_DIR/init_db.py"
chown -R root:root "$APP_DIR/config"

# Step 5: Initialize database
echo "[5/8] Initializing database..."
cd "$APP_DIR"
source "$VENV_DIR/bin/activate"
python3 init_db.py

# Step 6: Run AP setup
echo "[6/8] Configuring Access Point..."
python3 setup_ap.py

# Step 7: Install systemd service
echo "[7/8] Installing systemd service..."
cp "$APP_DIR/deploy/wifi-extender.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

# Step 8: Generate self-signed TLS certificate
echo "[8/8] Generating TLS certificate..."
CERT_DIR="$APP_DIR/certs"
mkdir -p "$CERT_DIR"
if [ ! -f "$CERT_DIR/server.crt" ]; then
    openssl req -x509 -newkey rsa:2048 -keyout "$CERT_DIR/server.key" \
        -out "$CERT_DIR/server.crt" -days 365 -nodes \
        -subj "/CN=wifi-ap-manager/O=RaspberryPi/C=US"
    chmod 600 "$CERT_DIR/server.key"
    echo "  Self-signed certificate generated"
else
    echo "  Certificate already exists, skipping"
fi

# Done
echo ""
echo "═══════════════════════════════════"
echo " Deployment Complete!"
echo "═══════════════════════════════════"
echo ""
echo " Dashboard: http://$(hostname -I | awk '{print $1}'):5000"
echo " Default login: admin / changeme"
echo ""
echo " Service commands:"
echo "   sudo systemctl status $SERVICE_NAME"
echo "   sudo systemctl restart $SERVICE_NAME"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo ""
