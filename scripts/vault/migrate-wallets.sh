#!/bin/bash

# THE OVERMIND PROTOCOL - Wallet Migration to Vault
# Securely migrate existing wallet files to HashiCorp Vault

set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-https://localhost:8200}"
WALLETS_DIR="${WALLETS_DIR:-./wallets}"
VAULT_MOUNT="overmind-secrets"

echo "🔐 THE OVERMIND PROTOCOL - Wallet Migration to Vault"
echo "===================================================="

# Check if Vault is accessible
if ! vault status >/dev/null 2>&1; then
    echo "❌ Vault is not accessible at $VAULT_ADDR"
    echo "   Please ensure Vault is running and you are authenticated"
    exit 1
fi

# Check if authenticated
if ! vault auth -method=token lookup >/dev/null 2>&1; then
    echo "❌ Not authenticated to Vault"
    echo "   Please run: vault auth <token>"
    exit 1
fi

echo "✅ Vault connection verified"

# Check if wallets directory exists
if [ ! -d "$WALLETS_DIR" ]; then
    echo "❌ Wallets directory not found: $WALLETS_DIR"
    exit 1
fi

echo "📁 Found wallets directory: $WALLETS_DIR"

# Create backup of existing wallets
BACKUP_DIR="./wallets-backup-$(date +%Y%m%d-%H%M%S)"
echo "💾 Creating backup: $BACKUP_DIR"
cp -r "$WALLETS_DIR" "$BACKUP_DIR"

# Function to migrate a single wallet
migrate_wallet() {
    local wallet_file="$1"
    local wallet_name=$(basename "$wallet_file" .json)
    
    echo "🔄 Migrating wallet: $wallet_name"
    
    # Read wallet file
    if [ ! -f "$wallet_file" ]; then
        echo "   ⚠️  Wallet file not found: $wallet_file"
        return 1
    fi
    
    # Validate JSON
    if ! jq empty "$wallet_file" 2>/dev/null; then
        echo "   ❌ Invalid JSON in wallet file: $wallet_file"
        return 1
    fi
    
    # Extract wallet data
    local private_key=$(jq -r '.private_key // empty' "$wallet_file")
    local address=$(jq -r '.address // empty' "$wallet_file")
    local balance_sol=$(jq -r '.balance_sol // 0' "$wallet_file")
    local security_level=$(jq -r '.security_level // "medium"' "$wallet_file")
    local created=$(jq -r '.created // .created_at // empty' "$wallet_file")
    
    # Validate required fields
    if [ -z "$private_key" ] || [ -z "$address" ]; then
        echo "   ❌ Missing required fields (private_key, address) in: $wallet_file"
        return 1
    fi
    
    # Set default created date if missing
    if [ -z "$created" ] || [ "$created" = "null" ]; then
        created=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    fi
    
    # Store in Vault
    echo "   📤 Storing in Vault..."
    if vault kv put "$VAULT_MOUNT/wallets/$wallet_name" \
        private_key="$private_key" \
        address="$address" \
        balance_sol="$balance_sol" \
        security_level="$security_level" \
        created_at="$created" \
        migrated_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        source_file="$wallet_file"; then
        
        echo "   ✅ Successfully migrated: $wallet_name"
        
        # Verify the stored data
        if vault kv get -field=address "$VAULT_MOUNT/wallets/$wallet_name" >/dev/null 2>&1; then
            echo "   ✅ Verification successful"
            return 0
        else
            echo "   ❌ Verification failed"
            return 1
        fi
    else
        echo "   ❌ Failed to store in Vault: $wallet_name"
        return 1
    fi
}

# Find and migrate all wallet files
echo "🔍 Scanning for wallet files..."
wallet_files=$(find "$WALLETS_DIR" -name "*.json" -type f | grep -v ".gitkeep" || true)

if [ -z "$wallet_files" ]; then
    echo "❌ No wallet files found in $WALLETS_DIR"
    exit 1
fi

echo "📋 Found wallet files:"
echo "$wallet_files" | sed 's/^/   - /'

# Migration counters
total_wallets=0
successful_migrations=0
failed_migrations=0

# Migrate each wallet
while IFS= read -r wallet_file; do
    if [ -n "$wallet_file" ]; then
        ((total_wallets++))
        if migrate_wallet "$wallet_file"; then
            ((successful_migrations++))
        else
            ((failed_migrations++))
        fi
        echo ""
    fi
done <<< "$wallet_files"

# Migration summary
echo "📊 MIGRATION SUMMARY"
echo "===================="
echo "Total wallets found: $total_wallets"
echo "Successful migrations: $successful_migrations"
echo "Failed migrations: $failed_migrations"
echo ""

if [ $failed_migrations -eq 0 ]; then
    echo "🎉 ALL WALLETS MIGRATED SUCCESSFULLY!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Verify wallets in Vault: vault kv list $VAULT_MOUNT/wallets"
    echo "   2. Test wallet access with your application"
    echo "   3. Update application configuration to use Vault"
    echo "   4. Securely delete original wallet files (after testing)"
    echo ""
    echo "💾 Backup created at: $BACKUP_DIR"
    echo "   Keep this backup until you've verified everything works"
else
    echo "⚠️  SOME MIGRATIONS FAILED"
    echo "   Please review the errors above and retry failed wallets"
    echo "   Original files are preserved for retry"
fi

# List migrated wallets
echo "🔍 Wallets now in Vault:"
vault kv list "$VAULT_MOUNT/wallets" 2>/dev/null | sed 's/^/   - /' || echo "   (Unable to list - check permissions)"

echo ""
echo "✅ Migration process completed"
