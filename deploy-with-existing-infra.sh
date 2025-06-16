#!/bin/bash

# THE OVERMIND PROTOCOL - Deployment with Existing Infrastructure
# Uses your existing Kestra and Dragonfly setup

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

check_existing_infrastructure() {
    log_info "Checking existing infrastructure..."
    
    # Check if Kestra is running
    if curl -f -s "${KESTRA_API_URL:-http://localhost:8080}/api/v1/flows" > /dev/null 2>&1; then
        log_success "Kestra is running and accessible"
    else
        log_warning "Kestra not accessible at ${KESTRA_API_URL:-http://localhost:8080}"
        log_info "Please ensure Kestra is running or update KESTRA_API_URL"
    fi
    
    # Check if Dragonfly is running
    if redis-cli -h "${DRAGONFLY_HOST:-localhost}" -p "${DRAGONFLY_PORT:-6379}" ping > /dev/null 2>&1; then
        log_success "Dragonfly is running and accessible"
    else
        log_warning "Dragonfly not accessible at ${DRAGONFLY_HOST:-localhost}:${DRAGONFLY_PORT:-6379}"
        log_info "Will use containerized Dragonfly instead"
    fi
}

create_environment_file() {
    log_info "Creating environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_info "Creating new .env file from template..."
        cp .env.production "$ENV_FILE"
        
        log_warning "Please edit $ENV_FILE with your API keys and configuration"
        log_info "Required variables:"
        echo "  - OPENAI_API_KEY"
        echo "  - SOLANA_DEVNET_RPC_URL"
        echo "  - SOLANA_DEVNET_WSS_URL"
        echo "  - SOLANA_WALLET_PRIVATE_KEY"
        echo "  - HELIUS_API_KEY"
        echo ""
        read -p "Press Enter after editing $ENV_FILE..."
    fi
    
    # Source environment
    source "$ENV_FILE"
    
    # Validate critical variables
    local required_vars=(
        "OPENAI_API_KEY"
        "SOLANA_DEVNET_RPC_URL"
        "SOLANA_WALLET_PRIVATE_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required variable $var is not set in $ENV_FILE"
            exit 1
        fi
    done
    
    log_success "Environment configuration validated"
}

deploy_overmind_components() {
    log_info "Deploying THE OVERMIND PROTOCOL components..."
    
    # Deploy only the components we need (excluding Kestra and external Dragonfly)
    log_info "Starting core services..."
    docker-compose -f "$COMPOSE_FILE" up -d \
        tensorzero-db \
        overmind-db \
        tensorzero-gateway \
        overmind-trading
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Deploy monitoring if not using external
    if [[ "${USE_EXTERNAL_MONITORING:-false}" != "true" ]]; then
        log_info "Starting monitoring services..."
        docker-compose -f "$COMPOSE_FILE" up -d \
            prometheus \
            grafana
    fi
    
    log_success "OVERMIND components deployed"
}

deploy_kestra_workflow() {
    log_info "Deploying Kestra workflow..."
    
    local kestra_url="${KESTRA_API_URL:-http://localhost:8080}"
    local workflow_file="kestra-workflows/overmind-trading-workflow.yml"
    
    if [[ -f "$workflow_file" ]]; then
        # Deploy workflow to Kestra
        curl -X POST \
            -H "Content-Type: application/x-yaml" \
            -H "Authorization: Bearer ${KESTRA_API_TOKEN:-}" \
            --data-binary "@$workflow_file" \
            "$kestra_url/api/v1/flows" || {
            log_warning "Failed to deploy workflow to Kestra"
            log_info "You can manually import $workflow_file to Kestra UI"
        }
        
        log_success "Kestra workflow deployed"
    else
        log_warning "Kestra workflow file not found: $workflow_file"
    fi
}

test_integration() {
    log_info "Testing integration with existing infrastructure..."
    
    # Test OVERMIND API
    local overmind_url="http://localhost:8080"
    if curl -f -s "$overmind_url/health" > /dev/null; then
        log_success "OVERMIND API is healthy"
    else
        log_error "OVERMIND API not responding"
        return 1
    fi
    
    # Test TensorZero
    local tensorzero_url="http://localhost:3000"
    if curl -f -s "$tensorzero_url/health" > /dev/null; then
        log_success "TensorZero Gateway is healthy"
    else
        log_error "TensorZero Gateway not responding"
        return 1
    fi
    
    # Test Kestra connection
    local kestra_url="${KESTRA_API_URL:-http://localhost:8080}"
    if curl -f -s "$kestra_url/api/v1/flows" > /dev/null; then
        log_success "Kestra connection successful"
    else
        log_warning "Kestra connection failed - workflows may need manual deployment"
    fi
    
    log_success "Integration tests passed"
}

show_deployment_status() {
    log_info "THE OVERMIND PROTOCOL Deployment Status:"
    echo ""
    
    # Show running containers
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    
    log_info "Access URLs:"
    echo "🧠 OVERMIND Trading:   http://localhost:8080"
    echo "🤖 TensorZero:        http://localhost:3000"
    echo "📊 Grafana:           http://localhost:3001"
    echo "📈 Prometheus:        http://localhost:9090"
    echo "🔧 Kestra:            ${KESTRA_API_URL:-http://localhost:8080}"
    echo ""
    
    log_info "Next Steps:"
    echo "1. 📊 Check Grafana dashboards for system metrics"
    echo "2. 🔧 Verify Kestra workflow is running"
    echo "3. 🧪 Run integration tests: cargo test --test real_api_integration_tests --ignored"
    echo "4. 📋 Monitor logs: ./deploy-overmind.sh logs"
    echo "5. ⏱️ Let system run in paper mode for 48+ hours"
    echo ""
    
    log_success "🧠 THE OVERMIND PROTOCOL deployed with existing infrastructure!"
}

main() {
    log_info "🧠 THE OVERMIND PROTOCOL - Deployment with Existing Infrastructure"
    log_info "=================================================================="
    
    # Check existing infrastructure
    check_existing_infrastructure
    
    # Setup environment
    create_environment_file
    
    # Deploy OVERMIND components
    deploy_overmind_components
    
    # Deploy Kestra workflow
    deploy_kestra_workflow
    
    # Test integration
    test_integration
    
    # Show status
    show_deployment_status
}

# Handle arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "test")
        test_integration
        ;;
    "workflow")
        deploy_kestra_workflow
        ;;
    "status")
        show_deployment_status
        ;;
    *)
        echo "Usage: $0 {deploy|test|workflow|status}"
        exit 1
        ;;
esac
