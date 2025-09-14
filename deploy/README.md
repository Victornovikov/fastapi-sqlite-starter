# FastAPI Deployment with Cloudflare Tunnel

This directory contains an automated deployment script for deploying a FastAPI application on a Linux server (optimized for Hetzner) with Cloudflare Tunnel for secure HTTPS access without exposing ports.

## Overview

The `deploy.sh` script automates the complete deployment process including:
- System configuration and security hardening
- Python environment setup
- Application service configuration
- Cloudflare Tunnel setup for secure HTTPS access
- Database initialization

## Requirements

- **Operating System**: Ubuntu/Debian-based Linux
- **Privileges**: Root access required
- **Cloudflare Account**: With API token
- **Repository**: Must be run from within the cloned git repository

## Usage

### Basic Usage

```bash
sudo ./deploy/deploy.sh --api-token YOUR_CLOUDFLARE_API_TOKEN
```

### With Custom Domain

```bash
sudo ./deploy/deploy.sh --api-token YOUR_CLOUDFLARE_API_TOKEN --domain your-domain.com
```

### Command Line Options

- `--api-token TOKEN` (Required): Your Cloudflare API token with tunnel creation permissions
- `--domain DOMAIN` (Optional): Custom domain for the application. If not provided, uses .pages.dev subdomain
- `--help, -h`: Display help message

## What the Script Does

### Phase 1: System Setup

1. **System Updates**
   - Updates package lists
   - Upgrades all system packages
   - Sets timezone to America/New_York

2. **Dependencies Installation**
   - Core utilities: curl, wget, git, nano, htop, net-tools
   - Security tools: ufw, fail2ban
   - Python: python3, python3-venv, python3-dev, python3-pip
   - Python 3.12 if available
   - Web server: nginx, supervisor
   - Database: sqlite3
   - Utilities: jq, lsof

3. **User Creation**
   - Creates dedicated `appuser` for running the application
   - No password, restricted shell access

4. **Firewall Configuration (UFW)**
   - Denies all incoming connections except SSH
   - Allows all outgoing connections
   - Note: Web ports not exposed (Cloudflare Tunnel handles this)

5. **Fail2ban Setup**
   - Configures SSH protection
   - 3 failed attempts = 1 hour ban
   - Monitors `/var/log/auth.log`

### Phase 2: Application Setup

1. **Directory Structure**
   - Creates `/logs` directory for application logs
   - Sets proper ownership to `appuser`

2. **Python Virtual Environment**
   - Creates venv in application directory
   - Upgrades pip to latest version
   - Installs all requirements from `requirements.txt`
   - Installs production server: gunicorn

3. **Environment Configuration**
   - Generates secure SECRET_KEY (32 bytes)
   - Generates SESSION_SECRET (32 bytes)
   - Sets database path to `sqlite:///app.db`
   - Configures HTTPS-only mode
   - Sets token expiration times
   - Configures CORS for the domain

### Phase 3: Service Configuration

1. **SystemD Service Creation** (`/etc/systemd/system/fastapi-app.service`)
   - Uses Gunicorn with Uvicorn workers
   - 2 worker processes for production
   - Binds to localhost:8000 (not exposed externally)
   - Auto-restart on failure
   - Logs to `logs/access.log` and `logs/error.log`
   - Security: NoNewPrivileges, PrivateTmp
   - Resource limit: 65536 file descriptors

2. **Database Initialization**
   - Creates SQLite database
   - Sets WAL (Write-Ahead Logging) mode for better concurrency
   - Sets secure permissions (600)

### Phase 4: Cloudflare Tunnel Setup

1. **Cloudflared Installation**
   - Downloads and installs latest cloudflared binary
   - From official Cloudflare GitHub releases

2. **Tunnel Creation**
   - Creates unique tunnel with timestamp suffix
   - Generates secure tunnel secret (32 bytes)
   - Uses Cloudflare API to create tunnel
   - Stores credentials in `/etc/cloudflared/`

3. **Tunnel Configuration**
   - Routes traffic from Cloudflare to localhost:8000
   - Configures ingress rules
   - For custom domains: Sets up DNS CNAME record
   - For .pages.dev: Requires manual configuration in dashboard

4. **Tunnel Service** (`/etc/systemd/system/cloudflared.service`)
   - Runs cloudflared as system service
   - Auto-restart on failure
   - Starts on system boot

### Phase 5: Validation

The script validates:
- FastAPI service is running
- Cloudflare tunnel is active
- Provides status information and useful commands

## Security Features

1. **No Port Exposure**: Application runs on localhost only, accessed via Cloudflare Tunnel
2. **Firewall**: UFW blocks all incoming except SSH
3. **Fail2ban**: Protects against SSH brute force
4. **Secure Tokens**: Cryptographically secure random tokens
5. **File Permissions**: Restrictive permissions on sensitive files
6. **System Hardening**: NoNewPrivileges, PrivateTmp for services
7. **HTTPS Only**: All traffic encrypted via Cloudflare

## Auto-Restart Behavior

