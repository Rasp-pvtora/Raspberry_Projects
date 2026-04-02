# Implementation Plan — Air-Gapped Cold Storage Crypto Wallet

## Phase 1 — Project Foundation & Wallet Engine

**Goal:** Scaffold the project, configure environment loading, set up the database, and build the core wallet engine with BIP-39/32 key generation and physical entropy.

- [ ] **Step 1.1 — Initialize Project Structure**
  - [ ] Create directory tree:
    ```
    src/, templates/, static/css/, static/js/, tests/, deploy/, scripts/, docs/, data/, data/backups/
    ```
  - [ ] Create `pyproject.toml` with project name, version, Python ≥3.11, and entry point `src.app`
  - [ ] Create `requirements.txt`:
    ```
    flask
    flask-socketio
    eventlet
    bcrypt
    python-dotenv
    bitcoinlib
    python-bitcoinlib
    qrcode
    pyzbar
    Pillow
    cryptography
    mnemonic
    picamera2
    RPi.GPIO
    gunicorn
    pytest
    pytest-cov
    ```
  - [ ] Create `.env.example` with all variables and documented defaults (see TSD §8)
  - [ ] Create `src/__init__.py` (empty)
  - [ ] Create `tests/__init__.py` (empty) and `tests/conftest.py` with shared fixtures

- [ ] **Step 1.2 — Configuration Loader**
  - [ ] Create `src/config.py`
  - [ ] Define `@dataclass class Config` with all `.env` fields and proper types
  - [ ] Implement `load_config()` — reads `.env` via `dotenv_values()`, applies defaults
  - [ ] Convert string values to `int`, `float`, `bool` as needed
  - [ ] Parse `DERIVATION_PATHS` comma-separated string into list
  - [ ] Parse `CAMERA_RESOLUTION` into `(width, height)` tuple
  - [ ] Add `is_enabled(feature: str) -> bool` helper for toggle checks
  - [ ] Write `tests/test_config.py` — test loading, defaults, type conversion, missing keys

- [ ] **Step 1.3 — SQLite Database Module**
  - [ ] Create `src/database.py`
  - [ ] Implement `get_connection(db_path)` with WAL mode pragma
  - [ ] Implement `init_db(conn)` — creates all 5 tables (see TSD §3)
  - [ ] Implement CRUD functions:
    - `insert_wallet(conn, wallet_data)` / `update_wallet(conn, wallet_id, data)`
    - `get_wallet(conn, wallet_id)` / `list_wallets(conn)`
    - `get_active_wallet(conn)` / `set_active_wallet(conn, wallet_id)`
    - `insert_address(conn, address_data)` / `get_addresses(conn, wallet_id)`
    - `insert_transaction(conn, tx_data)` / `update_transaction(conn, tx_id, data)`
    - `get_transactions(conn, wallet_id, limit, offset)`
    - `insert_signing_request(conn, req_data)` / `update_signing_request(conn, req_id, data)`
    - `get_signing_requests(conn, wallet_id, status)`
    - `get_setting(conn, key)` / `set_setting(conn, key, value)`
  - [ ] Use parameterized queries for all DB operations
  - [ ] Write `tests/test_database.py` — test schema creation, all CRUD ops, WAL mode

- [ ] **Step 1.4 — Physical Entropy Collector**
  - [ ] Create `src/entropy.py`
  - [ ] Implement `EntropyCollector` class:
    - `collect_hwrng(num_bytes)` — read from `/dev/hwrng`
    - `collect_camera_noise(frames)` — capture N camera frames, extract LSBs from pixel data
    - `collect_dice(rolls: list[int])` — convert dice roll sequence to binary entropy
    - `mix(*sources) -> bytes` — XOR all sources together with `os.urandom()` base
    - `validate(data: bytes) -> bool` — basic frequency test (bit distribution ~50/50)
    - `collect(num_bytes, include_camera, include_dice) -> bytes` — orchestrate collection
  - [ ] Toggle physical sources via `ENABLE_PHYSICAL_ENTROPY`
  - [ ] Fallback to `os.urandom()` when hardware sources unavailable
  - [ ] Mock mode: return deterministic bytes for reproducible tests

- [ ] **Step 1.5 — BIP-39 Mnemonic Generation**
  - [ ] Create `src/wallet.py`
  - [ ] Implement `WalletEngine` class:
    - `generate_mnemonic(strength=256, extra_entropy=None) -> str`:
      - If `extra_entropy` provided, XOR with generated entropy
      - Use `mnemonic` library to produce word list
      - Return space-separated mnemonic string
    - `validate_mnemonic(words: str) -> bool` — checksum verification
    - `mnemonic_to_seed(words: str, passphrase: str = "") -> bytes`:
      - PBKDF2-HMAC-SHA512 with 2048 iterations per BIP-39 spec
      - Return 64-byte seed
  - [ ] Support strengths: 128 (12 words), 160 (15), 192 (18), 224 (21), 256 (24)
  - [ ] Integrate physical entropy from `EntropyCollector`
  - [ ] Toggle via `ENABLE_BIP39`

