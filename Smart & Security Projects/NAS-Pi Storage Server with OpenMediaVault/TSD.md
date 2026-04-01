# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for **NAS-Pi Storage Server with OpenMediaVault**.

---

## 1. Scope

This project turns a Raspberry Pi into a Network-Attached Storage (NAS) device using OpenMediaVault as the platform. It provides file sharing (SMB/NFS/SFTP), software RAID protection (SnapRAID + mergerfs), Docker-based services (Nextcloud, Jellyfin, Syncthing), automated backups, disk health monitoring, UPS protection, and optional disk encryption. All management is via a web interface — no monitor or desktop required.

**Key goals:**
- OpenMediaVault 7 as the NAS management platform (headless, web-managed).
- File sharing via SMB/CIFS, NFS, and SFTP covering all operating systems.
- Multi-drive pooling (mergerfs) with parity protection (SnapRAID).
- Docker services: Nextcloud (cloud), Jellyfin (media), Syncthing (sync).
- Automated rsync backups with versioning and email notifications.
- S.M.A.R.T. disk health monitoring.
- UPS support with safe auto-shutdown.
- Optional LUKS disk encryption for data-at-rest protection.
- Performance tuning for USB 3.0 SSD throughput.

---

## 2. Minimum Viable Features (MVP)

### 2.1 OpenMediaVault Installation

- Raspberry Pi OS Lite (64-bit) as the base OS.
- OpenMediaVault 7 installed via script (`scripts/install-omv.sh`).
- Web interface accessible on port 80 from any browser on the LAN.
- Headless operation — no graphical desktop needed.

### 2.2 File Sharing

- **SMB/CIFS:** Windows, macOS, Linux clients. Per-share permissions. Guest access configurable.
- **NFS v3/v4:** High-performance Linux client access.
- **SFTP:** Secure file transfer via SSH. No additional setup.
- Users and groups managed via OMV web interface.

### 2.3 Storage Management

- **Single drive:** Format USB drive as ext4, mount as data filesystem.
- **Multi-drive pool (mergerfs):** Combine multiple USB drives into a single virtual filesystem via OMV mergerfs plugin.
- **Parity protection (SnapRAID):** Dedicate one drive to parity. Daily sync via cron. Recover from single-drive failure.

### 2.4 Docker Services

- Docker and Docker Compose installed via OMV plugin.
- **Nextcloud:** Self-hosted cloud storage with web and mobile access. `docker-compose/nextcloud.yml`.
- **Jellyfin:** Free media streaming server. `docker-compose/jellyfin.yml`.
- **Syncthing:** Peer-to-peer file sync. `docker-compose/syncthing.yml`.
- Each service has its own Docker Compose file and stores data on NAS shared folders.

### 2.5 Automated Backups

- rsync-based backup jobs defined in `config/rsync-backup.conf`.
- Pull from remote machines or receive pushes from clients.
- Incremental transfers (only changed files).
- Configurable versioning (keep N old versions).
- Cron-scheduled (daily, weekly, custom).
- Email notification after each job.

### 2.6 S.M.A.R.T. Disk Monitoring

- Configured via OMV web interface.
- Scheduled short and long self-tests.
- Email alerts on drive errors or degradation.
- Dashboard widget shows health status.

### 2.7 Deployment

- `deploy/deploy_to_pi.sh` script: rsync scripts/configs to the Pi.
- `scripts/install-omv.sh` for initial OMV installation.
- Individual setup scripts for each feature.
- Template config files in `config/`.

---

## 3. Nice-to-Have Features

### 3.1 UPS Monitoring (NUT)

- Network UPS Tools (NUT) via OMV plugin.
- USB UPS detection and monitoring (APC, CyberPower, Eaton, etc.).
- Safe shutdown when battery runs low.
- Dashboard widget for battery level and runtime.
- **Requires:** USB UPS (~$60–80).

### 3.2 Disk Encryption (LUKS)

- LUKS full-disk encryption on USB drives.
- Passphrase or keyfile required at boot.
- ~10–20% throughput reduction on Pi 4.
- Recommended for physically accessible locations.

