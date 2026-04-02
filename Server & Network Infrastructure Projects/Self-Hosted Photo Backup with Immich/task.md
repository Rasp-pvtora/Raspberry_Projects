# Task Tracker
## Self-Hosted Photo Backup with Immich

---

## Phase 1: Hardware & OS Preparation
- [ ] Flash Raspberry Pi OS 64-bit (Bookworm) to SD card
- [ ] Enable SSH, set hostname, configure Wi-Fi/Ethernet
- [ ] Boot Pi and connect via `ssh rasp-pi` (192.168.216.90)
- [ ] Run `sudo apt update && sudo apt upgrade -y`
- [ ] Connect USB 3.0 SSD and verify with `lsblk`
- [ ] Format SSD: `sudo mkfs.ext4 /dev/sda1`
- [ ] Mount SSD at `/mnt/ssd` and add to `/etc/fstab`
- [ ] Set SSD ownership: `sudo chown -R $USER:$USER /mnt/ssd`
- [ ] Create Immich directory structure on SSD
- [ ] Configure swap file (4GB recommended for Pi 4)

## Phase 2: Docker Installation
- [ ] Install Docker via official script (`curl -fsSL https://get.docker.com | sh`)
- [ ] Add user to docker group: `sudo usermod -aG docker $USER`
- [ ] Verify Docker: `docker --version`
- [ ] Verify Docker Compose: `docker compose version`
- [ ] Configure Docker log rotation

## Phase 3: Immich Deployment
- [ ] Create project directory: `mkdir -p ~/immich-app`
- [ ] Copy `.env.default` to `.env` and configure all settings
- [ ] Generate secure DB password: `openssl rand -base64 32`
- [ ] Set storage paths in `.env` to SSD locations
- [ ] Create `docker-compose.yml` with all services
- [ ] Pull Docker images: `docker compose pull`
- [ ] Start all containers: `docker compose up -d`
- [ ] Verify all containers running: `docker compose ps`
- [ ] Check logs for errors: `docker compose logs -f`

## Phase 4: Initial Configuration
- [ ] Access web UI at `http://192.168.216.90:2283`
- [ ] Create admin account
- [ ] Configure server settings (storage, thumbnails, ML jobs)
- [ ] Enable dark theme in user settings
- [ ] Test photo upload via web UI
- [ ] Verify face detection and object tagging jobs are running
- [ ] Check ML pipeline in Admin → Jobs

## Phase 5: Mobile App Setup
- [ ] Install Immich app on iOS (App Store)
- [ ] Install Immich app on Android (Google Play)
- [ ] Configure server URL in app: `http://192.168.216.90:2283`
- [ ] Login with admin credentials
- [ ] Enable background auto-backup in app settings
- [ ] Select photo/video folders to back up
- [ ] Test background upload functionality
- [ ] Verify photos appear in web timeline

## Phase 6: Nginx Reverse Proxy (ENABLE_NGINX=true)
- [ ] Create `nginx/immich.conf` configuration
- [ ] Add Nginx service to `docker-compose.yml`
- [ ] Set `client_max_body_size 50000M`
- [ ] Configure WebSocket proxy headers
- [ ] Restart stack: `docker compose up -d`
- [ ] Test access via `http://192.168.216.90`
- [ ] Verify large file uploads through proxy

## Phase 7: HTTPS Setup (ENABLE_HTTPS=true)
- [ ] Configure domain DNS to point to Pi (or use DynamicDNS)
- [ ] Set `IMMICH_DOMAIN` and `CERTBOT_EMAIL` in `.env`
- [ ] Install Certbot or add to Docker Compose
- [ ] Generate Let's Encrypt certificate
- [ ] Enable HTTPS server block in Nginx config
- [ ] Enable HTTP → HTTPS redirect
- [ ] Test HTTPS access and certificate renewal

## Phase 8: Hardware Transcoding (ENABLE_HW_TRANSCODING=true, Pi 5 only)
- [ ] Verify Pi 5 hardware: `cat /proc/device-tree/model`
- [ ] Check V4L2 devices: `ls /dev/video*`
- [ ] Add device mappings to `docker-compose.yml`
- [ ] Set `ENABLE_HW_TRANSCODING=true` in `.env`
- [ ] Restart stack and test video transcoding
- [ ] Compare transcoding speeds vs software-only

## Phase 9: Backup Strategy (ENABLE_BACKUP=true)
- [ ] Create `scripts/backup.sh` with proper permissions
- [ ] Configure backup schedule in `.env` (default: 2 AM daily)
- [ ] Set up local rsync to secondary drive (if available)
- [ ] Configure S3/MinIO backup (if using)
- [ ] Add cron job for automated backups
- [ ] Test backup script manually
- [ ] Test database restore procedure
- [ ] Verify backup retention cleanup

## Phase 10: Migration Tools (ENABLE_MIGRATION=true)
- [ ] Install `exiftool`: `sudo apt install libimage-exiftool-perl`
- [ ] Create migration staging directory
- [ ] Test Google Takeout import script
- [ ] Test Apple Photos export import
- [ ] Install Immich CLI for bulk uploads
- [ ] Verify metadata preservation after import
- [ ] Check timeline ordering after migration

## Phase 11: Storage Monitoring (ENABLE_MONITORING=true)
- [ ] Set up disk usage monitoring script
- [ ] Configure alert threshold (default: 85%)
- [ ] Add monitoring cron job
- [ ] Test alert notification
- [ ] Monitor Docker volume sizes
- [ ] Set up log rotation for all services

## Phase 12: LDAP/OIDC Auth (ENABLE_LDAP=true / ENABLE_OIDC=true)
- [ ] Configure LDAP connection settings in `.env`
- [ ] Or configure OIDC provider settings
- [ ] Test authentication flow
- [ ] Verify user auto-registration
- [ ] Test multi-user photo isolation

## Phase 13: Testing & Validation
- [ ] Upload 100+ test photos via mobile app
- [ ] Verify face detection completes on all photos
- [ ] Test search by text (CLIP)
- [ ] Test search by face
- [ ] Test map/geocoding view
- [ ] Test album creation and sharing
- [ ] Test shared link generation
- [ ] Benchmark upload throughput
- [ ] Verify SSD I/O performance: `sudo hdparm -Tt /dev/sda`
- [ ] Stress test: upload 1000+ photos and monitor resources
- [ ] Test system recovery after power loss
- [ ] Verify backup restore procedure end-to-end

## Phase 14: Production Hardening
- [ ] Change default database password
- [ ] Bind PostgreSQL/Redis to localhost only
- [ ] Configure firewall (ufw): only allow 80, 443, 22
- [ ] Enable unattended security updates
- [ ] Document admin credentials securely
- [ ] Set up system monitoring (htop, docker stats)
- [ ] Plan SSD replacement/expansion strategy
- [ ] Create system recovery documentation

---

## Notes
- Pi 4 (4GB): expect slower ML processing, swap required for large libraries
- Pi 5 (8GB): recommended for libraries >10K photos, hardware transcoding
- SSD is critical — do not run Immich on SD card
- First ML processing run will be slow (indexing all existing photos)
- Immich updates: always `docker compose pull` then `docker compose up -d`
