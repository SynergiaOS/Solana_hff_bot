#!/bin/bash

# THE OVERMIND PROTOCOL - Get Vault Configuration from Server
# Downloads configuration after manual setup

set -euo pipefail

SERVER_IP="${1:-89.117.53.53}"
SERVER_USER="${2:-marcin}"

echo "🔐 THE OVERMIND PROTOCOL - Getting Vault Configuration"
echo "====================================================="
echo ""
echo "🎯 Target Server: $SERVER_USER@$SERVER_IP"
echo ""

echo "📋 STEP 1: Downloading Vault configuration from server..."

# Try to download the configuration file
if scp "$SERVER_USER@$SERVER_IP:/tmp/vault-config.json" ./vault-production-config.json 2>/dev/null; then
    echo "✅ Configuration downloaded successfully!"
    echo ""
    
    # Display the configuration
    echo "🎯 VAULT CONFIGURATION:"
    echo "======================"
    cat vault-production-config.json | jq .
    echo ""
    
    # Extract key values
    VAULT_ADDR=$(jq -r '.vault_addr' vault-production-config.json)
    ROOT_TOKEN=$(jq -r '.root_token' vault-production-config.json)
    ROLE_ID=$(jq -r '.role_id' vault-production-config.json)
    SECRET_ID=$(jq -r '.secret_id' vault-production-config.json)
    
    echo "📋 EXTRACTED CONFIGURATION:"
    echo "   Vault Address: $VAULT_ADDR"
    echo "   Root Token: ${ROOT_TOKEN:0:20}..."
    echo "   Role ID: ${ROLE_ID:0:20}..."
    echo "   Secret ID: ${SECRET_ID:0:20}..."
    echo ""
    
    # Create .env.vault file
    echo "💾 Creating .env.vault file..."
    
    cat > .env.vault << EOF
# THE OVERMIND PROTOCOL - Vault Configuration (Production)
# Generated automatically from server setup

# =============================================================================
# VAULT SERVER CONFIGURATION
# =============================================================================

# Vault server address
VAULT_ADDR=$VAULT_ADDR

# Vault authentication token (root token for admin operations)
VAULT_TOKEN=$ROOT_TOKEN

# Skip TLS verification (using self-signed certificate)
VAULT_SKIP_VERIFY=true

# Vault namespace (empty for open source Vault)
VAULT_NAMESPACE=

# =============================================================================
# VAULT SECRETS CONFIGURATION
# =============================================================================

# KV secrets engine mount path
VAULT_MOUNT_PATH=overmind-secrets

# AppRole authentication (recommended for production)
VAULT_ROLE_ID=$ROLE_ID
VAULT_SECRET_ID=$SECRET_ID

# Transit encryption key name
VAULT_ENCRYPTION_KEY=overmind-encryption

# =============================================================================
# THE OVERMIND PROTOCOL VAULT SETTINGS
# =============================================================================

# Enable Vault integration
VAULT_ENABLED=true

# Vault operation mode
VAULT_MODE=production

# Wallet security level
VAULT_WALLET_SECURITY_LEVEL=MAXIMUM

# Vault audit logging
VAULT_AUDIT_ENABLED=true

# Vault token renewal settings
VAULT_TOKEN_RENEW_ENABLED=true
VAULT_TOKEN_RENEW_THRESHOLD=300

# =============================================================================
# PRODUCTION SETTINGS
# =============================================================================

# Production server IP
VAULT_PRODUCTION_SERVER=$SERVER_IP

# Production mode flag
VAULT_DEV_MODE=false

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# Maximum number of authentication retries
VAULT_MAX_RETRIES=3

# Request timeout (seconds)
VAULT_TIMEOUT=30

# Connection pool settings
VAULT_MAX_CONNECTIONS=10
VAULT_CONNECTION_TIMEOUT=10

# =============================================================================
# LOGGING SETTINGS
# =============================================================================

# Vault client logging level
VAULT_LOG_LEVEL=INFO

# Log Vault API requests (disabled for security)
VAULT_LOG_REQUESTS=false

# Log file path
VAULT_LOG_FILE=logs/vault-client.log
EOF

    echo "✅ .env.vault file created!"
    echo ""
    
    # Test connection
    echo "🔧 Testing Vault connection..."
    
    if command -v vault &> /dev/null; then
        export VAULT_ADDR="$VAULT_ADDR"
        export VAULT_TOKEN="$ROOT_TOKEN"
        export VAULT_SKIP_VERIFY="true"
        
        if vault status >/dev/null 2>&1; then
            echo "✅ Vault connection successful!"
            
            # Test secret access
            if vault kv list overmind-secrets >/dev/null 2>&1; then
                echo "✅ Secret engine accessible!"
            else
                echo "⚠️  Secret engine not accessible (this is normal if no secrets exist yet)"
            fi
        else
            echo "❌ Vault connection failed. Please check server status."
        fi
    else
        echo "⚠️  Vault CLI not installed locally. Install with: sudo apt install vault"
    fi
    
    echo ""
    echo "📋 NEXT STEPS:"
    echo "============="
    echo "1. ✅ Vault configuration downloaded"
    echo "2. ✅ .env.vault file created"
    echo "3. 🔄 Migrate wallets: ./scripts/vault/migrate-wallets.sh"
    echo "4. 🚀 Start THE OVERMIND PROTOCOL: source .env.vault && cargo run"
    echo ""
    echo "🎉 Vault integration ready for THE OVERMIND PROTOCOL!"
    
else
    echo "❌ Failed to download configuration from server."
    echo ""
    echo "📋 MANUAL STEPS:"
    echo "==============="
    echo "1. Connect to server: ssh $SERVER_USER@$SERVER_IP"
    echo "2. Check if file exists: ls -la /tmp/vault-config.json"
    echo "3. If file exists, copy manually:"
    echo "   scp $SERVER_USER@$SERVER_IP:/tmp/vault-config.json ./vault-production-config.json"
    echo ""
    echo "📋 ALTERNATIVE - Get configuration manually:"
    echo "==========================================="
    echo "Connect to server and run:"
    echo ""
    echo "ssh $SERVER_USER@$SERVER_IP"
    echo "cat /tmp/vault-config.json"
    echo ""
    echo "Then create .env.vault file with the values."
    
    exit 1
fi
