# Implementation Plan — Kubernetes (K3s) Edge Computing Cluster

## Phase 1 — Foundation & Single-Node K3s

### Step 1.1 — Project Scaffolding

- [ ] Create directory structure:
  ```bash
  mkdir -p scripts manifests/{metallb,longhorn,monitoring/grafana-dashboards,ingress/cert-manager,registry,dashboard,fluxcd,workloads/{nginx,redis,postgres,flask-app,cron-job}} deploy docs
  ```
- [ ] Create `.env.example` with all variables (reference TSD §8)
- [ ] Create `.gitignore`:
  ```
  .env
  *.bak
  etcd-snapshots/
  kubeconfig
  __pycache__/
  ```
- [ ] Create `scripts/status.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  echo "=== Nodes ==="
  sudo kubectl get nodes -o wide
  echo ""
  echo "=== Pods (all namespaces) ==="
  sudo kubectl get pods -A
  echo ""
  echo "=== Services (all namespaces) ==="
  sudo kubectl get svc -A
  echo ""
  if [ "${ENABLE_HA:-true}" = "true" ]; then
    echo "=== etcd Members ==="
    sudo kubectl -n kube-system exec -it $(sudo kubectl -n kube-system get pod -l component=etcd -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "etcd-pod") -- etcdctl member list 2>/dev/null || echo "etcd status unavailable"
  fi
  ```

**Checkpoint:** Project directory exists with all subdirectories. `.env.example` contains all variables.

### Step 1.2 — Node Prerequisites

- [ ] Implement `scripts/00-prereqs.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  # Update system
  sudo apt update && sudo apt upgrade -y
  # Install dependencies
  sudo apt install -y curl open-iscsi nfs-common jq
  # Enable and start iscsid (required for Longhorn)
  sudo systemctl enable --now iscsid
  # Disable swap
  sudo dphys-swapfile swapoff
  sudo dphys-swapfile uninstall
  sudo systemctl disable dphys-swapfile
  # Enable cgroups (required for K3s)
  CMDLINE="/boot/firmware/cmdline.txt"
  if ! grep -q "cgroup_enable=cpuset" "$CMDLINE"; then
    sudo sed -i 's/$/ cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory/' "$CMDLINE"
    echo "cgroups enabled — reboot required"
  fi
  echo "Prerequisites installed. Reboot if cgroups were added."
  ```
- [ ] Run on all nodes (via SSH loop or manually)

**Checkpoint:** All nodes have `open-iscsi` running, swap disabled, cgroups enabled. After reboot, `cat /proc/cgroups` shows `memory` enabled.

### Step 1.3 — Initialize First K3s Server

- [ ] Implement `scripts/01-init-server.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"

  INSTALL_ARGS="--write-kubeconfig-mode 644"

  # HA mode: use embedded etcd
  if [ "${ENABLE_HA:-true}" = "true" ]; then
    INSTALL_ARGS="${INSTALL_ARGS} --cluster-init"
  fi

  # CNI selection
  if [ "${CNI_PLUGIN:-flannel}" = "calico" ]; then
    INSTALL_ARGS="${INSTALL_ARGS} --flannel-backend=none --disable-network-policy"
  fi

  # Traefik toggle
  if [ "${ENABLE_TRAEFIK:-true}" != "true" ]; then
    INSTALL_ARGS="${INSTALL_ARGS} --disable=traefik"
  fi

  # Network CIDRs
  INSTALL_ARGS="${INSTALL_ARGS} --cluster-cidr=${POD_CIDR:-10.42.0.0/16} --service-cidr=${SERVICE_CIDR:-10.43.0.0/16}"

  # Token
  if [ -n "${K3S_TOKEN:-}" ]; then
    INSTALL_ARGS="${INSTALL_ARGS} --token=${K3S_TOKEN}"
  fi

  # Install K3s
  curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION:-}" sh -s - server ${INSTALL_ARGS}

  echo ""
  echo "K3s server initialized."
  echo "Node token: $(sudo cat /var/lib/rancher/k3s/server/node-token)"
  echo ""
  sudo kubectl get nodes
  ```