- [ ] **Step 1.6 — BIP-32/44/84 HD Wallet Derivation**
  - [ ] Implement in `WalletEngine`:
    - `derive_master_key(seed: bytes) -> HDKey` — HMAC-SHA512 to get master private/chain code
    - `derive_path(master: HDKey, path: str) -> HDKey` — BIP-32 child key derivation
    - `derive_wallet(seed, derivation_path) -> WalletKeys`:
      - Derive account-level key from path
      - Generate extended public key (xpub/zpub)
      - Extract master fingerprint (first 4 bytes of hash160 of master pubkey)
    - `derive_address_key(wallet_key, change: int, index: int) -> HDKey`:
      - Derive `m/.../change/index` child key for specific address
  - [ ] Support hardened derivation (index ≥ 0x80000000) for account-level keys
  - [ ] Support BIP-44 (`m/44'/coin'/account'`) and BIP-84 (`m/84'/coin'/account'`)
  - [ ] Toggle via `ENABLE_BIP32`

- [ ] **Step 1.7 — Address Generation**
  - [ ] Create `src/coins.py` with coin-specific logic:
    - `BTCCoin` class:
      - `generate_address(pubkey, addr_type='bech32') -> str` — P2WPKH (bc1...) or P2PKH (1...)
      - Network parameters (mainnet prefix, bech32 HRP)
    - `derive_btc_address(wallet_key, index, change=0) -> str`
  - [ ] Implement `generate_addresses(wallet, count, addr_type) -> list[Address]`:
    - Batch-derive N addresses from wallet
    - Store in `addresses` table with derivation path
    - Increment wallet's `address_index`
  - [ ] Track address gap limit (20 unused addresses)

- [ ] **Step 1.8 — Mock Mode**
  - [ ] Implement `MockCamera` class — returns test QR image with embedded data
  - [ ] Implement `MockDisplay` class — logs output to stdout instead of rendering
  - [ ] Implement `MockEntropy` class — returns deterministic bytes for reproducible tests
  - [ ] Factory functions: `create_camera(config)`, `create_display(config)`, `create_entropy(config)`
  - [ ] Activate via `MOCK_MODE=true`
  - [ ] Allow full dashboard and signing workflow testing without hardware

- [ ] **Step 1.9 — Phase 1 Tests**
  - [ ] `tests/test_config.py` — loading, defaults, type conversion, feature toggles
  - [ ] `tests/test_database.py` — schema creation, CRUD for all 5 tables, WAL mode
  - [ ] `tests/test_entropy.py` — hwrng (mocked), camera noise (mocked), dice, mixing, validation
  - [ ] `tests/test_wallet.py`:
    - BIP-39: generation, validation, seed derivation (known test vectors from BIP-39 spec)
    - BIP-32: master key derivation, child derivation (test vectors from BIP-32 spec)
    - BIP-44/84: full path derivation, address generation
  - [ ] `tests/test_coins.py` — BTC bech32 address generation, legacy address generation

**Checkpoint:** Wallet engine generates BIP-39 mnemonics with physical entropy, derives HD keys via BIP-32/44/84, and generates BTC addresses. Database stores wallet and address data. Config loader handles all `.env` toggles.

---

## Phase 2 — Transaction Signing & QR Exchange

**Goal:** Build the PSBT signing engine and QR code exchange protocol for air-gapped transaction signing.

- [ ] **Step 2.1 — PSBT Parser (BIP-174)**
  - [ ] Create `src/signer.py` with `TransactionSigner` class
  - [ ] Implement `parse_psbt(data: bytes) -> PSBT`:
    - Decode from base64 or raw binary
    - Validate magic bytes (`0x70736274ff`)
    - Parse global map (unsigned TX, xpub entries)
    - Parse per-input maps (UTXO data, derivation paths, sighash type)
    - Parse per-output maps (derivation paths)
    - Return structured PSBT object
  - [ ] Implement `validate_psbt(psbt: PSBT) -> ValidationResult`:
    - Check all inputs have UTXO data
    - Verify derivation paths match wallet keys
    - Check for duplicate inputs
    - Return list of warnings/errors
  - [ ] Toggle via `ENABLE_PSBT`

