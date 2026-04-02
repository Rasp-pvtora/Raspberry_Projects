# Task Tracker
## Blockchain Full Node

---

## Phase 1: Hardware & OS Preparation
- [ ] Flash Raspberry Pi OS 64-bit (Bookworm) to SD card
- [ ] Enable SSH, set hostname, configure Ethernet
- [ ] Boot Pi and connect via `ssh rasp-pi` (192.168.216.90)
- [ ] Run `sudo apt update && sudo apt upgrade -y`
- [ ] Connect 2TB NVMe SSD via USB 3.0 enclosure and verify with `lsblk`
- [ ] Format SSD: `sudo mkfs.ext4 /dev/sda1`
- [ ] Mount SSD at `/mnt/ssd` and add to `/etc/fstab`
- [ ] Set SSD ownership: `sudo chown -R $USER:$USER /mnt/ssd`
- [ ] Create directory structure on SSD (`bitcoin/`, `lnd/`, `nimbus/`)
- [ ] Configure swap file (4GB recommended for Pi 4)
- [ ] Verify SSD I/O performance: `sudo hdparm -Tt /dev/sda`

## Phase 2: Bitcoin Core Installation
- [ ] Download Bitcoin Core binary (aarch64) from bitcoincore.org
- [ ] Verify download signatures (SHA256SUMS + GPG)
- [ ] Extract and install to `/usr/local/bin/`
- [ ] Verify installation: `bitcoind --version`
- [ ] Create Bitcoin data directory: `mkdir -p /mnt/ssd/bitcoin`
- [ ] Copy `.env.example` to `.env` and configure RPC credentials
- [ ] Generate RPC password: `openssl rand -base64 32`
- [ ] Generate `bitcoin.conf` from `.env` template
- [ ] Start bitcoind: `bitcoind -datadir=/mnt/ssd/bitcoin -daemon`
- [ ] Verify RPC is working: `bitcoin-cli getblockchaininfo`

## Phase 3: Initial Block Download (IBD)
- [ ] Confirm Ethernet connection (not WiFi)
- [ ] Set `BITCOIN_DBCACHE=1024` (or higher if 8GB Pi)
- [ ] Optionally enable `BITCOIN_BLOCKSONLY_IBD=true` for faster sync
- [ ] Start IBD and monitor progress: `bitcoin-cli getblockchaininfo | jq '.verificationprogress'`
- [ ] Monitor disk usage: `df -h /mnt/ssd`
- [ ] Monitor RAM/swap: `free -h`
- [ ] Monitor CPU temperature: `vcgencmd measure_temp`
- [ ] Wait for IBD to complete (5–10 days on Pi 4 with Ethernet)
- [ ] Verify `verificationprogress` reaches ~1.0
- [ ] Check peer connections: `bitcoin-cli getpeerinfo | jq '.[].addr'`

## Phase 4: Python Environment & Dashboard Setup
- [ ] Install Python 3 and venv: `sudo apt install python3-venv python3-pip`
- [ ] Create venv: `python3 -m venv .venv && source .venv/bin/activate`
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Initialize SQLite database
- [ ] Generate bcrypt password hash for dashboard admin
- [ ] Set `ADMIN_PASSWORD_HASH` in `.env`
- [ ] Generate Flask `SECRET_KEY` and set in `.env`
- [ ] Start dashboard: `python -m src.app`
- [ ] Access dashboard at `http://192.168.216.90:5000`
- [ ] Login and verify dark theme
- [ ] Verify SocketIO live updates (block height, sync %, peers)
- [ ] Verify mempool display
- [ ] Verify system metrics (CPU, RAM, disk, temp)

## Phase 5: Bitcoin Core systemd Service
- [ ] Create `/etc/systemd/system/bitcoind.service`
- [ ] Configure `ExecStart`, `ExecStop`, `User`, `DataDirectory`
- [ ] Enable and start: `sudo systemctl enable --now bitcoind`
- [ ] Verify service status: `sudo systemctl status bitcoind`
- [ ] Test restart: `sudo systemctl restart bitcoind`
- [ ] Check logs: `journalctl -u bitcoind -f`

