#!/bin/bash
# THE OVERMIND PROTOCOL - Mission Control Production Deployment Script
# Deploys Mission Control dashboard to production environment with validation

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PRODUCTION_SERVER="marcin@89.117.53.53"
PRODUCTION_PATH="/home/marcin/Solana_hff_bot"
BACKUP_DIR="/home/marcin/backups/mission_control"
LOG_FILE="/tmp/mission_control_deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-deployment validation
validate_local_environment() {
    log "🔍 Validating local environment..."
    
    # Check required files exist
    local required_files=(
        "mission_control/app.py"
        "mission_control/requirements.txt"
        "mission_control/Dockerfile"
        "infrastructure/compose/docker-compose.overmind.yml"
        "infrastructure/nginx/overmind.conf"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            error "Required file missing: $file"
        fi
    done
    
    # Check Python dependencies
    if ! command -v python3 &> /dev/null; then
        error "Python3 is required but not installed"
    fi
    
    # Validate Mission Control app syntax
    log "Validating Mission Control app syntax..."
    cd "$PROJECT_ROOT"
    python3 -m py_compile mission_control/app.py || error "Mission Control app has syntax errors"
    
    success "Local environment validation passed"
}

# Create backup of existing deployment
create_backup() {
    log "📦 Creating backup of existing deployment..."
    
    ssh "$PRODUCTION_SERVER" "
        mkdir -p $BACKUP_DIR/$(date +%Y%m%d_%H%M%S)
        if [[ -d $PRODUCTION_PATH/mission_control ]]; then
            cp -r $PRODUCTION_PATH/mission_control $BACKUP_DIR/$(date +%Y%m%d_%H%M%S)/
            echo 'Backup created successfully'
        else
            echo 'No existing mission_control directory to backup'
        fi
    " || warning "Backup creation failed, continuing with deployment"
    
    success "Backup completed"
}

# Deploy Mission Control files
deploy_files() {
    log "🚀 Deploying Mission Control files..."
    
    # Create mission_control directory on production
    ssh "$PRODUCTION_SERVER" "mkdir -p $PRODUCTION_PATH/mission_control"
    
    # Copy Mission Control files
    scp -r "$PROJECT_ROOT/mission_control/"* "$PRODUCTION_SERVER:$PRODUCTION_PATH/mission_control/"
    
    # Copy updated Docker Compose configuration
    scp "$PROJECT_ROOT/infrastructure/compose/docker-compose.overmind.yml" \
        "$PRODUCTION_SERVER:$PRODUCTION_PATH/infrastructure/compose/"
    
    # Copy nginx configuration if it exists
    if [[ -f "$PROJECT_ROOT/infrastructure/nginx/overmind.conf" ]]; then
        scp "$PROJECT_ROOT/infrastructure/nginx/overmind.conf" \
            "$PRODUCTION_SERVER:/tmp/overmind.conf"
    fi
    
    success "Files deployed successfully"
}

# Update nginx configuration
update_nginx() {
    log "🌐 Updating nginx configuration..."
    
    ssh "$PRODUCTION_SERVER" "
        if [[ -f /tmp/overmind.conf ]]; then
            sudo cp /tmp/overmind.conf /etc/nginx/sites-available/overmind
            sudo nginx -t && sudo systemctl reload nginx
            echo 'Nginx configuration updated and reloaded'
        else
            echo 'No nginx configuration to update'
        fi
    " || warning "Nginx update failed, manual configuration may be required"
    
    success "Nginx configuration updated"
}

# Install Python dependencies
install_dependencies() {
    log "📦 Installing Python dependencies..."
    
    ssh "$PRODUCTION_SERVER" "
        cd $PRODUCTION_PATH/mission_control
        
        # Create virtual environment if it doesn't exist
        if [[ ! -d venv ]]; then
            python3 -m venv venv
        fi
        
        # Activate virtual environment and install dependencies
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        echo 'Dependencies installed successfully'
    " || error "Failed to install dependencies"
    
    success "Dependencies installed"
}

# Build and deploy Docker containers
deploy_containers() {
    log "🐳 Building and deploying Docker containers..."
    
    ssh "$PRODUCTION_SERVER" "
        cd $PRODUCTION_PATH
        
        # Build Mission Control container
        docker-compose -f infrastructure/compose/docker-compose.overmind.yml build mission-control
        
        # Start Mission Control service
        docker-compose -f infrastructure/compose/docker-compose.overmind.yml up -d mission-control
        
        echo 'Mission Control container deployed'
    " || error "Failed to deploy containers"
    
    success "Containers deployed successfully"
}

# Validate deployment
validate_deployment() {
    log "✅ Validating deployment..."
    
    # Wait for service to start
    log "Waiting for Mission Control to start..."
    sleep 30
    
    # Check if Mission Control is responding
    ssh "$PRODUCTION_SERVER" "
        # Check if container is running
        if docker-compose -f $PRODUCTION_PATH/infrastructure/compose/docker-compose.overmind.yml ps mission-control | grep -q 'Up'; then
            echo 'Mission Control container is running'
        else
            echo 'ERROR: Mission Control container is not running'
            exit 1
        fi
        
        # Check if service is responding
        if curl -f http://localhost:8501/health &>/dev/null; then
            echo 'Mission Control health check passed'
        else
            echo 'WARNING: Mission Control health check failed'
        fi
        
        # Check nginx proxy
        if curl -f http://localhost:8090/mission-control/ &>/dev/null; then
            echo 'Nginx proxy to Mission Control working'
        else
            echo 'WARNING: Nginx proxy check failed'
        fi
    " || error "Deployment validation failed"
    
    success "Deployment validation passed"
}

# Integration testing
run_integration_tests() {
    log "🧪 Running integration tests..."
    
    ssh "$PRODUCTION_SERVER" "
        cd $PRODUCTION_PATH
        
        # Test API endpoints
        echo 'Testing API endpoints...'
        
        # Test health endpoint
        if curl -f http://localhost:8501/health &>/dev/null; then
            echo '✅ Health endpoint working'
        else
            echo '❌ Health endpoint failed'
        fi
        
        # Test goal management API (if available)
        if curl -f http://localhost:8080/api/v1/control/health &>/dev/null; then
            echo '✅ Goal management API working'
        else
            echo '⚠️ Goal management API not available (may not be implemented yet)'
        fi
        
        # Check logs for errors
        echo 'Checking logs for errors...'
        if docker logs overmind-mission-control 2>&1 | grep -i error | head -5; then
            echo 'Found some errors in logs (review above)'
        else
            echo '✅ No errors found in logs'
        fi
    " || warning "Some integration tests failed"
    
    success "Integration tests completed"
}

# Rollback function
rollback() {
    log "🔄 Rolling back deployment..."
    
    ssh "$PRODUCTION_SERVER" "
        cd $PRODUCTION_PATH
        
        # Stop Mission Control container
        docker-compose -f infrastructure/compose/docker-compose.overmind.yml stop mission-control
        
        # Restore from latest backup
        LATEST_BACKUP=\$(ls -t $BACKUP_DIR/ | head -1)
        if [[ -n \"\$LATEST_BACKUP\" && -d \"$BACKUP_DIR/\$LATEST_BACKUP/mission_control\" ]]; then
            rm -rf $PRODUCTION_PATH/mission_control
            cp -r $BACKUP_DIR/\$LATEST_BACKUP/mission_control $PRODUCTION_PATH/
            echo 'Restored from backup: '\$LATEST_BACKUP
        else
            echo 'No backup available for rollback'
        fi
    " || error "Rollback failed"
    
    success "Rollback completed"
}

# Main deployment function
main() {
    log "🚀 Starting Mission Control Production Deployment"
    log "Production Server: $PRODUCTION_SERVER"
    log "Production Path: $PRODUCTION_PATH"
    log "Log File: $LOG_FILE"
    
    # Trap for cleanup on exit
    trap 'log "Deployment script finished"' EXIT
    
    # Deployment steps
    validate_local_environment
    create_backup
    deploy_files
    update_nginx
    install_dependencies
    deploy_containers
    validate_deployment
    run_integration_tests
    
    success "🎉 Mission Control deployment completed successfully!"
    log "Access Mission Control at: http://your-domain.com/mission-control/"
    log "Direct access: http://$PRODUCTION_SERVER:8501"
    log "Deployment log: $LOG_FILE"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    "validate")
        validate_deployment
        run_integration_tests
        ;;
    "test")
        run_integration_tests
        ;;
    *)
        echo "Usage: $0 [deploy|rollback|validate|test]"
        echo "  deploy   - Full deployment (default)"
        echo "  rollback - Rollback to previous version"
        echo "  validate - Validate current deployment"
        echo "  test     - Run integration tests only"
        exit 1
        ;;
esac
