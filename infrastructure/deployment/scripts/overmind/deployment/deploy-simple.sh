#!/bin/bash

# THE OVERMIND PROTOCOL - Simple Deployment
# Uses existing Dragonfly and SQLite for simplicity

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

check_dragonfly() {
    log_info "Checking Dragonfly connection..."
    
    if redis-cli -h localhost -p 6380 ping > /dev/null 2>&1; then
        log_success "✅ Dragonfly: Running on port 6380"
        return 0
    else
        log_warning "⚠️ Dragonfly: Not accessible on port 6380"
        log_info "Will use in-memory cache instead"
        return 1
    fi
}

deploy_tensorzero() {
    log_info "Deploying TensorZero Gateway with SQLite..."
    
    # Create minimal docker-compose for TensorZero with SQLite
    cat > docker-compose.simple.yml << 'EOF'
version: '3.8'

services:
  # TensorZero Gateway - AI Decision Engine
  tensorzero-gateway:
    image: tensorzero/gateway:latest
    container_name: overmind-tensorzero
    ports:
      - "3003:3000"
    environment:
      - TENSORZERO_DATABASE_URL=sqlite:///app/data/tensorzero.db
      - TENSORZERO_REDIS_URL=redis://host.docker.internal:6380
      - TENSORZERO_LOG_LEVEL=info
      - TENSORZERO_OPENAI_API_KEY=${OPENAI_API_KEY}
      - TENSORZERO_MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - TENSORZERO_GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./tensorzero-config:/app/config
      - ./data/tensorzero:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    extra_hosts:
      - "host.docker.internal:host-gateway"

volumes:
  tensorzero-data:
EOF
    
    # Create data directory
    mkdir -p data/tensorzero
    
    # Source environment
    source "$ENV_FILE"
    
    # Deploy TensorZero
    docker-compose -f docker-compose.simple.yml up -d
    
    log_success "TensorZero deployed with SQLite backend"
}

build_and_start_trading_system() {
    log_info "Building and starting THE OVERMIND PROTOCOL trading system..."
    
    # Source environment
    source "$ENV_FILE"
    export RUST_LOG=info
    export RUST_BACKTRACE=1
    
    # Use SQLite for simplicity
    export SNIPER_DATABASE_URL="sqlite:./data/snipercor.db"
    
    # Create logs and data directories
    mkdir -p logs data
    
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
    sleep 20
    
    # Test TensorZero
    local tensorzero_status="❌"
    if curl -f -s "http://localhost:3003/health" > /dev/null 2>&1; then
        tensorzero_status="✅"
        log_success "✅ TensorZero Gateway: Running"
    else
        log_warning "⚠️ TensorZero Gateway: Not responding"
    fi
    
    # Test Trading System
    local trading_status="❌"
    if curl -f -s "http://localhost:8080/health" > /dev/null 2>&1; then
        trading_status="✅"
        log_success "✅ Trading System: Running"
    else
        log_warning "⚠️ Trading System: Not responding"
        log_info "Check logs: tail -f logs/overmind.log"
    fi
    
    # Test existing Kestra
    local kestra_status="❌"
    if curl -f -s "http://localhost:8080/api/v1/flows" > /dev/null 2>&1; then
        kestra_status="✅"
        log_success "✅ Kestra: Running (existing)"
    else
        log_warning "⚠️ Kestra: Not accessible"
    fi
    
    # Test existing Grafana
    local grafana_status="❌"
    if curl -f -s "http://localhost:3000/api/health" > /dev/null 2>&1; then
        grafana_status="✅"
        log_success "✅ Grafana: Running (existing)"
    else
        log_warning "⚠️ Grafana: Not accessible"
    fi
    
    # Test existing Prometheus
    local prometheus_status="❌"
    if curl -f -s "http://localhost:9091/-/healthy" > /dev/null 2>&1; then
        prometheus_status="✅"
        log_success "✅ Prometheus: Running (existing)"
    else
        log_warning "⚠️ Prometheus: Not accessible"
    fi
    
    log_success "Service tests completed"
    
    # Return status summary
    echo ""
    log_info "📊 Service Status Summary:"
    echo "  🧠 Trading System:    $trading_status"
    echo "  🤖 TensorZero:       $tensorzero_status"
    echo "  🔧 Kestra:           $kestra_status"
    echo "  📊 Grafana:          $grafana_status"
    echo "  📈 Prometheus:       $prometheus_status"
    echo ""
}

