#!/usr/bin/env bash
# =============================================================================
# generate-cert.sh — Generate a self-signed TLS certificate (optional manual)
# Run with: bash scripts/generate-cert.sh
#
# NOTE: The server auto-generates a cert on startup when HTTPS_ENABLED=true
# and no cert files are found. This script is only needed if you want to
# manually create certs or use openssl instead of the Node.js selfsigned lib.
# =============================================================================
set -euo pipefail

CERT_DIR="${1:-./certs}"
DAYS="${2:-365}"
CN="${3:-TorSecurityNode}"

mkdir -p "$CERT_DIR"

echo "Generating self-signed certificate..."
echo "  Directory : $CERT_DIR"
echo "  Valid for : $DAYS days"
echo "  Common Name: $CN"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$CERT_DIR/key.pem" \
  -out "$CERT_DIR/cert.pem" \
  -days "$DAYS" \
  -subj "/CN=$CN" \
  2>/dev/null

chmod 600 "$CERT_DIR/key.pem"
chmod 644 "$CERT_DIR/cert.pem"

echo ""
echo "Done. Certificate files:"
echo "  $CERT_DIR/cert.pem"
echo "  $CERT_DIR/key.pem"
echo ""
echo "Enable HTTPS in .env:"
echo "  HTTPS_ENABLED=true"
echo "  HTTPS_CERT_PATH=$CERT_DIR/cert.pem"
echo "  HTTPS_KEY_PATH=$CERT_DIR/key.pem"
