#!/bin/bash

# THE OVERMIND PROTOCOL - Step-by-Step Deployment Guide
# Copy and paste commands to deploy on Contabo VDS

echo "🚀 THE OVERMIND PROTOCOL - Step-by-Step Deployment"
echo "=================================================="
echo ""
echo "This guide provides commands to copy and paste on your Contabo VDS server."
echo "Server: marcin@89.117.53.53"
echo ""
echo "STEP 1: Connect to your server:"
echo "ssh marcin@89.117.53.53"
echo ""
echo "STEP 2: Copy and paste the following commands one by one:"
echo ""

cat << 'EOF'
# ============================================================================
# THE OVERMIND PROTOCOL - Server Setup Commands
# ============================================================================

echo "🧠 THE OVERMIND PROTOCOL - Server Setup Starting..."
echo "Server: $(hostname) | User: $(whoami) | Date: $(date)"
echo ""

# ============================================================================
# STEP 1: Update system and install dependencies
# ============================================================================
echo "📦 Step 1: Installing system dependencies..."

sudo apt-get update -y
sudo apt-get install -y \
    curl \
    wget \
    git \
    htop \
    vim \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

echo "✅ System dependencies installed"

# ============================================================================
# STEP 2: Install Docker
# ============================================================================
echo "🐳 Step 2: Installing Docker..."

if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# ============================================================================
# STEP 3: Setup firewall
# ============================================================================
echo "🔥 Step 3: Configuring firewall..."

sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080/tcp  # Trading system
sudo ufw allow 3001/tcp  # Grafana
sudo ufw allow 9090/tcp  # Prometheus
sudo ufw allow 8000/tcp  # AI Brain Vector DB
sudo ufw allow 3000/tcp  # TensorZero
sudo ufw --force enable

echo "✅ Firewall configured"

# ============================================================================
# STEP 4: Create project directories
# ============================================================================
echo "📁 Step 4: Creating project directories..."

mkdir -p /home/marcin/overmind-protocol
mkdir -p /home/marcin/backups/overmind
mkdir -p /home/marcin/logs/overmind

echo "✅ Directories created:"
ls -la /home/marcin/

# ============================================================================
# STEP 5: Verify installation
# ============================================================================
echo "🔍 Step 5: Verifying installation..."

echo "Python3: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "pip3: $(pip3 --version 2>/dev/null || echo 'Not found')"
echo "Docker: $(docker --version 2>/dev/null || echo 'Not found')"
echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'Not found')"

echo ""
echo "🔧 Testing Docker..."
if command -v docker &> /dev/null; then
    sudo systemctl start docker
    sudo systemctl enable docker
    echo "✅ Docker service started"
else
    echo "❌ Docker not available"
fi

echo ""
echo "============================================================================"
echo "✅ SERVER SETUP COMPLETED!"
echo "============================================================================"
echo ""
echo "Your Contabo VDS is now ready for THE OVERMIND PROTOCOL."
echo ""
echo "Next: Logout and login again to refresh Docker group membership:"
echo "exit"
echo ""

# ============================================================================
# STEP 6: After logout/login - File Transfer Instructions
# ============================================================================
echo "After you logout and login again, run these commands:"
echo ""
echo "# Test Docker (should work without sudo after re-login)"
echo "docker run --rm hello-world"
echo ""
echo "# Create environment file"
echo "cat > /home/marcin/overmind-protocol/.env << 'ENVFILE'"
echo "# THE OVERMIND PROTOCOL - Production Environment"
echo "SNIPER_TRADING_MODE=paper"
echo "OVERMIND_MODE=enabled"
echo "OVERMIND_AI_MODE=enabled"
echo "OVERMIND_AI_CONFIDENCE_THRESHOLD=0.7"
echo ""
echo "# API Keys"
echo "OPENAI_API_KEY=your-openai-api-key-here"
echo "GROQ_API_KEY="
echo "MISTRAL_API_KEY="
echo ""
echo "# Solana Configuration (devnet for testing)"
echo "SOLANA_DEVNET_RPC_URL=https://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
echo "SOLANA_DEVNET_WSS_URL=wss://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
echo ""
echo "# Database passwords (auto-generated)"
echo "SNIPER_DB_PASSWORD=overmind_db_\$(openssl rand -hex 16)"
echo "TENSORZERO_DB_PASSWORD=tensorzero_db_\$(openssl rand -hex 16)"
echo "REDIS_PASSWORD=redis_\$(openssl rand -hex 16)"
echo "GRAFANA_ADMIN_PASSWORD=overmind_admin_\$(date +%s)"
echo ""
echo "# Performance settings"
echo "RUST_LOG=info"
echo "TOKIO_WORKER_THREADS=6"
echo "PYTHONPATH=/app/src"
echo "ENVFILE"
echo ""
echo "echo '✅ Environment file created'"
echo ""

