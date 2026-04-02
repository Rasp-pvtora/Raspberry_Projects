# Task List — Kubernetes (K3s) Edge Computing Cluster

## Phase 1 — Foundation & Single-Node K3s

- [ ] Create project directory structure (`scripts/`, `manifests/`, `deploy/`, `docs/`)
- [ ] Create `.env.example` with all variables and defaults
- [ ] Create `.gitignore` (exclude `.env`, `kubeconfig`, `*.bak`, `etcd-snapshots/`)
- [ ] Implement `scripts/00-prereqs.sh` — update OS, install `curl`, `open-iscsi`, `nfs-common`
- [ ] Disable swap on all nodes (`sudo dphys-swapfile swapoff && sudo systemctl disable dphys-swapfile`)
- [ ] Enable cgroups in `/boot/firmware/cmdline.txt` (`cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory`)
- [ ] Set static IP addresses on all nodes (`/etc/dhcpcd.conf` or NetworkManager)
- [ ] Set unique hostnames on all nodes (`k3s-server-1`, `k3s-server-2`, etc.)
- [ ] Implement `scripts/01-init-server.sh` — install K3s server with `--cluster-init` (embedded etcd)
- [ ] Source `.env` in all scripts for feature flags and config
- [ ] Verify K3s server starts and `kubectl get nodes` shows Ready
- [ ] Copy kubeconfig to dev machine (`scp rasp-pi:/etc/rancher/k3s/k3s.yaml ~/.kube/k3s-config`)
- [ ] Verify `kubectl` works from dev machine (update server IP in kubeconfig)
- [ ] Implement `scripts/status.sh` — print node status, pod status, etcd health

## Phase 2 — Multi-Node HA & Networking

- [ ] Implement `scripts/02-join-server.sh` — join additional server nodes with `K3S_URL` and `K3S_TOKEN`
- [ ] Implement `scripts/03-join-agent.sh` — join agent nodes
- [ ] Join second server node and verify etcd quorum (`etcdctl member list`)
- [ ] Join third server node (or agent) and verify all nodes Ready
- [ ] Test leader election — stop K3s on leader node, verify cluster continues
- [ ] Add `ENABLE_HA` flag — if `false`, skip `--cluster-init` flag (single-server SQLite mode)
- [ ] Add `CNI_PLUGIN` flag — if `calico`, install K3s with `--flannel-backend=none` and deploy Calico
- [ ] Create `manifests/` directory structure for all add-ons
- [ ] Test pod-to-pod communication across nodes
- [ ] Test CoreDNS resolution (`kubectl run -it --rm debug --image=busybox -- nslookup kubernetes`)
- [ ] Verify `SERVICE_CIDR` and `POD_CIDR` from `.env` are applied

## Phase 3 — Storage & Load Balancing

- [ ] Implement `scripts/04-install-helm.sh` — install Helm binary
- [ ] Implement `scripts/05-install-metallb.sh` — deploy MetalLB via Helm or manifests
- [ ] Create `manifests/metallb/namespace.yaml`
- [ ] Create `manifests/metallb/ip-pool.yaml` — use `METALLB_IP_RANGE` from `.env`
- [ ] Create `manifests/metallb/l2-advertisement.yaml`
- [ ] Verify MetalLB assigns external IP to a test `LoadBalancer` service
- [ ] Guard MetalLB install behind `ENABLE_METALLB` flag
- [ ] Implement `scripts/06-install-longhorn.sh` — deploy Longhorn via Helm
- [ ] Create `manifests/longhorn/values.yaml` — set `LONGHORN_REPLICA_COUNT`, resource limits
- [ ] Verify Longhorn UI accessible at `http://192.168.216.90:8080`
- [ ] Set Longhorn as default StorageClass
- [ ] Test PVC creation and pod mounting (write + read file)
- [ ] Guard Longhorn install behind `ENABLE_LONGHORN` flag

## Phase 4 — Monitoring & Observability

- [ ] Implement `scripts/07-install-monitoring.sh` — deploy kube-prometheus-stack via Helm
- [ ] Create `manifests/monitoring/namespace.yaml`
- [ ] Create `manifests/monitoring/prometheus-values.yaml` — scrape intervals, retention, ARM64 images
- [ ] Configure Grafana dark theme and admin password from `GRAFANA_ADMIN_PASSWORD`
- [ ] Create `manifests/monitoring/grafana-dashboards/cluster-overview.json`
- [ ] Create `manifests/monitoring/grafana-dashboards/node-exporter.json`
- [ ] Verify Prometheus scraping node-exporter, kube-state-metrics, kubelet
- [ ] Verify Grafana accessible at `http://192.168.216.90:3000` with dashboards loaded
- [ ] Guard monitoring install behind `ENABLE_MONITORING` flag
- [ ] Create `manifests/monitoring/loki-values.yaml` — Loki + Promtail DaemonSet
- [ ] Add Loki datasource to Grafana
- [ ] Verify log queries in Grafana Explore (LogQL)
- [ ] Guard Loki install behind `ENABLE_LOKI` flag

