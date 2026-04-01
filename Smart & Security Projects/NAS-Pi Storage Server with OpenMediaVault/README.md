# NAS-Pi Storage Server with OpenMediaVault

Turn a Raspberry Pi into a Network-Attached Storage (NAS) device for file sharing, backup, and personal cloud storage. Uses OpenMediaVault as the management platform with SMB/NFS/SFTP file sharing, Docker support for Nextcloud and Jellyfin, automated backups with rsync, UPS monitoring, and optional disk encryption. A powerful, cost-effective alternative to commercial NAS solutions.

🪙 **Donations are Welcome!**
If you find this project helpful, you can support my work with a small donation.
₿ Bitcoin donation: `bc1q...`

---

## Table of Contents

1. [Project structure](#project-structure)
2. [Hardware requirements](#hardware-requirements)
3. [Budget](#budget)
4. [Software and dependencies](#software-and-dependencies)
5. [Quickstart — Setup on Raspberry Pi](#quickstart--setup-on-raspberry-pi)
6. [OpenMediaVault overview](#openmediavault-overview)
7. [Feature 1 — File sharing (SMB / NFS / SFTP)](#feature-1--file-sharing-smb--nfs--sftp)
8. [Feature 2 — Storage management (SnapRAID + mergerfs)](#feature-2--storage-management-snapraid--mergerfs)
9. [Feature 3 — Docker services (Nextcloud, Jellyfin, Syncthing)](#feature-3--docker-services-nextcloud-jellyfin-syncthing)
10. [Feature 4 — Automated backups with rsync](#feature-4--automated-backups-with-rsync)
11. [Feature 5 — S.M.A.R.T. disk monitoring](#feature-5--smart-disk-monitoring)
12. [Feature 6 — UPS monitoring (NUT)](#feature-6--ups-monitoring-nut)
13. [Feature 7 — Disk encryption (LUKS)](#feature-7--disk-encryption-luks)
14. [Feature 8 — Performance tuning](#feature-8--performance-tuning)
15. [Remote access via WireGuard VPN](#remote-access-via-wireguard-vpn)
16. [Web interface](#web-interface)
17. [How to deploy to Raspberry Pi](#how-to-deploy-to-raspberry-pi)
18. [Real-world applications](#real-world-applications)
19. [Security notes](#security-notes)
20. [Troubleshooting](#troubleshooting)
21. [Where to next](#where-to-next)

---

## Project structure

```
.
├── scripts/
│   ├── install-omv.sh         ← OpenMediaVault installation script
│   ├── setup-shares.sh        ← Configure SMB/NFS/SFTP shares
│   ├── setup-docker.sh        ← Install Docker + Compose via OMV plugin
│   ├── setup-snapraid.sh      ← SnapRAID + mergerfs configuration
│   ├── setup-backup.sh        ← Automated rsync backup setup
│   ├── setup-ups.sh           ← NUT (Network UPS Tools) setup
│   ├── setup-luks.sh          ← LUKS disk encryption setup
│   ├── setup-wireguard.sh     ← WireGuard VPN setup
│   └── benchmark.sh           ← Disk read/write benchmark script
├── docker-compose/
│   ├── nextcloud.yml          ← Nextcloud Docker Compose
│   ├── jellyfin.yml           ← Jellyfin media server Docker Compose
│   └── syncthing.yml          ← Syncthing file sync Docker Compose
├── config/
│   ├── smb.conf.template      ← Samba share configuration template
│   ├── exports.template       ← NFS exports template
│   ├── snapraid.conf.template ← SnapRAID configuration template
│   └── rsync-backup.conf      ← rsync backup job configuration
├── deploy/
│   └── deploy_to_pi.sh        ← rsync-based deploy script
├── docs/
│   └── threat_model.md        ← Threat model and mitigations
├── README.md                  ← This file
├── TSD.md                     ← Technical Specification Description
└── task.md                    ← Engineering checklist
```

---

## Hardware requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB) / Pi 5 | Yes | Pi 4/5 with USB 3.0 required for acceptable NAS performance |
| microSD card (16 GB+) | Yes | For the OS only (data stored on USB drives) |
| USB 3.0 external HDD or SSD | Yes | Primary storage; SSD recommended for speed |
| Power supply (official) | Yes | 5V 3A for Pi 4, 5V 5A for Pi 5 |
| Ethernet cable | Yes | Gigabit Ethernet strongly recommended over WiFi |
| USB 3.0 hub (powered) | Optional | For connecting multiple drives |
| Second USB drive | Optional | For SnapRAID parity or additional storage |
| USB UPS (e.g., APC Back-UPS) | Optional | For safe shutdown on power failure |

---

## Budget

| Item | Estimated Price (USD) | Notes |
|---|---|---|
| USB 3.0 external SSD (500 GB) | $40 – $60 | Samsung T7 or similar; SSD for best performance |
| USB 3.0 external HDD (2 TB) | $55 – $75 | Cheaper per GB; slower than SSD |
| Powered USB 3.0 hub (4-port) | $15 – $25 | Required if using multiple drives |
| **Optional:** Second USB drive (parity) | $40 – $75 | For SnapRAID parity protection |
| **Optional:** USB UPS (APC Back-UPS 600VA) | $60 – $80 | Safe shutdown on power failure |
| **Optional:** Pi case with drive mount | $15 – $30 | Argon ONE M.2 case or 3D-printed |
| **Total (minimum)** | **~$40 – $60** | One USB SSD for basic NAS |

> **Note:** The Raspberry Pi itself, microSD card, power supply, and Ethernet cable are not included in the budget above.

---

## Software and dependencies

### Core software

| Software | Version | Purpose |
|---|---|---|
| [OpenMediaVault 7](https://www.openmediavault.org/) | ^7.x | NAS management platform (web UI, plugins) |
| [Samba](https://www.samba.org/) | ^4.x | SMB/CIFS file sharing (Windows, macOS, Linux) |
| [NFS](https://linux-nfs.org/) | ^4.x | NFS file sharing (Linux) |
| [OpenSSH](https://www.openssh.com/) | ^9.x | SFTP file transfer |
| [Docker](https://www.docker.com/) + Compose | ^27.x | Container runtime for additional services |
| [SnapRAID](https://www.snapraid.it/) | ^12.x | Snapshot-based software RAID (via OMV plugin) |
| [mergerfs](https://github.com/trapexit/mergerfs) | ^2.40 | FUSE union filesystem (pool multiple drives) |
| [rsync](https://rsync.samba.org/) | ^3.2 | File synchronization for automated backups |
| [NUT](https://networkupstools.org/) | ^2.8 | Network UPS Tools for power monitoring |
| [cryptsetup](https://gitlab.com/cryptsetup/cryptsetup) | ^2.7 | LUKS disk encryption |
| [smartmontools](https://www.smartmontools.org/) | ^7.4 | S.M.A.R.T. disk health monitoring |
| [WireGuard](https://www.wireguard.com/) | ^1.0 | VPN for remote access |

### Docker services (optional)

| Service | Purpose |
|---|---|
| [Nextcloud](https://nextcloud.com/) | Self-hosted cloud storage (web + mobile app) |
| [Jellyfin](https://jellyfin.org/) | Media server (movies, TV, music — free Plex alternative) |
| [Syncthing](https://syncthing.net/) | Peer-to-peer file sync across devices |

---

## Quickstart — Setup on Raspberry Pi

**1. Flash Raspberry Pi OS Lite (64-bit) to the microSD card**

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/). Select "Raspberry Pi OS Lite (64-bit)" — no desktop environment needed.

During imaging, enable SSH and set the `pi` user password.

**2. Boot and SSH into the Pi**

```bash
ssh rasp-pi
```

**3. Connect the USB storage drive**

Plug the USB 3.0 drive into a USB 3.0 port (blue port on Pi 4/5).

**4. Install OpenMediaVault**

```bash
sudo bash scripts/install-omv.sh
```

This script:
- Updates the system.
- Installs OpenMediaVault 7.
- Reboots the Pi.

**5. Access the OMV web interface**

After reboot, navigate to `http://192.168.216.90` in your browser.

- **Username:** `admin`
- **Password:** `openmediavault` (change immediately!)

**6. Configure storage and shares**

From the OMV web interface:
1. **Storage → Disks** — verify your USB drive is detected.
2. **Storage → File Systems** — create an ext4 filesystem on the USB drive.
3. **Storage → Shared Folders** — create shared folders.
4. **Services → SMB/CIFS** — enable and configure Samba shares.

**7. Connect from your devices**

- **Windows:** Open File Explorer → `\\192.168.216.90\share_name`
- **macOS:** Finder → Go → Connect to Server → `smb://192.168.216.90/share_name`
- **Linux:** `mount -t cifs //192.168.216.90/share_name /mnt/nas`

---

## OpenMediaVault overview

[OpenMediaVault (OMV)](https://www.openmediavault.org/) is a Debian-based NAS operating system with a full web-based management interface. It runs headlessly (no desktop/monitor needed) — all configuration is done via the web UI.

**Key OMV features:**
- Web-based management (no command line needed for basic operations).
- Plugin system (Docker, SnapRAID, mergerfs, NUT, and many more).
- User and group management with per-share permissions.
- Notification system (email alerts for disk failures, low space, etc.).
- Scheduled tasks (cron) for automated maintenance.
- S.M.A.R.T. monitoring and scheduled disk checks.

> **Important:** The Raspberry Pi runs headless (console OS only — no graphical desktop). All management is done through the OMV web interface accessed from any browser on the local network.

---

## Feature 1 — File sharing (SMB / NFS / SFTP)

Three file sharing protocols cover all operating systems.

### SMB/CIFS (Windows, macOS, Linux)

- The most widely compatible protocol.
- Windows natively supports SMB (File Explorer → `\\ip\share`).
- macOS supports SMB (Finder → Connect to Server).
- Configurable per-share permissions (read-only, read-write, per-user).

### NFS (Linux)

- Higher performance than SMB for Linux clients.
- Configured via OMV web interface or `exports.template`.
- Supports NFS v3 and v4.

### SFTP (all platforms)

- Secure file transfer over SSH.
- Works with FileZilla, WinSCP, or any SFTP client.
- Uses the existing SSH authentication — no additional setup.

---

## Feature 2 — Storage management (SnapRAID + mergerfs)

Manage multiple drives with data protection.

### mergerfs — Pool multiple drives

- Combines multiple USB drives into a single virtual filesystem.
- Files are spread across drives, but each file is stored on one physical drive.
- If one drive fails, only the files on that drive are lost (not everything).
- Installed as an OMV plugin.

### SnapRAID — Parity protection

- Calculates parity data across multiple drives and stores it on a dedicated parity drive.
- If one drive fails, all files can be reconstructed from the parity.
- **Not real-time RAID** — parity is synced on a schedule (e.g., daily via cron).
- Best for "write once, read many" data (media libraries, backups, archives).
- Installed as an OMV plugin.

**Recommended setup:**
- 2+ data drives pooled with mergerfs.
- 1 parity drive with SnapRAID.
- Daily parity sync via scheduled cron job.

---

## Feature 3 — Docker services (Nextcloud, Jellyfin, Syncthing)

OMV supports Docker and Docker Compose via the official plugin. Run additional services alongside the NAS.

### Nextcloud — Personal cloud storage

- **What:** Self-hosted Google Drive / Dropbox alternative.
- **Features:** Web file manager, mobile app (iOS/Android), calendar, contacts, document editing.
- **Access:** `http://192.168.216.90:8080` (or via reverse proxy).
- **Storage:** Uses a shared folder on the NAS drives.

### Jellyfin — Media server

- **What:** Free, open-source Plex alternative.
- **Features:** Stream movies, TV shows, and music to any device (web, mobile, Smart TV, Chromecast).
- **Access:** `http://192.168.216.90:8096`
- **Storage:** Points to a media shared folder on the NAS.

### Syncthing — Peer-to-peer file sync

- **What:** Decentralized file sync (like Dropbox, but peer-to-peer, no cloud).
- **Features:** Sync folders between the NAS and your laptop/phone/desktop. Encrypted in transit.
- **Access:** `http://192.168.216.90:8384`

**Setup:**

```bash
sudo bash scripts/setup-docker.sh
cd docker-compose
docker compose -f nextcloud.yml up -d
docker compose -f jellyfin.yml up -d
docker compose -f syncthing.yml up -d
```

---

## Feature 4 — Automated backups with rsync

Schedule automatic backups from other machines on the LAN to the NAS.

- **Pull backups:** The NAS rsync's data from configured machines on a schedule.
- **Push backups:** Other machines push to the NAS via rsync over SSH.
- **Incremental:** Only changed files are transferred (efficient for large datasets).
- **Versioned:** Keep N previous versions of each file (configurable rotation).
- **Configurable schedule:** Daily, weekly, or custom cron expression.
- **Email notification:** Get an email summary after each backup job.

**Setup:**

```bash
sudo bash scripts/setup-backup.sh
```

Edit `config/rsync-backup.conf` to define backup sources and schedules.

---

## Feature 5 — S.M.A.R.T. disk monitoring

Monitor the health of connected USB drives.

- **S.M.A.R.T. attributes:** Read temperature, power-on hours, reallocated sectors, pending sectors, etc.
- **Scheduled tests:** Run short and long self-tests on a schedule.
- **Email alerts:** OMV sends an email notification if a drive reports errors or degradation.
- **Dashboard widget:** Disk health status visible in the OMV web interface.

> **Note:** Not all USB enclosures support S.M.A.R.T. passthrough. Use a USB 3.0 to SATA adapter that supports TRIM and S.M.A.R.T. (e.g., JMicron JMS578 or ASMedia ASM1153e chipset).

---

## Feature 6 — UPS monitoring (NUT)

Safely shut down the NAS on power failure using a USB UPS.

- **NUT (Network UPS Tools):** Monitors the UPS via USB. When battery runs low, triggers a clean shutdown.
- **OMV integration:** NUT is available as an OMV plugin. Configure via the web interface.
- **Supported UPS models:** APC Back-UPS, CyberPower, Eaton, and many more (see [NUT compatibility list](https://networkupstools.org/stable-hcl.html)).
- **Dashboard widget:** Battery level, load, and estimated runtime visible in OMV.

**Setup:**

```bash
sudo bash scripts/setup-ups.sh
```

Connect the UPS to the Pi via USB. NUT auto-detects supported models.

---

## Feature 7 — Disk encryption (LUKS)

Encrypt attached drives for data-at-rest protection.

- **LUKS (Linux Unified Key Setup):** Full-disk encryption on the USB drives.
- **Performance impact:** ~10–20% throughput reduction on Pi 4 (Pi 5 is faster due to better CPU).
- **Setup:** Run the encryption script before creating the filesystem. You must enter the passphrase at boot (or use a keyfile).
- **When to use:** If the NAS stores sensitive data and the Pi is in a physically accessible location.

**Setup:**

```bash
sudo bash scripts/setup-luks.sh /dev/sda
```

> **Warning:** Encrypting a drive erases all data on it. Back up first.

---

## Feature 8 — Performance tuning

Optimize the NAS for maximum throughput.

| Tuning | Expected improvement | Notes |
|---|---|---|
| Use USB 3.0 SSD | 200–400 MB/s read | vs ~40 MB/s for HDD over USB 3.0 |
| Use ext4 filesystem | Best compatibility | btrfs for snapshots; ext4 for simplicity |
| Gigabit Ethernet (wired) | ~110 MB/s network | WiFi maxes at ~30–50 MB/s |
| SMB tuning (multichannel, large buffers) | +10–20% | Configured in `smb.conf.template` |
| Disable unnecessary services | Free CPU/RAM | Turn off unused services in OMV |
| btrfs with compression (zstd) | Save 20–40% disk space | For text-heavy or compressible data |

**Run the benchmark script:**

```bash
bash scripts/benchmark.sh /mnt/nas-drive
```

This tests sequential read/write and random I/O, printing results to the console.

---

## Remote access via WireGuard VPN

Access the NAS from outside the home network securely.

- **WireGuard:** A fast, modern VPN with minimal overhead.
- **How it works:** Install WireGuard on the Pi, open one UDP port on the router, and connect from your phone/laptop using the WireGuard client app.
- **No port forwarding for NAS services:** Only the VPN port is exposed. Once connected, you access SMB/NFS/Nextcloud as if you were on the local network.
- **Mobile access:** WireGuard apps for iOS, Android, Windows, macOS, Linux.

> **Note:** This is a nice-to-have feature. Requires router port forwarding configuration, which varies by router model.

**Setup:**

```bash
sudo bash scripts/setup-wireguard.sh
```

---

## Web interface

OpenMediaVault provides a full web-based management interface — accessible from any browser on the local network. No monitor or desktop environment is needed on the Pi.

**OMV Web Interface sections:**

| Section | Description |
|---|---|
| **Dashboard** | System overview: CPU, memory, disk usage, network, service status |
| **Storage** | Disks, filesystems, shared folders, SnapRAID, mergerfs |
| **Services** | SMB/CIFS, NFS, SSH/SFTP, rsync |
| **Users** | User and group management with per-share permissions |
| **System** | Notifications, certificates, plugins, cron jobs, power management |
| **Diagnostics** | Logs, S.M.A.R.T. reports, performance stats |

**Docker service UIs:**

| Service | URL | Default Port |
|---|---|---|
| Nextcloud | `http://192.168.216.90:8080` | 8080 |
| Jellyfin | `http://192.168.216.90:8096` | 8096 |
| Syncthing | `http://192.168.216.90:8384` | 8384 |

---

## How to deploy to Raspberry Pi

Your SSH config is already set up at `~/.ssh/config`:

```
Host rasp-pi
    HostName 192.168.216.90
    User pi
    Port 22
    IdentityFile ~/.ssh/id_ed25519
```

**Method A — Use the deploy script (recommended)**

From the project directory on your laptop:

```bash
bash deploy/deploy_to_pi.sh rasp-pi /home/pi/Projects/NASPi
```

This will:
1. Create the remote directory.
2. Rsync all project files (scripts, configs, docker-compose files).
3. NOT install OMV automatically — run `install-omv.sh` manually after deploy.

**Method B — Manual setup**

```bash
rsync -avz --delete \
  --exclude='.git/' \
  ./ \
  rasp-pi:/home/pi/Projects/NASPi/

ssh rasp-pi "cd /home/pi/Projects/NASPi && sudo bash scripts/install-omv.sh"
```

---

## Real-world applications

| Application | Who uses it | Why |
|---|---|---|
| **Home file server** | Families | Central storage for photos, documents, and media accessible from all devices |
| **Media server** | Movie/music enthusiasts | Stream media to TVs, phones, and tablets with Jellyfin |
| **Personal cloud** | Privacy-conscious users | Self-hosted Dropbox alternative with Nextcloud (no monthly fees) |
| **Backup server** | Anyone with multiple devices | Automated daily backups from laptops and desktops |
| **Photo library** | Photographers | Store and organize large photo libraries with Nextcloud Photos |
| **Development NAS** | Developers | Store and share project files, Git repos, and development databases |
| **Small office file share** | Small businesses | SMB file sharing for a small team without expensive NAS hardware |
| **Surveillance archive** | Security camera users | Store camera recordings on the NAS (integrates with other Pi projects) |
| **Education project** | Teachers, students | Learn about NAS, RAID, Docker, networking, and system administration |

---

## Security notes

- **Change the default OMV password immediately.** The default is `openmediavault` — change it from the web interface.
- **Change the Pi user password.** Set a strong password during initial setup.
- **Use per-user permissions.** Create separate NAS users with access to only their shared folders.
- **Enable SSH key authentication.** Disable password SSH login for better security.
- **Encrypt sensitive data with LUKS.** If the Pi is physically accessible, encrypt the USB drives.
- **Keep OMV updated.** Apply updates from the OMV web interface → System → Update Management.
- **UPS protection.** A power failure during a write operation can corrupt data. Use a UPS for critical data.
- **S.M.A.R.T. monitoring.** Enable disk health monitoring and email alerts for early warning of drive failure.
- **WireGuard VPN.** If accessing the NAS remotely, use VPN instead of exposing services directly to the internet.
- **Firewall.** OMV includes iptables firewall. Configure to allow only necessary ports on the LAN.
- See [docs/threat_model.md](docs/threat_model.md) for the full threat analysis.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| OMV web interface not accessible | Check Pi's IP: `hostname -I`. Ensure you are on the same network. Try `http://ip-address:80`. |
| USB drive not detected | Run `lsblk` to check. Try a different USB port (use blue USB 3.0 ports). Check drive power. |
| Slow transfer speeds | Use Ethernet (not WiFi). Use USB 3.0 port + SSD. Check SMB settings. Run `benchmark.sh`. |
| SMB share not visible on Windows | Check Samba is enabled in OMV. Ensure the Pi and PC are on the same subnet. Try `\\ip\share` directly. |
| S.M.A.R.T. not working | USB enclosure may not support passthrough. Try a different USB-to-SATA adapter (JMicron/ASMedia chipset). |
| Docker containers not starting | Check Docker is installed: `docker --version`. Verify `docker-compose` files. Check logs: `docker logs container_name`. |
| NUT not detecting UPS | Check USB connection: `lsusb`. Verify UPS model is supported by NUT. Try `nut-scanner`. |
| LUKS drive not unlocking | Enter the correct passphrase at boot. If using a keyfile, verify the path. |
| `install-omv.sh` fails | Ensure Pi OS is up to date: `sudo apt update && sudo apt upgrade`. Ensure Raspberry Pi OS Lite (64-bit). |
| OMV update fails | Check internet connection. Try: `sudo omv-upgrade`. Check OMV forums for known issues. |

---

## Where to next

- See [TSD.md](TSD.md) for the full technical specification, architecture, and development phases.
- See [task.md](task.md) for the engineering checklist with step-by-step implementation tasks.
- See [docs/threat_model.md](docs/threat_model.md) for the threat model and mitigations.
