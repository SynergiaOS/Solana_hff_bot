#!/bin/bash

# THE OVERMIND PROTOCOL - Contabo VDS Deployment
# Optimized deployment for marcin@89.117.53.53

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration for your Contabo VDS
CLOUD_USER="marcin"
CLOUD_HOST="89.117.53.53"
PROJECT_NAME="overmind-protocol"
DEPLOY_DIR="/home/marcin/overmind-protocol"
BACKUP_DIR="/home/marcin/backups/overmind"
LOG_FILE="/home/marcin/overmind-deployment.log"

# ASCII Art
echo -e "${PURPLE}"
cat << "EOF"
 _____ _   _ _____    _____  _   _ _____ ____  __  __ _____ _   _ ____  
|_   _| | | | ____|  / _ \ \| | | | ____|  _ \|  \/  |_   _| \ | |  _ \ 
  | | | |_| |  _|   | | | | | | | |  _| | |_) | |\/| | | | |  \| | | | |
  | | |  _  | |___  | |_| | |_| | | |___|  _ <| |  | | | | | |\  | |_| |
  |_| |_| |_|_____|  \___/ \___/|_|_____|_| \_\_|  |_| |_| |_| \_|____/ 

🚀 CONTABO VDS DEPLOYMENT - marcin@89.117.53.53
EOF
echo -e "${NC}"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test SSH connection
test_ssh_connection() {
    print_status "Testing SSH connection to $CLOUD_HOST..."
    
    if ssh -o ConnectTimeout=10 "$CLOUD_USER@$CLOUD_HOST" "echo 'SSH connection successful'" > /dev/null 2>&1; then
        print_success "SSH connection to $CLOUD_HOST established"
    else
        print_error "Cannot connect to $CLOUD_HOST via SSH"
        print_error "Please check your SSH configuration and try again"
        exit 1
    fi
}

# Check local prerequisites
check_local_prerequisites() {
    print_status "Checking local prerequisites..."
    
    # Check if reorganized structure exists
    if [[ ! -d "overmind-protocol" ]]; then
        print_warning "Reorganized project structure not found. Running reorganization..."
        if [[ -f "./reorganize-project.sh" ]]; then
            ./reorganize-project.sh
        else
            print_error "reorganize-project.sh not found. Please run it first."
            exit 1
        fi
    fi
    
    # Check required tools
    local tools=("ssh" "scp" "rsync")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            print_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    print_success "Local prerequisites check passed"
}

# Setup Contabo VDS server
setup_contabo_server() {
    print_status "Setting up Contabo VDS server..."
    
    ssh "$CLOUD_USER@$CLOUD_HOST" << 'EOF'
        # Update system
        sudo apt-get update && sudo apt-get upgrade -y
        
        # Install essential packages
        sudo apt-get install -y \
            curl \
            wget \
            git \
            htop \
            vim \
            ufw \
            fail2ban \
            unzip \
            software-properties-common \
            apt-transport-https \
            ca-certificates \
            gnupg \
            lsb-release
        
        # Install Docker
        if ! command -v docker &> /dev/null; then
            echo "Installing Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
        fi
        
        # Install Docker Compose
        if ! command -v docker-compose &> /dev/null; then
            echo "Installing Docker Compose..."
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
        fi
        
        # Setup firewall
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw allow 8080/tcp  # Trading system
        sudo ufw allow 3001/tcp  # Grafana
        sudo ufw allow 9090/tcp  # Prometheus
        sudo ufw allow 8000/tcp  # AI Brain Vector DB
        sudo ufw --force enable
        
        # Create directories
        mkdir -p /home/marcin/overmind-protocol
        mkdir -p /home/marcin/backups/overmind
        mkdir -p /home/marcin/logs/overmind
        
        # Setup log rotation
        sudo tee /etc/logrotate.d/overmind > /dev/null << 'LOGROTATE'
/home/marcin/logs/overmind/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 marcin marcin
}
LOGROTATE

        echo "✅ Contabo VDS server setup completed"
EOF
    
    print_success "Contabo VDS server setup completed"
}

