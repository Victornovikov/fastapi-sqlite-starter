#!/bin/bash

# FastAPI Hetzner + Cloudflare Tunnel Deployment Script
# Direct deployment using systemd and Python virtual environment
# Usage: ./deploy.sh --api-token YOUR_CLOUDFLARE_API_TOKEN [--domain your-domain.com]

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="fastapi-app"
APP_USER="appuser"
TIMEZONE="America/New_York"
PYTHON_VERSION="python3.12"
# APP_DIR will be set based on where the script is run from or git clone location

# Function to print colored output
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Parse command line arguments
parse_args() {
    API_TOKEN=""
    DOMAIN=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-token)
                API_TOKEN="$2"
                shift 2
                ;;
            --domain)
                DOMAIN="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 --api-token YOUR_CLOUDFLARE_API_TOKEN [OPTIONS]"
                echo ""
                echo "Required:"
                echo "  --api-token TOKEN    Your Cloudflare API token"
                echo ""
                echo "Optional:"
                echo "  --domain DOMAIN      Custom domain (default: uses .pages.dev subdomain)"
                echo "  --help, -h           Show this help message"
                echo ""
                echo "Run this script from within your cloned git repository"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    if [[ -z "$API_TOKEN" ]]; then
        log_error "Cloudflare API token is required"
        echo "Usage: $0 --api-token YOUR_CLOUDFLARE_API_TOKEN"
        exit 1
    fi
    
    # Always use the repository we're running from
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    APP_DIR="$(dirname "$SCRIPT_DIR")"
    
    if [[ ! -f "$APP_DIR/requirements.txt" ]]; then
        log_error "Error: requirements.txt not found in $APP_DIR"
        log_error "Make sure you're running this script from within your cloned repository"
        exit 1
    fi
    
    log_info "Using repository at: $APP_DIR"
}

# System configuration
configure_system() {
    log_info "Updating system packages..."
    apt-get update -qq
    apt-get upgrade -y -qq
    
    log_info "Setting timezone to ${TIMEZONE}..."
    timedatectl set-timezone ${TIMEZONE}
    
    log_info "Installing system dependencies..."
    # Install base dependencies first
    apt-get install -y -qq \
        curl wget git nano htop net-tools \
        ufw fail2ban \
        software-properties-common \
        build-essential \
        sqlite3 \
        python3 python3-venv python3-dev \
        python3-pip \
        nginx \
        supervisor \
        jq \
        lsof || true
    
    # Try to install Python 3.12 specific packages if available
    apt-get install -y -qq python3.12 python3.12-venv python3.12-dev 2>/dev/null || log_warning "Python 3.12 packages not available, using system Python"
    
    log_success "System configuration complete"
}

# Create application user
create_user() {
    log_info "Creating application user..."
    
    if id "$APP_USER" &>/dev/null; then
        log_warning "User ${APP_USER} already exists"
    else
        adduser --disabled-password --gecos "" ${APP_USER}
        log_success "User ${APP_USER} created"
    fi
}

# Configure firewall
configure_firewall() {
    log_info "Configuring UFW firewall..."

    ufw --force disable
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 22/tcp
    ufw allow 60000:61000/udp  # Allow mosh for mobile shell connections
    echo "y" | ufw --force enable

    log_success "Firewall configured (SSH, mosh enabled, no exposed web ports)"
}

# Configure fail2ban
configure_fail2ban() {
    log_info "Configuring fail2ban..."
    
    cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log_success "fail2ban configured"
}

