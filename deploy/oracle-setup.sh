#!/bin/bash
# Oracle Cloud Free Tier — Nowhere Deployment Script
# Run on a fresh Ubuntu 22.04 ARM VM
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/tatenda-source/nowhere/main/deploy/oracle-setup.sh | bash
#   — or —
#   chmod +x oracle-setup.sh && ./oracle-setup.sh

set -e

echo "==> Updating system..."
sudo apt-get update && sudo apt-get upgrade -y

echo "==> Installing Docker + Docker Compose..."
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "==> Adding current user to docker group..."
sudo usermod -aG docker $USER

echo "==> Opening firewall ports (iptables)..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save

echo "==> Cloning repository..."
git clone https://github.com/tatenda-source/nowhere.git ~/nowhere
cd ~/nowhere

echo "==> Creating .env from example..."
cp .env.example .env

echo "==> Generating secrets..."
JWT_SECRET=$(openssl rand -base64 48)
DEVICE_TOKEN_SECRET=$(openssl rand -base64 48)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" .env
sed -i "s|^DEVICE_TOKEN_SECRET=.*|DEVICE_TOKEN_SECRET=$DEVICE_TOKEN_SECRET|" .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|" .env
sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|" .env

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "==> IMPORTANT: Edit .env to set your domain:"
echo "    nano ~/nowhere/.env"
echo "    Update NOWHERE_DOMAIN and ALLOWED_ORIGINS"
echo ""
echo "==> Then build and start:"
echo "    cd ~/nowhere && npm --prefix app run build:web && docker compose up -d --build"
echo ""
echo "==> Check status:"
echo "    docker compose ps"
echo "    docker compose logs -f"
echo ""
echo "NOTE: You may need to log out and back in for docker group to take effect."
echo "      Alternatively, run: newgrp docker"