### Application Crash Recovery

**YES, the application automatically restarts if it crashes!**

The SystemD service is configured with `Restart=always` and `RestartSec=10`, which means:
- **Automatic restart**: If the FastAPI app crashes for any reason, SystemD will automatically restart it
- **10-second delay**: Waits 10 seconds before restarting to avoid rapid restart loops
- **Persistent**: Continues trying to restart indefinitely until the app runs successfully
- **Boot persistence**: Service starts automatically when the server reboots

You can verify this in the service file:
```bash
cat /etc/systemd/system/fastapi-app.service | grep Restart
# Output:
# Restart=always
# RestartSec=10
```

To check if the app has been restarting:
```bash
# Check service status and recent restarts
sudo systemctl status fastapi-app

# View restart history
sudo journalctl -u fastapi-app | grep "Started FastAPI"
```

## Service Management

### Application Service

```bash
# Check status
sudo systemctl status fastapi-app

# View logs
sudo journalctl -u fastapi-app -f

# Restart manually
sudo systemctl restart fastapi-app

# Stop (will NOT auto-restart when stopped manually)
sudo systemctl stop fastapi-app

# Start
sudo systemctl start fastapi-app

# Disable auto-start on boot
sudo systemctl disable fastapi-app

# Enable auto-start on boot
sudo systemctl enable fastapi-app
```

### Cloudflare Tunnel

```bash
# Check status
sudo systemctl status cloudflared

# View logs
sudo journalctl -u cloudflared -f

# Restart
sudo systemctl restart cloudflared
```

## Updating the Application

```bash
cd /path/to/your/app
git pull
sudo systemctl restart fastapi-app
```

## Logs

- **Application logs**: `<app_dir>/logs/app.log`
- **Access logs**: `<app_dir>/logs/access.log`
- **Error logs**: `<app_dir>/logs/error.log`
- **System logs**: `journalctl -u fastapi-app`
- **Tunnel logs**: `journalctl -u cloudflared`

## Known Issues and Fixes

### Mosh Connectivity Issue

**Problem**: After running the deployment script, mosh connections fail because UFW firewall blocks mosh UDP ports.

**Solution**: Add mosh ports to UFW rules:

```bash
# Allow mosh (UDP ports 60000-61000)
sudo ufw allow 60000:61000/udp

# Verify the rule was added
sudo ufw status

# Now mosh should work
mosh user@your-server
```

**Permanent Fix**: Add this to the deployment script's `configure_firewall()` function:
```bash
ufw allow 60000:61000/udp  # Add after the SSH rule
```

## Troubleshooting

### Port 8000 Already in Use

The script automatically checks and frees port 8000 if it's in use. It will:
1. Detect processes using the port
2. Kill those processes
3. Verify the port is free

### Database Issues

- Database is created at first startup
- WAL mode enabled for better concurrency
- Located at `<app_dir>/app.db`
- Permissions: 600 (read/write for owner only)

### Tunnel Not Working

1. Check tunnel status: `sudo systemctl status cloudflared`
2. Verify tunnel in Cloudflare Dashboard
3. For .pages.dev domains: Manual configuration required in dashboard
4. Check logs: `sudo journalctl -u cloudflared -f`

### Application Not Starting

1. Check service status: `sudo systemctl status fastapi-app`
2. Check logs: `sudo journalctl -u fastapi-app -f`
3. Verify Python dependencies installed correctly
4. Check `.env` file exists and has correct permissions

## Environment Variables

The script generates a `.env` file with:

- `SECRET_KEY`: JWT signing key
- `SESSION_SECRET`: Session encryption key
- `DATABASE_URL`: SQLite database path
- `HTTPS_ONLY`: Force HTTPS (true)
- `ALGORITHM`: JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiry (30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiry (7)
- `CORS_ORIGINS`: Allowed CORS origins
- `APP_DOMAIN`: Application domain
- `APP_DIR`: Application directory path

## Cloudflare Requirements

### API Token Permissions

Your Cloudflare API token needs:
- Account: Cloudflare Tunnel:Edit
- Zone: DNS:Edit (if using custom domain)

### Manual Steps for .pages.dev Domains

If not using a custom domain:
1. Go to Cloudflare Dashboard > Zero Trust > Networks > Tunnels
2. Find your tunnel by ID (shown after deployment)
3. Click "Configure" > "Public Hostname"
4. Add hostname with your desired subdomain and domain
5. Set service to `http://localhost:8000`

## Production Considerations

1. **Change default timezone** in script if needed (currently America/New_York)
2. **Review worker count** in systemd service (currently 2)
3. **Monitor logs** regularly for errors
4. **Set up backups** for the SQLite database
5. **Configure monitoring** for service health
6. **Review rate limits** in application code
7. **Set up log rotation** if needed (default: 5MB, 5 backups)

## Support

For issues with:
- **Application code**: Check application documentation
- **Deployment script**: Review this README and script comments
- **Cloudflare Tunnel**: Consult [Cloudflare Tunnel documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- **SystemD services**: Use `journalctl` for debugging