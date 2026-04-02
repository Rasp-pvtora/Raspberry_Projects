# Technical Specification Document (TSD)
## Self-Hosted Photo Backup with Immich

---

## 1. System Overview

| Attribute | Value |
|-----------|-------|
| **Platform** | Raspberry Pi 4 (4GB+) / Pi 5 |
| **Deployment** | Docker Compose |
| **Application** | Immich (self-hosted Google Photos alternative) |
| **Storage** | USB 3.0 SSD (ext4) mounted at `/mnt/ssd` |
| **Network** | SSH alias `rasp-pi` at `192.168.216.90` |
| **OS** | Raspberry Pi OS (64-bit, Bookworm) |
| **Theme** | Dark (Immich built-in dark mode) |

---

## 2. Architecture Diagram

```
Internet/LAN
     │
     ▼
┌─────────────┐     ┌──────────────────────────────────────┐
│   Nginx     │────▶│         Immich Server (:2283)         │
│  :80/:443   │     │   REST API + Web UI + WebSocket       │
│  (optional) │     └──────────┬───────────────────────────┘
└─────────────┘                │
                    ┌──────────┴───────────────────────────┐
                    │     Immich Machine Learning           │
                    │  Face Detection / Object Tagging /    │
                    │  CLIP Search / Geocoding              │
                    └──────────┬───────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
     ┌──────────────┐ ┌─────────────┐  ┌──────────────┐
     │  PostgreSQL   │ │   Redis     │  │  USB 3.0 SSD │
     │  + pgvecto.rs │ │   Cache     │  │  /mnt/ssd    │
     │  :5432        │ │   :6379     │  │  (photos +   │
     └──────────────┘ └─────────────┘  │   backups)   │
                                        └──────────────┘
```

---

## 3. Environment Configuration (.env.default)

