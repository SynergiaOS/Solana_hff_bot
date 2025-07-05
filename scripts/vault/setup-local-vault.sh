#!/bin/bash

# THE OVERMIND PROTOCOL - Local Vault Setup
# Quick setup for development and testing

set -euo pipefail

echo "🔐 THE OVERMIND PROTOCOL - Local Vault Setup"
echo "============================================="

# Check if vault is installed
if ! command -v vault &> /dev/null; then
    echo "📦 Installing Vault..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install vault
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew tap hashicorp/tap
            brew install hashicorp/tap/vault
        else
            echo "❌ Please install Homebrew first: https://brew.sh/"
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install Vault manually: https://developer.hashicorp.com/vault/install"
        exit 1
    fi
fi

echo "✅ Vault installed: $(vault version)"

# Create vault data directory
VAULT_DATA_DIR="./vault-data"
mkdir -p "$VAULT_DATA_DIR"

echo "🚀 Starting Vault dev server..."

# Start Vault in dev mode with custom root token
VAULT_DEV_ROOT_TOKEN="overmind-dev-token-$(date +%s)"

echo "📋 Starting Vault with:"
echo "   - Address: https://127.0.0.1:8200"
echo "   - Root Token: $VAULT_DEV_ROOT_TOKEN"
echo "   - TLS: Enabled"

# Start vault in background
vault server \
    -dev \
    -dev-root-token-id="$VAULT_DEV_ROOT_TOKEN" \
    -dev-tls \
    -dev-listen-address="127.0.0.1:8200" &

VAULT_PID=$!
echo "🔄 Vault PID: $VAULT_PID"

# Wait for Vault to start
echo "⏳ Waiting for Vault to start..."
sleep 5

# Get the TLS cert path from vault output
VAULT_CACERT_PATH="/tmp/vault-tls*/vault-ca.pem"

# Export environment variables
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_TOKEN="$VAULT_DEV_ROOT_TOKEN"
export VAULT_SKIP_VERIFY="true"  # For dev mode with self-signed cert

echo "🔧 Setting up Vault for THE OVERMIND PROTOCOL..."

# Wait a bit more for Vault to be fully ready
sleep 3

# Enable KV secrets engine v2
vault secrets enable -path=overmind-secrets kv-v2

# Enable Transit engine for encryption
vault secrets enable transit

# Create encryption key
vault write -f transit/keys/overmind-encryption

# Enable AppRole auth method
vault auth enable approle

echo "📋 Creating Vault policies..."

# Create trading policy
cat > /tmp/trading-policy.hcl << 'EOF'
# THE OVERMIND PROTOCOL - Trading Policy
path "overmind-secrets/data/wallets/*" {
  capabilities = ["read"]
}
path "overmind-secrets/metadata/wallets/*" {
  capabilities = ["read", "list"]
}
path "transit/encrypt/overmind-encryption" {
  capabilities = ["update"]
}
path "transit/decrypt/overmind-encryption" {
  capabilities = ["update"]
}
path "auth/token/lookup-self" {
  capabilities = ["read"]
}
path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

vault policy write trading-policy /tmp/trading-policy.hcl

# Create admin policy
cat > /tmp/admin-policy.hcl << 'EOF'
# THE OVERMIND PROTOCOL - Admin Policy
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
EOF

vault policy write admin-policy /tmp/admin-policy.hcl

echo "🎭 Creating AppRole for trading bot..."

# Create AppRole
vault write auth/approle/role/overmind-trading \
    token_policies="trading-policy" \
    token_ttl=1h \
    token_max_ttl=4h \
    bind_secret_id=true \
    secret_id_ttl=24h

# Get Role ID and Secret ID
ROLE_ID=$(vault read -field=role_id auth/approle/role/overmind-trading/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/overmind-trading/secret-id)

echo "💾 Saving configuration..."

# Create .env.vault file
cat > .env.vault << EOF
# THE OVERMIND PROTOCOL - Vault Configuration (Local Dev)
VAULT_ADDR=https://127.0.0.1:8200
VAULT_TOKEN=$VAULT_DEV_ROOT_TOKEN
VAULT_SKIP_VERIFY=true
VAULT_MOUNT_PATH=overmind-secrets
VAULT_ROLE_ID=$ROLE_ID
VAULT_SECRET_ID=$SECRET_ID

# For development only - in production use AppRole authentication
VAULT_DEV_MODE=true
EOF

# Create vault credentials file
cat > vault-credentials.json << EOF
{
  "vault_addr": "https://127.0.0.1:8200",
  "root_token": "$VAULT_DEV_ROOT_TOKEN",
  "role_id": "$ROLE_ID",
  "secret_id": "$SECRET_ID",
  "mount_path": "overmind-secrets",
  "dev_mode": true
}
EOF

echo "🔐 Creating sample wallet in Vault..."

# Store sample wallet
vault kv put overmind-secrets/wallets/main-trading-28sol \
    private_key="SAMPLE_KEY_WILL_BE_REPLACED" \
    address="4rtY4TCojYn2o86kRjNfETKcBxCWfX39dG4B21y4HYYm" \
    balance_sol=28.028235358 \
    security_level="MAXIMUM" \
    created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "✅ Vault setup completed!"
echo ""
echo "🎯 VAULT CONFIGURATION:"
echo "   Address: https://127.0.0.1:8200"
echo "   Root Token: $VAULT_DEV_ROOT_TOKEN"
echo "   Role ID: $ROLE_ID"
echo "   Secret ID: $SECRET_ID"
echo ""
echo "📁 Files created:"
echo "   - .env.vault (environment variables)"
echo "   - vault-credentials.json (API credentials)"
echo ""
echo "🔧 To use with THE OVERMIND PROTOCOL:"
echo "   source .env.vault"
echo "   cargo run"
echo ""
echo "🛑 To stop Vault:"
echo "   kill $VAULT_PID"
echo ""
echo "📋 Test Vault access:"
echo "   vault kv list overmind-secrets/wallets"

# Save PID for cleanup
echo "$VAULT_PID" > vault.pid

echo "🎉 THE OVERMIND PROTOCOL Vault setup complete!"
