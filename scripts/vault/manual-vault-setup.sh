#!/bin/bash

# THE OVERMIND PROTOCOL - Manual Vault Setup
# Step-by-step setup for production server

set -euo pipefail

echo "🔐 THE OVERMIND PROTOCOL - Manual Vault Setup"
echo "============================================="
echo ""
echo "This script will guide you through setting up Vault on your server."
echo "You'll need to run commands manually on the server."
echo ""

SERVER_IP="${1:-89.117.53.53}"
SERVER_USER="${2:-marcin}"

echo "🎯 Target Server: $SERVER_USER@$SERVER_IP"
echo ""

echo "📋 STEP 1: Connect to your server and run these commands:"
echo "========================================================="
echo ""
echo "ssh $SERVER_USER@$SERVER_IP"
echo ""

cat << 'EOF'
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y wget gpg lsb-release curl jq

# Add HashiCorp GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add HashiCorp repository
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Install Vault
sudo apt update && sudo apt install -y vault

# Verify installation
vault version

# Create Vault user and directories
sudo useradd --system --home /etc/vault.d --shell /bin/false vault || true
sudo mkdir -p /opt/vault/{data,logs,config,tls,keys}
sudo mkdir -p /etc/vault.d

# Set permissions
sudo chown -R vault:vault /opt/vault
sudo chmod 750 /opt/vault/data
sudo chmod 750 /opt/vault/keys
sudo chmod 755 /opt/vault/logs

echo "✅ Vault installation completed!"
EOF

echo ""
echo "📋 STEP 2: Generate TLS certificates:"
echo "====================================="
echo ""

cat << EOF
# Generate self-signed certificate for Vault
sudo openssl req -x509 -newkey rsa:4096 -sha256 -days 365 \\
    -nodes -keyout /opt/vault/tls/vault-key.pem \\
    -out /opt/vault/tls/vault-cert.pem \\
    -subj "/CN=$SERVER_IP" \\
    -addext "subjectAltName=DNS:vault.overmind.local,DNS:localhost,IP:$SERVER_IP,IP:127.0.0.1"

