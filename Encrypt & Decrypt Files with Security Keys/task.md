# Project Task Reference

This file is the single-source checklist for the engineering team: what has been done and what remains. Use the checkboxes to track progress; update as tasks are completed.

## Completed

- [x] Create repo skeleton and project structure
  - [x] `README.md` (quickstart and links)
  - [x] `pyproject.toml` / `requirements.txt`
  - [x] `.gitignore`
  - [x] repository layout: `src/enc_decrypt/`, `tests/`, `docs/`, `deploy/`, `.github/workflows/`
- [x] Draft threat model and requirements
  - [x] `docs/threat_model.md`
  - [x] `TSD.md` (technical specification description)
- [x] Implement software-only encryption/decryption CLI (laptop testing)
  - [x] `src/enc_decrypt/crypto_core.py` (AES-GCM per-file encrypt/decrypt)
  - [x] `src/enc_decrypt/cli.py` — commands: `encrypt`, `decrypt`, `provision`, `list-keys`, `rotate`
  - [x] Keystore format via `src/enc_decrypt/store.py` (replaces raw metadata sidecar)
- [x] Add hardware security key abstraction with mock for laptop
  - [x] `src/enc_decrypt/hwkey/base.py` — `IHardwareKey` abstract interface
  - [x] `src/enc_decrypt/hwkey/mock_hwkey.py` — mock wrap/unwrap (development only)
  - [x] `src/enc_decrypt/hwkey/__init__.py` — exports `IHardwareKey`, `MockHardwareKey`
- [x] Implement key provisioning, wrapping, and secure storage (keystore)
  - [x] `src/enc_decrypt/store.py`: `store_key`, `load_key`, `get_wrapped_dek`, `list_keys`, `rotate_key`, `delete_key`
  - [x] File permissions hardening (chmod 600 POSIX / icacls on Windows)
  - [x] `provision` CLI command (register new key slot)
  - [x] `rotate` CLI command (re-wrap DEK, update store)
  - [x] `list-keys` CLI command (tabular keystore overview)
- [x] Add tests, linting, CI pipeline
  - [x] `tests/conftest.py` — shared fixtures including `original_document` and `keystore_path`
  - [x] `tests/test_crypto.py` — encrypt/decrypt roundtrip, tamper detection, wrong key
  - [x] `tests/test_mock_hwkey.py` — mock adapter interface compliance, wrap/unwrap
  - [x] `tests/test_store.py` — store, load, rotate, delete, duplicate detection
  - [x] `tests/test_cli.py` — end-to-end CLI tests with `original_document.txt`
  - [x] `tests/test_import.py` — smoke import checks for all modules
  - [x] Linting: `ruff` configured in `pyproject.toml`
  - [x] Formatting: `black` configured in `pyproject.toml`
  - [x] CI: `.github/workflows/ci.yml` (test + security audit with `pip-audit`)
  - [x] **40 / 40 tests passing** (Python 3.13)
- [x] Write documentation, README, usage examples
  - [x] `README.md` updated with quickstart and links
  - [x] `TSD.md` — full technical spec

## Remaining / Future (Phase 2+)

- [ ] Add real hardware adapter (PKCS#11 / YubiKey)
  - [ ] `src/enc_decrypt/hwkey/pkcs11_adapter.py`
  - [ ] Integration test that skips when no token is present
  - [ ] `provision` command wired to physical token key generation/import
- [ ] Create Raspberry Pi deployment scripts (SSH-copy)
  - [x] `deploy/deploy_to_pi.sh` — rsync + remote pip install + smoke test
  - [ ] Test on real Raspberry Pi hardware
  - [ ] Optional: `systemd` unit file for watcher daemon
- [ ] Publish to private Git repository
  - [ ] `git init` / `git remote add origin <url>` and first push
- [ ] Optional features: GUI, file watcher, secure deletion
  - [ ] Folder watcher daemon (auto-encrypt based on directory policy)
  - [ ] GUI/TUI client (e.g. `Textual`) for non-CLI users
  - [ ] Secure-delete/shred after decrypt with platform caveats documented
  - [ ] Cloud backup of wrapped keys (envelope encryption, MFA-protected)

## How to run current prototype (developer)

1. Create venv and install dependencies:

```bash
py -3 -m venv .venv
.venv\Scripts\activate    # Windows
# or: source .venv/bin/activate  # macOS / Linux / Raspberry Pi
pip install -r requirements.txt
```

2. Encrypt `tests/original_document.txt`:

```bash
python -m src.enc_decrypt.cli encrypt \
    --input tests/original_document.txt \
    --output tests/original_document.txt.enc \
    --key-id doc-key --use-mock
```

3. Decrypt back:

```bash
python -m src.enc_decrypt.cli decrypt \
    --input tests/original_document.txt.enc \
    --output tests/original_document.txt.dec \
    --key-id doc-key --use-mock
```

4. List keys in keystore:

```bash
python -m src.enc_decrypt.cli list-keys
```

5. Run tests:

```bash
pytest
```

## Ownership suggestions

- Core crypto & CLI: Backend engineer (Python, cryptography)
- Hardware adapter & provisioning: Security engineer (PKCS#11, YubiKey)
- Tests and CI: DevOps / SRE

## Notes

- Do not commit keystore files, secrets, raw DEKs, or `*.enc` files into VCS.
- `mock_hwkey` is **development-only**; real adapters must ensure KEKs are non-exportable.
- The default keystore lives at `~/.enc_decrypt/keystore.json` with owner-only permissions.
