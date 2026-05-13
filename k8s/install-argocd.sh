#!/bin/bash
# Run from control plane node

set -euo pipefail

ARGOCD_NS=argocd

# ── Install ArgoCD ────────────────────────────────────────────────────────────
kubectl create namespace $ARGOCD_NS --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n $ARGOCD_NS \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl rollout status deploy/argocd-server -n $ARGOCD_NS --timeout=120s

# ── Expose ArgoCD UI (NodePort) ───────────────────────────────────────────────
kubectl patch svc argocd-server -n $ARGOCD_NS \
  -p '{"spec": {"type": "NodePort", "ports": [{"port": 443, "nodePort": 30443}]}}'

# ── Get initial admin password ────────────────────────────────────────────────
echo "ArgoCD admin password:"
kubectl -n $ARGOCD_NS get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo

# ── Deploy application ────────────────────────────────────────────────────────
kubectl apply -f argocd/application.yaml

echo "ArgoCD UI: https://<CONTROL_PLANE_IP>:30443"
