# 🔐 THE OVERMIND PROTOCOL - Vault Integration Quick Start

## 🎯 Overview

This guide shows you how to integrate HashiCorp Vault with THE OVERMIND PROTOCOL for secure multi-wallet management.

## 🚀 Quick Start Options

### Option 1: Local Development (5 minutes)

```bash
# 1. Run the setup script
chmod +x scripts/vault/setup-local-vault.sh
./scripts/vault/setup-local-vault.sh

# 2. Load environment variables
source .env.vault

# 3. Test the integration
cargo run
```

### Option 2: Production Server (15 minutes)

```bash
# 1. Setup Vault on production server
chmod +x scripts/vault/setup-production-vault.sh
./scripts/vault/setup-production-vault.sh 89.117.53.53 marcin

# 2. Configure environment
cp .env.vault.example .env.vault
# Edit .env.vault with production values

# 3. Migrate existing wallets
./scripts/vault/migrate-wallets.sh

# 4. Deploy THE OVERMIND PROTOCOL
docker-compose -f config/docker/docker-compose.vault.yml up -d
```

## 📋 Configuration Parameters

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VAULT_ADDR` | Vault server address | `https://127.0.0.1:8200` |
| `VAULT_TOKEN` | Authentication token | `hvs.CAESIF...` |
| `VAULT_MOUNT_PATH` | Secrets engine path | `overmind-secrets` |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `VAULT_SKIP_VERIFY` | Skip TLS verification | `true` (dev only) |
| `VAULT_NAMESPACE` | Vault namespace | `""` (Enterprise only) |
| `VAULT_MODE` | Operation mode | `dev` |

## 🔧 API Integration

### Basic Usage

```rust
use crate::modules::vault_integration::{VaultClient, VaultConfig};

// Create Vault client
let config = VaultConfig {
    vault_url: "https://127.0.0.1:8200".to_string(),
    vault_token: "your-token".to_string(),
    mount_path: "overmind-secrets".to_string(),
    role_id: None,
    secret_id: None,
};

let mut client = VaultClient::new(config);
client.authenticate().await?;

// Get wallet for trading
let wallet = client.get_wallet("main-trading-28sol").await?;
println!("Wallet address: {}", wallet.address);
```

### AppRole Authentication (Production)

```rust
let config = VaultConfig {
    vault_url: "https://89.117.53.53:8200".to_string(),
    vault_token: "".to_string(),  // Will be obtained via AppRole
    mount_path: "overmind-secrets".to_string(),
    role_id: Some("your-role-id".to_string()),
    secret_id: Some("your-secret-id".to_string()),
};
```

## 🔐 Security Features

### Multi-Wallet Management

```bash
# Store different wallet types
vault kv put overmind-secrets/wallets/main-trading-28sol \
    private_key="..." \
    address="4rtY4TCojYn2o86kRjNfETKcBxCWfX39dG4B21y4HYYm" \
    balance_sol=28.028235358 \
    security_level="MAXIMUM"

vault kv put overmind-secrets/wallets/arbitrage-wallet \
    private_key="..." \
    address="..." \
    balance_sol=5.0 \
    security_level="HIGH"
```

### Access Control Policies

```hcl
# Trading bot policy - read-only access to wallets
path "overmind-secrets/data/wallets/*" {
  capabilities = ["read"]
}

# Admin policy - full access
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
```

### Audit Logging

```bash
# Enable audit logging
vault audit enable file file_path=/vault/logs/audit.log

# View audit logs
tail -f /vault/logs/audit.log | jq .
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Connection Refused
```bash
# Check if Vault is running
vault status

# Check network connectivity
curl -k https://127.0.0.1:8200/v1/sys/health
```

#### 2. Authentication Failed
```bash
# Verify token
vault auth -method=token

# Check token info
vault token lookup
```

#### 3. Permission Denied
```bash
# Check current policies
vault token lookup -format=json | jq .data.policies

# Test policy
vault policy read trading-policy
```

### Debug Mode

```bash
# Enable debug logging
export VAULT_LOG_LEVEL=DEBUG
export RUST_LOG=debug

# Run with verbose output
cargo run 2>&1 | grep vault
```

## 📊 Monitoring

### Health Checks

```bash
# Vault server health
curl -k https://127.0.0.1:8200/v1/sys/health

# Seal status
vault status

# List active tokens
vault list auth/token/accessors
```

### Metrics

```bash
# Vault metrics (Prometheus format)
curl -k https://127.0.0.1:8200/v1/sys/metrics

# Custom metrics in THE OVERMIND PROTOCOL
curl http://localhost:8080/metrics | grep vault
```

## 🔄 Backup & Recovery

### Backup Vault Data

```bash
# Backup secrets
vault kv list -format=json overmind-secrets/wallets > wallets-backup.json

# Backup policies
vault policy list | xargs -I {} vault policy read {} > policies-backup.hcl
```

### Disaster Recovery

```bash
# Restore from backup
./scripts/vault/restore-from-backup.sh wallets-backup.json

# Emergency wallet access
vault kv get -field=private_key overmind-secrets/wallets/main-trading-28sol
```

## 🚀 Production Deployment

### Docker Compose

```yaml
# docker-compose.vault.yml
services:
  vault:
    image: hashicorp/vault:1.20.0
    ports:
      - "8200:8200"
    environment:
      VAULT_ADDR: "https://0.0.0.0:8200"
    volumes:
      - vault_data:/vault/data
      - ./config/vault:/vault/config
    command: vault server -config=/vault/config/vault.hcl

  overmind-core:
    build: .
    depends_on:
      - vault
    environment:
      VAULT_ADDR: "https://vault:8200"
      VAULT_ROLE_ID_FILE: "/vault/cache/role-id"
      VAULT_SECRET_ID_FILE: "/vault/cache/secret-id"
```

### Kubernetes Deployment

```yaml
# vault-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: overmind-vault
spec:
  replicas: 1
  selector:
    matchLabels:
      app: overmind-vault
  template:
    metadata:
      labels:
        app: overmind-vault
    spec:
      containers:
      - name: vault
        image: hashicorp/vault:1.20.0
        ports:
        - containerPort: 8200
        env:
        - name: VAULT_ADDR
          value: "https://0.0.0.0:8200"
```

## 📚 Additional Resources

- [HashiCorp Vault Documentation](https://developer.hashicorp.com/vault)
- [Vault API Reference](https://developer.hashicorp.com/vault/api-docs)
- [THE OVERMIND PROTOCOL Security Guide](./SECURITY.md)
- [Multi-Wallet Management Best Practices](./docs/MULTI_WALLET.md)

## 🆘 Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review Vault logs: `journalctl -u vault -f`
3. Check THE OVERMIND PROTOCOL logs: `tail -f logs/overmind.log`
4. Open an issue with detailed error messages

## 🎉 Success!

Once configured, THE OVERMIND PROTOCOL will:

- ✅ Securely store all wallet private keys in Vault
- ✅ Use role-based access control for different operations
- ✅ Maintain complete audit logs of all wallet access
- ✅ Support multiple wallet strategies with different security levels
- ✅ Automatically rotate authentication tokens
- ✅ Provide emergency access procedures

Your trading system is now enterprise-grade secure! 🔐
