#!/bin/bash

# THE OVERMIND PROTOCOL - Interactive Deployment
# Step-by-step deployment with user confirmation

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
SERVER="marcin@89.117.53.53"
DEPLOY_DIR="/home/marcin/overmind-protocol"

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

confirm_step() {
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to abort...${NC}"
    read
}

echo -e "${PURPLE}"
cat << "EOF"
 _____ _   _ _____    _____  _   _ _____ ____  __  __ _____ _   _ ____  
|_   _| | | | ____|  / _ \ \| | | | ____|  _ \|  \/  |_   _| \ | |  _ \ 
  | | | |_| |  _|   | | | | | | | |  _| | |_) | |\/| | | | |  \| | | | |
  | | |  _  | |___  | |_| | |_| | | |___|  _ <| |  | | | | | |\  | |_| |
  |_| |_| |_|_____|  \___/ \___/|_|_____|_| \_\_|  |_| |_| |_| \_|____/ 

🚀 INTERACTIVE DEPLOYMENT TO CONTABO VDS
EOF
echo -e "${NC}"

echo "This script will deploy THE OVERMIND PROTOCOL to your Contabo VDS step by step."
echo "Server: $SERVER"
echo ""

# Step 1: Check local files
print_step "1. Checking local project structure..."
if [[ ! -d "overmind-protocol" ]]; then
    print_error "overmind-protocol directory not found!"
    echo "Please run ./reorganize-project.sh first"
    exit 1
fi

if [[ ! -f "overmind-protocol/.env" ]]; then
    print_error ".env file not found in overmind-protocol/"
    echo "Please ensure overmind-protocol/.env exists with your API keys"
    exit 1
fi

print_success "Local project structure OK"
confirm_step

# Step 2: Test SSH connection
print_step "2. Testing SSH connection..."
echo "You will be prompted for your SSH password..."
if ssh -o ConnectTimeout=10 "$SERVER" "echo 'SSH connection successful'"; then
    print_success "SSH connection working"
else
    print_error "SSH connection failed"
    exit 1
fi
confirm_step

# Step 3: Sync files to server
print_step "3. Syncing project files to server..."
echo "This will copy all project files to $SERVER:$DEPLOY_DIR"
echo "You may be prompted for your SSH password multiple times..."
confirm_step

rsync -avz --progress \
    --exclude='.git' \
    --exclude='target' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    overmind-protocol/ "$SERVER:$DEPLOY_DIR/"

print_success "Files synced to server"
confirm_step

# Step 4: Setup server environment
print_step "4. Setting up server environment..."
echo "This will install Docker and configure the server..."
confirm_step

ssh "$SERVER" << 'EOF'
    echo "🔧 Setting up Contabo VDS environment..."
    
    # Update system
    sudo apt-get update -y
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        echo "✅ Docker installed"
    else
        echo "✅ Docker already installed"
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo "✅ Docker Compose installed"
    else
        echo "✅ Docker Compose already installed"
    fi
    
    # Setup firewall
    echo "Configuring firewall..."
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 8080/tcp  # Trading system
    sudo ufw allow 3001/tcp  # Grafana
    sudo ufw allow 9090/tcp  # Prometheus
    sudo ufw allow 8000/tcp  # AI Brain
    sudo ufw --force enable
    
    echo "✅ Server environment setup completed"
EOF

print_success "Server environment configured"
confirm_step

# Step 5: Build Docker images
print_step "5. Building Docker images on server..."
echo "This may take several minutes..."
confirm_step

ssh "$SERVER" << EOF
    cd $DEPLOY_DIR
    
    echo "🐳 Building Docker images..."
    
    # Find the right compose file
    COMPOSE_FILE=""
    if [[ -f "infrastructure/compose/docker-compose.production.yml" ]]; then
        COMPOSE_FILE="infrastructure/compose/docker-compose.production.yml"
    elif [[ -f "infrastructure/compose/docker-compose.overmind.yml" ]]; then
        COMPOSE_FILE="infrastructure/compose/docker-compose.overmind.yml"
    elif [[ -f "docker-compose.overmind.yml" ]]; then
        COMPOSE_FILE="docker-compose.overmind.yml"
    else
        echo "❌ No suitable docker-compose file found"
        exit 1
    fi
    
    echo "Using compose file: \$COMPOSE_FILE"
    
    # Build images
    docker-compose -f "\$COMPOSE_FILE" build
    
    echo "✅ Docker images built successfully"
EOF

print_success "Docker images built"
confirm_step

# Step 6: Start services
print_step "6. Starting THE OVERMIND PROTOCOL services..."
echo "This will start all services in the correct order..."
confirm_step

