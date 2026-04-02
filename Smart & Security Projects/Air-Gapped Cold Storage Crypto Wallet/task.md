# Task List — Air-Gapped Cold Storage Crypto Wallet

## Phase 1 — Project Foundation & Wallet Engine

- [ ] **1.1 Initialize project structure**
  - [ ] Create directory tree (`src/`, `templates/`, `static/css/`, `static/js/`, `tests/`, `deploy/`, `scripts/`, `docs/`, `data/`, `data/backups/`)
  - [ ] Create `pyproject.toml` with project metadata
  - [ ] Create `requirements.txt` with all dependencies
  - [ ] Create `.env.example` with all variables and defaults
  - [ ] Create `src/__init__.py`
  - [ ] Create `tests/__init__.py` and `tests/conftest.py`

- [ ] **1.2 Implement configuration loader**
  - [ ] Create `src/config.py` with dataclass for all `.env` variables
  - [ ] Load and validate `.env` using `python-dotenv`
  - [ ] Type conversion for int, float, bool values
  - [ ] Parse `DERIVATION_PATHS` comma-separated list
  - [ ] Parse `CAMERA_RESOLUTION` into width/height tuple
  - [ ] Defaults for all optional settings
  - [ ] Feature-toggle helper method (`is_enabled("feature_name")`)

- [ ] **1.3 Implement SQLite database module**
  - [ ] Create `src/database.py` with connection manager
  - [ ] Enable WAL mode on connection
  - [ ] Create `wallets` table schema
  - [ ] Create `addresses` table schema
  - [ ] Create `transactions` table schema
  - [ ] Create `signing_requests` table schema
  - [ ] Create `settings` table schema
  - [ ] Implement `init_db()` to create all tables
  - [ ] Implement CRUD helpers for each table
  - [ ] Implement parameterized queries for all DB operations

- [ ] **1.4 Implement physical entropy collector**
  - [ ] Create `src/entropy.py`
  - [ ] Implement `collect_hrng_entropy(num_bytes)` — read from `/dev/hwrng`
  - [ ] Implement `collect_camera_entropy(frames)` — capture N frames, extract noise
  - [ ] Implement `collect_dice_entropy(rolls)` — accept manual dice roll input
  - [ ] Implement `mix_entropy(*sources)` — XOR all sources with `os.urandom()`
  - [ ] Implement `validate_entropy(data)` — basic randomness quality check
  - [ ] Toggle via `ENABLE_PHYSICAL_ENTROPY`
  - [ ] Fallback to `os.urandom()` when physical sources unavailable

- [ ] **1.5 Implement BIP-39 mnemonic generation**
  - [ ] Create `src/wallet.py`
  - [ ] Implement `generate_mnemonic(strength, entropy_bytes)` — create seed phrase
  - [ ] Implement `validate_mnemonic(words)` — checksum verification
  - [ ] Implement `mnemonic_to_seed(words, passphrase)` — derive seed bytes
  - [ ] Support 12/15/18/21/24 word lengths (128/160/192/224/256 bit entropy)
  - [ ] Integrate physical entropy from `src/entropy.py`
  - [ ] Toggle via `ENABLE_BIP39`

- [ ] **1.6 Implement BIP-32/44/84 HD wallet derivation**
  - [ ] Implement `derive_master_key(seed)` — master private/public key pair
  - [ ] Implement `derive_child_key(parent, path)` — BIP-32 child derivation
  - [ ] Implement `derive_wallet(seed, derivation_path)` — full path derivation
  - [ ] Support BIP-44 paths (`m/44'/coin'/account'/change/index`)
  - [ ] Support BIP-84 paths (`m/84'/coin'/account'/change/index`)
  - [ ] Generate extended public key (xpub/zpub) for watch-only export
  - [ ] Extract master key fingerprint
  - [ ] Toggle via `ENABLE_BIP32`

