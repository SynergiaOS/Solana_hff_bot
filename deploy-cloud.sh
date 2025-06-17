#!/bin/bash

# THE OVERMIND PROTOCOL - Cloud Deployment Script
# Automated deployment to Contabo VDS (24GB RAM)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
CLOUD_USER="marcin"
CLOUD_HOST="89.117.53.53"  # Your Contabo VDS
PROJECT_NAME="overmind-protocol"
DEPLOY_DIR="/opt/overmind-protocol"
BACKUP_DIR="/opt/backups/overmind"
LOG_FILE="/var/log/overmind-deployment.log"

# ASCII Art
echo -e "${PURPLE}"
cat << "EOF"
 _____ _   _ _____    _____  _   _ _____ ____  __  __ _____ _   _ ____  
|_   _| | | | ____|  / _ \ \| | | | ____|  _ \|  \/  |_   _| \ | |  _ \ 
  | | | |_| |  _|   | | | | | | | |  _| | |_) | |\/| | | | |  \| | | | |
  | | |  _  | |___  | |_| | |_| | | |___|  _ <| |  | | | | | |\  | |_| |
  |_| |_| |_|_____|  \___/ \___/|_|_____|_| \_\_|  |_| |_| |_| \_|____/ 

☁️  CLOUD DEPLOYMENT TO CONTABO VDS
EOF
echo -e "${NC}"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites for cloud deployment..."
    
    # Check if reorganized structure exists
    if [[ ! -d "overmind-protocol" ]]; then
        print_error "Reorganized project structure not found. Run ./reorganize-project.sh first"
        exit 1
    fi
    
    # Check required tools
    local tools=("ssh" "scp" "rsync" "docker" "docker-compose")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    # Cloud host is pre-configured for Contabo VDS
    print_status "Using pre-configured Contabo VDS: $CLOUD_HOST"
    
    print_success "Prerequisites check passed"
}

# Setup cloud server
setup_cloud_server() {
    print_status "Setting up cloud server at $CLOUD_HOST..."
    
    # Update system
    ssh "$CLOUD_USER@$CLOUD_HOST" << 'EOF'
        apt-get update && apt-get upgrade -y
        apt-get install -y curl wget git htop vim ufw fail2ban
        
        # Install Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        
        # Install Docker Compose
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        
        # Setup firewall
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 8080/tcp  # Trading system
        ufw allow 3001/tcp  # Grafana
        ufw allow 9090/tcp  # Prometheus
        ufw --force enable
        
        # Create directories
        mkdir -p /opt/overmind-protocol
        mkdir -p /opt/backups/overmind
        mkdir -p /var/log/overmind
        
        # Setup log rotation
        cat > /etc/logrotate.d/overmind << 'LOGROTATE'
/var/log/overmind/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
LOGROTATE
EOF
    
    print_success "Cloud server setup completed"
}

