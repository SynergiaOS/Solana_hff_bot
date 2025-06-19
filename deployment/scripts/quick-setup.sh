#!/bin/bash

# THE OVERMIND PROTOCOL - Quick Setup Script
# Automated setup with provided API keys

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

create_environment_file() {
    log_info "Creating environment file with provided API keys..."
    
    # Copy template
    cp .env.production "$ENV_FILE"
    
    log_success "Environment file created with API keys"
    log_info "API Keys configured:"
    echo "  ✅ OpenAI API Key"
    echo "  ✅ Mistral API Key" 
    echo "  ✅ Google API Key"
    echo "  ✅ Perplexity API Key"
    echo "  ✅ Solana DevNet RPC URLs"
}

prompt_for_missing_config() {
    log_info "Collecting remaining configuration..."
    
    # Test wallet private key
    echo ""
    log_warning "CRITICAL: Need Solana test wallet private key"
    log_info "This should be a TEST wallet with minimal SOL for devnet testing"
    log_warning "NEVER use a wallet with real funds!"
    echo ""
    read -p "Enter Solana test wallet private key (base58): " WALLET_KEY
    
    if [[ -z "$WALLET_KEY" ]]; then
        log_error "Wallet private key is required"
        exit 1
    fi
    
    # Update environment file
    sed -i "s/SOLANA_WALLET_PRIVATE_KEY=your-test-wallet-private-key-base58-encoded/SOLANA_WALLET_PRIVATE_KEY=$WALLET_KEY/" "$ENV_FILE"
    
    # Kestra configuration
    echo ""
    log_info "Kestra Configuration:"
    read -p "Kestra API URL (default: http://localhost:8080): " KESTRA_URL
    KESTRA_URL=${KESTRA_URL:-http://localhost:8080}
    
    read -p "Kestra API Token (optional, press Enter to skip): " KESTRA_TOKEN
    
    # Dragonfly configuration
    echo ""
    log_info "Dragonfly Configuration:"
    read -p "Dragonfly Host (default: localhost): " DRAGONFLY_HOST
    DRAGONFLY_HOST=${DRAGONFLY_HOST:-localhost}
    
    read -p "Dragonfly Port (default: 6379): " DRAGONFLY_PORT
    DRAGONFLY_PORT=${DRAGONFLY_PORT:-6379}
    
    read -p "Dragonfly Password (optional, press Enter to skip): " DRAGONFLY_PASSWORD
    
    # Add to environment file
    echo "" >> "$ENV_FILE"
    echo "# Kestra Configuration" >> "$ENV_FILE"
    echo "KESTRA_API_URL=$KESTRA_URL" >> "$ENV_FILE"
    if [[ -n "$KESTRA_TOKEN" ]]; then
        echo "KESTRA_API_TOKEN=$KESTRA_TOKEN" >> "$ENV_FILE"
    fi
    
    echo "" >> "$ENV_FILE"
    echo "# Dragonfly Configuration" >> "$ENV_FILE"
    echo "DRAGONFLY_HOST=$DRAGONFLY_HOST" >> "$ENV_FILE"
    echo "DRAGONFLY_PORT=$DRAGONFLY_PORT" >> "$ENV_FILE"
    if [[ -n "$DRAGONFLY_PASSWORD" ]]; then
        echo "DRAGONFLY_PASSWORD=$DRAGONFLY_PASSWORD" >> "$ENV_FILE"
    fi
    
    log_success "Configuration completed"
}

generate_secure_passwords() {
    log_info "Generating secure passwords for databases..."
    
    # Generate random passwords
    TENSORZERO_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SNIPER_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    GRAFANA_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Update environment file
    sed -i "s/TENSORZERO_DB_PASSWORD=your-secure-tensorzero-db-password-here/TENSORZERO_DB_PASSWORD=$TENSORZERO_DB_PASSWORD/" "$ENV_FILE"
    sed -i "s/SNIPER_DB_PASSWORD=your-secure-sniper-db-password-here/SNIPER_DB_PASSWORD=$SNIPER_DB_PASSWORD/" "$ENV_FILE"
    sed -i "s/REDIS_PASSWORD=your-secure-redis-password-here/REDIS_PASSWORD=$REDIS_PASSWORD/" "$ENV_FILE"
    sed -i "s/GRAFANA_ADMIN_PASSWORD=your-secure-grafana-admin-password-here/GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD/" "$ENV_FILE"
    
    log_success "Secure passwords generated"
    log_info "Grafana admin password: $GRAFANA_PASSWORD"
}

test_api_keys() {
    log_info "Testing API key connectivity..."
    
    # Test OpenAI API
    local openai_key=$(grep "OPENAI_API_KEY=" "$ENV_FILE" | cut -d'=' -f2)
    if curl -s -H "Authorization: Bearer $openai_key" https://api.openai.com/v1/models | grep -q "gpt"; then
        log_success "OpenAI API key is valid"
    else
        log_warning "OpenAI API key test failed - may be rate limited or invalid"
    fi
    
    # Test Solana RPC
    local rpc_url=$(grep "SOLANA_DEVNET_RPC_URL=" "$ENV_FILE" | cut -d'=' -f2-)
    if curl -s -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"getVersion","params":[]}' "$rpc_url" | grep -q "solana-core"; then
        log_success "Solana RPC endpoint is accessible"
    else
        log_warning "Solana RPC endpoint test failed"
    fi
    
    log_success "API connectivity tests completed"
}

show_next_steps() {
    log_success "🧠 THE OVERMIND PROTOCOL - Setup Complete!"
    echo ""
    log_info "Configuration Summary:"
    echo "  📁 Environment file: $ENV_FILE"
    echo "  🔑 API Keys: Configured"
    echo "  🔐 Passwords: Generated"
    echo "  🔧 Infrastructure: Ready for connection"
    echo ""
    
    log_info "Next Steps:"
    echo "1. 🚀 Deploy THE OVERMIND PROTOCOL:"
    echo "   ./deploy-with-existing-infra.sh deploy"
    echo ""
    echo "2. 🧪 Test integration:"
    echo "   ./deploy-with-existing-infra.sh test"
    echo ""
    echo "3. 📊 Monitor system:"
    echo "   - Trading System: http://localhost:8080"
    echo "   - TensorZero: http://localhost:3000"
    echo "   - Grafana: http://localhost:3001 (admin/$(grep GRAFANA_ADMIN_PASSWORD $ENV_FILE | cut -d'=' -f2))"
    echo ""
    echo "4. 🔍 Run real API tests:"
    echo "   cargo test --test real_api_integration_tests --ignored"
    echo ""
    
    log_warning "IMPORTANT REMINDERS:"
    echo "  ⚠️  System starts in PAPER TRADING mode"
    echo "  ⚠️  Use only TEST wallet with minimal funds"
    echo "  ⚠️  Monitor for 48+ hours before considering live trading"
    echo "  ⚠️  Emergency stop: export SNIPER_TRADING_MODE=paper"
    echo ""
    
    log_success "Ready for deployment! 🚀"
}

main() {
    log_info "🧠 THE OVERMIND PROTOCOL - Quick Setup"
    log_info "======================================"
    
    # Create environment file with API keys
    create_environment_file
    
    # Prompt for missing configuration
    prompt_for_missing_config
    
    # Generate secure passwords
    generate_secure_passwords
    
    # Test API connectivity
    test_api_keys
    
    # Show next steps
    show_next_steps
}

# Run main function
main
