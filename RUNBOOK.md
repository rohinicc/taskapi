# TaskAPI — Full Deployment Runbook

## Stack
- **App**: FastAPI + PostgreSQL + Redis
- **CI/CD**: GitHub Actions → GHCR → ArgoCD → Helm → kubeadm K8s
- **Infra**: Terraform → AWS (ap-south-1)
- **Monitoring**: kube-prometheus-stack (Prometheus + Grafana + kube-state-metrics + node-exporter)

---

## 1. Project Structure

```
taskapi/
├── app/                          # FastAPI application
│   ├── main.py                   # App entry, Prometheus instrumentation
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── database.py               # PostgreSQL session factory
│   ├── cache.py                  # Redis get/set/delete helpers
│   └── routers/tasks.py          # CRUD endpoints
├── Dockerfile                    # Multi-stage build
├── docker-compose.yml            # Local dev (app + pg + redis)
├── requirements.txt
├── .github/workflows/ci-cd.yml   # Test → Build → Push → Update Helm tag
├── helm/taskapi/                 # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml               # CI updates image.tag here
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── secret.yaml
│       └── servicemonitor.yaml   # Prometheus ServiceMonitor CRD
├── argocd/application.yaml       # ArgoCD App pointing to helm/taskapi
├── terraform/                    # AWS infrastructure
│   ├── main.tf                   # VPC + EC2 (control-plane + workers)
│   ├── variables.tf
│   ├── outputs.tf
│   └── scripts/control-plane-init.sh
├── monitoring/
│   ├── prometheus-values.yaml    # kube-prometheus-stack Helm values
│   └── grafana-dashboards.yaml   # PromQL queries + dashboard IDs
└── k8s/install-argocd.sh
```

---

## 2. API Endpoints

| Method | Path                    | Description         | Cache        |
|--------|-------------------------|---------------------|--------------|
| POST   | /api/v1/tasks/          | Create task         | Busts all    |
| GET    | /api/v1/tasks/          | List all tasks      | task:all     |
| GET    | /api/v1/tasks/{id}      | Get single task     | task:{id}    |
| PUT    | /api/v1/tasks/{id}      | Update task         | Busts both   |
| DELETE | /api/v1/tasks/{id}      | Delete task         | Busts both   |
| GET    | /health                 | Health check        | —            |
| GET    | /metrics                | Prometheus metrics  | —            |

---

## 3. Data Model

```sql
CREATE TABLE tasks (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    description VARCHAR(1000),
    completed   BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ
);
```

---

## 4. CI/CD Flow

```
git push main
    │
    ├── GitHub Actions: pytest (with real pg + redis services)
    │
    ├── docker build + push → ghcr.io/<user>/taskapi:sha-<hash>
    │
    └── sed helm/taskapi/values.yaml: image.tag = sha-<hash>
        git push [skip ci]
            │
            └── ArgoCD detects Helm values change
                └── helm upgrade taskapi → K8s rolling deploy
```

---

## 5. Deployment Steps

### Step 1 — AWS Infrastructure

```bash
cd terraform
terraform init
terraform plan -out tfplan
terraform apply tfplan

# Get IPs
terraform output control_plane_public_ip
terraform output worker_private_ips
```

### Step 2 — Join Worker Nodes to Cluster

```bash
# SSH into control plane
ssh ubuntu@<CONTROL_PLANE_IP>
cat /tmp/join-command.sh   # copy the kubeadm join command

# SSH into each worker (via bastion or SSM)
sudo bash -c "<PASTE JOIN COMMAND>"
```

### Step 3 — Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --set controller.service.type=NodePort \
  --set controller.service.nodePorts.http=30080
```

### Step 4 — Install kube-prometheus-stack (Monitoring)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml
```

### Step 5 — Install ArgoCD + Deploy App

```bash
chmod +x k8s/install-argocd.sh
./k8s/install-argocd.sh
```

### Step 6 — Add Bitnami Dependency to Helm

```bash
# helm/taskapi/Chart.yaml — add this:
# dependencies:
#   - name: postgresql
#     version: "15.x.x"
#     repository: https://charts.bitnami.com/bitnami
#   - name: redis
#     version: "19.x.x"
#     repository: https://charts.bitnami.com/bitnami

helm repo add bitnami https://charts.bitnami.com/bitnami
helm dependency update helm/taskapi/
```

### Step 7 — Replace Placeholders

```bash
# In argocd/application.yaml
sed -i 's/YOUR_GITHUB_USERNAME/rohinicc/g' argocd/application.yaml

# In helm/taskapi/values.yaml
sed -i 's/YOUR_GITHUB_USERNAME/rohinicc/g' helm/taskapi/values.yaml
```

### Step 8 — Local Dev

```bash
docker compose up --build
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "First task", "description": "Test"}'
```

---

## 6. Monitoring Access

| Service    | Access                                   |
|------------|------------------------------------------|
| Grafana    | http://<NODE_IP>:30030  (admin/admin123) |
| ArgoCD     | https://<CONTROL_PLANE_IP>:30443         |
| Prometheus | kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring |

**Import Grafana Dashboards (IDs):**
- FastAPI Observability: `17175`
- Node Exporter Full: `1860`
- Kubernetes Cluster: `7249`
- Redis: `763`

---

## 7. GitHub Secrets Required

| Secret | Value |
|--------|-------|
| `GITHUB_TOKEN` | Auto-provided by Actions |

That's it — GHCR uses `GITHUB_TOKEN` for auth automatically.
