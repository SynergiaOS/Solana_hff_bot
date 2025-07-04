#!/bin/bash

# THE OVERMIND PROTOCOL - Server Deployment Script
# Deploys the system to production server with proper configuration

set -e  # Exit on any error

echo "🚀 THE OVERMIND PROTOCOL - Server Deployment"
echo "=============================================="

# Configuration
SERVER_USER="marcin"
SERVER_HOST="89.117.53.53"
PROJECT_DIR="/home/marcin/windsurf/Projects/LastBot"
REMOTE_DIR="/home/marcin/overmind-protocol"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Validate local environment
print_status "Step 1: Validating local environment..."

if ! command -v git &> /dev/null; then
    print_error "Git is not installed"
    exit 1
fi

if ! command -v ssh &> /dev/null; then
    print_error "SSH is not installed"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "Cargo.toml" ]; then
    print_error "Not in THE OVERMIND PROTOCOL directory (Cargo.toml not found)"
    exit 1
fi

# Check compilation
print_status "Checking compilation..."
if ! cargo check --quiet; then
    print_error "Code does not compile. Fix compilation errors first."
    exit 1
fi

print_success "Local environment validated"

# Step 2: Commit changes if needed
print_status "Step 2: Checking git status..."

if [ -n "$(git status --porcelain)" ]; then
    print_warning "Uncommitted changes detected"
    echo "Modified files:"
    git status --short
    
    read -p "Do you want to commit these changes? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Committing changes..."
        
        # Add critical fixes
        git add src/modules/executor.rs src/modules/rpc_failover.rs src/config.rs
        git add brain/src/overmind_brain/brain.py src/main.rs master_control_system.py
        git add src/modules/mod.rs src/modules/strategy.rs
        
        git commit -m "feat: implement critical fixes for production deployment

- Add transaction retry logic with exponential backoff
- Implement RPC endpoint failover system
- Enhance AI Brain error handling with fallbacks
- Add comprehensive logging with JSON format
- Fix master control system missing methods
- Update production Docker configuration"
        
        # Add infrastructure updates
        git add infrastructure/compose/docker-compose.production.yml
        git add .env.production deploy_to_server.sh
        
        git commit -m "feat: enhance deployment configuration

- Fix Docker Compose brain build path
- Replace GROQ with DeepSeek V2 configuration
- Add comprehensive environment template
- Create automated deployment script"
        
        print_success "Changes committed"
    else
        print_warning "Proceeding without committing changes"
    fi
else
    print_success "No uncommitted changes"
fi

# Step 3: Push to repository
print_status "Step 3: Pushing to repository..."

git push origin main
print_success "Code pushed to repository"

# Step 4: Deploy to server
print_status "Step 4: Deploying to server..."

# Create deployment commands
DEPLOY_COMMANDS="
set -e
cd $REMOTE_DIR || { echo 'Remote directory not found'; exit 1; }

echo '📥 Pulling latest code...'
git pull origin main

echo '🔧 Setting up environment...'
# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    cp .env.production .env
    echo '⚠️  Please edit .env file with your actual API keys'
fi

echo '🐳 Building and starting services...'
cd infrastructure/compose

# Stop existing services
docker-compose -f docker-compose.production.yml down || true

# Build and start services
docker-compose -f docker-compose.production.yml up -d --build

echo '⏳ Waiting for services to start...'
sleep 30

echo '🔍 Checking service health...'
docker-compose -f docker-compose.production.yml ps

echo '✅ Deployment completed!'
echo ''
echo '📋 Next steps:'
echo '1. Edit .env file with your actual API keys'
echo '2. Set SOLANA_WALLET_PRIVATE_KEY to your wallet private key'
echo '3. Configure DEEPSEEK_API_KEY (primary AI model)'
echo '4. Start paper trading: SNIPER_TRADING_MODE=paper'
echo '5. Monitor logs: docker-compose logs -f'
echo ''
echo '🌐 Access points:'
echo '- Grafana: http://89.117.53.53:3000'
echo '- Prometheus: http://89.117.53.53:9090'
echo '- API Health: http://89.117.53.53:8080/health'
"

# Execute deployment on server
print_status "Connecting to server and deploying..."

ssh -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "$DEPLOY_COMMANDS"

if [ $? -eq 0 ]; then
    print_success "Deployment completed successfully!"
    echo ""
    echo "🎯 THE OVERMIND PROTOCOL deployed to server!"
    echo ""
    echo "📋 IMPORTANT NEXT STEPS:"
    echo "1. SSH to server: ssh $SERVER_USER@$SERVER_HOST"
    echo "2. Edit .env file: nano $REMOTE_DIR/.env"
    echo "3. Add your API keys:"
    echo "   - DEEPSEEK_API_KEY=your_deepseek_key"
    echo "   - SOLANA_WALLET_PRIVATE_KEY=your_wallet_key"
    echo "   - HELIUS_API_KEY=edbcd361-78a0-4998-bd1e-8d4666722f82"
    echo "4. Restart services: docker-compose -f infrastructure/compose/docker-compose.production.yml restart"
    echo "5. Monitor: docker-compose -f infrastructure/compose/docker-compose.production.yml logs -f"
    echo ""
    echo "🌐 Access URLs:"
    echo "- Grafana: http://89.117.53.53:3000"
    echo "- Prometheus: http://89.117.53.53:9090" 
    echo "- API Health: http://89.117.53.53:8080/health"
    echo ""
    echo "🎯 Ready for paper trading validation!"
else
    print_error "Deployment failed!"
    exit 1
fi
