# Implementation Plan
## Quantum-Resistant VPN

---

## Executive Summary

Configure a WireGuard VPN tunnel on a Raspberry Pi, then layer it with post-quantum cryptographic algorithms using liboqs (Open Quantum Safe). The result is a hybrid VPN: classical (X25519) + PQC (ML-KEM-768/Kyber) for key exchange, protecting against "Harvest Now, Decrypt Later" attacks. A Flask + SocketIO dark-themed dashboard monitors VPN status, PQC benchmarks, certificates, and connected clients. All features are `.env` toggleable.

**Budget:** ~$0 (software only) | **Timeline:** 5–7 days

---

## Phase 1: Foundation (Day 1 — Morning)

### 1.1 OS & Network Setup
| Step | Action | Duration |
|------|--------|----------|
| 1 | Flash Pi OS 64-bit (Bookworm) with SSH enabled | 10 min |
| 2 | Connect Ethernet, boot, SSH via `ssh rasp-pi` | 5 min |
| 3 | Full system update: `sudo apt update && sudo apt upgrade -y` | 10 min |
| 4 | Install build tools: `sudo apt install build-essential cmake gcc ninja-build git libssl-dev` | 5 min |

### 1.2 Enable IP Forwarding
```bash
# Required for VPN routing
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Verify
cat /proc/sys/net/ipv4/ip_forward
# Expect: 1
```

### 1.3 Firewall Configuration
```bash
sudo ufw allow 22/tcp       # SSH
sudo ufw allow 51820/udp    # WireGuard
sudo ufw allow 5000/tcp     # Dashboard
sudo ufw enable
```

**Milestone:** Pi ready with build tools, IP forwarding, and firewall configured.

---

## Phase 2: WireGuard Installation (Day 1 — Afternoon)

### 2.1 Install WireGuard
```bash
sudo apt install wireguard wireguard-tools -y

# Verify kernel module
sudo modprobe wireguard
lsmod | grep wireguard
```

### 2.2 Generate Server Keys
```bash
cd /etc/wireguard
umask 077
wg genkey | tee server.key | wg pubkey > server.pub
```

### 2.3 Configure WireGuard Server
```bash
# Generate wg0.conf from .env template or manually create:
cat > /etc/wireguard/wg0.conf << 'EOF'
[Interface]
PrivateKey = <contents of server.key>
Address = 10.66.66.1/24
ListenPort = 51820
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Peers added dynamically via dashboard or manually
EOF
```

### 2.4 Start & Verify
```bash
sudo wg-quick up wg0
sudo wg show wg0

# Expect:
# interface: wg0
#   public key: <server_pubkey>
#   listening port: 51820
```

### 2.5 Enable Auto-Start
```bash
sudo systemctl enable wg-quick@wg0
```

**Milestone:** WireGuard tunnel running on the Pi with classical encryption.

---

## Phase 3: Build liboqs from Source (Day 2 — Morning)

### 3.1 Clone & Build
```bash
cd ~
git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git
cd liboqs
mkdir build && cd build

# Configure with all algorithms enabled
cmake -GNinja \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -DBUILD_SHARED_LIBS=ON \
  -DOQS_BUILD_ONLY_LIB=OFF \
  ..

# Build (takes ~10 min on Pi 4, ~5 min on Pi 5)
ninja

# Test (optional but recommended — takes ~5 min)
ninja run_tests
```

### 3.2 Install
```bash
sudo ninja install
sudo ldconfig

# Verify
ls /usr/local/lib/liboqs*
# Expect: liboqs.so, liboqs.so.x.x.x
```

### 3.3 Install Python Bindings
```bash
pip install liboqs-python

# Verify
python3 -c "
import oqs
print('KEM mechanisms:', len(oqs.get_enabled_kem_mechanisms()))
print('Sig mechanisms:', len(oqs.get_enabled_sig_mechanisms()))
print('ML-KEM-768 available:', 'ML-KEM-768' in oqs.get_enabled_kem_mechanisms())
"
```

**Milestone:** liboqs installed with ML-KEM, ML-DSA, and SPHINCS+ algorithms available.

---

## Phase 4: Build oqs-provider for OpenSSL 3.x (Day 2 — Afternoon)