### 3.3 Remote Access via WireGuard VPN

- WireGuard server on the Pi.
- Requires router port forwarding (one UDP port).
- Access NAS from outside the home as if on LAN.
- **Complexity:** Router configuration varies by model.

### 3.4 Grafana Monitoring

- Grafana + Prometheus for advanced NAS monitoring dashboards.
- Historical graphs for disk I/O, network throughput, temperature.
- Requires Docker and additional configuration.

### 3.5 Off-site Backup to Cloud

- rsync or rclone to cloud storage (Backblaze B2, AWS S3, Google Drive).
- Encrypted before upload (rclone crypt).
- **Requires:** Cloud storage account (some have free tiers).

---

## 4. High-Level Architecture

```
                      ┌────────────────────────────────────────────────────┐
                      │            Raspberry Pi (headless)                  │
                      │                                                    │
  Browser ─HTTP────► │  OpenMediaVault 7 (port 80)                         │
                      │  ├── System management (users, services, cron)     │
                      │  ├── Storage management (disks, filesystems)       │
                      │  ├── S.M.A.R.T. monitoring                         │
                      │  ├── Plugin: SnapRAID + mergerfs                   │
                      │  ├── Plugin: Docker (Portainer)                    │
                      │  └── Plugin: NUT (UPS monitoring)                  │
                      │                                                    │
  SMB client ──────► │  Samba (port 445) → shared folders                  │
  NFS client ──────► │  NFS (port 2049) → shared folders                   │
  SFTP client ─────► │  OpenSSH (port 22) → shared folders                 │
                      │                                                    │
                      │  Docker Services:                                   │
                      │  ├── Nextcloud (port 8080) → personal cloud        │
                      │  ├── Jellyfin (port 8096) → media streaming        │
                      │  └── Syncthing (port 8384) → file sync             │
                      │                                                    │
                      │  Storage:                                           │
                      │  ├── USB Drive 1 (ext4) ─┐                         │
                      │  ├── USB Drive 2 (ext4) ─┤─ mergerfs pool          │
                      │  └── USB Drive 3 (ext4) ── SnapRAID parity        │
                      │                                                    │
                      │  Backup:                                            │
                      │  └── rsync cron jobs → pull from LAN machines      │
                      │                                                    │
                      │  Optional:                                          │
                      │  ├── NUT → USB UPS monitoring                      │
                      │  ├── LUKS → disk encryption                        │
                      │  └── WireGuard → remote VPN access                 │
                      └────────────────────────────────────────────────────┘
```

---

## 5. Security and Threat Model

**Primary assets:**
- Stored data (files, photos, media, backups).
- NAS user credentials and OMV admin credentials.
- Docker service data (Nextcloud users, Jellyfin libraries).
- SSH keys and SFTP access.
- UPS control (can trigger shutdown).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Default OMV password | Change immediately on first login |
| Unauthorized file access | Per-user permissions on shared folders; SMB authentication |
| Data loss (drive failure) | SnapRAID parity; automated rsync backups |
| Data loss (power failure) | UPS with NUT auto-shutdown; journaling filesystem (ext4) |
| Data theft (physical) | LUKS encryption on drives; keep Pi in secure location |
| Network sniffing | SSH/SFTP for encrypted transfer; WireGuard for remote access |
| Brute-force SSH | SSH key authentication; disable password login; fail2ban |
| Docker container escape | Keep Docker updated; use official images; read-only bind mounts |
| Drive corruption | S.M.A.R.T. monitoring; scheduled disk checks; replace degraded drives |
| OMV web interface exposed | Firewall to LAN only; change default port; strong admin password |

See [docs/threat_model.md](docs/threat_model.md) for the complete analysis.

---

## 6. Suggested Tech Stack