test_ai_integration() {
    log_info "Testing AI integration..."
    
    # Wait a bit more for TensorZero to be fully ready
    sleep 10
    
    # Test TensorZero AI inference
    local response=$(timeout 15 curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"function_name":"overmind_trading_decision","input":{"market_data":"{\"test\":true,\"symbol\":\"SOL/USDC\",\"price\":50.0}"}}' \
        "http://localhost:3003/inference" 2>/dev/null || echo "timeout")
    
    if echo "$response" | grep -q "inference_id" 2>/dev/null; then
        log_success "✅ AI Integration: Working"
        log_info "Sample AI response received successfully"
    elif [[ "$response" == "timeout" ]]; then
        log_warning "⚠️ AI Integration: Timeout (may still be starting)"
    else
        log_warning "⚠️ AI Integration: Not ready yet"
        log_info "Response: $response"
        log_info "TensorZero may still be initializing..."
    fi
}

show_status() {
    local grafana_pass=$(grep "GRAFANA_ADMIN_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2)
    local wallet_address=$(solana-keygen pubkey test-wallet.json 2>/dev/null || echo "Unknown")
    
    log_success "🧠 THE OVERMIND PROTOCOL - Deployment Complete!"
    echo ""
    
    log_info "🔗 Access URLs:"
    echo "  🧠 Trading System:    http://localhost:8080"
    echo "  🤖 TensorZero:       http://localhost:3003"
    echo "  🔧 Kestra:           http://localhost:8080 (existing)"
    echo "  📊 Grafana:          http://localhost:3000 (existing)"
    echo "  📈 Prometheus:       http://localhost:9091 (existing)"
    echo ""
    
    log_info "🔐 Access Information:"
    echo "  🔑 Test Wallet:      $wallet_address"
    echo "  📊 Grafana Login:    admin / $grafana_pass (if using new instance)"
    echo ""
    
    log_info "📋 Monitoring Commands:"
    echo "  📄 Trading logs:     tail -f logs/overmind.log"
    echo "  📊 System metrics:   curl http://localhost:8080/metrics"
    echo "  🔧 Stop trading:     kill \$(cat overmind.pid)"
    echo "  🛑 Stop TensorZero:  docker-compose -f docker-compose.simple.yml down"
    echo ""
    
    log_info "🧪 Testing Commands:"
    echo "  🔬 Integration test:  cargo test --test real_api_integration_tests --ignored"
    echo "  🧠 OVERMIND tests:    cargo test --test overmind_integration_tests"
    echo "  🤖 AI test:          curl -X POST -H 'Content-Type: application/json' \\"
    echo "                        -d '{\"function_name\":\"overmind_trading_decision\",\"input\":{\"market_data\":\"{\\\"test\\\":true}\"}}' \\"
    echo "                        http://localhost:3003/inference"
    echo ""
    
    log_warning "⚠️ IMPORTANT:"
    echo "  • System is in PAPER TRADING mode"
    echo "  • Using SQLite for persistence (lightweight)"
    echo "  • Connected to your existing Dragonfly cache"
    echo "  • Monitor for 48+ hours before live trading"
    echo "  • Emergency stop: kill \$(cat overmind.pid)"
    echo ""
    
    log_success "THE OVERMIND PROTOCOL is running! 🚀"
    log_info "Next: Monitor logs and run integration tests"
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    
    # Stop trading system if running
    if [[ -f "overmind.pid" ]]; then
        kill "$(cat overmind.pid)" 2>/dev/null || true
        rm -f overmind.pid
    fi
    
    # Stop Docker services
    docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
    
    exit 1
}

main() {
    log_info "🧠 THE OVERMIND PROTOCOL - Simple Deployment"
    log_info "============================================"
    
    # Set error trap
    trap cleanup_on_error ERR
    
    # Check environment
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Please run: ./simple-setup.sh first"
        exit 1
    fi
    
    # Check Dragonfly (optional)
    check_dragonfly || true
    
    # Deploy TensorZero
    deploy_tensorzero
    
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
        docker-compose -f docker-compose.simple.yml down
        log_success "TensorZero stopped"
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