### 4.1 Verify OpenSSL Version
```bash
openssl version
# Must be OpenSSL 3.x (Pi OS Bookworm ships 3.0.x)

# Find modules directory
openssl version -m
# Note the MODULESDIR path
```

### 4.2 Clone & Build oqs-provider
```bash
cd ~
git clone --depth 1 https://github.com/open-quantum-safe/oqs-provider.git
cd oqs-provider
mkdir build && cd build

cmake -GNinja \
  -Dliboqs_DIR=/usr/local/lib/cmake/liboqs \
  ..

ninja
```

### 4.3 Install Provider
```bash
# Copy provider to OpenSSL modules directory
MODULES_DIR=$(openssl version -m | grep -oP '(?<=\").*(?=\")')
sudo cp lib/oqsprovider.so "$MODULES_DIR/"

# OR if path detection fails:
sudo cp lib/oqsprovider.so /usr/lib/aarch64-linux-gnu/ossl-modules/
```

### 4.4 Configure OpenSSL
```bash
# Add to /etc/ssl/openssl.cnf (or project-local config):
# Under [openssl_init]:
#   providers = provider_sect
#
# [provider_sect]
# default = default_sect
# oqsprovider = oqsprovider_sect
#
# [default_sect]
# activate = 1
#
# [oqsprovider_sect]
# activate = 1
# module = /usr/lib/aarch64-linux-gnu/ossl-modules/oqsprovider.so
```

### 4.5 Verify PQC Algorithms Available
```bash
# KEM algorithms
openssl list -kem-algorithms | grep -i "ml-kem\|kyber"

# Signature algorithms
openssl list -signature-algorithms | grep -i "ml-dsa\|dilithium\|sphincs"

# Quick test — generate ML-DSA key
openssl genpkey -algorithm mldsa65 -out test_mldsa.key
openssl pkey -in test_mldsa.key -pubout -out test_mldsa.pub
rm test_mldsa.key test_mldsa.pub
```

**Milestone:** OpenSSL 3.x can use PQC algorithms via oqs-provider. Ready for certificate generation.

---

## Phase 5: Python Dashboard Setup (Day 3)

### 5.1 Python Environment
```bash
cd ~/quantum-vpn
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2 Dashboard Configuration
```bash
# Generate Flask secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Set as SECRET_KEY in .env

# Generate admin password hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt()).decode())"
# Set as ADMIN_PASSWORD_HASH in .env
```

### 5.3 Initialize & Start
```bash
# Configure .env
cp .env.example .env
nano .env

# Initialize SQLite database
python3 -c "from src.database import init_db; init_db()"

# Start dashboard
python -m src.app
# Access at http://192.168.216.90:5000
```

### 5.4 Verify Dashboard
1. Browse to `http://192.168.216.90:5000`
2. Login with admin credentials
3. Verify dark theme
4. Check live SocketIO updates:
   - WireGuard tunnel status (up/down)
   - Connected peers
   - Traffic counters (RX/TX bytes)
5. Verify system metrics (CPU, RAM, disk, temp)

**Milestone:** Dashboard running with WireGuard monitoring.

---

## Phase 6: Hybrid Key Exchange Implementation (Day 4)

### 6.1 Implement PQC Engine (`src/pqc_engine.py`)
```python
# Wrapper around liboqs for KEM operations:
# - keygen(algorithm) → (public_key, secret_key)
# - encapsulate(algorithm, public_key) → (ciphertext, shared_secret)
# - decapsulate(algorithm, secret_key, ciphertext) → shared_secret
```

### 6.2 Implement Hybrid KEX (`src/hybrid_kex.py`)
```python
# Combined key exchange:
# 1. X25519 ECDH → ss_classical (32 bytes)
# 2. ML-KEM-768 encaps/decaps → ss_pqc (32 bytes)
# 3. combined = HKDF-SHA256(ss_classical || ss_pqc, info="hybrid-vpn-psk")
# 4. WireGuard PSK = combined[:32]
```

### 6.3 Inject PQC PSK into WireGuard
```bash
# The hybrid shared secret becomes the WireGuard PresharedKey.
# WireGuard's PresharedKey field adds an additional layer of symmetric
# key material to the Noise protocol handshake.

# Set per-peer PSK:
sudo wg set wg0 peer <peer_pubkey> preshared-key <(echo $HYBRID_PSK)
```