## Phase 5 — Ingress, TLS & Add-ons

- [ ] Create `manifests/ingress/traefik-values.yaml` — custom Traefik Helm values
- [ ] Verify Traefik Dashboard accessible (if enabled)
- [ ] Guard Traefik with `ENABLE_TRAEFIK` flag (disable to use alternative ingress)
- [ ] Implement `scripts/08-install-cert-manager.sh` — deploy cert-manager via Helm
- [ ] Create `manifests/ingress/cert-manager/cluster-issuer.yaml` — Let's Encrypt staging + prod
- [ ] Create `manifests/ingress/cert-manager/wildcard-cert.yaml`
- [ ] Guard cert-manager behind `ENABLE_CERT_MANAGER` flag
- [ ] Implement `scripts/09-install-registry.sh` — deploy private Docker Distribution registry
- [ ] Create `manifests/registry/namespace.yaml`, `deployment.yaml`, `service.yaml`, `ingress.yaml`
- [ ] Configure Longhorn PVC for registry storage (`REGISTRY_STORAGE_SIZE`)
- [ ] Configure K3s nodes to trust private registry (`/etc/rancher/k3s/registries.yaml`)
- [ ] Guard registry behind `ENABLE_REGISTRY` flag
- [ ] Implement `scripts/10-install-fluxcd.sh` — bootstrap FluxCD with `flux bootstrap`
- [ ] Create `manifests/fluxcd/gotk-components.yaml` and `gotk-sync.yaml`
- [ ] Guard FluxCD behind `ENABLE_FLUXCD` flag
- [ ] Implement `scripts/11-install-dashboard.sh` — deploy Kubernetes Dashboard or Rancher
- [ ] Create `manifests/dashboard/admin-user.yaml` — ServiceAccount + ClusterRoleBinding
- [ ] Create `manifests/dashboard/values.yaml`
- [ ] Support `DASHBOARD_TYPE` switch (kubernetes-dashboard vs. rancher)
- [ ] Guard dashboard behind `ENABLE_DASHBOARD` flag

## Phase 6 — Example Workloads & Hardening

- [ ] Implement `scripts/12-deploy-workloads.sh` — apply all example manifests
- [ ] Create `manifests/workloads/nginx/` — Deployment + Service + Ingress
- [ ] Create `manifests/workloads/redis/` — Deployment + ClusterIP Service
- [ ] Create `manifests/workloads/postgres/` — StatefulSet + PVC + Secret + Service
- [ ] Create `manifests/workloads/flask-app/` — Deployment + ConfigMap + Service + Ingress
- [ ] Create `manifests/workloads/cron-job/cronjob.yaml` — scheduled task
- [ ] Verify Nginx accessible via MetalLB external IP
- [ ] Verify Redis reachable from other pods (ClusterIP)
- [ ] Verify PostgreSQL data persists across pod restart (Longhorn PVC)
- [ ] Verify Flask app serves via Traefik ingress
- [ ] Verify cron job runs on schedule
- [ ] Guard workloads behind `ENABLE_EXAMPLE_WORKLOADS` flag
- [ ] Implement `scripts/backup-etcd.sh` — snapshot etcd to file with retention
- [ ] Add cron entry for `ETCD_BACKUP_SCHEDULE`
- [ ] Guard etcd backup behind `ENABLE_ETCD_BACKUP` flag
- [ ] Implement `scripts/reset-node.sh` — uninstall K3s, clean up data dirs
- [ ] Create `deploy/deploy_to_cluster.sh` — rsync scripts/manifests to control node
- [ ] Apply RBAC hardening — restrict default ServiceAccount permissions
- [ ] Apply Pod Security Admission (restricted) on workload namespaces
- [ ] Apply Calico network policies (default-deny ingress) if `CNI_PLUGIN=calico`
- [ ] Verify etcd encryption at rest (`--secrets-encryption`)
- [ ] Create `docs/network-diagram.md` — cluster network topology
- [ ] Create `docs/disaster-recovery.md` — backup, restore, failover procedures
- [ ] Test full cluster rebuild from scripts (fresh SD cards → working cluster)
- [ ] Update `README.md` with final instructions
- [ ] Final `.env.example` review — all variables documented