```bash
###############################################################################
# IMMICH SELF-HOSTED PHOTO BACKUP — ENVIRONMENT CONFIGURATION
# Copy to .env and customize before deployment
# All features are toggleable via ENABLE_* flags
###############################################################################

# ===========================================================================
# CORE SETTINGS
# ===========================================================================

# Immich version — use 'release' for stable, or pin to specific version
IMMICH_VERSION=release

# Timezone
TZ=UTC

# Pi IP / hostname
PI_HOST=192.168.216.90
PI_SSH_ALIAS=rasp-pi

# ===========================================================================
# DATABASE (PostgreSQL + pgvecto.rs)
# ===========================================================================

DB_ENGINE=postgres
DB_HOSTNAME=immich-postgres
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=CHANGE_ME_USE_openssl_rand_base64_32
DB_DATABASE_NAME=immich

# PostgreSQL tuning for Raspberry Pi
DB_SHARED_BUFFERS=256MB
DB_WORK_MEM=32MB
DB_EFFECTIVE_CACHE_SIZE=512MB
DB_MAX_CONNECTIONS=50

# ===========================================================================
# REDIS CACHE
# ===========================================================================

ENABLE_REDIS_CACHE=true
REDIS_HOSTNAME=immich-redis
REDIS_PORT=6379
REDIS_PASSWORD=
# Max memory for Redis (recommended for Pi)
REDIS_MAXMEMORY=128mb

# ===========================================================================
# STORAGE PATHS
# ===========================================================================

# Primary SSD mount point
SSD_MOUNT=/mnt/ssd
SSD_DEVICE=/dev/sda1
SSD_FILESYSTEM=ext4

# Immich storage locations (all on SSD)
UPLOAD_LOCATION=/mnt/ssd/immich/upload
LIBRARY_LOCATION=/mnt/ssd/immich/library
THUMB_LOCATION=/mnt/ssd/immich/thumbs
ENCODED_VIDEO_LOCATION=/mnt/ssd/immich/encoded-video
PROFILE_LOCATION=/mnt/ssd/immich/profile
BACKUP_LOCATION=/mnt/ssd/immich/backups

# Docker volumes base path
DOCKER_VOLUMES_PATH=/mnt/ssd/docker-volumes

# ===========================================================================
# FEATURE TOGGLES
# ===========================================================================

# Nginx reverse proxy (port 80/443 → 2283)
ENABLE_NGINX=true

# HTTPS via Let's Encrypt (requires public domain + port 80 forwarding)
ENABLE_HTTPS=false
IMMICH_DOMAIN=photos.example.com
CERTBOT_EMAIL=you@example.com

# Hardware transcoding — Pi 5 VideoCore VII only
ENABLE_HW_TRANSCODING=false
# V4L2 device paths for Pi 5
HW_TRANSCODE_DEVICE_0=/dev/video10
HW_TRANSCODE_DEVICE_1=/dev/video11
HW_TRANSCODE_DEVICE_2=/dev/video12

# Automated backup (rsync to secondary drive or S3)
ENABLE_BACKUP=true
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=30

# Backup to secondary local drive
BACKUP_LOCAL_ENABLED=true
BACKUP_LOCAL_PATH=/mnt/backup-hdd/immich

# Backup to S3-compatible storage (MinIO)
BACKUP_S3_ENABLED=false
BACKUP_S3_ENDPOINT=http://minio.local:9000
BACKUP_S3_BUCKET=immich-backup
BACKUP_S3_ACCESS_KEY=
BACKUP_S3_SECRET_KEY=
BACKUP_S3_REGION=us-east-1

# Storage monitoring dashboard
ENABLE_MONITORING=false
MONITORING_PORT=9100
MONITORING_ALERT_THRESHOLD_PERCENT=85

# Migration tools (Google Takeout / Apple Photos import)
ENABLE_MIGRATION=false
MIGRATION_SOURCE_PATH=/mnt/ssd/import

# LDAP / OIDC authentication
ENABLE_LDAP=false
LDAP_URL=ldap://ldap.example.com
LDAP_BIND_DN=
LDAP_BIND_PASSWORD=
LDAP_BASE_DN=
LDAP_SEARCH_FILTER=

ENABLE_OIDC=false
OIDC_ISSUER_URL=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_SCOPE=openid profile email
OIDC_AUTO_REGISTER=true

# ===========================================================================
# MACHINE LEARNING
# ===========================================================================

# ML model settings
MACHINE_LEARNING_ENABLED=true
MACHINE_LEARNING_URL=http://immich-machine-learning:3003
MACHINE_LEARNING_WORKER_TIMEOUT=300
MACHINE_LEARNING_MODEL_TTL=600

# Face detection
ML_FACE_DETECTION_ENABLED=true
ML_FACE_DETECTION_MODEL=buffalo_l
ML_FACE_DETECTION_MIN_SCORE=0.7

# CLIP (search by text)
ML_CLIP_ENABLED=true
ML_CLIP_MODEL=ViT-B-32__openai

# Object tagging
ML_OBJECT_TAGGING_ENABLED=true

# ===========================================================================
# IMMICH SERVER
# ===========================================================================

IMMICH_SERVER_PORT=2283
IMMICH_METRICS_ENABLED=false
IMMICH_LOG_LEVEL=log

# Upload limits
IMMICH_MAX_UPLOAD_SIZE=50000
# Concurrent upload workers
IMMICH_UPLOAD_WORKERS=2

# Thumbnail generation
THUMB_QUALITY=80
THUMB_SIZE=250
THUMB_LARGE_SIZE=1440

# ===========================================================================
# NETWORK
# ===========================================================================

# Expose ports on host (set to 127.0.0.1:PORT to restrict to localhost)
IMMICH_BIND=0.0.0.0:2283
NGINX_HTTP_BIND=0.0.0.0:80
NGINX_HTTPS_BIND=0.0.0.0:443
POSTGRES_BIND=127.0.0.1:5432
REDIS_BIND=127.0.0.1:6379

# ===========================================================================
# SYSTEM / PI SETTINGS
# ===========================================================================

# User/Group ID for file permissions
PUID=1000
PGID=1000

# Swap file size (recommended for Pi 4)
SWAP_SIZE=4G
SWAP_FILE=/swapfile

# Docker log rotation
DOCKER_LOG_MAX_SIZE=10m
DOCKER_LOG_MAX_FILE=3
```

---

## 4. Docker Compose Specification

