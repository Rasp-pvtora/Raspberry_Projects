# Task Tracker
## Quantum-Resistant VPN

---

## Phase 1: OS & Network Preparation
- [ ] Flash Raspberry Pi OS 64-bit (Bookworm) to SD card
- [ ] Enable SSH, set hostname, configure Ethernet
- [ ] Boot Pi and connect via `ssh rasp-pi` (192.168.216.90)
- [ ] Run `sudo apt update && sudo apt upgrade -y`
- [ ] Install build essentials: `sudo apt install build-essential cmake gcc ninja-build git`
- [ ] Install OpenSSL 3.x development headers: `sudo apt install libssl-dev`
- [ ] Verify OpenSSL version: `openssl version` (must be 3.x)
- [ ] Enable IP forwarding: `echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p`
- [ ] Configure firewall: `sudo ufw allow 51820/udp && sudo ufw allow 5000/tcp`

## Phase 2: WireGuard Installation
- [ ] Install WireGuard: `sudo apt install wireguard wireguard-tools`
- [ ] Verify kernel module: `sudo modprobe wireguard && lsmod | grep wireguard`
- [ ] Generate server keypair: `wg genkey | tee server.key | wg pubkey > server.pub`
- [ ] Set key permissions: `chmod 600 server.key`
- [ ] Create WireGuard config directory: `sudo mkdir -p /etc/wireguard`
- [ ] Generate `wg0.conf` from `.env` template
- [ ] Start WireGuard tunnel: `sudo wg-quick up wg0`
- [ ] Verify tunnel: `sudo wg show wg0`
- [ ] Test connectivity: `ping 10.66.66.1` from client
- [ ] Configure NAT: `iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE`

## Phase 3: Build liboqs from Source
- [ ] Install dependencies: `sudo apt install astyle cmake gcc ninja-build libssl-dev python3-pytest`
- [ ] Clone liboqs: `git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git`
- [ ] Create build directory: `cd liboqs && mkdir build && cd build`
- [ ] Configure: `cmake -GNinja -DCMAKE_INSTALL_PREFIX=/usr/local ..`
- [ ] Build: `ninja`
- [ ] Run tests: `ninja run_tests` (verify ML-KEM, ML-DSA, SPHINCS+ pass)
- [ ] Install: `sudo ninja install && sudo ldconfig`
- [ ] Verify installation: `ls /usr/local/lib/liboqs*`
- [ ] Test Python binding: `python3 -c "import oqs; print(oqs.get_enabled_kem_mechanisms())"`

## Phase 4: Build oqs-provider for OpenSSL 3.x
- [ ] Clone oqs-provider: `git clone --depth 1 https://github.com/open-quantum-safe/oqs-provider.git`
- [ ] Build: `cd oqs-provider && mkdir build && cd build && cmake -GNinja .. && ninja`
- [ ] Install provider .so to OpenSSL modules directory
- [ ] Determine modules path: `openssl version -m`
- [ ] Copy: `sudo cp oqsprov.so /usr/lib/aarch64-linux-gnu/ossl-modules/`
- [ ] Configure OpenSSL: add `oqs-provider` to `openssl.cnf`
- [ ] Verify: `openssl list -kem-algorithms | grep -i kyber`
- [ ] Verify: `openssl list -signature-algorithms | grep -i dilithium`

## Phase 5: Python Environment & Dashboard Setup
- [ ] Install Python 3 and venv: `sudo apt install python3-venv python3-pip`
- [ ] Create venv: `python3 -m venv .venv && source .venv/bin/activate`
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env` and configure
- [ ] Generate Flask `SECRET_KEY` and set in `.env`
- [ ] Generate bcrypt password hash for dashboard admin
- [ ] Set `ADMIN_PASSWORD_HASH` in `.env`
- [ ] Initialize SQLite database
- [ ] Start dashboard: `python -m src.app`
- [ ] Access dashboard at `http://192.168.216.90:5000`
- [ ] Login and verify dark theme
- [ ] Verify SocketIO live updates (VPN status, peer count)
- [ ] Verify system metrics (CPU, RAM, disk, temp)

## Phase 6: Hybrid Key Exchange Implementation
- [ ] Implement `pqc_engine.py` — liboqs wrapper for KEM operations
- [ ] Implement `hybrid_kex.py` — X25519 + ML-KEM combined key exchange
- [ ] Test ML-KEM-768 keygen / encaps / decaps roundtrip
- [ ] Test combined shared secret derivation via HKDF
- [ ] Generate PQC-enhanced pre-shared key for WireGuard
- [ ] Inject PQC PSK into `wg0.conf` (PresharedKey field)
- [ ] Verify WireGuard tunnel still works with hybrid PSK
- [ ] Test handshake with and without PQC — compare latency
- [ ] Add PQC mode indicator to dashboard

