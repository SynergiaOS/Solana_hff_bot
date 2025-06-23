#!/bin/bash

# ============================================================================
# THE OVERMIND PROTOCOL - Production Deployment Script
# ============================================================================
# This script deploys THE OVERMIND PROTOCOL to production server
# Execute on server: marcin@89.117.53.53

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# PHASE 1: PRE-DEPLOYMENT CHECKS
# ============================================================================

log "🎯 THE OVERMIND PROTOCOL - Production Deployment Starting"
log "========================================================"

# Check if running as correct user
if [ "$USER" != "marcin" ]; then
    error "This script must be run as user 'marcin'"
    exit 1
fi

# Check if we're on the correct server
EXPECTED_IP="89.117.53.53"
CURRENT_IP=$(curl -s ifconfig.me || echo "unknown")
if [ "$CURRENT_IP" != "$EXPECTED_IP" ]; then
    warning "Current IP ($CURRENT_IP) doesn't match expected ($EXPECTED_IP)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Docker installation
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

success "Pre-deployment checks passed"

# ============================================================================
# PHASE 2: PROJECT SETUP
# ============================================================================

log "📁 Setting up project directory..."

# Create project directory if it doesn't exist
PROJECT_DIR="/opt/overmind"
if [ ! -d "$PROJECT_DIR" ]; then
    log "Creating project directory: $PROJECT_DIR"
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown marcin:marcin "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Clone or update repository
if [ ! -d ".git" ]; then
    log "Cloning THE OVERMIND PROTOCOL repository..."
    git clone https://github.com/SynergiaOS/Solana_hff_bot.git .
else
    log "Updating existing repository..."
    git fetch origin
    git reset --hard origin/main
    git pull origin main
fi

success "Project setup completed"

# ============================================================================
# PHASE 3: ENVIRONMENT CONFIGURATION
# ============================================================================

log "⚙️ Configuring environment..."

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        log "Copying .env.production to .env"
        cp .env.production .env
    else
        error ".env file not found. Please create .env with production configuration."
        log "You can use .env.production as a template."
        exit 1
    fi
fi

# Validate critical environment variables
log "Validating environment configuration..."

# Check if .env has placeholder values
if grep -q "your_.*_here" .env; then
    error "Found placeholder values in .env file. Please configure all required values:"
    grep "your_.*_here" .env
    exit 1
fi

# Check for required variables
REQUIRED_VARS=(
    "SNIPER_TRADING_MODE"
    "OPENAI_API_KEY"
    "HELIUS_API_KEY"
    "SOLANA_WALLET_PRIVATE_KEY"
    "SNIPER_DB_PASSWORD"
    "GRAFANA_ADMIN_PASSWORD"
)

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" .env; then
        error "Required environment variable $var not found in .env"
        exit 1
    fi
done

# Verify trading mode is set to paper for initial deployment
TRADING_MODE=$(grep "^SNIPER_TRADING_MODE=" .env | cut -d'=' -f2)
if [ "$TRADING_MODE" != "paper" ]; then
    error "SNIPER_TRADING_MODE must be set to 'paper' for initial deployment"
    exit 1
fi

success "Environment configuration validated"

# ============================================================================
# PHASE 4: INFRASTRUCTURE PREPARATION
# ============================================================================

log "🏗️ Preparing infrastructure..."

# Create necessary directories
mkdir -p logs
mkdir -p data/chroma
mkdir -p data/postgres
mkdir -p data/prometheus
mkdir -p data/grafana
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p wallets

# Set proper permissions
chmod 755 logs data
chmod 700 wallets

# Copy configuration files
if [ -f "infrastructure/compose/docker-compose.overmind.yml" ]; then
    cp infrastructure/compose/docker-compose.overmind.yml docker-compose.yml
    success "Docker Compose configuration copied"
else
    error "Docker Compose configuration not found"
    exit 1
fi