### 6.4 Verify Hybrid Handshake
```bash
# Check WireGuard shows preshared key in use:
sudo wg show wg0
# Expect: "preshared key: (hidden)" for each peer

# Test connectivity through tunnel:
ping -c 5 10.66.66.2  # from server to client
```

**Milestone:** WireGuard tunnel protected by hybrid X25519 + ML-KEM-768 key exchange.

---

## Phase 7: PQC Certificate Management (Day 5 — Morning)

### 7.1 Generate PQC CA
```bash
# Using oqs-provider via OpenSSL:
openssl genpkey -algorithm mldsa65 -out certs/ca.key
chmod 600 certs/ca.key

openssl req -x509 -new -key certs/ca.key \
  -out certs/ca.pem \
  -days 3650 \
  -subj "/CN=Quantum-Resistant VPN CA/O=HomeLab"
```

### 7.2 Generate Server Certificate
```bash
openssl genpkey -algorithm mldsa65 -out certs/server.key
chmod 600 certs/server.key

openssl req -new -key certs/server.key \
  -out certs/server.csr \
  -subj "/CN=vpn.local/O=HomeLab"

openssl x509 -req -in certs/server.csr \
  -CA certs/ca.pem -CAkey certs/ca.key \
  -CAcreateserial -out certs/server.pem -days 365
```

### 7.3 Verify Certificate Chain
```bash
openssl verify -CAfile certs/ca.pem certs/server.pem
# Expect: certs/server.pem: OK

openssl x509 -in certs/server.pem -noout -text | head -20
# Expect: Signature Algorithm: mldsa65
```

### 7.4 Dashboard Integration
- Certificate listing with expiry dates
- One-click client cert generation
- Revocation support via CRL

**Milestone:** PQC Certificate Authority operational with ML-DSA-65 signed certificates.

---

## Phase 8: Client Config & QR Codes (Day 5 — Afternoon)

### 8.1 Client Config Generation
```bash
# Install qrencode
sudo apt install qrencode -y

# Generate client keypair
wg genkey | tee clients/client1.key | wg pubkey > clients/client1.pub

# Generate client config from template
python3 -c "
from src.client_gen import generate_client_config
generate_client_config('client1', '10.66.66.2/32')
"
```

### 8.2 QR Code Generation
```bash
# Generate QR code from config
qrencode -t png -o clients/client1.png -r clients/client1.conf

# Or from dashboard: GET /api/clients/client1/qr
```

### 8.3 Client-Side Setup
1. Install WireGuard on client device (phone, laptop, second Pi)
2. Scan QR code or import `.conf` file
3. Connect — verify tunnel establishes
4. Check dashboard shows peer as connected

**Milestone:** Clients can connect via QR code with PQC-enhanced WireGuard configs.

---

## Phase 9: Automatic Key Rotation (Day 6 — Morning)

### 9.1 Implement Key Rotation (`src/key_rotation.py`)
```python
# Rotation flow:
# 1. Generate fresh ML-KEM-768 key pair
# 2. Exchange with each peer (via side channel or dashboard)
# 3. Derive new hybrid PSK
# 4. Apply via: wg set wg0 peer <key> preshared-key <new_psk>
# 5. Log rotation to key_rotation_log table
# 6. Old PSK is discarded (only hash stored for audit)
```

### 9.2 Configure Schedule
```bash
# In .env:
ENABLE_KEY_ROTATION=true
KEY_ROTATION_INTERVAL_HOURS=24
KEY_ROTATION_GRACE_MINUTES=5
```

### 9.3 Test Rotation
```bash
# Set short interval for testing
# KEY_ROTATION_INTERVAL_HOURS=0.02  (≈ 1 minute)

# Watch rotation in dashboard
# Verify tunnel stays up during rotation
# Check key_rotation_log for entries
```

**Milestone:** Keys rotate automatically every 24 hours with zero-downtime rekeying.

---

## Phase 10: Performance Benchmarking (Day 6 — Afternoon)

### 10.1 Implement Benchmarks (`src/benchmark.py`)
```python
# For each algorithm in BENCHMARK_ALGORITHMS:
#   1. Run keygen × BENCHMARK_ITERATIONS
#   2. Run encaps/sign × BENCHMARK_ITERATIONS
#   3. Run decaps/verify × BENCHMARK_ITERATIONS
#   4. Record mean, median, p99 latency
#   5. Record CPU temperature during benchmark
#   6. Store results in benchmark_results table
```