# Deploy application
deploy_application() {
    print_status "Deploying THE OVERMIND PROTOCOL to cloud..."
    
    # Sync project files
    print_status "Syncing project files..."
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='target' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        overmind-protocol/ "$CLOUD_USER@$CLOUD_HOST:$DEPLOY_DIR/"
    
    # Setup environment
    print_status "Setting up environment..."
    ssh "$CLOUD_USER@$CLOUD_HOST" << EOF
        cd $DEPLOY_DIR
        
        # Create production environment file
        cat > .env << 'ENVFILE'
# THE OVERMIND PROTOCOL - Production Environment
SNIPER_TRADING_MODE=paper
OVERMIND_MODE=enabled
OVERMIND_AI_MODE=enabled

# Database passwords (generated)
SNIPER_DB_PASSWORD=\$(openssl rand -base64 32)
TENSORZERO_DB_PASSWORD=\$(openssl rand -base64 32)
REDIS_PASSWORD=\$(openssl rand -base64 32)
GRAFANA_ADMIN_PASSWORD=overmind_\$(date +%s)

# Solana Configuration (devnet)
SOLANA_DEVNET_RPC_URL=https://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580
SOLANA_DEVNET_WSS_URL=wss://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580

# API Keys (to be set manually)
OPENAI_API_KEY=
GROQ_API_KEY=
MISTRAL_API_KEY=
FINANCIAL_DATASETS_API_KEY=
HELIUS_API_KEY=
QUICKNODE_API_KEY=
SOLANA_WALLET_PRIVATE_KEY=
ENVFILE

        # Make scripts executable
        chmod +x scripts/deployment/*.sh
        chmod +x scripts/maintenance/*.sh
        
        # Build Docker images
        docker-compose -f infrastructure/compose/docker-compose.overmind.yml build
        
        print_success "Application deployed to cloud"
EOF
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring and alerting..."
    
    ssh "$CLOUD_USER@$CLOUD_HOST" << EOF
        cd $DEPLOY_DIR
        
        # Create monitoring configuration
        mkdir -p /opt/monitoring/{grafana,prometheus,alertmanager}
        
        # Setup Prometheus configuration
        cat > /opt/monitoring/prometheus/prometheus.yml << 'PROMCONFIG'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'overmind-trading'
    static_configs:
      - targets: ['overmind-trading:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'overmind-brain'
    static_configs:
      - targets: ['overmind-brain:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
PROMCONFIG

        # Setup alert rules
        cat > /opt/monitoring/prometheus/alert_rules.yml << 'ALERTRULES'
groups:
  - name: overmind_alerts
    rules:
      - alert: TradingSystemDown
        expr: up{job="overmind-trading"} == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "OVERMIND Trading System is down"
          
      - alert: AIBrainDown
        expr: up{job="overmind-brain"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "OVERMIND AI Brain is down"
          
      - alert: HighLatency
        expr: overmind_execution_latency_ms > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High execution latency detected"
ALERTRULES

        print_success "Monitoring setup completed"
EOF
}

# Start services
start_services() {
    print_status "Starting THE OVERMIND PROTOCOL services..."
    
    ssh "$CLOUD_USER@$CLOUD_HOST" << EOF
        cd $DEPLOY_DIR
        
        # Start services
        docker-compose -f infrastructure/compose/docker-compose.overmind.yml up -d
        
        # Wait for services to start
        sleep 30
        
        # Check service health
        docker-compose -f infrastructure/compose/docker-compose.overmind.yml ps
        
        print_success "Services started successfully"
EOF
}

# Setup SSL and domain (optional)
setup_ssl() {
    if [[ -n "${DOMAIN_NAME:-}" ]]; then
        print_status "Setting up SSL for domain $DOMAIN_NAME..."
        
        ssh "$CLOUD_USER@$CLOUD_HOST" << EOF
            # Install Certbot
            apt-get install -y certbot nginx
            
            # Setup Nginx reverse proxy
            cat > /etc/nginx/sites-available/overmind << 'NGINXCONFIG'
server {
    listen 80;
    server_name $DOMAIN_NAME;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /grafana/ {
        proxy_pass http://localhost:3001/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
NGINXCONFIG
            
            ln -sf /etc/nginx/sites-available/overmind /etc/nginx/sites-enabled/
            nginx -t && systemctl reload nginx
            
            # Get SSL certificate
            certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME
            
            print_success "SSL setup completed for $DOMAIN_NAME"
EOF
    fi
}

# Display deployment info
display_deployment_info() {
    echo ""
    echo -e "${PURPLE}🎯 THE OVERMIND PROTOCOL - Cloud Deployment Complete${NC}"
    echo -e "${CYAN}================================================================${NC}"
    echo ""
    echo -e "${GREEN}🌐 Server:${NC}              $CLOUD_HOST"
    echo -e "${GREEN}🧠 Trading System:${NC}      http://$CLOUD_HOST:8080"
    echo -e "${GREEN}📊 Grafana:${NC}             http://$CLOUD_HOST:3001"
    echo -e "${GREEN}📈 Prometheus:${NC}          http://$CLOUD_HOST:9090"
    echo -e "${GREEN}🤖 AI Brain:${NC}            http://$CLOUD_HOST:8000"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo -e "${CYAN}  1. Set API keys in .env file on server${NC}"
    echo -e "${CYAN}  2. Configure Solana wallet${NC}"
    echo -e "${CYAN}  3. Monitor system for 48+ hours${NC}"
    echo -e "${CYAN}  4. Review logs and metrics${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Management Commands:${NC}"
    echo -e "${CYAN}  SSH to server:${NC}         ssh $CLOUD_USER@$CLOUD_HOST"
    echo -e "${CYAN}  View logs:${NC}             ssh $CLOUD_USER@$CLOUD_HOST 'cd $DEPLOY_DIR && docker-compose logs -f'"
    echo -e "${CYAN}  Restart system:${NC}        ssh $CLOUD_USER@$CLOUD_HOST 'cd $DEPLOY_DIR && docker-compose restart'"
    echo -e "${CYAN}  Stop system:${NC}           ssh $CLOUD_USER@$CLOUD_HOST 'cd $DEPLOY_DIR && docker-compose down'"
    echo ""
    echo -e "${PURPLE}🧠 THE OVERMIND PROTOCOL is now running in the cloud!${NC}"
    echo -e "${YELLOW}⚠️  Remember: System is in PAPER TRADING mode${NC}"
    echo ""
}

# Main deployment function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                CLOUD_HOST="$2"
                shift 2
                ;;
            --domain)
                DOMAIN_NAME="$2"
                shift 2
                ;;
            *)
                echo "Usage: $0 --host <server-ip> [--domain <domain-name>]"
                exit 1
                ;;
        esac
    done
    
    # Check if host is provided via environment or command line
    if [[ -z "${CLOUD_HOST}" ]]; then
        print_error "Cloud host not specified. Use: $0 --host <server-ip>"
        exit 1
    fi
    
    print_status "🚀 Starting cloud deployment to $CLOUD_HOST"
    
    check_prerequisites
    setup_cloud_server
    deploy_application
    setup_monitoring
    start_services
    setup_ssl
    display_deployment_info
    
    print_success "🎯 Cloud deployment completed successfully!"
}

# Execute main function with all arguments
main "$@"
