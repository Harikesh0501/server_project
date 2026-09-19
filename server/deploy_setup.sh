#!/usr/bin/env bash
# ==============================================================================
# Sovereign Cloud Deployment Platform - Ubuntu Server Toolchain Installer
# Automated Setup for EPIC-00, EPIC-01, EPIC-02, and EPIC-07
# Supports: Ubuntu Server 24.04 LTS / 22.04 LTS (amd64 / arm64)
# ==============================================================================

set -euo pipefail

# ANSI Color Codes
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}  Sovereign Cloud Platform - Server Setup Engine      ${NC}"
echo -e "${CYAN}  100% Self-Hosted (Vercel + Render Sovereign Cloud)  ${NC}"
echo -e "${CYAN}======================================================${NC}"

# Check for root / sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[ERROR] Please run this script with sudo or as root: sudo bash deploy_setup.sh${NC}"
  exit 1
fi

REAL_USER="${SUDO_USER:-$USER}"
echo -e "${GREEN}[+] Running installer for host user: ${REAL_USER}${NC}"

# ------------------------------------------------------------------------------
# 1. Base OS Packages & System Update (Task 0.7.1)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[*] Step 1/8: Updating Ubuntu APT repositories and base packages...${NC}"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl wget git htop net-tools ca-certificates gnupg lsb-release \
    software-properties-common ufw build-essential libssl-dev pkg-config

# ------------------------------------------------------------------------------
# 2. Linux Kernel Optimization & Sysctl Hardening (Task 1.1)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[*] Step 2/8: Configuring Linux Kernel sysctl parameters...${NC}"
SYSCTL_CONF="/etc/sysctl.d/99-deploy-platform.conf"
cat << 'EOF' > "${SYSCTL_CONF}"
# High-concurrency network & memory tuning for Sovereign Cloud
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
fs.file-max = 2097152
vm.max_map_count = 262144
vm.overcommit_memory = 1
net.ipv4.ip_forward = 1
EOF
sysctl --system > /dev/null 2>&1 || true

# System security limits
cat << 'EOF' > /etc/security/limits.d/99-deploy.conf
* soft nofile 1048576
* hard nofile 1048576
* soft nproc 65535
* hard nproc 65535
EOF

# ------------------------------------------------------------------------------
# 3. Official Docker Engine CE Installation (Task 0.7.2, 0.7.3)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[*] Step 3/8: Installing Official Docker Engine CE (Community Edition)...${NC}"
install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
fi

ARCH=$(dpkg --print-architecture)
CODENAME=$(lsb_release -cs)
echo "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${CODENAME} stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
usermod -aG docker "${REAL_USER}"
systemctl enable --now docker

# ------------------------------------------------------------------------------
# 4. Private Docker Bridge Network Creation (Task 2.1)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[*] Step 4/8: Provisioning private container network (deploy-private-net)...${NC}"
if ! docker network ls | grep -q "deploy-private-net"; then
    docker network create \
        --driver bridge \
        --subnet 172.28.0.0/16 \
        --gateway 172.28.0.1 \
        --opt "com.docker.network.bridge.name=br-deploy" \
        deploy-private-net
    echo -e "${GREEN}[+] Created private bridge network 'deploy-private-net' (172.28.0.0/16)${NC}"
else
    echo -e "${GREEN}[+] Private network 'deploy-private-net' already exists.${NC}"
fi

# ------------------------------------------------------------------------------
# 5. Caddy 2 Reverse Proxy Installation (Task 0.7.6, Task 2.3)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[*] Step 5/8: Installing Caddy 2 High-Performance Ingress Proxy...${NC}"
if ! command -v caddy &> /dev/null; then
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
    apt-get update -y
    apt-get install -y caddy
    systemctl enable --now caddy
fi

# ------------------------------------------------------------------------------
# 6. Python 3.12 & Node.js 22 LTS Toolchain (Task 0.7.4, 0.7.5)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[*] Step 6/8: Setting up Python 3 and Node.js 22 runtime environments...${NC}"
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv

if ! command -v node &> /dev/null || [ "$(node -v | cut -d'.' -f1)" != "v22" ]; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
fi

echo -e "${GREEN}[+] Node.js version: $(node -v)${NC}"
echo -e "${GREEN}[+] NPM version: $(npm -v)${NC}"
echo -e "${GREEN}[+] Python version: $(python3 --version)${NC}"

# ------------------------------------------------------------------------------
# 7. Platform Data Directories & Master Key Vault (Task 4.1)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[*] Step 7/8: Preparing platform storage directories & zero-trust key vault...${NC}"
mkdir -p /var/lib/deploy/data
mkdir -p /var/lib/deploy/builds
mkdir -p /etc/deploy
chmod 750 /var/lib/deploy
chmod 700 /etc/deploy
chown -R "${REAL_USER}:${REAL_USER}" /var/lib/deploy

# Generate master encryption key if missing
if [ ! -f /etc/deploy/master.key ]; then
    openssl rand 32 > /etc/deploy/master.key
    chmod 400 /etc/deploy/master.key
    chown "${REAL_USER}:${REAL_USER}" /etc/deploy/master.key
    echo -e "${GREEN}[+] Generated AES-256-GCM Master Key: /etc/deploy/master.key${NC}"
fi

# ------------------------------------------------------------------------------
# 8. UFW Firewall Configuration (Task 0.6.5, Task 2.2)
# ------------------------------------------------------------------------------
echo -e "${YELLOW}[*] Step 8/8: Hardening UFW Firewall...${NC}"
ufw allow 22/tcp comment "SSH Server"
ufw allow 80/tcp comment "Caddy Ingress HTTP"
ufw allow 443/tcp comment "Caddy Ingress HTTPS"
ufw allow 8000/tcp comment "FastAPI Control Plane"
ufw allow 3000/tcp comment "Platform Web Dashboard"
ufw allow 5000/tcp comment "Local Docker Registry"
ufw --force enable

echo -e "\n${GREEN}==============================================================${NC}"
echo -e "${GREEN}  SUCCESS: Sovereign Cloud Server Toolchain is 100% Installed! ${NC}"
echo -e "${GREEN}==============================================================${NC}"
echo -e "${CYAN}Host LAN IP:${NC} $(hostname -I | awk '{print $1}')"
echo -e "${CYAN}Docker:${NC}     $(docker --version)"
echo -e "${CYAN}Caddy:${NC}      $(caddy version)"
echo -e "${CYAN}Node.js:${NC}    $(node -v)"
echo -e "${CYAN}Python:${NC}     $(python3 --version)"
echo -e "${YELLOW}Note: Please log out and back in, or run 'newgrp docker' to use docker without sudo.${NC}\n"