# Deploy THE OVERMIND PROTOCOL
deploy_overmind() {
    print_status "Deploying THE OVERMIND PROTOCOL to Contabo VDS..."
    
    # Sync project files
    print_status "Syncing project files..."
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='target' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        overmind-protocol/ "$CLOUD_USER@$CLOUD_HOST:$DEPLOY_DIR/"
    
    print_success "Project files synced to Contabo VDS"
    
    # Setup environment and build
    print_status "Setting up environment on Contabo VDS..."
    ssh "$CLOUD_USER@$CLOUD_HOST" << EOF
        cd $DEPLOY_DIR
        
        # Create production environment file
        cat > .env << 'ENVFILE'
# THE OVERMIND PROTOCOL - Contabo VDS Production Environment
SNIPER_TRADING_MODE=paper
OVERMIND_MODE=enabled
OVERMIND_AI_MODE=enabled

# Database passwords (generated for security)
SNIPER_DB_PASSWORD=overmind_db_\$(openssl rand -hex 16)
TENSORZERO_DB_PASSWORD=tensorzero_db_\$(openssl rand -hex 16)
REDIS_PASSWORD=redis_\$(openssl rand -hex 16)
GRAFANA_ADMIN_PASSWORD=overmind_admin_\$(date +%s)

# Solana Configuration (devnet for testing)
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

# Performance settings for Contabo VDS
RUST_LOG=info
TOKIO_WORKER_THREADS=6
OVERMIND_AI_CONFIDENCE_THRESHOLD=0.7
SNIPER_MAX_POSITION_SIZE=10000
SNIPER_MAX_DAILY_LOSS=1000
ENVFILE

        # Make scripts executable
        find scripts/ -name "*.sh" -exec chmod +x {} \;
        
        # Create logs directory
        mkdir -p logs
        
        echo "✅ Environment setup completed on Contabo VDS"
EOF
    
    print_success "Environment setup completed"
}

# Build Docker images
build_docker_images() {
    print_status "Building Docker images on Contabo VDS..."
    
    ssh "$CLOUD_USER@$CLOUD_HOST" << EOF
        cd $DEPLOY_DIR
        
        # Build images using production compose file
        if [[ -f "docker-compose.production.yml" ]]; then
            docker-compose -f docker-compose.production.yml build
        elif [[ -f "infrastructure/compose/docker-compose.overmind.yml" ]]; then
            docker-compose -f infrastructure/compose/docker-compose.overmind.yml build
        else
            echo "Using main docker-compose file..."
            docker-compose build
        fi
        
        echo "✅ Docker images built successfully"
EOF
    
    print_success "Docker images built on Contabo VDS"
}

# Start services
start_overmind_services() {
    print_status "Starting THE OVERMIND PROTOCOL services..."
    
    ssh "$CLOUD_USER@$CLOUD_HOST" << EOF
        cd $DEPLOY_DIR
        
        # Determine which compose file to use
        COMPOSE_FILE=""
        if [[ -f "docker-compose.production.yml" ]]; then
            COMPOSE_FILE="docker-compose.production.yml"
        elif [[ -f "infrastructure/compose/docker-compose.overmind.yml" ]]; then
            COMPOSE_FILE="infrastructure/compose/docker-compose.overmind.yml"
        else
            COMPOSE_FILE="docker-compose.yml"
        fi
        
        echo "Using compose file: \$COMPOSE_FILE"
        
        # Start infrastructure services first
        echo "Starting infrastructure services..."
        docker-compose -f "\$COMPOSE_FILE" up -d \
            overmind-dragonfly \
            overmind-chroma \
            overmind-postgres \
            tensorzero-clickhouse
        
        # Wait for databases to be ready
        echo "Waiting for databases to initialize..."
        sleep 30
        
        # Start AI and optimization services
        echo "Starting AI services..."
        docker-compose -f "\$COMPOSE_FILE" up -d \
            tensorzero-gateway \
            overmind-brain
        
        # Wait for AI services
        echo "Waiting for AI services to start..."
        sleep 20
        
        # Start trading system
        echo "Starting trading system..."
        docker-compose -f "\$COMPOSE_FILE" up -d \
            overmind-executor
        
        # Start monitoring
        echo "Starting monitoring services..."
        docker-compose -f "\$COMPOSE_FILE" up -d \
            prometheus \
            grafana \
            node-exporter
        
        echo "✅ All services started"
EOF
    
    print_success "THE OVERMIND PROTOCOL services started on Contabo VDS"
}

