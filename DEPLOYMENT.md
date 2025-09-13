# Production Deployment Guide

Deploy your FastAPI app to a VPS with Cloudflare Tunnel for secure, zero-exposed-ports hosting.

## Prerequisites

- Fresh Ubuntu 22.04 VPS (Hetzner, DigitalOcean, or any provider)
- [Cloudflare account](https://dash.cloudflare.com/sign-up) (free)
- Domain added to Cloudflare (optional but recommended)
- SSH access to your server

## Quick Deploy (15 minutes)

### 1. Get Cloudflare API Token

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. Click **Create Token**
3. Use template: **Create Custom Token**
4. Set permissions:
   - Account > Cloudflare Tunnel > Edit
   - Zone > Zone > Read
   - Zone > DNS > Edit (if using custom domain)
5. Click **Continue** → **Create Token**
6. Copy the token (shown only once!)

### 2. Deploy Your App

SSH to your server and run:

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Run deployment (as root)
sudo ./deploy/deploy.sh --api-token YOUR_CLOUDFLARE_TOKEN

# Optional: specify domain (must be added to Cloudflare)
sudo ./deploy/deploy.sh --api-token YOUR_TOKEN --domain yourdomain.com
```

### 3. Configure Public Access (Required Manual Step)

The deployment creates a tunnel but **does NOT** make it publicly accessible. You must:

1. Go to [Cloudflare Zero Trust Dashboard](https://dash.cloudflare.com)
2. Navigate to **Networks** → **Tunnels**
3. Find your tunnel (ID shown in deployment output)
4. Click on it, then click **Configure**
5. You'll need to **migrate to Cloudflare-managed** if prompted
6. Go to **Public Hostname** tab
7. Click **Add a public hostname**:
   - **Subdomain**: Choose any (or leave blank for root)
   - **Domain**: Select from your Cloudflare domains
   - **Type**: HTTP
   - **URL**: `localhost:8000`
8. Save the configuration

Your app will be available at `https://[subdomain.]yourdomain.com` within minutes!

## What Actually Happens

### The Script Automates:
- ✅ Python 3.12 installation and virtual environment
- ✅ FastAPI app setup as systemd service
- ✅ Cloudflare tunnel creation
- ✅ SQLite database with WAL mode
- ✅ Environment configuration

### You Must Manually:
- ❌ Configure public hostname in Cloudflare Dashboard
- ❌ Migrate tunnel from local to remote management (if needed)
- ❌ Set up custom domain DNS (if not using Cloudflare DNS)

### Why Manual Steps?
The deployment creates a **locally-managed tunnel** which requires manual configuration for public access. This is because:
- `.pages.dev` domains don't work with tunnels
- Domain validation would require additional API permissions
- Remote-managed tunnels are easier to configure via dashboard

## Daily Operations

### Update Your App
```bash
cd /opt/fastapi-sqlite  # or your app directory
git pull
sudo systemctl restart fastapi-app
```

### Check Status
```bash
# Service status
sudo systemctl status fastapi-app

# View logs
sudo journalctl -u fastapi-app -f

# Tunnel status
sudo systemctl status cloudflared
```

### Common Issues

#### App crashes with "Extra inputs are not permitted"
Your `app/config.py` needs to ignore extra .env fields:
```python
class Config:
    env_file = ".env"
    extra = "ignore"  # Add this line
```

#### "This site can't be reached"
- Tunnel is running but no public hostname configured
- Follow step 3 above to add public hostname

#### 502 Bad Gateway
- FastAPI app is not running
- Check: `sudo systemctl status fastapi-app`
- Check logs: `sudo journalctl -u fastapi-app -n 50`

## File Structure

After deployment:

```
/opt/fastapi-sqlite/     # Or your specified directory
├── venv/               # Python virtual environment
├── logs/               # Application logs
├── app.db              # SQLite database
├── .env                # Production configuration
└── app/                # Your application code
```

## Security Features

- **Zero exposed ports** - Only SSH (22) is open
- **All traffic through Cloudflare** - DDoS protection included
- **Non-root execution** - App runs as `appuser`
- **Automatic HTTPS** - SSL/TLS via Cloudflare
- **WAL mode SQLite** - Better concurrency handling

## Alternative: Fully Automated Deployment

For a fully automated deployment without manual steps:

1. Add your domain to Cloudflare first
2. Ensure the domain's DNS is managed by Cloudflare
3. Use the domain in deployment: `--domain yourdomain.com`
4. The script will attempt to configure everything automatically

**Note**: This only works if your domain is already in your Cloudflare account.

## Need Help?

1. Check service logs: `sudo journalctl -u fastapi-app -n 100`
2. Check tunnel logs: `sudo journalctl -u cloudflared -n 100`
3. Verify tunnel in [Cloudflare Dashboard](https://dash.cloudflare.com)
4. Check [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

---

**Pro tips:**
- Save your Cloudflare API token securely
- Use a password manager for the token
- Consider using Cloudflare Access for authentication
- Monitor your tunnel health in the Zero Trust dashboard