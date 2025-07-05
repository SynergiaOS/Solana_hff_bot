#!/bin/bash

# THE OVERMIND PROTOCOL - Vault Initialization Script
# Secure setup for multi-wallet management

set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-https://vault:8200}"
VAULT_KEYS_DIR="/vault/keys"
INIT_FILE="${VAULT_KEYS_DIR}/vault-init.json"

echo "🔐 THE OVERMIND PROTOCOL - Vault Initialization"
echo "================================================"

# Wait for Vault to be ready
echo "⏳ Waiting for Vault to be ready..."
until vault status >/dev/null 2>&1 || [ $? -eq 2 ]; do
    echo "   Vault not ready, waiting 5 seconds..."
    sleep 5
done

# Check if Vault is already initialized
if vault status | grep -q "Initialized.*true"; then
    echo "✅ Vault is already initialized"
    
    # Check if unsealed
    if vault status | grep -q "Sealed.*false"; then
        echo "✅ Vault is already unsealed"
        exit 0
    else
        echo "🔓 Vault is sealed, attempting to unseal..."
        if [ -f "$INIT_FILE" ]; then
            UNSEAL_KEYS=$(jq -r '.unseal_keys_b64[]' "$INIT_FILE")
            for key in $UNSEAL_KEYS; do
                vault operator unseal "$key" || true
            done
            echo "✅ Vault unsealed successfully"
        else
            echo "❌ No unseal keys found. Manual intervention required."
            exit 1
        fi
    fi
    exit 0
fi

echo "🚀 Initializing Vault..."

# Initialize Vault
vault operator init \
    -key-shares=5 \
    -key-threshold=3 \
    -format=json > "$INIT_FILE"

echo "✅ Vault initialized successfully"

# Extract unseal keys and root token
UNSEAL_KEYS=$(jq -r '.unseal_keys_b64[]' "$INIT_FILE")
ROOT_TOKEN=$(jq -r '.root_token' "$INIT_FILE")

echo "🔓 Unsealing Vault..."

# Unseal Vault (need 3 out of 5 keys)
count=0
for key in $UNSEAL_KEYS; do
    if [ $count -lt 3 ]; then
        vault operator unseal "$key"
        ((count++))
    fi
done

echo "✅ Vault unsealed successfully"

# Login with root token
vault auth "$ROOT_TOKEN"

echo "⚙️ Configuring Vault for THE OVERMIND PROTOCOL..."

# Enable KV secrets engine v2 for wallets
vault secrets enable -path=overmind-secrets kv-v2

# Enable Transit engine for encryption
vault secrets enable transit

# Create encryption key for sensitive data
vault write -f transit/keys/overmind-encryption

# Enable AppRole auth method
vault auth enable approle

# Create policies
echo "📋 Creating Vault policies..."

# Trading policy - read access to wallets
cat > /tmp/trading-policy.hcl << 'EOF'
# THE OVERMIND PROTOCOL - Trading Policy
# Read access to wallet secrets

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

# Admin policy - full access
cat > /tmp/admin-policy.hcl << 'EOF'
# THE OVERMIND PROTOCOL - Admin Policy
# Full access to all secrets and configuration

path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
EOF

vault policy write admin-policy /tmp/admin-policy.hcl

# Emergency policy - emergency access only
cat > /tmp/emergency-policy.hcl << 'EOF'
# THE OVERMIND PROTOCOL - Emergency Policy
# Emergency access to critical wallets

path "overmind-secrets/data/wallets/main-trading-28sol" {
  capabilities = ["read"]
}

path "overmind-secrets/data/wallets/emergency-*" {
  capabilities = ["read", "create", "update"]
}

path "transit/decrypt/overmind-encryption" {
  capabilities = ["update"]
}
EOF

vault policy write emergency-policy /tmp/emergency-policy.hcl

echo "🎭 Creating AppRole for trading bot..."

# Create AppRole for trading bot
vault write auth/approle/role/overmind-trading \
    token_policies="trading-policy" \
    token_ttl=1h \
    token_max_ttl=4h \
    bind_secret_id=true \
    secret_id_ttl=24h

# Get Role ID and Secret ID
ROLE_ID=$(vault read -field=role_id auth/approle/role/overmind-trading/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/overmind-trading/secret-id)

# Save credentials for the application
cat > "${VAULT_KEYS_DIR}/overmind-credentials.json" << EOF
{
  "role_id": "$ROLE_ID",
  "secret_id": "$SECRET_ID",
  "vault_addr": "$VAULT_ADDR",
  "mount_path": "overmind-secrets"
}
EOF

echo "🔐 Creating sample wallet secrets..."

# Create sample wallet structure (will be replaced with real wallets)
vault kv put overmind-secrets/wallets/main-trading-28sol \
    private_key="SAMPLE_KEY_WILL_BE_REPLACED" \
    address="SAMPLE_ADDRESS" \
    balance_sol=28.0 \
    security_level="MAXIMUM" \
    created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

vault kv put overmind-secrets/wallets/arbitrage-wallet \
    private_key="SAMPLE_KEY_WILL_BE_REPLACED" \
    address="SAMPLE_ADDRESS" \
    balance_sol=5.0 \
    security_level="HIGH" \
    created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "📊 Setting up audit logging..."

# Enable file audit device
vault audit enable file file_path=/vault/logs/audit.log

echo "🎉 THE OVERMIND PROTOCOL Vault setup completed!"
echo "================================================"
echo ""
echo "🔑 IMPORTANT SECURITY INFORMATION:"
echo "   - Root token and unseal keys saved to: $INIT_FILE"
echo "   - AppRole credentials saved to: ${VAULT_KEYS_DIR}/overmind-credentials.json"
echo "   - Audit logs will be written to: /vault/logs/audit.log"
echo ""
echo "⚠️  CRITICAL: Secure the unseal keys and root token immediately!"
echo "   - Store unseal keys in separate secure locations"
echo "   - Revoke root token after setup is complete"
echo "   - Enable auto-unseal for production use"
echo ""
echo "🚀 Vault is ready for THE OVERMIND PROTOCOL!"

# Set proper permissions
chmod 600 "$INIT_FILE"
chmod 600 "${VAULT_KEYS_DIR}/overmind-credentials.json"

echo "✅ Vault initialization completed successfully"