# Check service health
check_service_health() {
    print_status "Checking service health on Contabo VDS..."
    
    ssh "$CLOUD_USER@$CLOUD_HOST" << EOF
        cd $DEPLOY_DIR
        
        echo "=== Docker Container Status ==="
        docker-compose ps
        
        echo ""
        echo "=== Service Health Checks ==="
        
        # Wait a bit for services to fully start
        sleep 10
        
        # Check each service
        services=(
            "http://localhost:8080/health:Trading System"
            "http://localhost:8000/api/v1/heartbeat:Vector Database"
            "http://localhost:3000/health:TensorZero Gateway"
            "http://localhost:9090/-/healthy:Prometheus"
            "http://localhost:3001/api/health:Grafana"
        )
        
        for service in "\${services[@]}"; do
            IFS=':' read -r url name <<< "\$service"
            echo -n "Checking \$name... "
            
            if curl -f -s "\$url" > /dev/null 2>&1; then
                echo "✅ Healthy"
            else
                echo "⚠️  Not responding (may still be starting)"
            fi
        done
        
        echo ""
        echo "=== System Resources ==="
        echo "Memory usage:"
        free -h
        echo ""
        echo "Disk usage:"
        df -h
        echo ""
        echo "Docker system info:"
        docker system df
EOF
    
    print_success "Health check completed"
}

# Display access information
display_access_info() {
    echo ""
    echo -e "${PURPLE}🎯 THE OVERMIND PROTOCOL - Contabo VDS Deployment Complete${NC}"
    echo -e "${CYAN}================================================================${NC}"
    echo ""
    echo -e "${GREEN}🌐 Server:${NC}              $CLOUD_HOST"
    echo -e "${GREEN}🧠 Trading System:${NC}      http://$CLOUD_HOST:8080"
    echo -e "${GREEN}📊 Grafana:${NC}             http://$CLOUD_HOST:3001"
    echo -e "${GREEN}📈 Prometheus:${NC}          http://$CLOUD_HOST:9090"
    echo -e "${GREEN}🤖 AI Vector DB:${NC}        http://$CLOUD_HOST:8000"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo -e "${CYAN}  1. Set API keys in .env file:${NC}"
    echo -e "     ssh $CLOUD_USER@$CLOUD_HOST 'nano $DEPLOY_DIR/.env'"
    echo -e "${CYAN}  2. Restart services after setting API keys:${NC}"
    echo -e "     ssh $CLOUD_USER@$CLOUD_HOST 'cd $DEPLOY_DIR && docker-compose restart'"
    echo -e "${CYAN}  3. Monitor system for 48+ hours in paper trading mode${NC}"
    echo -e "${CYAN}  4. Review logs and performance metrics${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Management Commands:${NC}"
    echo -e "${CYAN}  SSH to server:${NC}         ssh $CLOUD_USER@$CLOUD_HOST"
    echo -e "${CYAN}  View logs:${NC}             ssh $CLOUD_USER@$CLOUD_HOST 'cd $DEPLOY_DIR && docker-compose logs -f'"
    echo -e "${CYAN}  Check status:${NC}          ssh $CLOUD_USER@$CLOUD_HOST 'cd $DEPLOY_DIR && docker-compose ps'"
    echo -e "${CYAN}  Restart system:${NC}        ssh $CLOUD_USER@$CLOUD_HOST 'cd $DEPLOY_DIR && docker-compose restart'"
    echo -e "${CYAN}  Stop system:${NC}           ssh $CLOUD_USER@$CLOUD_HOST 'cd $DEPLOY_DIR && docker-compose down'"
    echo ""
    echo -e "${PURPLE}🧠 THE OVERMIND PROTOCOL is now running on your Contabo VDS!${NC}"
    echo -e "${YELLOW}⚠️  Remember: System is in PAPER TRADING mode${NC}"
    echo ""
}

# Main deployment function
main() {
    print_status "🚀 Starting THE OVERMIND PROTOCOL deployment to Contabo VDS"
    
    test_ssh_connection
    check_local_prerequisites
    setup_contabo_server
    deploy_overmind
    build_docker_images
    start_overmind_services
    check_service_health
    display_access_info
    
    print_success "🎯 Contabo VDS deployment completed successfully!"
}

# Execute main function
main "$@"
