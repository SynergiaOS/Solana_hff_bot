#!/bin/bash

# THE OVERMIND PROTOCOL - Production Deployment Script
# Automated deployment with safety checks and monitoring

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.overmind.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file $ENV_FILE not found"
        log_info "Please copy .env.production to .env and configure it"
        exit 1
    fi
    
    # Check compose file
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Docker Compose file $COMPOSE_FILE not found"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

validate_environment() {
    log_info "Validating environment configuration..."
    
    # Source environment file
    source "$ENV_FILE"
    
    # Check critical variables
    local required_vars=(
        "OPENAI_API_KEY"
        "TENSORZERO_DB_PASSWORD"
        "SNIPER_DB_PASSWORD"
        "SOLANA_DEVNET_RPC_URL"
        "SOLANA_WALLET_PRIVATE_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Check trading mode
    if [[ "$SNIPER_TRADING_MODE" != "paper" ]]; then
        log_warning "Trading mode is set to $SNIPER_TRADING_MODE"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    log_success "Environment validation passed"
}

create_backup() {
    log_info "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup environment file
    cp "$ENV_FILE" "$BACKUP_DIR/"
    
    # Backup docker volumes if they exist
    if docker volume ls | grep -q overmind; then
        log_info "Backing up Docker volumes..."
        docker run --rm -v overmind-db-data:/data -v "$PWD/$BACKUP_DIR":/backup alpine tar czf /backup/overmind-db-data.tar.gz -C /data .
    fi
    
    log_success "Backup created in $BACKUP_DIR"
}

build_images() {
    log_info "Building Docker images..."
    
    docker-compose -f "$COMPOSE_FILE" build --no-cache overmind-trading
    
    log_success "Docker images built successfully"
}

deploy_services() {
    log_info "Deploying THE OVERMIND PROTOCOL services..."
    
    # Start infrastructure services first
    log_info "Starting infrastructure services..."
    docker-compose -f "$COMPOSE_FILE" up -d \
        tensorzero-db \
        tensorzero-dragonfly \
        overmind-db \
        overmind-dragonfly \
        chroma \
        elasticsearch \
        prometheus
    
    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    sleep 30
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" up -d \
        tensorzero-gateway \
        overmind-brain \
        overmind-trading
    
    # Wait for applications to be ready
    log_info "Waiting for applications to be ready..."
    sleep 20
    
    # Start monitoring services
    log_info "Starting monitoring services..."
    docker-compose -f "$COMPOSE_FILE" up -d \
        grafana \
        alertmanager \
        kibana
    
    log_success "All services deployed successfully"
}

health_check() {
    log_info "Performing health checks..."
    
    local services=(
        "http://localhost:8080/health:OVERMIND Trading System"
        "http://localhost:3000/health:TensorZero Gateway"
        "http://localhost:8000/api/v1/heartbeat:Chroma Vector DB"
        "http://localhost:9090/-/healthy:Prometheus"
        "http://localhost:3001/api/health:Grafana"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service"
        
        log_info "Checking $name..."
        
        for i in {1..30}; do
            if curl -f -s "$url" > /dev/null 2>&1; then
                log_success "$name is healthy"
                break
            fi
            
            if [[ $i -eq 30 ]]; then
                log_error "$name health check failed"
                return 1
            fi
            
            sleep 2
        done
    done
    
    log_success "All health checks passed"
}

show_status() {
    log_info "THE OVERMIND PROTOCOL Status:"
    echo
    docker-compose -f "$COMPOSE_FILE" ps
    echo
    
    log_info "Access URLs:"
    echo "🧠 Trading System:     http://localhost:8080"
    echo "🤖 AI Brain (Vector):  http://localhost:8000"
    echo "📊 Grafana Dashboard:  http://localhost:3001 (admin/password from .env)"
    echo "📈 Prometheus:         http://localhost:9090"
    echo "🔍 Kibana Logs:       http://localhost:5601"
    echo "🚀 TensorZero:        http://localhost:3000"
    echo
    
    log_info "Monitoring Commands:"
    echo "📋 View logs:          docker-compose -f $COMPOSE_FILE logs -f overmind-trading"
    echo "📊 View metrics:       curl http://localhost:8080/metrics"
    echo "🔧 Shell access:       docker-compose -f $COMPOSE_FILE exec overmind-trading /bin/bash"
    echo
}

cleanup_on_failure() {
    log_error "Deployment failed. Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down
    exit 1
}

main() {
    log_info "🧠 THE OVERMIND PROTOCOL - Production Deployment"
    log_info "================================================"
    
    # Set trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    # Run deployment steps
    check_prerequisites
    validate_environment
    create_backup
    build_images
    deploy_services
    health_check
    show_status
    
    log_success "🚀 THE OVERMIND PROTOCOL deployed successfully!"
    log_info "Monitor the system for 10-15 minutes to ensure stability"
    log_warning "Remember: System is in PAPER TRADING mode. Monitor for 48+ hours before considering live trading."
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping THE OVERMIND PROTOCOL..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "THE OVERMIND PROTOCOL stopped"
        ;;
    "restart")
        log_info "Restarting THE OVERMIND PROTOCOL..."
        docker-compose -f "$COMPOSE_FILE" restart
        log_success "THE OVERMIND PROTOCOL restarted"
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f "${2:-overmind-trading}"
        ;;
    "status")
        show_status
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status}"
        echo "  deploy  - Deploy THE OVERMIND PROTOCOL"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show logs (optionally specify service)"
        echo "  status  - Show current status"
        exit 1
        ;;
esac