- [ ] **Step 2.2 — Transaction Signing**
  - [ ] Implement `sign_psbt(psbt: PSBT, wallet: WalletKeys) -> PSBT`:
    - Iterate inputs, find those matching wallet's derivation paths
    - For each matching input: derive private key, compute sighash, sign
    - Support SegWit (BIP-143) sighash computation for P2WPKH inputs
    - Support legacy (pre-SegWit) sighash for P2PKH inputs
    - Add partial signatures to PSBT input maps
    - Return updated PSBT with signatures
  - [ ] Implement `finalize_psbt(psbt: PSBT) -> bytes`:
    - Check all inputs are fully signed
    - Construct final scriptSig/witness for each input
    - Extract final raw transaction bytes
    - Compute TXID
  - [ ] Implement `sign_raw_tx(tx_hex, wallet, input_info) -> str`:
    - Legacy signing path for non-PSBT workflows
    - Return signed transaction hex
  - [ ] Record all signing events in `transactions` table

- [ ] **Step 2.3 — Transaction Review Summary**
  - [ ] Implement `generate_review(psbt: PSBT) -> ReviewSummary`:
    - Extract: number of inputs, total input value (satoshis)
    - Extract: each output address and amount
    - Calculate: fee (total input − total output)
    - Identify: change outputs (matching wallet derivation paths)
    - Format: human-readable summary with BTC amounts
  - [ ] Display summary on screen/dashboard for user verification before signing
  - [ ] Require explicit user confirmation (button press or web UI confirm)

- [ ] **Step 2.4 — QR Code Generation**
  - [ ] Create `src/qr_handler.py`
  - [ ] Implement `encode_qr(data: bytes, error_correction='H') -> PIL.Image`:
    - Select optimal QR version for data size
    - Generate QR code with `qrcode` library
    - Render to PIL Image at configured module size
  - [ ] Implement `render_to_display(qr_image, display_manager)`:
    - Resize QR image to fit display resolution
    - Send to LCD/e-ink via display manager
  - [ ] Configurable error correction from `QR_ERROR_CORRECTION`

- [ ] **Step 2.5 — QR Code Scanning**
  - [ ] Implement `scan_qr(camera) -> bytes`:
    - Capture frame from Pi Camera
    - Decode QR code from frame using `pyzbar`
    - Return decoded data bytes
  - [ ] Implement `continuous_scan(camera, timeout_sec=60) -> bytes`:
    - Loop: capture frame, attempt decode, repeat until success or timeout
    - Display "Scanning..." indicator on screen
    - Return decoded data or raise `TimeoutError`
  - [ ] Handle multiple QR format types (alphanumeric, binary, base64)

- [ ] **Step 2.6 — Chunked QR Protocol**
  - [ ] Implement `chunk_data(data: bytes, max_chunk: int) -> list[bytes]`:
    - Split data into chunks ≤ `QR_MAX_CHUNK_SIZE`
    - Prepend header to each chunk: `p{chunk_idx}of{total}:{data}`
  - [ ] Implement `encode_chunked_qr(chunks) -> list[PIL.Image]`:
    - Generate one QR code per chunk
    - Return list of images for sequential display
  - [ ] Implement `display_chunked_qr(images, display, interval_ms=1000)`:
    - Cycle through QR images on display at configured interval
    - Repeat until user cancels or all chunks acknowledged
  - [ ] Implement `scan_chunked_qr(camera, expected_total) -> bytes`:
    - Scan QR codes, parse headers, collect unique chunks
    - Track progress (received/total)
    - Reassemble data when all chunks received
    - Validate reassembled data checksum (SHA-256 in final chunk)

- [ ] **Step 2.7 — Phase 2 Tests**
  - [ ] `tests/test_signer.py`:
    - Test PSBT parsing (valid PSBT, malformed, missing UTXO, unknown keys)
    - Test PSBT validation (matching keys, non-matching, duplicate inputs)
    - Test signing against known test vectors (BIP-174 test vectors)
    - Test finalization (fully signed, partially signed rejection)
    - Test review summary generation (amounts, fees, change detection)
  - [ ] `tests/test_qr_handler.py`:
    - Test QR encoding (small data, max capacity, error correction levels)
    - Test QR decoding (mocked camera with embedded QR image)
    - Test chunked protocol (split, reassemble, integrity check, missing chunk handling)
    - Test continuous scan timeout behavior

**Checkpoint:** Full PSBT signing pipeline working. QR exchange protocol handles single and chunked QR codes. Transaction review summary displayed before signing. All signing events recorded in database.

---

## Phase 3 — Web Dashboard & Authentication

**Goal:** Build the authenticated dark-themed local dashboard with wallet management and signing workflow.

