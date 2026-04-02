# Implementation Plan
## Blockchain Full Node

---

## Executive Summary

Configure a Raspberry Pi 4 (8GB) / Pi 5 with a 2TB NVMe SSD to run a Bitcoin Core full validation node that downloads and verifies the entire blockchain (~600GB). The node validates every transaction independently — no trust in third-party servers. Optional services include Lightning Network (LND), Electrum Personal Server, BTCPay Server, BTC RPC Explorer, Tor routing, mempool visualization, UPS protection, and Ethereum Nimbus light client. A Flask + SocketIO dark-themed dashboard monitors sync status, peer count, mempool size, block height, disk usage, and all optional services. All features are `.env` toggleable.

**Budget:** ~$95–175 | **Timeline:** 7–14 days (IBD dominates: 5–10 days)

---

## Phase 1: Foundation (Day 1 — Morning)

### 1.1 Hardware Assembly
| Step | Action | Duration |
|------|--------|----------|
| 1 | Flash Pi OS 64-bit (Bookworm) with SSH enabled | 10 min |
| 2 | Connect Ethernet (**required** for IBD), boot, SSH via `ssh rasp-pi` | 5 min |
| 3 | Full system update: `sudo apt update && sudo apt upgrade -y` | 10 min |
| 4 | Connect 2TB NVMe SSD via USB 3.0 enclosure to blue USB 3.0 port | 2 min |

### 1.2 SSD Preparation
```bash
# Identify disk
lsblk

# Format (WARNING: erases all data)
sudo mkfs.ext4 /dev/sda1

# Mount
sudo mkdir -p /mnt/ssd
sudo mount /dev/sda1 /mnt/ssd

# Persist across reboots
echo '/dev/sda1 /mnt/ssd ext4 defaults,noatime,nofail 0 2' | sudo tee -a /etc/fstab

# Ownership
sudo chown -R $USER:$USER /mnt/ssd

# Create directory structure
mkdir -p /mnt/ssd/{bitcoin,lnd,nimbus}
```

### 1.3 Swap Configuration (Pi 4 — Critical for IBD)
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 1.4 Verify Performance
```bash
# SSD speed
sudo hdparm -Tt /dev/sda
# Expect: ~300+ MB/sec buffered reads via USB 3.0

# Memory
free -h
# Expect: ~8GB RAM + 4GB swap
```

**Milestone:** Pi ready with SSD mounted, swap configured, Ethernet connected.

---

## Phase 2: Bitcoin Core Installation (Day 1 — Afternoon)

### 2.1 Download & Verify
```bash
# Download Bitcoin Core (check bitcoincore.org for latest version)
BITCOIN_VERSION="27.0"
wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/bitcoin-${BITCOIN_VERSION}-aarch64-linux-gnu.tar.gz
wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/SHA256SUMS
wget https://bitcoincore.org/bin/bitcoin-core-${BITCOIN_VERSION}/SHA256SUMS.asc

# Verify checksum
sha256sum --check SHA256SUMS --ignore-missing

# Verify GPG signatures (import Bitcoin Core signing keys first)
gpg --keyserver hkps://keys.openpgp.org --recv-keys <signing-key-fingerprints>
gpg --verify SHA256SUMS.asc SHA256SUMS
```

### 2.2 Install
```bash
tar -xzf bitcoin-${BITCOIN_VERSION}-aarch64-linux-gnu.tar.gz
sudo install -m 0755 -o root -g root -t /usr/local/bin bitcoin-${BITCOIN_VERSION}/bin/*
bitcoind --version
bitcoin-cli --version
```

### 2.3 Configure
```bash
# Project setup
mkdir -p ~/fullnode/data
cd ~/fullnode

# Copy environment
cp .env.example .env
nano .env     # Set RPC credentials, toggle features

# Generate RPC password
openssl rand -base64 32
# Paste into BITCOIN_RPC_PASSWORD in .env

# Generate bitcoin.conf from template
python3 -c "
from src.config import generate_bitcoin_conf
generate_bitcoin_conf()
"
# Or manually create /mnt/ssd/bitcoin/bitcoin.conf from config/bitcoin.conf.template
```

**Milestone:** Bitcoin Core installed, verified, configured.

---

## Phase 3: Initial Block Download (Days 1–10)

