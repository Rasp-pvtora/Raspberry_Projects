# Technical Specification Document — Kubernetes (K3s) Edge Computing Cluster

## 1. Project Scope

Deploy K3s (lightweight Kubernetes by Rancher) on 2–4 Raspberry Pis to form an edge computing cluster. The project covers full cluster lifecycle: node provisioning, K3s installation, multi-node high availability with embedded etcd, networking (Flannel/Calico), ingress (Traefik + cert-manager), load balancing (MetalLB), distributed storage (Longhorn), monitoring (Prometheus + Grafana + Loki), GitOps (FluxCD), private container registry, Kubernetes Dashboard or Rancher UI, and example workloads. All setup is driven by shell scripts and Kubernetes YAML manifests.

**Target hardware:** 2–4 Raspberry Pi 4 (4 GB+) / Pi 5 with Ethernet networking and network switch.

**Primary interface:** `kubectl` CLI, Kubernetes Dashboard / Rancher web UI, Grafana dashboards.

---

## 2. Feature Tiers

### P0 — MVP (Must Have)

| Feature | Description |
|---|---|
| K3s server installation | Single-node K3s server with embedded SQLite |
| K3s agent join | Agent nodes join cluster via token |
| kubectl access | kubeconfig on server node, copy to dev machine |
| Traefik ingress | Built-in ingress controller (bundled with K3s) |
| Flannel CNI | Default overlay networking |
| MetalLB load balancer | L2 mode, configurable IP pool for LAN access |
| Longhorn storage | Distributed block storage across nodes |
| Prometheus + Grafana | Cluster metrics and visualization (dark theme) |
| Example workloads | Nginx, Redis, PostgreSQL, Flask app, cron job |
| Kubernetes Dashboard | Web UI for cluster resource management |
| Helper scripts | Numbered bash scripts for each setup step |
| Configuration | All features toggleable via `.env` |

### P1 — Nice to Have

