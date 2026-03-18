#!/usr/bin/env bash
# deploy/deploy_to_pi.sh
#
# Copy project files to Raspberry Pi and install dependencies.
#
# Usage:
#   ./deploy/deploy_to_pi.sh <pi-user> <pi-host> [remote-dir]
#
# Example:
#   ./deploy/deploy_to_pi.sh pi 192.168.1.100 /home/pi/enc_decrypt
#
# Prerequisites (local machine):
#   - ssh key set up for passwordless login to Pi
#   - rsync installed locally
#
# What this script does:
#   1. Sync project source to Pi via rsync (excluding venv, cache, secrets).
#   2. Install Python deps on Pi in a remote virtualenv.
#   3. Run smoke test on Pi (import check).

set -euo pipefail

PI_USER="${1:?Usage: $0 <pi-user> <pi-host> [remote-dir]}"
PI_HOST="${2:?Usage: $0 <pi-user> <pi-host> [remote-dir]}"
REMOTE_DIR="${3:-/home/${PI_USER}/enc_decrypt}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Deploying to ${PI_USER}@${PI_HOST}:${REMOTE_DIR}"

# ---- 1. Sync files --------------------------------------------------------
rsync -avz --delete \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache/' \
  --exclude='.git/' \
  --exclude='secrets.json' \
  --exclude='*.enc' \
  "${LOCAL_DIR}/" \
  "${PI_USER}@${PI_HOST}:${REMOTE_DIR}/"

echo "==> Files synced."

# ---- 2. Install dependencies on Pi ----------------------------------------
ssh "${PI_USER}@${PI_HOST}" bash <<EOF
set -euo pipefail
cd "${REMOTE_DIR}"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "  virtualenv created."
fi

source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  Dependencies installed."
EOF

echo "==> Dependencies installed on Pi."

# ---- 3. Smoke test ---------------------------------------------------------
ssh "${PI_USER}@${PI_HOST}" bash <<EOF
set -euo pipefail
cd "${REMOTE_DIR}"
source .venv/bin/activate

python -c "
from src.enc_decrypt import crypto_core
from src.enc_decrypt.hwkey.mock_hwkey import MockHardwareKey
dek = crypto_core.generate_data_key()
t = MockHardwareKey()
assert t.unwrap_key(t.wrap_key(dek)) == dek
print('Smoke test passed.')
"
EOF

echo ""
echo "==> Deployment complete. Run CLI on Pi with:"
echo "    ssh ${PI_USER}@${PI_HOST}"
echo "    cd ${REMOTE_DIR} && source .venv/bin/activate"
echo "    python -m src.enc_decrypt.cli --help"
