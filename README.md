# TaskAPI

FastAPI task management API with PostgreSQL, Redis caching, Prometheus monitoring, and a full GitOps deployment pipeline (GitHub Actions → GHCR → ArgoCD → Helm → kubeadm K8s on AWS).

## Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.11) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Monitoring | Prometheus + Grafana (kube-prometheus-stack) |
| Container | Docker, multi-stage build |
| CI/CD | GitHub Actions → GHCR → ArgoCD |
| Orchestration | Helm + kubeadm Kubernetes |
| Infra | Terraform (AWS, ap-south-1) |

## Quick Start

```bash
docker compose up --build
```

Open http://localhost:8000 for the web UI, or http://localhost:8000/docs for Swagger.

## API Endpoints

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

## Data Model

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

## Project Structure

```
taskapi/
├── app/                          # FastAPI application
│   ├── main.py                   # Entry point, routes, static mount
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── schemas.py                # Pydantic schemas
│   ├── database.py               # PostgreSQL session factory
│   ├── cache.py                  # Redis helpers (lazy connect)
│   ├── routers/tasks.py          # CRUD endpoints
│   └── static/index.html         # Web UI
├── tests/                        # Pytest test suite
│   ├── conftest.py               # Fixtures (SQLite override, cache mock)
│   └── test_tasks.py             # 12 CRUD + validation tests
├── Dockerfile                    # Multi-stage build
├── docker-compose.yml            # Local dev (app + pg + redis)
├── requirements.txt
├── .github/workflows/ci-cd.yml   # Test → Build → Push → Deploy
├── helm/taskapi/                 # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── ingress.yaml
│       ├── secret.yaml
│       └── servicemonitor.yaml
├── argocd/application.yaml       # ArgoCD App
├── k8s/install-argocd.sh         # ArgoCD install script
├── monitoring/                   # Prometheus/Grafana configs
├── terraform/                    # AWS infra (VPC + EC2)
└── RUNBOOK.md                    # Full deployment guide
```

## Running Tests

```bash
pip install -r requirements.txt pytest httpx
pytest tests/ -v
```

Tests use SQLite in-memory and mock Redis — no external dependencies needed.

## CI/CD Pipeline

```
git push main → GitHub Actions
  ├── pytest (PostgreSQL + Redis service containers)
  ├── docker build + push → ghcr.io
  └── Update Helm image tag → git push [skip ci]
       └── ArgoCD detects drift → helm upgrade → K8s rolling deploy
```

## Deployment

See [RUNBOOK.md](RUNBOOK.md) for full deployment steps:
1. Terraform → AWS infra (VPC + EC2)
2. kubeadm cluster setup
3. NGINX Ingress, Prometheus, ArgoCD installation
4. Application deploy via ArgoCD

## Monitoring Dashboards

| Dashboard | Grafana ID |
|-----------|-----------|
| FastAPI Observability | 17175 |
| Node Exporter Full | 1860 |
| Kubernetes Cluster | 7249 |
| Redis | 763 |
| PostgreSQL | 9628 |
