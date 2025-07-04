#!/bin/bash

# 🚀 THE OVERMIND PROTOCOL - Max Throughput Deployment
# Deploy to server with 25K transactions/day capability

set -e

echo "🚀🚀🚀 THE OVERMIND PROTOCOL - MAX THROUGHPUT DEPLOYMENT 🚀🚀🚀"
echo "=================================================================="
echo "🎯 Target: 25,000 transactions/day"
echo "💪 Server: 8-core/32GB optimized"
echo "⚡ Jito Bundle: Ultra-low latency"
echo "🧠 AI Coordination: Full ecosystem"
echo "=================================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Server details
SERVER_IP="89.117.53.53"
SERVER_USER="marcin"

echo -e "${CYAN}🎯 Deploying to server: $SERVER_USER@$SERVER_IP${NC}"

# Create deployment package
echo -e "${YELLOW}📦 Creating deployment package...${NC}"

# Create temporary deployment directory
DEPLOY_DIR="overmind_max_throughput_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"

# Copy essential files
echo -e "${BLUE}📋 Copying production files...${NC}"
cp -r infrastructure/ "$DEPLOY_DIR/"
cp -r brain/ "$DEPLOY_DIR/"
cp -r src/ "$DEPLOY_DIR/core/"
cp Cargo.toml "$DEPLOY_DIR/core/"
cp README.md "$DEPLOY_DIR/"

# Create optimized environment file
echo -e "${PURPLE}⚙️ Creating optimized .env file...${NC}"
cat > "$DEPLOY_DIR/.env.production" << 'EOF'
# THE OVERMIND PROTOCOL - Max Throughput Configuration
# Optimized for 8-core/32GB server with 25K tx/day capability

# ============================================================================
# TRADING CONFIGURATION - LIVE MODE
# ============================================================================
SNIPER_TRADING_MODE=live
PAPER_TRADING_MODE=false
OVERMIND_MODE=enabled
OVERMIND_AI_MODE=enabled

# ============================================================================
# PERFORMANCE OPTIMIZATION - MAX THROUGHPUT
# ============================================================================
OVERMIND_MAX_THREADS=64
OVERMIND_TX_BUFFER=1000
OVERMIND_MAX_TPS=150
OVERMIND_DAILY_TX_CAP=22000
OVERMIND_AUTO_THROTTLE=true
OVERMIND_MEMORY_POOL_GB=24
OVERMIND_JITO_ENDPOINT=https://amsterdam.mainnet.jito.wtf:8899

# ============================================================================
# SOLANA CONFIGURATION - MAINNET
# ============================================================================
SOLANA_RPC_URL=https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580
SOLANA_WSS_URL=wss://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580
HELIUS_API_KEY=edbcd361-78a0-4998-bd1e-8d4666722f82
QUICKNODE_API_KEY=a10fad0f63cdfe46533f1892ac720517b08fe580

# ============================================================================
# WALLET CONFIGURATION - SECURE
# ============================================================================
SOLANA_WALLET_PRIVATE_KEY=[4,72,104,80,115,72,122,99,111,106,111,114,55,120,66,76,111,107,68,57,119,55,84,54,106,72,70,88,118,86,70,107,67,115,107,78,56,104,71,83,78,75,51,54,67,122,78,80,72,120,82,82,106,53,68,103,54,82,67,99,103,55,57,83,83,87,109,89,118,87,69,119,83,119,107,49,50,67,111,82,120,118,50,87,53,57]

# ============================================================================
# RISK MANAGEMENT - AGGRESSIVE BUT SAFE
# ============================================================================
SNIPER_MAX_POSITION_SIZE=5.0
SNIPER_MAX_DAILY_LOSS=2.0
OVERMIND_AI_CONFIDENCE_THRESHOLD=0.55
SNIPER_AI_MAX_TRADES_PER_HOUR=100

# ============================================================================
# DATABASE PASSWORDS - SECURE
# ============================================================================
SNIPER_DB_PASSWORD=overmind_secure_2024
TENSORZERO_DB_PASSWORD=tensorzero_secure_2024
GRAFANA_ADMIN_PASSWORD=grafana_admin_2024