## Phase 6: Dashboard systemd Service
- [ ] Create `/etc/systemd/system/fullnode-dashboard.service`
- [ ] Configure `ExecStart` with venv Python path
- [ ] Enable and start: `sudo systemctl enable --now fullnode-dashboard`
- [ ] Verify dashboard auto-starts on boot
- [ ] Test service restart

## Phase 7: Lightning Network — LND (ENABLE_LND=true)
- [ ] Ensure Bitcoin Core is fully synced
- [ ] Enable ZMQ in `bitcoin.conf` (`zmqpubrawblock`, `zmqpubrawtx`)
- [ ] Restart bitcoind
- [ ] Download LND binary (aarch64) and verify signatures
- [ ] Install to `/usr/local/bin/`
- [ ] Create LND data directory: `mkdir -p /mnt/ssd/lnd`
- [ ] Generate `lnd.conf` from `.env` template
- [ ] Start LND: `lnd --configfile=/mnt/ssd/lnd/lnd.conf &`
- [ ] Create LND wallet: `lncli create`
- [ ] Unlock wallet: `lncli unlock`
- [ ] Wait for LND to sync to chain and graph
- [ ] Verify on dashboard: Lightning status section appears
- [ ] Open test channel (optional)
- [ ] Create systemd service for LND

## Phase 8: Electrum Personal Server (ENABLE_ELECTRUM_SERVER=true)
- [ ] Install Electrum Personal Server
- [ ] Configure with xpub/zpub from cold wallet (exported via QR)
- [ ] Set `ELECTRUM_WALLETS` in `.env`
- [ ] Start Electrum server
- [ ] Connect Electrum desktop wallet to `192.168.216.90:50002`
- [ ] Verify transaction history loads from own node
- [ ] Test watch-only wallet balance display
- [ ] Create systemd service

## Phase 9: BTCPay Server (ENABLE_BTCPAY=true)
- [ ] Install BTCPay Server (Docker or manual)
- [ ] Configure to use local Bitcoin Core RPC
- [ ] Set `BTCPAY_PORT` and `BTCPAY_DOMAIN` in `.env`
- [ ] Enable LND integration (if LND enabled)
- [ ] Access BTCPay admin panel
- [ ] Create test store and invoice
- [ ] Verify invoice payment detection
- [ ] Create systemd service

## Phase 10: BTC RPC Explorer (ENABLE_BTC_RPC_EXPLORER=true)
- [ ] Install BTC RPC Explorer (Node.js)
- [ ] Configure to use local Bitcoin Core RPC
- [ ] Enable privacy mode (`BTC_RPC_EXPLORER_PRIVACY=true`)
- [ ] Set `BTC_RPC_EXPLORER_PORT` in `.env`
- [ ] Access at `http://192.168.216.90:3002`
- [ ] Test block, transaction, and address lookups
- [ ] Verify no external API calls are made
- [ ] Create systemd service

## Phase 11: Tor Routing (ENABLE_TOR=true)
- [ ] Install Tor: `sudo apt install tor`
- [ ] Configure `torrc` from template
- [ ] Generate hashed control password: `tor --hash-password <password>`
- [ ] Start Tor service: `sudo systemctl enable --now tor`
- [ ] Add `proxy=127.0.0.1:9050` to `bitcoin.conf`
- [ ] Restart bitcoind
- [ ] Verify Tor peers: `bitcoin-cli getpeerinfo | jq '.[].network'`
- [ ] Optionally set up hidden service
- [ ] Record `.onion` address from `/var/lib/tor/bitcoin-service/hostname`
- [ ] Verify hidden service is reachable
- [ ] Update dashboard Tor status display