- [ ] **1.7 Implement address generation**
  - [ ] Create `src/coins.py` with coin-specific address derivation
  - [ ] BTC: P2WPKH (bech32 bc1...) from BIP-84 derivation
  - [ ] BTC: P2PKH (legacy 1...) from BIP-44 derivation
  - [ ] Implement `generate_addresses(wallet, count, address_type)` — batch generation
  - [ ] Store generated addresses in `addresses` table
  - [ ] Track address index for gap-limit compliance

- [ ] **1.8 Implement mock mode**
  - [ ] Add mock camera class (returns test QR image)
  - [ ] Add mock display class (logs output instead of rendering)
  - [ ] Add mock entropy (deterministic seed for reproducible tests)
  - [ ] Activate via `MOCK_MODE=true` in config
  - [ ] Allow full dashboard testing without hardware

- [ ] **1.9 Write Phase 1 tests**
  - [ ] Test config loader (valid `.env`, missing values, type conversion, derivation path parsing)
  - [ ] Test database schema creation and CRUD operations for all 5 tables
  - [ ] Test entropy collection (mocked `/dev/hwrng`, camera, dice)
  - [ ] Test entropy mixing and validation
  - [ ] Test BIP-39 mnemonic generation and validation
  - [ ] Test mnemonic-to-seed derivation
  - [ ] Test BIP-32/44/84 key derivation against known test vectors
  - [ ] Test address generation (BTC bech32, legacy)
  - [ ] Test mock mode output

---

## Phase 2 — Transaction Signing & QR Exchange

- [ ] **2.1 Implement PSBT parser**
  - [ ] Create `src/signer.py`
  - [ ] Implement `parse_psbt(data)` — decode BIP-174 PSBT from base64/binary
  - [ ] Validate PSBT structure (magic bytes, key-value pairs, global map)
  - [ ] Extract input UTXOs, output addresses, amounts, and fees
  - [ ] Identify which inputs match wallet keys (by derivation path or scriptPubKey)
  - [ ] Toggle via `ENABLE_PSBT`

- [ ] **2.2 Implement transaction signing**
  - [ ] Implement `sign_psbt(psbt, wallet)` — sign matching inputs, return updated PSBT
  - [ ] Implement `sign_raw_tx(tx_hex, wallet, input_info)` — sign raw transaction
  - [ ] Implement `finalize_psbt(psbt)` — finalize fully-signed PSBT
  - [ ] Compute and populate TXID after signing
  - [ ] Record signing event in `transactions` table
  - [ ] Support SegWit (P2WPKH) and legacy (P2PKH) signing

- [ ] **2.3 Implement TX review summary**
  - [ ] Implement `generate_review(psbt_or_tx)` — human-readable summary
  - [ ] Display: number of inputs, total input amount
  - [ ] Display: each output address and amount
  - [ ] Display: calculated fee
  - [ ] Display: change output identification
  - [ ] Require user confirmation before signing proceeds

- [ ] **2.4 Implement QR code generation**
  - [ ] Create `src/qr_handler.py`
  - [ ] Implement `encode_to_qr(data, error_correction)` — generate QR image (PIL Image)
  - [ ] Implement `render_qr_to_display(qr_image, display)` — show on LCD/e-ink
  - [ ] Configurable error correction level from `QR_ERROR_CORRECTION`
  - [ ] Optimize QR version selection for data size

- [ ] **2.5 Implement QR code scanning**
  - [ ] Implement `scan_qr(camera)` — capture frame, decode with pyzbar
  - [ ] Implement `continuous_scan(camera, timeout)` — scan until QR found or timeout
  - [ ] Support multiple QR code formats (alphanumeric, binary, base64)
  - [ ] Return decoded data and metadata (format, error correction, version)

- [ ] **2.6 Implement chunked QR protocol**
  - [ ] Implement `chunk_data(data, max_size)` — split large TX into chunks
  - [ ] Implement `encode_chunked_qr(chunks)` — generate animated QR sequence
  - [ ] Implement `decode_chunked_qr(scanner)` — reassemble from multiple scans
  - [ ] Header format: `chunk_index/total_chunks:data`
  - [ ] Track received chunks and display progress
  - [ ] Validate reassembled data integrity (checksum)