```yaml
# docker-compose.yml
version: "3.8"

services:
  # ==========================================================================
  # IMMICH SERVER (API + Web UI)
  # ==========================================================================
  immich-server:
    container_name: immich-server
    image: ghcr.io/immich-app/immich-server:${IMMICH_VERSION:-release}
    restart: unless-stopped
    ports:
      - "${IMMICH_BIND:-0.0.0.0:2283}:2283"
    volumes:
      - ${UPLOAD_LOCATION:-/mnt/ssd/immich/upload}:/usr/src/app/upload
      - ${LIBRARY_LOCATION:-/mnt/ssd/immich/library}:/usr/src/app/library
      - /etc/localtime:/etc/localtime:ro
    environment:
      - DB_HOSTNAME=${DB_HOSTNAME:-immich-postgres}
      - DB_PORT=${DB_PORT:-5432}
      - DB_USERNAME=${DB_USERNAME:-postgres}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_DATABASE_NAME=${DB_DATABASE_NAME:-immich}
      - REDIS_HOSTNAME=${REDIS_HOSTNAME:-immich-redis}
      - REDIS_PORT=${REDIS_PORT:-6379}
      - IMMICH_MACHINE_LEARNING_URL=${MACHINE_LEARNING_URL:-http://immich-machine-learning:3003}
      - TZ=${TZ:-UTC}
    depends_on:
      - immich-postgres
      - immich-redis
    logging:
      driver: json-file
      options:
        max-size: "${DOCKER_LOG_MAX_SIZE:-10m}"
        max-file: "${DOCKER_LOG_MAX_FILE:-3}"

  # ==========================================================================
  # IMMICH MACHINE LEARNING
  # ==========================================================================
  immich-machine-learning:
    container_name: immich-machine-learning
    image: ghcr.io/immich-app/immich-machine-learning:${IMMICH_VERSION:-release}
    restart: unless-stopped
    volumes:
      - immich-ml-cache:/cache
    environment:
      - MACHINE_LEARNING_WORKER_TIMEOUT=${MACHINE_LEARNING_WORKER_TIMEOUT:-300}
      - MACHINE_LEARNING_MODEL_TTL=${MACHINE_LEARNING_MODEL_TTL:-600}
      - TZ=${TZ:-UTC}
    logging:
      driver: json-file
      options:
        max-size: "${DOCKER_LOG_MAX_SIZE:-10m}"
        max-file: "${DOCKER_LOG_MAX_FILE:-3}"

  # ==========================================================================
  # POSTGRESQL + pgvecto.rs
  # ==========================================================================
  immich-postgres:
    container_name: immich-postgres
    image: tensorchord/pgvecto-rs:pg16-v0.2.0
    restart: unless-stopped
    ports:
      - "${POSTGRES_BIND:-127.0.0.1:5432}:5432"
    volumes:
      - ${DOCKER_VOLUMES_PATH:-/mnt/ssd/docker-volumes}/postgres:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_USER=${DB_USERNAME:-postgres}
      - POSTGRES_DB=${DB_DATABASE_NAME:-immich}
    command: >
      postgres
        -c shared_buffers=${DB_SHARED_BUFFERS:-256MB}
        -c work_mem=${DB_WORK_MEM:-32MB}
        -c effective_cache_size=${DB_EFFECTIVE_CACHE_SIZE:-512MB}
        -c max_connections=${DB_MAX_CONNECTIONS:-50}
    logging:
      driver: json-file
      options:
        max-size: "${DOCKER_LOG_MAX_SIZE:-10m}"
        max-file: "${DOCKER_LOG_MAX_FILE:-3}"

  # ==========================================================================
  # REDIS CACHE
  # ==========================================================================
  immich-redis:
    container_name: immich-redis
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "${REDIS_BIND:-127.0.0.1:6379}:6379"
    command: >
      redis-server
        --maxmemory ${REDIS_MAXMEMORY:-128mb}
        --maxmemory-policy allkeys-lru
    volumes:
      - ${DOCKER_VOLUMES_PATH:-/mnt/ssd/docker-volumes}/redis:/data
    logging:
      driver: json-file
      options:
        max-size: "${DOCKER_LOG_MAX_SIZE:-10m}"
        max-file: "${DOCKER_LOG_MAX_FILE:-3}"

volumes:
  immich-ml-cache:
```

---

## 5. Nginx Configuration

```nginx
# nginx/immich.conf
# Included when ENABLE_NGINX=true

upstream immich_server {
    server immich-server:2283;
    keepalive 32;
}

server {
    listen 80;
    server_name ${IMMICH_DOMAIN:-_};

    # Redirect to HTTPS if enabled
    # (uncomment when ENABLE_HTTPS=true)
    # return 301 https://$host$request_uri;

    client_max_body_size 50000M;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://immich_server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for large uploads
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        proxy_connect_timeout 600s;
    }
}

# HTTPS server block (when ENABLE_HTTPS=true)
# server {
#     listen 443 ssl http2;
#     server_name ${IMMICH_DOMAIN};
#
#     ssl_certificate /etc/letsencrypt/live/${IMMICH_DOMAIN}/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/${IMMICH_DOMAIN}/privkey.pem;
#     ssl_protocols TLSv1.2 TLSv1.3;
#     ssl_ciphers HIGH:!aNULL:!MD5;
#
#     client_max_body_size 50000M;
#
#     location / {
#         proxy_pass http://immich_server;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#         proxy_http_version 1.1;
#         proxy_set_header Upgrade $http_upgrade;
#         proxy_set_header Connection "upgrade";
#         proxy_read_timeout 600s;
#         proxy_send_timeout 600s;
#     }
# }
```