**Checkpoint:** `sudo kubectl get nodes` shows one node in `Ready` state. Token printed for joining additional nodes.

### Step 1.4 — Copy kubeconfig to Dev Machine

- [ ] Copy kubeconfig and adjust server IP:
  ```bash
  scp rasp-pi:/etc/rancher/k3s/k3s.yaml ~/.kube/k3s-config
  sed -i 's/127.0.0.1/192.168.216.90/' ~/.kube/k3s-config
  export KUBECONFIG=~/.kube/k3s-config
  kubectl get nodes
  ```

**Checkpoint:** `kubectl get nodes` works from dev machine.

---

## Phase 2 — Multi-Node HA & Networking

### Step 2.1 — Join Additional Server Nodes

- [ ] Implement `scripts/02-join-server.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"

  if [ -z "${K3S_URL:-}" ] || [ -z "${K3S_TOKEN:-}" ]; then
    echo "Error: K3S_URL and K3S_TOKEN must be set (or pass as env vars)"
    exit 1
  fi

  INSTALL_ARGS="--write-kubeconfig-mode 644"

  if [ "${CNI_PLUGIN:-flannel}" = "calico" ]; then
    INSTALL_ARGS="${INSTALL_ARGS} --flannel-backend=none --disable-network-policy"
  fi

  if [ "${ENABLE_TRAEFIK:-true}" != "true" ]; then
    INSTALL_ARGS="${INSTALL_ARGS} --disable=traefik"
  fi

  curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION:-}" \
    K3S_URL="${K3S_URL}" K3S_TOKEN="${K3S_TOKEN}" \
    sh -s - server ${INSTALL_ARGS}

  echo "Server node joined."
  ```
- [ ] Run on each additional server node

**Checkpoint:** `kubectl get nodes` shows 2–3 server nodes in `Ready`. `etcdctl member list` shows matching count.

### Step 2.2 — Join Agent Nodes

- [ ] Implement `scripts/03-join-agent.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"

  if [ -z "${K3S_URL:-}" ] || [ -z "${K3S_TOKEN:-}" ]; then
    echo "Error: K3S_URL and K3S_TOKEN must be set"
    exit 1
  fi

  curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION:-}" \
    K3S_URL="${K3S_URL}" K3S_TOKEN="${K3S_TOKEN}" \
    sh -s - agent

  echo "Agent node joined."
  ```
- [ ] Run on each agent node

**Checkpoint:** All nodes visible in `kubectl get nodes`. Worker nodes labeled `<none>` under ROLES.

### Step 2.3 — Calico CNI (Optional)

