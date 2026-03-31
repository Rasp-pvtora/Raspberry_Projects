#!/usr/bin/env bash
# =============================================================================
# setup-tor.sh — Install and configure Tor Hidden Service on Raspberry Pi
# Run with: sudo bash scripts/setup-tor.sh
# =============================================================================
set -euo pipefail

echo "=== Tor Hidden Service Setup ==="

# 1. Install Tor and Nginx
echo "[1/5] Installing Tor and Nginx..."
apt-get update -qq
apt-get install -y tor nginx

# 2. Configure Nginx to listen on localhost only
echo "[2/5] Configuring Nginx..."
cat > /etc/nginx/sites-available/onion-site <<'NGINX'
server {
    listen 127.0.0.1:80;
    server_name localhost;

    root /var/www/onion-site;
    index index.html;

    server_tokens off;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~ /\. {
        deny all;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/onion-site /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# 3. Deploy the sample website
echo "[3/5] Deploying sample website..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
mkdir -p /var/www/onion-site
cp -r "$PROJECT_DIR/website/"* /var/www/onion-site/
chown -R www-data:www-data /var/www/onion-site

# 4. Configure Tor Hidden Service
echo "[4/5] Configuring Tor Hidden Service..."
MARKER="# --- Tor Security Node Hidden Service ---"
if ! grep -q "$MARKER" /etc/tor/torrc; then
    cat >> /etc/tor/torrc <<EOF

$MARKER
HiddenServiceDir /var/lib/tor/tor-security-node
HiddenServicePort 80 127.0.0.1:80
$MARKER END
EOF
fi

systemctl restart tor

# 5. Wait for .onion address
echo "[5/5] Waiting for .onion address..."
sleep 5
if [ -f /var/lib/tor/tor-security-node/hostname ]; then
    ONION=$(cat /var/lib/tor/tor-security-node/hostname)
    echo ""
    echo "=== SUCCESS ==="
    echo "Your .onion address: $ONION"
    echo "Access it via Tor Browser."
    echo ""
else
    echo "WARNING: .onion address not yet generated. Check: sudo systemctl status tor"
fi