- [ ] **Step 3.1 — Flask App Factory**
  - [ ] Create `src/app.py`:
    - `create_app(config)` factory pattern
    - Initialize Flask-SocketIO with eventlet mode
    - Register route handlers
    - Initialize database on startup
    - Run tamper detection on startup (if enabled)
    - Implement `__main__` block to run the app
    - Bind to `127.0.0.1` only (localhost — air-gapped)
  - [ ] Toggle dashboard via `ENABLE_WEB_DASHBOARD`

- [ ] **Step 3.2 — Authentication Module**
  - [ ] Create `src/auth.py`:
    - `verify_password(plaintext, bcrypt_hash) -> bool`
    - `login_user(session, username)` — set session data with expiry timestamp
    - `logout_user(session)` — clear session
    - `is_authenticated(session) -> bool` — check session validity and expiry
    - `login_required(f)` — decorator redirecting to `/login`
  - [ ] Route `GET /login` — render login form
  - [ ] Route `POST /login` — verify credentials, rate limit check, set session
  - [ ] Route `POST /logout` — clear session, redirect to login
  - [ ] Rate limiter: store attempt counts per IP in memory dict with 15-min window
  - [ ] Session expiry: check `SESSION_EXPIRY_HOURS` (default 24h) on each request

- [ ] **Step 3.3 — Dark Theme Templates & CSS**
  - [ ] Create `templates/base.html`:
    - HTML5 boilerplate with dark background (`#1a1a2e`)
    - Navigation bar (app title, active wallet indicator, tamper status, logout)
    - Content block, script block
    - SocketIO client script
  - [ ] Create `static/css/style.css`:
    - Dark palette: background `#1a1a2e`, cards `#16213e`, text `#e0e0e0`, accent `#0f3460`
    - Status badges: signing (green pulse), pending (yellow), error (red), verified (green)
    - Coin badges: BTC (orange), ETH (blue), LTC (gray)
    - QR code display area (centered, high-contrast white on dark)
    - Table styling, responsive grid, form inputs
    - Camera preview area styling

- [ ] **Step 3.4 — Login Page**
  - [ ] Create `templates/login.html` extending base
  - [ ] Centered login card with username/password fields
  - [ ] CSRF token hidden field
  - [ ] Flash message area for errors ("Invalid credentials", "Rate limited")
  - [ ] Air-gap status indicator at bottom

- [ ] **Step 3.5 — Dashboard Page**
  - [ ] Create `templates/dashboard.html` extending base
  - [ ] Summary cards: Active Wallet, Coin, Available Addresses, Total Signings
  - [ ] Current receive address with QR code display
  - [ ] Recent signing request feed (last 10 with status badges)
  - [ ] Tamper detection status indicator (green check / red alert)
  - [ ] Quick action buttons: New Wallet, Sign Transaction, Generate Address

- [ ] **Step 3.6 — Wallet Management Page**
  - [ ] Create `templates/wallets.html` extending base
  - [ ] List all wallets: name, coin, type (single/multisig), derivation path, address count
  - [ ] Create wallet form: name, coin selector, derivation path, mnemonic strength
  - [ ] Mnemonic display modal (show once, require confirmation)
  - [ ] Import wallet form: enter mnemonic words for recovery
  - [ ] Select active wallet button
  - [ ] Address list per wallet: address, path, used status, QR display button

- [ ] **Step 3.7 — Signing Workflow Page**
  - [ ] Create `templates/sign.html` extending base
  - [ ] Step-by-step wizard:
    - **Step 1 — Scan:** Camera preview with "Start Scan" button, chunk progress bar
    - **Step 2 — Review:** TX summary table (inputs, outputs, fee), address verification
    - **Step 3 — Confirm:** Large "SIGN" button with red warning text, "REJECT" button
    - **Step 4 — Display:** Signed QR code on screen, "Done" button to dismiss
  - [ ] Abort button visible at all steps
  - [ ] SocketIO-powered status updates (scanning → reviewing → signing → displaying)

- [ ] **Step 3.8 — SocketIO Real-time Events**
  - [ ] Server emits:
    - `scan_progress` — `{chunks_received, total_chunks}`
    - `signing_status` — `{status: 'parsing'|'reviewing'|'signing'|'complete'|'error'}`
    - `tamper_alert` — `{modified_files: [...]}`
    - `wallet_update` — `{wallet_id, new_address}`
  - [ ] Create `static/js/dashboard.js` — connect SocketIO, update status panels
  - [ ] Create `static/js/sign.js` — handle signing wizard state transitions

