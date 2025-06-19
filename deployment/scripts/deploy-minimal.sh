#!/bin/bash

# THE OVERMIND PROTOCOL - Minimal Deployment
# Uses existing infrastructure (Dragonfly, PostgreSQL)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
ENV_FILE=".env"

check_existing_services() {
    log_info "Checking existing infrastructure..."
    
    # Check Dragonfly
    if redis-cli -h localhost -p 6380 ping > /dev/null 2>&1; then
        log_success "✅ Dragonfly: Running on port 6380"
    else
        log_error "❌ Dragonfly: Not accessible on port 6380"
        return 1
    fi
    
    # Check PostgreSQL
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        log_success "✅ PostgreSQL: Running on port 5432"
    else
        log_error "❌ PostgreSQL: Not accessible on port 5432"
        return 1
    fi
    
    log_success "Existing infrastructure verified"
}

deploy_tensorzero_only() {
    log_info "Deploying TensorZero Gateway..."
    
    # Create minimal docker-compose for TensorZero only
    cat > docker-compose.minimal.yml << 'EOF'
version: '3.8'

services:
  # TensorZero Gateway - AI Decision Engine
  tensorzero-gateway:
    image: tensorzero/gateway:latest
    container_name: overmind-tensorzero
    ports:
      - "3000:3000"
    environment:
      - TENSORZERO_DATABASE_URL=postgresql://postgres:password@host.docker.internal:5432/tensorzero
      - TENSORZERO_REDIS_URL=redis://host.docker.internal:6380
      - TENSORZERO_LOG_LEVEL=info
      - TENSORZERO_OPENAI_API_KEY=${OPENAI_API_KEY}
      - TENSORZERO_MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - TENSORZERO_GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./tensorzero-config:/app/config
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    extra_hosts:
      - "host.docker.internal:host-gateway"

  # Prometheus - Metrics Collection
  prometheus:
    image: prom/prometheus:latest
    container_name: overmind-prometheus
    ports:
      - "9092:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  # Grafana - Visualization
  grafana:
    image: grafana/grafana:latest
    container_name: overmind-grafana
    ports:
      - "3002:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
EOF
    
    # Source environment
    source "$ENV_FILE"
    
    # Deploy TensorZero and monitoring
    docker-compose -f docker-compose.minimal.yml up -d
    
    log_success "TensorZero and monitoring deployed"
}

setup_database() {
    log_info "Setting up database schemas..."
    
    # Create TensorZero database if it doesn't exist
    PGPASSWORD=password createdb -h localhost -U postgres tensorzero 2>/dev/null || {
        log_info "TensorZero database already exists or using different credentials"
    }
    
    # Create SNIPERCOR database if it doesn't exist
    PGPASSWORD=password createdb -h localhost -U postgres snipercor 2>/dev/null || {
        log_info "SNIPERCOR database already exists or using different credentials"
    }
    
    log_success "Database setup completed"
}

build_and_start_trading_system() {
    log_info "Building and starting THE OVERMIND PROTOCOL trading system..."
    
    # Source environment
    source "$ENV_FILE"
    export RUST_LOG=info
    export RUST_BACKTRACE=1
    
    # Update database URL to use existing PostgreSQL
    export SNIPER_DATABASE_URL="postgresql://postgres:password@localhost:5432/snipercor"
    
    # Create logs directory
    mkdir -p logs
    
    # Build the system
    log_info "Building trading system..."
    if cargo build --profile contabo; then
        log_success "Trading system built successfully"
    else
        log_error "Failed to build trading system"
        return 1
    fi
    
    # Start the trading system
    log_info "Starting trading system..."
    nohup ./target/contabo/snipercor > logs/overmind.log 2>&1 &
    
    # Save PID
    echo $! > overmind.pid
    
    log_success "Trading system started (PID: $(cat overmind.pid))"
}

test_services() {
    log_info "Testing deployed services..."
    
    # Wait for services to start
    sleep 15
    
    # Test TensorZero
    if curl -f -s "http://localhost:3000/health" > /dev/null 2>&1; then
        log_success "✅ TensorZero Gateway: Running"
    else
        log_warning "⚠️ TensorZero Gateway: Not responding"
    fi
    
    # Test Trading System
    if curl -f -s "http://localhost:8080/health" > /dev/null 2>&1; then
        log_success "✅ Trading System: Running"
    else
        log_warning "⚠️ Trading System: Not responding"
        log_info "Check logs: tail -f logs/overmind.log"
    fi
    
    # Test Prometheus
    if curl -f -s "http://localhost:9092/-/healthy" > /dev/null 2>&1; then
        log_success "✅ Prometheus: Running"
    else
        log_warning "⚠️ Prometheus: Not responding"
    fi

    # Test Grafana
    if curl -f -s "http://localhost:3002/api/health" > /dev/null 2>&1; then
        log_success "✅ Grafana: Running"
    else
        log_warning "⚠️ Grafana: Not responding"
    fi
    
    log_success "Service tests completed"
}