## Phase 7: PQC Certificate Management (ENABLE_PQC_CERTS=true)
- [ ] Implement `cert_manager.py` — PQC CA and certificate generation
- [ ] Generate CA keypair with ML-DSA-65 via oqs-provider
- [ ] Generate self-signed CA certificate (PQC X.509)
- [ ] Generate server certificate signed by PQC CA
- [ ] Generate client certificate signed by PQC CA
- [ ] Verify certificate chain: `openssl verify -CAfile ca.pem server.pem`
- [ ] Add certificate listing to dashboard (certs page)
- [ ] Add certificate expiry tracking
- [ ] Add certificate revocation support
- [ ] Store certificate metadata in SQLite

## Phase 8: Client Config Generation (ENABLE_QR_CODES=true)
- [ ] Implement `client_gen.py` — client config template rendering
- [ ] Install qrencode: `sudo apt install qrencode`
- [ ] Generate WireGuard client config from template
- [ ] Include PQC-enhanced PSK in client config
- [ ] Generate QR code from client config
- [ ] Add client management page to dashboard
- [ ] Add QR code display on dashboard
- [ ] Test scanning QR code with WireGuard mobile app
- [ ] Add batch generation support (N clients at once)
- [ ] Add client config download button

## Phase 9: Automatic Key Rotation (ENABLE_KEY_ROTATION=true)
- [ ] Implement `key_rotation.py` — scheduled key rotation
- [ ] Generate new PQC key material on rotation trigger
- [ ] Derive new WireGuard PSK from fresh PQC KEM exchange
- [ ] Update `wg0.conf` with new PSK (zero-downtime)
- [ ] Apply via `wg set wg0 peer <key> preshared-key <new_psk>`
- [ ] Log rotation event to `key_rotation_log` table
- [ ] Add rotation status to dashboard
- [ ] Test scheduled rotation (set interval to 1 minute for testing)
- [ ] Test manual rotation via API (`POST /api/pqc/rotate-keys`)
- [ ] Verify audit log records old/new PSK hashes

## Phase 10: Performance Benchmarking (ENABLE_BENCHMARK=true)
- [ ] Implement `benchmark.py` — PQC algorithm benchmarks
- [ ] Benchmark ML-KEM-512 keygen / encaps / decaps
- [ ] Benchmark ML-KEM-768 keygen / encaps / decaps
- [ ] Benchmark ML-KEM-1024 keygen / encaps / decaps
- [ ] Benchmark ML-DSA-44 keygen / sign / verify
- [ ] Benchmark ML-DSA-65 keygen / sign / verify
- [ ] Benchmark ML-DSA-87 keygen / sign / verify
- [ ] Measure hybrid handshake total time (X25519 + ML-KEM)
- [ ] Measure VPN throughput with `iperf3` (with and without PQC)
- [ ] Store results in `benchmark_results` table
- [ ] Add benchmark charts to dashboard (Chart.js)
- [ ] Add historical trend display
- [ ] Schedule periodic benchmarks via `.env` interval

## Phase 11: systemd Services
- [ ] Create `/etc/systemd/system/quantum-vpn-dashboard.service`
- [ ] Configure `ExecStart` with venv Python path
- [ ] Enable and start: `sudo systemctl enable --now quantum-vpn-dashboard`
- [ ] Verify dashboard auto-starts on boot
- [ ] Configure WireGuard auto-start: `sudo systemctl enable wg-quick@wg0`
- [ ] Test full reboot — verify both services start

## Phase 12: Testing & Validation
- [ ] Write unit tests for `pqc_engine.py` (keygen, encaps, decaps)
- [ ] Write unit tests for `hybrid_kex.py` (combined secret derivation)
- [ ] Write unit tests for `cert_manager.py` (CA, server, client certs)
- [ ] Write unit tests for `client_gen.py` (config generation, QR)
- [ ] Write unit tests for `key_rotation.py` (rotation logic, logging)
- [ ] Write unit tests for `benchmark.py` (result collection)
- [ ] Write integration tests for `auth.py` (login, rate limit, session)
- [ ] Write API tests for all REST endpoints
- [ ] Test mock mode — all features work without WireGuard/liboqs
- [ ] Test end-to-end: client connects via PQC-enhanced WireGuard tunnel
- [ ] Optional: set up secondary Pi as VPN client for full E2E test
- [ ] Run `pytest` — all tests pass

## Phase 13: Documentation & Deployment
- [ ] Write `docs/threat_model.md` — detailed HNDL threat analysis
- [ ] Write `docs/pqc_algorithms.md` — algorithm comparison and selection
- [ ] Write `docs/benchmark_guide.md` — interpreting performance results
- [ ] Write `docs/client_setup.md` — client-side setup instructions
- [ ] Review and finalize `README.md`
- [ ] Deploy to Pi via `bash deploy/deploy_to_pi.sh`
- [ ] Final smoke test on production Pi
- [ ] Verify all `.env` toggles work (enable/disable each feature)
