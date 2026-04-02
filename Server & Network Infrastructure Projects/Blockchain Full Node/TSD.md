# Technical Specification Document — Blockchain Full Node

## 1. Scope

### In Scope

- Bitcoin Core full validation node (unpruned ~600GB blockchain)
- Initial Block Download (IBD) optimization for Raspberry Pi
- Lightning Network daemon (LND) with REST/gRPC APIs
- Electrum Personal Server for private wallet verification
- BTCPay Server self-hosted payment processing
- BTC RPC Explorer self-hosted block explorer
- Tor routing for Bitcoin P2P traffic and optional hidden service
- Mempool visualization with fee estimation
- UPS monitoring and graceful shutdown via NUT
- Ethereum Nimbus light client (dual-node BTC + ETH)
- Dark-themed Flask + SocketIO monitoring dashboard
- bcrypt authentication with rate limiting and session expiry
- SQLite for monitoring data persistence
- All features toggled via `.env`
- Mock mode for development/testing without services
- Deployment via rsync to `rasp-pi` (192.168.216.90)

### Out of Scope

- Private key generation or storage (companion Cold Wallet project)
- Transaction signing (handled by air-gapped Cold Wallet)
- Bitcoin mining
- Altcoin full nodes (only BTC full + ETH light)
- Cloud deployment or VPS hosting
- GUI wallet (use Electrum, Sparrow, or BlueWallet)
- Automated trading or portfolio management
- Commercial licensing or paid features

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | Bitcoin Core full validation node with IBD | P0 |
| P0-2 | SSD mount, format, and fstab persistence | P0 |
| P0-3 | Bitcoin Core RPC client (Python wrapper) | P0 |
| P0-4 | Flask monitoring dashboard (sync %, block height, peers) | P0 |
| P0-5 | Mempool size and fee rate display | P0 |
| P0-6 | Disk usage, CPU temp, RAM monitoring | P0 |
| P0-7 | SocketIO live updates (no page refresh) | P0 |
| P0-8 | bcrypt auth, rate limiting (10/15min), 24h session | P0 |
| P0-9 | SQLite monitoring database | P0 |
| P0-10 | Dark theme web UI | P0 |
| P0-11 | `.env` toggleable features | P0 |
| P0-12 | Mock mode (dev/test without running services) | P0 |
| P0-13 | Deploy script (rsync to rasp-pi) | P0 |
| P0-14 | bitcoin.conf template generation from `.env` | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | Lightning Network (LND) | P1 | Channel management, balance display |
| P1-2 | Electrum Personal Server | P1 | Private wallet verification |
| P1-3 | Tor routing | P1 | P2P privacy, hidden service |
| P1-4 | BTC RPC Explorer | P1 | Self-hosted block explorer |
| P1-5 | UPS protection (NUT) | P1 | Graceful shutdown on power loss |
| P1-6 | Mempool fee histogram | P1 | Visual fee distribution chart |
| P1-7 | BTCPay Server | P2 | Payment processing |
| P1-8 | Ethereum Nimbus light client | P2 | Dual-node BTC + ETH |
| P2-1 | Historical sync data charts | P2 | Track IBD progress over time |
| P2-2 | Email/Telegram alerts | P2 | Node down, disk full, UPS battery low |
| P2-3 | Prometheus/Grafana export | P2 | Advanced monitoring stack |

---

## 3. Database Schema

SQLite with WAL mode enabled. All timestamps stored as ISO-8601 UTC.

### Table: `node_status`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| chain | TEXT | NOT NULL, DEFAULT 'main' | Bitcoin network (`main`, `test`, `regtest`) |
| block_height | INTEGER | NOT NULL | Current best block height |
| block_hash | TEXT | NOT NULL | Current best block hash |
| verification_progress | REAL | NOT NULL | IBD progress (0.0 → 1.0) |
| chain_size_bytes | INTEGER | | Blockchain size on disk in bytes |
| difficulty | REAL | | Current mining difficulty |
| peer_count | INTEGER | NOT NULL | Connected peer count |
| mempool_tx_count | INTEGER | | Number of transactions in mempool |
| mempool_bytes | INTEGER | | Mempool size in bytes |
| mempool_min_fee | REAL | | Minimum fee rate in mempool (sat/vB) |
| network_hash_ps | REAL | | Estimated network hash rate (hashes/sec) |
| is_ibd | INTEGER | DEFAULT 0 | 1 if still in Initial Block Download |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp of this snapshot |

