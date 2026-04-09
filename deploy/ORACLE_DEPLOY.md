# Nowhere — Oracle Cloud Free Tier Deployment Guide

Deploy Nowhere on Oracle Cloud's Always Free ARM VM.

## What you get (free forever)

- **Ampere A1** ARM instance: 1 OCPU, 1 GB RAM, Ubuntu 22.04
- All Docker images in this stack support `linux/arm64`
- 1 GB RAM is enough: Redis 256M + API 512M + Caddy 128M = 896M total

---

## Step 1: Create an Oracle Cloud account

1. Go to [cloud.oracle.com](https://cloud.oracle.com) and sign up
2. Choose the **Always Free** tier (no credit card charge beyond the $1 verification hold)
3. Pick your home region (closest to your users)

## Step 2: Create an ARM VM

1. Go to **Compute > Instances > Create Instance**
2. Configure:
   - **Name:** `nowhere`
   - **Image:** Ubuntu 22.04 (Canonical)
   - **Shape:** VM.Standard.A1.Flex — **1 OCPU, 1 GB RAM**
   - **Networking:** Use default VCN or create one (ensure public subnet)
   - **SSH keys:** Upload or paste your public key (`~/.ssh/id_rsa.pub`)
3. Click **Create**
4. Note the **Public IP Address** once the instance is running

## Step 3: Configure Security List (CRITICAL)

Oracle Cloud has **TWO firewalls** — the VCN Security List in the console AND iptables inside the VM. Both must allow traffic.

### VCN Security List (Oracle Console)

1. Go to **Networking > Virtual Cloud Networks > your VCN > Security Lists**
2. Click the default security list
3. Add **Ingress Rules**:

| Stateless | Source CIDR   | Protocol | Dest Port | Description |
|-----------|---------------|----------|-----------|-------------|
| No        | 0.0.0.0/0     | TCP      | 80        | HTTP        |
| No        | 0.0.0.0/0     | TCP      | 443       | HTTPS       |
| No        | 0.0.0.0/0     | TCP      | 22        | SSH (exists by default) |

4. Save the rules

### VM iptables (handled by setup script)

The setup script opens ports 80 and 443 in iptables automatically. If you need to do it manually:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

## Step 4: SSH into the VM

```bash
ssh ubuntu@<PUBLIC_IP>
```

## Step 5: Run the setup script

```bash
curl -fsSL https://raw.githubusercontent.com/tatenda-source/nowhere/main/deploy/oracle-setup.sh | bash
```

Or clone first and run locally:

```bash
git clone https://github.com/tatenda-source/nowhere.git ~/nowhere
chmod +x ~/nowhere/deploy/oracle-setup.sh
~/nowhere/deploy/oracle-setup.sh
```

After the script completes, log out and back in (or run `newgrp docker`) so the docker group takes effect.

## Step 6: Configure your domain

### With a custom domain (recommended)

1. In your DNS provider, create an **A record**:
   - **Name:** `nowhere.yourdomain.com` (or `@` for apex)
   - **Value:** your VM's public IP
2. Edit `.env`:

```bash
cd ~/nowhere
nano .env
```

Set:
```
NOWHERE_DOMAIN=nowhere.yourdomain.com
ALLOWED_ORIGINS=https://nowhere.yourdomain.com
```

Caddy will automatically obtain a Let's Encrypt TLS certificate.

### Without a domain (testing only)

Leave `NOWHERE_DOMAIN` as-is or set it to the VM's public IP. Caddy will use a self-signed certificate. Browsers will show a warning but it works for testing.

## Step 7: Build and start

```bash
cd ~/nowhere

# Install Node.js if not present (for web build)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Build the Expo web app
npm --prefix app install
npm --prefix app run build:web

# Start all services
docker compose up -d --build
```

Or if you have `make` installed:

```bash
make deploy
```

## Step 8: Verify

```bash
# Check all containers are running
docker compose ps

# Health check
curl -f http://localhost:8000/health

# View logs
docker compose logs -f

# Test from outside (replace with your domain or IP)
curl -f https://nowhere.yourdomain.com/health
```

Verify:
- Health endpoint returns OK
- PWA installs from the browser
- WebSocket connections work (check browser devtools)

---

## Common operations

```bash
# View logs
docker compose logs -f

# Restart all services
docker compose restart

# Restart a single service
docker compose restart api

# Stop everything
docker compose down

# Update to latest code
git pull && make deploy

# Full clean (removes volumes — data loss!)
docker compose down --volumes --remove-orphans
```

## Troubleshooting

### Cannot reach the server from outside

1. Check **both** firewalls:
   - Oracle Console: Security List ingress rules for ports 80/443
   - VM: `sudo iptables -L INPUT -n --line-numbers` (ports 80/443 should be ACCEPT)
2. Verify containers are running: `docker compose ps`
3. Check Caddy logs: `docker compose logs caddy`

### Out of memory

The 1 GB VM is tight. If you see OOM kills:
- Check usage: `free -m` and `docker stats`
- Ensure resource limits are set in `docker-compose.yml`
- Consider upgrading to 2 OCPU / 2 GB (still free tier — up to 4 OCPU / 24 GB shared across A1 instances)

### TLS certificate not working

- Ensure your domain's A record points to the VM's public IP
- Ensure port 443 is open in **both** firewalls
- Check Caddy logs: `docker compose logs caddy`
- Caddy needs port 80 open for the ACME HTTP-01 challenge