### 3.1 Start IBD
```bash
# Start Bitcoin Core daemon
bitcoind -datadir=/mnt/ssd/bitcoin -daemon

# Monitor sync progress
watch -n 60 'bitcoin-cli -datadir=/mnt/ssd/bitcoin getblockchaininfo | jq "{blocks, headers, verificationprogress, size_on_disk}"'
```

### 3.2 IBD Optimization Tips
| Setting | Recommendation | Impact |
|---------|---------------|--------|
| `dbcache` | 1024–2048 MB (8GB Pi) | Fastest IBD improvement |
| `blocksonly` | Enable during IBD | Skip mempool relay, save bandwidth |
| Ethernet | **Required** — not WiFi | WiFi too slow/unreliable for IBD |
| Swap | 4GB minimum | Prevents OOM crashes |

### 3.3 Monitor During IBD
```bash
# Disk usage
df -h /mnt/ssd

# System resources
htop

# CPU temperature (throttling starts at 80°C)
vcgencmd measure_temp

# Bitcoin debug log
tail -f /mnt/ssd/bitcoin/debug.log
```

> **IBD takes 5–10 days on Pi 4 with Ethernet.** This is normal. Do not interrupt the process. If the Pi crashes or loses power during IBD, the chainstate database may be corrupted, requiring a restart from scratch — this is why UPS is recommended.

**Milestone:** Bitcoin blockchain fully downloaded and verified. `verificationprogress` ≈ 1.0.

---

## Phase 4: Python Dashboard Setup (Day 2 — while IBD runs)

### 4.1 Python Environment
```bash
cd ~/fullnode
sudo apt install python3-venv python3-pip -y
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4.2 Dashboard Configuration
```bash
# Generate Flask secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Set as SECRET_KEY in .env

# Generate admin password hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())"
# Set as ADMIN_PASSWORD_HASH in .env
```

### 4.3 Initialize & Start
```bash
# Initialize SQLite database
python3 -c "from src.database import init_db; init_db()"

# Start dashboard
python -m src.app
# Access at http://192.168.216.90:5000
```

### 4.4 Verify Dashboard
1. Browse to `http://192.168.216.90:5000`
2. Login with admin credentials
3. Verify dark theme
4. Check live SocketIO updates:
   - Block height & sync progress (will be <100% during IBD)
   - Peer count
   - Mempool size (may be 0 during `blocksonly` IBD)
   - Disk usage, CPU temp, RAM

**Milestone:** Dashboard running and displaying live IBD progress.

---

## Phase 5: systemd Services (After IBD Completes)

### 5.1 Bitcoin Core Service
```bash
sudo tee /etc/systemd/system/bitcoind.service << 'EOF'
[Unit]
Description=Bitcoin Core Daemon
After=network.target

[Service]
User=pi
Type=forking
ExecStart=/usr/local/bin/bitcoind -datadir=/mnt/ssd/bitcoin -daemon -pid=/run/bitcoind/bitcoind.pid
ExecStop=/usr/local/bin/bitcoin-cli -datadir=/mnt/ssd/bitcoin stop
PIDFile=/run/bitcoind/bitcoind.pid
RuntimeDirectory=bitcoind
Restart=on-failure
RestartSec=30
TimeoutStartSec=infinity
TimeoutStopSec=600

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now bitcoind
```

### 5.2 Dashboard Service
```bash
sudo tee /etc/systemd/system/fullnode-dashboard.service << 'EOF'
[Unit]
Description=Blockchain Full Node Monitoring Dashboard
After=network.target bitcoind.service

[Service]
User=pi
WorkingDirectory=/home/pi/fullnode
ExecStart=/home/pi/fullnode/.venv/bin/python -m src.app
Restart=always
RestartSec=10
Environment=PATH=/home/pi/fullnode/.venv/bin:/usr/local/bin:/usr/bin

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now fullnode-dashboard
```

**Milestone:** Both services auto-start on boot.

---

## Phase 6: Lightning Network — LND (Optional, Post-IBD)

> **Prerequisite:** Bitcoin Core must be fully synced before starting LND.

### 6.1 Enable ZMQ in Bitcoin Core
```bash
# Add to bitcoin.conf:
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28333

# Restart Bitcoin Core
sudo systemctl restart bitcoind
```