- [ ] **Step 3.9 — Settings Panel**
  - [ ] Create `templates/settings.html` extending base
  - [ ] Active coin display with selector
  - [ ] Derivation path display
  - [ ] Feature toggle display (read-only, showing `.env` state)
  - [ ] Camera status indicator
  - [ ] Display type indicator (LCD / e-ink / HDMI)
  - [ ] Tamper status with "Re-check" button
  - [ ] Regenerate integrity manifest button (requires confirmation)

- [ ] **Step 3.10 — Phase 3 Tests**
  - [ ] `tests/test_auth.py` — login, logout, invalid creds, rate limiting, session expiry
  - [ ] `tests/test_api.py`:
    - Dashboard route (auth required, data populated)
    - Wallet creation and recovery endpoints
    - Address generation endpoint
    - Signing workflow endpoints (initiate scan → confirm → sign)
    - Settings retrieval
  - [ ] Test SocketIO event emission
  - [ ] Test CSRF protection on all POST routes

**Checkpoint:** Fully functional dark-themed local dashboard with wallet management, signing workflow wizard, and real-time status updates. All protected by bcrypt auth with rate limiting. Dashboard binds to localhost only.

---

## Phase 4 — Multi-Coin, Multisig & Backup

**Goal:** Add multi-coin key derivation, multisig support, and AES-256 encrypted backup system.

- [ ] **Step 4.1 — ETH Key Derivation**
  - [ ] Add `ETHCoin` class to `src/coins.py`:
    - Derivation path: `m/44'/60'/0'/0/index`
    - `derive_eth_private_key(wallet_key, index) -> bytes` — 32-byte private key
    - `private_to_address(privkey) -> str` — Keccak-256 of uncompressed pubkey, take last 20 bytes, 0x prefix
    - EIP-55 mixed-case checksum encoding
  - [ ] Store ETH addresses in `addresses` table with `coin='ETH'`

- [ ] **Step 4.2 — LTC Key Derivation**
  - [ ] Add `LTCCoin` class to `src/coins.py`:
    - Derivation path: `m/84'/2'/0'/0/index`
    - `generate_address(pubkey) -> str` — bech32 with `ltc` HRP
    - Network parameters (Litecoin mainnet)
  - [ ] Support LTC transaction signing (same structure as BTC, different network magic)

- [ ] **Step 4.3 — Multisig Wallet Manager**
  - [ ] Create `src/multisig.py` with `MultisigManager` class:
    - `create_multisig_wallet(name, scheme, own_xpub) -> int`:
      - Parse scheme string ("2-of-3" → m=2, n=3)
      - Create wallet record with `wallet_type='multisig'`
      - Store own xpub as first cosigner
    - `add_cosigner(wallet_id, cosigner_xpub, label) -> bool`:
      - Validate xpub format
      - Check cosigner count doesn't exceed N
      - Store cosigner data (JSON in wallet metadata or separate table)
    - `is_ready(wallet_id) -> bool` — check all N cosigners registered
    - `generate_multisig_address(wallet_id, index) -> str`:
      - Derive pubkeys from all cosigners at `index`
      - Build M-of-N multisig redeem script (sorted pubkeys)
      - Generate P2WSH (bech32) address
  - [ ] Toggle via `ENABLE_MULTISIG`

- [ ] **Step 4.4 — Cosigner Key Exchange via QR**
  - [ ] Implement `export_own_xpub_qr(wallet) -> PIL.Image`:
    - Encode xpub + fingerprint + derivation path as JSON
    - Generate QR image for display
  - [ ] Implement `import_cosigner_xpub_qr(camera) -> CosignerInfo`:
    - Scan QR from cosigner's device
    - Parse JSON, validate xpub format
    - Return `CosignerInfo(xpub, fingerprint, path, label)`
  - [ ] Add QR exchange UI to signing workflow page

- [ ] **Step 4.5 — Multisig PSBT Signing**
  - [ ] Implement `sign_multisig_psbt(psbt, wallet) -> PSBT`:
    - Identify inputs matching multisig addresses
    - Derive own private key for each input
    - Add partial signature (own signature only)
    - Update PSBT with partial signature in correct field
  - [ ] Implement `count_signatures(psbt, input_idx) -> int`:
    - Count partial signatures present for an input
  - [ ] Implement `check_threshold(psbt, wallet) -> bool`:
    - Return True if M-of-N signatures collected across all inputs
  - [ ] Auto-finalize when threshold reached