---

## 6. Shell Scripts

### 6.1 Setup Script — `scripts/setup.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Source environment
ENV_FILE="${1:-.env}"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: $ENV_FILE not found. Copy .env.default to .env first."
    exit 1
fi
source "$ENV_FILE"

echo "=== Immich Setup on Raspberry Pi ==="

# System updates
echo "[1/7] Updating system..."
sudo apt update && sudo apt upgrade -y

# Docker
echo "[2/7] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
fi

# SSD
echo "[3/7] Mounting SSD..."
if ! mountpoint -q "${SSD_MOUNT}"; then
    sudo mkdir -p "${SSD_MOUNT}"
    sudo mount "${SSD_DEVICE}" "${SSD_MOUNT}"
    grep -q "${SSD_DEVICE}" /etc/fstab || \
        echo "${SSD_DEVICE} ${SSD_MOUNT} ${SSD_FILESYSTEM} defaults,noatime,nofail 0 2" | sudo tee -a /etc/fstab
fi

# Directories
echo "[4/7] Creating directories..."
mkdir -p "${UPLOAD_LOCATION}" "${LIBRARY_LOCATION}" "${THUMB_LOCATION}" \
    "${ENCODED_VIDEO_LOCATION}" "${PROFILE_LOCATION}" "${BACKUP_LOCATION}" \
    "${DOCKER_VOLUMES_PATH}"

# Swap (Pi 4)
echo "[5/7] Configuring swap..."
if [[ "${SWAP_SIZE:-0}" != "0" ]] && [[ ! -f "${SWAP_FILE:-/swapfile}" ]]; then
    sudo fallocate -l "${SWAP_SIZE}" "${SWAP_FILE}"
    sudo chmod 600 "${SWAP_FILE}"
    sudo mkswap "${SWAP_FILE}"
    sudo swapon "${SWAP_FILE}"
    grep -q "${SWAP_FILE}" /etc/fstab || \
        echo "${SWAP_FILE} none swap sw 0 0" | sudo tee -a /etc/fstab
fi

# Deploy
echo "[6/7] Pulling Docker images..."
docker compose pull

echo "[7/7] Starting Immich..."
docker compose up -d

echo ""
echo "=== Immich is starting! ==="
echo "Web UI: http://${PI_HOST}:2283"
echo "Create your admin account on first visit."
```

### 6.2 Backup Script — `scripts/backup.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

source "${1:-.env}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${BACKUP_LOCATION}/backup_${TIMESTAMP}.log"

echo "=== Immich Backup — ${TIMESTAMP} ===" | tee "$LOG_FILE"

# Database dump
echo "[1/3] Dumping database..." | tee -a "$LOG_FILE"
docker exec -t immich-postgres pg_dumpall -c -U "${DB_USERNAME}" \
    > "${BACKUP_LOCATION}/db_${TIMESTAMP}.sql" 2>> "$LOG_FILE"

# Local rsync
if [[ "${BACKUP_LOCAL_ENABLED:-false}" == "true" ]]; then
    echo "[2/3] Syncing to local backup drive..." | tee -a "$LOG_FILE"
    rsync -avz --delete \
        "${UPLOAD_LOCATION}/" "${BACKUP_LOCAL_PATH}/upload/" >> "$LOG_FILE" 2>&1
    rsync -avz --delete \
        "${BACKUP_LOCATION}/" "${BACKUP_LOCAL_PATH}/db-dumps/" >> "$LOG_FILE" 2>&1
fi

# S3 sync
if [[ "${BACKUP_S3_ENABLED:-false}" == "true" ]]; then
    echo "[3/3] Syncing to S3..." | tee -a "$LOG_FILE"
    aws --endpoint-url "${BACKUP_S3_ENDPOINT}" s3 sync \
        "${UPLOAD_LOCATION}/" "s3://${BACKUP_S3_BUCKET}/upload/" >> "$LOG_FILE" 2>&1
    aws --endpoint-url "${BACKUP_S3_ENDPOINT}" s3 cp \
        "${BACKUP_LOCATION}/db_${TIMESTAMP}.sql" \
        "s3://${BACKUP_S3_BUCKET}/db-dumps/" >> "$LOG_FILE" 2>&1
fi

# Cleanup old backups
find "${BACKUP_LOCATION}" -name "db_*.sql" -mtime +${BACKUP_RETENTION_DAYS:-30} -delete

