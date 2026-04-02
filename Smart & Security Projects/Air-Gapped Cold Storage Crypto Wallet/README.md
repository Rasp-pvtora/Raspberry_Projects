# Air-Gapped Cold Storage Crypto Wallet

A Raspberry Pi that **NEVER touches a network** — WiFi and Bluetooth are permanently disabled at the hardware level. Generates private keys offline, signs transactions via QR code exchange (camera reads unsigned TX, screen displays signed TX as QR). The air gap ensures private keys can never be stolen remotely. Features BIP-39 mnemonic generation, BIP-32/44/84 hierarchical derivation, multi-coin support (BTC, ETH, LTC), multisig schemes, PSBT (BIP-174) workflow, AES-256 encrypted SD backups, tamper detection on boot, and physical entropy from hardware RNG + camera noise. Managed through a local dark-themed Flask + SocketIO dashboard accessible only from the Pi's own display.

---

**If you find this project useful, consider supporting development:**

**BTC:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Libraries & Dependencies](#libraries--dependencies)
- [Quickstart](#quickstart)
- [Environment Configuration](#environment-configuration)
- [System Overview](#system-overview)
- [Features](#features)
  - [Offline Key Generation](#offline-key-generation)
  - [QR Code Exchange Protocol](#qr-code-exchange-protocol)
  - [PSBT Support (BIP-174)](#psbt-support-bip-174)
  - [BIP-39 Mnemonic](#bip-39-mnemonic)
  - [BIP-32/44/84 Derivation](#bip-324484-derivation)
  - [Multi-Coin Support](#multi-coin-support)
  - [Multisig Schemes](#multisig-schemes)
  - [Encrypted SD Backup (AES-256)](#encrypted-sd-backup-aes-256)
  - [E-Ink Display Option](#e-ink-display-option)
  - [Tamper Detection](#tamper-detection)
  - [Physical Entropy](#physical-entropy)
  - [Web Dashboard (Local Only)](#web-dashboard-local-only)
- [Authentication](#authentication)
- [Companion Project — Blockchain Full Node](#companion-project--blockchain-full-node)
- [Deployment](#deployment)
- [Running the Service](#running-the-service)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
Air-Gapped Cold Storage Crypto Wallet/
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
│   ├── wallet.py               # Wallet creation & management (BIP-39/32/44/84)
│   ├── signer.py               # Transaction signing engine (PSBT, raw TX)
│   ├── qr_handler.py           # QR encode/decode (camera input, display output)
│   ├── entropy.py              # Physical entropy collector (HRNG + camera noise)
│   ├── backup.py               # AES-256 encrypted SD card backup/restore
│   ├── multisig.py             # Multisig scheme manager (2-of-3, 3-of-5)
│   ├── coins.py                # Multi-coin support (BTC, ETH, LTC derivation)
│   ├── tamper.py               # Boot-time integrity hash verification
│   ├── display.py              # Display manager (LCD / e-ink HAT abstraction)
│   ├── database.py             # SQLite DB models & helpers
│   ├── auth.py                 # bcrypt auth & session management
│   ├── config.py               # .env loader & config dataclass
│   └── utils.py                # Shared utilities
├── templates/
│   ├── base.html               # Dark theme layout
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main dashboard
│   ├── wallets.html            # Wallet management page
│   ├── sign.html               # Transaction signing page
│   ├── backup.html             # Backup & restore page
│   ├── qr_scan.html            # QR camera scan page
│   └── settings.html           # Runtime settings panel
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme styles
│   └── js/
│       ├── dashboard.js        # SocketIO client & live status
│       ├── qr.js               # QR display & camera interaction
│       └── sign.js             # Signing workflow UI logic
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures & mock mode helpers
│   ├── test_wallet.py          # Key generation & derivation tests
│   ├── test_signer.py          # PSBT & raw TX signing tests
│   ├── test_qr_handler.py      # QR encode/decode tests
│   ├── test_entropy.py         # Entropy source tests
│   ├── test_backup.py          # Encrypted backup/restore tests
│   ├── test_multisig.py        # Multisig scheme tests
│   ├── test_coins.py           # Multi-coin derivation tests
│   ├── test_tamper.py          # Integrity verification tests
│   ├── test_auth.py            # Auth & session tests
│   ├── test_api.py             # Dashboard API endpoint tests
│   └── test_database.py        # Database CRUD tests
├── deploy/
│   └── deploy_to_pi.sh         # rsync deploy script (rasp-pi)
├── scripts/
│   ├── disable_networking.sh   # Permanently disable WiFi/BT
│   ├── install_deps.sh         # OS-level dependency installer
│   └── generate_password_hash.sh # Helper to generate bcrypt hash
└── docs/
    ├── air_gap_guide.md        # Air gap verification checklist
    ├── qr_protocol.md          # QR exchange protocol specification
    └── backup_recovery.md      # Backup & disaster recovery guide
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 | Yes | WiFi/Bluetooth **permanently disabled** (air-gapped) |
| Pi Camera Module V2 | Yes | Reads unsigned TX QR codes from online device |
| LCD Display (3.5" or 5") | Yes | Displays signed TX QR codes, wallet info, and dashboard |
| MicroSD card (16GB+) | Yes | For OS, encrypted wallet data, and backups |
| Power supply (5V/3A) | Yes | Standalone power only — never USB to another device |
| E-Ink HAT (optional) | No | Waveshare 2.13" e-ink for persistent address/QR display |
| Physical dice (optional) | No | Additional manual entropy source for key generation |

> **CRITICAL:** The Pi 4's WiFi and Bluetooth must be **permanently disabled** via `dtoverlay=disable-wifi` and `dtoverlay=disable-bt` in `/boot/config.txt`. The only data path in/out is QR codes displayed on screen and read by camera. No USB data cables, no network cables, no wireless signals.

---

## Budget

| Item | Estimated Cost |
|---|---|
| Raspberry Pi 4 (already owned) | $0 |
| Pi Camera Module V2 | ~$25–30 |
| LCD Display (3.5"–5") | ~$15–25 |
| E-Ink HAT (optional) | ~$15–20 |
| **Total** | **~$40–57** |

*(Assumes you already have a Raspberry Pi 4 and SD card.)*

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| Flask | Local-only web dashboard framework |
| Flask-SocketIO | Real-time WebSocket for signing status updates |
| python-dotenv | `.env` configuration loading |
| bcrypt | Password hashing for dashboard auth |
| bitcoinlib | Bitcoin key management, HD wallets, PSBT |
| python-bitcoinlib | Low-level Bitcoin protocol & transaction signing |
| mnemonic | BIP-39 mnemonic phrase generation |
| qrcode | QR code generation for signed transactions |
| pyzbar | QR code reading from camera images |
| Pillow | Image processing for camera and QR rendering |
| cryptography | AES-256 encryption for SD card backups |
| picamera2 | Pi Camera V2 interface |
| RPi.GPIO | GPIO for physical button (confirm signing) |

---

## Quickstart

```bash
# 1. SSH into the Pi (BEFORE disabling networking permanently)
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/cold-wallet && cd ~/cold-wallet

# 3. Install OS-level dependencies
sudo bash scripts/install_deps.sh

# 4. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
nano .env              # Set credentials, toggle features

# 6. PERMANENTLY disable WiFi and Bluetooth
sudo bash scripts/disable_networking.sh
# Adds dtoverlay=disable-wifi and dtoverlay=disable-bt to /boot/config.txt
# REBOOT REQUIRED — after this, the Pi is permanently air-gapped

# 7. Reboot into air-gapped mode
sudo reboot

# 8. After reboot — access via local display + keyboard only
# Dashboard runs on localhost:5000 (local display only)
sudo .venv/bin/python -m src.app
```

> **After Step 6, the Pi will never connect to any network again.** All future interaction is through the local display, keyboard, and QR camera exchange.

---

## Environment Configuration

All features are toggleable via `.env`. Copy `.env.example` and adjust:

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(generate)* | Flask session secret key |
| `ADMIN_USERNAME` | `admin` | Dashboard login username |
| `ADMIN_PASSWORD_HASH` | *(bcrypt hash)* | bcrypt-hashed admin password |
| `DB_PATH` | `data/cold_wallet.db` | SQLite database file path |
| `ENABLE_BIP39` | `true` | Toggle BIP-39 mnemonic generation |
| `MNEMONIC_STRENGTH` | `256` | Mnemonic entropy bits (128/160/192/224/256) |
| `ENABLE_BIP32` | `true` | Toggle BIP-32 HD wallet derivation |
| `DERIVATION_PATHS` | `m/44'/0'/0',m/84'/0'/0'` | Comma-separated derivation paths |
| `ENABLE_PSBT` | `true` | Toggle PSBT (BIP-174) support |
| `ENABLE_MULTI_COIN` | `true` | Toggle multi-coin support (BTC, ETH, LTC) |
| `DEFAULT_COIN` | `BTC` | Default coin for new wallets |
| `ENABLE_MULTISIG` | `false` | Toggle multisig schemes |
| `MULTISIG_SCHEME` | `2-of-3` | Default multisig scheme (`2-of-3`, `3-of-5`) |
| `ENABLE_QR_EXCHANGE` | `true` | Toggle QR code exchange protocol |
| `QR_ERROR_CORRECTION` | `M` | QR error correction level (L/M/Q/H) |
| `QR_MAX_CHUNK_SIZE` | `2953` | Max bytes per QR code (split large TXs) |
| `ENABLE_CAMERA` | `true` | Toggle Pi Camera for QR scanning |
| `CAMERA_RESOLUTION` | `1280x720` | Camera capture resolution |
| `ENABLE_ENCRYPTED_BACKUP` | `true` | Toggle AES-256 encrypted SD backups |
| `BACKUP_DIR` | `data/backups/` | Encrypted backup storage directory |
| `ENABLE_EINK_DISPLAY` | `false` | Toggle e-ink display output |
| `EINK_MODEL` | `waveshare_2in13` | E-ink HAT model identifier |
| `ENABLE_LCD_DISPLAY` | `true` | Toggle LCD display output |
| `ENABLE_TAMPER_DETECTION` | `true` | Toggle boot-time integrity hash check |
| `TAMPER_HASH_FILE` | `data/integrity.sha256` | Path to integrity hash manifest |
| `ENABLE_PHYSICAL_ENTROPY` | `true` | Toggle hardware RNG + camera noise entropy |
| `ENTROPY_CAMERA_FRAMES` | `10` | Number of camera frames for noise entropy |
| `ENABLE_WEB_DASHBOARD` | `true` | Toggle local web dashboard |
| `DASHBOARD_HOST` | `127.0.0.1` | Dashboard bind address (**localhost only**) |
| `DASHBOARD_PORT` | `5000` | Dashboard bind port |
| `SESSION_EXPIRY_HOURS` | `24` | Session expiry in hours |
| `RATE_LIMIT` | `10/15min` | Login rate limit (attempts/window) |
| `MOCK_MODE` | `false` | Run without real hardware (dev/test) |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                Raspberry Pi 4 (AIR-GAPPED — No WiFi/BT/Ethernet)         │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  Physical         │    │  Wallet Engine    │    │  Transaction     │   │
│  │  Entropy          │───>│                   │    │  Signer          │   │
│  │  (HRNG + camera   │    │  BIP-39 mnemonic  │    │  (PSBT / raw TX) │   │
│  │   noise + dice)   │    │  BIP-32/44/84     │    │                  │   │
│  └──────────────────┘    │  derivation        │    └────────┬─────────┘   │
│                          │  Multi-coin keys   │             │             │
│  ┌──────────────────┐    └────────┬───────────┘             │             │
│  │  Tamper Detect    │            │                         │             │
│  │  (SHA-256 hash    │    ┌───────▼───────────┐    ┌────────▼─────────┐  │
│  │   check on boot)  │    │  SQLite Database   │    │  QR Handler      │  │
│  └──────────────────┘    │                     │    │                  │  │
│                          │  wallets, addresses │    │  Camera → decode │  │
│  ┌──────────────────┐    │  transactions       │    │  unsigned TX     │  │
│  │  Encrypted        │    │  signing_requests   │    │                  │  │
│  │  Backup           │    │  settings           │    │  Display → show  │  │
│  │  (AES-256)        │    └────────┬───────────┘    │  signed TX QR    │  │
│  └──────────────────┘             │                 └────────┬─────────┘  │
│                                   │                          │             │
│  ┌──────────────────┐    ┌────────▼──────────────────────────▼─────────┐  │
│  │  Display Manager  │    │  Flask + SocketIO Dashboard (localhost)     │  │
│  │  (LCD / e-ink)    │<──>│  - bcrypt auth (rate limit 10/15min)       │  │
│  │                   │    │  - 24h session expiry                       │  │
│  └──────────────────┘    │  - Dark theme, wallet management            │  │
│                          │  - QR scan & display, signing workflow       │  │
│  ┌──────────────────┐    └─────────────────────────────────────────────┘  │
│  │  Multisig         │                                                    │
│  │  (2-of-3, 3-of-5) │                                                   │
│  └──────────────────┘                                                    │
│                                                                          │
│         ┌──────────┐                               ┌──────────┐         │
│         │ Pi Camera │  ← reads unsigned TX QR ←    │ LCD/E-ink │         │
│         │ (input)   │                               │ (output)  │         │
│         └──────────┘                               └──────────┘         │
│              ▲                                          │                │
│              │              AIR GAP                     ▼                │
├──────────────┼──────────────────────────────────────────┼────────────────┤
│              │         (NO electrical connection)       │                │
│              │                                          │                │
│         ┌────┴─────┐                               ┌───┴──────┐        │
│         │ Phone/PC  │  shows unsigned TX QR         │ Phone/PC  │        │
│         │ screen    │                               │ camera    │        │
│         └──────────┘                               └──────────┘        │
│                          Online Device                                   │
│                    (wallet app / full node)                               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Offline Key Generation

All private keys are generated entirely offline on the air-gapped Pi. Keys never exist on any networked device.

- BIP-39 mnemonic seed phrase (12/15/18/21/24 words)
- Configurable entropy strength (128–256 bits)
- Physical entropy mixing from hardware RNG, camera sensor noise, and optional dice rolls
- Keys are derived, stored encrypted, and never transmitted electronically
- Toggle via `ENABLE_BIP39`, `ENABLE_PHYSICAL_ENTROPY`

### QR Code Exchange Protocol

The only data path between the air-gapped Pi and the outside world is visual — QR codes on screens read by cameras.

**Workflow:**
1. Online device constructs an unsigned transaction (or PSBT) and displays it as a QR code
2. Pi Camera reads the QR code from the online device's screen
3. Cold wallet parses, validates, and signs the transaction offline
4. Pi display shows the signed transaction as a QR code
5. Online device's camera reads the signed QR from the Pi's display
6. Online device broadcasts the signed transaction to the network

- Supports animated QR codes for large transactions (chunked encoding)
- Configurable error correction level (`QR_ERROR_CORRECTION`)
- Maximum chunk size configurable (`QR_MAX_CHUNK_SIZE`)
- Toggle via `ENABLE_QR_EXCHANGE`

### PSBT Support (BIP-174)

Full Partially Signed Bitcoin Transaction support for interoperability with hardware wallets and watch-only wallet software.

- Parse PSBT from QR input (base64 or binary)
- Validate PSBT structure and input references
- Sign PSBT inputs matching wallet keys
- Output signed/finalized PSBT as QR code
- Compatible with Electrum, Sparrow, BlueWallet, Specter
- Toggle via `ENABLE_PSBT`

### BIP-39 Mnemonic

Industry-standard mnemonic seed phrase generation and recovery.

- Generate 12/15/18/21/24 word seed phrases
- Checksum validation on import
- Optional passphrase (25th word) for additional security
- Seed phrase displayed once on screen — never stored in plaintext
- Backup via encrypted SD export
- Toggle via `ENABLE_BIP39`

### BIP-32/44/84 Derivation

Hierarchical deterministic (HD) wallet derivation following Bitcoin standards.

- **BIP-32:** Base HD wallet key derivation
- **BIP-44:** Multi-account hierarchy (`m/44'/coin'/account'/change/index`)
- **BIP-84:** Native SegWit (bech32) addresses (`m/84'/0'/0'/0/0`)
- Configurable derivation paths per coin
- Automatic address generation from derived keys
- Toggle via `ENABLE_BIP32`

### Multi-Coin Support

Support for multiple cryptocurrencies from a single seed phrase.

| Coin | Derivation Path | Address Format | Status |
|---|---|---|---|
| **BTC** (Bitcoin) | `m/84'/0'/0'` | bech32 (bc1...) | Primary |
| **ETH** (Ethereum) | `m/44'/60'/0'` | 0x... | Supported |
| **LTC** (Litecoin) | `m/84'/2'/0'` | ltc1... | Supported |

- Default coin configurable via `DEFAULT_COIN`
- Toggle via `ENABLE_MULTI_COIN`

### Multisig Schemes

Multi-signature wallet support for enhanced security — require M-of-N cosigners to authorize a transaction.

- **2-of-3:** Require 2 of 3 keys to sign (recommended for personal use)
- **3-of-5:** Require 3 of 5 keys to sign (recommended for organizational use)
- Exchange cosigner public keys via QR code
- Build and partially sign multisig PSBTs
- Combine partial signatures from multiple cold wallets
- Toggle via `ENABLE_MULTISIG`, configurable via `MULTISIG_SCHEME`

### Encrypted SD Backup (AES-256)

Secure backup of wallet data to the SD card or external media, encrypted at rest.

- AES-256-GCM encryption with key derived from user passphrase (PBKDF2, 600k iterations)
- Backup includes: encrypted seed, derived keys metadata, wallet config, address index
- Restore from backup with passphrase verification
- Backup integrity validated via HMAC
- Toggle via `ENABLE_ENCRYPTED_BACKUP`

### E-Ink Display Option

Optional e-ink HAT for persistent display of receive addresses and QR codes without power consumption.

- Displays current receive address QR code persistently (no power needed to maintain image)
- Ideal for donation addresses or receive-only display
- Supported models: Waveshare 2.13" e-ink HAT
- Falls back to LCD display when e-ink disabled
- Toggle via `ENABLE_EINK_DISPLAY`

### Tamper Detection

Boot-time integrity verification ensures the cold wallet software has not been modified.

- SHA-256 hash manifest generated at initial setup
- On every boot: recalculate hashes of all `src/` files and compare to manifest
- Alert on screen if any file has been modified (potential tampering)
- Log tamper events to database
- Toggle via `ENABLE_TAMPER_DETECTION`

### Physical Entropy

Enhanced randomness for key generation using multiple physical entropy sources.

- **/dev/hwrng** — hardware random number generator on the Pi's SoC
- **Camera noise** — capture N frames from Pi Camera in darkness, extract sensor noise
- **Dice rolls** — optional manual dice entry for user-verifiable entropy
- All sources XOR'd with Python's `os.urandom()` for defense in depth
- Toggle via `ENABLE_PHYSICAL_ENTROPY`

### Web Dashboard (Local Only)

Dark-themed management interface accessible **only from localhost** on the Pi's own display. Never exposed to any network.

- Wallet overview (balances, addresses, derivation paths)
- Transaction signing workflow with QR preview
- Camera live view for QR scanning
- Backup management (create, verify, restore)
- Settings panel for feature configuration
- Real-time signing status via SocketIO
- Bound to `127.0.0.1` — unreachable from any network (because there is none)

---

## Authentication

The local web dashboard is protected with bcrypt-hashed password authentication:

- Admin credentials configured via `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` in `.env`
- Generate a password hash: `python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpass', bcrypt.gensalt()).decode())"`
- Login rate limiting: **10 attempts per 15 minutes** per IP (`RATE_LIMIT`)
- Session cookies with **24-hour expiry** (`SESSION_EXPIRY_HOURS`)
- Sessions invalidated on password change or server restart
- All dashboard routes require authentication except `/login`

---

## Companion Project — Blockchain Full Node

> ### 🛡️ How This Relates to a Blockchain Full Node
>
> The **Blockchain Full Node** project validates transactions and maintains a copy of the blockchain. The **Cold Storage Crypto Wallet** (this project) generates keys and signs transactions offline.
>
> **They complement each other but MUST run on separate devices:**
>
> | | Cold Wallet (this project) | Full Node |
> |---|---|---|
> | **Network** | **NEVER connected** — air-gapped, WiFi/BT disabled | Always connected — syncs blockchain 24/7 |
> | **Purpose** | Generate keys, sign transactions offline | Validate transactions, broadcast to network |
> | **Data flow** | QR codes only (camera ↔ display) | TCP/IP (Bitcoin P2P protocol, port 8333) |
> | **Security model** | Keys never leave the device | No private keys stored |
>
> **Typical workflow:**
> 1. **Full Node** constructs an unsigned transaction (or PSBT) using your watch-only wallet
> 2. Full Node displays the unsigned TX as a QR code on its screen
> 3. **Cold Wallet** camera reads the QR → signs the TX offline → displays signed QR
> 4. Full Node camera reads the signed QR → broadcasts the signed TX to the Bitcoin network
>
> **Why separate devices?** If the cold wallet ever touches a network, the air gap is broken and private keys are exposed to remote attack. The full node must be online to sync and broadcast. These are fundamentally incompatible security requirements — combining them on one device defeats the entire purpose of cold storage.

---

## Deployment

> **Note:** Deployment via rsync is done **BEFORE** disabling networking. After the air gap is established, all updates must be transferred via SD card swap or QR-based code patching.

Use the deploy script to push code to the Pi (pre-air-gap only):

```bash
# From development machine (BEFORE disabling networking)
bash deploy/deploy_to_pi.sh
```

The deploy script (`deploy_to_pi.sh`):
```bash
#!/usr/bin/env bash
set -euo pipefail

PI_HOST="rasp-pi"                              # SSH alias -> pi@192.168.216.90
REMOTE_DIR="/home/pi/cold-wallet"

echo "[*] Deploying to ${PI_HOST}:${REMOTE_DIR}"
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
    --exclude '.git' --exclude 'data/' \
    ./ "${PI_HOST}:${REMOTE_DIR}/"

ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
echo "[✓] Deploy complete."
echo "[!] Remember: after disabling networking, this is the LAST remote deploy possible."
```

---

## Running the Service

### Manual

```bash
# On the Pi (local keyboard + display only after air-gap)
cd ~/cold-wallet
source .venv/bin/activate
sudo .venv/bin/python -m src.app
# Dashboard at http://127.0.0.1:5000 (local display only)
```

### systemd Service

Create `/etc/systemd/system/cold-wallet.service`:

```ini
[Unit]
Description=Air-Gapped Cold Storage Crypto Wallet
After=local-fs.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/pi/cold-wallet
EnvironmentFile=/home/pi/cold-wallet/.env
ExecStartPre=/bin/bash scripts/disable_networking.sh
ExecStart=/home/pi/cold-wallet/.venv/bin/python -m src.app
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable cold-wallet
sudo systemctl start cold-wallet
sudo journalctl -u cold-wallet -f    # Follow logs
```

---

## Security Notes

- **Air gap is sacred** — WiFi and Bluetooth are **permanently disabled** at the firmware level. Never re-enable them. Never connect an Ethernet cable. Never connect USB data cables to other computers.
- **QR codes are the only data path** — all transaction data flows through camera ↔ display. No electronic data channel exists.
- **Seed phrase security** — the mnemonic is displayed once and never stored in plaintext. Encrypted backups only.
- **Run as root** — camera and display access require root privileges. Dashboard is localhost-only.
- **Rotate `SECRET_KEY`** regularly and never store `.env` in version control.
- **Password hashing** — only bcrypt hashes are stored; plaintext passwords are never persisted.
- **Rate limiting** — protects against brute-force login attempts on the local dashboard.
- **Tamper detection** — the integrity hash manifest catches unauthorized modifications to source files on boot.
- **Physical security** — the Pi stores private keys; keep it in a secure location. Consider a tamper-evident enclosure.
- **Encrypted backups** — wallet backups are AES-256-GCM encrypted. Store backup media separately from the Pi in a secure location.
- **Verify the air gap** — after setup, run `ip link show` and confirm no `wlan0` or `eth0` interfaces are UP. Check with `rfkill list` that all radios are hard-blocked.

---

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| WiFi/BT still active after disable script | Overlays not applied | Verify `/boot/config.txt` has `dtoverlay=disable-wifi` and `dtoverlay=disable-bt`; reboot |
| Camera not detected | Camera interface disabled | Run `sudo raspi-config` → Interface Options → Camera → Enable; reboot |
| QR code not scanning | Low resolution or poor lighting | Increase `CAMERA_RESOLUTION`; ensure adequate lighting on the source QR |
| QR too large for single code | Transaction exceeds `QR_MAX_CHUNK_SIZE` | Animated/chunked QR will split automatically; ensure online device supports chunked reading |
| Tamper alert on boot | Source files modified | If intentional (update), regenerate hash manifest; if unexpected, investigate |
| Backup restore fails | Wrong passphrase or corrupt backup | Verify passphrase; try alternate backup copy; check HMAC integrity |
| E-ink display blank | Wrong model configured | Verify `EINK_MODEL` matches your HAT; check SPI is enabled |
| `ModuleNotFoundError` | Missing Python dependency | Activate venv and run `pip install -r requirements.txt` |
| Dashboard not loading | Web dashboard disabled or wrong port | Check `ENABLE_WEB_DASHBOARD=true` and `DASHBOARD_PORT` in `.env` |
| Key derivation error | Unsupported derivation path | Verify `DERIVATION_PATHS` format matches BIP-44/84 standard |
| Multisig cosigner QR rejected | Incompatible key format | Ensure cosigner exports xpub in the expected format (see `docs/qr_protocol.md`) |
| Signing fails on PSBT | Missing UTXO data in PSBT | Ensure the online wallet includes full UTXO information in the PSBT |

---

## Where to Next

- **Taproot support** — BIP-86 derivation for P2TR (pay-to-taproot) addresses
- **Shamir's Secret Sharing** — split seed phrase into N shares requiring K to reconstruct (SLIP-39)
- **NFC signing** — use NFC tap to transfer signed transactions (short-range, still air-gapped-adjacent)
- **Timelock transactions** — sign transactions with `nLockTime` for scheduled broadcasting
- **Lightning Network** — channel state signing for Lightning-compatible cold storage
- **Multi-language mnemonic** — BIP-39 wordlists in multiple languages
- **Hardware security module** — ATECC608A integration for tamper-resistant key storage
- **Passphrase manager** — manage multiple wallet passphrases (25th word) securely
- **Watch-only wallet export** — export xpub/zpub via QR for companion watch-only wallets
- **Offline firmware updates** — verify and apply Pi firmware updates via SD card without network