- [ ] **2.7 Write Phase 2 tests**
  - [ ] Test PSBT parsing (valid PSBT, malformed, missing fields)
  - [ ] Test transaction signing against known test vectors
  - [ ] Test PSBT finalization
  - [ ] Test TX review summary generation
  - [ ] Test QR encoding (single code, various data sizes)
  - [ ] Test QR decoding (mocked camera frames with embedded QR)
  - [ ] Test chunked protocol (split, reassemble, integrity check)
  - [ ] Test signing request lifecycle (received → reviewed → confirmed → signed)

---

## Phase 3 — Web Dashboard & Authentication

- [ ] **3.1 Implement Flask app factory**
  - [ ] Create `src/app.py` with `create_app()` factory
  - [ ] Initialize Flask-SocketIO with eventlet
  - [ ] Register blueprints/routes
  - [ ] Integrate config and database initialization
  - [ ] Run tamper detection on startup (if enabled)
  - [ ] Implement `__main__` entry point
  - [ ] Bind to `127.0.0.1` only (localhost)

- [ ] **3.2 Implement authentication**
  - [ ] Create `src/auth.py`
  - [ ] Implement bcrypt password verification
  - [ ] Implement login route (`POST /login`)
  - [ ] Implement logout route (`POST /logout`)
  - [ ] Implement rate limiting (10 attempts per 15 minutes per IP)
  - [ ] Implement session with 24-hour expiry
  - [ ] Implement `@login_required` decorator for all protected routes
  - [ ] Read `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` from config

- [ ] **3.3 Create dark theme templates and CSS**
  - [ ] Create `templates/base.html` with dark theme layout
  - [ ] Create `static/css/style.css` with dark color scheme
  - [ ] Responsive layout for LCD display sizes
  - [ ] Navigation bar with app title, active wallet indicator, and logout button

- [ ] **3.4 Build login page**
  - [ ] Create `templates/login.html`
  - [ ] Username and password form with CSRF token
  - [ ] Error message display for failed login
  - [ ] Rate limit warning display

- [ ] **3.5 Build dashboard page**
  - [ ] Create `templates/dashboard.html`
  - [ ] Summary cards: Active Wallet, Coin, Addresses Generated, Recent Signings
  - [ ] Current receive address with QR code display
  - [ ] Recent signing request feed (last 10)
  - [ ] Tamper detection status indicator

- [ ] **3.6 Build wallet management page**
  - [ ] Create `templates/wallets.html`
  - [ ] List all wallets with coin, type, derivation path, address count
  - [ ] Create new wallet form (name, coin, derivation path, mnemonic display)
  - [ ] Import wallet from mnemonic (recovery)
  - [ ] Select active wallet button
  - [ ] Address list with copy-to-clipboard and QR display

- [ ] **3.7 Build signing workflow page**
  - [ ] Create `templates/sign.html`
  - [ ] Step 1: Scan QR — camera preview with scan button
  - [ ] Step 2: Review — TX summary (inputs, outputs, fee, addresses)
  - [ ] Step 3: Confirm — explicit confirmation button with warning
  - [ ] Step 4: Display — signed TX QR code on screen for online device camera
  - [ ] Abort button at any step
  - [ ] Progress indicator for chunked QR scan/display

- [ ] **3.8 Implement SocketIO real-time updates**
  - [ ] Emit `scan_progress` event (QR chunks received)
  - [ ] Emit `signing_status` event (parsing → reviewing → signing → complete)
  - [ ] Emit `tamper_alert` event (if integrity check fails)
  - [ ] Emit `wallet_update` event (new address generated)
  - [ ] Client-side handler in `static/js/dashboard.js`

- [ ] **3.9 Build settings panel**
  - [ ] Create `templates/settings.html`
  - [ ] Active coin selector
  - [ ] Derivation path display
  - [ ] Feature toggle display (read-only from `.env`)
  - [ ] Camera status indicator
  - [ ] Display type indicator (LCD / e-ink)
  - [ ] Tamper detection status and re-check button