EOF

echo ""
echo "============================================================================"
echo "AFTER SERVER SETUP - FILE TRANSFER"
echo "============================================================================"
echo ""
echo "From your LOCAL machine, run this command to transfer files:"
echo ""
echo "rsync -avz --progress \\"
echo "    --exclude='.git' \\"
echo "    --exclude='target' \\"
echo "    --exclude='node_modules' \\"
echo "    --exclude='__pycache__' \\"
echo "    overmind-protocol/ marcin@89.117.53.53:/home/marcin/overmind-protocol/"
echo ""
echo "============================================================================"
echo "DOCKER DEPLOYMENT COMMANDS"
echo "============================================================================"
echo ""
echo "After file transfer, run these commands ON THE SERVER:"
echo ""

cat << 'EOF'
# ============================================================================
# THE OVERMIND PROTOCOL - Docker Deployment
# ============================================================================

cd /home/marcin/overmind-protocol

echo "🐳 Starting THE OVERMIND PROTOCOL Docker deployment..."

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
    echo "Available files:"
    find . -name "docker-compose*.yml" -type f
    exit 1
fi

echo "✅ Using compose file: $COMPOSE_FILE"

# ============================================================================
# STEP 1: Build Docker images
# ============================================================================
echo "🔨 Step 1: Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build

echo "✅ Docker images built"

# ============================================================================
# STEP 2: Start infrastructure services
# ============================================================================
echo "🏗️  Step 2: Starting infrastructure services..."

# Start databases and message brokers first
docker-compose -f "$COMPOSE_FILE" up -d \
    overmind-dragonfly \
    overmind-chroma \
    overmind-postgres \
    tensorzero-clickhouse 2>/dev/null || \
docker-compose -f "$COMPOSE_FILE" up -d \
    tensorzero-db \
    tensorzero-dragonfly \
    overmind-db \
    overmind-dragonfly \
    chroma

echo "⏳ Waiting for databases to initialize (30 seconds)..."
sleep 30

echo "✅ Infrastructure services started"

# ============================================================================
# STEP 3: Start AI services
# ============================================================================
echo "🧠 Step 3: Starting AI services..."

docker-compose -f "$COMPOSE_FILE" up -d \
    tensorzero-gateway \
    overmind-brain 2>/dev/null || \
docker-compose -f "$COMPOSE_FILE" up -d \
    tensorzero-gateway

echo "⏳ Waiting for AI services to start (20 seconds)..."
sleep 20

echo "✅ AI services started"

# ============================================================================
# STEP 4: Start trading system
# ============================================================================
echo "💰 Step 4: Starting trading system..."

docker-compose -f "$COMPOSE_FILE" up -d \
    overmind-executor 2>/dev/null || \
docker-compose -f "$COMPOSE_FILE" up -d \
    overmind-trading

echo "✅ Trading system started"

# ============================================================================
# STEP 5: Start monitoring
# ============================================================================
echo "📊 Step 5: Starting monitoring services..."

docker-compose -f "$COMPOSE_FILE" up -d \
    prometheus \
    grafana \
    node-exporter 2>/dev/null || \
docker-compose -f "$COMPOSE_FILE" up -d \
    prometheus \
    grafana

echo "✅ Monitoring services started"

# ============================================================================
# STEP 6: Check deployment status
# ============================================================================
echo "🔍 Step 6: Checking deployment status..."

echo ""
echo "📊 Container Status:"
docker-compose -f "$COMPOSE_FILE" ps

echo ""
echo "🔍 Health Check Results:"
echo "========================"

# Wait for services to fully start
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

echo ""
echo "============================================================================"
echo "🎯 THE OVERMIND PROTOCOL DEPLOYMENT COMPLETED!"
echo "============================================================================"
echo ""
echo "🌐 Access URLs:"
echo "  Trading System:    http://89.117.53.53:8080"
echo "  Grafana Dashboard: http://89.117.53.53:3001"
echo "  Prometheus:        http://89.117.53.53:9090"
echo "  AI Vector DB:      http://89.117.53.53:8000"
echo ""
echo "📋 Management Commands:"
echo "  View status: docker-compose -f \"$COMPOSE_FILE\" ps"
echo "  View logs:   docker-compose -f \"$COMPOSE_FILE\" logs -f"
echo "  Restart:     docker-compose -f \"$COMPOSE_FILE\" restart"
echo "  Stop:        docker-compose -f \"$COMPOSE_FILE\" down"
echo ""
echo "🧠 THE OVERMIND PROTOCOL is now running on your Contabo VDS!"
echo "⚠️  System is in PAPER TRADING mode - monitor before going live"
echo ""

EOF