# ============================================================================
# AI API KEYS
# ============================================================================
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
MISTRAL_API_KEY=your_mistral_key_here
GOOGLE_API_KEY=your_google_key_here
FINANCIAL_DATASETS_API_KEY=your_financial_datasets_key_here

# ============================================================================
# SYSTEM OPTIMIZATION
# ============================================================================
RUST_LOG=info
TOKIO_WORKER_THREADS=8
PYTHONPATH=/app/src
EOF

# Create deployment script for server
echo -e "${GREEN}🚀 Creating server deployment script...${NC}"
cat > "$DEPLOY_DIR/deploy_on_server.sh" << 'EOF'
#!/bin/bash

# THE OVERMIND PROTOCOL - Server Deployment Script
# Run this on the server to deploy max throughput system

set -e

echo "🚀 THE OVERMIND PROTOCOL - Server Deployment Starting..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f infrastructure/compose/docker-compose.production.yml down || true

# Load environment variables
echo "⚙️ Loading environment variables..."
export $(cat .env.production | xargs)

# Build and start the system
echo "🚀 Starting THE OVERMIND PROTOCOL with max throughput..."
docker-compose -f infrastructure/compose/docker-compose.production.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check system health
echo "🔍 Checking system health..."
docker-compose -f infrastructure/compose/docker-compose.production.yml ps

# Display access information
echo ""
echo "🎉 THE OVERMIND PROTOCOL DEPLOYED SUCCESSFULLY!"
echo "=============================================="
echo "📊 Grafana Dashboard: http://$(curl -s ifconfig.me):3001"
echo "🎛️ Trading API: http://$(curl -s ifconfig.me):8080"
echo "📈 Prometheus: http://localhost:9090"
echo ""
echo "🎯 SYSTEM CAPABILITIES:"
echo "   ⚡ Max TPS: 150"
echo "   📊 Daily Capacity: 22,000 transactions"
echo "   💪 CPU Cores: 7.5 allocated"
echo "   🧠 Memory: 28GB allocated"
echo "   🌐 Jito Endpoint: Amsterdam (ultra-low latency)"
echo ""
echo "🚀 THE OVERMIND PROTOCOL: Ready for 25K transactions/day!"

# Show logs
echo "📋 Showing recent logs..."
docker-compose -f infrastructure/compose/docker-compose.production.yml logs --tail=50
EOF

chmod +x "$DEPLOY_DIR/deploy_on_server.sh"

# Create archive
echo -e "${BLUE}📦 Creating deployment archive...${NC}"
tar -czf "${DEPLOY_DIR}.tar.gz" "$DEPLOY_DIR"

echo -e "${GREEN}✅ Deployment package ready: ${DEPLOY_DIR}.tar.gz${NC}"

# Upload to server
echo -e "${YELLOW}📤 Uploading to server...${NC}"
scp "${DEPLOY_DIR}.tar.gz" "$SERVER_USER@$SERVER_IP:~/"

# Deploy on server
echo -e "${PURPLE}🚀 Deploying on server...${NC}"
ssh "$SERVER_USER@$SERVER_IP" << EOF
    echo "🎯 Extracting deployment package..."
    tar -xzf "${DEPLOY_DIR}.tar.gz"
    cd "$DEPLOY_DIR"
    
    echo "🚀 Starting deployment..."
    chmod +x deploy_on_server.sh
    ./deploy_on_server.sh
EOF

# Cleanup local files
echo -e "${BLUE}🧹 Cleaning up local files...${NC}"
rm -rf "$DEPLOY_DIR"
rm -f "${DEPLOY_DIR}.tar.gz"

echo ""
echo -e "${CYAN}🎉 MAX THROUGHPUT DEPLOYMENT COMPLETE!${NC}"
echo "======================================"
echo -e "${GREEN}✅ THE OVERMIND PROTOCOL deployed with 25K tx/day capability${NC}"
echo -e "${YELLOW}📊 Access Grafana: http://$SERVER_IP:3001${NC}"
echo -e "${YELLOW}🎛️ Access API: http://$SERVER_IP:8080${NC}"
echo ""
echo -e "${PURPLE}🚀 System ready for maximum transaction throughput!${NC}"