- [ ] **Step 4.6 — Encrypted Backup Creation**
  - [ ] Create `src/backup.py` with `BackupManager` class:
    - `create_backup(passphrase: str, wallet_ids: list[int] = None) -> str`:
      - Collect wallet data: encrypted seeds, xpubs, metadata, address indices
      - Serialize to JSON
      - Derive AES key from passphrase: PBKDF2-HMAC-SHA256, 600,000 iterations, random 16-byte salt
      - Encrypt with AES-256-GCM (12-byte nonce, 16-byte auth tag)
      - Prepend: version byte + salt + nonce
      - Write to `BACKUP_DIR/backup_YYYYMMDD_HHMMSS.enc`
      - Return backup file path
  - [ ] Toggle via `ENABLE_ENCRYPTED_BACKUP`

- [ ] **Step 4.7 — Backup Restore**
  - [ ] Implement `restore_backup(backup_path: str, passphrase: str) -> list[int]`:
    - Read backup file
    - Extract version, salt, nonce from header
    - Derive AES key from passphrase + salt
    - Decrypt with AES-256-GCM (auth tag verifies integrity)
    - Deserialize wallet data
    - Import wallets and addresses into database
    - Return list of restored wallet IDs
  - [ ] Implement `verify_backup(backup_path: str, passphrase: str) -> bool`:
    - Attempt decrypt; return True if auth tag passes, False if not
    - Do not import any data
  - [ ] Implement `list_backups() -> list[BackupInfo]`:
    - Scan `BACKUP_DIR` for `.enc` files
    - Return list with filename, size, modified date

- [ ] **Step 4.8 — Backup Management Page**
  - [ ] Create `templates/backup.html` extending base
  - [ ] Create backup form:
    - Passphrase input (double-entry for confirmation)
    - Select wallets to include (checkboxes, default all)
    - "Create Backup" button
    - Passphrase strength indicator
  - [ ] Existing backups list: filename, date, size, verify button, restore button
  - [ ] Restore form: select backup file, enter passphrase, "Restore" button
  - [ ] Verify button: test decryption without importing

- [ ] **Step 4.9 — Phase 4 Tests**
  - [ ] `tests/test_coins.py`:
    - ETH address generation (known test vectors, EIP-55 checksum)
    - LTC bech32 address generation
  - [ ] `tests/test_multisig.py`:
    - Multisig wallet creation (2-of-3, 3-of-5)
    - Cosigner xpub import/validation
    - Multisig address generation (sorted pubkeys, P2WSH)
    - Partial signing and threshold checking
  - [ ] `tests/test_backup.py`:
    - Backup creation (encryption, salt, nonce)
    - Backup restore (decryption, data integrity)
    - Verify backup (pass/fail)
    - Wrong passphrase (authentication failure)
    - Backup listing

**Checkpoint:** Multi-coin support (BTC, ETH, LTC). Multisig 2-of-3 and 3-of-5 with cosigner QR exchange. AES-256-GCM encrypted backup with PBKDF2 key derivation. Backup management UI.

---

## Phase 5 — Display, Tamper Detection & Entropy Enhancement

**Goal:** Add e-ink display support, boot-time tamper detection, and enhanced physical entropy with quality validation.

- [ ] **Step 5.1 — Display Manager (LCD)**
  - [ ] Create `src/display.py` with `DisplayManager` class:
    - `__init__(config)` — select backend based on `DISPLAY_TYPE`
    - `show_qr(image: PIL.Image)` — render QR code on display
    - `show_text(text: str, font_size: int)` — render text message
    - `show_address(address: str, qr_image: PIL.Image)` — combined address + QR view
    - `show_signing_status(status: str)` — status message during signing
    - `clear()` — clear display to black
  - [ ] LCD backend: write to framebuffer (`/dev/fb0` or SDL)
  - [ ] Toggle via `ENABLE_LCD_DISPLAY`

- [ ] **Step 5.2 — E-Ink Display Support**
  - [ ] Add `EInkBackend` to `DisplayManager`:
    - Import Waveshare 2.13" e-ink driver (SPI)
    - `init()` — initialize SPI connection and clear display
    - `show_qr(image)` — convert to 1-bit, send to e-ink (full refresh)
    - `show_address(address, qr)` — persistent address display
    - `partial_refresh(image)` — partial update for status messages
    - `sleep()` — put display in low-power mode
  - [ ] Toggle via `ENABLE_EINK_DISPLAY`
  - [ ] Fallback: if e-ink not detected, revert to LCD backend with warning