### 6.2 Install LND
```bash
LND_VERSION="0.18.0-beta"
wget https://github.com/lightningnetwork/lnd/releases/download/v${LND_VERSION}/lnd-linux-arm64-v${LND_VERSION}.tar.gz
# Verify signature (check LND release page for manifest + GPG key)
tar -xzf lnd-linux-arm64-v${LND_VERSION}.tar.gz
sudo install -m 0755 lnd-linux-arm64-v${LND_VERSION}/{lnd,lncli} /usr/local/bin/
```

### 6.3 Configure & Start
```bash
# Set ENABLE_LND=true in .env
# Generate lnd.conf from template

mkdir -p /mnt/ssd/lnd
lnd --configfile=/mnt/ssd/lnd/lnd.conf &

# Create wallet (first time only)
lncli create
# SAVE THE SEED PHRASE OFFLINE

# Unlock wallet (on subsequent starts)
lncli unlock
```

### 6.4 Verify
```bash
lncli getinfo
# Verify synced_to_chain=true and synced_to_graph progressing
```

**Milestone:** LND running, synced to chain, visible on dashboard.

---

## Phase 7: Electrum Personal Server (Optional)

### 7.1 Install
```bash
pip install electrum-personal-server
```

### 7.2 Configure
```bash
# Set ENABLE_ELECTRUM_SERVER=true in .env
# Set ELECTRUM_WALLETS= with xpub/zpub exported from Cold Wallet via QR
```

### 7.3 Initial Scan
```bash
# First run — scans blockchain for wallet transactions (can take hours)
electrum-personal-server config.ini
```

> **Pairs with 🧊 Air-Gapped Cold Storage Crypto Wallet:** Export your watch-only xpub/zpub via QR code from the cold wallet, then import it here for full sovereignty — your own keys + your own node.

**Milestone:** Electrum desktop connects to your own node.

---

## Phase 8: Tor Routing (Optional)

### 8.1 Install & Configure
```bash
sudo apt install tor -y

# Generate hashed password
tor --hash-password "YOUR_TOR_PASSWORD"

# Set ENABLE_TOR=true in .env
# Run setup script
sudo bash scripts/setup_tor.sh
```

### 8.2 Update Bitcoin Core
```bash
# Add to bitcoin.conf:
proxy=127.0.0.1:9050
listen=1
bind=127.0.0.1

# For hidden service:
# Tor creates .onion address automatically

sudo systemctl restart bitcoind
```

### 8.3 Verify
```bash
bitcoin-cli getnetworkinfo | jq '.networks[] | select(.name=="onion")'
# Verify reachable=true
```

**Milestone:** Bitcoin P2P traffic routed through Tor.

---

## Phase 9: BTC RPC Explorer (Optional)

### 9.1 Install
```bash
# Install Node.js (required for BTC RPC Explorer)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install nodejs -y

git clone https://github.com/janoside/btc-rpc-explorer.git /opt/btc-rpc-explorer
cd /opt/btc-rpc-explorer
npm install
```

### 9.2 Configure
```bash
# Set ENABLE_BTC_RPC_EXPLORER=true in .env
# Configure .env for BTC RPC Explorer:
# BTCEXP_BITCOIND_HOST=127.0.0.1
# BTCEXP_BITCOIND_PORT=8332
# BTCEXP_BITCOIND_USER=bitcoinrpc
# BTCEXP_BITCOIND_PASS=<from .env>
# BTCEXP_PRIVACY_MODE=true
```

### 9.3 Start & Verify
```bash
npm start
# Access at http://192.168.216.90:3002
```

**Milestone:** Self-hosted block explorer querying your own node.

---

## Phase 10: UPS Protection (Optional)

### 10.1 Install NUT
```bash
sudo apt install nut -y
sudo nut-scanner    # Auto-detect USB UPS
```

### 10.2 Configure
```bash
# Set ENABLE_UPS=true in .env
sudo bash scripts/setup_ups.sh
# Configures ups.conf, upsmon.conf from templates

sudo systemctl enable --now nut-server nut-monitor
```

### 10.3 Verify
```bash
upsc myups
# Check battery.charge, battery.runtime, ups.status

# Test graceful shutdown
# Unplug UPS from wall → verify dashboard shows battery draining
# At UPS_SHUTDOWN_BATTERY_PCT → verify bitcoind stops, then system powers off
```

**Milestone:** UPS monitoring on dashboard, graceful shutdown on power loss.

---

## Phase 11: Ethereum Nimbus Light Client (Optional)