### Table: `system_metrics`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| cpu_percent | REAL | | CPU usage percentage |
| cpu_temp_c | REAL | | CPU temperature in Celsius |
| ram_used_mb | REAL | | RAM used in MB |
| ram_total_mb | REAL | | Total RAM in MB |
| disk_used_gb | REAL | | SSD used space in GB |
| disk_total_gb | REAL | | SSD total space in GB |
| disk_percent | REAL | | SSD usage percentage |
| swap_used_mb | REAL | | Swap used in MB |
| uptime_seconds | INTEGER | | System uptime in seconds |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `lightning_status`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| identity_pubkey | TEXT | | LND node public key |
| alias | TEXT | | LND node alias |
| num_active_channels | INTEGER | DEFAULT 0 | Open and active channels |
| num_pending_channels | INTEGER | DEFAULT 0 | Pending channel opens/closes |
| num_peers | INTEGER | DEFAULT 0 | Connected Lightning peers |
| total_capacity_sat | INTEGER | DEFAULT 0 | Total channel capacity (satoshis) |
| local_balance_sat | INTEGER | DEFAULT 0 | Local balance across all channels |
| remote_balance_sat | INTEGER | DEFAULT 0 | Remote balance across all channels |
| synced_to_chain | INTEGER | DEFAULT 0 | 1 if LND is synced to Bitcoin chain |
| synced_to_graph | INTEGER | DEFAULT 0 | 1 if LND has synced channel graph |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `mempool_snapshots`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| tx_count | INTEGER | NOT NULL | Total transactions in mempool |
| total_bytes | INTEGER | NOT NULL | Total mempool size in bytes |
| total_fee_btc | REAL | | Total fees in BTC |
| min_fee_rate | REAL | | Minimum fee rate (sat/vB) |
| fee_histogram | TEXT | | JSON array of [fee_rate, vsize] buckets |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `eth_status`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| client | TEXT | DEFAULT 'nimbus' | Ethereum client name |
| head_slot | INTEGER | | Current head slot |
| sync_distance | INTEGER | | Slots behind head |
| is_syncing | INTEGER | DEFAULT 1 | 1 if still syncing |
| peer_count | INTEGER | DEFAULT 0 | Connected Ethereum peers |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `ups_status`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| ups_name | TEXT | NOT NULL | NUT UPS device name |
| status | TEXT | | UPS status (`OL`, `OB`, `LB`, etc.) |
| battery_charge_pct | REAL | | Battery charge percentage |
| battery_runtime_sec | INTEGER | | Estimated runtime in seconds |
| input_voltage | REAL | | Input voltage (V) |
| load_pct | REAL | | UPS load percentage |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | TEXT | PK | Setting name |
| value | TEXT | | Setting value (JSON-encoded) |
| updated_at | TEXT | NOT NULL | ISO-8601 last update time |

---

## 4. Environment Configuration (.env.default)

