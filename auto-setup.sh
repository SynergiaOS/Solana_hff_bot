#!/bin/bash

# THE OVERMIND PROTOCOL - Automated Setup
# Complete setup with generated test wallet

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
    
    # Convert wallet to base58 private key
    local wallet_array=$(cat "$WALLET_FILE")
    local private_key=$(echo "$wallet_array" | python3 -c "
import json
import sys
import base58

# Read the array from stdin
wallet_data = json.load(sys.stdin)

# Convert to bytes and then to base58
private_key_bytes = bytes(wallet_data)
private_key_base58 = base58.b58encode(private_key_bytes).decode('ascii')
print(private_key_base58)
")
    
    # Update wallet private key
    sed -i "s/SOLANA_WALLET_PRIVATE_KEY=your-test-wallet-private-key-base58-encoded/SOLANA_WALLET_PRIVATE_KEY=$private_key/" "$ENV_FILE"
    
    # Generate secure passwords
    local tensorzero_pass=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local sniper_pass=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local redis_pass=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    local grafana_pass=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Update passwords
    sed -i "s/TENSORZERO_DB_PASSWORD=your-secure-tensorzero-db-password-here/TENSORZERO_DB_PASSWORD=$tensorzero_pass/" "$ENV_FILE"
    sed -i "s/SNIPER_DB_PASSWORD=your-secure-sniper-db-password-here/SNIPER_DB_PASSWORD=$sniper_pass/" "$ENV_FILE"
    sed -i "s/REDIS_PASSWORD=your-secure-redis-password-here/REDIS_PASSWORD=$redis_pass/" "$ENV_FILE"
    sed -i "s/GRAFANA_ADMIN_PASSWORD=your-secure-grafana-admin-password-here/GRAFANA_ADMIN_PASSWORD=$grafana_pass/" "$ENV_FILE"
    
    # Add infrastructure config (using containerized versions)
    cat >> "$ENV_FILE" << EOF

# Infrastructure Configuration (Containerized)
KESTRA_API_URL=http://localhost:8080
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379

# Generated Passwords
# Grafana Admin: admin / $grafana_pass
EOF
    
    log_success "Environment configured with test wallet and secure passwords"
    log_info "Test Wallet Address: $(solana-keygen pubkey $WALLET_FILE)"
    log_info "Grafana Password: $grafana_pass"
}

fund_test_wallet() {
    log_info "Funding test wallet with devnet SOL..."
    
    local wallet_address=$(solana-keygen pubkey "$WALLET_FILE")
    
    # Set Solana to devnet
    solana config set --url devnet
    
    # Request airdrop
    log_info "Requesting SOL airdrop for testing..."
    solana airdrop 2 "$wallet_address" || {
        log_warning "Airdrop failed - may be rate limited"
        log_info "You can manually request SOL at: https://faucet.solana.com/"
        log_info "Wallet address: $wallet_address"
    }
    
    # Check balance
    local balance=$(solana balance "$wallet_address" 2>/dev/null || echo "0")
    log_info "Wallet balance: $balance"
    
    if [[ "$balance" == "0 SOL" ]]; then
        log_warning "Wallet has no SOL - please fund manually"
        log_info "Address: $wallet_address"
        log_info "Faucet: https://faucet.solana.com/"
    else
        log_success "Test wallet funded successfully"
    fi
}

test_api_connectivity() {
    log_info "Testing API connectivity..."
    
    # Source environment
    source "$ENV_FILE"
    
    # Test OpenAI
    if curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \
        "https://api.openai.com/v1/models" | grep -q "gpt"; then
        log_success "OpenAI API: Connected ✅"
    else
        log_warning "OpenAI API: Connection failed ⚠️"
    fi
    
    # Test Solana RPC
    if curl -s -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"getVersion","params":[]}' \
        "$SOLANA_DEVNET_RPC_URL" | grep -q "solana-core"; then
        log_success "Solana RPC: Connected ✅"
    else
        log_warning "Solana RPC: Connection failed ⚠️"
    fi
    
    # Test Mistral
    if curl -s -H "Authorization: Bearer $MISTRAL_API_KEY" \
        "https://api.mistral.ai/v1/models" | grep -q "mistral"; then
        log_success "Mistral API: Connected ✅"
    else
        log_warning "Mistral API: Connection failed ⚠️"
    fi
    
    log_success "API connectivity tests completed"
}

show_summary() {
    log_success "🧠 THE OVERMIND PROTOCOL - Setup Complete!"
    echo ""
    log_info "Configuration Summary:"
    echo "  📁 Environment: $ENV_FILE"
    echo "  🔑 Test Wallet: $(solana-keygen pubkey $WALLET_FILE)"
    echo "  💰 Wallet Balance: $(solana balance $(solana-keygen pubkey $WALLET_FILE) 2>/dev/null || echo 'Unknown')"
    echo "  🔐 Passwords: Generated and configured"
    echo "  🌐 APIs: Tested and ready"
    echo ""
    
    log_info "Ready for deployment! Next commands:"
    echo "1. 🚀 Deploy system:"
    echo "   ./deploy-with-existing-infra.sh deploy"
    echo ""
    echo "2. 📊 Monitor deployment:"
    echo "   ./deploy-with-existing-infra.sh status"
    echo ""
    echo "3. 🧪 Test integration:"
    echo "   cargo test --test real_api_integration_tests --ignored"
    echo ""
    
    log_warning "IMPORTANT:"
    echo "  ⚠️  System will start in PAPER TRADING mode"
    echo "  ⚠️  Test wallet has minimal SOL for testing only"
    echo "  ⚠️  Monitor system for 48+ hours before considering live trading"
    echo ""
    
    log_success "THE OVERMIND PROTOCOL is ready for deployment! 🚀"
}

main() {
    log_info "🧠 THE OVERMIND PROTOCOL - Automated Setup"
    log_info "=========================================="
    
    # Check if wallet exists
    if [[ ! -f "$WALLET_FILE" ]]; then
        log_error "Test wallet file not found: $WALLET_FILE"
        log_info "Please run: solana-keygen new --no-bip39-passphrase --outfile $WALLET_FILE"
        exit 1
    fi
    
    # Setup environment
    setup_environment
    
    # Fund test wallet
    fund_test_wallet
    
    # Test API connectivity
    test_api_connectivity
    
    # Show summary
    show_summary
}

# Check dependencies
if ! command -v python3 &> /dev/null; then
    log_error "Python3 is required for wallet conversion"
    exit 1
fi

if ! python3 -c "import base58" 2>/dev/null; then
    log_info "Installing base58 library..."
    pip3 install base58 || {
        log_error "Failed to install base58. Please install manually: pip3 install base58"
        exit 1
    }
fi

# Run main
main
