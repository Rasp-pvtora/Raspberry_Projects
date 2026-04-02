# Technical Specification Document — Quantum-Resistant VPN

## 1. Scope

### In Scope

- WireGuard VPN tunnel on Raspberry Pi (kernel module + userspace tools)
- Post-quantum cryptography layer via liboqs (Open Quantum Safe)
- Hybrid key exchange: X25519 (classical) + ML-KEM-768/Kyber (post-quantum)
- Multiple PQC algorithm support (ML-KEM, ML-DSA/Dilithium, SPHINCS+)
- oqs-provider for OpenSSL 3.x integration
- PQC X.509 certificate generation and CA management
- Client configuration generation with QR codes (qrencode)
- Automatic key rotation (WireGuard PSK + PQC session keys)
- Performance benchmarking dashboard (handshake times, throughput, latency)
- Dark-themed Flask + SocketIO monitoring dashboard
- bcrypt authentication with rate limiting and session expiry
- SQLite for benchmark data and VPN status persistence
- All features toggled via `.env`
- Mock mode for development/testing without WireGuard or liboqs
- Deployment via rsync to `rasp-pi` (192.168.216.90)
- Threat model documenting "Harvest Now, Decrypt Later" attack

### Out of Scope

- Hardware quantum key distribution (QKD)
- Commercial VPN service or multi-tenant hosting
- Full Tor integration (separate project)
- Mobile app development (clients use standard WireGuard apps)
- Custom WireGuard kernel module patches
- Cloud or VPS deployment
- Automated trading or financial applications
- Quantum computing simulation or emulation

---

## 2. MVP Features (P0)

| ID | Feature | Priority |
|----|---------|----------|
| P0-1 | WireGuard tunnel setup (wg0 interface, server mode) | P0 |
| P0-2 | liboqs compiled from source for aarch64 | P0 |
| P0-3 | oqs-provider built and linked to OpenSSL 3.x | P0 |
| P0-4 | Hybrid key exchange: X25519 + ML-KEM-768 | P0 |
| P0-5 | PQC-enhanced WireGuard pre-shared key (PSK) generation | P0 |
| P0-6 | Flask dashboard (VPN status, connected clients, traffic) | P0 |
| P0-7 | SocketIO live updates (no page refresh) | P0 |
| P0-8 | bcrypt auth, rate limiting (10/15min), 24h session | P0 |
| P0-9 | SQLite database for status and benchmarks | P0 |
| P0-10 | Dark theme web UI | P0 |
| P0-11 | `.env` toggleable features | P0 |
| P0-12 | Mock mode (dev/test without running services) | P0 |
| P0-13 | Deploy script (rsync to rasp-pi) | P0 |
| P0-14 | Client config generation (wg0 peer configs) | P0 |

### Nice-to-Have (P1/P2)

| ID | Feature | Priority | Notes |
|----|---------|----------|-------|
| P1-1 | PQC X.509 certificate management (ML-DSA CA) | P1 | Full CA with server/client certs |
| P1-2 | QR code generation for client configs | P1 | Mobile-friendly setup |
| P1-3 | Automatic key rotation | P1 | Configurable interval (default 24h) |
| P1-4 | Performance benchmarking dashboard | P1 | Handshake times, throughput charts |
| P1-5 | Multiple PQC algorithm selection | P1 | ML-KEM-1024, ML-DSA-87, SPHINCS+ |
| P1-6 | Batch client generation | P1 | Generate N client configs at once |
| P2-1 | Historical benchmark trend charts | P2 | Track performance over time |
| P2-2 | Email/Telegram alerts | P2 | Tunnel down, cert expiry, key rotation |
| P2-3 | Prometheus/Grafana export | P2 | Advanced monitoring stack |
| P2-4 | Multi-site mesh VPN | P2 | Multiple Pis with PQC tunnels |

---

## 3. Database Schema

SQLite with WAL mode enabled. All timestamps stored as ISO-8601 UTC.