- [ ] **3.10 Write Phase 3 tests**
  - [ ] Test login (valid credentials, invalid credentials, rate limiting)
  - [ ] Test session expiry (24-hour window)
  - [ ] Test protected route access (authenticated vs unauthenticated)
  - [ ] Test dashboard data API endpoints
  - [ ] Test wallet creation and recovery endpoints
  - [ ] Test signing workflow API (scan → review → confirm → sign → display)
  - [ ] Test SocketIO event emission
  - [ ] Test CSRF protection on forms

---

## Phase 4 — Multi-Coin, Multisig & Backup

- [ ] **4.1 Implement ETH key derivation**
  - [ ] Add ETH derivation path (`m/44'/60'/0'`)
  - [ ] Derive ETH private key from HD wallet
  - [ ] Generate ETH address (Keccak-256 hash of public key, 0x prefix, EIP-55 checksum)
  - [ ] Support EIP-155 transaction signing

- [ ] **4.2 Implement LTC key derivation**
  - [ ] Add LTC derivation path (`m/84'/2'/0'`)
  - [ ] Derive LTC keys from HD wallet
  - [ ] Generate LTC bech32 addresses (ltc1...)
  - [ ] Support LTC transaction signing (similar to BTC with different network params)

- [ ] **4.3 Implement multisig scheme manager**
  - [ ] Create `src/multisig.py`
  - [ ] Implement `create_multisig_wallet(scheme, own_xpub)` — initialize M-of-N wallet
  - [ ] Implement `add_cosigner(wallet_id, cosigner_xpub)` — register cosigner public key
  - [ ] Implement `generate_multisig_address(wallet)` — P2WSH multisig address
  - [ ] Implement `get_multisig_status(wallet)` — show registered cosigners and readiness
  - [ ] Support 2-of-3 and 3-of-5 schemes
  - [ ] Toggle via `ENABLE_MULTISIG`

- [ ] **4.4 Implement cosigner key exchange via QR**
  - [ ] Implement `export_cosigner_xpub_qr(wallet)` — display own xpub as QR
  - [ ] Implement `import_cosigner_xpub_qr(camera)` — scan cosigner xpub from QR
  - [ ] Validate imported xpub format and fingerprint
  - [ ] Store cosigner data in wallet record

- [ ] **4.5 Implement multisig PSBT signing**
  - [ ] Implement `sign_multisig_psbt(psbt, wallet)` — add partial signature
  - [ ] Track signature count (how many of M signatures present)
  - [ ] Implement `combine_psbt(psbt_parts)` — merge partial PSBTs
  - [ ] Finalize when M-of-N threshold reached
  - [ ] Display which cosigners have signed

- [ ] **4.6 Implement encrypted backup**
  - [ ] Create `src/backup.py`
  - [ ] Implement `create_backup(passphrase)`:
    - Derive encryption key from passphrase (PBKDF2, 600k iterations, random salt)
    - Serialize wallet data (encrypted seed, xpub, metadata, address index)
    - Encrypt with AES-256-GCM
    - Generate HMAC for integrity verification
    - Write to `BACKUP_DIR` with timestamped filename
  - [ ] Toggle via `ENABLE_ENCRYPTED_BACKUP`

- [ ] **4.7 Implement backup restore**
  - [ ] Implement `restore_backup(backup_path, passphrase)`:
    - Read and decrypt backup file
    - Verify HMAC integrity
    - Reconstruct wallet from decrypted data
    - Import addresses and metadata
    - Set restored wallet as active
  - [ ] Implement `verify_backup(backup_path, passphrase)` — check integrity without restoring
  - [ ] Implement `list_backups()` — list available backup files with metadata

- [ ] **4.8 Build backup management page**
  - [ ] Create `templates/backup.html`
  - [ ] Create backup form with passphrase input (double-entry confirmation)
  - [ ] List existing backups with timestamps and sizes
  - [ ] Restore from backup form with passphrase input
  - [ ] Verify backup button (integrity check without restore)
  - [ ] Passphrase strength indicator

