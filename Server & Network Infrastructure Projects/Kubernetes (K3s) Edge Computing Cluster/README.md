# Kubernetes (K3s) Edge Computing Cluster

Deploy K3s (lightweight Kubernetes by Rancher) on 2–4 Raspberry Pis to form an edge computing cluster. Learn container orchestration, service discovery, load balancing, and self-healing. Multi-node high availability with embedded etcd, GitOps with FluxCD, full monitoring stack (Prometheus + Grafana + Loki), Traefik ingress with cert-manager, MetalLB bare-metal load balancer, Longhorn distributed storage, private container registry, and example workloads (Nginx, Redis, PostgreSQL, Flask app, cron job). All setup is driven by shell scripts and Kubernetes YAML manifests — no custom web dashboard.

> **Edge-native:** Every component runs on ARM64 Raspberry Pi hardware. No cloud dependency after initial image pulls.

---

### Support This Project

If you find this project useful, consider supporting development:

**Bitcoin:** `bc1q...`

---

## Table of Contents

- [Project Structure](#project-structure)
- [Hardware Requirements](#hardware-requirements)
- [Budget](#budget)
- [Quickstart](#quickstart)
- [Environment Variables](#environment-variables)
- [Cluster Architecture](#cluster-architecture)
- [Features](#features)
  - [K3s Server & Agent Deployment](#k3s-server--agent-deployment)
  - [Multi-Node High Availability (etcd)](#multi-node-high-availability-etcd)
  - [GitOps with FluxCD](#gitops-with-fluxcd)
  - [Prometheus Metrics](#prometheus-metrics)
  - [Grafana Dashboards](#grafana-dashboards)
  - [Loki Log Aggregation](#loki-log-aggregation)
  - [Traefik Ingress & HTTPS](#traefik-ingress--https)
  - [MetalLB Bare-Metal Load Balancer](#metallb-bare-metal-load-balancer)
  - [Longhorn Distributed Storage](#longhorn-distributed-storage)
  - [Private Container Registry](#private-container-registry)
  - [Example Workloads](#example-workloads)
  - [Kubernetes Dashboard / Rancher UI](#kubernetes-dashboard--rancher-ui)
  - [Flannel / Calico Networking](#flannel--calico-networking)
- [Authentication & Security](#authentication--security)
- [Deployment](#deployment)
- [Running as systemd Services](#running-as-systemd-services)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [Where to Next](#where-to-next)

---

## Project Structure

```
Kubernetes (K3s) Edge Computing Cluster/
├── README.md                        # This file
├── TSD.md                           # Technical specification document
├── task.md                          # Task checklist by phase
├── implementation_plan.md           # Step-by-step implementation guide
├── .env.example                     # Environment variable template
├── scripts/
│   ├── 00-prereqs.sh                # Install OS dependencies on all nodes
│   ├── 01-init-server.sh            # Initialize K3s server (first control plane)
│   ├── 02-join-server.sh            # Join additional server nodes (HA etcd)
│   ├── 03-join-agent.sh             # Join agent (worker) nodes
│   ├── 04-install-helm.sh           # Install Helm on control node
│   ├── 05-install-metallb.sh        # Deploy MetalLB load balancer
│   ├── 06-install-longhorn.sh       # Deploy Longhorn distributed storage
│   ├── 07-install-monitoring.sh     # Deploy Prometheus + Grafana + Loki stack
│   ├── 08-install-cert-manager.sh   # Deploy cert-manager for TLS
│   ├── 09-install-registry.sh       # Deploy private container registry
│   ├── 10-install-fluxcd.sh         # Bootstrap FluxCD GitOps
│   ├── 11-install-dashboard.sh      # Deploy Kubernetes Dashboard or Rancher
│   ├── 12-deploy-workloads.sh       # Deploy example workloads
│   ├── reset-node.sh                # Uninstall K3s and clean up a node
│   ├── backup-etcd.sh               # Snapshot etcd to file
│   └── status.sh                    # Cluster health check summary
├── manifests/
│   ├── metallb/
│   │   ├── namespace.yaml
│   │   ├── ip-pool.yaml             # Address pool for LB IPs
│   │   └── l2-advertisement.yaml
│   ├── longhorn/
│   │   └── values.yaml              # Helm values override
│   ├── monitoring/
│   │   ├── namespace.yaml
│   │   ├── prometheus-values.yaml   # kube-prometheus-stack values
│   │   ├── loki-values.yaml         # Loki + Promtail values
│   │   └── grafana-dashboards/
│   │       ├── cluster-overview.json
│   │       └── node-exporter.json
│   ├── ingress/
│   │   ├── traefik-values.yaml      # Traefik Helm values
│   │   └── cert-manager/
│   │       ├── cluster-issuer.yaml  # Let's Encrypt ClusterIssuer
│   │       └── wildcard-cert.yaml
│   ├── registry/
│   │   ├── namespace.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   ├── dashboard/
│   │   ├── admin-user.yaml          # ServiceAccount + ClusterRoleBinding
│   │   └── values.yaml
│   ├── fluxcd/
│   │   ├── gotk-components.yaml     # FluxCD toolkit components
│   │   └── gotk-sync.yaml           # Git repository sync
│   └── workloads/
│       ├── nginx/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   └── ingress.yaml
│       ├── redis/
│       │   ├── deployment.yaml
│       │   └── service.yaml
│       ├── postgres/
│       │   ├── statefulset.yaml
│       │   ├── service.yaml
│       │   ├── pvc.yaml
│       │   └── secret.yaml
│       ├── flask-app/
│       │   ├── deployment.yaml
│       │   ├── service.yaml
│       │   ├── ingress.yaml
│       │   └── configmap.yaml
│       └── cron-job/
│           └── cronjob.yaml
├── deploy/
│   └── deploy_to_cluster.sh         # Rsync scripts & manifests to control node
└── docs/
    ├── network-diagram.md           # Cluster network topology
    └── disaster-recovery.md         # Backup & restore procedures
```

---

## Hardware Requirements

| Component | Required | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB+) / Pi 5 | **Yes** (2–4 units) | 4 GB minimum; 8 GB recommended for server nodes |
| MicroSD Card (32 GB+) | **Yes** (per node) | Class 10 / A2 for etcd and Longhorn I/O |
| Ethernet Cable (Cat5e+) | **Yes** (per node) | Wired networking required for reliable cluster comms |
| Network Switch (5+ port) | **Yes** | Gigabit recommended |
| Power Supply (5V 3A+) | **Yes** (per node) | Official Pi PSU or PoE HAT |
| PoE HAT | Optional | Eliminates separate power supplies; requires PoE switch |
| USB SSD / NVMe (via USB) | Optional | Better Longhorn performance than microSD |

---

## Budget

| Item | Cost (per unit) | Qty (3-node) | Subtotal |
|---|---|---|---|
| Raspberry Pi 4 (4 GB) / Pi 5 | $35–80 | 3 | $105–240 |
| MicroSD Card (32 GB A2) | ~$8 | 3 | ~$24 |
| Ethernet Cable (1 m) | ~$3 | 3 | ~$9 |
| Gigabit Network Switch (5-port) | ~$15 | 1 | ~$15 |
| PoE HAT (optional) | ~$15 | 3 | ~$45 |
| **Total (without PoE)** | | | **~$153–288** |
| **Total (with PoE)** | | | **~$198–333** |

---

## Quickstart

### 1. Prepare All Nodes

Flash Raspberry Pi OS Lite (64-bit, Bookworm) on each microSD card. Enable SSH in the imager settings. Set unique hostnames (`k3s-server-1`, `k3s-server-2`, `k3s-agent-1`, etc.) and configure static IPs.

```bash
# From your development machine — copy scripts to control node
scp -r scripts/ manifests/ .env.example rasp-pi:~/k3s-cluster/
ssh rasp-pi
cd ~/k3s-cluster
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env    # Set node IPs, tokens, feature flags
```

### 3. Install Prerequisites (All Nodes)

```bash
# Run on each node (or use SSH loop)
bash scripts/00-prereqs.sh
```

This installs: `curl`, `open-iscsi` (Longhorn), `nfs-common`, disables swap, enables cgroups.

### 4. Initialize First Server Node

```bash
# On the first server node (e.g., k3s-server-1 at 192.168.216.90)
bash scripts/01-init-server.sh
```

This installs K3s in server mode with embedded etcd. Retrieve the node token:

```bash
sudo cat /var/lib/rancher/k3s/server/node-token
```

### 5. Join Additional Nodes

```bash
# On each additional server node (HA mode)
K3S_URL="https://192.168.216.90:6443" K3S_TOKEN="<token>" bash scripts/02-join-server.sh

# On each agent/worker node
K3S_URL="https://192.168.216.90:6443" K3S_TOKEN="<token>" bash scripts/03-join-agent.sh
```

### 6. Verify Cluster

```bash
sudo kubectl get nodes -o wide
# Should show all nodes in Ready state
```

### 7. Deploy Add-ons

```bash
bash scripts/04-install-helm.sh
bash scripts/05-install-metallb.sh
bash scripts/06-install-longhorn.sh
bash scripts/07-install-monitoring.sh
bash scripts/08-install-cert-manager.sh
bash scripts/09-install-registry.sh
bash scripts/10-install-fluxcd.sh
bash scripts/11-install-dashboard.sh
bash scripts/12-deploy-workloads.sh
```

### 8. Access Services

| Service | URL |
|---|---|
| Kubernetes Dashboard | `https://192.168.216.90:8443` |
| Grafana | `http://192.168.216.90:3000` |
| Prometheus | `http://192.168.216.90:9090` |
| Longhorn UI | `http://192.168.216.90:8080` |
| Traefik Dashboard | `http://192.168.216.90:9000` |
| Example Nginx | `http://<METALLB_IP>` |

---

## Environment Variables

All features are toggleable via `.env`. Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|---|---|---|
| `CLUSTER_NAME` | `k3s-edge` | Cluster display name |
| `K3S_VERSION` | `v1.31.4+k3s1` | K3s release version |
| `K3S_TOKEN` | *(generated)* | Shared secret for node join |
| `SERVER_IP_1` | `192.168.216.90` | First server node IP (control plane) |
| `SERVER_IP_2` | `` | Second server node IP (HA) |
| `SERVER_IP_3` | `` | Third server node IP (HA) |
| `AGENT_IPS` | `` | Comma-separated agent node IPs |
| `SSH_USER` | `pi` | SSH username for remote nodes |
| `SSH_KEY_PATH` | `~/.ssh/id_rsa` | SSH private key path |
| `ENABLE_HA` | `true` | Enable multi-node HA with embedded etcd |
| `ENABLE_METALLB` | `true` | Deploy MetalLB bare-metal load balancer |
| `METALLB_IP_RANGE` | `192.168.216.200-192.168.216.220` | IP pool for LoadBalancer services |
| `ENABLE_LONGHORN` | `true` | Deploy Longhorn distributed storage |
| `LONGHORN_REPLICA_COUNT` | `2` | Default volume replica count |
| `ENABLE_MONITORING` | `true` | Deploy Prometheus + Grafana stack |
| `GRAFANA_ADMIN_PASSWORD` | `change-me` | Grafana admin password |
| `ENABLE_LOKI` | `true` | Deploy Loki + Promtail log aggregation |
| `ENABLE_TRAEFIK` | `true` | Use Traefik as ingress controller (bundled) |
| `ENABLE_CERT_MANAGER` | `false` | Deploy cert-manager for TLS certificates |
| `CERT_MANAGER_EMAIL` | `` | Email for Let's Encrypt registration |
| `ENABLE_REGISTRY` | `false` | Deploy private container registry |
| `REGISTRY_STORAGE_SIZE` | `10Gi` | PVC size for registry storage |
| `ENABLE_FLUXCD` | `false` | Bootstrap FluxCD GitOps |
| `FLUX_GIT_REPO` | `` | Git repository URL for FluxCD sync |
| `FLUX_GIT_BRANCH` | `main` | Branch to track |
| `FLUX_GIT_TOKEN` | `` | Git personal access token (for private repos) |
| `ENABLE_DASHBOARD` | `true` | Deploy Kubernetes Dashboard |
| `DASHBOARD_TYPE` | `kubernetes-dashboard` | `kubernetes-dashboard` or `rancher` |
| `ENABLE_EXAMPLE_WORKLOADS` | `true` | Deploy example apps (Nginx, Redis, etc.) |
| `CNI_PLUGIN` | `flannel` | Network plugin: `flannel` (default) or `calico` |
| `POD_CIDR` | `10.42.0.0/16` | Pod network CIDR |
| `SERVICE_CIDR` | `10.43.0.0/16` | Service network CIDR |
| `ENABLE_ETCD_BACKUP` | `true` | Enable scheduled etcd snapshots |
| `ETCD_BACKUP_SCHEDULE` | `0 */6 * * *` | Cron schedule for etcd backups |
| `ETCD_BACKUP_RETENTION` | `5` | Number of snapshots to retain |
| `KUBECONFIG_PATH` | `/etc/rancher/k3s/k3s.yaml` | Path to kubeconfig file |

---

## Cluster Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        K3s Edge Computing Cluster                            │
│                                                                              │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌─────────────────┐  │
│  │ k3s-server-1 (Pi)     │  │ k3s-server-2 (Pi)     │  │ k3s-agent-1 (Pi)│  │
│  │ 192.168.216.90        │  │ 192.168.216.91        │  │ 192.168.216.92  │  │
│  │ Role: server+etcd     │  │ Role: server+etcd     │  │ Role: agent     │  │
│  │ ┌───────────────────┐ │  │ ┌───────────────────┐ │  │ ┌─────────────┐ │  │
│  │ │ K3s Server        │ │  │ │ K3s Server        │ │  │ │ K3s Agent   │ │  │
│  │ │ API Server        │ │  │ │ API Server        │ │  │ │ kubelet     │ │  │
│  │ │ etcd (embedded)   │ │  │ │ etcd (embedded)   │ │  │ │ kube-proxy  │ │  │
│  │ │ Scheduler         │ │  │ │ Scheduler         │ │  │ └─────────────┘ │  │
│  │ │ Controller Mgr    │ │  │ │ Controller Mgr    │ │  │ ┌─────────────┐ │  │
│  │ └───────────────────┘ │  │ └───────────────────┘ │  │ │ Workloads   │ │  │
│  │ ┌───────────────────┐ │  │ ┌───────────────────┐ │  │ │ Nginx,Redis │ │  │
│  │ │ Traefik Ingress   │ │  │ │ Traefik Ingress   │ │  │ │ Postgres    │ │  │
│  │ │ MetalLB Speaker   │ │  │ │ MetalLB Speaker   │ │  │ │ Flask App   │ │  │
│  │ │ Longhorn Mgr      │ │  │ │ Longhorn Mgr      │ │  │ │ CronJobs    │ │  │
│  │ └───────────────────┘ │  │ └───────────────────┘ │  │ └─────────────┘ │  │
│  └───────────┬───────────┘  └───────────┬───────────┘  └────────┬────────┘  │
│              │                           │                       │            │
│              └───────────────┬───────────┘                       │            │
│                              │                                   │            │
│                    ┌─────────┴───────────┐                       │            │
│                    │ Embedded etcd       │                       │            │
│                    │ (HA quorum: 2 of 3) │                       │            │
│                    └─────────────────────┘                       │            │
│                                                                  │            │
│  ┌───────────────────────────────────────────────────────────────┘           │
│  │                                                                           │
│  │  Cluster Services (scheduled across all nodes):                          │
│  │  ┌──────────────┐ ┌────────────┐ ┌───────────┐ ┌──────────────────────┐ │
│  │  │ Prometheus   │ │ Grafana    │ │ Loki      │ │ Kubernetes Dashboard │ │
│  │  │ + Exporters  │ │ Dashboards │ │ + Promtail│ │ or Rancher UI       │ │
│  │  └──────────────┘ └────────────┘ └───────────┘ └──────────────────────┘ │
│  │  ┌──────────────┐ ┌────────────┐ ┌───────────┐ ┌──────────────────────┐ │
│  │  │ MetalLB      │ │ Longhorn   │ │ FluxCD    │ │ cert-manager         │ │
│  │  │ (L2 mode)    │ │ Storage    │ │ GitOps    │ │ (Let's Encrypt)      │ │
│  │  └──────────────┘ └────────────┘ └───────────┘ └──────────────────────┘ │
│  │  ┌──────────────┐                                                       │
│  │  │ Private      │                                                       │
│  │  │ Registry     │                                                       │
│  │  └──────────────┘                                                       │
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Network: Flannel/Calico CNI │ Pods: 10.42.0.0/16 │ Svc: 10.43.0.0/16│  │
│  │ MetalLB External IPs: 192.168.216.200–220                            │  │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Features

### K3s Server & Agent Deployment

K3s is a CNCF-certified lightweight Kubernetes distribution by Rancher. It replaces etcd with SQLite (single-node) or embedded etcd (HA), bundles containerd, Flannel, CoreDNS, and Traefik. Installs with a single `curl` command per node.

- Server nodes run the API server, scheduler, controller manager, and etcd
- Agent nodes run kubelet and kube-proxy, accepting workloads
- Toggle: All nodes are deployed via `scripts/01-init-server.sh` and `scripts/03-join-agent.sh`

### Multi-Node High Availability (etcd)

Three server nodes form an etcd quorum for fault tolerance. If one server node fails, the cluster continues operating. Automatic leader election ensures no single point of failure for the control plane.

- Toggle: `ENABLE_HA=true`
- Requires: At least 3 server nodes (`SERVER_IP_1`, `SERVER_IP_2`, `SERVER_IP_3`)
- Backup: `ENABLE_ETCD_BACKUP=true` with configurable schedule

### GitOps with FluxCD

FluxCD continuously reconciles the cluster state with a Git repository. Push YAML manifests to Git and FluxCD automatically applies them. Supports Kustomize, Helm charts, and plain manifests.

- Toggle: `ENABLE_FLUXCD=true`
- Config: `FLUX_GIT_REPO`, `FLUX_GIT_BRANCH`, `FLUX_GIT_TOKEN`
- Bootstrap: `scripts/10-install-fluxcd.sh`

### Prometheus Metrics

Collects cluster-wide metrics using kube-prometheus-stack: node CPU/memory/disk, pod resource usage, API server latency, etcd health, Kubernetes object counts. Prometheus server runs in-cluster with persistent storage via Longhorn.

- Toggle: `ENABLE_MONITORING=true`
- Access: `http://192.168.216.90:9090`
- Retention: Configurable in `manifests/monitoring/prometheus-values.yaml`

### Grafana Dashboards

Pre-configured Grafana with dashboards for cluster overview, node exporter metrics, pod resource usage, and Kubernetes API health. Dark theme enabled by default. Provisioned dashboards auto-load on deployment.

- Toggle: `ENABLE_MONITORING=true`
- Access: `http://192.168.216.90:3000` (admin / `GRAFANA_ADMIN_PASSWORD`)
- Dashboards: `manifests/monitoring/grafana-dashboards/`

### Loki Log Aggregation

Loki collects logs from all pods via Promtail DaemonSet. Query logs in Grafana using LogQL. Lightweight alternative to Elasticsearch — designed for Kubernetes on resource-constrained hardware.

- Toggle: `ENABLE_LOKI=true`
- Config: `manifests/monitoring/loki-values.yaml`
- Query: Grafana → Explore → Loki datasource

### Traefik Ingress & HTTPS

Traefik is the default K3s ingress controller. Routes external HTTP/HTTPS traffic to services based on hostname or path rules. Combined with cert-manager, auto-provisions Let's Encrypt TLS certificates.

- Toggle: `ENABLE_TRAEFIK=true` (bundled with K3s by default)
- HTTPS: `ENABLE_CERT_MANAGER=true`, `CERT_MANAGER_EMAIL=you@example.com`
- Config: `manifests/ingress/traefik-values.yaml`

### MetalLB Bare-Metal Load Balancer

MetalLB provides `LoadBalancer`-type services on bare-metal clusters (no cloud provider needed). Assigns IP addresses from a configurable pool to services, making them accessible on the LAN.

- Toggle: `ENABLE_METALLB=true`
- IP pool: `METALLB_IP_RANGE=192.168.216.200-192.168.216.220`
- Mode: L2 (ARP-based, no BGP router required)

### Longhorn Distributed Storage

Longhorn provides replicated block storage across nodes. Volumes survive node failure with configurable replica count. Includes a management UI, scheduled backups, and snapshot support.

- Toggle: `ENABLE_LONGHORN=true`
- Replicas: `LONGHORN_REPLICA_COUNT=2`
- UI: `http://192.168.216.90:8080`
- Requirements: `open-iscsi` installed on all nodes

### Private Container Registry

Self-hosted container registry (Docker Distribution or Harbor) for storing custom images without relying on Docker Hub. Useful for air-gapped deployments and custom application images.

- Toggle: `ENABLE_REGISTRY=true`
- Storage: `REGISTRY_STORAGE_SIZE=10Gi` (Longhorn PVC)
- Push: `docker push 192.168.216.90:5000/myapp:latest`

### Example Workloads

Pre-built manifests demonstrating common Kubernetes patterns:

| Workload | Pattern | Description |
|---|---|---|
| **Nginx** | Deployment + Service + Ingress | Stateless web server with external access |
| **Redis** | Deployment + ClusterIP Service | In-cluster cache, no external exposure |
| **PostgreSQL** | StatefulSet + PVC + Secret | Stateful database with persistent Longhorn volume |
| **Flask App** | Deployment + ConfigMap + Ingress | Custom app with environment config |
| **Cron Job** | CronJob | Scheduled task (e.g., cleanup, backup) |

- Toggle: `ENABLE_EXAMPLE_WORKLOADS=true`
- Manifests: `manifests/workloads/`

### Kubernetes Dashboard / Rancher UI

Web-based cluster management UI. Kubernetes Dashboard provides resource visualization and basic management. Rancher offers a full management platform with multi-cluster support.

- Toggle: `ENABLE_DASHBOARD=true`
- Type: `DASHBOARD_TYPE=kubernetes-dashboard` or `rancher`
- Access: `https://192.168.216.90:8443` (token-based auth)

### Flannel / Calico Networking

Flannel (default in K3s) provides simple VXLAN overlay networking. Calico adds network policy enforcement for pod-level firewall rules. Switch via `.env` before cluster initialization.

- Config: `CNI_PLUGIN=flannel` or `calico`
- Pod CIDR: `POD_CIDR=10.42.0.0/16`
- Service CIDR: `SERVICE_CIDR=10.43.0.0/16`

---

## Authentication & Security

- **Kubernetes RBAC** — role-based access control for all API operations
- **Dashboard token auth** — ServiceAccount token required for Dashboard login
- **Grafana auth** — admin password set via `GRAFANA_ADMIN_PASSWORD`
- **bcrypt password hashing** — used in helper scripts for any local auth needs (10 req / 15 min rate limit, 24h session expiry)
- **TLS everywhere** — cert-manager auto-provisions certificates for ingress
- **Network policies** — Calico enables pod-to-pod firewall rules
- **etcd encryption** — K3s supports encryption at rest for secrets

Generate a Kubernetes Dashboard token:

```bash
kubectl -n kubernetes-dashboard create token admin-user
```

Access the dashboard:

```bash
# Port-forward if not using ingress
kubectl port-forward -n kubernetes-dashboard svc/kubernetes-dashboard 8443:443
# Open https://localhost:8443 and paste the token
```

---

## Deployment

### Deploy via SCP

```bash
# From development machine — sync to control node
scp -r scripts/ manifests/ .env rasp-pi:~/k3s-cluster/
```

### Deploy Script

```bash
chmod +x deploy/deploy_to_cluster.sh
./deploy/deploy_to_cluster.sh
```

The deploy script:
1. Syncs scripts and manifests to `rasp-pi` (192.168.216.90)
2. SSHs to each node and runs prerequisite setup
3. Initializes the K3s server on the first control-plane node
4. Joins additional server and agent nodes
5. Deploys enabled add-ons (MetalLB, Longhorn, monitoring, etc.)

### Remote Node Setup via SSH

```bash
# Loop over all nodes from control machine
for NODE in 192.168.216.90 192.168.216.91 192.168.216.92; do
  ssh pi@${NODE} "bash ~/k3s-cluster/scripts/00-prereqs.sh"
done
```

---

## Running as systemd Services

K3s installs its own systemd services automatically:

```bash
# Server node service
sudo systemctl status k3s

# Agent node service
sudo systemctl status k3s-agent

# View logs
sudo journalctl -u k3s -f
sudo journalctl -u k3s-agent -f

# Restart
sudo systemctl restart k3s
sudo systemctl restart k3s-agent
```

K3s starts on boot by default. To disable:

```bash
sudo systemctl disable k3s
```

---

## Security Notes

- **Control plane access** — restrict `kubectl` access via RBAC. Do not share the `k3s.yaml` kubeconfig without scoping it.
- **etcd encryption** — enable `--secrets-encryption` flag for K3s to encrypt secrets at rest.
- **Network policies** — use Calico CNI for pod-level firewall rules. Default-deny ingress is recommended for production.
- **No public exposure** — keep the cluster on a private LAN. Use VPN for remote access.
- **Image scanning** — scan container images for vulnerabilities before deploying (Trivy, Grype).
- **Pod Security Standards** — enforce restricted Pod Security Admission (PSA) on namespaces.
- **Rotate tokens** — periodically rotate the `K3S_TOKEN` and Kubernetes ServiceAccount tokens.
- **SD card encryption** — consider LUKS full-disk encryption on each node.
- **Update regularly** — `k3s` self-updates can be enabled, or run `curl -sfL https://get.k3s.io | sh -` to update.
- **Physical security** — lock nodes in a secure location; anyone with SD card access has cluster credentials.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Node not joining cluster | Verify `K3S_TOKEN` matches. Check firewall allows port 6443. Run `sudo journalctl -u k3s-agent -f`. |
| `kubectl` connection refused | Ensure K3s server is running: `sudo systemctl status k3s`. Check `KUBECONFIG` is set. |
| Pods stuck in `Pending` | Check node resources: `kubectl describe pod <name>`. Verify Longhorn PVCs are bound. |
| MetalLB not assigning IPs | Verify `METALLB_IP_RANGE` doesn't overlap with DHCP. Check L2 advertisement config. |
| Longhorn volumes degraded | Verify `open-iscsi` is installed on all nodes. Check replica count vs. available nodes. |
| Grafana not loading dashboards | Check Prometheus is running: `kubectl -n monitoring get pods`. Verify datasource config. |
| Traefik 404 errors | Verify ingress rules match hostname. Check `kubectl get ingress -A`. |
| etcd leader election failure | Need odd number of servers (1 or 3). Check network connectivity between server nodes. |
| High CPU on Pi | Reduce monitoring scrape interval. Disable Loki on resource-constrained nodes. |
| `cgroup` errors on boot | Ensure `/boot/firmware/cmdline.txt` contains `cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory`. |
| Image pull failures | Check registry credentials. For private registry, configure `registries.yaml` on each node. |
| DNS resolution fails | Check CoreDNS pods: `kubectl -n kube-system get pods -l k8s-app=kube-dns`. |

---

## Where to Next

- **Service mesh** — install Linkerd or Istio for mTLS, traffic splitting, and observability
- **Argo CD** — alternative GitOps engine to FluxCD with a rich web UI
- **Velero backup** — cluster-wide backup and disaster recovery to S3-compatible storage
- **Horizontal Pod Autoscaler** — auto-scale workloads based on CPU/memory metrics
- **Raspberry Pi cluster case** — 3D print or buy a stacking case for clean rack mounting
- **PoE-powered cluster** — PoE HATs + PoE switch for single-cable power and data
- **Multi-cluster federation** — connect multiple K3s clusters with Liqo or Submariner
- **Edge AI inference** — deploy TensorFlow Lite or ONNX Runtime as a Kubernetes workload
- **CI/CD pipeline** — Tekton or Drone CI running in-cluster for build-test-deploy
- **Virtual kubelet** — extend cluster capacity to cloud VMs during peak load
- **GPU acceleration** — Coral USB Accelerator with K3s device plugin for ML inference
- **ArgoRollouts** — progressive delivery with canary and blue-green deployments
