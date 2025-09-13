# Hetzner + Cloudflare Tunnel Deployment Plan (No Docker)

## Goal
Create a single bash script that deploys the FastAPI application directly on a Hetzner VPS using systemd and Cloudflare Tunnel for zero-exposed-port architecture, with a free Cloudflare Pages domain by default.

## Architecture
```
Internet → Cloudflare Edge → Tunnel → Hetzner Server → systemd → FastAPI
                ↑                           ↑              ↑
        (SSL, DDoS, CDN)            (Zero Ports)    (Python venv)
```

## Implementation Checklist

### Phase 1: Create Master Deployment Script

- [ ] Create `deploy-simple.sh` with parameter handling
  - Accept Cloudflare API token as parameter
  - Accept optional custom domain (default to .pages.dev)
  - Accept optional repository URL for cloning
  - Validate required parameters
  - Show usage help if parameters missing

- [ ] Add system configuration
  - Update system packages
  - Set timezone to America/New_York
  - Install Python 3.12 and pip
  - Install system dependencies (git, curl, wget, sqlite3)

- [ ] Add security setup
  - Create non-root user (appuser) for running the app
  - Configure UFW firewall (SSH only)
  - Install and configure fail2ban for SSH protection
  - Harden SSH configuration

- [ ] Add application deployment
  - Clone repository or copy files from current directory
  - Create application directory (/opt/fastapi-app)
  - Set up Python virtual environment
  - Install Python requirements
  - Set proper ownership and permissions

- [ ] Add environment configuration
  - Generate secure SECRET_KEY and SESSION_SECRET
  - Create .env file with production settings
  - Configure DATABASE_URL for SQLite
  - Set HTTPS_ONLY=true for secure cookies

- [ ] Add systemd service setup
  - Create systemd service file for FastAPI
  - Configure automatic restart on failure
  - Set environment variables
  - Enable service for auto-start on boot

- [ ] Add Cloudflare Tunnel setup
  - Install cloudflared
  - Create tunnel using API token
  - Configure tunnel for localhost:8000
  - Set up as systemd service
  - Enable auto-start

- [ ] Add SQLite configuration
  - Initialize database with WAL mode
  - Set proper file permissions (600)
  - Create data directory with correct ownership

- [ ] Add backup automation
  - Create simple backup script for SQLite
  - Set up cron job for hourly backups
  - Configure 7-day retention
  - Store in /opt/fastapi-app/backups

- [ ] Add health monitoring
  - Create health check script
  - Verify FastAPI is responding
  - Check Cloudflare tunnel status
  - Monitor disk space

- [ ] Add deployment validation
  - Verify all services running
  - Test application endpoint
  - Display access URL
  - Show maintenance commands

### Phase 2: Create Supporting Scripts

- [ ] Create backup script (`backup.sh`)
  - SQLite .backup command
  - Timestamp-based naming
  - Gzip compression
  - Automatic cleanup of old backups

- [ ] Create restore script (`restore.sh`)
  - Stop FastAPI service
  - Restore from backup
  - Restart service
  - Verify restoration

- [ ] Create health check script (`health.sh`)
  - Check systemd service status
  - Verify app responds on localhost
  - Check tunnel connectivity
  - Monitor resource usage

- [ ] Create update script (`update.sh`)
  - Pull latest code from git
  - Install new dependencies
  - Run database migrations if needed
  - Restart service with zero downtime

### Phase 3: Create systemd Service Files

- [ ] Create FastAPI service (`fastapi-app.service`)
  - Run as non-root user
  - Use Python virtual environment
  - Set working directory
  - Configure restart policy
  - Load environment variables

- [ ] Configure service dependencies
  - Start after network is ready
  - Require cloudflared tunnel
  - Set resource limits
  - Configure logging

### Phase 4: Update Documentation

- [ ] Update README.md
  - Simplified deployment instructions
  - No Docker requirements
  - Direct Python execution

- [ ] Create DEPLOYMENT-SIMPLE.md
  - Step-by-step guide
  - Troubleshooting section
  - Maintenance procedures

## Script Usage

```bash
# Basic deployment with free domain
./deploy-simple.sh --api-token YOUR_TOKEN

# With custom domain
./deploy-simple.sh --api-token YOUR_TOKEN --domain yourdomain.com

# With repository URL
./deploy-simple.sh --api-token YOUR_TOKEN --repo https://github.com/you/repo
```

## Advantages of This Approach

1. **Simpler**: No Docker complexity
2. **Faster**: Direct Python execution
3. **Lighter**: Less resource overhead
4. **Easier Debugging**: Direct access to logs and processes
5. **Standard**: Uses systemd like most Linux services

## File Structure

```
/opt/fastapi-app/
├── app/                 # Application code
├── venv/               # Python virtual environment
├── data/               # SQLite database
├── backups/            # Database backups
├── logs/               # Application logs
├── scripts/            # Maintenance scripts
├── .env                # Production environment
└── requirements.txt    # Python dependencies
```

## Systemd Service Example

```ini
[Unit]
Description=FastAPI Application
After=network.target

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/fastapi-app
Environment="PATH=/opt/fastapi-app/venv/bin"
EnvironmentFile=/opt/fastapi-app/.env
ExecStart=/opt/fastapi-app/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Success Criteria

- [ ] Single script deployment
- [ ] Zero exposed ports (except SSH)
- [ ] Application accessible via HTTPS
- [ ] Database persists across restarts
- [ ] Automated backups working
- [ ] Total deployment under 10 minutes

## Deliverables

1. `deploy/deploy-simple.sh` - Main deployment script
2. `deploy/scripts/backup.sh` - Backup automation
3. `deploy/scripts/restore.sh` - Restore utility
4. `deploy/scripts/health.sh` - Health monitoring
5. `deploy/scripts/update.sh` - Update script
6. `deploy/systemd/fastapi-app.service` - Service definition
7. Updated documentation

> **Please review the simplified blueprint; reply **PROCEED** to continue or **EDIT** to make changes.**