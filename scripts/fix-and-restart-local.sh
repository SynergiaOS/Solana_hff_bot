#!/bin/bash

# THE OVERMIND PROTOCOL - Fix and Restart Local Development
# Quick fix for Docker build issues and restart

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 THE OVERMIND PROTOCOL - Fix and Restart Local Development${NC}"
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

# Navigate to project root
cd "$(dirname "$0")/.."

echo "🧹 Cleaning up previous containers and images..."
docker-compose -f docker-compose.local.yml down --remove-orphans 2>/dev/null || true
docker system prune -f 2>/dev/null || true
print_status "Cleanup completed"

echo "🏗️  Building and starting services (this may take a few minutes)..."
docker-compose -f docker-compose.local.yml up --build -d

if [ $? -eq 0 ]; then
    print_status "Services started successfully"
    
    echo "⏳ Waiting for services to be ready..."
    sleep 30
    
    echo ""
    echo -e "${BLUE}🌐 Service Access Points:${NC}"
    echo "  Mission Control: http://localhost:8501"
    echo "  AI Brain API:    http://localhost:8001"
    echo "  HFT Executor:    http://localhost:8080"
    echo "  Vector Database: http://localhost:8000"
    echo "  Redis Commander: http://localhost:8081"
    echo "  pgAdmin:         http://localhost:8082"
    echo ""
    
    echo "🔍 Checking service health..."
    
    # Check Mission Control
    if curl -f http://localhost:8501/_stcore/health >/dev/null 2>&1; then
        print_status "Mission Control is healthy"
    else
        print_warning "Mission Control not ready yet (may still be starting)"
    fi
    
    # Check Vector Database
    if curl -f http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
        print_status "Vector Database is healthy"
    else
        print_warning "Vector Database not ready yet (may still be starting)"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 Local development environment is running!${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next steps:${NC}"
    echo "  1. Open Mission Control: http://localhost:8501"
    echo "  2. Test goal setting functionality"
    echo "  3. Check logs: docker-compose -f docker-compose.local.yml logs -f"
    echo ""
    
else
    print_error "Failed to start services"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "  1. Check Docker is running: docker info"
    echo "  2. Check logs: docker-compose -f docker-compose.local.yml logs"
    echo "  3. Try manual build: docker-compose -f docker-compose.local.yml build"
    exit 1
fi