# Copy monitoring configurations
if [ -d "monitoring" ]; then
    log "Setting up monitoring configurations..."
    # Prometheus config
    if [ ! -f "monitoring/prometheus.yml" ]; then
        cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'overmind-trading'
    static_configs:
      - targets: ['overmind-trading:8080']
  
  - job_name: 'overmind-brain'
    static_configs:
      - targets: ['overmind-brain:8000']
  
  - job_name: 'tensorzero'
    static_configs:
      - targets: ['tensorzero-gateway:3000']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
EOF
    fi
fi

success "Infrastructure preparation completed"

# ============================================================================
# PHASE 5: DEPLOYMENT EXECUTION
# ============================================================================

log "🚀 Starting THE OVERMIND PROTOCOL deployment..."

# Stop any existing containers
log "Stopping existing containers..."
docker-compose down --remove-orphans || true

# Pull latest images
log "Pulling latest Docker images..."
docker-compose pull

# Build custom images
log "Building custom images..."
docker-compose build --no-cache

# Start the system
log "Starting THE OVERMIND PROTOCOL..."
docker-compose up -d

# Wait for services to start
log "Waiting for services to initialize..."
sleep 30

success "THE OVERMIND PROTOCOL deployment completed"

# ============================================================================
# PHASE 6: DEPLOYMENT VERIFICATION
# ============================================================================

log "🔍 Verifying deployment..."

# Check container status
log "Checking container status..."
docker-compose ps

# Check critical services
SERVICES=(
    "overmind-trading:8080"
    "overmind-grafana:3000"
    "overmind-prometheus:9090"
    "overmind-chroma:8000"
)

for service in "${SERVICES[@]}"; do
    container=$(echo $service | cut -d':' -f1)
    port=$(echo $service | cut -d':' -f2)
    
    if docker-compose ps | grep -q "$container.*Up"; then
        success "✅ $container is running"
    else
        error "❌ $container is not running"
    fi
done

# Health checks
log "Performing health checks..."

# Wait a bit more for services to be ready
sleep 60

# Check if trading system is responding
if curl -f -s http://localhost:8080/health > /dev/null; then
    success "✅ Trading system health check passed"
else
    warning "⚠️ Trading system health check failed - checking logs..."
    docker-compose logs --tail=20 overmind-trading
fi

# Check if Grafana is accessible
if curl -f -s http://localhost:3001 > /dev/null; then
    success "✅ Grafana is accessible"
else
    warning "⚠️ Grafana is not accessible"
fi

success "Deployment verification completed"

# ============================================================================
# PHASE 7: POST-DEPLOYMENT INSTRUCTIONS
# ============================================================================

log "📋 Post-deployment instructions:"
echo
echo "🎯 THE OVERMIND PROTOCOL has been deployed successfully!"
echo
echo "📊 Access Points:"
echo "  • Trading System API: http://89.117.53.53:8080"
echo "  • Grafana Dashboard: http://89.117.53.53:3001"
echo "  • Prometheus Metrics: http://89.117.53.53:9090"
echo "  • Chroma Vector DB: http://89.117.53.53:8000"
echo
echo "🔐 Default Credentials:"
echo "  • Grafana: admin / [check .env GRAFANA_ADMIN_PASSWORD]"
echo
echo "📈 Next Steps:"
echo "  1. Open Grafana dashboard and verify metrics are flowing"
echo "  2. Monitor logs for the first 30 minutes:"
echo "     docker-compose logs -f overmind-trading"
echo "  3. Check trading system status:"
echo "     curl http://localhost:8080/health"
echo "  4. Begin 48-hour paper trading validation"
echo
echo "🚨 CRITICAL: System is in PAPER TRADING mode"
echo "   Monitor for 48 hours before considering live trading"
echo
echo "📝 Monitoring Commands:"
echo "  • View all logs: docker-compose logs -f"
echo "  • Check status: docker-compose ps"
echo "  • Restart system: docker-compose restart"
echo "  • Stop system: docker-compose down"
echo
success "🎯 THE OVERMIND PROTOCOL deployment completed successfully!"
echo "⭐ 48-hour validation period begins now..."