# Create required directories (ones not in git)
create_runtime_directories() {
    log_info "Creating runtime directories..."

    # Create logs directory for application logs
    mkdir -p ${APP_DIR}/logs

    # Create log files with proper permissions to avoid permission errors
    touch ${APP_DIR}/logs/app.log
    touch ${APP_DIR}/logs/access.log
    touch ${APP_DIR}/logs/error.log

    # Set ownership for the entire repo to app user
    chown -R ${APP_USER}:${APP_USER} ${APP_DIR}

    # Ensure log files have write permissions for app user
    chmod 664 ${APP_DIR}/logs/*.log

    log_success "Runtime directories created"
}

# Set up Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    cd ${APP_DIR}
    
    # Create virtual environment as root first, then change ownership
    # Use the pyenv Python if available, otherwise fall back to system python3
    if command -v python3 &> /dev/null; then
        python3 -m venv venv
    else
        python3.12 -m venv venv
    fi
    chown -R ${APP_USER}:${APP_USER} venv
    
    # Upgrade pip
    sudo -u ${APP_USER} ${APP_DIR}/venv/bin/pip install --upgrade pip
    
    # Install requirements
    log_info "Installing Python dependencies..."
    sudo -u ${APP_USER} ${APP_DIR}/venv/bin/pip install -r requirements.txt
    
    # Install additional production dependencies
    sudo -u ${APP_USER} ${APP_DIR}/venv/bin/pip install gunicorn
    
    log_success "Python environment configured"
}

# Generate environment file
generate_env_file() {
    log_info "Generating production environment file..."

    # Generate secure keys
    SECRET_KEY=$(openssl rand -hex 32)

    # Determine domain and email settings
    if [[ -z "$DOMAIN" ]]; then
        # Generate random subdomain for pages.dev
        RANDOM_NAME="${APP_NAME}-$(openssl rand -hex 4)"
        DOMAIN="${RANDOM_NAME}.pages.dev"
        log_info "Using free domain: ${DOMAIN}"
        EMAIL_FROM="noreply@${DOMAIN}"
    else
        log_info "Using custom domain: ${DOMAIN}"
        EMAIL_FROM="noreply@${DOMAIN}"
    fi

    # Determine reset URL base
    RESET_URL_BASE="https://${DOMAIN}/reset"

    cat > ${APP_DIR}/.env <<EOF
# Production Environment Configuration

# Core settings
DATABASE_URL=sqlite:///${APP_DIR}/app.db
SECRET_KEY=${SECRET_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production

# Email settings (configure these with your actual API keys)
RESEND_API_KEY=
EMAIL_FROM=${EMAIL_FROM}
EMAIL_FROM_NAME=FastAPI App
RESET_URL_BASE=${RESET_URL_BASE}

# Optional webhook secret for Resend
RESEND_WEBHOOK_SECRET=

# Logging settings
LOG_LEVEL=INFO
LOG_DIR=${APP_DIR}/logs
LOG_FILE=app.log
LOG_MAX_BYTES=5242880
LOG_BACKUP_COUNT=5
LOG_TO_CONSOLE=true

# Optional AI integrations (add your API keys if needed)
OPENAI_API_KEY=

# CORS settings (comma-separated list of allowed origins)
CORS_ORIGINS=https://${DOMAIN}

# App domain
APP_DOMAIN=${DOMAIN}
APP_DIR=${APP_DIR}
EOF

    chmod 600 ${APP_DIR}/.env
    chown ${APP_USER}:${APP_USER} ${APP_DIR}/.env

    log_success "Environment file generated"
    log_warning "Remember to add your API keys (RESEND_API_KEY, OPENAI_API_KEY, etc.) to ${APP_DIR}/.env"
}

# Create systemd service for FastAPI
create_systemd_service() {
    log_info "Creating systemd service for FastAPI..."
    
    cat > /etc/systemd/system/fastapi-app.service <<EOF
[Unit]
Description=FastAPI Application
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
EnvironmentFile=${APP_DIR}/.env

# Use Gunicorn with Uvicorn workers for production
ExecStart=${APP_DIR}/venv/bin/gunicorn app.main:app \\
    --workers 2 \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --bind 127.0.0.1:8000 \\
    --access-logfile ${APP_DIR}/logs/access.log \\
    --error-logfile ${APP_DIR}/logs/error.log \\
    --capture-output \\
    --enable-stdio-inheritance

# Restart policy
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true

# Resource limits
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable fastapi-app
    
    log_success "Systemd service created"
}

# Check and free port
check_and_free_port() {
    local port=$1
    log_info "Checking if port ${port} is available..."
    
    # Check if port is in use
    if lsof -i :${port} >/dev/null 2>&1; then
        log_warning "Port ${port} is in use. Attempting to free it..."
        
        # Get PIDs using the port
        PIDS=$(lsof -t -i :${port} 2>/dev/null)
        
        if [[ -n "$PIDS" ]]; then
            # Show what's using the port
            log_info "Processes using port ${port}:"
            lsof -i :${port} || true
            
            # Kill the processes
            for pid in $PIDS; do
                log_info "Killing process $pid"
                kill -9 $pid 2>/dev/null || true
            done
            
            # Wait a moment for port to be freed
            sleep 2
            
            # Verify port is now free
            if lsof -i :${port} >/dev/null 2>&1; then
                log_error "Failed to free port ${port}"
                exit 1
            else
                log_success "Port ${port} is now free"
            fi
        fi
    else
        log_success "Port ${port} is available"
    fi
}

# Initialize database
initialize_database() {
    log_info "Initializing SQLite database..."
    
    # Check and free port before starting service
    check_and_free_port 8000
    
    # Start the service temporarily to create database
    systemctl start fastapi-app
    sleep 5
    
    # Set WAL mode for better concurrency
    if [[ -f ${APP_DIR}/app.db ]]; then
        sqlite3 ${APP_DIR}/app.db "PRAGMA journal_mode=WAL;"
        # Set proper permissions - 664 allows owner and group to read/write
        chmod 664 ${APP_DIR}/app.db
        chown ${APP_USER}:${APP_USER} ${APP_DIR}/app.db
        log_success "Database initialized with WAL mode"
    else
        log_warning "Database will be created on first access"
    fi

    # Also ensure any WAL files have proper permissions
    if [[ -f ${APP_DIR}/app.db-wal ]]; then
        chmod 664 ${APP_DIR}/app.db-wal
        chown ${APP_USER}:${APP_USER} ${APP_DIR}/app.db-wal
    fi
    if [[ -f ${APP_DIR}/app.db-shm ]]; then
        chmod 664 ${APP_DIR}/app.db-shm
        chown ${APP_USER}:${APP_USER} ${APP_DIR}/app.db-shm
    fi
    
    # Restart service
    systemctl restart fastapi-app
}

# Install Cloudflare Tunnel
install_cloudflared() {
    log_info "Installing cloudflared..."
    
    if command -v cloudflared &> /dev/null; then
        log_warning "cloudflared already installed"
    else
        # Download and install cloudflared
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        dpkg -i cloudflared-linux-amd64.deb
        rm cloudflared-linux-amd64.deb
    fi
    
    log_success "cloudflared installed"
}

# Configure Cloudflare Tunnel
configure_tunnel() {
    log_info "Configuring Cloudflare Tunnel..."
    
    # Get domain from env file
    source ${APP_DIR}/.env
    
    # Create tunnel configuration directory
    mkdir -p /etc/cloudflared
    
    # Generate tunnel name
    TUNNEL_NAME="${APP_NAME}-$(date +%s)"
    
    # Create tunnel using service token
    export TUNNEL_TOKEN="${API_TOKEN}"
    
    log_info "Creating tunnel: ${TUNNEL_NAME}..."
    # Create .cloudflared directory if it doesn't exist
    mkdir -p /root/.cloudflared
    mkdir -p /etc/cloudflared
    
    # For service tokens, we create the tunnel and get a token in one step
    log_info "Creating tunnel with service token..."
    
    # Generate a unique tunnel secret
    TUNNEL_SECRET=$(openssl rand -hex 32)
    
    # Create the tunnel using the Cloudflare API directly
    ACCOUNT_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts" \
        -H "Authorization: Bearer ${API_TOKEN}" \
        -H "Content-Type: application/json" | jq -r '.result[0].id')
    
    if [[ -z "$ACCOUNT_ID" || "$ACCOUNT_ID" == "null" ]]; then
        log_error "Failed to get Cloudflare account ID. Check your API token permissions."
        exit 1
    fi
    
    # Create tunnel via API
    TUNNEL_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels" \
        -H "Authorization: Bearer ${API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"${TUNNEL_NAME}\",\"tunnel_secret\":\"${TUNNEL_SECRET}\"}")
    
    TUNNEL_ID=$(echo "$TUNNEL_RESPONSE" | jq -r '.result.id')
    TUNNEL_TOKEN=$(echo "$TUNNEL_RESPONSE" | jq -r '.result.token')
    
    if [[ -z "$TUNNEL_ID" || "$TUNNEL_ID" == "null" ]]; then
        log_error "Failed to create tunnel"
        echo "$TUNNEL_RESPONSE" | jq '.'
        exit 1
    fi
    
    log_success "Tunnel created with ID: ${TUNNEL_ID}"
    
    # Create tunnel configuration
    cat > /etc/cloudflared/config.yml <<EOF
url: http://localhost:8000
tunnel: ${TUNNEL_ID}
credentials-file: /etc/cloudflared/${TUNNEL_ID}.json
EOF

    # Create credentials file with the tunnel token
    cat > /etc/cloudflared/${TUNNEL_ID}.json <<EOF
{
  "AccountTag": "${ACCOUNT_ID}",
  "TunnelSecret": "${TUNNEL_SECRET}",
  "TunnelID": "${TUNNEL_ID}"
}
EOF
    chmod 600 /etc/cloudflared/${TUNNEL_ID}.json
    
    # Configure ingress rules via API
    log_info "Configuring tunnel ingress rules..."
    
    # For .pages.dev domains or when no domain is configured, skip hostname configuration
    if [[ "$DOMAIN" == *.pages.dev ]] || [[ -z "$DOMAIN" ]]; then
        # Configure tunnel without hostname - will require manual configuration in dashboard
        INGRESS_CONFIG='{
            "config": {
                "ingress": [
                    {
                        "service": "http://localhost:8000"
                    }
                ]
            }
        }'
        log_warning "No valid domain configured. You'll need to add a public hostname in Cloudflare Dashboard."
    else
        # Configure with hostname for properly owned domains
        INGRESS_CONFIG='{
            "config": {
                "ingress": [
                    {
                        "hostname": "'${APP_DOMAIN}'",
                        "service": "http://localhost:8000"
                    },
                    {
                        "service": "http_status:404"
                    }
                ]
            }
        }'
    fi
    
    INGRESS_RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/tunnels/${TUNNEL_ID}/configurations" \
        -H "Authorization: Bearer ${API_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$INGRESS_CONFIG")
    
    # Check if ingress configuration was successful
    if echo "$INGRESS_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        log_success "Tunnel ingress rules configured"
    else
        log_warning "Failed to configure tunnel ingress rules. Manual configuration may be required."
        echo "$INGRESS_RESPONSE" | jq '.' || echo "$INGRESS_RESPONSE"
    fi
    
    # Route DNS (if using custom domain)
    if [[ "$DOMAIN" != *.pages.dev ]] && [[ -n "$DOMAIN" ]]; then
        log_info "Checking if ${DOMAIN} is managed in Cloudflare..."
        # Get zone ID for the domain
        ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=${DOMAIN#*.}" \
            -H "Authorization: Bearer ${API_TOKEN}" \
            -H "Content-Type: application/json" | jq -r '.result[0].id')
        
        if [[ -n "$ZONE_ID" && "$ZONE_ID" != "null" ]]; then
            # Create CNAME record
            DNS_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
                -H "Authorization: Bearer ${API_TOKEN}" \
                -H "Content-Type: application/json" \
                -d "{
                    \"type\":\"CNAME\",
                    \"name\":\"${DOMAIN%%.*}\",
                    \"content\":\"${TUNNEL_ID}.cfargotunnel.com\",
                    \"proxied\":true
                }")
            log_success "DNS record created for ${DOMAIN}"
        else
            log_warning "Could not find zone for ${DOMAIN}. You may need to add the DNS record manually."
        fi
    else
        # For .pages.dev domains or unconfigured domains, no public URL is available yet
        APP_DOMAIN=""
        log_warning "No public hostname configured. You'll need to configure one in Cloudflare Dashboard."
        log_info "Tunnel ID: ${TUNNEL_ID}"
    fi
    
    # Create systemd service for tunnel
    cat > /etc/systemd/system/cloudflared.service <<EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=notify
ExecStart=/usr/local/bin/cloudflared --config /etc/cloudflared/config.yml tunnel run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl start cloudflared
    systemctl enable cloudflared
    
    log_success "Cloudflare Tunnel configured and started"
    
    # Update .env file with actual APP_DOMAIN value
    if [[ -f ${APP_DIR}/.env ]]; then
        if [[ -z "$APP_DOMAIN" ]]; then
            # Remove or comment out APP_DOMAIN if no public URL
            sed -i 's/^APP_DOMAIN=.*/# APP_DOMAIN not configured - add public hostname in Cloudflare Dashboard/' ${APP_DIR}/.env
        else
            # Update with actual domain
            sed -i "s|^APP_DOMAIN=.*|APP_DOMAIN=${APP_DOMAIN}|" ${APP_DIR}/.env
        fi
    fi
}



