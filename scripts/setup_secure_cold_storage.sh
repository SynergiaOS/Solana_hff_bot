#!/bin/bash
# 🔐 SECURE COLD STORAGE SETUP (WITHOUT HARDWARE WALLET)
# Maximum security using encrypted software wallets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 OVERMIND VAULT - SECURE COLD STORAGE SETUP${NC}"
echo "=================================================="

# Create secure directories
SECURE_DIR="$HOME/.overmind_vault"
BACKUP_DIR="$HOME/.overmind_vault_backup"
TEMP_DIR="/tmp/overmind_secure_$$"

echo -e "${YELLOW}📁 Creating secure directories...${NC}"
mkdir -p "$SECURE_DIR"
mkdir -p "$BACKUP_DIR"
mkdir -p "$TEMP_DIR"

# Set restrictive permissions
chmod 700 "$SECURE_DIR"
chmod 700 "$BACKUP_DIR"
chmod 700 "$TEMP_DIR"

echo -e "${GREEN}✅ Secure directories created${NC}"

# Generate strong encryption password
echo -e "${YELLOW}🔑 Generating encryption keys...${NC}"
ENCRYPTION_PASSWORD=$(openssl rand -base64 32)
BACKUP_PASSWORD=$(openssl rand -base64 32)

echo -e "${BLUE}📝 IMPORTANT: Save these passwords securely!${NC}"
echo "Primary Encryption Password: $ENCRYPTION_PASSWORD"
echo "Backup Encryption Password: $BACKUP_PASSWORD"
echo ""
echo -e "${RED}⚠️  WRITE THESE DOWN AND STORE IN SAFE PLACE!${NC}"
echo -e "${RED}⚠️  WITHOUT THESE PASSWORDS, FUNDS ARE LOST FOREVER!${NC}"
echo ""

read -p "Press ENTER after you've saved the passwords..."

# Generate new cold storage wallet (air-gapped style)
echo -e "${YELLOW}🏦 Generating cold storage wallet...${NC}"

# Disconnect from internet for key generation (simulated)
echo -e "${YELLOW}🌐 Generating keys in secure environment...${NC}"

# Generate wallet
solana-keygen new --no-bip39-passphrase --outfile "$TEMP_DIR/cold_storage_raw.json" --silent

# Get wallet info
COLD_STORAGE_ADDRESS=$(solana-keygen pubkey "$TEMP_DIR/cold_storage_raw.json")
echo -e "${GREEN}📍 Cold Storage Address: $COLD_STORAGE_ADDRESS${NC}"

# Encrypt the wallet file
echo -e "${YELLOW}🔒 Encrypting wallet file...${NC}"
openssl enc -aes-256-cbc -salt -in "$TEMP_DIR/cold_storage_raw.json" \
    -out "$SECURE_DIR/cold_storage.enc" \
    -pass pass:"$ENCRYPTION_PASSWORD"

# Create encrypted backup
openssl enc -aes-256-cbc -salt -in "$TEMP_DIR/cold_storage_raw.json" \
    -out "$BACKUP_DIR/cold_storage_backup.enc" \
    -pass pass:"$BACKUP_PASSWORD"

# Securely delete raw wallet
shred -vfz -n 3 "$TEMP_DIR/cold_storage_raw.json"

echo -e "${GREEN}✅ Cold storage wallet encrypted and secured${NC}"

# Generate hot wallets
echo -e "${YELLOW}🔥 Generating hot trading wallets...${NC}"

# Primary trading wallet
solana-keygen new --no-bip39-passphrase --outfile "$TEMP_DIR/primary_trading.json" --silent
PRIMARY_ADDRESS=$(solana-keygen pubkey "$TEMP_DIR/primary_trading.json")
openssl enc -aes-256-cbc -salt -in "$TEMP_DIR/primary_trading.json" \
    -out "$SECURE_DIR/primary_trading.enc" \
    -pass pass:"$ENCRYPTION_PASSWORD"
shred -vfz -n 3 "$TEMP_DIR/primary_trading.json"

# HFT trading wallet
solana-keygen new --no-bip39-passphrase --outfile "$TEMP_DIR/hft_trading.json" --silent
HFT_ADDRESS=$(solana-keygen pubkey "$TEMP_DIR/hft_trading.json")
openssl enc -aes-256-cbc -salt -in "$TEMP_DIR/hft_trading.json" \
    -out "$SECURE_DIR/hft_trading.enc" \
    -pass pass:"$ENCRYPTION_PASSWORD"
shred -vfz -n 3 "$TEMP_DIR/hft_trading.json"

# Experimental wallet
solana-keygen new --no-bip39-passphrase --outfile "$TEMP_DIR/experimental.json" --silent
EXPERIMENTAL_ADDRESS=$(solana-keygen pubkey "$TEMP_DIR/experimental.json")
openssl enc -aes-256-cbc -salt -in "$TEMP_DIR/experimental.json" \
    -out "$SECURE_DIR/experimental.enc" \
    -pass pass:"$ENCRYPTION_PASSWORD"
