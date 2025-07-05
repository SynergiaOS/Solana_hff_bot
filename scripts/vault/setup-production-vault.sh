#!/bin/bash

# THE OVERMIND PROTOCOL - Production Vault Setup
# Setup for server deployment (89.117.53.53)

set -euo pipefail

SERVER_IP="${1:-89.117.53.53}"
SERVER_USER="${2:-marcin}"

echo "🔐 THE OVERMIND PROTOCOL - Production Vault Setup"
echo "================================================="
echo "Target Server: $SERVER_USER@$SERVER_IP"

# Check if we can connect to server
if ! ssh -o ConnectTimeout=5 "$SERVER_USER@$SERVER_IP" "echo 'Connection test successful'"; then
    echo "❌ Cannot connect to server $SERVER_USER@$SERVER_IP"
    echo "   Please check SSH connection and try again"
    exit 1
fi

echo "✅ Server connection verified"

echo "📦 Installing Vault on server..."

# Install Vault on server
ssh "$SERVER_USER@$SERVER_IP" << 'REMOTE_SCRIPT'
# Update system
sudo apt update

# Install required packages
sudo apt install -y wget gpg lsb-release

# Add HashiCorp GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add HashiCorp repository
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Install Vault
sudo apt update && sudo apt install -y vault

# Verify installation
vault version

echo "✅ Vault installed successfully"
REMOTE_SCRIPT

echo "📁 Creating Vault directories on server..."

# Create necessary directories
ssh "$SERVER_USER@$SERVER_IP" << 'REMOTE_SCRIPT'
# Create Vault directories
sudo mkdir -p /opt/vault/{data,logs,config,tls,keys}
sudo mkdir -p /etc/vault.d

# Set permissions
sudo chown -R vault:vault /opt/vault
sudo chmod 750 /opt/vault/data
sudo chmod 750 /opt/vault/keys
sudo chmod 755 /opt/vault/logs
REMOTE_SCRIPT

echo "🔐 Generating TLS certificates..."

# Generate TLS certificates on server
ssh "$SERVER_USER@$SERVER_IP" << REMOTE_SCRIPT
# Generate self-signed certificate for Vault
sudo openssl req -x509 -newkey rsa:4096 -sha256 -days 365 \
    -nodes -keyout /opt/vault/tls/vault-key.pem \
    -out /opt/vault/tls/vault-cert.pem \
    -subj "/CN=$SERVER_IP" \
    -addext "subjectAltName=DNS:vault.overmind.local,DNS:localhost,IP:$SERVER_IP,IP:127.0.0.1"

