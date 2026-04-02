# Implementation Plan
## Self-Hosted Photo Backup with Immich

---

## Executive Summary

Deploy Immich — a high-performance self-hosted Google Photos alternative — on a Raspberry Pi 4/5 using Docker Compose. The system provides mobile auto-backup (iOS/Android), AI-powered face detection, object tagging, CLIP search, geocoding, albums, and sharing. All photos stored on a local USB 3.0 SSD for complete data sovereignty. All features are `.env` toggleable.

**Budget:** ~$43–65 | **Timeline:** 1–2 days (core) + 1–2 days (optional features)

---

## Phase 1: Foundation (Day 1 — Morning)

### 1.1 Hardware Assembly
| Step | Action | Duration |
|------|--------|----------|
| 1 | Flash Pi OS 64-bit (Bookworm) with SSH enabled | 10 min |
| 2 | Connect Ethernet, boot, SSH via `ssh rasp-pi` | 5 min |
| 3 | Full system update | 10 min |
| 4 | Connect USB 3.0 SSD to blue USB 3.0 port | 2 min |

### 1.2 SSD Preparation
```bash
# Identify disk
lsblk

# Format (WARNING: erases all data)
sudo mkfs.ext4 /dev/sda1

# Mount
sudo mkdir -p /mnt/ssd
sudo mount /dev/sda1 /mnt/ssd

# Persist
echo '/dev/sda1 /mnt/ssd ext4 defaults,noatime,nofail 0 2' | sudo tee -a /etc/fstab

# Ownership
sudo chown -R $USER:$USER /mnt/ssd

# Immich directories
mkdir -p /mnt/ssd/immich/{upload,library,thumbs,encoded-video,profile,backups}
mkdir -p /mnt/ssd/docker-volumes
```

### 1.3 Docker Installation
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
```

### 1.4 Swap Configuration (Pi 4)
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**Milestone:** Pi ready with Docker, SSD mounted, swap configured.

---

## Phase 2: Core Deployment (Day 1 — Afternoon)

### 2.1 Project Setup
```bash
mkdir -p ~/immich-app/nginx ~/immich-app/scripts
cd ~/immich-app
```

### 2.2 Configuration
1. Create `.env` from `.env.default` template (see TSD.md Section 3)
2. Generate database password: `openssl rand -base64 32`
3. Set timezone, storage paths, feature toggles
4. Create `docker-compose.yml` (see TSD.md Section 4)

### 2.3 Deploy
```bash
docker compose pull       # ~10-20 min on first pull
docker compose up -d
docker compose ps         # Verify all containers healthy
docker compose logs -f immich-server  # Watch startup
```

### 2.4 Initial Setup
1. Browse to `http://192.168.216.90:2283`
2. Create admin account (first user becomes admin)
3. Navigate to Administration → Settings
4. Configure storage template, job concurrency
5. Enable dark theme in user settings

**Milestone:** Immich running, admin account created, web UI accessible.

---

## Phase 3: Mobile App & Upload Testing (Day 1 — Evening)

### 3.1 App Installation
| Platform | Store | Search |
|----------|-------|--------|
| iOS | App Store | "Immich" |
| Android | Google Play | "Immich" |

### 3.2 App Configuration
1. Open app → Enter server URL: `http://192.168.216.90:2283`
2. Login with admin credentials
3. Settings → Backup:
   - Enable auto-backup
   - Select photo + video folders
   - Set backup trigger (Wi-Fi only recommended)
   - Enable background backup

### 3.3 Validation
- Upload 10–20 test photos from phone
- Verify photos appear in web timeline
- Check face detection starts processing (Admin → Jobs)
- Test CLIP search: search by description (e.g., "sunset", "dog")
- Verify thumbnail generation

**Milestone:** Mobile backup working, ML pipeline processing.

---

## Phase 4: Nginx Reverse Proxy (Day 2 — Morning)

### 4.1 Enable
```bash
# .env
ENABLE_NGINX=true
```

### 4.2 Configuration
Create `nginx/immich.conf` (see TSD.md Section 5):
- Upstream to Immich server on port 2283
- `client_max_body_size 50000M` (for video uploads)
- WebSocket proxy headers for real-time updates
- Security headers (X-Content-Type-Options, X-Frame-Options)

### 4.3 Docker Integration
Add Nginx service to `docker-compose.yml`:
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/immich.conf:/etc/nginx/conf.d/default.conf:ro
  depends_on:
    - immich-server
```

### 4.4 HTTPS (Optional)
If `ENABLE_HTTPS=true`:
1. Configure domain DNS → Pi IP
2. Run Certbot: `sudo certbot --nginx -d photos.example.com`
3. Enable HTTPS server block in Nginx config
4. Set up auto-renewal cron

**Milestone:** Nginx proxying traffic, optional HTTPS.

---

## Phase 5: Backup Strategy (Day 2 — Afternoon)

### 5.1 Database Backups
```bash
# Manual test
docker exec -t immich-postgres pg_dumpall -c -U postgres \
    > /mnt/ssd/immich/backups/db_$(date +%F).sql
```

### 5.2 File Sync Setup
**Option A: Local secondary drive**
```bash
# Mount backup HDD
sudo mkdir -p /mnt/backup-hdd
sudo mount /dev/sdb1 /mnt/backup-hdd