# Set proper permissions
sudo chown vault:vault /opt/vault/tls/*
sudo chmod 600 /opt/vault/tls/vault-key.pem
sudo chmod 644 /opt/vault/tls/vault-cert.pem

echo "✅ TLS certificates generated!"
EOF

echo ""
echo "📋 STEP 3: Create Vault configuration:"
echo "======================================"
echo ""

cat << 'EOF'
# Create Vault configuration file
sudo tee /etc/vault.d/vault.hcl > /dev/null << 'VAULT_CONFIG'
# THE OVERMIND PROTOCOL - Vault Configuration

# Storage backend
storage "file" {
  path = "/opt/vault/data"
}

# HTTPS listener
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/opt/vault/tls/vault-cert.pem"
  tls_key_file  = "/opt/vault/tls/vault-key.pem"
}

# API address
api_addr = "https://0.0.0.0:8200"
cluster_addr = "https://0.0.0.0:8201"

# Disable mlock for development (remove in production)
disable_mlock = true

# UI
ui = true

# Logging
log_level = "INFO"
log_file = "/opt/vault/logs/vault.log"
log_rotate_duration = "24h"
log_rotate_max_files = 30

# Performance
default_lease_ttl = "768h"
max_lease_ttl = "8760h"
VAULT_CONFIG

# Set proper permissions
sudo chown vault:vault /etc/vault.d/vault.hcl
sudo chmod 640 /etc/vault.d/vault.hcl

echo "✅ Vault configuration created!"
EOF

echo ""
echo "📋 STEP 4: Create systemd service:"
echo "=================================="
echo ""

cat << 'EOF'
# Create systemd service
sudo tee /etc/systemd/system/vault.service > /dev/null << 'SERVICE_CONFIG'
[Unit]
Description=HashiCorp Vault
Documentation=https://www.vaultproject.io/docs/
Requires=network-online.target
After=network-online.target
ConditionFileNotEmpty=/etc/vault.d/vault.hcl
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=notify
User=vault
Group=vault
ProtectSystem=full
ProtectHome=read-only
PrivateTmp=yes
PrivateDevices=yes
SecureBits=keep-caps
AmbientCapabilities=CAP_IPC_LOCK
CapabilityBoundingSet=CAP_SYSLOG CAP_IPC_LOCK
NoNewPrivileges=yes
ExecStart=/usr/bin/vault server -config=/etc/vault.d/vault.hcl
ExecReload=/bin/kill --signal HUP $MAINPID
KillMode=process
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
StartLimitInterval=60
StartLimitBurst=3
LimitNOFILE=65536
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
SERVICE_CONFIG

# Reload systemd and enable Vault
sudo systemctl daemon-reload
sudo systemctl enable vault
sudo systemctl start vault

# Wait for Vault to start
sleep 5

# Check status
sudo systemctl status vault --no-pager

echo "✅ Vault service started!"
EOF

echo ""
echo "📋 STEP 5: Initialize and configure Vault:"
echo "=========================================="
echo ""

cat << EOF
# Set environment variables
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_SKIP_VERIFY="true"

# Wait for Vault to be ready
until vault status >/dev/null 2>&1 || [ \\\$? -eq 2 ]; do
    echo "Waiting for Vault to be ready..."
    sleep 2
done

# Initialize Vault
vault operator init -key-shares=5 -key-threshold=3 -format=json > /opt/vault/keys/vault-init.json

# Set proper permissions
sudo chown vault:vault /opt/vault/keys/vault-init.json
sudo chmod 600 /opt/vault/keys/vault-init.json

# Extract unseal keys and root token
UNSEAL_KEYS=\$(jq -r '.unseal_keys_b64[]' /opt/vault/keys/vault-init.json)
ROOT_TOKEN=\$(jq -r '.root_token' /opt/vault/keys/vault-init.json)

# Unseal with first 3 keys
count=0
for key in \$UNSEAL_KEYS; do
    if [ \$count -lt 3 ]; then
        vault operator unseal "\$key"
        ((count++))
    fi
done

# Login with root token
vault auth "\$ROOT_TOKEN"

echo "✅ Vault initialized and unsealed!"
echo "Root Token: \$ROOT_TOKEN"
EOF

echo ""
echo "📋 STEP 6: Configure for THE OVERMIND PROTOCOL:"
echo "==============================================="
echo ""

cat << 'EOF'
# Enable KV secrets engine v2
vault secrets enable -path=overmind-secrets kv-v2

# Enable Transit engine for encryption
vault secrets enable transit

# Create encryption key
vault write -f transit/keys/overmind-encryption

# Enable AppRole auth method
vault auth enable approle

# Create trading policy
tee /tmp/trading-policy.hcl > /dev/null << 'POLICY'
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
POLICY

vault policy write trading-policy /tmp/trading-policy.hcl

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

# Create configuration file
tee /tmp/vault-config.json > /dev/null << CONFIG
{
  "vault_addr": "https://$SERVER_IP:8200",
  "root_token": "$ROOT_TOKEN",
  "role_id": "$ROLE_ID",
  "secret_id": "$SECRET_ID",
  "mount_path": "overmind-secrets",
  "production_mode": true,
  "server_ip": "$SERVER_IP"
}
CONFIG

echo "✅ THE OVERMIND PROTOCOL configuration completed!"
echo ""
echo "🎯 VAULT CONFIGURATION:"
echo "   Address: https://$SERVER_IP:8200"
echo "   Root Token: $ROOT_TOKEN"
echo "   Role ID: $ROLE_ID"
echo "   Secret ID: $SECRET_ID"
echo ""
echo "📁 Configuration saved to: /tmp/vault-config.json"
EOF

echo ""
echo "📋 STEP 7: Test the setup:"
echo "========================="
echo ""

cat << 'EOF'
# Test Vault status
vault status

# Test secret storage
vault kv put overmind-secrets/test-wallet \
    private_key="test_key_12345" \
    address="test_address_67890" \
    balance_sol=1.0

# Test secret retrieval
vault kv get overmind-secrets/test-wallet

# Test AppRole authentication
vault write auth/approle/login \
    role_id="$ROLE_ID" \
    secret_id="$SECRET_ID"

echo "✅ Vault setup verification completed!"
EOF

echo ""
echo "🎉 MANUAL SETUP GUIDE COMPLETE!"
echo ""
echo "📋 Next steps after server setup:"
echo "1. Copy /tmp/vault-config.json from server to local machine"
echo "2. Run: ./scripts/vault/migrate-wallets.sh"
echo "3. Configure THE OVERMIND PROTOCOL with Vault credentials"
echo ""
echo "🚀 Ready to start secure trading with THE OVERMIND PROTOCOL!"