# Final validation
validate_deployment() {
    log_info "Validating deployment..."
    
    echo ""
    echo "==================================="
    echo "Deployment Validation"
    echo "==================================="
    
    # Check services are running
    if systemctl is-active fastapi-app > /dev/null; then
        echo "✓ FastAPI service: Running"
    else
        echo "✗ FastAPI service: Not running"
    fi
    
    if systemctl is-active cloudflared > /dev/null; then
        echo "✓ Cloudflare tunnel: Active"
    else
        echo "✗ Cloudflare tunnel: Not active"
    fi
    
    echo ""
    echo "==================================="
    echo "Deployment Complete!"
    echo "==================================="
    echo ""
    
    source ${APP_DIR}/.env
    
    echo "Your application status:"
    if [[ -z "$APP_DOMAIN" ]] || [[ "$DOMAIN" == *.pages.dev ]]; then
        echo ""
        echo "  ⚠️  No public URL configured yet!"
        echo ""
        echo "  To make your app accessible from the internet:"
        echo "  1. Go to Cloudflare Dashboard > Zero Trust > Networks > Tunnels"
        echo "  2. Find your tunnel: ${TUNNEL_ID}"
        echo "  3. Click on it and go to 'Public Hostname' tab"
        echo "  4. Add a hostname with:"
        echo "     - Subdomain: Choose any name (e.g., 'my-app')"
        echo "     - Domain: Select one of your domains"
        echo "     - Service: http://localhost:8000"
        echo ""
        echo "  Tunnel ID: ${TUNNEL_ID}"
    else
        echo "  https://${APP_DOMAIN}"
    fi
    echo ""
    echo "Cloudflare Dashboard:"
    echo "  View tunnel: https://dash.cloudflare.com/select-account/zero-trust/tunnels"
    echo ""
    echo "Useful commands:"
    echo "  Check status:     systemctl status fastapi-app"
    echo "  View logs:        journalctl -u fastapi-app -f"
    echo "  Restart app:      systemctl restart fastapi-app"
    echo "  Update app:       cd ${APP_DIR} && git pull && systemctl restart fastapi-app"
    echo "  Tunnel status:    systemctl status cloudflared"
    echo ""
    echo "==================================="
    
    log_success "Deployment validated successfully!"
}

# Main execution
main() {
    echo "==================================="
    echo "FastAPI Deployment Script"
    echo "==================================="
    echo ""
    
    check_root
    parse_args "$@"
    
    log_info "Starting deployment..."
    
    # Phase 1: System Setup
    configure_system
    create_user
    configure_firewall
    configure_fail2ban
    
    # Phase 2: Application Setup
    create_runtime_directories
    setup_python_env
    generate_env_file
    
    # Phase 3: Service Configuration
    create_systemd_service
    initialize_database
    
    # Phase 4: Cloudflare Tunnel
    install_cloudflared
    configure_tunnel
    
    # Phase 5: Validation
    validate_deployment
    
    log_success "Deployment complete!"
}

# Run main function with all arguments
main "$@"