ssh "$SERVER" << EOF
    cd $DEPLOY_DIR
    
    echo "🚀 Starting THE OVERMIND PROTOCOL services..."
    
    # Find compose file
    COMPOSE_FILE=""
    if [[ -f "infrastructure/compose/docker-compose.production.yml" ]]; then
        COMPOSE_FILE="infrastructure/compose/docker-compose.production.yml"
    elif [[ -f "infrastructure/compose/docker-compose.overmind.yml" ]]; then
        COMPOSE_FILE="infrastructure/compose/docker-compose.overmind.yml"
    elif [[ -f "docker-compose.overmind.yml" ]]; then
        COMPOSE_FILE="docker-compose.overmind.yml"
    fi
    
    echo "Using compose file: \$COMPOSE_FILE"
    
    # Start infrastructure first
    echo "Starting infrastructure services..."
    docker-compose -f "\$COMPOSE_FILE" up -d overmind-dragonfly overmind-chroma overmind-postgres tensorzero-clickhouse 2>/dev/null || \
    docker-compose -f "\$COMPOSE_FILE" up -d tensorzero-db tensorzero-dragonfly overmind-db overmind-dragonfly chroma
    
    echo "Waiting for databases to initialize..."
    sleep 30
    
    # Start AI services
    echo "Starting AI services..."
    docker-compose -f "\$COMPOSE_FILE" up -d tensorzero-gateway overmind-brain 2>/dev/null || \
    docker-compose -f "\$COMPOSE_FILE" up -d tensorzero-gateway overmind-trading
    
    echo "Waiting for AI services..."
    sleep 20
    
    # Start monitoring
    echo "Starting monitoring services..."
    docker-compose -f "\$COMPOSE_FILE" up -d prometheus grafana node-exporter 2>/dev/null || \
    docker-compose -f "\$COMPOSE_FILE" up -d prometheus grafana
    
    echo "✅ All services started"
    
    # Show status
    echo ""
    echo "📊 Container Status:"
    docker-compose -f "\$COMPOSE_FILE" ps
EOF

print_success "Services started"
confirm_step

# Step 7: Health check
print_step "7. Performing health checks..."
echo "Testing all service endpoints..."

ssh "$SERVER" << 'EOF'
    echo "🔍 Health Check Results:"
    echo "========================"
    
    # Wait a bit for services to fully start
    sleep 10
    
    # Test endpoints
    echo -n "Trading System (8080): "
    if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "⚠️  Not responding"
    fi
    
    echo -n "AI Vector DB (8000): "
    if curl -f -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "⚠️  Not responding"
    fi
    
    echo -n "TensorZero (3000): "
    if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "⚠️  Not responding"
    fi
    
    echo -n "Prometheus (9090): "
    if curl -f -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "⚠️  Not responding"
    fi
    
    echo -n "Grafana (3001): "
    if curl -f -s http://localhost:3001/api/health > /dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "⚠️  Not responding"
    fi
    
    echo ""
    echo "📈 System Resources:"
    echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
    echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
EOF

print_success "Health check completed"

# Final summary
echo ""
echo -e "${PURPLE}🎯 THE OVERMIND PROTOCOL DEPLOYMENT COMPLETED!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo -e "${GREEN}🌐 Access URLs:${NC}"
echo "  Trading System:    http://89.117.53.53:8080"
echo "  Grafana Dashboard: http://89.117.53.53:3001"
echo "  Prometheus:        http://89.117.53.53:9090"
echo "  AI Vector DB:      http://89.117.53.53:8000"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Open http://89.117.53.53:8080 to check trading system"
echo "2. Open http://89.117.53.53:3001 for Grafana monitoring"
echo "3. Monitor system for 48+ hours in paper trading mode"
echo "4. Check logs: ssh $SERVER 'cd $DEPLOY_DIR && docker-compose logs -f'"
echo ""
echo -e "${YELLOW}🔧 Management Commands:${NC}"
echo "  View status: ssh $SERVER 'cd $DEPLOY_DIR && docker-compose ps'"
echo "  View logs:   ssh $SERVER 'cd $DEPLOY_DIR && docker-compose logs -f'"
echo "  Restart:     ssh $SERVER 'cd $DEPLOY_DIR && docker-compose restart'"
echo "  Stop:        ssh $SERVER 'cd $DEPLOY_DIR && docker-compose down'"
echo ""
echo -e "${GREEN}🧠 THE OVERMIND PROTOCOL is now running on your Contabo VDS!${NC}"
echo -e "${YELLOW}⚠️  System is in PAPER TRADING mode - monitor before going live${NC}"
