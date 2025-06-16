#!/bin/bash

# THE OVERMIND PROTOCOL - Quick Deployment
# Deploy infrastructure without building main app

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
COMPOSE_FILE="docker-compose.overmind.yml"

deploy_infrastructure() {
    log_info "Deploying THE OVERMIND PROTOCOL infrastructure..."
    
    # Deploy databases first
    log_info "Starting databases..."
    docker-compose -f "$COMPOSE_FILE" up -d \
        tensorzero-db \
        tensorzero-dragonfly \
        overmind-db \
        overmind-dragonfly
    
    # Wait for databases
    log_info "Waiting for databases to be ready..."
    sleep 20
    
    # Deploy TensorZero Gateway
    log_info "Starting TensorZero Gateway..."
    docker-compose -f "$COMPOSE_FILE" up -d tensorzero-gateway
    
    # Wait for TensorZero
    log_info "Waiting for TensorZero to be ready..."
    sleep 15
    
    # Deploy monitoring
    log_info "Starting monitoring services..."
    docker-compose -f "$COMPOSE_FILE" up -d \
        prometheus \
        grafana \
        elasticsearch \
        kibana
    
    log_success "Infrastructure deployed successfully"
}

test_services() {
    log_info "Testing deployed services..."
    
    # Test TensorZero
    if curl -f -s "http://localhost:3000/health" > /dev/null 2>&1; then
        log_success "✅ TensorZero Gateway: Running"
    else
        log_warning "⚠️ TensorZero Gateway: Not responding"
    fi
    
    # Test Prometheus
    if curl -f -s "http://localhost:9090/-/healthy" > /dev/null 2>&1; then
        log_success "✅ Prometheus: Running"
    else
        log_warning "⚠️ Prometheus: Not responding"
    fi
    
    # Test Grafana
    if curl -f -s "http://localhost:3001/api/health" > /dev/null 2>&1; then
        log_success "✅ Grafana: Running"
    else
        log_warning "⚠️ Grafana: Not responding"
    fi
    
    log_success "Service tests completed"
}

start_trading_system() {
    log_info "Starting THE OVERMIND PROTOCOL trading system..."
    
    # Build and run locally instead of Docker
    log_info "Building trading system locally..."
    
    # Set environment variables
    source "$ENV_FILE"
    export RUST_LOG=info
    export RUST_BACKTRACE=1
    
    # Build in release mode
    if cargo build --profile contabo; then
        log_success "Trading system built successfully"
        
        # Start in background
        log_info "Starting trading system..."
        nohup ./target/contabo/snipercor > logs/overmind.log 2>&1 &
        
        # Save PID
        echo $! > overmind.pid
        
        log_success "Trading system started (PID: $(cat overmind.pid))"
    else
        log_error "Failed to build trading system"
        return 1
    fi
}

test_integration() {
    log_info "Testing integration..."
    
    # Wait for trading system to start
    sleep 10
    
    # Test trading system health
    if curl -f -s "http://localhost:8080/health" > /dev/null 2>&1; then
        log_success "✅ Trading System: Running"
    else
        log_warning "⚠️ Trading System: Not responding"
        log_info "Check logs: tail -f logs/overmind.log"
    fi
    
    # Test TensorZero integration
    log_info "Testing AI integration..."
    if timeout 10 curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"function_name":"overmind_trading_decision","input":{"market_data":"{\"test\":true}"}}' \
        "http://localhost:3000/inference" | grep -q "inference_id" 2>/dev/null; then
        log_success "✅ AI Integration: Working"
    else
        log_warning "⚠️ AI Integration: Failed"
    fi
    
    log_success "Integration tests completed"
}

show_status() {
    log_success "🧠 THE OVERMIND PROTOCOL - Deployment Status"
    echo ""
    
    log_info "📊 Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    
    log_info "🔗 Access URLs:"
    echo "  🧠 Trading System:    http://localhost:8080"
    echo "  🤖 TensorZero:       http://localhost:3000"
    echo "  📊 Grafana:          http://localhost:3001"
    echo "  📈 Prometheus:       http://localhost:9090"
    echo "  🔍 Kibana:           http://localhost:5601"
    echo ""
    
    log_info "📋 Monitoring Commands:"
    echo "  📄 Trading logs:     tail -f logs/overmind.log"
    echo "  📊 System metrics:   curl http://localhost:8080/metrics"
    echo "  🔧 Stop trading:     kill \$(cat overmind.pid)"
    echo "  🛑 Stop all:         docker-compose -f $COMPOSE_FILE down"
    echo ""
    
    # Show Grafana password
    local grafana_pass=$(grep "GRAFANA_ADMIN_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2)
    log_info "🔐 Grafana Login: admin / $grafana_pass"
    echo ""
    
    log_warning "⚠️ IMPORTANT:"
    echo "  • System is in PAPER TRADING mode"
    echo "  • Monitor for 48+ hours before live trading"
    echo "  • Check logs regularly for any issues"
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
    docker-compose -f "$COMPOSE_FILE" down
    
    exit 1
}

main() {
    log_info "🧠 THE OVERMIND PROTOCOL - Quick Deployment"
    log_info "============================================"
    
    # Set error trap
    trap cleanup_on_error ERR
    
    # Check environment
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Please run: ./simple-setup.sh first"
        exit 1
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Test services
    test_services
    
    # Start trading system
    start_trading_system
    
    # Test integration
    test_integration
    
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
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Infrastructure stopped"
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
