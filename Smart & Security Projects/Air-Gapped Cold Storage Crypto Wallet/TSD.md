# Technical Specification Document — Air-Gapped Cold Storage Crypto Wallet

## 1. Scope

### In Scope

- Offline private key generation (BIP-39 mnemonic, physical entropy)
- Hierarchical deterministic wallet derivation (BIP-32/44/84)
- PSBT (BIP-174) parsing, signing, and finalization
- QR code exchange protocol (camera input, display output, chunked encoding)
- Multi-coin support (BTC primary, ETH, LTC)
- Multisig schemes (2-of-3, 3-of-5) with cosigner key exchange via QR
- AES-256-GCM encrypted SD card backups with PBKDF2 key derivation
- E-ink display option (Waveshare 2.13" HAT) for persistent address display
- Boot-time tamper detection (SHA-256 hash manifest verification)
- Physical entropy collection (hardware RNG + camera noise + optional dice)
- Dark-themed Flask + SocketIO local-only web dashboard with auth
- bcrypt authentication with rate limiting and session expiry
- Mock mode for development/testing without hardware
- All features toggled via `.env`
- SQLite for persistence
- Deployment via rsync to `rasp-pi` (192.168.216.90) — pre-air-gap only
- Permanent WiFi/Bluetooth/Ethernet disable scripts

### Out of Scope

- Network connectivity of any kind (the device is permanently air-gapped)
- Blockchain synchronization or transaction broadcasting
- Full node functionality (companion project on a separate device)
- Fiat currency conversion or price tracking
- Exchange API integration
- Cloud backup or remote management
- Hardware Security Module (HSM) integration (future enhancement)
- Lightning Network channel management
- Non-Linux host OS for the Pi
- Commercial licensing or paid features
- Automated trading or portfolio management

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | BIP-39 mnemonic generation (12/24 words) with physical entropy | P0 |
| P0-2 | BIP-32/44/84 HD wallet derivation (BTC primary) | P0 |
| P0-3 | PSBT (BIP-174) parsing and signing | P0 |
| P0-4 | QR code generation (signed TX display on screen) | P0 |
| P0-5 | QR code scanning (unsigned TX from camera) | P0 |
| P0-6 | Wallet management (create, list, select active wallet) | P0 |
| P0-7 | Address generation and display | P0 |
| P0-8 | AES-256 encrypted backup/restore | P0 |
| P0-9 | Web dashboard (dark theme, wallet overview, signing workflow) | P0 |
| P0-10 | Authentication (bcrypt, rate limiting 10/15min, 24h session) | P0 |
| P0-11 | SQLite database (schema, wallets, addresses, signing requests) | P0 |
| P0-12 | Mock mode (simulated camera/display for dev/testing) | P0 |
| P0-13 | WiFi/BT disable script (permanent air gap) | P0 |
| P0-14 | Deploy script (rsync to rasp-pi, pre-air-gap) | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | Multi-coin support (ETH, LTC) | P1 | Separate derivation paths per coin |
| P1-2 | Multisig (2-of-3) | P1 | Cosigner key exchange via QR |
| P1-3 | E-ink display support | P1 | Waveshare 2.13" HAT |
| P1-4 | Boot-time tamper detection | P1 | SHA-256 manifest check |
| P1-5 | Physical entropy (camera noise + dice) | P1 | Enhance HRNG with additional sources |
| P1-6 | Animated/chunked QR for large transactions | P1 | Split QR for TXs > 2953 bytes |
| P1-7 | Multisig (3-of-5) | P1 | Extended multisig scheme |
| P2-1 | BIP-39 passphrase (25th word) | P2 | Additional wallet security layer |
| P2-2 | Watch-only wallet xpub export via QR | P2 | For companion online wallet setup |
| P2-3 | Taproot (BIP-86) derivation | P2 | P2TR address support |
| P2-4 | SLIP-39 Shamir's Secret Sharing | P2 | Split seed into shares |

---

## 3. Database Schema

SQLite with WAL mode enabled. All timestamps stored as ISO-8601 UTC.

### Table: `wallets`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique wallet ID |
| name | TEXT | NOT NULL, UNIQUE | Human-readable wallet name |
| coin | TEXT | NOT NULL, DEFAULT 'BTC' | Cryptocurrency (`BTC`, `ETH`, `LTC`) |
| wallet_type | TEXT | NOT NULL, DEFAULT 'single' | `single` or `multisig` |
| multisig_scheme | TEXT | | `2-of-3`, `3-of-5`, NULL for single-sig |
| derivation_path | TEXT | NOT NULL | HD derivation path (e.g., `m/84'/0'/0'`) |
| encrypted_seed | BLOB | NOT NULL | AES-256-GCM encrypted seed bytes |
| seed_salt | BLOB | NOT NULL | PBKDF2 salt for seed encryption key |
| xpub | TEXT | NOT NULL | Extended public key (for address generation) |
| fingerprint | TEXT | NOT NULL | Master key fingerprint (4 bytes hex) |
| address_index | INTEGER | DEFAULT 0 | Next unused address index |
| is_active | INTEGER | DEFAULT 0 | 1 if this is the currently active wallet |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |
| updated_at | TEXT | NOT NULL | ISO-8601 last modification timestamp |

### Table: `addresses`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique address ID |
| wallet_id | INTEGER | FK → wallets.id, INDEX | Parent wallet reference |
| path | TEXT | NOT NULL | Full derivation path (e.g., `m/84'/0'/0'/0/0`) |
| address | TEXT | NOT NULL, UNIQUE | Derived address string |
| address_type | TEXT | NOT NULL | `receive` or `change` |
| index | INTEGER | NOT NULL | Address index within derivation |
| is_used | INTEGER | DEFAULT 0 | 1 if address has been involved in a signing |
| label | TEXT | | Optional user label |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |

### Table: `transactions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique transaction record ID |
| wallet_id | INTEGER | FK → wallets.id, INDEX | Wallet used for signing |
| txid | TEXT | | Transaction ID (hash, populated after signing) |
| tx_type | TEXT | NOT NULL | `psbt`, `raw`, `multisig_partial` |
| unsigned_data | TEXT | NOT NULL | Base64-encoded unsigned TX/PSBT (as received) |
| signed_data | TEXT | | Base64-encoded signed TX/PSBT (after signing) |
| amount_sat | INTEGER | | Total output amount in satoshis (if parseable) |
| fee_sat | INTEGER | | Transaction fee in satoshis (if parseable) |
| num_inputs | INTEGER | | Number of transaction inputs |
| num_outputs | INTEGER | | Number of transaction outputs |
| status | TEXT | NOT NULL, DEFAULT 'pending' | `pending`, `signed`, `rejected`, `error` |
| error_message | TEXT | | Error details if status is `error` |
| signed_at | TEXT | | ISO-8601 timestamp of signing |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |

### Table: `signing_requests`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique signing request ID |
| transaction_id | INTEGER | FK → transactions.id, INDEX | Associated transaction |
| wallet_id | INTEGER | FK → wallets.id, INDEX | Target wallet for signing |
| qr_data_in | TEXT | NOT NULL | Raw QR data received from camera |
| qr_chunks_in | INTEGER | DEFAULT 1 | Number of QR chunks received |
| qr_data_out | TEXT | | Signed QR data for display |
| qr_chunks_out | INTEGER | | Number of QR chunks for display |
| review_summary | TEXT | | Human-readable TX summary shown to user |
| user_confirmed | INTEGER | DEFAULT 0 | 1 if user confirmed signing |
| status | TEXT | NOT NULL, DEFAULT 'received' | `received`, `reviewed`, `confirmed`, `signed`, `rejected`, `error` |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |
| completed_at | TEXT | | ISO-8601 completion timestamp |

### Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | TEXT | PK | Setting name |
| value | TEXT | | Setting value (JSON-encoded) |
| updated_at | TEXT | NOT NULL | ISO-8601 last update time |

---

## 4. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                Raspberry Pi 4 (AIR-GAPPED — No WiFi/BT/Ethernet)         │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  Physical Entropy │    │  Wallet Engine    │    │  TX Signer       │   │
│  │  ┌────────────┐  │───>│  ┌────────────┐  │    │  ┌────────────┐  │   │
│  │  │ /dev/hwrng │  │    │  │ BIP-39     │  │    │  │ PSBT parse │  │   │
│  │  │ Camera     │  │    │  │ BIP-32     │  │    │  │ Raw TX     │  │   │
│  │  │ noise      │  │    │  │ BIP-44     │  │    │  │ Multisig   │  │   │
│  │  │ Dice rolls │  │    │  │ BIP-84     │  │    │  │ partial    │  │   │
│  │  └────────────┘  │    │  └────────────┘  │    │  └────────────┘  │   │
│  └──────────────────┘    │  ┌────────────┐  │    └────────┬─────────┘   │
│                          │  │ Multi-coin │  │             │             │
│  ┌──────────────────┐    │  │ BTC/ETH/LTC│  │             │             │
│  │  Tamper Detect    │    │  └────────────┘  │             │             │
│  │  SHA-256 hash     │    └────────┬─────────┘             │             │
│  │  check on boot    │             │                       │             │
│  └──────────────────┘    ┌─────────▼───────────────────────▼──────────┐ │
│                          │                SQLite Database               │ │
│  ┌──────────────────┐    │  ┌────────┐ ┌─────────┐ ┌──────────────┐  │ │
│  │  Encrypted Backup │    │  │wallets │ │addresses│ │transactions  │  │ │
│  │  (AES-256-GCM)    │    │  └────────┘ └─────────┘ └──────────────┘  │ │
│  │  PBKDF2 600k iter │    │  ┌────────────────┐ ┌──────────┐          │ │
│  └──────────────────┘    │  │signing_requests │ │settings  │          │ │
│                          │  └────────────────┘ └──────────┘          │ │
│  ┌──────────────────┐    └────────────────────────┬───────────────────┘ │
│  │  QR Handler       │                            │                     │
│  │  ┌────────────┐   │    ┌───────────────────────▼───────────────────┐ │
│  │  │ Camera →   │   │    │  Flask + SocketIO Dashboard (localhost)    │ │
│  │  │ pyzbar     │   │<──>│  - bcrypt auth (rate limit 10/15min)      │ │
│  │  │ decode     │   │    │  - 24h session expiry                      │ │
│  │  ├────────────┤   │    │  - Dark theme, wallet mgmt, signing        │ │
│  │  │ qrcode →   │   │    │  - QR scan & display, backup controls      │ │
│  │  │ Pillow →   │   │    └───────────────────────────────────────────┘ │
│  │  │ display    │   │                                                   │
│  │  └────────────┘   │    ┌──────────────────┐                          │
│  └──────────────────┘    │  Display Manager  │                          │
│                          │  LCD / e-ink HAT  │                          │
│  ┌──────────────────┐    └──────────────────┘                          │
│  │  Multisig Mgr     │                                                   │
│  │  2-of-3 / 3-of-5  │                                                   │
│  │  cosigner QR xchg  │                                                   │
│  └──────────────────┘                                                   │
│                                                                          │
│  ══════════════════════ AIR GAP (NO ELECTRICAL CONNECTION) ════════════  │
│                                                                          │
│  Pi Camera ← reads QR from online device screen                          │
│  LCD/E-ink → displays signed QR for online device camera                 │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Security Threat Model

| Threat | Impact | Likelihood | Mitigation |
|--------|--------|------------|------------|
| Remote key theft via network | Total loss of funds | Impossible | Air gap — WiFi/BT/Ethernet permanently disabled |
| Malware on Pi modifying signing logic | Signed TX sends funds to attacker | Low | Tamper detection (SHA-256 hash on boot), read-only SD option |
| Physical device theft | Funds at risk if seed extracted | Medium | AES-256 encrypted seed, strong passphrase, tamper-evident enclosure |
| Side-channel attack (power/EM analysis) | Key extraction | Very Low | Physical shielding, randomized timing in signing |
| QR code interception (camera recording) | Signed TX intercepted (broadcast by attacker) | Low | Signed TX without private keys is safely broadcastable by anyone |
| Brute-force dashboard login | Unauthorized signing | Low | bcrypt, rate limiting (10/15min), session expiry (24h) |
| Supply chain attack (compromised Pi) | Pre-installed malware | Low | Verify Pi source, hash-check OS image, tamper detection on boot |
| Malicious PSBT (modified outputs) | User signs TX sending to wrong address | Medium | Display TX summary for user review before signing, address verification |
| Entropy weakness (predictable keys) | Key brute-force feasible | Low | Physical entropy (HRNG + camera noise + dice), entropy quality checks |
| Backup passphrase brute-force | Encrypted backup decrypted | Medium | PBKDF2 with 600k iterations, strong passphrase enforcement |
| USB-based attack (malicious peripheral) | Code execution on Pi | Low | No USB data ports used; only power supply connected |
| SD card corruption | Wallet data loss | Medium | Encrypted backups on separate media, backup verification |
| CSRF on signing confirmation | Unauthorized TX signing | Low | CSRF tokens on all forms, signing requires explicit user confirmation |

---

## 6. Tech Stack

| Layer | Technology | Version / Notes |
|-------|-----------|-----------------|
| Language | Python 3.11+ | Type hints throughout |
| Web framework | Flask | 3.x with app factory pattern |
| Real-time | Flask-SocketIO | eventlet async mode |
| Bitcoin core | python-bitcoinlib | Low-level TX construction & signing |
| Bitcoin HD | bitcoinlib | BIP-32/44/84 derivation, PSBT |
| Mnemonic | mnemonic | BIP-39 seed phrase generation |
| QR generation | qrcode + Pillow | PNG rendering for display |
| QR reading | pyzbar | Decode from camera frames |
| Camera | picamera2 | Pi Camera V2 interface |
| Encryption | cryptography | AES-256-GCM, PBKDF2 |
| Auth | bcrypt | Password hashing |
| Config | python-dotenv | `.env` loader |
| Database | SQLite3 | WAL mode, stdlib `sqlite3` |
| Display | Pillow + waveshare driver | LCD framebuffer / e-ink SPI |
| GPIO | RPi.GPIO | Physical confirm button |
| CSS | Custom dark theme | No framework |
| Deployment | rsync + systemd | SSH alias `rasp-pi` (pre-air-gap) |
| Testing | pytest + pytest-cov | Mocking with unittest.mock |

---

## 7. Development Phases

### Phase 1 — Project Foundation & Wallet Engine

**Goal:** Scaffold the project, configure environment loading, set up the database, and build the core wallet engine with BIP-39/32 key generation.

| # | Task | Deliverable |
|---|------|-------------|
| 1.1 | Initialize project structure (dirs, `pyproject.toml`, `requirements.txt`) | Repo skeleton |
| 1.2 | Implement `.env` config loader with dataclass validation | `src/config.py` |
| 1.3 | Implement SQLite database module with schema creation (WAL mode) | `src/database.py` |
| 1.4 | Implement BIP-39 mnemonic generation with physical entropy | `src/wallet.py`, `src/entropy.py` |
| 1.5 | Implement BIP-32/44/84 HD wallet derivation | `src/wallet.py` |
| 1.6 | Implement address generation (bech32/legacy) | `src/wallet.py`, `src/coins.py` |
| 1.7 | Implement mock mode (simulated camera/display) | Mock paths |
| 1.8 | Write unit tests for config, database, wallet, entropy | `tests/` |

### Phase 2 — Transaction Signing & QR Exchange

**Goal:** Build the PSBT signing engine and QR code exchange protocol.

| # | Task | Deliverable |
|---|------|-------------|
| 2.1 | Implement PSBT parser (BIP-174 decode, validate) | `src/signer.py` |
| 2.2 | Implement transaction signing (PSBT and raw TX) | `src/signer.py` |
| 2.3 | Implement QR code generation (signed TX → QR image) | `src/qr_handler.py` |
| 2.4 | Implement QR code scanning (camera → decoded data) | `src/qr_handler.py` |
| 2.5 | Implement chunked QR protocol for large transactions | `src/qr_handler.py` |
| 2.6 | Implement TX review summary for user confirmation | `src/signer.py` |
| 2.7 | Write unit tests for signer, QR handler, chunking | `tests/` |

### Phase 3 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed local dashboard with wallet management and signing workflow.

| # | Task | Deliverable |
|---|------|-------------|
| 3.1 | Implement Flask app factory with SocketIO | `src/app.py` |
| 3.2 | Implement bcrypt auth with rate limiting (10/15min) and session (24h) | `src/auth.py` |
| 3.3 | Create dark-theme base template and CSS | `templates/`, `static/` |
| 3.4 | Build login page | `templates/login.html` |
| 3.5 | Build dashboard page (wallet overview, recent signing activity) | `templates/dashboard.html` |
| 3.6 | Build wallet management page (create, list, select active) | `templates/wallets.html` |
| 3.7 | Build signing workflow page (QR scan → review → sign → display) | `templates/sign.html` |
| 3.8 | Implement SocketIO real-time signing status | `src/app.py`, `static/js/` |
| 3.9 | Build settings panel (feature toggles, display config) | `templates/settings.html` |
| 3.10 | Write API endpoint and auth tests | `tests/` |

### Phase 4 — Multi-Coin, Multisig & Backup

**Goal:** Add multi-coin derivation, multisig support, and encrypted backup system.

| # | Task | Deliverable |
|---|------|-------------|
| 4.1 | Implement ETH key derivation and address generation | `src/coins.py` |
| 4.2 | Implement LTC key derivation and address generation | `src/coins.py` |
| 4.3 | Implement multisig scheme manager (2-of-3) | `src/multisig.py` |
| 4.4 | Implement cosigner public key exchange via QR | `src/multisig.py`, `src/qr_handler.py` |
| 4.5 | Implement multisig PSBT partial signing | `src/multisig.py`, `src/signer.py` |
| 4.6 | Implement AES-256-GCM encrypted backup | `src/backup.py` |
| 4.7 | Implement backup restore with passphrase verification | `src/backup.py` |
| 4.8 | Build backup management UI page | `templates/backup.html` |
| 4.9 | Write multi-coin, multisig, and backup tests | `tests/` |

### Phase 5 — Display, Tamper Detection & Entropy

**Goal:** Add e-ink display support, boot-time tamper detection, and enhanced physical entropy.

| # | Task | Deliverable |
|---|------|-------------|
| 5.1 | Implement display manager (LCD framebuffer abstraction) | `src/display.py` |
| 5.2 | Implement e-ink HAT driver integration | `src/display.py` |
| 5.3 | Implement boot-time tamper detection (SHA-256 manifest) | `src/tamper.py` |
| 5.4 | Implement camera noise entropy source | `src/entropy.py` |
| 5.5 | Implement dice roll entropy input | `src/entropy.py` |
| 5.6 | Implement entropy quality validation | `src/entropy.py` |
| 5.7 | Write display, tamper, and entropy tests | `tests/` |

### Phase 6 — Deployment & Documentation

**Goal:** Finalize deploy pipeline, air-gap scripts, and all documentation.

| # | Task | Deliverable |
|---|------|-------------|
| 6.1 | Create deploy script (rsync to rasp-pi, pre-air-gap) | `deploy/deploy_to_pi.sh` |
| 6.2 | Create networking disable script (permanent air gap) | `scripts/disable_networking.sh` |
| 6.3 | Create OS dependency installer script | `scripts/install_deps.sh` |
| 6.4 | Write systemd service unit file | docs / README |
| 6.5 | Write air gap verification guide | `docs/air_gap_guide.md` |
| 6.6 | Write QR protocol specification | `docs/qr_protocol.md` |
| 6.7 | Write backup & disaster recovery guide | `docs/backup_recovery.md` |
| 6.8 | Final integration testing on Raspberry Pi hardware | Test report |
| 6.9 | Update README with final instructions | `README.md` |

---

## 8. `.env.default` Reference

```ini
# ─── Flask & Security ──────────────────────────────────────
SECRET_KEY=change-me-to-a-random-string
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # bcrypt hash of your password

# ─── Database ──────────────────────────────────────────────
DB_PATH=data/cold_wallet.db

# ─── BIP-39 Mnemonic ──────────────────────────────────────
ENABLE_BIP39=true
MNEMONIC_STRENGTH=256
# Strength: 128=12 words, 160=15, 192=18, 224=21, 256=24

# ─── BIP-32/44/84 Derivation ──────────────────────────────
ENABLE_BIP32=true
DERIVATION_PATHS=m/44'/0'/0',m/84'/0'/0'

# ─── PSBT (BIP-174) ──────────────────────────────────────
ENABLE_PSBT=true

# ─── Multi-Coin ──────────────────────────────────────────
ENABLE_MULTI_COIN=true
DEFAULT_COIN=BTC
# Supported: BTC, ETH, LTC

# ─── Multisig ────────────────────────────────────────────
ENABLE_MULTISIG=false
MULTISIG_SCHEME=2-of-3
# Supported: 2-of-3, 3-of-5

# ─── QR Code Exchange ────────────────────────────────────
ENABLE_QR_EXCHANGE=true
QR_ERROR_CORRECTION=M
# Error correction: L=7%, M=15%, Q=25%, H=30%
QR_MAX_CHUNK_SIZE=2953

# ─── Camera ──────────────────────────────────────────────
ENABLE_CAMERA=true
CAMERA_RESOLUTION=1280x720

# ─── Encrypted Backup ────────────────────────────────────
ENABLE_ENCRYPTED_BACKUP=true
BACKUP_DIR=data/backups/

# ─── E-Ink Display ───────────────────────────────────────
ENABLE_EINK_DISPLAY=false
EINK_MODEL=waveshare_2in13

# ─── LCD Display ─────────────────────────────────────────
ENABLE_LCD_DISPLAY=true

# ─── Tamper Detection ────────────────────────────────────
ENABLE_TAMPER_DETECTION=true
TAMPER_HASH_FILE=data/integrity.sha256

# ─── Physical Entropy ────────────────────────────────────
ENABLE_PHYSICAL_ENTROPY=true
ENTROPY_CAMERA_FRAMES=10

# ─── Web Dashboard ───────────────────────────────────────
ENABLE_WEB_DASHBOARD=true
DASHBOARD_HOST=127.0.0.1
# CRITICAL: Must be 127.0.0.1 (localhost only) — device is air-gapped
DASHBOARD_PORT=5000
SESSION_EXPIRY_HOURS=24
RATE_LIMIT=10/15min

# ─── Development ─────────────────────────────────────────
MOCK_MODE=false
LOG_LEVEL=INFO
```

---

## 9. Deliverables

| # | Deliverable | Format | Notes |
|---|-------------|--------|-------|
| 1 | Wallet engine (BIP-39/32/44/84) | Python module | `src/wallet.py` |
| 2 | Transaction signer (PSBT + raw TX) | Python module | `src/signer.py` |
| 3 | QR code handler (encode/decode/chunked) | Python module | `src/qr_handler.py` |
| 4 | Physical entropy collector | Python module | `src/entropy.py` |
| 5 | Multi-coin support (BTC/ETH/LTC) | Python module | `src/coins.py` |
| 6 | Multisig scheme manager | Python module | `src/multisig.py` |
| 7 | Encrypted backup/restore | Python module | `src/backup.py` |
| 8 | Display manager (LCD/e-ink) | Python module | `src/display.py` |
| 9 | Tamper detection | Python module | `src/tamper.py` |
| 10 | SQLite database layer | Python module | `src/database.py` |
| 11 | Flask + SocketIO local dashboard | Python + HTML/JS/CSS | `src/app.py`, `templates/`, `static/` |
| 12 | bcrypt auth with rate limiting | Python module | `src/auth.py` |
| 13 | Configuration loader | Python module | `src/config.py` |
| 14 | WiFi/BT disable script | Bash | `scripts/disable_networking.sh` |
| 15 | OS dependency installer | Bash | `scripts/install_deps.sh` |
| 16 | Deploy script (pre-air-gap) | Bash | `deploy/deploy_to_pi.sh` |
| 17 | systemd service unit | INI | Documented in README |
| 18 | Test suite (≥80% coverage) | pytest | `tests/` |
| 19 | Air gap verification guide | Markdown | `docs/air_gap_guide.md` |
| 20 | QR protocol specification | Markdown | `docs/qr_protocol.md` |
| 21 | Backup & recovery guide | Markdown | `docs/backup_recovery.md` |
| 22 | README & TSD | Markdown | Root-level docs |