### 11.1 Install
```bash
# Download Nimbus (check nimbus.team for latest)
wget https://github.com/status-im/nimbus-eth2/releases/download/<version>/nimbus-eth2_Linux_arm64v8.tar.gz
tar -xzf nimbus-eth2_Linux_arm64v8.tar.gz
sudo install -m 0755 build/nimbus_beacon_node /usr/local/bin/
```

### 11.2 Start
```bash
# Set ENABLE_NIMBUS=true in .env
mkdir -p /mnt/ssd/nimbus

nimbus_beacon_node \
    --data-dir=/mnt/ssd/nimbus \
    --network=mainnet \
    --light-client=on \
    --rest=true \
    --rest-port=5052 &
```

### 11.3 Verify
```bash
curl http://localhost:5052/eth/v1/node/syncing
# Verify is_syncing and head_slot values
```

**Milestone:** Dual-node (BTC + ETH) running on single Pi.

---

## Phase 12: BTCPay Server (Optional)

### 12.1 Install
```bash
# Set ENABLE_BTCPAY=true in .env
# BTCPay uses Docker internally
sudo bash scripts/install_btcpay.sh
```

### 12.2 Configure
```bash
# Point BTCPay to local Bitcoin Core RPC
# Enable LND integration (if LND enabled)
# Access admin panel at http://192.168.216.90:23000
```

**Milestone:** Self-hosted payment processor running.

---

## Phase 13: Cold Wallet Integration (After All Services Running)

### 13.1 Setup Watch-Only Wallet
1. On 🧊 Cold Wallet: export xpub/zpub as QR code
2. On Full Node: scan QR or manually enter xpub in Electrum Personal Server
3. Electrum Personal Server indexes the blockchain for your addresses

### 13.2 End-to-End PSBT Workflow
1. **Full Node** — Electrum constructs unsigned PSBT
2. **Full Node** — Display PSBT as QR code on screen
3. **Cold Wallet** — Camera reads QR → offline signing → displays signed QR
4. **Full Node** — Camera/app reads signed QR → broadcasts TX
5. **Full Node** — Verify TX appears in mempool → wait for confirmation

### 13.3 Document
- Write `docs/cold_wallet_workflow.md` with screenshots and step-by-step guide

**Milestone:** Complete financial sovereignty — your keys (cold wallet) + your node (full node).

---

## Phase 14: Production Hardening

### 14.1 Security
```bash
# Firewall
sudo ufw default deny incoming
sudo ufw allow 22/tcp       # SSH
sudo ufw allow 8333/tcp     # Bitcoin P2P
sudo ufw allow 5000/tcp     # Dashboard (LAN only)
sudo ufw enable

# Unattended security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 14.2 Monitoring
```bash
# SSD health
sudo apt install smartmontools -y
sudo smartctl -a /dev/sda

# Log rotation
sudo tee /etc/logrotate.d/fullnode << 'EOF'
/mnt/ssd/bitcoin/debug.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
EOF
```

### 14.3 Final Verification
- [ ] All systemd services start on boot
- [ ] Dashboard accessible after reboot
- [ ] Bitcoin Core stays synced
- [ ] All `.env` toggles tested
- [ ] Passwords changed from defaults
- [ ] Firewall active
- [ ] UPS tested (if enabled)

**Milestone:** Production-ready Bitcoin full node with monitoring dashboard.

---

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|-------------|
| 1. Foundation | 1 hour | None |
| 2. Bitcoin Core Install | 1 hour | Phase 1 |
| 3. IBD | 5–10 days | Phase 2 |
| 4. Dashboard | 2 hours | Phase 2 (can run during IBD) |
| 5. systemd Services | 30 min | Phase 3 (after IBD) |
| 6. Lightning (LND) | 2 hours | Phase 5 |
| 7. Electrum Server | 1 hour + scan time | Phase 5 |
| 8. Tor | 1 hour | Phase 5 |
| 9. BTC RPC Explorer | 1 hour | Phase 5 |
| 10. UPS | 30 min | Phase 1 |
| 11. Nimbus (ETH) | 1 hour | Phase 1 |
| 12. BTCPay | 1 hour | Phases 5 + 6 |
| 13. Cold Wallet Integration | 2 hours | Phase 7 |
| 14. Hardening | 1 hour | All |

**Total:** ~1–2 days active work + 5–10 days IBD wait