- [ ] **4.9 Write Phase 4 tests**
  - [ ] Test ETH key derivation and address generation (known test vectors)
  - [ ] Test LTC key derivation and address generation
  - [ ] Test multisig wallet creation (2-of-3, 3-of-5)
  - [ ] Test cosigner xpub import/export
  - [ ] Test multisig address generation
  - [ ] Test multisig PSBT partial signing and combination
  - [ ] Test encrypted backup creation (encryption, HMAC)
  - [ ] Test backup restore (decryption, integrity verification)
  - [ ] Test backup with wrong passphrase (failure case)

---

## Phase 5 — Display, Tamper Detection & Entropy

- [ ] **5.1 Implement display manager**
  - [ ] Create `src/display.py`
  - [ ] Implement `DisplayManager` class with LCD backend
  - [ ] Implement `show_qr(image)` — render QR on LCD via framebuffer
  - [ ] Implement `show_text(text)` — render text message on display
  - [ ] Implement `show_address(address, qr_image)` — combined address + QR view
  - [ ] Implement `clear()` — clear display
  - [ ] Toggle via `ENABLE_LCD_DISPLAY`

- [ ] **5.2 Implement e-ink display support**
  - [ ] Add e-ink backend to `DisplayManager`
  - [ ] Integrate Waveshare 2.13" e-ink HAT driver (SPI)
  - [ ] Implement partial refresh for QR code updates
  - [ ] Implement full refresh for page changes
  - [ ] Show receive address QR persistently (no power needed)
  - [ ] Toggle via `ENABLE_EINK_DISPLAY`
  - [ ] Fallback to LCD when e-ink disabled

- [ ] **5.3 Implement boot-time tamper detection**
  - [ ] Create `src/tamper.py`
  - [ ] Implement `generate_manifest()` — SHA-256 hash all files in `src/`
  - [ ] Implement `verify_integrity()` — compare current hashes to stored manifest
  - [ ] Implement `get_tamper_status()` — return list of modified/missing files
  - [ ] On first run: generate and store manifest to `TAMPER_HASH_FILE`
  - [ ] On subsequent boots: verify against manifest, alert on mismatch
  - [ ] Log tamper events (file changed, file missing, file added)
  - [ ] Display tamper alert on dashboard
  - [ ] Toggle via `ENABLE_TAMPER_DETECTION`

- [ ] **5.4 Implement camera noise entropy**
  - [ ] Enhance `src/entropy.py`
  - [ ] Capture `ENTROPY_CAMERA_FRAMES` frames in darkness (lens cap on)
  - [ ] Extract least-significant bits from pixel values (thermal noise)
  - [ ] Hash extracted noise with SHA-512 for whitening
  - [ ] Mix with other entropy sources

- [ ] **5.5 Implement dice roll entropy**
  - [ ] Add dice roll input to entropy collector
  - [ ] Accept sequence of dice values (1–6) via web UI or local input
  - [ ] Convert dice rolls to binary entropy (base-6 to binary)
  - [ ] Require minimum roll count for target entropy bits
  - [ ] Display entropy accumulated vs required

- [ ] **5.6 Implement entropy quality validation**
  - [ ] Run basic statistical tests on collected entropy:
    - Bit frequency test (should be ~50/50)
    - Run length test (no excessive repetition)
    - Minimum entropy estimation
  - [ ] Reject entropy below quality threshold
  - [ ] Log entropy source breakdown (how many bytes from each source)

- [ ] **5.7 Write Phase 5 tests**
  - [ ] Test LCD display rendering (mocked framebuffer)
  - [ ] Test e-ink display rendering (mocked SPI)
  - [ ] Test display fallback (e-ink disabled → LCD)
  - [ ] Test tamper manifest generation
  - [ ] Test tamper verification (clean, modified, missing file scenarios)
  - [ ] Test camera noise entropy extraction (mocked camera)
  - [ ] Test dice roll entropy conversion
  - [ ] Test entropy quality validation (good randomness, bad randomness)
  - [ ] Test entropy mixing (multiple sources combined)