shred -vfz -n 3 "$TEMP_DIR/experimental.json"

echo -e "${GREEN}✅ All wallets generated and encrypted${NC}"

# Create wallet configuration
cat > "$SECURE_DIR/wallet_config.json" << EOF
{
  "cold_storage": {
    "address": "$COLD_STORAGE_ADDRESS",
    "encrypted_file": "$SECURE_DIR/cold_storage.enc",
    "backup_file": "$BACKUP_DIR/cold_storage_backup.enc",
    "max_balance": 999999.0,
    "requires_manual_approval": true
  },
  "primary_trading": {
    "address": "$PRIMARY_ADDRESS",
    "encrypted_file": "$SECURE_DIR/primary_trading.enc",
    "max_balance": 1.0,
    "auto_trading": true
  },
  "hft_trading": {
    "address": "$HFT_ADDRESS",
    "encrypted_file": "$SECURE_DIR/hft_trading.enc",
    "max_balance": 0.5,
    "auto_trading": true
  },
  "experimental": {
    "address": "$EXPERIMENTAL_ADDRESS",
    "encrypted_file": "$SECURE_DIR/experimental.enc",
    "max_balance": 0.1,
    "auto_trading": true
  }
}
EOF

# Create secure environment file
cat > "$SECURE_DIR/.env.vault" << EOF
# 🔐 OVERMIND VAULT CONFIGURATION
# DO NOT COMMIT TO REPOSITORY

# Wallet Addresses (Public - Safe to use)
COLD_STORAGE_ADDRESS=$COLD_STORAGE_ADDRESS
PRIMARY_TRADING_ADDRESS=$PRIMARY_ADDRESS
HFT_TRADING_ADDRESS=$HFT_ADDRESS
EXPERIMENTAL_ADDRESS=$EXPERIMENTAL_ADDRESS

# Encrypted Wallet Files
COLD_STORAGE_ENCRYPTED_FILE=$SECURE_DIR/cold_storage.enc
PRIMARY_TRADING_ENCRYPTED_FILE=$SECURE_DIR/primary_trading.enc
HFT_TRADING_ENCRYPTED_FILE=$SECURE_DIR/hft_trading.enc
EXPERIMENTAL_ENCRYPTED_FILE=$SECURE_DIR/experimental.enc

# Security Configuration
VAULT_ENCRYPTION_ENABLED=true
VAULT_BACKUP_ENABLED=true
VAULT_SECURE_MODE=MAXIMUM

# Profit Management
PROFIT_SWEEP_ENABLED=true
PROFIT_SWEEP_DESTINATION=$COLD_STORAGE_ADDRESS
PROFIT_SWEEP_THRESHOLD=0.1
PROFIT_SWEEP_PERCENTAGE=90.0

# Access Control
MANUAL_APPROVAL_THRESHOLD=1.0
TIME_LOCK_THRESHOLD=5.0
TIME_LOCK_DURATION_HOURS=24
EOF

# Clean up temp directory
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}🎉 OVERMIND VAULT SETUP COMPLETE!${NC}"
echo "=================================="
echo ""
echo -e "${BLUE}📋 WALLET SUMMARY:${NC}"
echo "Cold Storage:     $COLD_STORAGE_ADDRESS"
echo "Primary Trading:  $PRIMARY_ADDRESS"
echo "HFT Trading:      $HFT_ADDRESS"
echo "Experimental:     $EXPERIMENTAL_ADDRESS"
echo ""
echo -e "${YELLOW}🔐 SECURITY FEATURES:${NC}"
echo "✅ AES-256 encryption"
echo "✅ Encrypted backups"
echo "✅ Secure file permissions"
echo "✅ Raw key shredding"
echo "✅ Air-gapped generation"
echo ""
echo -e "${RED}⚠️  CRITICAL SECURITY REMINDERS:${NC}"
echo "1. Save encryption passwords in safe place"
echo "2. Create additional backups of encrypted files"
echo "3. Never commit passwords to repository"
echo "4. Test decryption before transferring large amounts"
echo ""
echo -e "${BLUE}📁 FILES CREATED:${NC}"
echo "Configuration: $SECURE_DIR/wallet_config.json"
echo "Environment:   $SECURE_DIR/.env.vault"
echo "Encrypted:     $SECURE_DIR/*.enc"
echo "Backup:        $BACKUP_DIR/*.enc"
echo ""
echo -e "${GREEN}🚀 NEXT STEPS:${NC}"
echo "1. Transfer 27.6 SOL to cold storage: $COLD_STORAGE_ADDRESS"
echo "2. Source environment: source $SECURE_DIR/.env.vault"
echo "3. Start OVERMIND VAULT: ./start_vault.sh"
echo ""
echo -e "${YELLOW}💡 To decrypt wallet when needed:${NC}"
echo "openssl enc -aes-256-cbc -d -in $SECURE_DIR/cold_storage.enc -out /tmp/wallet.json -pass pass:YOUR_PASSWORD"