- [ ] If `CNI_PLUGIN=calico`:
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
  ```
- [ ] Verify Calico pods running: `kubectl -n kube-system get pods -l k8s-app=calico-node`
- [ ] Test cross-node pod communication

**Checkpoint:** All pods in `Running` state. Pod-to-pod ping across nodes succeeds.

### Step 2.4 — HA Validation

- [ ] Verify etcd quorum: `sudo k3s etcd-snapshot save --name test`
- [ ] Stop K3s on one server node: `sudo systemctl stop k3s`
- [ ] Verify cluster still accepts `kubectl` commands from another server
- [ ] Restart stopped node: `sudo systemctl start k3s`

**Checkpoint:** Cluster survives single server node failure. etcd re-joins after restart.

---

## Phase 3 — Storage & Load Balancing

### Step 3.1 — Install Helm

- [ ] Implement `scripts/04-install-helm.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  helm version
  echo "Helm installed."
  ```

**Checkpoint:** `helm version` shows v3.x.

### Step 3.2 — Deploy MetalLB

- [ ] Implement `scripts/05-install-metallb.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_METALLB:-true}" != "true" ]; then
    echo "MetalLB disabled. Skipping."
    exit 0
  fi
  helm repo add metallb https://metallb.github.io/metallb
  helm repo update
  helm install metallb metallb/metallb -n metallb-system --create-namespace --wait
  # Apply IP pool and L2 advertisement
  kubectl apply -f manifests/metallb/
  echo "MetalLB deployed with IP range: ${METALLB_IP_RANGE}"
  ```
- [ ] Create `manifests/metallb/ip-pool.yaml`:
  ```yaml
  apiVersion: metallb.io/v1beta1
  kind: IPAddressPool
  metadata:
    name: default-pool
    namespace: metallb-system
  spec:
    addresses:
      - 192.168.216.200-192.168.216.220  # Override with METALLB_IP_RANGE
  ```
- [ ] Create `manifests/metallb/l2-advertisement.yaml`:
  ```yaml
  apiVersion: metallb.io/v1beta1
  kind: L2Advertisement
  metadata:
    name: default
    namespace: metallb-system
  spec:
    ipAddressPools:
      - default-pool
  ```
- [ ] Test: create a `LoadBalancer` service and verify external IP is assigned

**Checkpoint:** `kubectl get svc` shows a service with an external IP from the MetalLB pool.

### Step 3.3 — Deploy Longhorn

- [ ] Implement `scripts/06-install-longhorn.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_LONGHORN:-true}" != "true" ]; then
    echo "Longhorn disabled. Skipping."
    exit 0
  fi
  helm repo add longhorn https://charts.longhorn.io
  helm repo update
  helm install longhorn longhorn/longhorn -n longhorn-system --create-namespace \
    -f manifests/longhorn/values.yaml --wait
  # Set as default StorageClass
  kubectl patch storageclass longhorn -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
  kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}' 2>/dev/null || true
  echo "Longhorn deployed. UI: http://${SERVER_IP_1}:8080"
  ```
- [ ] Create `manifests/longhorn/values.yaml`:
  ```yaml
  defaultSettings:
    defaultReplicaCount: 2    # Override with LONGHORN_REPLICA_COUNT
    defaultDataPath: /var/lib/longhorn
    storageMinimalAvailablePercentage: 15
  persistence:
    defaultClassReplicaCount: 2
  ```
- [ ] Test PVC: create a PVC, mount in a pod, write data, delete pod, re-mount, verify data

**Checkpoint:** Longhorn UI accessible. PVC creates successfully. Data persists across pod restarts.

---

## Phase 4 — Monitoring & Observability

### Step 4.1 — Deploy Prometheus + Grafana

- [ ] Implement `scripts/07-install-monitoring.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_MONITORING:-true}" != "true" ]; then
    echo "Monitoring disabled. Skipping."
    exit 0
  fi
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo update
  kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
  helm install kube-prometheus prometheus-community/kube-prometheus-stack \
    -n monitoring -f manifests/monitoring/prometheus-values.yaml --wait

  # Deploy Loki if enabled
  if [ "${ENABLE_LOKI:-true}" = "true" ]; then
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    helm install loki grafana/loki-stack -n monitoring \
      -f manifests/monitoring/loki-values.yaml --wait
    echo "Loki + Promtail deployed."
  fi

  echo "Monitoring stack deployed."
  echo "  Grafana: http://${SERVER_IP_1}:3000 (admin / ${GRAFANA_ADMIN_PASSWORD})"
  echo "  Prometheus: http://${SERVER_IP_1}:9090"
  ```
- [ ] Create `manifests/monitoring/prometheus-values.yaml`:
  ```yaml
  grafana:
    adminPassword: "change-me"    # Override with GRAFANA_ADMIN_PASSWORD
    service:
      type: LoadBalancer
    grafana.ini:
      users:
        default_theme: dark
    dashboardProviders:
      dashboardproviders.yaml:
        apiVersion: 1
        providers:
          - name: 'custom'
            folder: 'K3s Cluster'
            type: file
            options:
              path: /var/lib/grafana/dashboards/custom
    dashboardsConfigMaps:
      custom: grafana-custom-dashboards
  prometheus:
    service:
      type: LoadBalancer
    prometheusSpec:
      retention: 7d
      resources:
        requests:
          memory: 256Mi
          cpu: 100m
        limits:
          memory: 512Mi
          cpu: 500m
  nodeExporter:
    enabled: true
  kubeStateMetrics:
    enabled: true
  ```
- [ ] Create `manifests/monitoring/loki-values.yaml`:
  ```yaml
  loki:
    persistence:
      enabled: true
      size: 5Gi
  promtail:
    enabled: true
  grafana:
    enabled: false    # Use Grafana from kube-prometheus-stack
  ```
- [ ] Create Grafana dashboard JSON files in `manifests/monitoring/grafana-dashboards/`

**Checkpoint:** Grafana accessible with dark theme. Dashboards show node metrics. Prometheus targets all healthy. Loki queries return pod logs.

---

## Phase 5 — Ingress, TLS & Add-ons

### Step 5.1 — Traefik Configuration

- [ ] Create `manifests/ingress/traefik-values.yaml` (optional overrides):
  ```yaml
  dashboard:
    enabled: true
  ports:
    web:
      redirectTo:
        port: websecure    # HTTP → HTTPS redirect (if cert-manager enabled)
  ```
- [ ] Verify Traefik pods running: `kubectl -n kube-system get pods -l app.kubernetes.io/name=traefik`

**Checkpoint:** Traefik ingress controller is processing ingress resources.

### Step 5.2 — cert-manager for TLS

- [ ] Implement `scripts/08-install-cert-manager.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_CERT_MANAGER:-false}" != "true" ]; then
    echo "cert-manager disabled. Skipping."
    exit 0
  fi
  helm repo add jetstack https://charts.jetstack.io
  helm repo update
  helm install cert-manager jetstack/cert-manager -n cert-manager --create-namespace \
    --set installCRDs=true --wait
  kubectl apply -f manifests/ingress/cert-manager/
  echo "cert-manager deployed with ClusterIssuer."
  ```
- [ ] Create `manifests/ingress/cert-manager/cluster-issuer.yaml`:
  ```yaml
  apiVersion: cert-manager.io/v1
  kind: ClusterIssuer
  metadata:
    name: letsencrypt-prod
  spec:
    acme:
      server: https://acme-v02.api.letsencrypt.org/directory
      email: ""    # Override with CERT_MANAGER_EMAIL
      privateKeySecretRef:
        name: letsencrypt-prod-key
      solvers:
        - http01:
            ingress:
              class: traefik
  ```

**Checkpoint:** cert-manager pods running. ClusterIssuer ready. Certificates auto-provision for ingress with `cert-manager.io/cluster-issuer` annotation.

### Step 5.3 — Private Container Registry

- [ ] Implement `scripts/09-install-registry.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_REGISTRY:-false}" != "true" ]; then
    echo "Private registry disabled. Skipping."
    exit 0
  fi
  kubectl apply -f manifests/registry/
  echo "Private registry deployed."
  echo "Push images to: ${SERVER_IP_1}:5000/image:tag"
  ```
- [ ] Create registry manifests (`namespace.yaml`, `deployment.yaml`, `service.yaml`, `ingress.yaml`)
- [ ] Configure K3s to trust the registry — create `/etc/rancher/k3s/registries.yaml` on each node:
  ```yaml
  mirrors:
    "192.168.216.90:5000":
      endpoint:
        - "http://192.168.216.90:5000"
  ```

**Checkpoint:** `docker push 192.168.216.90:5000/test:latest` succeeds. Pods can pull from the private registry.

### Step 5.4 — FluxCD GitOps

- [ ] Implement `scripts/10-install-fluxcd.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_FLUXCD:-false}" != "true" ]; then
    echo "FluxCD disabled. Skipping."
    exit 0
  fi
  # Install flux CLI
  curl -s https://fluxcd.io/install.sh | sudo bash
  # Bootstrap
  flux bootstrap git \
    --url="${FLUX_GIT_REPO}" \
    --branch="${FLUX_GIT_BRANCH:-main}" \
    --token-auth \
    --password="${FLUX_GIT_TOKEN}" \
    --path=clusters/k3s-edge
  echo "FluxCD bootstrapped. Monitoring: ${FLUX_GIT_REPO}"
  ```

**Checkpoint:** FluxCD pods running in `flux-system` namespace. Git repo synced. Changes in repo auto-apply to cluster.

### Step 5.5 — Kubernetes Dashboard / Rancher

- [ ] Implement `scripts/11-install-dashboard.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_DASHBOARD:-true}" != "true" ]; then
    echo "Dashboard disabled. Skipping."
    exit 0
  fi
  if [ "${DASHBOARD_TYPE:-kubernetes-dashboard}" = "rancher" ]; then
    helm repo add rancher-latest https://releases.rancher.com/server-charts/latest
    helm repo update
    kubectl create namespace cattle-system --dry-run=client -o yaml | kubectl apply -f -
    helm install rancher rancher-latest/rancher -n cattle-system \
      --set hostname=rancher.local --set replicas=1 --wait
    echo "Rancher deployed. Access: https://${SERVER_IP_1}"
  else
    helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
    helm repo update
    helm install kubernetes-dashboard kubernetes-dashboard/kubernetes-dashboard \
      -n kubernetes-dashboard --create-namespace -f manifests/dashboard/values.yaml --wait
    kubectl apply -f manifests/dashboard/admin-user.yaml
    echo "Kubernetes Dashboard deployed. Access: https://${SERVER_IP_1}:8443"
    echo "Token: kubectl -n kubernetes-dashboard create token admin-user"
  fi
  ```
- [ ] Create `manifests/dashboard/admin-user.yaml`:
  ```yaml
  apiVersion: v1
  kind: ServiceAccount
  metadata:
    name: admin-user
    namespace: kubernetes-dashboard
  ---
  apiVersion: rbac.authorization.k8s.io/v1
  kind: ClusterRoleBinding
  metadata:
    name: admin-user
  roleRef:
    apiGroup: rbac.authorization.k8s.io
    kind: ClusterRole
    name: cluster-admin
  subjects:
    - kind: ServiceAccount
      name: admin-user
      namespace: kubernetes-dashboard
  ```

**Checkpoint:** Dashboard accessible via browser. Token-based login works. Cluster resources visible.

---

## Phase 6 — Example Workloads & Hardening

### Step 6.1 — Deploy Example Workloads

- [ ] Implement `scripts/12-deploy-workloads.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_EXAMPLE_WORKLOADS:-true}" != "true" ]; then
    echo "Example workloads disabled. Skipping."
    exit 0
  fi
  kubectl create namespace workloads --dry-run=client -o yaml | kubectl apply -f -
  kubectl apply -f manifests/workloads/nginx/ -n workloads
  kubectl apply -f manifests/workloads/redis/ -n workloads
  kubectl apply -f manifests/workloads/postgres/ -n workloads
  kubectl apply -f manifests/workloads/flask-app/ -n workloads
  kubectl apply -f manifests/workloads/cron-job/ -n workloads
  echo "Example workloads deployed."
  kubectl get pods -n workloads
  ```
- [ ] Create Nginx manifests (Deployment + Service type LoadBalancer + Ingress)
- [ ] Create Redis manifests (Deployment + ClusterIP Service)
- [ ] Create PostgreSQL manifests (StatefulSet + PVC (Longhorn) + Secret + Service)
- [ ] Create Flask app manifests (Deployment + ConfigMap + Service + Ingress)
- [ ] Create cron job manifest (CronJob running cleanup/backup every hour)

**Checkpoint:** All pods in `Running`. Nginx accessible via MetalLB IP. PostgreSQL data survives pod restart.

### Step 6.2 — etcd Backup Automation

- [ ] Implement `scripts/backup-etcd.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  if [ "${ENABLE_ETCD_BACKUP:-true}" != "true" ]; then
    echo "etcd backup disabled. Skipping."
    exit 0
  fi
  BACKUP_DIR="/var/lib/rancher/k3s/server/db/etcd-snapshots"
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  sudo k3s etcd-snapshot save --name "manual-${TIMESTAMP}"
  # Retention: keep last N snapshots
  RETENTION=${ETCD_BACKUP_RETENTION:-5}
  ls -1t "${BACKUP_DIR}"/manual-* 2>/dev/null | tail -n +$((RETENTION + 1)) | xargs -r sudo rm -f
  echo "etcd snapshot saved. Retained last ${RETENTION} snapshots."
  ```
- [ ] Add cron entry for scheduled backups:
  ```bash
  (crontab -l 2>/dev/null; echo "${ETCD_BACKUP_SCHEDULE:-0 */6 * * *} /home/pi/k3s-cluster/scripts/backup-etcd.sh") | crontab -
  ```

**Checkpoint:** `sudo k3s etcd-snapshot list` shows snapshots. Old snapshots pruned per retention setting.

### Step 6.3 — Node Reset Script

- [ ] Implement `scripts/reset-node.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  echo "WARNING: This will uninstall K3s and delete all cluster data on this node."
  read -p "Continue? (y/N): " confirm
  if [ "$confirm" != "y" ]; then
    echo "Aborted."
    exit 0
  fi
  if [ -x /usr/local/bin/k3s-uninstall.sh ]; then
    sudo /usr/local/bin/k3s-uninstall.sh
  elif [ -x /usr/local/bin/k3s-agent-uninstall.sh ]; then
    sudo /usr/local/bin/k3s-agent-uninstall.sh
  else
    echo "K3s uninstall script not found."
  fi
  sudo rm -rf /var/lib/rancher /etc/rancher
  echo "Node reset complete."
  ```

**Checkpoint:** Node is clean, no K3s processes running.

### Step 6.4 — Deploy Script

- [ ] Create `deploy/deploy_to_cluster.sh`:
  ```bash
  #!/bin/bash
  set -euo pipefail
  source "$(dirname "$0")/../.env"
  REMOTE="${SSH_USER:-pi}@${SERVER_IP_1:-192.168.216.90}"
  REMOTE_DIR="~/k3s-cluster"
  rsync -avz --exclude='.env' --exclude='.git' --exclude='etcd-snapshots' \
    . ${REMOTE}:${REMOTE_DIR}/
  echo "Files synced to ${REMOTE}:${REMOTE_DIR}"
  ```

**Checkpoint:** Run deploy script → files appear on control node → scripts executable.

### Step 6.5 — Security Hardening

- [ ] Apply Pod Security Admission to workload namespaces:
  ```bash
  kubectl label namespace workloads pod-security.kubernetes.io/enforce=restricted
  ```
- [ ] Enable etcd encryption at rest:
  - Add `--secrets-encryption` to K3s server install args
- [ ] Apply Calico default-deny NetworkPolicy (if `CNI_PLUGIN=calico`):
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: default-deny-ingress
    namespace: workloads
  spec:
    podSelector: {}
    policyTypes:
      - Ingress
  ```
- [ ] Restrict Dashboard ServiceAccount to read-only for production use
- [ ] Verify all secrets are encrypted: `sudo k3s secrets-encrypt status`

**Checkpoint:** Pod security restrictions enforced. Privileged pods rejected. Secrets encrypted at rest.

### Step 6.6 — Documentation

- [ ] Create `docs/network-diagram.md` — cluster IP layout, port map, CNI topology
- [ ] Create `docs/disaster-recovery.md`:
  - etcd snapshot restore procedure
  - Single-node failure recovery
  - Full cluster rebuild from scratch
  - Longhorn volume recovery
- [ ] Final review of `README.md` — verify all instructions match actual scripts
- [ ] Final review of `.env.example` — all variables documented with comments
- [ ] Test complete cluster rebuild from fresh SD cards using only the scripts

**Checkpoint:** Fresh SD cards + scripts → fully operational cluster with all enabled add-ons.