# Set proper permissions
sudo chown vault:vault /opt/vault/tls/*
sudo chmod 600 /opt/vault/tls/vault-key.pem
sudo chmod 644 /opt/vault/tls/vault-cert.pem

echo "✅ TLS certificates generated"
REMOTE_SCRIPT

echo "⚙️ Uploading Vault configuration..."

# Upload Vault configuration
scp config/vault/vault-config.hcl "$SERVER_USER@$SERVER_IP:/tmp/vault-config.hcl"

# Move config to proper location and set permissions
ssh "$SERVER_USER@$SERVER_IP" << 'REMOTE_SCRIPT'
sudo mv /tmp/vault-config.hcl /etc/vault.d/vault.hcl
sudo chown vault:vault /etc/vault.d/vault.hcl
sudo chmod 640 /etc/vault.d/vault.hcl
REMOTE_SCRIPT

echo "🔧 Creating Vault systemd service..."

# Create systemd service
ssh "$SERVER_USER@$SERVER_IP" << 'REMOTE_SCRIPT'
sudo tee /etc/systemd/system/vault.service > /dev/null << 'EOF'
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
EOF

# Reload systemd and enable Vault
sudo systemctl daemon-reload
sudo systemctl enable vault

echo "✅ Vault service created and enabled"
REMOTE_SCRIPT

echo "🚀 Starting Vault service..."

# Start Vault
ssh "$SERVER_USER@$SERVER_IP" << 'REMOTE_SCRIPT'
sudo systemctl start vault

# Wait for Vault to start
sleep 5

# Check status
sudo systemctl status vault --no-pager
REMOTE_SCRIPT

echo "🔧 Initializing Vault..."

# Initialize Vault
ssh "$SERVER_USER@$SERVER_IP" << REMOTE_SCRIPT
# Set environment variables
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_SKIP_VERIFY="true"

# Wait for Vault to be ready
until vault status >/dev/null 2>&1 || [ \$? -eq 2 ]; do
    echo "Waiting for Vault to be ready..."
    sleep 2
done

# Initialize Vault
vault operator init -key-shares=5 -key-threshold=3 -format=json > /opt/vault/keys/vault-init.json

# Set proper permissions
sudo chown vault:vault /opt/vault/keys/vault-init.json
sudo chmod 600 /opt/vault/keys/vault-init.json

echo "✅ Vault initialized"
REMOTE_SCRIPT

echo "🔓 Unsealing Vault..."

# Unseal Vault
ssh "$SERVER_USER@$SERVER_IP" << 'REMOTE_SCRIPT'
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_SKIP_VERIFY="true"

# Extract unseal keys
UNSEAL_KEYS=$(jq -r '.unseal_keys_b64[]' /opt/vault/keys/vault-init.json)
ROOT_TOKEN=$(jq -r '.root_token' /opt/vault/keys/vault-init.json)

# Unseal with first 3 keys
count=0
for key in $UNSEAL_KEYS; do
    if [ $count -lt 3 ]; then
        vault operator unseal "$key"
        ((count++))
    fi
done

echo "✅ Vault unsealed"

# Login with root token
vault auth "$ROOT_TOKEN"

echo "✅ Authenticated with root token"
REMOTE_SCRIPT

echo "⚙️ Configuring Vault for THE OVERMIND PROTOCOL..."

# Upload and run initialization script
scp scripts/vault/init-vault.sh "$SERVER_USER@$SERVER_IP:/tmp/init-vault.sh"

ssh "$SERVER_USER@$SERVER_IP" << 'REMOTE_SCRIPT'
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_SKIP_VERIFY="true"

# Get root token
ROOT_TOKEN=$(jq -r '.root_token' /opt/vault/keys/vault-init.json)
export VAULT_TOKEN="$ROOT_TOKEN"

# Run initialization script
chmod +x /tmp/init-vault.sh
/tmp/init-vault.sh

echo "✅ Vault configured for THE OVERMIND PROTOCOL"
REMOTE_SCRIPT

echo "📋 Retrieving configuration..."

# Get configuration from server
ssh "$SERVER_USER@$SERVER_IP" << 'REMOTE_SCRIPT'
export VAULT_ADDR="https://127.0.0.1:8200"
export VAULT_SKIP_VERIFY="true"

# Get credentials
ROOT_TOKEN=$(jq -r '.root_token' /opt/vault/keys/vault-init.json)
ROLE_ID=$(VAULT_TOKEN="$ROOT_TOKEN" vault read -field=role_id auth/approle/role/overmind-trading/role-id)
SECRET_ID=$(VAULT_TOKEN="$ROOT_TOKEN" vault write -field=secret_id -f auth/approle/role/overmind-trading/secret-id)

# Create production config
cat > /tmp/vault-production-config.json << EOF
{
  "vault_addr": "https://$SERVER_IP:8200",
  "root_token": "$ROOT_TOKEN",
  "role_id": "$ROLE_ID",
  "secret_id": "$SECRET_ID",
  "mount_path": "overmind-secrets",
  "production_mode": true,
  "server_ip": "$SERVER_IP"
}
EOF

echo "Configuration saved to /tmp/vault-production-config.json"
REMOTE_SCRIPT

# Download configuration
scp "$SERVER_USER@$SERVER_IP:/tmp/vault-production-config.json" ./vault-production-config.json

echo "✅ Production Vault setup completed!"
echo ""
echo "🎯 PRODUCTION VAULT CONFIGURATION:"
echo "   Server: $SERVER_IP:8200"
echo "   Config: ./vault-production-config.json"
echo ""
echo "🔧 To use with THE OVERMIND PROTOCOL:"
echo "   export VAULT_ADDR=https://$SERVER_IP:8200"
echo "   export VAULT_SKIP_VERIFY=true"
echo "   # Use credentials from vault-production-config.json"
echo ""
echo "📋 Next steps:"
echo "   1. Migrate wallets: ./scripts/vault/migrate-wallets.sh"
echo "   2. Test connection: vault status"
echo "   3. Deploy THE OVERMIND PROTOCOL with Vault integration"
echo ""
echo "⚠️  IMPORTANT SECURITY:"
echo "   - Secure the vault-init.json file on server"
echo "   - Store unseal keys in separate secure locations"
echo "   - Consider setting up auto-unseal for production"
echo ""
echo "🎉 Production Vault ready for THE OVERMIND PROTOCOL!"
