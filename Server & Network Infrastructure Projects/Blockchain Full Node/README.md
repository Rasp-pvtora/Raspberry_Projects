# Blockchain Full Node

<div align="center">

![Bitcoin](https://img.shields.io/badge/Bitcoin-Full_Node-F7931A?style=for-the-badge&logo=bitcoin&logoColor=white)
![Ethereum](https://img.shields.io/badge/Ethereum-Light_Node-3C3C3D?style=for-the-badge&logo=ethereum&logoColor=white)
![Lightning](https://img.shields.io/badge/Lightning-Network-FFC107?style=for-the-badge&logo=lightning&logoColor=black)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-4%2F5-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Configure a Raspberry Pi with a high-speed 2TB SSD to download and verify the entire Bitcoin blockchain (~600GB). The node validates every transaction independently — no trust in third-party servers. Optional Lightning Network (LND), Electrum Personal Server, BTCPay Server, BTC RPC Explorer, Tor routing, mempool visualization, UPS protection, and Ethereum light node (Nimbus).**

[Features](#features) • [Hardware](#hardware-requirements) • [Quick Start](#quick-start) • [Configuration](#environment-configuration) • [Dashboard](#monitoring-dashboard) • [Companion Project](#companion-project--air-gapped-cold-storage-crypto-wallet) • [Troubleshooting](#troubleshooting)

</div>

---

**If you find this project useful, consider supporting development:**

**BTC:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Libraries & Dependencies](#libraries--dependencies)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [System Overview](#system-overview)
- [Features](#features)
  - [Bitcoin Core Full Validation Node](#bitcoin-core-full-validation-node)
  - [Lightning Network (LND)](#lightning-network-lnd)
  - [Electrum Personal Server](#electrum-personal-server)
  - [BTCPay Server](#btcpay-server)
  - [BTC RPC Explorer](#btc-rpc-explorer)
  - [Tor Routing](#tor-routing)
  - [Mempool Visualization Dashboard](#mempool-visualization-dashboard)
  - [UPS Protection (NUT)](#ups-protection-nut)
  - [Ethereum Nimbus Light Client](#ethereum-nimbus-light-client)
  - [Flask Monitoring Dashboard](#flask-monitoring-dashboard)
- [Authentication](#authentication)
- [Companion Project — Air-Gapped Cold Storage Crypto Wallet](#companion-project--air-gapped-cold-storage-crypto-wallet)
- [Deployment](#deployment)
- [Running the Service](#running-the-service)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
Blockchain Full Node/
├── README.md                   # This file
├── TSD.md                      # Technical Specification Document
├── task.md                     # Development task checklist
├── implementation_plan.md      # Phased implementation guide
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
├── .env.example                # Environment variable template
├── src/
│   ├── __init__.py
│   ├── app.py                  # Flask app factory & SocketIO init
│   ├── rpc.py                  # Bitcoin Core RPC client wrapper
│   ├── lnd_client.py           # LND gRPC / REST client
│   ├── mempool.py              # Mempool stats collector
│   ├── monitor.py              # System monitor (disk, CPU, temp, peers)
│   ├── tor_manager.py          # Tor service management & status
│   ├── ups.py                  # NUT UPS monitoring & graceful shutdown
│   ├── eth_client.py           # Nimbus Ethereum light client interface
│   ├── database.py             # SQLite DB models & helpers
│   ├── auth.py                 # bcrypt auth & session management
│   ├── config.py               # .env loader & config dataclass
│   └── utils.py                # Shared utilities
├── templates/
│   ├── base.html               # Dark theme layout
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main monitoring dashboard
│   ├── mempool.html            # Mempool visualization page
│   ├── lightning.html          # Lightning Network overview
│   ├── explorer.html           # Block/TX explorer integration
│   └── settings.html           # Runtime settings panel
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme styles
│   └── js/
│       ├── dashboard.js        # SocketIO client & live status
│       ├── mempool.js          # Mempool chart rendering
│       └── lightning.js        # LN channel visualization
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures & mock mode helpers
│   ├── test_rpc.py             # Bitcoin RPC client tests
│   ├── test_lnd_client.py      # LND client tests
│   ├── test_mempool.py         # Mempool collector tests
│   ├── test_monitor.py         # System monitor tests
│   ├── test_ups.py             # UPS integration tests
│   ├── test_eth_client.py      # Nimbus client tests
│   ├── test_auth.py            # Auth & session tests
│   ├── test_api.py             # Dashboard API endpoint tests
│   └── test_database.py        # Database CRUD tests
├── deploy/
│   └── deploy_to_pi.sh         # rsync deploy script (rasp-pi)
├── scripts/
│   ├── install_bitcoin_core.sh # Download & verify Bitcoin Core
│   ├── install_lnd.sh          # Download & verify LND
│   ├── install_nimbus.sh       # Download & verify Nimbus
│   ├── install_deps.sh         # OS-level dependency installer
│   ├── setup_tor.sh            # Tor hidden service configuration
│   ├── setup_ups.sh            # NUT UPS daemon configuration
│   └── generate_password_hash.sh # Helper to generate bcrypt hash
├── config/
│   ├── bitcoin.conf.template   # Bitcoin Core configuration template
│   ├── lnd.conf.template       # LND configuration template
│   ├── torrc.template          # Tor configuration template
│   └── nut/
│       ├── ups.conf.template   # NUT UPS driver config
│       └── upsmon.conf.template# NUT monitor config
└── docs/
    ├── ibd_guide.md            # Initial Block Download optimization
    ├── lightning_guide.md       # Lightning Network usage guide
    ├── tor_guide.md            # Tor routing setup guide
    └── cold_wallet_workflow.md # Cold wallet ↔ full node workflow
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (8GB) / Pi 5 | Yes | 8GB RAM required for IBD + LND |
| 2TB NVMe SSD | Yes | Bitcoin blockchain ~600GB + indexes + room for growth |
| NVMe-to-USB 3.0 enclosure | Yes | Connect SSD via USB 3.0 to Pi |
| Ethernet cable | Yes | **Required** during Initial Block Download (IBD) |
| Power supply (5V/3A+) | Yes | Official Pi PSU |
| UPS (optional) | No | Graceful shutdown on power loss — protects blockchain DB |

> **IMPORTANT:** Initial Block Download (IBD) takes 5–10 days on a Pi 4 over Ethernet. WiFi is too slow and unreliable for IBD. After IBD completes, the node stays synced incrementally (~1-2 MB per block every 10 minutes).

---

## Budget

| Item | Estimated Cost |
|---|---|
| 2TB NVMe SSD | ~$80–120 |
| NVMe-to-USB 3.0 enclosure | ~$15 |
| UPS (optional) | ~$25–40 |
| **Total** | **~$95–175** |

*(Assumes you already own a Raspberry Pi 4/5 with 8GB RAM, power supply, and Ethernet cable.)*

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| Flask | Monitoring dashboard web framework |
| Flask-SocketIO | Real-time WebSocket for live sync status |
| python-bitcoinlib | Bitcoin Core RPC interaction & TX parsing |
| requests | HTTP client for REST APIs (LND, BTC RPC Explorer) |
| bcrypt | Password hashing for dashboard auth |
| python-dotenv | `.env` configuration loading |
| Jinja2 | HTML template rendering (included with Flask) |
| eventlet / gevent | Async worker for SocketIO |
| psutil | System resource monitoring (CPU, RAM, disk, temp) |

---

## Quick Start

```bash
# 1. SSH into the Pi
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/fullnode && cd ~/fullnode

# 3. Install OS-level dependencies
sudo bash scripts/install_deps.sh

# 4. Install Bitcoin Core
sudo bash scripts/install_bitcoin_core.sh

# 5. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 6. Configure environment
cp .env.example .env
nano .env              # Set RPC credentials, toggle features

# 7. Prepare SSD
sudo mkfs.ext4 /dev/sda1
sudo mkdir -p /mnt/ssd
sudo mount /dev/sda1 /mnt/ssd
echo '/dev/sda1 /mnt/ssd ext4 defaults,noatime,nofail 0 2' | sudo tee -a /etc/fstab
sudo chown -R $USER:$USER /mnt/ssd

# 8. Start Bitcoin Core (Initial Block Download — 5-10 days)
bitcoind -datadir=/mnt/ssd/bitcoin -daemon

# 9. Start monitoring dashboard
python -m src.app
# Dashboard at http://192.168.216.90:5000
```

---

## Environment Configuration

All features are toggleable via `.env`. Copy `.env.example` and adjust:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(generate)* | Flask session secret key |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD_HASH` | *(bcrypt hash)* | bcrypt-hashed admin password |
| `DB_PATH` | `data/fullnode.db` | SQLite database file path |
| `PI_HOST` | `192.168.216.90` | Pi IP address |
| `PI_SSH_ALIAS` | `rasp-pi` | SSH alias |
| `SSD_MOUNT` | `/mnt/ssd` | SSD mount point |
| `SSD_DEVICE` | `/dev/sda1` | SSD block device |
| `ENABLE_BITCOIN_CORE` | `true` | Toggle Bitcoin Core full node |
| `BITCOIN_DATADIR` | `/mnt/ssd/bitcoin` | Bitcoin blockchain data directory |
| `BITCOIN_RPC_USER` | `bitcoinrpc` | Bitcoin Core RPC username |
| `BITCOIN_RPC_PASSWORD` | *(generate)* | Bitcoin Core RPC password |
| `BITCOIN_RPC_HOST` | `127.0.0.1` | Bitcoin Core RPC bind address |
| `BITCOIN_RPC_PORT` | `8332` | Bitcoin Core RPC port |
| `BITCOIN_P2P_PORT` | `8333` | Bitcoin P2P network port |
| `BITCOIN_DBCACHE` | `1024` | RAM cache for IBD (MB) |
| `BITCOIN_MAXMEMPOOL` | `300` | Max mempool size (MB) |
| `BITCOIN_PRUNE` | `0` | Prune mode (0 = full node, >550 = prune to N MB) |
| `ENABLE_LND` | `false` | Toggle Lightning Network daemon |
| `LND_DIR` | `/mnt/ssd/lnd` | LND data directory |
| `LND_ALIAS` | `mynode-lightning` | Lightning node public alias |
| `LND_REST_PORT` | `8080` | LND REST API port |
| `LND_GRPC_PORT` | `10009` | LND gRPC port |
| `LND_AUTOPILOT` | `false` | Toggle LND autopilot channel management |
| `LND_WATCHTOWER` | `true` | Toggle LND watchtower client |
| `ENABLE_ELECTRUM_SERVER` | `false` | Toggle Electrum Personal Server |
| `ELECTRUM_RPC_PORT` | `50002` | Electrum server port |
| `ELECTRUM_WALLETS` | `` | Comma-separated xpub/zpub keys |
| `ENABLE_BTCPAY` | `false` | Toggle BTCPay Server |
| `BTCPAY_PORT` | `23000` | BTCPay Server port |
| `BTCPAY_DOMAIN` | `btcpay.local` | BTCPay public domain |
| `ENABLE_BTC_RPC_EXPLORER` | `false` | Toggle BTC RPC Explorer |
| `BTC_RPC_EXPLORER_PORT` | `3002` | Explorer web UI port |
| `ENABLE_TOR` | `false` | Toggle Tor routing for Bitcoin P2P |
| `TOR_SOCKS_PORT` | `9050` | Tor SOCKS proxy port |
| `TOR_CONTROL_PORT` | `9051` | Tor control port |
| `TOR_HIDDEN_SERVICE` | `false` | Expose node as Tor hidden service |
| `ENABLE_MEMPOOL_DASHBOARD` | `true` | Toggle mempool visualization |
| `MEMPOOL_REFRESH_INTERVAL` | `30` | Mempool refresh interval (seconds) |
| `ENABLE_UPS` | `false` | Toggle UPS monitoring (NUT) |
| `UPS_NAME` | `myups` | NUT UPS device name |
| `UPS_DRIVER` | `usbhid-ups` | NUT UPS driver |
| `UPS_PORT` | `auto` | NUT UPS port |
| `UPS_SHUTDOWN_BATTERY_PCT` | `20` | Battery % to trigger graceful shutdown |
| `ENABLE_NIMBUS` | `false` | Toggle Ethereum Nimbus light client |
| `NIMBUS_DATADIR` | `/mnt/ssd/nimbus` | Nimbus data directory |
| `NIMBUS_REST_PORT` | `5052` | Nimbus REST API port |
| `NIMBUS_NETWORK` | `mainnet` | Ethereum network |
| `ENABLE_WEB_DASHBOARD` | `true` | Toggle Flask monitoring dashboard |
| `DASHBOARD_HOST` | `0.0.0.0` | Dashboard bind address |
| `DASHBOARD_PORT` | `5000` | Dashboard bind port |
| `SESSION_EXPIRY_HOURS` | `24` | Session expiry in hours |
| `RATE_LIMIT` | `10/15min` | Login rate limit (attempts/window) |
| `MOCK_MODE` | `false` | Run without real services (dev/test) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     Raspberry Pi 4 (8GB) / Pi 5                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                      Bitcoin Core (bitcoind)                             │ │
│  │  Full validation node — downloads & verifies entire blockchain (~600GB) │ │
│  │  RPC :8332 | P2P :8333 | datadir: /mnt/ssd/bitcoin                     │ │
│  └───────────────┬───────────────┬───────────────┬─────────────────────────┘ │
│                  │               │               │                           │
│    ┌─────────────▼──┐  ┌────────▼────────┐  ┌───▼──────────────┐           │
│    │  LND (Lightning)│  │ Electrum Server │  │ BTCPay Server    │           │
│    │  :8080 / :10009 │  │ :50002          │  │ :23000           │           │
│    │  (optional)     │  │ (optional)      │  │ (optional)       │           │
│    └────────────────┘  └─────────────────┘  └──────────────────┘           │
│                                                                              │
│    ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐           │
│    │ BTC RPC Explorer│  │ Tor Hidden Svc  │  │ NUT UPS Monitor  │           │
│    │ :3002           │  │ :9050 / :9051   │  │ (graceful shtdn) │           │
│    │ (optional)      │  │ (optional)      │  │ (optional)       │           │
│    └────────────────┘  └─────────────────┘  └──────────────────┘           │
│                                                                              │
│    ┌────────────────┐  ┌──────────────────────────────────────────────────┐ │
│    │ Nimbus (ETH)   │  │  Flask + SocketIO Monitoring Dashboard (:5000)   │ │
│    │ :5052           │  │  - Sync status, block height, peer count        │ │
│    │ (optional)      │  │  - Mempool size & fee visualization             │ │
│    └────────────────┘  │  - Disk usage, CPU temp, RAM                     │ │
│                         │  - LN channels, ETH sync (if enabled)           │ │
│                         │  - Dark theme, bcrypt auth                       │ │
│                         └──────────────────────────────────────────────────┘ │
│                                         │                                    │
│    ┌────────────────────────────────────▼───────────────────────────────────┐│
│    │              2TB NVMe SSD (/mnt/ssd) — USB 3.0 enclosure              ││
│    │  /mnt/ssd/bitcoin/  — Bitcoin blockchain + indexes (~600GB)           ││
│    │  /mnt/ssd/lnd/      — Lightning Network data                          ││
│    │  /mnt/ssd/nimbus/   — Ethereum chain data                             ││
│    └───────────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
          │                                            │
          ▼                                            ▼
   Ethernet (Gigabit)                        Tor Network (optional)
   Bitcoin P2P :8333                         Hidden service .onion
   LND P2P :9735                             Private P2P routing
```

---

## Features

### Bitcoin Core Full Validation Node

The core of the project — a full Bitcoin Core node that downloads and independently verifies every transaction in the ~600GB blockchain. No trust in third-party servers.

- Full IBD (Initial Block Download) with verification of all blocks since genesis
- Configurable `dbcache` for IBD performance (default 1024MB on 8GB Pi)
- Mempool management with configurable max size
- Pruning mode optional (`BITCOIN_PRUNE=0` for full node, `>550` for pruned)
- RPC interface for wallet operations, block queries, and mempool inspection
- Toggle via `ENABLE_BITCOIN_CORE`

### Lightning Network (LND)

Layer-2 payment channel network for instant, low-fee Bitcoin transactions.

- LND daemon connected to local Bitcoin Core (no external dependency)
- REST and gRPC APIs for programmatic channel management
- Autopilot optional for automatic channel opening
- Watchtower client to protect against channel breaches while offline
- Channel balance monitoring via dashboard
- Toggle via `ENABLE_LND`

### Electrum Personal Server

Serve your own Electrum wallet — connect Electrum desktop/mobile to your own node instead of trusting third-party servers.

- Watch-only wallet monitoring via xpub/zpub keys
- Transaction history and balance from your own verified blockchain
- Pairs with the 🧊 Air-Gapped Cold Storage Crypto Wallet for complete sovereignty
- Toggle via `ENABLE_ELECTRUM_SERVER`

### BTCPay Server

Self-hosted Bitcoin payment processor — accept Bitcoin payments without third-party fees or custodial risk.

- Invoice generation and payment tracking
- LND integration for Lightning invoices (if LND enabled)
- Web-based admin panel
- Toggle via `ENABLE_BTCPAY`

### BTC RPC Explorer

Self-hosted blockchain explorer — query blocks, transactions, and addresses from your own node.

- Full block and transaction details
- Address balance and history lookup
- Mempool visualization
- No external API calls — all data from your local node
- Toggle via `ENABLE_BTC_RPC_EXPLORER`

### Tor Routing

Route all Bitcoin P2P traffic through the Tor network for network-level privacy.

- Bitcoin Core configured to use Tor for all outbound connections
- Optional Tor hidden service to make your node reachable as a `.onion` address
- Prevents ISP and network observers from knowing you run a Bitcoin node
- Toggle via `ENABLE_TOR`

### Mempool Visualization Dashboard

Real-time mempool statistics and fee estimation displayed in the Flask monitoring dashboard.

- Current mempool size (transactions and vbytes)
- Fee rate distribution histogram
- Estimated confirmation times per fee tier
- Auto-refresh via SocketIO (configurable interval)
- Toggle via `ENABLE_MEMPOOL_DASHBOARD`

### UPS Protection (NUT)

Uninterruptible Power Supply monitoring via Network UPS Tools (NUT) — graceful shutdown on power loss to protect the blockchain database from corruption.

- USB UPS detection and monitoring
- Battery level, load, and runtime tracking on dashboard
- Configurable shutdown threshold (`UPS_SHUTDOWN_BATTERY_PCT`)
- Automatic `bitcoind stop` before system poweroff
- Toggle via `ENABLE_UPS`

### Ethereum Nimbus Light Client

Run an Ethereum consensus layer light client alongside Bitcoin — dual-node setup on a single Pi.

- Nimbus light client syncs Ethereum beacon chain with minimal resources
- REST API for beacon chain queries
- Sync status displayed on monitoring dashboard
- Toggle via `ENABLE_NIMBUS`

### Flask Monitoring Dashboard

Dark-themed Flask + SocketIO web dashboard for real-time node monitoring.

| Metric | Source |
|---|---|
| Block height & sync progress | Bitcoin Core RPC `getblockchaininfo` |
| Peer count & network info | Bitcoin Core RPC `getnetworkinfo` |
| Mempool size & fee rates | Bitcoin Core RPC `getmempoolinfo` |
| Disk usage (SSD) | `psutil` / `shutil.disk_usage` |
| CPU temperature & RAM | `psutil` |
| LN channels & balance | LND REST API (if enabled) |
| ETH sync status | Nimbus REST API (if enabled) |
| UPS battery & runtime | NUT client (if enabled) |
| Tor connection status | Tor control port (if enabled) |

- bcrypt authentication with rate limiting (10 attempts / 15 min)
- 24-hour session expiry
- SocketIO live updates (no page refresh)
- Toggle via `ENABLE_WEB_DASHBOARD`

---

## Authentication

The Flask dashboard uses bcrypt-hashed passwords with rate limiting.

```bash
# Generate a bcrypt password hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())"

# Set in .env
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...
```

- Login rate limit: 10 attempts per 15 minutes
- Session expiry: 24 hours (configurable via `SESSION_EXPIRY_HOURS`)
- All passwords stored as bcrypt hashes — never plaintext

---

## Companion Project — 🧊 Air-Gapped Cold Storage Crypto Wallet

> ### 🛡️ Complete Financial Sovereignty
>
> The **cold wallet signs transactions offline**, and **this full node validates them**. Together they provide **complete financial sovereignty** — you generate keys on a device that never touches a network, and you verify transactions on a node that trusts no one.
>
> **They complement each other but MUST run on separate devices:**
>
> | | Full Node (this project) | Cold Wallet |
> |---|---|---|
> | **Network** | Always connected — syncs blockchain 24/7 | **NEVER connected** — air-gapped |
> | **Purpose** | Validate transactions, broadcast to network | Generate keys, sign transactions offline |
> | **Data flow** | TCP/IP (Bitcoin P2P protocol, port 8333) | QR codes only (camera ↔ display) |
> | **Security model** | No private keys stored | Keys never leave the device |
>
> **Typical workflow with PSBT:**
> 1. **Full Node** constructs an unsigned PSBT using your watch-only wallet (Electrum Personal Server)
> 2. Full Node displays the unsigned TX as a QR code on its screen
> 3. **Cold Wallet** camera reads the QR → signs the TX offline → displays signed QR
> 4. Full Node camera reads the signed QR → broadcasts the signed TX to the Bitcoin network
>
> **Why separate devices?** The cold wallet's air gap guarantees private keys are never exposed to remote attacks. The full node must be online to sync and broadcast. Combining them on one device defeats the entire purpose of cold storage.
>
> 👉 See: **Smart & Security Projects / Air-Gapped Cold Storage Crypto Wallet**

---

## Deployment

Use the deploy script to push code to the Pi:

```bash
# From development machine
bash deploy/deploy_to_pi.sh
```

The deploy script (`deploy_to_pi.sh`):
```bash
#!/usr/bin/env bash
set -euo pipefail

PI_HOST="rasp-pi"                              # SSH alias -> pi@192.168.216.90
REMOTE_DIR="/home/pi/fullnode"

echo "[*] Deploying to ${PI_HOST}:${REMOTE_DIR}"
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude 'data/' --exclude '.env' \
    ./ "${PI_HOST}:${REMOTE_DIR}/"
echo "[✓] Deploy complete"
```

---

## Running the Service

```bash
# Start Bitcoin Core
bitcoind -datadir=/mnt/ssd/bitcoin -daemon

# Check sync progress
bitcoin-cli -datadir=/mnt/ssd/bitcoin getblockchaininfo | jq '.verificationprogress'

# Start monitoring dashboard
cd ~/fullnode
source .venv/bin/activate
python -m src.app

# Optional: Start LND (after Bitcoin Core is synced)
lnd --configfile=/mnt/ssd/lnd/lnd.conf &

# Optional: Start Nimbus (Ethereum light client)
nimbus_beacon_node --data-dir=/mnt/ssd/nimbus --network=mainnet --light-client=on &
```

### systemd Service (Production)

```bash
# /etc/systemd/system/fullnode-dashboard.service
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
```

---

## Security Notes

- **RPC Credentials:** Never reuse passwords. Generate with `openssl rand -base64 32`
- **Firewall:** Only expose ports you need (`8333` for P2P, `5000` for dashboard on LAN)
- **Tor:** Enable `ENABLE_TOR=true` to prevent ISP from knowing you run a Bitcoin node
- **UPS:** Strongly recommended — unclean shutdown during IBD can corrupt the blockchain database and require re-download
- **Dashboard Auth:** Always set a strong bcrypt-hashed password; rate limiting protects against brute force
- **No Private Keys:** This node stores **no private keys** — use the companion 🧊 Cold Storage Wallet for key management

---

## Troubleshooting

| Issue | Solution |
|---|---|
| IBD extremely slow | Ensure Ethernet (not WiFi), increase `BITCOIN_DBCACHE` to 2048+ if 8GB Pi |
| `bitcoind` crashes during IBD | Check RAM + swap; increase swap to 4GB; reduce `dbcache` |
| SSD not detected | Check USB 3.0 port (blue); try different enclosure; `lsblk` to verify |
| Disk full during IBD | Bitcoin blockchain grows ~60GB/year; ensure 2TB SSD |
| LND won't start | Bitcoin Core must be fully synced first; check `getblockchaininfo` |
| Tor connection fails | Verify `tor` service running: `systemctl status tor`; check firewall |
| Dashboard shows stale data | Check SocketIO connection; verify `bitcoind` is running |
| NUT/UPS not detected | Check USB connection; `lsusb` to verify; try `nut-scanner` |
| Nimbus sync stuck | Check available disk space and RAM; Nimbus light client needs ~2GB RAM |

---

## Where to Next

- Enable Lightning Network and open your first payment channel
- Set up BTCPay Server to accept Bitcoin payments for a project
- Connect Electrum desktop wallet to your own Electrum Personal Server
- Run the 🧊 **Air-Gapped Cold Storage Crypto Wallet** for offline signing
- Enable Tor for complete network privacy
- Add UPS protection for production reliability
- Monitor both BTC and ETH from a single dashboard