### Table: `vpn_status`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| interface | TEXT | NOT NULL, DEFAULT 'wg0' | WireGuard interface name |
| is_up | INTEGER | NOT NULL, DEFAULT 0 | 1 if tunnel is active |
| public_key | TEXT | | Server public key |
| listen_port | INTEGER | DEFAULT 51820 | WireGuard listen port |
| connected_peers | INTEGER | DEFAULT 0 | Number of connected clients |
| total_rx_bytes | INTEGER | DEFAULT 0 | Total bytes received |
| total_tx_bytes | INTEGER | DEFAULT 0 | Total bytes transmitted |
| latest_handshake | TEXT | | ISO-8601 timestamp of latest handshake |
| pqc_mode | TEXT | DEFAULT 'hybrid' | Active PQC mode (`hybrid`, `classical`, `pqc_only`) |
| kem_algorithm | TEXT | DEFAULT 'ML-KEM-768' | Active KEM algorithm |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp of this snapshot |

### Table: `peer_status`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| peer_name | TEXT | NOT NULL | Human-readable peer label |
| public_key | TEXT | NOT NULL | Peer WireGuard public key |
| allowed_ips | TEXT | NOT NULL | Peer AllowedIPs CIDR |
| endpoint | TEXT | | Peer endpoint (IP:port) |
| latest_handshake | TEXT | | ISO-8601 timestamp |
| rx_bytes | INTEGER | DEFAULT 0 | Bytes received from peer |
| tx_bytes | INTEGER | DEFAULT 0 | Bytes transmitted to peer |
| psk_rotated_at | TEXT | | Last PSK rotation timestamp |
| is_online | INTEGER | DEFAULT 0 | 1 if handshake within 3 minutes |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `benchmark_results`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| algorithm | TEXT | NOT NULL | Algorithm name (e.g., ML-KEM-768) |
| operation | TEXT | NOT NULL | Operation type (`keygen`, `encaps`, `decaps`, `sign`, `verify`) |
| iterations | INTEGER | NOT NULL | Number of iterations run |
| mean_us | REAL | NOT NULL | Mean time in microseconds |
| median_us | REAL | | Median time in microseconds |
| p99_us | REAL | | 99th percentile in microseconds |
| throughput_ops | REAL | | Operations per second |
| cpu_temp_c | REAL | | CPU temperature during benchmark |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `certificates`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| common_name | TEXT | NOT NULL | Certificate CN |
| cert_type | TEXT | NOT NULL | Type: `ca`, `server`, `client` |
| algorithm | TEXT | NOT NULL | Signing algorithm (e.g., ML-DSA-65) |
| serial_number | TEXT | UNIQUE | Certificate serial number |
| not_before | TEXT | NOT NULL | Validity start (ISO-8601) |
| not_after | TEXT | NOT NULL | Validity end (ISO-8601) |
| fingerprint_sha256 | TEXT | | SHA-256 fingerprint |
| cert_pem_path | TEXT | | Path to PEM certificate file |
| key_pem_path | TEXT | | Path to PEM private key file |
| is_revoked | INTEGER | DEFAULT 0 | 1 if certificate is revoked |
| created_at | TEXT | NOT NULL | ISO-8601 creation timestamp |

### Table: `system_metrics`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| cpu_percent | REAL | | CPU usage percentage |
| cpu_temp_c | REAL | | CPU temperature in Celsius |
| ram_used_mb | REAL | | RAM used in MB |
| ram_total_mb | REAL | | Total RAM in MB |
| disk_used_gb | REAL | | Disk used space in GB |
| disk_total_gb | REAL | | Disk total space in GB |
| net_rx_bytes_sec | REAL | | Network receive rate (bytes/sec) |
| net_tx_bytes_sec | REAL | | Network transmit rate (bytes/sec) |
| vpn_throughput_mbps | REAL | | VPN throughput in Mbps |
| uptime_seconds | INTEGER | | System uptime in seconds |
| recorded_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `key_rotation_log`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PK, AUTOINCREMENT | Unique record ID |
| peer_name | TEXT | NOT NULL | Peer that was rekeyed |
| old_psk_hash | TEXT | | SHA-256 of previous PSK (for audit) |
| new_psk_hash | TEXT | | SHA-256 of new PSK (for audit) |
| kem_algorithm | TEXT | | KEM algorithm used for key material |
| rotation_trigger | TEXT | | Trigger: `scheduled`, `manual`, `expiry` |
| success | INTEGER | NOT NULL | 1 if rotation succeeded |
| error_message | TEXT | | Error details if failed |
| rotated_at | TEXT | NOT NULL | ISO-8601 timestamp |

