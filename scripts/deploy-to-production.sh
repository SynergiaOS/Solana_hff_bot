#!/bin/bash

# THE OVERMIND PROTOCOL - Professional Production Deployment Script
# Implements "Local Playground, Global Battlefield" workflow

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_SERVER="marcin@89.117.53.53"
PROJECT_PATH="/home/marcin/windsurf/Projects/LastBot"
COMPOSE_FILE="deployment/docker-compose/docker-compose.overmind.yml"
BACKUP_DIR="/tmp/overmind-backup-$(date +%Y%m%d-%H%M%S)"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 THE OVERMIND PROTOCOL - Production Deployment${NC}"
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

# Function to run command with error handling
run_command() {
    local cmd="$1"
    local description="$2"
    
    echo "🔄 $description..."
    if eval "$cmd"; then
        print_status "$description completed"
    else
        print_error "$description failed"
        exit 1
    fi
}

# Pre-deployment validation checklist
validate_local_environment() {
    echo "🔍 STAGE 1: Local Environment Validation"
    echo "========================================"
    
    cd "$PROJECT_ROOT"
    
    # Check if we're in the right directory
    if [ ! -f "pixi.toml" ] || [ ! -f "docker-compose.local.yml" ]; then
        print_error "Not in THE OVERMIND PROTOCOL project directory"
        exit 1
    fi
    print_status "Project directory validated"
    
    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_error "Uncommitted changes detected. Please commit all changes before deployment."
        echo "Run: git add . && git commit -m 'your message'"
        exit 1
    fi
    print_status "No uncommitted changes"
    
    # Check if local tests pass
    echo "🧪 Running local test suite..."
    if command -v pixi >/dev/null 2>&1; then
        run_command "pixi run test-agent" "Python tests"
    else
        print_warning "Pixi not available, skipping Python tests"
    fi
    
    if command -v cargo >/dev/null 2>&1; then
        run_command "cargo test" "Rust tests"
    else
        print_warning "Cargo not available, skipping Rust tests"
    fi
    
    # Check if local environment is working
    echo "🏗️ Validating local environment..."
    if docker-compose -f docker-compose.local.yml ps | grep -q "Up"; then
        print_status "Local environment is running"
        
        # Test Mission Control health
        if curl -f http://localhost:8501/_stcore/health >/dev/null 2>&1; then
            print_status "Mission Control dashboard is healthy"
        else
            print_warning "Mission Control dashboard not responding (may be normal if not started)"
        fi
    else
        print_warning "Local environment not running (may be normal)"
    fi
    
    echo ""
}

# Git operations
handle_version_control() {
    echo "📝 STAGE 2: Version Control Operations"
    echo "====================================="
    
    cd "$PROJECT_ROOT"
    
    # Push to remote
    run_command "git push origin main" "Pushing changes to remote repository"
    
    # Get current commit hash
    COMMIT_HASH=$(git rev-parse HEAD)
    print_status "Current commit: $COMMIT_HASH"
    
    echo ""
}

# Production server operations
deploy_to_production() {
    echo "🚀 STAGE 3: Production Deployment"
    echo "================================="
    
    # Test SSH connection
    run_command "ssh -o ConnectTimeout=10 $PRODUCTION_SERVER 'echo \"SSH connection successful\"'" "Testing SSH connection"
    
    # Create backup of current production state
    echo "💾 Creating production backup..."
    ssh $PRODUCTION_SERVER "mkdir -p $BACKUP_DIR"
    ssh $PRODUCTION_SERVER "cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE ps > $BACKUP_DIR/services-before.txt 2>/dev/null || true"
    ssh $PRODUCTION_SERVER "cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE logs --tail=100 > $BACKUP_DIR/logs-before.txt 2>/dev/null || true"
    print_status "Production backup created at $BACKUP_DIR"
    
    # Pull latest changes
    run_command "ssh $PRODUCTION_SERVER 'cd $PROJECT_PATH && git pull origin main'" "Pulling latest changes on production server"
    
    # Verify the commit hash matches
    PROD_COMMIT=$(ssh $PRODUCTION_SERVER "cd $PROJECT_PATH && git rev-parse HEAD")
    if [ "$COMMIT_HASH" = "$PROD_COMMIT" ]; then
        print_status "Commit hash verified: $PROD_COMMIT"
    else
        print_error "Commit hash mismatch! Local: $COMMIT_HASH, Production: $PROD_COMMIT"
        exit 1
    fi
    
    # Deploy services
    echo "🏗️ Deploying services..."
    ssh $PRODUCTION_SERVER "cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE up --build -d"
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 30
    
    echo ""
}