- [ ] **Step 5.3 — Boot-Time Tamper Detection**
  - [ ] Create `src/tamper.py` with `TamperDetector` class:
    - `generate_manifest(src_dir: str) -> dict`:
      - Walk all `.py` files in `src/`
      - Compute SHA-256 hash of each file
      - Return `{filepath: hash}` dict
    - `save_manifest(manifest: dict, path: str)`:
      - Write JSON manifest to `TAMPER_HASH_FILE`
    - `verify_integrity(src_dir: str) -> TamperResult`:
      - Load stored manifest
      - Recompute hashes of all `src/` files
      - Compare: identify modified, missing, and new files
      - Return `TamperResult(is_clean, modified=[], missing=[], added=[])`
    - `get_status() -> str` — return "clean", "tampered", or "uninitialized"
  - [ ] On first run (no manifest exists): generate and save automatically
  - [ ] On subsequent boots: verify and report
  - [ ] Alert on dashboard via SocketIO `tamper_alert` event
  - [ ] Toggle via `ENABLE_TAMPER_DETECTION`

- [ ] **Step 5.4 — Camera Noise Entropy**
  - [ ] Enhance `EntropyCollector.collect_camera_noise()`:
    - Capture `ENTROPY_CAMERA_FRAMES` frames
    - Extract least-significant bits from pixel values (R, G, B channels)
    - Collect at least `num_bytes * 8` raw bits from frames
    - Hash raw bits with SHA-512 for whitening
    - Return hashed output as entropy bytes

- [ ] **Step 5.5 — Dice Roll Entropy**
  - [ ] Enhance `EntropyCollector.collect_dice()`:
    - Accept list of dice values (1–6) from web UI input
    - Convert base-6 sequence to binary:
      - Two dice values → one byte: `(d1 - 1) * 6 + (d2 - 1)` → 0–35 range → discard 32–35, use 0–31 (5 bits)
    - Calculate: minimum N dice rolls needed for target entropy bits
    - Display progress (rolls entered / rolls needed)

- [ ] **Step 5.6 — Entropy Quality Validation**
  - [ ] Enhance `EntropyCollector.validate()`:
    - **Frequency test:** count 0-bits and 1-bits, check ratio within ±5% of 50%
    - **Runs test:** count consecutive same-bit runs, compare to expected distribution
    - **Minimum entropy estimate:** compress data, verify compressed size ≥ 90% of raw
  - [ ] Reject entropy that fails tests (require regeneration)
  - [ ] Log entropy quality metrics for audit

- [ ] **Step 5.7 — Phase 5 Tests**
  - [ ] `tests/test_display.py`:
    - LCD rendering (mocked framebuffer)
    - E-ink rendering (mocked SPI)
    - Display fallback (e-ink disabled → LCD)
    - QR display sizing for different resolutions
  - [ ] `tests/test_tamper.py`:
    - Manifest generation (hash all src files)
    - Clean verification (no changes)
    - Tampered verification (modified file detected)
    - Missing file detection
    - New file detection
    - No manifest (first run) → generate
  - [ ] `tests/test_entropy.py` (additions):
    - Camera noise extraction (mocked camera frames)
    - Dice roll conversion (known values)
    - Entropy quality validation (good data passes, bad data fails)
    - Mixed source entropy

**Checkpoint:** E-ink display support for persistent address display. Boot-time tamper detection catches modified files. Physical entropy enhanced with camera noise and dice rolls, validated for quality.

---

## Phase 6 — Deployment, Air-Gap Scripts & Documentation

**Goal:** Finalize deploy pipeline, air-gap setup scripts, systemd service, and all documentation.

- [ ] **Step 6.1 — Deploy Script (Pre-Air-Gap)**
  - [ ] Create `deploy/deploy_to_pi.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    PI_HOST="rasp-pi"
    REMOTE_DIR="/home/pi/cold-wallet"
    echo "[*] Deploying to ${PI_HOST}:${REMOTE_DIR}"
    rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
        --exclude '.git' --exclude 'data/' \
        ./ "${PI_HOST}:${REMOTE_DIR}/"
    ssh "${PI_HOST}" "cd ${REMOTE_DIR} && source .venv/bin/activate && pip install -r requirements.txt"
    echo "[✓] Deploy complete."
    echo "[!] NEXT: Run scripts/disable_networking.sh to establish air gap."
    ```
  - [ ] Make executable (`chmod +x`)

- [ ] **Step 6.2 — Networking Disable Script**
  - [ ] Create `scripts/disable_networking.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    # Disable WiFi overlay
    if ! grep -q "dtoverlay=disable-wifi" /boot/config.txt; then
        echo "dtoverlay=disable-wifi" >> /boot/config.txt
        echo "[+] WiFi disabled via overlay"
    fi
    # Disable Bluetooth overlay
    if ! grep -q "dtoverlay=disable-bt" /boot/config.txt; then
        echo "dtoverlay=disable-bt" >> /boot/config.txt
        echo "[+] Bluetooth disabled via overlay"
    fi
    # Blacklist kernel modules
    cat >> /etc/modprobe.d/disable-wireless.conf << 'EOF'
    blacklist brcmfmac
    blacklist brcmutil
    blacklist btbcm
    blacklist hci_uart
    blacklist bluetooth
    EOF
    # Disable services
    systemctl disable wpa_supplicant 2>/dev/null || true
    systemctl disable bluetooth 2>/dev/null || true
    systemctl disable hciuart 2>/dev/null || true
    echo "[✓] Networking permanently disabled."
    echo "[!] REBOOT REQUIRED: sudo reboot"
    echo "[!] After reboot, run scripts/verify_airgap.sh to confirm."
    ```
  - [ ] Make executable