## Phase 12: UPS Protection (ENABLE_UPS=true)
- [ ] Connect USB UPS to Pi
- [ ] Install NUT: `sudo apt install nut`
- [ ] Run `nut-scanner` to detect UPS
- [ ] Configure `ups.conf`, `upsmon.conf` from templates
- [ ] Start NUT services: `sudo systemctl enable --now nut-server nut-monitor`
- [ ] Verify UPS detection: `upsc myups`
- [ ] Test dashboard UPS display (battery %, runtime, load)
- [ ] Configure shutdown threshold in `.env`
- [ ] Test graceful shutdown: unplug power and verify `bitcoind stop` runs
- [ ] Verify blockchain DB integrity after UPS shutdown

## Phase 13: Ethereum Nimbus Light Client (ENABLE_NIMBUS=true)
- [ ] Download Nimbus binary (aarch64)
- [ ] Create data directory: `mkdir -p /mnt/ssd/nimbus`
- [ ] Start Nimbus in light client mode
- [ ] Verify REST API: `curl http://localhost:5052/eth/v1/node/syncing`
- [ ] Verify dashboard ETH status display
- [ ] Monitor resource usage (Nimbus should use <2GB RAM)
- [ ] Create systemd service

## Phase 14: Mempool Visualization (ENABLE_MEMPOOL_DASHBOARD=true)
- [ ] Verify `getrawmempool verbose` works in bitcoin-cli
- [ ] Implement fee histogram collection in `src/mempool.py`
- [ ] Verify SocketIO mempool updates on dashboard
- [ ] Test fee estimation display
- [ ] Configure `MEMPOOL_REFRESH_INTERVAL` in `.env`
- [ ] Verify historical mempool snapshots in SQLite
- [ ] Test mempool chart rendering (JavaScript)

## Phase 15: Testing & Validation
- [ ] Run all Python tests: `pytest tests/`
- [ ] Test mock mode: `MOCK_MODE=true python -m src.app`
- [ ] Verify all `.env` toggles work (enable/disable each feature)
- [ ] Test dashboard with only Bitcoin Core (everything else disabled)
- [ ] Test dashboard with all features enabled
- [ ] Stress test: monitor dashboard during heavy mempool activity
- [ ] Benchmark SSD I/O: `sudo hdparm -Tt /dev/sda`
- [ ] Test system recovery after power loss (with UPS)
- [ ] Test system recovery after power loss (without UPS)
- [ ] Verify SocketIO reconnection after network hiccup

## Phase 16: Cold Wallet Integration Testing
- [ ] Set up watch-only wallet via Electrum Personal Server
- [ ] Construct unsigned PSBT on full node
- [ ] Display unsigned TX as QR code
- [ ] Sign TX on 🧊 Air-Gapped Cold Storage Crypto Wallet
- [ ] Read signed QR back on full node
- [ ] Broadcast signed transaction via full node
- [ ] Verify transaction appears in mempool and gets confirmed
- [ ] Document end-to-end workflow in `docs/cold_wallet_workflow.md`

## Phase 17: Production Hardening
- [ ] Change all default passwords (RPC, dashboard, Tor control)
- [ ] Bind Bitcoin RPC to localhost only
- [ ] Configure firewall (ufw): `sudo ufw allow 22,8333,5000/tcp && sudo ufw enable`
- [ ] Enable unattended security updates
- [ ] Set up log rotation for all services
- [ ] Document admin credentials securely (offline)
- [ ] Test full system reboot and verify all services auto-start
- [ ] Plan SSD health monitoring (`smartctl`)
- [ ] Create system recovery documentation

---

## Notes
- IBD takes 5–10 days on Pi 4 over Ethernet; do not use WiFi for IBD
- Pi 4 (8GB) is the minimum recommended; Pi 5 dramatically speeds up IBD
- UPS is strongly recommended — unclean shutdown during IBD can corrupt chainstate
- After IBD, the node stays synced incrementally (~1-2 MB per block every ~10 min)
- Bitcoin blockchain grows ~60GB/year; 2TB SSD provides years of headroom
- LND requires Bitcoin Core to be fully synced before starting
- Nimbus light client is experimental; monitor resource usage
- Pair with 🧊 Air-Gapped Cold Storage Crypto Wallet for complete financial sovereignty