```bash
###############################################################################
# BLOCKCHAIN FULL NODE — ENVIRONMENT CONFIGURATION
# Copy to .env and customize before deployment
# All features are toggleable via ENABLE_* flags
###############################################################################

# ===========================================================================
# CORE SETTINGS
# ===========================================================================

# Flask session secret — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=CHANGE_ME

# Dashboard authentication
ADMIN_USERNAME=admin
# Generate: python3 -c "import bcrypt; print(bcrypt.hashpw(b'changeme', bcrypt.gensalt()).decode())"
ADMIN_PASSWORD_HASH=CHANGE_ME

# SQLite database path
DB_PATH=data/fullnode.db

# Timezone
TZ=UTC

# Pi IP / hostname
PI_HOST=192.168.216.90
PI_SSH_ALIAS=rasp-pi

# ===========================================================================
# STORAGE
# ===========================================================================

# Primary SSD mount point
SSD_MOUNT=/mnt/ssd
SSD_DEVICE=/dev/sda1
SSD_FILESYSTEM=ext4

# ===========================================================================
# BITCOIN CORE
# ===========================================================================

ENABLE_BITCOIN_CORE=true

# Data directory (on SSD)
BITCOIN_DATADIR=/mnt/ssd/bitcoin

# RPC credentials — generate password: openssl rand -base64 32
BITCOIN_RPC_USER=bitcoinrpc
BITCOIN_RPC_PASSWORD=CHANGE_ME_USE_openssl_rand_base64_32
BITCOIN_RPC_HOST=127.0.0.1
BITCOIN_RPC_PORT=8332

# P2P network
BITCOIN_P2P_PORT=8333
BITCOIN_MAX_CONNECTIONS=40

# Performance tuning
# dbcache: RAM allocated for IBD (MB). Higher = faster IBD. 1024 safe for 8GB Pi.
BITCOIN_DBCACHE=1024
BITCOIN_MAXMEMPOOL=300

# Prune: 0 = full node (keep all blocks), >550 = prune to N MB
BITCOIN_PRUNE=0

# Block-only mode during IBD (faster sync, no mempool relay)
BITCOIN_BLOCKSONLY_IBD=true

# ===========================================================================
# LIGHTNING NETWORK (LND)
# ===========================================================================

ENABLE_LND=false

LND_DIR=/mnt/ssd/lnd
LND_ALIAS=mynode-lightning
LND_REST_PORT=8080
LND_GRPC_PORT=10009
LND_P2P_PORT=9735

# Autopilot — automatic channel management
LND_AUTOPILOT=false
LND_AUTOPILOT_MAX_CHANNELS=5
LND_AUTOPILOT_ALLOCATION=0.6

# Watchtower — monitor channels while offline
LND_WATCHTOWER=true

# ===========================================================================
# ELECTRUM PERSONAL SERVER
# ===========================================================================

ENABLE_ELECTRUM_SERVER=false

ELECTRUM_RPC_PORT=50002
# Comma-separated xpub/zpub keys for wallet monitoring
ELECTRUM_WALLETS=

# ===========================================================================
# BTCPAY SERVER
# ===========================================================================

ENABLE_BTCPAY=false

BTCPAY_PORT=23000
BTCPAY_DOMAIN=btcpay.local
BTCPAY_LN_ENABLED=true

# ===========================================================================
# BTC RPC EXPLORER
# ===========================================================================

ENABLE_BTC_RPC_EXPLORER=false

BTC_RPC_EXPLORER_PORT=3002
# Privacy mode — no external API calls
BTC_RPC_EXPLORER_PRIVACY=true

# ===========================================================================
# TOR ROUTING
# ===========================================================================

ENABLE_TOR=false

TOR_SOCKS_PORT=9050
TOR_CONTROL_PORT=9051
TOR_CONTROL_PASSWORD=CHANGE_ME

# Expose node as Tor hidden service (.onion address)
TOR_HIDDEN_SERVICE=false

# Route ALL Bitcoin traffic through Tor (proxy=127.0.0.1:9050)
TOR_PROXY_ALL=false
# Or only use Tor for onion peers (onlynet=onion)
TOR_ONLYNET_ONION=false

# ===========================================================================
# MEMPOOL VISUALIZATION
# ===========================================================================

ENABLE_MEMPOOL_DASHBOARD=true

# Refresh interval for mempool data (seconds)
MEMPOOL_REFRESH_INTERVAL=30
# Max historical snapshots to keep in DB
MEMPOOL_MAX_SNAPSHOTS=2880

# ===========================================================================
# UPS PROTECTION (NUT)
# ===========================================================================

ENABLE_UPS=false

UPS_NAME=myups
UPS_DRIVER=usbhid-ups
UPS_PORT=auto

# Battery percentage to trigger graceful shutdown
UPS_SHUTDOWN_BATTERY_PCT=20
# Shutdown command: stops bitcoind, then powers off
UPS_SHUTDOWN_CMD="bitcoin-cli -datadir=/mnt/ssd/bitcoin stop && sudo shutdown -h now"

# ===========================================================================
# ETHEREUM NIMBUS LIGHT CLIENT
# ===========================================================================

ENABLE_NIMBUS=false

NIMBUS_DATADIR=/mnt/ssd/nimbus
NIMBUS_REST_PORT=5052
NIMBUS_NETWORK=mainnet
# Light client mode (minimal disk + RAM usage)
NIMBUS_LIGHT_CLIENT=true

# ===========================================================================
# FLASK MONITORING DASHBOARD
# ===========================================================================

ENABLE_WEB_DASHBOARD=true

DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000
SESSION_EXPIRY_HOURS=24
RATE_LIMIT=10/15min

# SocketIO update interval (seconds)
SOCKETIO_UPDATE_INTERVAL=10

# ===========================================================================
# DEVELOPMENT / TESTING
# ===========================================================================

# Mock mode — simulate all services without real Bitcoin Core / LND
MOCK_MODE=false
LOG_LEVEL=INFO

# Docker log rotation (for containerized services)
DOCKER_LOG_MAX_SIZE=10m
DOCKER_LOG_MAX_FILE=3
```