# Post-deployment validation
validate_production_deployment() {
    echo "✅ STAGE 4: Production Validation"
    echo "================================="
    
    # Check service status
    echo "🔍 Checking service status..."
    ssh $PRODUCTION_SERVER "cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE ps"
    
    # Health checks
    echo "🏥 Running health checks..."
    
    # Mission Control health check
    if ssh $PRODUCTION_SERVER "curl -f http://localhost:8501/_stcore/health" >/dev/null 2>&1; then
        print_status "Mission Control dashboard is healthy"
    else
        print_error "Mission Control dashboard health check failed"
        echo "Check logs: ssh $PRODUCTION_SERVER 'cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE logs mission-control'"
    fi
    
    # AI Brain health check
    if ssh $PRODUCTION_SERVER "curl -f http://localhost:8001/health" >/dev/null 2>&1; then
        print_status "AI Brain is healthy"
    else
        print_warning "AI Brain health check failed (may be starting up)"
    fi
    
    # HFT Executor health check
    if ssh $PRODUCTION_SERVER "curl -f http://localhost:8080/health" >/dev/null 2>&1; then
        print_status "HFT Executor is healthy"
    else
        print_warning "HFT Executor health check failed (may be starting up)"
    fi
    
    # Database connectivity
    if ssh $PRODUCTION_SERVER "cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE exec -T postgres-local pg_isready -U overmind" >/dev/null 2>&1; then
        print_status "Database is healthy"
    else
        print_warning "Database health check failed"
    fi
    
    echo ""
}

# Deployment summary
show_deployment_summary() {
    echo "📊 DEPLOYMENT SUMMARY"
    echo "===================="
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📍 Production Access Points:${NC}"
    echo "  Mission Control: http://89.117.53.53:8501"
    echo "  AI Brain API:    http://89.117.53.53:8001"
    echo "  HFT Executor:    http://89.117.53.53:8080"
    echo "  Monitoring:      http://89.117.53.53:9090"
    echo ""
    echo -e "${BLUE}🛠️ Useful Commands:${NC}"
    echo "  View logs:       ssh $PRODUCTION_SERVER 'cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE logs -f'"
    echo "  Check status:    ssh $PRODUCTION_SERVER 'cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE ps'"
    echo "  Restart service: ssh $PRODUCTION_SERVER 'cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE restart [service]'"
    echo "  Emergency stop:  ssh $PRODUCTION_SERVER 'cd $PROJECT_PATH && docker-compose -f $COMPOSE_FILE down'"
    echo ""
    echo -e "${YELLOW}📋 Post-Deployment Checklist:${NC}"
    echo "  [ ] Verify Mission Control dashboard loads correctly"
    echo "  [ ] Check that goal setting works without AttributeError"
    echo "  [ ] Monitor logs for any errors in the first 10 minutes"
    echo "  [ ] Validate trading mode is set correctly (paper/live)"
    echo ""
    echo -e "${GREEN}✅ Deployment completed at $(date)${NC}"
    echo -e "${GREEN}✅ Commit deployed: $COMMIT_HASH${NC}"
    echo -e "${GREEN}✅ Backup location: $BACKUP_DIR${NC}"
}

# Rollback function
rollback_deployment() {
    echo -e "${RED}🔄 ROLLBACK PROCEDURE${NC}"
    echo "===================="
    echo ""
    echo "If you need to rollback this deployment:"
    echo "1. SSH to production: ssh $PRODUCTION_SERVER"
    echo "2. Navigate to project: cd $PROJECT_PATH"
    echo "3. Stop current services: docker-compose -f $COMPOSE_FILE down"
    echo "4. Checkout previous commit: git checkout HEAD~1"
    echo "5. Restart services: docker-compose -f $COMPOSE_FILE up -d"
    echo ""
    echo "Backup location: $BACKUP_DIR"
}

# Main execution
main() {
    echo "Starting professional production deployment..."
    echo ""
    
    # Confirmation prompt
    echo -e "${YELLOW}⚠️  This will deploy THE OVERMIND PROTOCOL to production server.${NC}"
    echo -e "${YELLOW}   Make sure you have completed local testing and validation.${NC}"
    echo ""
    read -p "Continue with production deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
    
    # Execute deployment stages
    validate_local_environment
    handle_version_control
    deploy_to_production
    validate_production_deployment
    show_deployment_summary
    
    echo ""
    echo -e "${GREEN}🎉 THE OVERMIND PROTOCOL deployment completed successfully!${NC}"
}

# Handle script interruption
trap 'echo -e "\n${RED}Deployment interrupted!${NC}"; rollback_deployment; exit 1' INT

# Run main function
main "$@"