| Feature | Description |
|---|---|
| Multi-node HA (etcd) | 3-node embedded etcd quorum for fault tolerance |
| Loki log aggregation | Centralized log collection + Grafana LogQL |
| cert-manager | Automated TLS certificates (Let's Encrypt) |
| FluxCD GitOps | Continuous reconciliation from Git repo |
| Private registry | Self-hosted container image registry |
| Calico CNI | Network policy enforcement as alternative to Flannel |
| Rancher UI | Full cluster management platform (alternative to Dashboard) |
| Scheduled etcd backups | Cron-based etcd snapshots with retention |
| Disaster recovery docs | Backup, restore, and failover procedures |

---

## 3. Node Roles & Cluster Topology

### Role Definitions

| Role | K3s Component | Responsibilities |
|---|---|---|
| **Server (control plane)** | `k3s server` | API server, scheduler, controller manager, etcd |
| **Agent (worker)** | `k3s agent` | kubelet, kube-proxy, runs workload pods |
| **Server + Agent** | `k3s server` | Control plane duties + accepts workload pods (default for small clusters) |

### Recommended Topologies

| Cluster Size | Topology | HA | Notes |
|---|---|---|---|
| 2 nodes | 1 server + 1 agent | No | Simplest setup, server is SPOF |
| 3 nodes | 3 servers (etcd) | Yes | Full HA, all nodes accept workloads |
| 4 nodes | 3 servers + 1 agent | Yes | Dedicated worker for heavy workloads |

### Node Assignment (Default)

| Hostname | IP | Role | Hardware |
|---|---|---|---|
| `k3s-server-1` | `192.168.216.90` | Server + etcd (init) | Pi 4/5 (4–8 GB) |
| `k3s-server-2` | `192.168.216.91` | Server + etcd (join) | Pi 4/5 (4–8 GB) |
| `k3s-server-3` | `192.168.216.92` | Server + etcd (join) | Pi 4/5 (4–8 GB) |
| `k3s-agent-1` | `192.168.216.93` | Agent (worker) | Pi 4/5 (4+ GB) |

---

## 4. Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Physical Layer                                  │
│                                                                          │
│   [Pi: k3s-server-1]  [Pi: k3s-server-2]  [Pi: k3s-server-3]          │
│   192.168.216.90       192.168.216.91       192.168.216.92              │
│         │                    │                    │                      │
│         └────────────────────┼────────────────────┘                      │
│                              │                                           │
│                    [Gigabit Network Switch]                              │
│                              │                                           │
│                    [Pi: k3s-agent-1]                                     │
│                    192.168.216.93                                        │
└──────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                        Kubernetes Layer                                  │
│                                                                          │
│  Control Plane (x3 HA):                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐       │
│  │ kube-apiserver │  │ kube-scheduler │  │ controller-manager  │       │
│  └────────────────┘  └────────────────┘  └─────────────────────┘       │
│  ┌─────────────────────────────────────────────┐                        │
│  │ Embedded etcd (3-node quorum, raft consensus)│                       │
│  └─────────────────────────────────────────────┘                        │
│                                                                          │
│  Node Services (all nodes):                                             │
│  ┌──────────┐  ┌────────────┐  ┌──────────────┐                        │
│  │ kubelet  │  │ kube-proxy │  │ containerd   │                        │
│  └──────────┘  └────────────┘  └──────────────┘                        │
│                                                                          │
│  Networking:                                                            │
│  ┌────────────────┐  ┌─────────┐  ┌────────────────┐                   │
│  │ Flannel/Calico │  │ CoreDNS │  │ Traefik Ingress│                   │
│  │ (CNI plugin)   │  │         │  │ (+ cert-manager)│                  │
│  └────────────────┘  └─────────┘  └────────────────┘                   │
│                                                                          │
│  Storage & Load Balancing:                                              │
│  ┌──────────────────┐  ┌──────────────────────────┐                    │
│  │ Longhorn         │  │ MetalLB (L2 mode)        │                    │
│  │ (replicated PVs) │  │ External IP: .200–.220   │                    │
│  └──────────────────┘  └──────────────────────────┘                    │
│                                                                          │
│  Observability:                                                         │
│  ┌────────────┐  ┌─────────┐  ┌──────────────────┐                    │
│  │ Prometheus │  │ Grafana │  │ Loki + Promtail  │                    │
│  │ + Exporters│  │ (dark)  │  │ (log aggregation)│                    │
│  └────────────┘  └─────────┘  └──────────────────┘                    │
│                                                                          │
│  GitOps & Management:                                                   │
│  ┌──────────┐  ┌───────────────────┐  ┌──────────────────┐            │
│  │ FluxCD   │  │ K8s Dashboard /   │  │ Private Registry │            │
│  │ (sync)   │  │ Rancher UI        │  │ (Harbor/distrib) │            │
│  └──────────┘  └───────────────────┘  └──────────────────┘            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Threat Model

| Threat | Impact | Mitigation |
|---|---|---|
| Unauthorized API access | Cluster compromise | RBAC, kubeconfig scoped to roles, do not expose 6443 publicly |
| etcd data exposure | Secret leakage | Enable `--secrets-encryption`, restrict etcd port (2379/2380) |
| Container escape | Node compromise | Pod Security Standards (restricted), minimal base images |
| Network sniffing between pods | Data interception | Calico network policies, Flannel with WireGuard encryption |
| Malicious container images | Workload compromise | Image scanning (Trivy), private registry, signed images |
| Dashboard token theft | Cluster admin access | Short-lived tokens, restrict Dashboard to read-only role |
| Node physical theft | Full cluster access | LUKS disk encryption, remote wipe capability |
| Supply chain attack (Helm charts) | Malicious deployments | Pin chart versions, verify signatures, audit values |
| DDoS on ingress | Service unavailability | Rate limiting in Traefik, MetalLB IP filtering |
| Unpatched K3s | Known CVE exploitation | Enable auto-update or scheduled manual updates |
| Stale etcd backups | Data loss on failure | Scheduled backups (`ETCD_BACKUP_SCHEDULE`), off-node copies |
| Brute-force Grafana login | Monitoring access | Strong `GRAFANA_ADMIN_PASSWORD`, network-level access control |

---

## 6. Tech Stack

| Layer | Technology |
|---|---|
| Hardware | 2–4 Raspberry Pi 4/5, Gigabit Switch, Ethernet |
| OS | Raspberry Pi OS Lite (64-bit, Bookworm) |
| Container Runtime | containerd (bundled with K3s) |
| Orchestration | K3s (lightweight Kubernetes) |
| CNI | Flannel (default) / Calico (optional) |
| Ingress | Traefik 2.x (bundled with K3s) |
| TLS | cert-manager + Let's Encrypt |
| Load Balancer | MetalLB (L2 mode) |
| Storage | Longhorn distributed block storage |
| Monitoring | Prometheus (kube-prometheus-stack) |
| Visualization | Grafana (dark theme) |
| Logging | Loki + Promtail |
| GitOps | FluxCD |
| Registry | Docker Distribution / Harbor |
| Dashboard | Kubernetes Dashboard / Rancher |
| DNS | CoreDNS (bundled with K3s) |
| Scripting | Bash (setup scripts) |
| Manifests | Kubernetes YAML + Helm charts |
| Config | `.env` file (sourced by bash scripts) |
| Deployment | SCP / rsync to `rasp-pi` (192.168.216.90) |

---

## 7. Implementation Phases

### Phase 1 — Foundation & Single-Node K3s

- Project scaffolding (directory structure, `.env`, scripts skeleton)
- OS hardening and prerequisite installation on all nodes
- K3s single-server installation
- kubectl access verification
- Basic networking validation (CoreDNS, Flannel)

### Phase 2 — Multi-Node HA & Networking

- Join additional server nodes (embedded etcd HA)
- Join agent nodes
- Verify etcd quorum and leader election
- CNI selection (Flannel default, Calico optional)
- Network policy testing (if Calico)

### Phase 3 — Storage & Load Balancing

- MetalLB deployment and IP pool configuration
- Longhorn deployment and default StorageClass
- PVC provisioning verification
- Volume replication and failover testing

### Phase 4 — Monitoring & Observability

- kube-prometheus-stack deployment (Prometheus + Grafana)
- Grafana dashboard provisioning (cluster overview, node exporter)
- Loki + Promtail deployment
- Alert rules configuration
- Dark theme Grafana configuration

### Phase 5 — Ingress, TLS & Add-ons

- Traefik configuration and custom values
- cert-manager deployment and ClusterIssuer
- Private registry deployment
- Kubernetes Dashboard / Rancher deployment
- FluxCD bootstrap

### Phase 6 — Example Workloads & Hardening

- Deploy all example workloads (Nginx, Redis, PostgreSQL, Flask app, cron job)
- Verify ingress routing, storage, and service discovery
- etcd backup automation
- Security hardening (RBAC, PSA, network policies)
- Documentation finalization

---

## 8. Default Environment Configuration

```ini
# .env.default — Kubernetes (K3s) Edge Computing Cluster

# --- Cluster ---
CLUSTER_NAME=k3s-edge
K3S_VERSION=v1.31.4+k3s1
K3S_TOKEN=
KUBECONFIG_PATH=/etc/rancher/k3s/k3s.yaml

# --- Node IPs ---
SERVER_IP_1=192.168.216.90
SERVER_IP_2=
SERVER_IP_3=
AGENT_IPS=

# --- SSH ---
SSH_USER=pi
SSH_KEY_PATH=~/.ssh/id_rsa

# --- High Availability ---
ENABLE_HA=true

# --- Networking ---
CNI_PLUGIN=flannel
POD_CIDR=10.42.0.0/16
SERVICE_CIDR=10.43.0.0/16

# --- MetalLB ---
ENABLE_METALLB=true
METALLB_IP_RANGE=192.168.216.200-192.168.216.220

# --- Longhorn Storage ---
ENABLE_LONGHORN=true
LONGHORN_REPLICA_COUNT=2

# --- Monitoring (Prometheus + Grafana) ---
ENABLE_MONITORING=true
GRAFANA_ADMIN_PASSWORD=change-me

# --- Loki Log Aggregation ---
ENABLE_LOKI=true

# --- Traefik Ingress ---
ENABLE_TRAEFIK=true

# --- TLS (cert-manager) ---
ENABLE_CERT_MANAGER=false
CERT_MANAGER_EMAIL=

# --- Private Registry ---
ENABLE_REGISTRY=false
REGISTRY_STORAGE_SIZE=10Gi

# --- GitOps (FluxCD) ---
ENABLE_FLUXCD=false
FLUX_GIT_REPO=
FLUX_GIT_BRANCH=main
FLUX_GIT_TOKEN=

# --- Dashboard ---
ENABLE_DASHBOARD=true
DASHBOARD_TYPE=kubernetes-dashboard

# --- Example Workloads ---
ENABLE_EXAMPLE_WORKLOADS=true

# --- etcd Backup ---
ENABLE_ETCD_BACKUP=true
ETCD_BACKUP_SCHEDULE=0 */6 * * *
ETCD_BACKUP_RETENTION=5
```

---

## 9. Port Reference

| Port | Protocol | Service | Scope |
|---|---|---|---|
| 6443 | TCP | K3s API Server | Server nodes |
| 2379–2380 | TCP | etcd (peer + client) | Server nodes only |
| 8472 | UDP | Flannel VXLAN | All nodes |
| 10250 | TCP | kubelet | All nodes |
| 10251 | TCP | kube-scheduler | Server nodes |
| 10252 | TCP | controller-manager | Server nodes |
| 51820 | UDP | Flannel WireGuard (if enabled) | All nodes |
| 80/443 | TCP | Traefik Ingress | All nodes (NodePort/LB) |
| 3000 | TCP | Grafana | Monitoring namespace |
| 9090 | TCP | Prometheus | Monitoring namespace |
| 9000 | TCP | Traefik Dashboard | Traefik namespace |
| 8080 | TCP | Longhorn UI | longhorn-system namespace |
| 8443 | TCP | Kubernetes Dashboard | kubernetes-dashboard namespace |
| 5000 | TCP | Private Registry | registry namespace |

---

## 10. Deliverables

| Deliverable | Format | Description |
|---|---|---|
| `scripts/00-prereqs.sh` | Bash | Install OS dependencies, disable swap, enable cgroups |
| `scripts/01-init-server.sh` | Bash | Initialize first K3s server with embedded etcd |
| `scripts/02-join-server.sh` | Bash | Join additional server nodes for HA |
| `scripts/03-join-agent.sh` | Bash | Join agent/worker nodes |
| `scripts/04-install-helm.sh` | Bash | Install Helm package manager |
| `scripts/05-install-metallb.sh` | Bash | Deploy MetalLB with IP pool |
| `scripts/06-install-longhorn.sh` | Bash | Deploy Longhorn storage |
| `scripts/07-install-monitoring.sh` | Bash | Deploy Prometheus + Grafana + Loki |
| `scripts/08-install-cert-manager.sh` | Bash | Deploy cert-manager for TLS |
| `scripts/09-install-registry.sh` | Bash | Deploy private container registry |
| `scripts/10-install-fluxcd.sh` | Bash | Bootstrap FluxCD GitOps |
| `scripts/11-install-dashboard.sh` | Bash | Deploy Kubernetes Dashboard or Rancher |
| `scripts/12-deploy-workloads.sh` | Bash | Deploy example workloads |
| `scripts/reset-node.sh` | Bash | Uninstall K3s and clean up |
| `scripts/backup-etcd.sh` | Bash | Snapshot etcd to file |
| `scripts/status.sh` | Bash | Cluster health check summary |
| `manifests/` | YAML | All Kubernetes manifests and Helm values |
| `deploy/deploy_to_cluster.sh` | Bash | Rsync + SSH deploy to cluster |
| `.env.example` | INI | Environment variable template |
| `docs/` | Markdown | Network diagram, disaster recovery |
