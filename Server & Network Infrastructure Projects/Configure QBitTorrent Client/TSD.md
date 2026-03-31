# Technical Specification Description (TSD)

This document describes the scope, minimum viable features, nice-to-have features, architecture, security considerations, suggested stack, and development plan for the **Configure QBitTorrent Client** project.

---

## 1. Scope

This project sets up a headless qBittorrent instance on a Raspberry Pi with a web-based interface for remote torrent management. The Pi acts as a low-power, always-on download machine with external storage, HTTPS-secured Web UI, RSS automation, bandwidth scheduling, and automated media organization via Sonarr/Radarr/Prowlarr.

---

## 2. Minimum Viable Features (MVP)

Each MVP feature includes a deeper explanation and rationale.

- **Headless qBittorrent-nox installation:**
  - Install `qbittorrent-nox` (no desktop GUI required) on Raspberry Pi OS.
  - Run under a dedicated non-privileged system user (`qbtuser`) for security isolation.

- **Web UI configuration:**
  - Configure the built-in Web UI accessible on port `8080` from any device on the LAN.
  - Change default credentials on first access.
  - Configure download paths, connection limits, and seeding ratios through the Web UI.

- **Systemd service:**
  - Create a `qbittorrent-nox.service` unit so the torrent client starts automatically on boot, restarts on failure, and can be managed with standard `systemctl` commands.

- **External storage setup:**
  - Mount a USB HDD or SSD to avoid SD card wear.
  - Configure with proper fstab entry using UUID, `nofail` option, and correct ownership for the `qbtuser`.
  - Set qBittorrent's download path to the external storage.

