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

