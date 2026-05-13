# TaskAPI

FastAPI task management API with PostgreSQL, Redis caching, Prometheus monitoring, and a full GitOps deployment pipeline.

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.11) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Monitoring | Prometheus + Grafana |
| Container | Docker, multi-stage build |
| CI/CD | GitHub Actions → GHCR → ArgoCD |
| Orchestration | Helm + Kubernetes |
| Infra | Terraform (AWS Free Tier) |

---

## 1. Quick Start (Docker Compose)

```bash
docker compose up --build
```

Open:
- **Web UI:** http://localhost:8000
- **Swagger:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

## 2. Running Tests

```bash
pip install -r requirements.txt pytest httpx
pytest tests/ -v
```

Tests use SQLite in-memory and mock Redis — no external dependencies.

---

## 3. Local Kubernetes (Docker Desktop)

### 3.1 Enable K8s in Docker Desktop
Settings → Kubernetes → Enable Kubernetes → Apply & Restart

### 3.2 Build & Deploy
```bash
# Build image locally
docker build -t taskapi-app .

# Deploy app
kubectl create deployment taskapi --image=taskapi-app --replicas=2
kubectl expose deployment taskapi --port=8000 --target-port=8000

# Access
kubectl port-forward svc/taskapi 8000:8000
```

### 3.3 Deploy with Helm
```bash
helm install taskapi helm/taskapi/ \
  --set serviceMonitor.enabled=false \
  --set ingress.enabled=false
```

### 3.4 Install Prometheus + Grafana
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml
```

### 3.5 Install ArgoCD
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --namespace argocd --for=condition=ready pods --all --timeout=300s

# Deploy app via ArgoCD
kubectl apply -f argocd/application.yaml
```

---

## 4. Access Credentials

| Service | Command | URL | Credentials |
|---------|---------|-----|-------------|
| **App** | `kubectl port-forward svc/taskapi 8000:8000 -n taskapi` | http://localhost:8000 | — |
| **Grafana** | `kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring` | http://localhost:3000 | `admin` / `admin123` |
| **Prometheus** | `kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring` | http://localhost:9090 | — |
| **ArgoCD** | `kubectl port-forward svc/argocd-server 8080:443 -n argocd` | https://localhost:8080 | `admin` (password below) |

Get ArgoCD password:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode
```

---

## 5. AWS Free Tier Deployment (Terraform)

Deploys a single `t3.micro` EC2 instance running the app via Docker Compose.

### Prerequisites
- AWS Access Key + Secret Key
- SSH public key (`~/.ssh/id_rsa.pub`)

### Steps
```bash
cd terraform

# Set your keys
# Edit terraform.tfvars with your AWS credentials

terraform init
terraform plan
terraform apply

# Get the app URL
terraform output app_url
```

The EC2 instance automatically:
1. Installs Docker + Docker Compose
2. Clones the repo from GitHub
3. Runs `docker compose up --build -d`

### Destroy
```bash
terraform destroy --auto-approve
```

---

## 6. CI/CD Pipeline

```
git push main → GitHub Actions
  ├── pytest (PostgreSQL + Redis service containers)
  ├── docker build + push → ghcr.io
  └── Update Helm image tag → git push [skip ci]
       └── ArgoCD detects drift → helm upgrade → K8s rolling deploy
```

### Required GitHub Secrets
| Secret | Value |
|--------|-------|
| `GITHUB_TOKEN` | Auto-provided (needs `packages: write` permission) |

---

## 7. API Endpoints

| Method | Path | Description | Cache |
|--------|------|-------------|-------|
| POST | `/api/v1/tasks/` | Create task | Busts all |
| GET | `/api/v1/tasks/` | List all tasks | `task:all` (5m) |
| GET | `/api/v1/tasks/{id}` | Get single task | `task:{id}` (5m) |
| PUT | `/api/v1/tasks/{id}` | Update task | Busts both |
| DELETE | `/api/v1/tasks/{id}` | Delete task | Busts both |
| GET | `/health` | Health check | — |
| GET | `/metrics` | Prometheus metrics | — |
| GET | `/ui` | Web UI | — |

## 8. Data Model

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

## 9. Grafana Dashboards

| Dashboard | Grafana ID |
|-----------|-----------|
| FastAPI Observability | 17175 |
| Node Exporter Full | 1860 |
| Kubernetes Cluster | 7249 |
| Redis | 763 |
| PostgreSQL | 9628 |

## 10. Project Structure

```
taskapi/
├── app/                          # FastAPI application
│   ├── main.py                   # Entry point, routes, static mount
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── schemas.py                # Pydantic schemas
│   ├── database.py               # PostgreSQL session factory
│   ├── cache.py                  # Redis helpers
│   └── routers/tasks.py          # CRUD endpoints
├── tests/                        # Pytest test suite
├── Dockerfile                    # Multi-stage build
├── docker-compose.yml            # Local dev (app + pg + redis)
├── helm/taskapi/                 # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── secret.yaml
│       └── servicemonitor.yaml
├── argocd/application.yaml       # ArgoCD Application
├── monitoring/                   # Prometheus/Grafana configs
│   ├── prometheus-values.yaml
│   └── grafana-dashboards.yaml
├── terraform/                    # AWS Free Tier infra
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── scripts/userdata.sh
└── .github/workflows/ci-cd.yml   # GitHub Actions
```
