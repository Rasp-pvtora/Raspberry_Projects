# Self-Hosted Photo Backup with Immich

<div align="center">

![Immich](https://img.shields.io/badge/Immich-Photo_Backup-4250e4?style=for-the-badge&logo=data:image/svg+xml;base64,...)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-4%2F5-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Deploy a high-performance self-hosted Google Photos alternative on Raspberry Pi — complete data sovereignty with AI-powered photo management.**

[Features](#features) • [Hardware](#hardware-requirements) • [Quick Start](#quick-start) • [Configuration](#configuration) • [Maintenance](#maintenance) • [Troubleshooting](#troubleshooting)

</div>

---

## Overview

Immich is a powerful self-hosted photo and video backup solution with mobile app auto-backup, facial recognition, object tagging, geocoding, timeline view, sharing, and albums. This project deploys Immich on a Raspberry Pi using Docker Compose with external SSD storage, Nginx reverse proxy, hardware transcoding, and automated backups — all configurable via `.env`.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Mobile Auto-Backup** | iOS & Android apps with background sync |
| **AI/ML Pipelines** | Face detection, object tagging, CLIP search |
| **Geocoding** | Reverse geocode photos on a map timeline |
| **Sharing & Albums** | Share albums with links or specific users |
| **Hardware Transcoding** | Pi 5 VideoCore VII acceleration |
| **External SSD Storage** | USB 3.0 SSD for fast, reliable photo storage |
| **Nginx + HTTPS** | Let's Encrypt certificates via reverse proxy |
| **Automated Backups** | rsync to secondary drive or MinIO S3 |
| **Migration Tools** | Import from Google Takeout & Apple Photos |
| **LDAP/OIDC Auth** | Enterprise authentication option |

---

## Hardware Requirements

### Required

| Component | Specification | Est. Cost |
|-----------|--------------|-----------|
| Raspberry Pi | Pi 4 (4GB+) or Pi 5 | (existing) |
| USB 3.0 SSD | 500GB minimum | $35–50 |
| SATA-to-USB Adapter | USB 3.0 | $8 |
| Ethernet Cable | Gigabit recommended | (existing) |
| Power Supply | Official Pi PSU (5V/3A+) | (existing) |

### Optional

| Component | Specification | Est. Cost |
|-----------|--------------|-----------|
| NVMe Enclosure | USB 3.0 / Pi 5 HAT | $15 |
| Secondary HDD | 2TB for backups | $30–50 |

**Total Estimated Budget: ~$43–65**

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Raspberry Pi 4/5                    │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │  Nginx  │──│  Immich   │──│  PostgreSQL + Redis │  │
│  │ :80/443 │  │  Server   │  │  (Docker volumes)   │  │
│  └─────────┘  │  :2283    │  └────────────────────┘  │
│               └──────────┘                            │
│                    │                                  │
│  ┌─────────────────┴───────────────────┐             │
│  │      Immich ML (face/object/CLIP)   │             │
│  │      Immich Microservices           │             │
│  └─────────────────────────────────────┘             │
│                    │                                  │
│  ┌─────────────────┴───────────────────┐             │
│  │         USB 3.0 SSD (/mnt/ssd)     │             │
│  │   Photos / Thumbnails / Backups     │             │
│  └─────────────────────────────────────┘             │
└──────────────────────────────────────────────────────┘
        │                         │
   Mobile Apps              Web Browser
  (iOS/Android)           (photos.local)
```

---

## Quick Start

### 1. Prepare the Pi

```bash
# SSH into the Pi
ssh rasp-pi    # 192.168.216.90

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

### 2. Mount External SSD

```bash
# Identify the SSD
lsblk

# Format if new (CAUTION: erases all data)
sudo mkfs.ext4 /dev/sda1

# Create mount point and mount
sudo mkdir -p /mnt/ssd
sudo mount /dev/sda1 /mnt/ssd

# Persist across reboots
echo '/dev/sda1 /mnt/ssd ext4 defaults,noatime,nofail 0 2' | sudo tee -a /etc/fstab

# Set ownership
sudo chown -R $USER:$USER /mnt/ssd

# Create Immich directories
mkdir -p /mnt/ssd/immich/{upload,library,thumbs,encoded-video,profile,backups}
```

### 3. Deploy Immich

```bash
# Clone project
mkdir -p ~/immich-app && cd ~/immich-app

# Copy configuration files (from this repo or create from TSD.md)
# .env, docker-compose.yml, nginx.conf

# Pull and start all containers
docker compose pull
docker compose up -d

# Check status
docker compose ps
docker compose logs -f immich-server
```

### 4. Initial Setup

1. Open browser: `http://192.168.216.90:2283`
2. Create admin account on first launch
3. Install mobile app (iOS App Store / Google Play — search "Immich")
4. Configure app: enter server URL, login, enable auto-backup

---

## Configuration

All settings are controlled via `.env` — see [TSD.md](TSD.md) for the full `.env.default` template.

### Core Settings

```bash
# .env - Core
IMMICH_VERSION=release           # Immich version tag
UPLOAD_LOCATION=/mnt/ssd/immich/upload
DB_PASSWORD=<generate-secure>    # openssl rand -base64 32
```

### Feature Toggles

```bash
ENABLE_NGINX=true                # Nginx reverse proxy
ENABLE_HTTPS=false               # Let's Encrypt (requires domain)
ENABLE_HW_TRANSCODING=false      # Pi 5 VideoCore VII
ENABLE_BACKUP=true               # Automated rsync backups
ENABLE_REDIS_CACHE=true          # Redis caching layer
ENABLE_MONITORING=false          # Storage monitoring dashboard
ENABLE_MIGRATION=false           # Google Takeout / Apple import
ENABLE_LDAP=false                # LDAP/OIDC authentication
```

### Docker Compose

The `docker-compose.yml` orchestrates:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `immich-server` | `ghcr.io/immich-app/immich-server` | 2283 | API + Web UI |
| `immich-machine-learning` | `ghcr.io/immich-app/immich-machine-learning` | — | Face/object/CLIP |
| `postgres` | `tensorchord/pgvecto-rs:pg16-v0.2.0` | 5432 | Database |
| `redis` | `redis:7-alpine` | 6379 | Cache |
| `nginx` | `nginx:alpine` | 80/443 | Reverse proxy (optional) |

### Nginx Reverse Proxy

```nginx
# /etc/nginx/conf.d/immich.conf (simplified)
server {
    listen 80;
    server_name photos.example.com;
    client_max_body_size 50000M;

    location / {
        proxy_pass http://127.0.0.1:2283;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

HTTPS with Let's Encrypt:

```bash
# Enable in .env
ENABLE_HTTPS=true
IMMICH_DOMAIN=photos.example.com
CERTBOT_EMAIL=you@example.com

# Certbot runs inside Docker or standalone
sudo certbot --nginx -d photos.example.com
```

### Hardware Transcoding (Pi 5)

```bash
# Enable in .env
ENABLE_HW_TRANSCODING=true

# docker-compose.yml adds device mapping:
# devices:
#   - /dev/video10:/dev/video10
#   - /dev/video11:/dev/video11
#   - /dev/video12:/dev/video12
```

### Storage Layout

```
/mnt/ssd/immich/
├── upload/          # Original uploaded photos/videos
├── library/         # Immich-managed library
├── thumbs/          # Generated thumbnails
├── encoded-video/   # Transcoded video files
├── profile/         # User profile images
└── backups/         # Database + metadata backups
```

---

## Maintenance

### Backup Strategy

```bash
# Automated backup script (runs via cron)
scripts/backup.sh

# Manual backup
docker exec -t immich-postgres pg_dumpall -c -U postgres > /mnt/ssd/immich/backups/db_$(date +%F).sql

# rsync to secondary drive
rsync -avz --progress /mnt/ssd/immich/ /mnt/backup-hdd/immich/

# rsync to remote (MinIO S3)
# Configure BACKUP_S3_* variables in .env
```

### Updates

```bash
cd ~/immich-app

# Pull latest images
docker compose pull

# Recreate containers
docker compose up -d

# Clean old images
docker image prune -f
```

### Monitoring

```bash
# Storage usage
df -h /mnt/ssd
du -sh /mnt/ssd/immich/*

# Container health
docker compose ps
docker stats --no-stream

# Logs
docker compose logs --tail=100 immich-server
docker compose logs --tail=100 immich-machine-learning
```

### Migration Tools

```bash
# Google Takeout import
scripts/migrate-google-takeout.sh /path/to/takeout/

# Apple Photos export import
scripts/migrate-apple-photos.sh /path/to/export/

# CLI upload
immich upload --recursive /path/to/photos/
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| SSD not detected | Check `lsblk`, try different USB port (use USB 3.0 blue) |
| ML container OOM | Set `MACHINE_LEARNING_WORKER_TIMEOUT=300` in `.env`, consider swap |
| Slow thumbnail generation | Normal on Pi 4 — ML runs on ARM; Pi 5 is ~2x faster |
| Upload fails | Check `client_max_body_size` in Nginx, verify disk space |
| Mobile app won't connect | Ensure Pi and phone on same network, check firewall |
| Database errors | Check `docker compose logs postgres`, verify `DB_PASSWORD` |
| Permission denied on SSD | Run `sudo chown -R 1000:1000 /mnt/ssd/immich` |

### Performance Tuning

```bash
# Add swap (recommended for Pi 4 with 4GB)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize PostgreSQL for Pi
# In .env:
DB_SHARED_BUFFERS=256MB
DB_WORK_MEM=32MB
```

### Useful Commands

```bash
# Restart all services
docker compose restart

# Reset admin password
docker exec -it immich-server /bin/sh
# Inside container: use Immich CLI

# Force re-run ML jobs
# Use Immich Admin UI → Jobs → Queue all

# Check Immich version
docker exec immich-server cat /app/package.json | grep version
```

---

## Security Notes

- Change default `DB_PASSWORD` before first start
- Enable HTTPS for any non-LAN access
- Keep Immich updated — security patches ship with releases
- SSD encryption (LUKS) recommended for sensitive photo libraries
- Firewall: only expose ports 80/443 if using Nginx, otherwise 2283
- Consider LDAP/OIDC for multi-user setups

---

## References

- [Immich Official Docs](https://immich.app/docs)
- [Immich GitHub](https://github.com/immich-app/immich)
- [Immich Docker Install](https://immich.app/docs/install/docker-compose)
- [Immich Mobile App](https://immich.app/docs/features/mobile-app)
- [Immich CLI](https://immich.app/docs/features/command-line-interface)
- [Nginx Proxy Guide](https://immich.app/docs/administration/reverse-proxy)

---

<div align="center">

**Found this useful? Support the project:**

`bc1q...`

</div>