---

## 5. Bitcoin Core Configuration Template

Generated from `.env` values by `src/config.py`:

```ini
# bitcoin.conf — auto-generated from .env
# Data directory: /mnt/ssd/bitcoin

# Network
server=1
listen=1
port=8333
maxconnections=40

# RPC
rpcuser=bitcoinrpc
rpcpassword=<from .env>
rpcbind=127.0.0.1
rpcport=8332
rpcallowip=127.0.0.1

# Performance
dbcache=1024
maxmempool=300

# Pruning (0 = no prune = full node)
prune=0

# Tor (if ENABLE_TOR=true)
# proxy=127.0.0.1:9050
# listen=1
# bind=127.0.0.1

# ZMQ (for LND, if ENABLE_LND=true)
# zmqpubrawblock=tcp://127.0.0.1:28332
# zmqpubrawtx=tcp://127.0.0.1:28333

# Logging
printtoconsole=0
debuglogfile=/mnt/ssd/bitcoin/debug.log
shrinkdebugfile=1
```

---

## 6. LND Configuration Template

```ini
# lnd.conf — auto-generated from .env (when ENABLE_LND=true)

[Application Options]
alias=mynode-lightning
debuglevel=info
maxpendingchannels=3
listen=0.0.0.0:9735
restlisten=0.0.0.0:8080
rpclisten=0.0.0.0:10009

[Bitcoin]
bitcoin.active=1
bitcoin.mainnet=1
bitcoin.node=bitcoind

[Bitcoind]
bitcoind.rpchost=127.0.0.1:8332
bitcoind.rpcuser=bitcoinrpc
bitcoind.rpcpass=<from .env>
bitcoind.zmqpubrawblock=tcp://127.0.0.1:28332
bitcoind.zmqpubrawtx=tcp://127.0.0.1:28333

[tor]
# tor.active=true           (if ENABLE_TOR=true)
# tor.socks=127.0.0.1:9050

[autopilot]
# autopilot.active=true     (if LND_AUTOPILOT=true)
# autopilot.maxchannels=5
# autopilot.allocation=0.6

[wtclient]
wtclient.active=true
```

---

## 7. Tor Configuration Template

