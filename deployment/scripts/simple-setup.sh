#!/bin/bash

# THE OVERMIND PROTOCOL - Simple Setup
# No external dependencies required

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
WALLET_FILE="test-wallet.json"

setup_environment() {
    log_info "Setting up THE OVERMIND PROTOCOL environment..."
    
    # Copy template with API keys
    cp .env.production "$ENV_FILE"
    
    # Use the wallet array directly as private key (Solana format)
    local wallet_array=$(cat "$WALLET_FILE")
    
    # Update wallet private key with the JSON array format
    sed -i "s/SOLANA_WALLET_PRIVATE_KEY=your-test-wallet-private-key-base58-encoded/SOLANA_WALLET_PRIVATE_KEY='$wallet_array'/" "$ENV_FILE"
    
    # Generate secure passwords
    local tensorzero_pass=$(openssl rand -hex 16)
    local sniper_pass=$(openssl rand -hex 16)
    local redis_pass=$(openssl rand -hex 16)
    local grafana_pass=$(openssl rand -hex 16)
    
    # Update passwords
    sed -i "s/TENSORZERO_DB_PASSWORD=your-secure-tensorzero-db-password-here/TENSORZERO_DB_PASSWORD=$tensorzero_pass/" "$ENV_FILE"
    sed -i "s/SNIPER_DB_PASSWORD=your-secure-sniper-db-password-here/SNIPER_DB_PASSWORD=$sniper_pass/" "$ENV_FILE"
    sed -i "s/REDIS_PASSWORD=your-secure-redis-password-here/REDIS_PASSWORD=$redis_pass/" "$ENV_FILE"
    sed -i "s/GRAFANA_ADMIN_PASSWORD=your-secure-grafana-admin-password-here/GRAFANA_ADMIN_PASSWORD=$grafana_pass/" "$ENV_FILE"
    
    # Add infrastructure config
    cat >> "$ENV_FILE" << EOF

# Infrastructure Configuration
KESTRA_API_URL=http://localhost:8080
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379

# Access Information
# Grafana: admin / $grafana_pass
# Test Wallet: $(solana-keygen pubkey $WALLET_FILE)
EOF
    
    log_success "Environment configured successfully"
    log_info "Test Wallet Address: $(solana-keygen pubkey $WALLET_FILE)"
    log_info "Grafana Password: $grafana_pass"
}

fund_test_wallet() {
    log_info "Setting up test wallet for devnet..."
    
    local wallet_address=$(solana-keygen pubkey "$WALLET_FILE")
    
    # Set Solana to devnet
    solana config set --url devnet >/dev/null 2>&1
    
    log_info "Test wallet address: $wallet_address"
    log_info "Requesting devnet SOL..."
    
    # Try airdrop
    if solana airdrop 1 "$wallet_address" >/dev/null 2>&1; then
        local balance=$(solana balance "$wallet_address" 2>/dev/null || echo "0 SOL")
        log_success "Airdrop successful - Balance: $balance"
    else
        log_warning "Airdrop failed (rate limited or network issue)"
        log_info "Manual funding required:"
        log_info "  1. Visit: https://faucet.solana.com/"
        log_info "  2. Enter address: $wallet_address"
        log_info "  3. Request 1-2 SOL for testing"
    fi
}

test_apis() {
    log_info "Testing API connectivity..."
    
    source "$ENV_FILE"
    
    # Test OpenAI
    log_info "Testing OpenAI API..."
    if timeout 10 curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
        "https://api.openai.com/v1/models" | grep -q "gpt" 2>/dev/null; then
        log_success "✅ OpenAI API: Connected"
    else
        log_warning "⚠️ OpenAI API: Failed (may be rate limited)"
    fi
    
    # Test Solana RPC
    log_info "Testing Solana RPC..."
    if timeout 10 curl -s -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"getVersion","params":[]}' \
        "$SOLANA_DEVNET_RPC_URL" | grep -q "solana-core" 2>/dev/null; then
        log_success "✅ Solana RPC: Connected"
    else
        log_warning "⚠️ Solana RPC: Failed"
    fi
    
    # Test Mistral
    log_info "Testing Mistral API..."
    if timeout 10 curl -s -H "Authorization: Bearer $MISTRAL_API_KEY" \
        "https://api.mistral.ai/v1/models" | grep -q "mistral" 2>/dev/null; then
        log_success "✅ Mistral API: Connected"
    else
        log_warning "⚠️ Mistral API: Failed (may be rate limited)"
    fi
    
    log_success "API tests completed"
}

show_summary() {
    source "$ENV_FILE"
    local wallet_address=$(solana-keygen pubkey "$WALLET_FILE")
    local balance=$(solana balance "$wallet_address" 2>/dev/null || echo "Unknown")
    local grafana_pass=$(grep "GRAFANA_ADMIN_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2)
    
    echo ""
    log_success "🧠 THE OVERMIND PROTOCOL - Setup Complete!"
    echo ""
    log_info "📋 Configuration Summary:"
    echo "  📁 Environment file: $ENV_FILE"
    echo "  🔑 Test wallet: $wallet_address"
    echo "  💰 Wallet balance: $balance"
    echo "  🔐 All passwords generated"
    echo "  🌐 API keys configured"
    echo ""
    
    log_info "🚀 Ready for Deployment!"
    echo ""
    echo "Next steps:"
    echo "1. Deploy THE OVERMIND PROTOCOL:"
    echo "   ./deploy-with-existing-infra.sh deploy"
    echo ""
    echo "2. Monitor deployment:"
    echo "   ./deploy-with-existing-infra.sh status"
    echo ""
    echo "3. Access dashboards:"
    echo "   - Trading System: http://localhost:8080"
    echo "   - TensorZero: http://localhost:3000"
    echo "   - Grafana: http://localhost:3001 (admin/$grafana_pass)"
    echo ""
    echo "4. Run integration tests:"
    echo "   cargo test --test real_api_integration_tests --ignored"
    echo ""
    
    log_warning "⚠️ IMPORTANT REMINDERS:"
    echo "  • System starts in PAPER TRADING mode"
    echo "  • Test wallet for devnet only"
    echo "  • Monitor for 48+ hours before live trading"
    echo "  • Emergency stop: export SNIPER_TRADING_MODE=paper"
    echo ""
    
    log_success "THE OVERMIND PROTOCOL is ready! 🚀"
}

main() {
    log_info "🧠 THE OVERMIND PROTOCOL - Simple Setup"
    log_info "======================================="
    
    # Check wallet exists
    if [[ ! -f "$WALLET_FILE" ]]; then
        log_error "Test wallet not found: $WALLET_FILE"
        exit 1
    fi
    
    # Setup environment
    setup_environment
    
    # Fund wallet
    fund_test_wallet
    
    # Test APIs
    test_apis
    
    # Show summary
    show_summary
}

main
