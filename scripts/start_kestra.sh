#!/bin/bash

# THE OVERMIND PROTOCOL - Kestra Startup Script
# Professional workflow orchestration setup

set -e

echo "🚀 THE OVERMIND PROTOCOL - Starting Kestra Orchestration"
echo "=" * 60

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KESTRA_DIR="$PROJECT_ROOT/infrastructure/kestra"
COMPOSE_FILE="$KESTRA_DIR/docker-compose.kestra.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check prerequisites
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
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create OVERMIND network if it doesn't exist
create_network() {
    log_info "Creating OVERMIND network..."
    
    if ! docker network ls | grep -q "overmind-network"; then
        docker network create overmind-network
        log_success "OVERMIND network created"
    else
        log_info "OVERMIND network already exists"
    fi
}

# Setup Kestra directories
setup_directories() {
    log_info "Setting up Kestra directories..."
    
    mkdir -p "$KESTRA_DIR/flows"
    mkdir -p "$KESTRA_DIR/data"
    mkdir -p "$KESTRA_DIR/logs"
    
    log_success "Directories created"
}

# Start Kestra services
start_kestra() {
    log_info "Starting Kestra services..."
    
    cd "$PROJECT_ROOT"
    
    # Start Kestra stack
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check service health
    check_service_health
}

# Check service health
check_service_health() {
    log_info "Checking service health..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"
        
        # Check PostgreSQL
        if docker-compose -f "$COMPOSE_FILE" exec -T kestra-postgres pg_isready -U kestra &> /dev/null; then
            log_success "PostgreSQL is healthy"
        else
            log_warning "PostgreSQL not ready yet..."
        fi
        
        # Check Kestra server
        if curl -s http://localhost:8080/health &> /dev/null; then
            log_success "Kestra server is healthy"
            break
        else
            log_warning "Kestra server not ready yet..."
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Services failed to start properly"
            show_logs
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log_success "All services are healthy"
}

# Show service logs
show_logs() {
    log_info "Showing service logs..."
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
}

# Deploy flows
deploy_flows() {
    log_info "Deploying Kestra flows..."
    
    # Copy flows to Kestra
    if [ -d "$KESTRA_DIR/flows" ]; then
        log_info "Flows directory found, deploying flows..."
        
        # List available flows
        log_info "Available flows:"
        ls -la "$KESTRA_DIR/flows/"
        
        log_success "Flows deployed (manual import required via UI)"
    else
        log_warning "No flows directory found"
    fi
}

# Show access information
show_access_info() {
    log_success "Kestra is now running!"
    echo ""
    echo "🌐 Access Information:"
    echo "   Kestra UI: http://localhost:8080"
    echo "   Username: admin (if basic auth enabled)"
    echo "   Password: admin (if basic auth enabled)"
    echo ""
    echo "📊 Available Flows:"
    echo "   - historical-backtest: Automated backtesting with premium APIs"
    echo "   - mainnet-paper-trading: Paper trading on Solana Mainnet"
    echo ""
    echo "🔧 Management Commands:"
    echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "   Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "   Restart: docker-compose -f $COMPOSE_FILE restart"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Open Kestra UI at http://localhost:8080"
    echo "   2. Import flows from infrastructure/kestra/flows/"
    echo "   3. Configure environment variables in flows"
    echo "   4. Test flows in development environment first"
    echo ""
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down
    log_success "Cleanup completed"
}

# Main execution
main() {
    echo "Starting THE OVERMIND PROTOCOL Kestra setup..."
    
    # Handle script arguments
    case "${1:-start}" in
        "start")
            check_prerequisites
            create_network
            setup_directories
            start_kestra
            deploy_flows
            show_access_info
            ;;
        "stop")
            log_info "Stopping Kestra services..."
            docker-compose -f "$COMPOSE_FILE" down
            log_success "Kestra services stopped"
            ;;
        "restart")
            log_info "Restarting Kestra services..."
            docker-compose -f "$COMPOSE_FILE" restart
            check_service_health
            log_success "Kestra services restarted"
            ;;
        "logs")
            show_logs
            ;;
        "status")
            log_info "Checking Kestra status..."
            docker-compose -f "$COMPOSE_FILE" ps
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            echo "THE OVERMIND PROTOCOL - Kestra Management"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start     Start Kestra services (default)"
            echo "  stop      Stop Kestra services"
            echo "  restart   Restart Kestra services"
            echo "  logs      Show service logs"
            echo "  status    Show service status"
            echo "  cleanup   Stop and remove all containers"
            echo "  help      Show this help message"
            echo ""
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Trap cleanup on script exit
trap cleanup EXIT

# Run main function
main "$@"