---

## Phase 6 — Deployment & Documentation

- [ ] **6.1 Create deploy script**
  - [ ] Create `deploy/deploy_to_pi.sh`
  - [ ] rsync project to `rasp-pi` (pi@192.168.216.90)
  - [ ] Exclude `.venv`, `__pycache__`, `.git`, `data/`
  - [ ] Remote `pip install -r requirements.txt`
  - [ ] Print warning: this is the last network deploy before air-gap

- [ ] **6.2 Create networking disable script**
  - [ ] Create `scripts/disable_networking.sh`
  - [ ] Add `dtoverlay=disable-wifi` to `/boot/config.txt` if not present
  - [ ] Add `dtoverlay=disable-bt` to `/boot/config.txt` if not present
  - [ ] Disable `wpa_supplicant` service
  - [ ] Disable `bluetooth` service
  - [ ] Disable `hciuart` service
  - [ ] Blacklist WiFi kernel modules (`brcmfmac`, `brcmutil`)
  - [ ] Blacklist Bluetooth kernel modules (`btbcm`, `hci_uart`)
  - [ ] Print reboot required message
  - [ ] Print air-gap verification steps

- [ ] **6.3 Create OS dependency installer**
  - [ ] Create `scripts/install_deps.sh`
  - [ ] Install `python3-venv`, `python3-dev`, `python3-pip`
  - [ ] Install `libzbar0` (for pyzbar QR decoding)
  - [ ] Install `libjpeg-dev`, `libpng-dev` (for Pillow)
  - [ ] Install camera libraries (`libcamera-apps`)
  - [ ] Enable camera interface and SPI (for e-ink)
  - [ ] Print success message

- [ ] **6.4 Create password hash helper**
  - [ ] Create `scripts/generate_password_hash.sh`
  - [ ] Prompt for password (no echo)
  - [ ] Generate bcrypt hash using Python one-liner
  - [ ] Print hash for inclusion in `.env`

- [ ] **6.5 Write systemd service unit**
  - [ ] Create service file for documentation (in README)
  - [ ] `ExecStartPre` runs networking disable script (idempotent)
  - [ ] Bind to `127.0.0.1` only
  - [ ] Restart on failure with backoff

- [ ] **6.6 Write air gap verification guide**
  - [ ] Create `docs/air_gap_guide.md`
  - [ ] Step-by-step verification commands (`ip link`, `rfkill list`, `iwconfig`)
  - [ ] Expected output for each command
  - [ ] What to do if air gap is compromised

- [ ] **6.7 Write QR protocol specification**
  - [ ] Create `docs/qr_protocol.md`
  - [ ] Document single QR format (base64-encoded PSBT)
  - [ ] Document chunked QR format (header + data)
  - [ ] Document supported QR versions and error correction levels
  - [ ] Interoperability notes with Electrum, Sparrow, BlueWallet

- [ ] **6.8 Write backup & recovery guide**
  - [ ] Create `docs/backup_recovery.md`
  - [ ] Backup creation procedure
  - [ ] Restore procedure
  - [ ] Verify procedure
  - [ ] Disaster recovery scenarios (lost Pi, corrupted SD, forgotten passphrase)
  - [ ] Best practices for backup media storage

- [ ] **6.9 Final integration testing**
  - [ ] Test full workflow: generate wallet → derive addresses → receive unsigned PSBT via QR → sign → display signed QR
  - [ ] Test air gap verification after networking disable
  - [ ] Test backup/restore round-trip
  - [ ] Test tamper detection with intentional file modification
  - [ ] Test multisig workflow with 2 cold wallets
  - [ ] Test multi-coin address generation (BTC, ETH, LTC)
  - [ ] Test e-ink display (if available)
  - [ ] Verify dashboard bound to localhost only

- [ ] **6.10 Update README**
  - [ ] Finalize quickstart instructions
  - [ ] Add screenshots of dashboard (from LCD display)
  - [ ] Verify all feature descriptions match implementation
  - [ ] Update troubleshooting table with real-world issues found during testing
