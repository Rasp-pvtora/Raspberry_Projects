# Quantum-Resistant VPN

<div align="center">

![WireGuard](https://img.shields.io/badge/WireGuard-VPN-88171A?style=for-the-badge&logo=wireguard&logoColor=white)
![Post-Quantum](https://img.shields.io/badge/Post--Quantum-ML--KEM%20%2F%20Kyber-7B2D8B?style=for-the-badge&logo=quantcast&logoColor=white)
![liboqs](https://img.shields.io/badge/liboqs-Open_Quantum_Safe-0078D4?style=for-the-badge)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-4%2F5-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Configure a WireGuard VPN tunnel on the Pi, then layer it with post-quantum cryptographic algorithms using liboqs (Open Quantum Safe). Creates a hybrid VPN: classical (X25519) + PQC (ML-KEM/Kyber) for key exchange. Protects against "Harvest Now, Decrypt Later" attacks where adversaries capture encrypted traffic today to decrypt with future quantum computers.**

[Features](#features) • [Threat Model](#threat-model--harvest-now-decrypt-later) • [Hardware](#hardware-requirements) • [Quick Start](#quick-start) • [Configuration](#environment-configuration) • [Dashboard](#monitoring-dashboard) • [Troubleshooting](#troubleshooting)

</div>

---

**If you find this project useful, consider supporting development:**

**BTC:** `bc1q...`

---

## Table of Contents

- [Threat Model — Harvest Now, Decrypt Later](#threat-model--harvest-now-decrypt-later)
- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Libraries & Dependencies](#libraries--dependencies)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [System Overview](#system-overview)
- [Features](#features)
  - [Hybrid Key Exchange (X25519 + ML-KEM-768)](#hybrid-key-exchange-x25519--ml-kem-768)
  - [Multiple PQC Algorithms](#multiple-pqc-algorithms)
  - [oqs-provider for OpenSSL 3.x](#oqs-provider-for-openssl-3x)
  - [PQC X.509 Certificate Management](#pqc-x509-certificate-management)
  - [Client Config Generation with QR Codes](#client-config-generation-with-qr-codes)
  - [Automatic Key Rotation](#automatic-key-rotation)
  - [Performance Benchmarking Dashboard](#performance-benchmarking-dashboard)
  - [WireGuard Integration](#wireguard-integration)
  - [Flask Monitoring Dashboard](#flask-monitoring-dashboard)
- [Authentication](#authentication)
- [Deployment](#deployment)
- [Running the Service](#running-the-service)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Threat Model — Harvest Now, Decrypt Later

> **This is the primary motivation for this project.**

### The Attack

Nation-state adversaries and advanced persistent threats (APTs) are **recording encrypted VPN traffic today** — even though they cannot decrypt it with current classical computers. The strategy is simple:

1. **Harvest** — Capture and store encrypted traffic at ISP taps, submarine cable intercepts, or compromised network infrastructure.
2. **Wait** — Store the encrypted data for 5–15+ years.
3. **Decrypt Later** — Once a sufficiently powerful quantum computer exists, use Shor's algorithm to break the classical key exchange (ECDH/X25519) and retroactively decrypt **all** stored traffic.

### Why This Matters Now

| Factor | Detail |
|--------|--------|
| **NIST PQC standards finalized** | ML-KEM (Kyber), ML-DSA (Dilithium), SLH-DSA (SPHINCS+) standardized in 2024 |
| **Quantum timeline** | Cryptographically relevant quantum computers estimated 2030–2040 |
| **Data shelf life** | Medical records, financial data, state secrets remain sensitive for decades |
| **Storage is cheap** | Storing petabytes of encrypted traffic costs adversaries very little |
| **Retroactive exposure** | Traffic captured today cannot be "un-captured" — once recorded, it's forever at risk |

### The Defense — Hybrid PQC

This project implements **hybrid key exchange**: every VPN handshake uses **both** classical X25519 **and** post-quantum ML-KEM-768 (Kyber). The combined shared secret ensures:

- If quantum computers **never** arrive → X25519 alone keeps you safe (proven security).
- If quantum computers **do** arrive → ML-KEM-768 keeps you safe (quantum-resistant).
- An attacker must break **both** algorithms simultaneously to compromise the session.

**Even traffic captured today is protected against future quantum decryption.**

### Who Should Care

- Journalists and activists communicating under hostile regimes
- Healthcare organizations transmitting HIPAA-protected data
- Financial institutions with long-lived transaction records
- Legal firms exchanging privileged communications
- Anyone whose encrypted traffic needs to remain confidential for 10+ years

---

## Project Structure

```
Quantum-Resistant VPN/
├── README.md                    # This file
├── TSD.md                      # Technical Specification Document
├── task.md                     # Development task checklist
├── implementation_plan.md      # Phased implementation guide
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
├── .env.example                # Environment variable template
├── src/
│   ├── __init__.py
│   ├── app.py                  # Flask app factory & SocketIO init
│   ├── wireguard.py            # WireGuard tunnel management
│   ├── pqc_engine.py           # liboqs / oqs-provider integration
│   ├── hybrid_kex.py           # Hybrid key exchange (X25519 + ML-KEM)
│   ├── cert_manager.py         # PQC X.509 certificate generation
│   ├── key_rotation.py         # Automatic key rotation scheduler
│   ├── client_gen.py           # Client config generator + QR codes
│   ├── benchmark.py            # PQC performance benchmarking
│   ├── monitor.py              # System monitor (CPU, RAM, temp, throughput)
│   ├── database.py             # SQLite DB models & helpers
│   ├── auth.py                 # bcrypt auth & session management
│   ├── config.py               # .env loader & config dataclass
│   └── utils.py                # Shared utilities
├── templates/
│   ├── base.html               # Dark theme layout
│   ├── login.html              # Login page
│   ├── dashboard.html          # Main VPN monitoring dashboard
│   ├── clients.html            # Client management & QR codes
│   ├── certs.html              # Certificate management page
│   ├── benchmark.html          # PQC benchmark results
│   └── settings.html           # Runtime settings panel
├── static/
│   ├── css/
│   │   └── style.css           # Dark theme styles
│   └── js/
│       ├── dashboard.js        # SocketIO client & live status
│       ├── benchmark.js        # Benchmark chart rendering
│       └── clients.js          # Client config & QR interaction
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures & mock mode helpers
│   ├── test_wireguard.py       # WireGuard management tests
│   ├── test_pqc_engine.py      # liboqs integration tests
│   ├── test_hybrid_kex.py      # Hybrid key exchange tests
│   ├── test_cert_manager.py    # Certificate management tests
│   ├── test_key_rotation.py    # Key rotation tests
│   ├── test_client_gen.py      # Client config generation tests
│   ├── test_benchmark.py       # Benchmark accuracy tests
│   ├── test_auth.py            # Auth & session tests
│   ├── test_api.py             # Dashboard API endpoint tests
│   └── test_database.py        # Database CRUD tests
├── deploy/
│   └── deploy_to_pi.sh         # rsync deploy script (rasp-pi)
├── scripts/
│   ├── install_liboqs.sh       # Build liboqs from source
│   ├── install_oqs_provider.sh # Build oqs-provider for OpenSSL 3.x
│   ├── install_wireguard.sh    # WireGuard kernel module & tools
│   ├── install_deps.sh         # OS-level dependency installer
│   ├── generate_password_hash.sh # Helper to generate bcrypt hash
│   └── rotate_keys.sh          # Manual key rotation trigger
├── config/
│   ├── wg0.conf.template       # WireGuard server config template
│   ├── client.conf.template    # WireGuard client config template
│   ├── openssl_oqs.cnf.template # OpenSSL config with oqs-provider
│   └── pqc_ca.cnf.template     # PQC CA certificate config
└── docs/
    ├── threat_model.md          # Detailed HNDL threat model
    ├── pqc_algorithms.md        # Algorithm comparison & selection guide
    ├── benchmark_guide.md       # Interpreting performance results
    └── client_setup.md          # Client-side VPN setup instructions
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4GB+) / Pi 5 | Yes | PQC runs in software — Pi 5 recommended for better benchmarks |
| MicroSD card (32GB+) | Yes | OS + project files |
| Ethernet cable | Yes | Reliable VPN tunnel requires wired connection |
| Power supply (5V/3A+) | Yes | Official Pi PSU |
| Secondary Pi (optional) | No | Useful as VPN client for end-to-end testing |

> **No extra hardware required.** All post-quantum cryptography runs in software via liboqs. The Pi's ARM CPU handles ML-KEM-768 key encapsulation in ~1ms.

---

## Budget

| Item | Estimated Cost |
|---|---|
| liboqs + oqs-provider | Free (open source) |
| WireGuard | Free (in-kernel) |
| All software dependencies | Free |
| **Total** | **~$0** |

*(Assumes you already own a Raspberry Pi 4/5 with power supply and Ethernet cable.)*

---

## Libraries & Dependencies

| Library | Purpose |
|---|---|
| Flask | Monitoring dashboard web framework |
| Flask-SocketIO | Real-time WebSocket for live VPN status |
| liboqs | Post-quantum cryptographic algorithms (compiled from source) |
| oqs-provider | OpenSSL 3.x provider for PQC algorithms |
| wireguard-tools | WireGuard tunnel management (`wg`, `wg-quick`) |
| qrencode | QR code generation for client configs |
| bcrypt | Password hashing for dashboard auth |
| python-dotenv | `.env` configuration loading |
| Jinja2 | HTML template rendering (included with Flask) |
| eventlet / gevent | Async worker for SocketIO |
| psutil | System resource monitoring (CPU, RAM, disk, temp) |

---

## Quick Start

```bash
# 1. SSH into the Pi
ssh rasp-pi          # alias for pi@192.168.216.90

# 2. Clone the repo
git clone <repo-url> ~/quantum-vpn && cd ~/quantum-vpn

# 3. Install OS-level dependencies
sudo bash scripts/install_deps.sh

# 4. Build liboqs from source
sudo bash scripts/install_liboqs.sh

# 5. Build oqs-provider for OpenSSL 3.x
sudo bash scripts/install_oqs_provider.sh

# 6. Install WireGuard
sudo bash scripts/install_wireguard.sh

# 7. Set up Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 8. Configure environment
cp .env.example .env
nano .env              # Set VPN subnet, toggle PQC features

# 9. Generate admin password hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())"
# Set as ADMIN_PASSWORD_HASH in .env

# 10. Generate PQC certificates
python3 -c "from src.cert_manager import generate_ca; generate_ca()"

# 11. Initialize database & start dashboard
python3 -c "from src.database import init_db; init_db()"
python -m src.app
# Access at http://192.168.216.90:5000

# 12. Start WireGuard tunnel
sudo wg-quick up wg0
```

---

## Environment Configuration

See [TSD.md — §4 Environment Configuration](TSD.md#4-environment-configuration-envdefault) for the full `.env.default` block with all toggleable features.

Key toggles:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_HYBRID_KEX` | `true` | X25519 + ML-KEM-768 hybrid key exchange |
| `ENABLE_PQC_CERTS` | `true` | PQC X.509 certificate generation |
| `ENABLE_KEY_ROTATION` | `true` | Automatic key rotation |
| `ENABLE_BENCHMARK` | `true` | Performance benchmarking dashboard |
| `ENABLE_QR_CODES` | `true` | QR code generation for client configs |
| `ENABLE_MOCK_MODE` | `false` | Development/testing without WireGuard |

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     VPN Client                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ WireGuard Client + Hybrid PQC Key Exchange          │    │
│  │ X25519 ──────┐                                      │    │
│  │              ├──► Combined Shared Secret ──► Tunnel  │    │
│  │ ML-KEM-768 ──┘                                      │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Encrypted Tunnel (ChaCha20-Poly1305)
                       │ + PQC-protected key exchange
┌──────────────────────▼──────────────────────────────────────┐
│                 Raspberry Pi VPN Server                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │  WireGuard       │  │  liboqs /         │  │  oqs-     │  │
│  │  Kernel Module   │  │  PQC Engine       │  │  provider │  │
│  │  (wg0 interface) │  │  ML-KEM, ML-DSA   │  │  OpenSSL  │  │
│  └────────┬────────┘  │  SPHINCS+          │  │  3.x      │  │
│           │           └──────────┬─────────┘  └─────┬─────┘  │
│           │                      │                   │        │
│  ┌────────▼──────────────────────▼───────────────────▼─────┐ │
│  │              Flask + SocketIO Dashboard                   │ │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐ │ │
│  │  │ VPN      │ │ Benchmark │ │ Cert     │ │ Client    │ │ │
│  │  │ Status   │ │ Results   │ │ Manager  │ │ Generator │ │ │
│  │  └──────────┘ └───────────┘ └──────────┘ └───────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Features

### Hybrid Key Exchange (X25519 + ML-KEM-768)

Every VPN handshake combines a classical X25519 ECDH key exchange with a post-quantum ML-KEM-768 (Kyber) key encapsulation. The shared secrets from both are combined via HKDF, ensuring security even if one algorithm is compromised. This is the NIST-recommended hybrid approach for the PQC transition period.

### Multiple PQC Algorithms

| Algorithm | Type | Use Case | NIST Standard |
|-----------|------|----------|---------------|
| ML-KEM-768 (Kyber) | KEM | Key exchange (primary) | FIPS 203 |
| ML-KEM-1024 (Kyber) | KEM | Key exchange (high security) | FIPS 203 |
| ML-DSA-65 (Dilithium) | Signature | Certificate signing | FIPS 204 |
| ML-DSA-87 (Dilithium) | Signature | Certificate signing (high security) | FIPS 204 |
| SLH-DSA (SPHINCS+) | Signature | Stateless hash-based signatures | FIPS 205 |

### oqs-provider for OpenSSL 3.x

The oqs-provider integrates liboqs algorithms directly into OpenSSL 3.x. This enables standard OpenSSL commands (`openssl genpkey`, `openssl req`, `openssl s_server`) to use PQC algorithms transparently. No application-level changes needed for TLS.

### PQC X.509 Certificate Management

Generate X.509 certificates signed with post-quantum algorithms (ML-DSA / Dilithium). Includes a PQC Certificate Authority (CA) for issuing server and client certificates. Supports hybrid certificates that chain classical + PQC signatures.

### Client Config Generation with QR Codes

Auto-generate WireGuard client configurations with PQC parameters. Each config is rendered as a scannable QR code for easy mobile setup. Supports batch generation for multiple clients.

### Automatic Key Rotation

Configurable key rotation schedule (default: every 24 hours). Rotates both WireGuard pre-shared keys and PQC session keys. Zero-downtime rotation with graceful rekeying.

### Performance Benchmarking Dashboard

Real-time benchmarking of PQC algorithms on the Pi's ARM CPU:
- Handshake times (classical vs. hybrid vs. pure PQC)
- Throughput impact (MB/s with and without PQC layer)
- Key generation speed per algorithm
- Encapsulation / decapsulation latency
- Historical trend charts

### WireGuard Integration

Integrates with the standard WireGuard kernel module. The PQC layer sits above WireGuard, enhancing the pre-shared key (PSK) mechanism with quantum-resistant key material. Existing WireGuard clients continue to work — PQC is an additive security layer.

### Flask Monitoring Dashboard

Dark-themed web dashboard at `http://192.168.216.90:5000`:
- VPN tunnel status (up/down, connected clients, traffic)
- PQC algorithm status and active key exchange mode
- Benchmark results with charts
- Certificate expiry tracking
- Client management with QR code display
- System metrics (CPU, RAM, temp, throughput)
- SocketIO live updates — no page refresh

---

## Authentication

- **bcrypt** password hashing (cost factor 12)
- **Rate limiting:** 10 failed attempts per 15-minute window
- **Session expiry:** 24 hours
- **Single admin user** (configurable via `.env`)
- **CSRF protection** on all forms
- Login page inherits dark theme

---

## Deployment

```bash
# From development machine — deploy to Pi
cd deploy/
bash deploy_to_pi.sh

# The script runs:
# rsync -avz --exclude '.venv' --exclude '__pycache__' \
#   . rasp-pi:~/quantum-vpn/
```

---

## Running the Service

```bash
# Start WireGuard tunnel
sudo wg-quick up wg0

# Start dashboard (development)
source .venv/bin/activate
python -m src.app

# Or via systemd (production)
sudo systemctl enable --now quantum-vpn-dashboard
sudo systemctl enable --now wg-quick@wg0
```

---

## Security Notes

- **Hybrid mode is mandatory by default** — pure classical mode requires explicit opt-in via `ENABLE_HYBRID_KEX=false`
- PQC algorithms are compiled from source (liboqs) — no binary blobs
- All pre-shared keys are generated from `/dev/urandom` via `os.urandom()`
- Certificate private keys are stored with `chmod 600`
- Dashboard binds to `0.0.0.0` by default — restrict with `DASHBOARD_HOST` in `.env`
- WireGuard uses `AllowedIPs` to restrict tunnel traffic
- Rate limiting prevents brute-force attacks on dashboard auth
- Key rotation minimizes exposure window for any single compromised key

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `liboqs` build fails | Ensure `cmake`, `gcc`, `ninja-build` installed: `sudo apt install cmake gcc ninja-build` |
| `oqs-provider` not found by OpenSSL | Check `OPENSSL_MODULES` path: `openssl version -m` — provider `.so` must be in that directory |
| WireGuard `wg0` not starting | Check `sudo wg show` — verify keys generated, check `dmesg` for kernel module errors |
| Handshake timeout | Verify UDP port 51820 forwarded on router, check firewall: `sudo ufw allow 51820/udp` |
| Slow PQC benchmarks | Expected on Pi 4 — ML-KEM-768 ~1ms, ML-DSA-65 ~5ms. Pi 5 is ~2x faster |
| QR code not rendering | Install `qrencode`: `sudo apt install qrencode` |
| Python `import oqs` fails | Ensure liboqs installed to system path or set `LD_LIBRARY_PATH=/usr/local/lib` |
| Dashboard login fails | Regenerate bcrypt hash, check `ADMIN_PASSWORD_HASH` in `.env` — hash must start with `$2b$` |

---

## Where to Next

- **Extend with Tor routing** — Route VPN traffic through Tor for additional anonymity
- **Multi-site mesh** — Connect multiple Pis with PQC-protected WireGuard tunnels
- **Hardware security module** — Store PQC private keys on a USB HSM
- **Quantum key distribution (QKD)** — Future integration when affordable QKD hardware ships
- **NIST algorithm updates** — Monitor for new PQC algorithm selections and update liboqs accordingly