test_ai_integration() {
    log_info "Testing AI integration..."
    
    # Test TensorZero AI inference
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"function_name":"overmind_trading_decision","input":{"market_data":"{\"test\":true}"}}' \
        "http://localhost:3000/inference" 2>/dev/null)
    
    if echo "$response" | grep -q "inference_id" 2>/dev/null; then
        log_success "✅ AI Integration: Working"
    else
        log_warning "⚠️ AI Integration: Failed or not ready yet"
        log_info "Response: $response"
    fi
}

show_status() {
    local grafana_pass=$(grep "GRAFANA_ADMIN_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2)
    local wallet_address=$(solana-keygen pubkey test-wallet.json 2>/dev/null || echo "Unknown")
    
    log_success "🧠 THE OVERMIND PROTOCOL - Deployment Complete!"
    echo ""
    
    log_info "📊 System Status:"
    echo "  🧠 Trading System:    http://localhost:8080"
    echo "  🤖 TensorZero:       http://localhost:3000"
    echo "  📊 Grafana:          http://localhost:3002"
    echo "  📈 Prometheus:       http://localhost:9092"
    echo ""
    
    log_info "🔐 Access Information:"
    echo "  📊 Grafana Login:    admin / $grafana_pass"
    echo "  🔑 Test Wallet:      $wallet_address"
    echo ""
    
    log_info "📋 Monitoring Commands:"
    echo "  📄 Trading logs:     tail -f logs/overmind.log"
    echo "  📊 System metrics:   curl http://localhost:8080/metrics"
    echo "  🔧 Stop trading:     kill \$(cat overmind.pid)"
    echo "  🛑 Stop services:    docker-compose -f docker-compose.minimal.yml down"
    echo ""
    
    log_info "🧪 Testing Commands:"
    echo "  🔬 Integration test:  cargo test --test real_api_integration_tests --ignored"
    echo "  🧠 OVERMIND tests:    cargo test --test overmind_integration_tests"
    echo ""
    
    log_warning "⚠️ IMPORTANT:"
    echo "  • System is in PAPER TRADING mode"
    echo "  • Using existing Dragonfly and PostgreSQL"
    echo "  • Monitor for 48+ hours before live trading"
    echo "  • Emergency stop: kill \$(cat overmind.pid)"
    echo ""
    
    log_success "THE OVERMIND PROTOCOL is running! 🚀"
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    
    # Stop trading system if running
    if [[ -f "overmind.pid" ]]; then
        kill "$(cat overmind.pid)" 2>/dev/null || true
        rm -f overmind.pid
    fi
    
    # Stop Docker services
    docker-compose -f docker-compose.minimal.yml down 2>/dev/null || true
    
    exit 1
}

main() {
    log_info "🧠 THE OVERMIND PROTOCOL - Minimal Deployment"
    log_info "============================================="
    
    # Set error trap
    trap cleanup_on_error ERR
    
    # Check environment
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Please run: ./simple-setup.sh first"
        exit 1
    fi
    
    # Check existing services
    check_existing_services
    
    # Setup database
    setup_database
    
    # Deploy TensorZero and monitoring
    deploy_tensorzero_only
    
    # Build and start trading system
    build_and_start_trading_system
    
    # Test services
    test_services
    
    # Test AI integration
    test_ai_integration
    
    # Show status
    show_status
}

# Handle arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping THE OVERMIND PROTOCOL..."
        
        # Stop trading system
        if [[ -f "overmind.pid" ]]; then
            kill "$(cat overmind.pid)" 2>/dev/null || true
            rm -f overmind.pid
            log_success "Trading system stopped"
        fi
        
        # Stop Docker services
        docker-compose -f docker-compose.minimal.yml down
        log_success "Services stopped"
        ;;
    "status")
        show_status
        ;;
    "logs")
        if [[ -f "logs/overmind.log" ]]; then
            tail -f logs/overmind.log
        else
            log_error "Log file not found: logs/overmind.log"
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|stop|status|logs}"
        exit 1
        ;;
esac