# rsync
rsync -avz --delete /mnt/ssd/immich/ /mnt/backup-hdd/immich/
```

**Option B: S3/MinIO**
```bash
# Configure in .env
BACKUP_S3_ENABLED=true
BACKUP_S3_ENDPOINT=http://minio.local:9000
BACKUP_S3_BUCKET=immich-backup
```

### 5.3 Automation
```bash
# Deploy backup script
chmod +x scripts/backup.sh

# Add cron
echo '0 2 * * * root /home/pi/immich-app/scripts/backup.sh' | sudo tee /etc/cron.d/immich-backup
```

### 5.4 Restore Test
```bash
# Restore database
cat /mnt/ssd/immich/backups/db_YYYY-MM-DD.sql | docker exec -i immich-postgres psql -U postgres
docker compose restart immich-server
```

**Milestone:** Automated nightly backups, tested restore procedure.

---

## Phase 6: Optional Features (Day 2 — Evening)

### 6.1 Hardware Transcoding (Pi 5 Only)
```bash
# .env
ENABLE_HW_TRANSCODING=true

# Verify devices exist
ls /dev/video1*

# Add to docker-compose.yml immich-server service:
# devices:
#   - /dev/video10:/dev/video10
#   - /dev/video11:/dev/video11
#   - /dev/video12:/dev/video12
```

### 6.2 Migration: Google Takeout
```bash
# Enable migration
ENABLE_MIGRATION=true

# Install exiftool for metadata
sudo apt install libimage-exiftool-perl

# Run migration script
scripts/migrate-google-takeout.sh /path/to/Takeout/

# Then upload via Immich CLI or web UI
```

### 6.3 Migration: Apple Photos
```bash
# Export from Apple Photos → folder
# Copy to Pi via rsync/scp
rsync -avz ~/Photos/Export/ rasp-pi:/mnt/ssd/import/apple-photos/

# Upload via Immich CLI
immich upload --recursive /mnt/ssd/import/apple-photos/
```

### 6.4 Storage Monitoring
```bash
# .env
ENABLE_MONITORING=true
MONITORING_ALERT_THRESHOLD_PERCENT=85

# Adds cron job for disk usage alerts
```

### 6.5 LDAP/OIDC Authentication
```bash
# .env (LDAP example)
ENABLE_LDAP=true
LDAP_URL=ldap://ldap.example.com
LDAP_BIND_DN=cn=admin,dc=example,dc=com
LDAP_BASE_DN=ou=users,dc=example,dc=com

# Or OIDC
ENABLE_OIDC=true
OIDC_ISSUER_URL=https://auth.example.com
OIDC_CLIENT_ID=immich
OIDC_CLIENT_SECRET=<secret>
```

**Milestone:** All optional features configured and tested.

---

## Phase 7: Production Hardening

### 7.1 Security Checklist
- [ ] Strong DB password (32+ chars, randomly generated)
- [ ] PostgreSQL/Redis bound to `127.0.0.1`
- [ ] Firewall configured:
  ```bash
  sudo ufw default deny incoming
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```
- [ ] HTTPS enabled for non-LAN access
- [ ] Nginx security headers configured
- [ ] Unattended upgrades enabled:
  ```bash
  sudo apt install unattended-upgrades
  sudo dpkg-reconfigure -plow unattended-upgrades
  ```

### 7.2 Performance Tuning
- PostgreSQL: Adjust `shared_buffers`, `work_mem` based on available RAM
- Redis: `maxmemory 128mb` with LRU eviction
- ML: Set `MACHINE_LEARNING_WORKER_TIMEOUT=300` to prevent OOM kills
- Docker: Log rotation (`max-size: 10m`, `max-file: 3`)

### 7.3 Monitoring
```bash
# Quick health check
docker compose ps
docker stats --no-stream
df -h /mnt/ssd
free -h
```

---

## Timeline Summary

| Phase | Description | Duration | Required |
|-------|-------------|----------|----------|
| 1 | Foundation (OS, SSD, Docker) | 1–2 hours | Yes |
| 2 | Core Deployment (Immich) | 1–2 hours | Yes |
| 3 | Mobile App Setup | 30 min | Yes |
| 4 | Nginx Reverse Proxy | 30–60 min | Recommended |
| 5 | Backup Strategy | 1 hour | Recommended |
| 6 | Optional Features | 1–3 hours | Optional |
| 7 | Production Hardening | 30–60 min | Recommended |

**Total: 1–2 days**

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| SD card failure | All data on SSD; SD card only for OS |
| SSD failure | Automated backups to secondary drive or S3 |
| Power loss during write | ext4 journaling, `noatime` mount option |
| Pi 4 RAM limits (4GB) | Swap file, ML timeout tuning, Redis memory cap |
| ML pipeline slow | Expected on ARM; Pi 5 recommended for large libraries |
| Docker image size | Images stored on SSD (`DOCKER_VOLUMES_PATH`) |
| Immich breaking update | Pin `IMMICH_VERSION` to specific release tag |
| Network exposure | Firewall + localhost binding for internal services |

---

## Success Criteria

- [ ] Immich web UI accessible at `http://192.168.216.90:2283`
- [ ] Mobile app auto-backup working (iOS and/or Android)
- [ ] Face detection processing photos automatically
- [ ] Search by text (CLIP) returns relevant results
- [ ] All photos stored on external SSD (`/mnt/ssd`)
- [ ] Automated backups running on schedule
- [ ] System stable under sustained use (100+ photos/day)
- [ ] Recovery tested: restore from backup successfully