### Table: `settings`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | TEXT | PK | Setting name |
| value | TEXT | | Setting value (JSON-encoded) |
| updated_at | TEXT | NOT NULL | ISO-8601 last update time |

---

## 4. Environment Configuration (.env.default)

```bash
###############################################################################
# QUANTUM-RESISTANT VPN — ENVIRONMENT CONFIGURATION
# Copy to .env and customize before deployment
# All features are toggleable via ENABLE_* flags
###############################################################################

# ===========================================================================
# CORE SETTINGS
# ===========================================================================

# Flask session secret — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=CHANGE_ME

# Dashboard authentication
ADMIN_USERNAME=admin
# Generate: python3 -c "import bcrypt; print(bcrypt.hashpw(b'changeme', bcrypt.gensalt()).decode())"
ADMIN_PASSWORD_HASH=CHANGE_ME

# SQLite database path
DB_PATH=data/quantum_vpn.db

# Dashboard host and port
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Mock mode — run dashboard without WireGuard or liboqs installed
ENABLE_MOCK_MODE=false

# ===========================================================================
# WIREGUARD CONFIGURATION
# ===========================================================================

# WireGuard interface name
WG_INTERFACE=wg0

# Server listen port
WG_LISTEN_PORT=51820

# VPN subnet (server gets .1)
WG_SUBNET=10.66.66.0/24
WG_SERVER_IP=10.66.66.1

# Server endpoint (public IP or DDNS hostname for clients to connect)
WG_ENDPOINT=192.168.216.90

# DNS for VPN clients (Pi-hole, Cloudflare, etc.)
WG_DNS=1.1.1.1,1.0.0.1

# Network interface for NAT (iptables MASQUERADE)
WG_NAT_INTERFACE=eth0

# WireGuard config directory
WG_CONFIG_DIR=/etc/wireguard

# Persistent keepalive (seconds, 0 to disable)
WG_PERSISTENT_KEEPALIVE=25

# ===========================================================================
# POST-QUANTUM CRYPTOGRAPHY
# ===========================================================================

# Enable hybrid key exchange (X25519 + ML-KEM)
ENABLE_HYBRID_KEX=true

# Default KEM algorithm for key exchange
# Options: ML-KEM-512, ML-KEM-768, ML-KEM-1024
PQC_KEM_ALGORITHM=ML-KEM-768

# Default signature algorithm for certificates
# Options: ML-DSA-44, ML-DSA-65, ML-DSA-87, SPHINCS+-SHA2-128f, SPHINCS+-SHA2-256f
PQC_SIG_ALGORITHM=ML-DSA-65

# liboqs library path (compiled from source)
LIBOQS_LIB_PATH=/usr/local/lib

# oqs-provider path for OpenSSL 3.x
OQS_PROVIDER_PATH=/usr/local/lib/ossl-modules

# ===========================================================================
# PQC CERTIFICATE MANAGEMENT
# ===========================================================================

# Enable PQC X.509 certificate generation
ENABLE_PQC_CERTS=true

# CA certificate validity (days)
PQC_CA_VALIDITY_DAYS=3650

# Server/client certificate validity (days)
PQC_CERT_VALIDITY_DAYS=365

# CA common name
PQC_CA_CN=Quantum-Resistant VPN CA

# Certificate output directory
PQC_CERT_DIR=certs/

# ===========================================================================
# KEY ROTATION
# ===========================================================================

# Enable automatic key rotation
ENABLE_KEY_ROTATION=true

# Rotation interval in hours (default: 24)
KEY_ROTATION_INTERVAL_HOURS=24

# Grace period for old keys (minutes) — peers have this long to rekey
KEY_ROTATION_GRACE_MINUTES=5

# ===========================================================================
# CLIENT CONFIGURATION
# ===========================================================================

# Enable QR code generation for client configs
ENABLE_QR_CODES=true

# Client config output directory
CLIENT_CONFIG_DIR=clients/

# QR code image format (png, svg)
QR_FORMAT=png

# ===========================================================================
# PERFORMANCE BENCHMARKING
# ===========================================================================

# Enable PQC benchmark dashboard
ENABLE_BENCHMARK=true

# Number of iterations per benchmark run
BENCHMARK_ITERATIONS=1000

# Benchmark schedule (cron-like: run every N hours)
BENCHMARK_INTERVAL_HOURS=6

# Algorithms to benchmark (comma-separated)
BENCHMARK_ALGORITHMS=ML-KEM-512,ML-KEM-768,ML-KEM-1024,ML-DSA-44,ML-DSA-65,ML-DSA-87

# ===========================================================================
# MONITORING
# ===========================================================================

# System metrics collection interval (seconds)
METRICS_INTERVAL_SECONDS=30

# VPN status polling interval (seconds)
VPN_POLL_INTERVAL_SECONDS=10

# Retain metrics for N days (older records are purged)
METRICS_RETENTION_DAYS=30

# ===========================================================================
# DEPLOYMENT
# ===========================================================================

# Target Pi SSH alias (must match ~/.ssh/config)
DEPLOY_HOST=rasp-pi
DEPLOY_PATH=~/quantum-vpn
```

