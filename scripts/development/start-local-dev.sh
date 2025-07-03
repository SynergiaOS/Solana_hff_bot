#!/bin/bash

# THE OVERMIND PROTOCOL - Local Development Startup Script
# Professional local development environment setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 THE OVERMIND PROTOCOL - Local Development Environment${NC}"
echo -e "${BLUE}================================================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is running
check_docker() {
    echo "🔍 Checking Docker..."
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_status "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    echo "🔍 Checking Docker Compose..."
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install Docker Compose."
        exit 1
    fi
    print_status "Docker Compose is available"
}

# Setup environment file
setup_env() {
    echo "🔧 Setting up environment..."
    cd "$PROJECT_ROOT"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.local" ]; then
            cp .env.local .env
            print_status "Created .env from .env.local template"
            print_warning "Please edit .env file and add your API keys!"
            echo "  - OPENAI_API_KEY (required for AI functionality)"
            echo "  - DEEPSEEK_API_KEY (optional alternative)"
            echo "  - HELIUS_API_KEY (optional for enhanced Solana data)"
        else
            print_error ".env.local template not found!"
            exit 1
        fi
    else
        print_status "Environment file .env already exists"
    fi
}

# Check for required API keys
check_api_keys() {
    echo "🔑 Checking API keys..."
    cd "$PROJECT_ROOT"
    
    if [ -f ".env" ]; then
        source .env
        
        if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
            print_warning "OPENAI_API_KEY not configured in .env file"
            echo "  The AI Brain will not function without this key."
            echo "  You can still start the system, but AI features will be limited."
        else
            print_status "OPENAI_API_KEY is configured"
        fi
    fi
}

# Clean up previous containers (optional)
cleanup_previous() {
    echo "🧹 Cleaning up previous containers..."
    cd "$PROJECT_ROOT"
    
    # Stop and remove containers if they exist
    docker-compose -f docker-compose.local.yml down --remove-orphans 2>/dev/null || true
    print_status "Previous containers cleaned up"
}

# Build and start services
start_services() {
    echo "🏗️  Building and starting services..."
    cd "$PROJECT_ROOT"
    
    # Build and start all services
    docker-compose -f docker-compose.local.yml up --build -d
    
    if [ $? -eq 0 ]; then
        print_status "All services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Wait for services to be healthy
wait_for_services() {
    echo "⏳ Waiting for services to be healthy..."
    cd "$PROJECT_ROOT"
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "  Attempt $attempt/$max_attempts..."
        
        # Check if all services are healthy
        if docker-compose -f docker-compose.local.yml ps | grep -q "unhealthy\|starting"; then
            echo "    Some services are still starting..."
            sleep 10
            ((attempt++))
        else
            print_status "All services are healthy"
            return 0
        fi
    done
    
    print_warning "Some services may still be starting. Check status manually."
}

# Display service information
show_service_info() {
    echo ""
    echo -e "${BLUE}🌐 Service Access Information${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
    echo -e "${GREEN}📊 Mission Control Dashboard:${NC}    http://localhost:8501"
    echo -e "${GREEN}🧠 AI Brain API:${NC}                http://localhost:8001"
    echo -e "${GREEN}⚡ HFT Executor API:${NC}            http://localhost:8080"
    echo -e "${GREEN}🗄️  Vector Database (Chroma):${NC}    http://localhost:8000"
    echo -e "${GREEN}🗃️  PostgreSQL Database:${NC}        localhost:5432"
    echo -e "${GREEN}🔄 DragonflyDB (Redis):${NC}         localhost:6379"
    echo ""
    echo -e "${YELLOW}🛠️  Development Tools:${NC}"
    echo -e "${GREEN}📊 Redis Commander:${NC}             http://localhost:8081"
    echo -e "${GREEN}🗄️  pgAdmin:${NC}                    http://localhost:8082"
    echo ""
    echo -e "${BLUE}📋 Useful Commands:${NC}"
    echo "  View logs:        docker-compose -f docker-compose.local.yml logs -f"
    echo "  Check status:     docker-compose -f docker-compose.local.yml ps"
    echo "  Stop services:    docker-compose -f docker-compose.local.yml down"
    echo "  Restart service:  docker-compose -f docker-compose.local.yml restart [service]"
    echo ""
}

# Show logs option
show_logs() {
    echo -e "${BLUE}📋 Would you like to view the logs? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "📋 Showing logs (Ctrl+C to exit)..."
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.local.yml logs -f
    fi
}

# Main execution
main() {
    echo "Starting THE OVERMIND PROTOCOL local development environment..."
    echo ""
    
    # Run all checks and setup
    check_docker
    check_docker_compose
    setup_env
    check_api_keys
    
    # Ask user if they want to clean up previous containers
    echo ""
    echo -e "${YELLOW}🧹 Clean up previous containers? (recommended) (y/n)${NC}"
    read -r cleanup_response
    if [[ "$cleanup_response" =~ ^[Yy]$ ]]; then
        cleanup_previous
    fi
    
    echo ""
    start_services
    wait_for_services
    
    echo ""
    print_status "THE OVERMIND PROTOCOL local development environment is ready!"
    show_service_info
    
    echo ""
    show_logs
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Script interrupted. Services are still running.${NC}"; exit 1' INT

# Run main function
main "$@"