### 10.2 Throughput Measurement
```bash
# Install iperf3 on server and client Pi
sudo apt install iperf3 -y

# Server (on VPN Pi):
iperf3 -s -B 10.66.66.1

# Client (on second Pi):
iperf3 -c 10.66.66.1 -t 30

# Compare:
# 1. Direct Ethernet (no VPN)
# 2. WireGuard (classical only)
# 3. WireGuard + hybrid PQC PSK
```

### 10.3 Dashboard Charts
- Bar chart: algorithm comparison (keygen, encaps, decaps latency)
- Line chart: historical handshake times
- Gauge: current VPN throughput
- Table: detailed benchmark results with p99 latency

**Milestone:** PQC performance benchmarked and visualized on dashboard.

---

## Phase 11: systemd Services & Production (Day 7)

### 11.1 Dashboard Service
```ini
# /etc/systemd/system/quantum-vpn-dashboard.service
[Unit]
Description=Quantum-Resistant VPN Dashboard
After=network.target wg-quick@wg0.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/quantum-vpn
Environment=PATH=/home/pi/quantum-vpn/.venv/bin:/usr/bin
ExecStart=/home/pi/quantum-vpn/.venv/bin/python -m src.app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 11.2 Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now quantum-vpn-dashboard
sudo systemctl enable --now wg-quick@wg0

# Verify
sudo systemctl status quantum-vpn-dashboard
sudo systemctl status wg-quick@wg0
```

### 11.3 Final Validation
```bash
# Full reboot test
sudo reboot

# After reboot, verify:
sudo wg show wg0                    # Tunnel is up
curl http://localhost:5000/login     # Dashboard is running
sudo systemctl status quantum-vpn-dashboard  # Service active
```

**Milestone:** Production-ready. VPN and dashboard survive reboots.

---

## Phase 12: Testing & Documentation (Day 7 — Afternoon)

### 12.1 Run Test Suite
```bash
source .venv/bin/activate
pytest tests/ -v --tb=short

# Expected:
# test_pqc_engine.py      — PASSED (keygen, encaps, decaps)
# test_hybrid_kex.py      — PASSED (combined secret derivation)
# test_cert_manager.py    — PASSED (CA, server, client certs)
# test_client_gen.py      — PASSED (config generation, QR)
# test_key_rotation.py    — PASSED (rotation logic, logging)
# test_benchmark.py       — PASSED (result collection)
# test_auth.py            — PASSED (login, rate limit, session)
# test_api.py             — PASSED (all REST endpoints)
# test_database.py        — PASSED (CRUD operations)
```

### 12.2 End-to-End Test (Optional — requires second Pi)
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Generate client config with QR code | Config file + QR image created |
| 2 | Import config on second Pi / phone | WireGuard peer configured |
| 3 | Connect client to VPN | Handshake completes, traffic flows |
| 4 | Check dashboard | New peer shows as connected |
| 5 | Trigger key rotation | Tunnel stays up, new PSK applied |
| 6 | Run iperf3 through tunnel | Throughput within expected range |
| 7 | Verify PQC mode on dashboard | Shows "Hybrid: X25519 + ML-KEM-768" |

### 12.3 Deploy
```bash
# From development machine:
cd deploy/
bash deploy_to_pi.sh

# On Pi:
sudo systemctl restart quantum-vpn-dashboard
sudo systemctl restart wg-quick@wg0
```

**Milestone:** Project complete. Quantum-resistant VPN operational with hybrid PQC key exchange.

---

## Summary

| Phase | Description | Day |
|-------|-------------|-----|
| 1 | OS & network preparation | Day 1 AM |
| 2 | WireGuard installation | Day 1 PM |
| 3 | Build liboqs from source | Day 2 AM |
| 4 | Build oqs-provider for OpenSSL 3.x | Day 2 PM |
| 5 | Python dashboard setup | Day 3 |
| 6 | Hybrid key exchange implementation | Day 4 |
| 7 | PQC certificate management | Day 5 AM |
| 8 | Client config & QR codes | Day 5 PM |
| 9 | Automatic key rotation | Day 6 AM |
| 10 | Performance benchmarking | Day 6 PM |
| 11 | systemd services & production | Day 7 AM |
| 12 | Testing & documentation | Day 7 PM |