---

## 5. API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Login page |
| POST | `/login` | Authenticate (bcrypt, rate limited) |
| GET | `/logout` | End session |

### Dashboard Pages (auth required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main VPN status dashboard |
| GET | `/clients` | Client management & QR codes |
| GET | `/certs` | Certificate management |
| GET | `/benchmark` | PQC benchmark results |
| GET | `/settings` | Runtime settings |

### REST API (auth required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vpn/status` | Current VPN tunnel status |
| GET | `/api/vpn/peers` | Connected peer list with stats |
| POST | `/api/vpn/peers` | Add new peer |
| DELETE | `/api/vpn/peers/<name>` | Remove peer |
| GET | `/api/pqc/status` | Active PQC algorithms and mode |
| POST | `/api/pqc/rotate-keys` | Trigger manual key rotation |
| GET | `/api/benchmark/latest` | Latest benchmark results |
| POST | `/api/benchmark/run` | Trigger new benchmark run |
| GET | `/api/certs` | List all certificates |
| POST | `/api/certs/generate` | Generate new client certificate |
| POST | `/api/certs/revoke/<id>` | Revoke a certificate |
| GET | `/api/clients/<name>/config` | Download client WireGuard config |
| GET | `/api/clients/<name>/qr` | Get QR code image for client config |
| GET | `/api/system/metrics` | Current system metrics |
| GET | `/api/rotation/log` | Key rotation audit log |

### SocketIO Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `vpn_status` | Server → Client | VPN tunnel state, peer count, traffic |
| `peer_update` | Server → Client | Individual peer status change |
| `benchmark_progress` | Server → Client | Live benchmark progress (%) |
| `benchmark_result` | Server → Client | Completed benchmark data |
| `key_rotation` | Server → Client | Key rotation event notification |
| `system_metrics` | Server → Client | CPU, RAM, temp, throughput |
| `cert_expiry_warning` | Server → Client | Certificate approaching expiry |

---

## 6. PQC Algorithm Details

### Key Encapsulation Mechanisms (KEM)