- **HTTPS reverse proxy (Nginx):**
  - Install Nginx as a reverse proxy in front of the Web UI.
  - Generate a self-signed TLS certificate (or use Let's Encrypt if the Pi is publicly accessible).
  - Bind qBittorrent to `127.0.0.1` so it is only accessible through Nginx.
  - Prevents credentials from being sent in plaintext over the LAN.

- **RSS feed automation:**
  - Configure qBittorrent's built-in RSS reader and downloader.
  - Set up feed subscriptions and filter rules to automatically download matching torrents.
  - Useful for automatically fetching regularly released content.

- **Bandwidth scheduling:**
  - Configure alternative speed limits (reduced rates during peak hours).
  - Schedule speed limit toggling so the Pi uses full bandwidth during off-peak hours and does not saturate the network during the day.

- **Automatic media organization (Sonarr / Radarr / Prowlarr):**
  - Install Prowlarr as a centralized indexer manager.
  - Install Sonarr (for TV shows) and Radarr (for movies) for automated media management.
  - Connect all three tools to qBittorrent as the download client.
  - Set media root folders on external storage for organized libraries.

---

## 3. Nice-to-Have Features

These features require paid third-party services and are optional.

- **VPN kill-switch:**
  - Route all torrent traffic through a VPN tunnel (WireGuard or OpenVPN). While the software is free and open-source, practical use requires a paid VPN subscription (e.g., Mullvad, ProtonVPN, NordVPN).
  - Configure iptables rules to block all traffic that does not go through the VPN interface (`wg0`), preventing IP and data leaks if the VPN disconnects.
  - Bind qBittorrent to the VPN network interface for additional leak prevention.
  - Persist iptables rules across reboots with `iptables-persistent`.

- **Dynamic DNS for remote access:**
  - Use a DDNS service (some free, some paid) to access the Web UI from outside the home network.
  - Combine with port forwarding and the Nginx HTTPS proxy for secure remote management.

---

## 4. High-level Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │              Raspberry Pi                    │
                    │                                              │
  Browser ──HTTPS──►│  Nginx (443) ──► qBittorrent-nox (8080)     │
                    │       │              │          │             │
                    │       │         ┌────┘          └────┐       │
                    │       │         ▼                    ▼       │
                    │       │    RSS Downloader    BitTorrent Net  │
                    │       │                          │           │
                    │       │                     ┌────┘           │
                    │       ▼                     ▼               │
                    │  /mnt/external (USB HDD/SSD)                │
                    │       │                                      │
                    │       ├── /downloads/                        │
                    │       ├── /tv/          ◄── Sonarr           │
                    │       └── /movies/      ◄── Radarr           │
                    │                                              │
                    │  Prowlarr ──► Sonarr / Radarr ──► qBittorrent│
                    └──────────────────────────────────────────────┘

Optional:
                    │  wg0 (WireGuard VPN tunnel)                  │
                    │  iptables kill-switch                        │
```

**Components:**

| Component | Role |
|---|---|
| `qbittorrent-nox` | Headless torrent client with Web UI |
| `Nginx` | HTTPS reverse proxy protecting the Web UI |
| `systemd` | Service management and auto-start |
| `fstab` + USB drive | Persistent external storage for downloads |
| `Prowlarr` | Centralized torrent indexer manager |
| `Sonarr` / `Radarr` | Automated TV and movie download management |
| `WireGuard` (optional) | VPN tunnel for traffic privacy |
| `iptables` (optional) | Kill-switch to prevent non-VPN traffic leaks |

---

## 5. Security Considerations

**Primary assets:**
- Downloaded content (stored on external drive).
- Web UI credentials (admin password).
- Network privacy (IP address, download activity).

**Threats and mitigations:**

| Threat | Mitigation |
|---|---|
| Credential interception (HTTP plaintext) | HTTPS via Nginx reverse proxy; bind qBittorrent to localhost |
| Unauthorized access to Web UI | Strong admin password; firewall (`ufw`) allowing only necessary ports |
| Running as root | Dedicated `qbtuser` with no sudo privileges |
| SD card failure from heavy writes | External USB storage for all downloads |
| ISP monitoring of torrent traffic | VPN kill-switch (nice-to-have) |
| VPN disconnects and IP leaks | iptables rules blocking non-VPN traffic |
| Service downtime after power loss | `systemd` auto-restart; `nofail` in fstab |
| Stale software with known vulnerabilities | Regular `apt update && apt upgrade` |

---

## 6. Suggested Tech Stack

| Tool | Purpose |
|---|---|
| Raspberry Pi OS (Lite) | Operating system (headless, no desktop) |
| `qbittorrent-nox` | Headless torrent client |
| `nginx` | HTTPS reverse proxy |
| `openssl` | Self-signed TLS certificate generation |
| `systemd` | Service management |
| `ext4` / `ntfs-3g` | Filesystem for external storage |
| `ufw` | Firewall |
| Prowlarr / Sonarr / Radarr | Media automation suite (.NET runtime) |
| WireGuard (optional) | VPN tunnel |
| `iptables-persistent` (optional) | Persistent firewall rules for kill-switch |

---

## 7. Development Phases & Concrete Steps

### Phase A — Base installation (Day 1)

1. Flash Raspberry Pi OS Lite and enable SSH.
2. Install `qbittorrent-nox` and create `qbtuser`.
3. Run first-time setup, accept legal notice, change default password.
4. Create and enable the systemd service.
5. Verify Web UI is accessible from a browser.

### Phase B — Storage and security (Day 1–2)

1. Connect and mount USB HDD/SSD.
2. Configure fstab for auto-mount with `nofail`.
3. Set ownership and update qBittorrent download path.
4. Install Nginx and generate a self-signed TLS certificate.
5. Configure the reverse proxy and bind qBittorrent to localhost.
6. Configure `ufw` firewall rules.

### Phase C — Automation and scheduling (Day 2–3)

1. Configure RSS feeds and download rules in qBittorrent.
2. Set up alternative speed limits and schedule.
3. Install Prowlarr, Sonarr, and Radarr.
4. Connect indexers in Prowlarr.
5. Connect qBittorrent as download client in Sonarr/Radarr.
6. Set up media root folders on external storage.

### Phase D — VPN integration (optional)

1. Install WireGuard and import VPN provider configuration.
2. Test VPN connectivity and verify IP change.
3. Configure iptables kill-switch.
4. Persist iptables rules.
5. Bind qBittorrent to the VPN interface.
6. Enable WireGuard on boot.

---

## 8. Deliverables

- Working headless qBittorrent-nox installation with Web UI.
- Systemd service with auto-start on boot.
- External USB storage mounted and configured as download path.
- Nginx HTTPS reverse proxy protecting the Web UI.
- RSS automation and bandwidth scheduling configured.
- Sonarr/Radarr/Prowlarr integration (optional but documented).
- `README.md` with full setup guide.
- `TSD.md` (this document).

---

## 9. Open Questions

- Which VPN provider do you plan to use (if any)? This affects the WireGuard configuration.
- Do you want the Pi to be accessible from outside the home network (requires DDNS and port forwarding)?
- What filesystem should the external drive use (`ext4` for Linux-only or `ntfs` for cross-platform)?
- Do you need Sonarr/Radarr, or is manual torrent management sufficient for your use case?
