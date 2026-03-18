# Encrypt & Decrypt Files with Security Keys

A secure Python CLI tool to encrypt and decrypt files using per-file AES-GCM keys protected by a hardware security key adapter. Runs on laptop (software-only / mock mode) and on Raspberry Pi.

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Quickstart — Laptop (development)](#quickstart--laptop-development)
3. [How keys are generated and managed](#how-keys-are-generated-and-managed)
4. [Sharing encrypted files using a key file](#sharing-encrypted-files-using-a-key-file)
5. [How to create a passwordless SSH setup](#how-to-create-a-passwordless-ssh-setup)
6. [How to deploy the project to Raspberry Pi](#how-to-deploy-the-project-to-raspberry-pi)
7. [How to run on the Raspberry Pi](#how-to-run-on-the-raspberry-pi)
8. [Full CLI reference](#full-cli-reference)
9. [Security notes](#security-notes)
10. [Where to next](#where-to-next)

---

## Project structure

```
.
├── src/enc_decrypt/
│   ├── cli.py          ← CLI entrypoint (all commands)
│   ├── crypto_core.py  ← AES-GCM file encryption / decryption
│   ├── store.py        ← Keystore (wrapped-key persistence)
│   └── hwkey/
│       ├── base.py         ← IHardwareKey abstract interface
│       ├── mock_hwkey.py   ← Software mock adapter (development only)
│       └── __init__.py
├── tests/
│   ├── original_document.txt   ← Sample file for testing
│   └── test_*.py
├── deploy/
│   └── deploy_to_pi.sh  ← rsync-based deploy script
├── docs/
│   └── threat_model.md
├── TSD.md              ← Technical Specification
├── task.md             ← Engineering checklist
├── pyproject.toml
└── requirements.txt
```

---

## Quickstart — Laptop (development)

**1. Clone the repository**

```bash
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/Encrypt & Decrypt Files with Security Keys"
```

**2. Create a virtual environment and install dependencies**

```bash
# Windows
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Encrypt a file**

```bash
python -m src.enc_decrypt.cli encrypt \
    --input  tests/original_document.txt \
    --output tests/original_document.txt.enc \
    --key-id my-doc-key \
    --use-mock
```

**4. Decrypt a file**

```bash
python -m src.enc_decrypt.cli decrypt \
    --input  tests/original_document.txt.enc \
    --output tests/original_document.txt.dec \
    --key-id my-doc-key \
    --use-mock
```

**5. Run tests**

```bash
pytest
```

---

## How keys are generated and managed

You do **not** create a key manually before encrypting.  
The `encrypt` command manages everything automatically:

1. **A random 256-bit DEK (Data Encryption Key) is generated in memory** for that specific file.
2. **The file is encrypted** using AES-GCM with that DEK.
3. **The DEK is wrapped (protected)** by the hardware adapter (`--use-mock` during development, a real hardware token later). The wrapped DEK is stored in the keystore at `~/.enc_decrypt/keystore.json`. The raw DEK is never written to disk.
4. **`--key-id`** is the name you assign to that key slot (e.g. `my-doc-key`). It links the ciphertext file to its stored key.
5. **To decrypt**, the CLI looks up `my-doc-key` in the keystore, unwraps the DEK using the same adapter, and decrypts the file. You never handle the raw key bytes directly.

```
Encrypt:  plaintext ──[AES-GCM + DEK]──► ciphertext
                            │
                       [adapter.wrap]
                            │
                     keystore[key-id] = wrapped_DEK

Decrypt:  ciphertext ──[AES-GCM + DEK]──► plaintext
                              ▲
                        [adapter.unwrap]
                              │
                       keystore[key-id]
```

You can encrypt **any file** — just change `--input`, `--output`, and `--key-id`:

```bash
python -m src.enc_decrypt.cli encrypt \
    --input  /path/to/myfile.pdf \
    --output /path/to/myfile.pdf.enc \
    --key-id myfile-key \
    --use-mock
```

---

## Sharing encrypted files using a key file

A common use case: send the encrypted file by email and deliver the key separately on a USB stick so only the intended recipient can open it.

**Step 1 — Encrypt the file and export its key**

```bash
# Encrypt
python -m src.enc_decrypt.cli encrypt \
    --input  contract.pdf \
    --output contract.pdf.enc \
    --key-id contract-key \
    --use-mock

# Export the key to a portable file
python -m src.enc_decrypt.cli export-key \
    --key-id contract-key \
    --output contract.key \
    --use-mock
```

- Send `contract.pdf.enc` by email (or any channel).
- Copy `contract.key` onto a USB stick and hand it to the recipient physically.

**Step 2 — Recipient decrypts using only the key file**

The recipient does **not need a keystore** — they use `--key-file` directly:

```bash
python -m src.enc_decrypt.cli decrypt \
    --input    contract.pdf.enc \
    --output   contract.pdf \
    --key-file contract.key
```

> **Security warning:** The `.key` file contains the raw encryption key in base64.
> Protect it like a password. Do not send it through the same channel as the encrypted file.

**Optional — Import the key file into your own keystore**

```bash
python -m src.enc_decrypt.cli import-key \
    --key-file contract.key \
    --key-id   contract-received \
    --use-mock
```

---

## How to create a passwordless SSH setup

This is required before you can deploy to the Raspberry Pi from your laptop without entering a password every time.

**On your laptop (Windows with Git Bash, WSL, or PowerShell with OpenSSH):**

**1. Generate an SSH key pair (if you do not have one already)**

```bash
ssh-keygen -t ed25519 -C "your-label"
# Accept the default path (~/.ssh/id_ed25519)
# Leave passphrase empty for fully passwordless, or set one for extra security
```

This creates two files:
- `~/.ssh/id_ed25519` — your **private** key (never share this)
- `~/.ssh/id_ed25519.pub` — your **public** key (safe to copy anywhere)

**2. Copy the public key to the Raspberry Pi**

```bash
# From Linux / macOS / WSL / Git Bash:
ssh-copy-id pi@192.168.x.x

# From Windows PowerShell (manual equivalent):
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh pi@192.168.x.x "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

**3. Create an SSH config alias (optional but recommended)**

Edit `~/.ssh/config` (create if missing):

```
Host rasp-pi
    HostName 192.168.x.x
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

Now you can connect with just:

```bash
ssh rasp-pi
```

**4. Test the connection**

```bash
ssh rasp-pi "echo SSH OK"
```

You should see `SSH OK` without being asked for a password.

---

## How to deploy the project to Raspberry Pi

There are two methods:

### Method A — Clone directly from GitHub on the Pi (requires Pi internet access)

SSH into the Pi and run:

```bash
ssh rasp-pi
mkdir -p /home/pi/Projects
cd /home/pi/Projects
git clone https://github.com/Rasp-pvtora/Raspberry_Projects.git
cd "Raspberry_Projects/Smart & Security Projects/Encrypt & Decrypt Files with Security Keys"
pip3 install --user cryptography click
python3 -m src.enc_decrypt.cli --help
```

To update later when the Pi has internet:

```bash
cd /home/pi/Projects/Raspberry_Projects
git pull origin main
```

### Method B — Copy from laptop via SCP (no Pi internet needed)

From your laptop, in the project directory:

```bash
# Create the folder on the Pi
ssh rasp-pi "mkdir -p /home/pi/Projects/01-EncDecript_File_with_SecurityKeys"

# Copy files (rsync preferred, excludes venv and cache)
rsync -avz --delete \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache/' \
  ./ \
  rasp-pi:/home/pi/Projects/01-EncDecript_File_with_SecurityKeys/

# OR use the included deploy script (from project root):
bash deploy/deploy_to_pi.sh pi rasp-pi /home/pi/Projects/01-EncDecript_File_with_SecurityKeys
```

Then install dependencies on the Pi:

```bash
ssh rasp-pi "pip3 install --user cryptography click"
```

---

## How to run on the Raspberry Pi

**1. SSH into the Pi**

```bash
ssh rasp-pi
```

**2. Go to the project directory**

```bash
cd /home/pi/Projects/01-EncDecript_File_with_SecurityKeys
```

**3. Encrypt a file**

```bash
python3 -m src.enc_decrypt.cli encrypt \
    --input  tests/original_document.txt \
    --output tests/original_document.txt.enc \
    --key-id my-key \
    --use-mock
```

**4. Decrypt a file**

```bash
python3 -m src.enc_decrypt.cli decrypt \
    --input  tests/original_document.txt.enc \
    --output tests/original_document.txt.dec \
    --key-id my-key \
    --use-mock
```

**5. Export a key to a file (USB sharing)**

```bash
python3 -m src.enc_decrypt.cli export-key \
    --key-id my-key \
    --output my-key.key \
    --use-mock
```

**6. Decrypt using a key file (no keystore)**

```bash
python3 -m src.enc_decrypt.cli decrypt \
    --input    tests/original_document.txt.enc \
    --output   tests/original_document.txt.dec \
    --key-file my-key.key
```

**7. List all keys in the keystore**

```bash
python3 -m src.enc_decrypt.cli list-keys
```

---

## Full CLI reference

| Command | Description |
|---|---|
| `encrypt` | Encrypt a file; generate and store a DEK in the keystore |
| `decrypt` | Decrypt a file via `--key-id` (keystore) or `--key-file` (portable key) |
| `export-key` | Export a DEK from the keystore to a portable `.key` file |
| `import-key` | Import a `.key` file into the local keystore |
| `provision` | Register a new named key slot in the keystore |
| `list-keys` | List all key-ids with creation time and adapter |
| `rotate` | Replace the DEK for an existing key slot with a new one |

Common options:

| Option | Description |
|---|---|
| `--use-mock` | Use the software mock adapter (development / no hardware token) |
| `--key-id NAME` | Logical name for the key in the keystore |
| `--key-file PATH` | Path to an exported `.key` file |
| `--store PATH` | Override the default keystore path (`~/.enc_decrypt/keystore.json`) |

---

## Security notes

- The default keystore lives at `~/.enc_decrypt/keystore.json` with owner-only file permissions (`chmod 600`).
- `--use-mock` is **development only**. The mock adapter does not protect keys cryptographically; it is a stand-in for a real hardware token (YubiKey, PKCS#11 HSM).
- Exported `.key` files contain the raw DEK in base64. Treat them like passwords. Never transmit the key file and the encrypted file through the same channel.
- See [docs/threat_model.md](docs/threat_model.md) and [TSD.md](TSD.md) for the full security analysis.

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture diagram, and development phases.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model and mitigations.
- See [task.md](task.md) for the engineering checklist.