| Algorithm | NIST Standard | Public Key | Ciphertext | Shared Secret | Security Level |
|-----------|---------------|------------|------------|---------------|----------------|
| ML-KEM-512 | FIPS 203 | 800 B | 768 B | 32 B | NIST Level 1 (AES-128) |
| ML-KEM-768 | FIPS 203 | 1184 B | 1088 B | 32 B | NIST Level 3 (AES-192) |
| ML-KEM-1024 | FIPS 203 | 1568 B | 1568 B | 32 B | NIST Level 5 (AES-256) |

### Digital Signature Algorithms

| Algorithm | NIST Standard | Public Key | Signature | Security Level |
|-----------|---------------|------------|-----------|----------------|
| ML-DSA-44 | FIPS 204 | 1312 B | 2420 B | NIST Level 2 |
| ML-DSA-65 | FIPS 204 | 1952 B | 3293 B | NIST Level 3 |
| ML-DSA-87 | FIPS 204 | 2592 B | 4595 B | NIST Level 5 |
| SLH-DSA-SHA2-128f | FIPS 205 | 32 B | 17088 B | NIST Level 1 |
| SLH-DSA-SHA2-256f | FIPS 205 | 64 B | 49856 B | NIST Level 5 |

### Hybrid Key Exchange Flow

```
Client                                    Server
  │                                         │
  │──── X25519 public key ────────────────►│
  │──── ML-KEM-768 encaps public key ─────►│
  │                                         │
  │                              X25519 ECDH ──► ss_classical
  │                              ML-KEM decaps ──► ss_pqc
  │                                         │
  │◄──── X25519 public key ────────────────│
  │◄──── ML-KEM-768 ciphertext ────────────│
  │                                         │
  │  X25519 ECDH ──► ss_classical          │
  │  ML-KEM decaps ──► ss_pqc             │
  │                                         │
  │  combined = HKDF(ss_classical ‖ ss_pqc) │
  │  WireGuard PSK = combined[:32]         │
  │                                         │
  │◄════ Encrypted WireGuard Tunnel ══════►│
  │      (ChaCha20-Poly1305 + hybrid PSK)  │
```

---

## 7. Security Considerations

### Threat Model Summary

| Threat | Mitigation |
|--------|------------|
| Harvest Now, Decrypt Later | Hybrid PQC key exchange — even captured traffic is quantum-resistant |
| Classical ECDH compromise | ML-KEM-768 provides independent quantum-resistant shared secret |
| PQC algorithm weakness | X25519 provides fallback classical security |
| Key compromise | Automatic rotation every 24h limits exposure window |
| Brute-force dashboard auth | bcrypt (cost 12) + rate limiting (10/15min) |
| Session hijacking | 24h expiry, secure cookie flags, CSRF tokens |
| Man-in-the-middle | PQC X.509 certificates for mutual authentication |
| Side-channel attacks on PQC | liboqs implements constant-time operations |

### Key Storage

- WireGuard private keys: `/etc/wireguard/` with `chmod 600`
- PQC CA private key: `certs/ca.key` with `chmod 600`
- All key material generated from `/dev/urandom` via `os.urandom()`
- Pre-shared keys are never logged — only SHA-256 hashes stored for audit

---

## 8. Performance Expectations (Raspberry Pi 4)

| Operation | Algorithm | Expected Latency |
|-----------|-----------|------------------|
| Key generation | ML-KEM-768 | ~0.1 ms |
| Encapsulation | ML-KEM-768 | ~0.2 ms |
| Decapsulation | ML-KEM-768 | ~0.2 ms |
| Key generation | ML-DSA-65 | ~0.5 ms |
| Sign | ML-DSA-65 | ~1.5 ms |
| Verify | ML-DSA-65 | ~0.5 ms |
| Hybrid handshake | X25519 + ML-KEM-768 | ~1–2 ms total |
| VPN throughput | WireGuard + hybrid PSK | ~150–300 Mbps (Pi 4 Ethernet) |

> **Note:** PQC overhead on handshake is negligible (~1ms). Steady-state throughput is unaffected because ChaCha20-Poly1305 symmetric encryption is unchanged — only the key exchange gains PQC protection.