```ini
# torrc additions (when ENABLE_TOR=true)

SOCKSPort 9050
ControlPort 9051
HashedControlPassword <generated from TOR_CONTROL_PASSWORD>

# Hidden service for Bitcoin P2P (if TOR_HIDDEN_SERVICE=true)
# HiddenServiceDir /var/lib/tor/bitcoin-service/
# HiddenServicePort 8333 127.0.0.1:8333

# Hidden service for LND P2P (if ENABLE_LND=true && TOR_HIDDEN_SERVICE=true)
# HiddenServiceDir /var/lib/tor/lnd-service/
# HiddenServicePort 9735 127.0.0.1:9735
```

---

## 8. API Endpoints (Flask Dashboard)

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Login page |
| POST | `/login` | Authenticate (username + password) |
| GET | `/logout` | End session |

### Dashboard Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard (redirect to login if unauthenticated) |
| GET | `/mempool` | Mempool visualization page |
| GET | `/lightning` | Lightning Network status (if LND enabled) |
| GET | `/explorer` | Block/TX explorer interface (if enabled) |
| GET | `/settings` | Runtime settings panel |

### REST API (JSON)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Full node status (block height, sync, peers) |
| GET | `/api/mempool` | Current mempool stats |
| GET | `/api/mempool/history` | Historical mempool snapshots |
| GET | `/api/system` | System metrics (CPU, RAM, disk, temp) |
| GET | `/api/lightning` | LND status (if enabled) |
| GET | `/api/ethereum` | Nimbus status (if enabled) |
| GET | `/api/ups` | UPS status (if enabled) |
| GET | `/api/tor` | Tor connection status (if enabled) |

### SocketIO Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `connect` | Client → Server | Authenticate session |
| `node_status` | Server → Client | `{ block_height, sync_pct, peers, mempool_size }` |
| `system_metrics` | Server → Client | `{ cpu, temp, ram, disk }` |
| `mempool_update` | Server → Client | `{ tx_count, bytes, fee_histogram }` |
| `lightning_update` | Server → Client | `{ channels, balance, peers }` (if enabled) |
| `ups_update` | Server → Client | `{ battery_pct, runtime, status }` (if enabled) |

---

## 9. Deployment Architecture

```
Developer Machine                    Raspberry Pi (rasp-pi / 192.168.216.90)
┌─────────────────┐                 ┌──────────────────────────────────────┐
│                 │    rsync/SSH     │  /home/pi/fullnode/                  │
│  Source code    │ ───────────────> │    src/, templates/, static/         │
│  .env.example   │                 │    .env (local config)               │
│  config/*.tmpl  │                 │                                      │
└─────────────────┘                 │  /mnt/ssd/                           │
                                    │    bitcoin/    (~600GB blockchain)   │
                                    │    lnd/        (LN data, if enabled) │
                                    │    nimbus/     (ETH data, if enabled)│
                                    │                                      │
                                    │  Services:                           │
                                    │    bitcoind    (systemd)             │
                                    │    lnd         (systemd, optional)   │
                                    │    nimbus      (systemd, optional)   │
                                    │    tor         (systemd, optional)   │
                                    │    nut-server  (systemd, optional)   │
                                    │    flask app   (systemd)             │
                                    └──────────────────────────────────────┘
```

---

## 10. Security Requirements

| Area | Requirement |
|------|-------------|
| RPC Credentials | Generated with `openssl rand -base64 32`; never defaults |
| Dashboard Auth | bcrypt hash, rate limit 10/15min, 24h session expiry |
| RPC Binding | Bitcoin Core RPC bound to `127.0.0.1` only |
| Firewall | `ufw allow 22,8333,5000/tcp`; deny all others by default |
| Tor | Optional but recommended; hides node from ISP-level surveillance |
| UPS | Recommended; unclean shutdown during IBD can corrupt chainstate |
| No Private Keys | This node stores **zero** private keys — signing is done on the 🧊 Cold Wallet |
| Session Security | `SECRET_KEY` unique per deployment; `HttpOnly` + `SameSite` cookies |
| CSRF Protection | All POST forms include CSRF tokens |