| Component | Technology | Rationale |
|---|---|---|
| NAS platform | OpenMediaVault 7 | Mature, web-managed, plugin ecosystem, Debian-based |
| File sharing | Samba, NFS, SFTP | Cover all OS clients |
| Storage pool | mergerfs | Simple drive pooling, no RAID controller needed |
| Parity | SnapRAID | Snapshot-based, data-drive independent, recoverable |
| Containers | Docker + Compose | Run additional services without conflicting with OMV |
| Cloud storage | Nextcloud (Docker) | Self-hosted, feature-rich, mobile apps |
| Media server | Jellyfin (Docker) | Free, open-source, hardware transcoding on Pi 5 |
| File sync | Syncthing (Docker) | P2P, encrypted, no cloud dependency |
| Backups | rsync + cron | Standard, incremental, efficient |
| UPS | NUT (OMV plugin) | Wide UPS compatibility, OMV-integrated |
| Encryption | LUKS (cryptsetup) | Standard Linux disk encryption |
| VPN | WireGuard | Fast, modern, minimal overhead |
| Monitoring | smartmontools | Industry standard S.M.A.R.T. tools |

---

## 7. Development Phases & Concrete Steps

### Phase A — OMV installation and file sharing (Week 1)

1. Write `scripts/install-omv.sh` (update OS, install OMV 7, reboot).
2. Document OMV web interface first-login and password change.
3. Write `scripts/setup-shares.sh` (create shared folders, configure SMB/NFS).
4. Create `config/smb.conf.template` and `config/exports.template`.
5. Test file sharing from Windows, macOS, and Linux clients.
6. Document client connection steps in README.

### Phase B — Storage management (Week 1–2)

1. Write `scripts/setup-snapraid.sh` (install SnapRAID + mergerfs OMV plugins).
2. Create `config/snapraid.conf.template`.
3. Document mergerfs drive pooling setup via OMV UI.
4. Configure SnapRAID parity sync as a daily cron job.
5. Test drive failure recovery with SnapRAID.
6. Write `scripts/benchmark.sh` for storage performance testing.

### Phase C — Docker services (Week 2)

1. Write `scripts/setup-docker.sh` (install Docker OMV plugin).
2. Create `docker-compose/nextcloud.yml` with MariaDB and Redis.
3. Create `docker-compose/jellyfin.yml` with hardware transcoding config.
4. Create `docker-compose/syncthing.yml`.
5. Test all three services from browser and mobile apps.
6. Document Docker service access URLs and default ports.

### Phase D — Backups and monitoring (Week 2–3)

1. Write `scripts/setup-backup.sh` (rsync cron jobs).
2. Create `config/rsync-backup.conf` with source/destination/schedule definitions.
3. Configure S.M.A.R.T. monitoring and email alerts in OMV.
4. Write `scripts/setup-ups.sh` (NUT installation and configuration).
5. Test UPS monitoring and auto-shutdown.
6. Test email notifications for backup completion and disk warnings.

### Phase E — Encryption, VPN, and tuning (Week 3)

1. Write `scripts/setup-luks.sh` (LUKS encryption setup for USB drives).
2. Write `scripts/setup-wireguard.sh` (WireGuard server configuration).
3. Document performance tuning (SMB settings, filesystem choice, SSD vs HDD).
4. Run benchmarks and document results.
5. Write deployment script `deploy/deploy_to_pi.sh`.

### Phase F — Documentation (Week 3–4)

1. Write `README.md` with full setup guide.
2. Write `TSD.md` (this document).
3. Write `task.md` engineering checklist.
4. Write `docs/threat_model.md`.
5. End-to-end testing on Raspberry Pi 4 and Pi 5.

---

## 8. Deliverables

- OpenMediaVault 7 installation script for Raspberry Pi.
- SMB/NFS/SFTP file sharing configuration scripts and templates.
- mergerfs + SnapRAID setup for multi-drive pooling and parity.
- Docker Compose files for Nextcloud, Jellyfin, and Syncthing.
- Automated rsync backup system with versioning and email notifications.
- S.M.A.R.T. disk monitoring configuration.
- UPS monitoring setup (NUT).
- LUKS disk encryption setup script.
- WireGuard VPN setup script.
- Storage performance benchmark script.
- Deploy script for Raspberry Pi (SSH alias: `rasp-pi` at `192.168.216.90`).
- `README.md`, `TSD.md`, `task.md`, `docs/threat_model.md`.
