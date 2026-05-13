#!/bin/bash
set -euo pipefail

# ── Container runtime (containerd) ────────────────────────────────────────────
apt-get update -y
apt-get install -y apt-transport-https ca-certificates curl gnupg containerd

mkdir -p /etc/containerd
containerd config default > /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
systemctl restart containerd && systemctl enable containerd

# ── Kernel settings ───────────────────────────────────────────────────────────
cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sysctl --system
modprobe br_netfilter overlay

# ── kubeadm / kubelet / kubectl ───────────────────────────────────────────────
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.29/deb/Release.key \
  | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
  https://pkgs.k8s.io/core:/stable:/v1.29/deb/ /" \
  > /etc/apt/sources.list.d/kubernetes.list
apt-get update -y
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

swapoff -a
sed -i '/swap/d' /etc/fstab

# ── Init cluster ──────────────────────────────────────────────────────────────
kubeadm init --pod-network-cidr=192.168.0.0/16

mkdir -p /root/.kube
cp /etc/kubernetes/admin.conf /root/.kube/config

# ── Calico CNI ────────────────────────────────────────────────────────────────
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

# ── Print join command ────────────────────────────────────────────────────────
kubeadm token create --print-join-command > /tmp/join-command.sh