echo "=== Backup complete ===" | tee -a "$LOG_FILE"
```

### 6.3 Migration Script — `scripts/migrate-google-takeout.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${1:?Usage: $0 /path/to/google-takeout}"
source "${2:-.env}"

echo "=== Google Takeout → Immich Migration ==="
echo "Source: ${SOURCE_DIR}"

# Validate
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "ERROR: Source directory not found"
    exit 1
fi

# Copy to import staging area
STAGING="${MIGRATION_SOURCE_PATH:-/mnt/ssd/import}/google-takeout"
mkdir -p "$STAGING"

echo "[1/3] Copying photos to staging..."
find "$SOURCE_DIR" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \
    -o -iname "*.heic" -o -iname "*.mp4" -o -iname "*.mov" -o -iname "*.gif" \
    -o -iname "*.webp" -o -iname "*.raw" -o -iname "*.cr2" -o -iname "*.nef" \) \
    -exec cp -v {} "$STAGING/" \;

echo "[2/3] Applying JSON metadata (exiftool)..."
if command -v exiftool &>/dev/null; then
    find "$SOURCE_DIR" -name "*.json" -exec sh -c '
        json="$1"
        photo="${json%.json}"
        if [[ -f "$photo" ]]; then
            exiftool -overwrite_original -TagsFromFile "$json" "$photo" 2>/dev/null || true
        fi
    ' _ {} \;
else
    echo "WARNING: exiftool not installed — skipping metadata merge"
    echo "Install: sudo apt install libimage-exiftool-perl"
fi

echo "[3/3] Upload via Immich CLI..."
echo "Run: immich upload --recursive ${STAGING}/"
echo "Or use the Immich web UI to import from: ${STAGING}"

echo "=== Migration staging complete ==="
```

---

## 7. Cron Jobs

```bash
# /etc/cron.d/immich-backup
# Nightly backup at 2 AM
0 2 * * * root /home/pi/immich-app/scripts/backup.sh /home/pi/immich-app/.env >> /var/log/immich-backup.log 2>&1

# Storage monitoring alert (every 6 hours)
0 */6 * * * root df --output=pcent /mnt/ssd | tail -1 | tr -d ' %' | awk -v t="${MONITORING_ALERT_THRESHOLD_PERCENT:-85}" '{if ($1 > t) system("echo SSD usage: "$1"% | mail -s Immich-Storage-Alert root")}'
```

---

## 8. Security Considerations

| Area | Implementation |
|------|---------------|
| Database password | Generated via `openssl rand -base64 32` |
| Network binding | PostgreSQL/Redis bound to `127.0.0.1` only |
| HTTPS | Let's Encrypt via Certbot (when `ENABLE_HTTPS=true`) |
| Nginx headers | X-Content-Type-Options, X-Frame-Options, XSS-Protection |
| File permissions | `PUID`/`PGID` 1000, SSD owned by service user |
| SSD encryption | Optional LUKS full-disk encryption |
| Auth | LDAP/OIDC toggleable for enterprise environments |
| Docker | Non-root containers, limited port exposure |
| Backups | Encrypted S3 transport (TLS), local rsync |

---

## 9. Performance Expectations

| Operation | Pi 4 (4GB) | Pi 5 (8GB) |
|-----------|-----------|-----------|
| Photo upload (via app) | ~50–100/min | ~100–200/min |
| Thumbnail generation | ~2–5 sec/photo | ~1–2 sec/photo |
| Face detection (initial) | ~3–8 sec/photo | ~1–3 sec/photo |
| CLIP indexing | ~5–10 sec/photo | ~2–4 sec/photo |
| Video transcoding | Software only | HW accel available |
| Web UI response | ~1–3 sec | <1 sec |
| Library: 10K photos | Manageable | Smooth |
| Library: 50K+ photos | Needs swap + patience | Recommended |

---

## 10. File Structure

```
~/immich-app/
├── .env                          # Active configuration (from .env.default)
├── .env.default                  # Template with all options
├── docker-compose.yml            # Docker Compose orchestration
├── nginx/
│   └── immich.conf               # Nginx reverse proxy config
├── scripts/
│   ├── setup.sh                  # Initial deployment script
│   ├── backup.sh                 # Automated backup script
│   ├── migrate-google-takeout.sh # Google Takeout import
│   └── migrate-apple-photos.sh   # Apple Photos import
└── README.md                     # Documentation

/mnt/ssd/immich/
├── upload/                       # Original photos/videos
├── library/                      # Immich-managed library
├── thumbs/                       # Generated thumbnails
├── encoded-video/                # Transcoded videos
├── profile/                      # User profile images
└── backups/                      # DB dumps + metadata
```
