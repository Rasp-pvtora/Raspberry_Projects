# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for `01-EncDecript_File_with_SecurityKeys`.

1. Scope
--------

This project provides a secure toolset to encrypt and decrypt files where the data encryption keys (DEKs) are protected (wrapped) by a hardware-backed key-encryption key (KEK) stored on a hardware security token (e.g., YubiKey or PKCS#11-compatible HSM). The initial deliverable runs on a laptop in software-only mode for development and testing. Later the project is deployed to a Raspberry Pi where a physical hardware key is used.

2. Minimum Viable Features (MVP)
--------------------------------

Each MVP feature includes a deeper explanation and rationale.

- CLI: `encrypt`, `decrypt`, `provision`, `list-keys`.
  - `encrypt`: generates a random DEK for the target file, encrypts the file with AEAD, wraps the DEK with the KEK (or mock adapter), and writes an output file plus metadata (wrapped DEK, nonce, algorithm, version).
  - `decrypt`: loads the metadata, unwraps the DEK via the hardware adapter (or mock), decrypts the file, and writes plaintext output. Decryption operations should zero sensitive buffers as soon as possible.
  - `provision`: initialize a key entry in the keystore. In software-only mode this creates a locally wrapped KEK (for testing); in hardware mode it instructs the token to generate or import a KEK.
  - `list-keys`: enumerate available wrapped keys and metadata.

- Software-only encryption core:
  - Use a secure AEAD primitive (AES-GCM with 256-bit key or ChaCha20-Poly1305) to encrypt file contents. The library must include safe streaming for large files (chunking) to avoid loading large files fully into memory. Metadata must include algorithm, nonce(s), tag, and version information.

- Hardware key adapter abstraction:
  - Define an interface `IHardwareKey` with `wrap_key`, `unwrap_key`, `generate_key` (optional), and `identify()` methods. Provide a `mock_hwkey` implementation for local testing (non-secure, deterministic) which allows development without a physical token.

- Keystore (wrapped key storage):
  - A small JSON/YAML keystore that stores wrapped DEKs/KEKs and metadata (creation timestamp, key id, usage policy). The keystore file must be protected by file system permissions and optionally encrypted with a user passphrase in addition to hardware wrapping.

- Tests:
  - Unit tests for cryptographic correctness (encrypt/decrypt roundtrip), adapter mock tests, and CLI functional tests.

3. Nice-to-Have Features (detailed)
----------------------------------

- Secure file shredding after decrypt (optional):
  - When requested, overwrite on-disk plaintext with multiple passes or platform-appropriate secure-delete APIs before removing files. Document platform limitations (TRIM, SSD wear-leveling make guaranteed secure deletion impossible on some storage).

- Folder watcher / auto-encrypt daemon:
  - A small background service (or systemd unit on Pi) that watches a directory and automatically encrypts new files according to a policy. Useful for protecting exported documents. The daemon must handle partial files, backoff for transient errors, and maintain an operation log.

- User profiles and policies:
  - Support multiple key profiles (work, personal), with policy templates controlling default algorithms, whether to use per-file vs per-folder DEKs, and key rotation schedules.

- GUI or TUI client:
  - A minimal cross-platform GUI (e.g., TUI using `Textual` or a small Tkinter/Qt window) to help non-CLI users encrypt/decrypt files and manage the keystore.

- Cloud backup of wrapped keys (encrypted):
  - Optionally allow uploading wrapped keys to a private cloud or S3 bucket. Keys must remain wrapped with a KEK that is never exported; use envelope encryption and require multi-factor protection for the backup account.

4. High-level Architecture
-------------------------

Components:

- CLI layer (`src/enc_decrypt/cli.py`): Parses arguments, performs user interaction, and calls into the service/API layer.
- Crypto core (`src/enc_decrypt/crypto_core.py`): Implements AEAD file encryption/decryption, streaming encryption for large files, and metadata serialization.
- Hardware adapter (`src/enc_decrypt/hwkey/`): Provides `IHardwareKey` interface and implementations: `mock_hwkey.py` (for development) and later `pkcs11_adapter.py` / `yubikey_adapter.py`.
- Keystore (`src/enc_decrypt/store.py`): Manages wrapped key entries on disk, enforces file permissions, and provides import/export.
- Tests (`tests/`): Unit and integration tests using the `mock_hwkey`.

Data flow example (encrypt):

1. CLI receives `encrypt` command and input/output paths.
2. Crypto core generates a DEK (per-file) and encrypts the file using AEAD with streaming.
3. The DEK is wrapped using the configured `IHardwareKey` adapter (mock or real).
4. Write ciphertext file and sidecar metadata containing wrapped DEK, nonce, algorithm, and version.

5. Security and Threat Model (detailed)
-------------------------------------

Primary assets:

- Plaintext file contents (confidentiality requirement).
- DEKs (short-lived symmetric keys used for file encryption).
- KEKs (hardware-backed private keys or device-protected keys).

Threats and mitigations:

- Lost or stolen laptop:
  - Mitigation: encrypted files are unreadable without the KEK; DEKs are wrapped. Require presence of the hardware token and optionally a passphrase to unwrap.

- Compromised OS (malware):
  - Mitigation: cannot fully prevent an OS-level attacker from capturing plaintext while a user decrypts files on that host. Minimize exposure by reducing plaintext lifetime, avoiding automatic decryption into persistent system locations, and offering an option to decrypt to RAM-backed volumes when available.

- Stolen hardware token:
  - Mitigation: require an additional user factor (PIN/passphrase) for token use where supported. Use token features that protect against unauthorized use (touch-confirmation, PIN). Document token loss recovery steps and key rotation.

- Replay or tampering of ciphertext/metadata:
  - Mitigation: use AEAD to detect tampering; include versioning and integrity checks in metadata.

- Backup leakage of wrapped keys:
  - Mitigation: backups must store only wrapped keys; if a wrapped key is leaked, it is still protected by the KEK on the hardware token. Consider tying backups to an account protected by MFA.

Operational guidance:

- Keep tokens physically secure and remove them when not needed.
- Use strong passphrases for any optional passphrase-protection on the keystore.
- Educate users about host compromise risks — decrypt only on trusted machines when possible.

6. Suggested Tech Stack & Libraries
----------------------------------

- Language: Python 3.11+.
- Crypto: `cryptography` (hazmat APIs for AEAD and secure primitives). Consider `libsodium`/`pynacl` for ChaCha20-Poly1305 if desired.
- CLI: `click` for user-friendly command line interface.
- PKCS#11 / token integration: `python-pkcs11` or call `ykman`/`ykman` subprocess for YubiKey workflows; on Linux the `opensc` stack can be used if needed.
- Testing: `pytest`.
- Formatting & linting: `black`, `ruff`.

7. Development Phases & Concrete Steps
------------------------------------

Phase A — Repository setup & MVP (weeks 0–2)

1. Scaffold repository, create `pyproject.toml`, `requirements.txt`, and initial package layout. (Done)
2. Implement the crypto core with AEAD streaming and tests for small and large files.
3. Implement the CLI commands `encrypt` and `decrypt` wired to the software-only core.
4. Add `mock_hwkey` adapter and a simple keystore format for wrapped keys.

Phase B — Hardware adapter & integration (weeks 2–4)

1. Implement `IHardwareKey` adapter for PKCS#11 or YubiKey. Start with a simple command-line integration using `ykman` or `python-pkcs11`.
2. Update `provision` command to use hardware token to generate or import KEKs.
3. Add integration tests that run only when a hardware token is available (skip otherwise).

Phase C — Hardening, packaging & deployment (weeks 4–6)

1. Add keystore passphrase option (optional) and tighten file permissions.
2. Implement secure-delete options with platform caveats documented.
3. Add Raspberry Pi deployment scripts (SSH-copy, package installation) and test on Pi.
4. Configure CI to run tests and static analysis on push to private repo.

Phase D — Optional features & polish

1. Folder-watcher daemon, GUI/TUI client, cloud backup integration.
2. Add monitoring and usage metrics (opt-in) and extended documentation.

8. Deliverables for initial iteration
------------------------------------

- Working CLI with `encrypt`/`decrypt` (software-only) and unit tests.
- `mock_hwkey` adapter and small keystore implementation.
- `TSD.md`, `docs/threat_model.md`, updated `README.md`.

9. Open questions for the user
----------------------------

- Preferred hardware tokens to support first (YubiKey, Nitrokey, PKCS#11 HSM)?
- Do you want per-file DEKs or a per-directory DEK policy by default?
- Any corporate compliance constraints (FIPS, export controls) to consider now?

Answering these will help prioritize adapter and algorithm choices.
 # 01-EncDecript_File_with_SecurityKeys

 Purpose
 -------

 This repository is a prototype for encrypting and decrypting files using a hardware security key (HSM/token). It is designed to be developed and tested on a laptop (software-only mode) and later deployed to a Raspberry Pi for hardware integration.

 Quickstart (development)
 ------------------------

 1. Create and activate a virtual environment:

 ```bash
 python -m venv .venv
 .venv\Scripts\activate    # Windows
 # or: source .venv/bin/activate  # macOS / Linux
 ```

 2. Install dependencies:

 ```bash
 pip install -r requirements.txt
 ```

 3. Run the CLI (placeholders until core implemented):

 ```bash
 python -m src.enc_decrypt.cli encrypt --input secret.txt --output secret.txt.enc
 python -m src.enc_decrypt.cli decrypt --input secret.txt.enc --output secret.txt
 ```

 Project structure
 -----------------

 - `README.md` — this file.
 - `TSD.md` — Technical Specification Description (scope, architecture, requirements).
 - `docs/threat_model.md` — concise threat model and mitigations.
 - `pyproject.toml`, `requirements.txt` — dependencies and packaging.
 - `src/enc_decrypt/` — source package: CLI, `crypto_core`, `hwkey` adapters.
 - `tests/` — unit/integration tests.

 Goals and Project Phases
 ------------------------

 The project progresses in two main phases:

 - Phase 1 (Laptop/testing): implement a secure software-only core (AES-GCM or ChaCha20-Poly1305), a `mock_hwkey` adapter, a CLI, and unit tests.
 - Phase 2 (Hardware integration): add a real hardware-key adapter (PKCS#11/YubiKey), secure keystore, Raspberry Pi deployment scripts, and integration tests.

 Security notes
 --------------

 - The project uses authenticated encryption for confidentiality and integrity.
 - Keys are ephemeral in memory as much as possible; DEKs are wrapped by KEKs that remain private on the hardware token.
 - Never commit secrets or keystore files to version control. Follow `docs/threat_model.md` for detailed guidance.

 Contributing
 ------------

 Open issues for feature requests or bugs. Follow standard PR workflow and ensure tests pass before merging.

 Where to next
 -------------

 - See [TSD.md](TSD.md) for a detailed technical specification.
 - See [docs/threat_model.md](docs/threat_model.md) for the threat model and security assumptions.