- [ ] **Step 6.3 — Air-Gap Verification Script**
  - [ ] Create `scripts/verify_airgap.sh`:
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    echo "[*] Verifying air gap..."
    # Check no wireless interfaces
    if ip link show wlan0 &>/dev/null; then
        echo "[✗] FAIL: wlan0 interface exists!"
        exit 1
    fi
    # Check no bluetooth
    if hciconfig hci0 &>/dev/null 2>&1; then
        echo "[✗] FAIL: Bluetooth adapter detected!"
        exit 1
    fi
    # Check rfkill
    if rfkill list 2>/dev/null | grep -qi "soft blocked: no"; then
        echo "[!] WARNING: Some radios not soft-blocked. Check rfkill list."
    fi
    # Check no active network (except loopback)
    ACTIVE=$(ip -o link show up | grep -v "lo:" | wc -l)
    if [ "$ACTIVE" -gt 0 ]; then
        echo "[✗] FAIL: ${ACTIVE} active network interface(s) detected!"
        ip -o link show up | grep -v "lo:"
        exit 1
    fi
    echo "[✓] Air gap verified. No network interfaces active."
    ```
  - [ ] Make executable

- [ ] **Step 6.4 — OS Dependency Installer**
  - [ ] Create `scripts/install_deps.sh`:
    - Install `python3-venv`, `python3-dev`, `python3-pip`
    - Install `libzbar0` (for pyzbar)
    - Install `libjpeg-dev`, `libpng-dev`, `libfreetype6-dev` (for Pillow)
    - Install `libcamera-apps` (for picamera2)
    - Enable camera interface (`raspi-config nonint do_camera 0`)
    - Enable SPI (`raspi-config nonint do_spi 0`) — for e-ink
    - Print success message

- [ ] **Step 6.5 — Air Gap Verification Guide**
  - [ ] Create `docs/air_gap_guide.md`:
    - Pre-air-gap checklist (all software installed, all deps present)
    - Disable networking procedure (step-by-step)
    - Post-reboot verification commands with expected output
    - What to do if air gap is broken
    - How to update software after air gap (SD card swap method)

- [ ] **Step 6.6 — QR Protocol Specification**
  - [ ] Create `docs/qr_protocol.md`:
    - Single QR format: base64-encoded PSBT
    - Chunked QR format: `p{idx}of{total}:{base64_chunk}`
    - Supported QR versions and data capacities
    - Error correction level recommendations
    - Interoperability with Electrum, Sparrow, BlueWallet, Specter
    - Cosigner xpub exchange format (JSON structure)

- [ ] **Step 6.7 — Backup & Recovery Guide**
  - [ ] Create `docs/backup_recovery.md`:
    - Backup creation procedure (step-by-step with screenshots)
    - Recommended backup schedule
    - Restore procedure on same Pi
    - Restore procedure on new Pi (from scratch)
    - Disaster recovery: lost Pi, corrupted SD, forgotten passphrase
    - Physical security for backup media (separate location, fireproof safe)

- [ ] **Step 6.8 — Final Integration Testing**
  - [ ] Full workflow test: generate wallet → derive addresses → sign PSBT via QR → display signed QR
  - [ ] Air-gap verification after running disable script and rebooting
  - [ ] Backup creation → restore → verify wallet data matches
  - [ ] Tamper detection: modify a src file → reboot → verify alert displayed
  - [ ] Multisig workflow: exchange xpubs between 2 cold wallets, sign same PSBT
  - [ ] Multi-coin: generate BTC, ETH, LTC addresses from same seed
  - [ ] E-ink display test (if HAT available)
  - [ ] Chunked QR test with large PSBT (>2953 bytes)
  - [ ] Verify dashboard bound to 127.0.0.1 only (cannot access from another device)

- [ ] **Step 6.9 — Finalize README**
  - [ ] Update quickstart with any changes from integration testing
  - [ ] Add screenshots of dashboard running on Pi display
  - [ ] Verify all `.env` variables documented
  - [ ] Verify all features described match implementation
  - [ ] Update troubleshooting table with real-world issues found during testing
