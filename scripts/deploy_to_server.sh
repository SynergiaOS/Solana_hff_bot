#!/bin/bash
# 🚀 DEPLOY OVERMIND VAULT TO SERVER
# Complete deployment with password management

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Server configuration
SERVER_USER="marcin"
SERVER_HOST="89.117.53.53"
SERVER_PATH="/home/marcin/windsurf/Projects/LastBot"

echo -e "${BLUE}🚀 DEPLOYING OVERMIND VAULT TO SERVER${NC}"
echo "====================================="

# Check if we have the master keys file
if [ ! -f "OVERMIND_VAULT_MASTER_KEYS.txt" ]; then
    echo -e "${RED}❌ Master keys file not found${NC}"
    echo "Run setup_secure_cold_storage.sh first"
    exit 1
fi

echo -e "${YELLOW}📋 Pre-deployment checklist:${NC}"
echo "1. ✅ Master keys file exists"
echo "2. ⚠️  Ensure you have saved passwords offline"
echo "3. ⚠️  Verify server SSH access"
echo "4. ⚠️  Confirm server has required dependencies"

read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Create deployment package
echo -e "${YELLOW}📦 Creating deployment package...${NC}"
DEPLOY_DIR="overmind_vault_deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"

# Copy necessary files (NO PRIVATE KEYS)
cp -r src/ "$DEPLOY_DIR/"
cp -r scripts/ "$DEPLOY_DIR/"
cp -r config/ "$DEPLOY_DIR/"
cp -r docs/ "$DEPLOY_DIR/"
cp Cargo.toml "$DEPLOY_DIR/"
cp Cargo.lock "$DEPLOY_DIR/"
cp README.md "$DEPLOY_DIR/"

# Copy encrypted vault files if they exist
if [ -d "$HOME/.overmind_vault" ]; then
    echo -e "${YELLOW}📁 Copying encrypted vault files...${NC}"
    mkdir -p "$DEPLOY_DIR/.overmind_vault"
    cp "$HOME/.overmind_vault"/*.enc "$DEPLOY_DIR/.overmind_vault/" 2>/dev/null || true
    cp "$HOME/.overmind_vault"/*.json "$DEPLOY_DIR/.overmind_vault/" 2>/dev/null || true
    cp "$HOME/.overmind_vault/.env.vault" "$DEPLOY_DIR/.overmind_vault/" 2>/dev/null || true
fi

# Copy backup files
if [ -d "$HOME/.overmind_vault_backup" ]; then
    echo -e "${YELLOW}💾 Copying backup files...${NC}"
    mkdir -p "$DEPLOY_DIR/.overmind_vault_backup"
    cp "$HOME/.overmind_vault_backup"/*.enc "$DEPLOY_DIR/.overmind_vault_backup/" 2>/dev/null || true
fi

# Create server-specific configuration
echo -e "${YELLOW}⚙️ Creating server configuration...${NC}"

cat > "$DEPLOY_DIR/server_setup.sh" << 'EOF'
#!/bin/bash
# Server setup script for OVERMIND VAULT

echo "🔧 Setting up OVERMIND VAULT on server..."

# Install dependencies
sudo apt update
sudo apt install -y openssl bc curl

# Install Rust if not present
if ! command -v cargo &> /dev/null; then
    echo "📦 Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
fi

# Install Solana CLI if not present
if ! command -v solana &> /dev/null; then
    echo "📦 Installing Solana CLI..."
    sh -c "$(curl -sSfL https://release.solana.com/v1.18.4/install)"
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
fi

# Set up vault directories with correct permissions
mkdir -p ~/.overmind_vault
mkdir -p ~/.overmind_vault_backup
chmod 700 ~/.overmind_vault
chmod 700 ~/.overmind_vault_backup

# Copy vault files if they exist
if [ -d ".overmind_vault" ]; then
    cp .overmind_vault/* ~/.overmind_vault/ 2>/dev/null || true
fi

if [ -d ".overmind_vault_backup" ]; then
    cp .overmind_vault_backup/* ~/.overmind_vault_backup/ 2>/dev/null || true
fi

# Build the project
echo "🔨 Building OVERMIND VAULT..."
cargo build --release

# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py

echo "✅ Server setup complete!"
echo ""
echo "🔑 IMPORTANT: You need to set encryption passwords!"
echo "Run: python3 scripts/secure_wallet_access.py"
EOF

chmod +x "$DEPLOY_DIR/server_setup.sh"

# Create password setup instructions
cat > "$DEPLOY_DIR/PASSWORD_SETUP_INSTRUCTIONS.txt" << EOF
🔐 OVERMIND VAULT - SERVER PASSWORD SETUP
========================================

⚠️  CRITICAL: After deployment, you MUST set encryption passwords!

📋 STEPS TO COMPLETE SETUP:

1. SSH to server:
   ssh $SERVER_USER@$SERVER_HOST

2. Navigate to project:
   cd $SERVER_PATH

3. Run server setup:
   ./server_setup.sh

4. Set encryption passwords:
   You have two options:

   OPTION A: Use existing passwords (if you have them)
   - Copy your saved passwords from OVERMIND_VAULT_MASTER_KEYS.txt
   - Use them when prompted by secure_wallet_access.py

   OPTION B: Generate new passwords (if starting fresh)
   - Run: ./scripts/setup_secure_cold_storage.sh
   - Save the generated passwords offline
   - Update your OVERMIND_VAULT_MASTER_KEYS.txt file

5. Test wallet access:
   python3 scripts/secure_wallet_access.py

6. Start the vault:
   ./scripts/start_vault.sh

═══════════════════════════════════════════════════

🔑 ENCRYPTION PASSWORDS NEEDED:

Primary Encryption Password: [FROM_YOUR_MASTER_KEYS_FILE]
Backup Encryption Password: [FROM_YOUR_MASTER_KEYS_FILE]

⚠️  These passwords are NOT included in deployment for security!
⚠️  You must enter them manually on the server!

═══════════════════════════════════════════════════

📁 SERVER FILE LOCATIONS:

Encrypted Wallets: ~/.overmind_vault/*.enc
Backup Files: ~/.overmind_vault_backup/*.enc
Configuration: ~/.overmind_vault/wallet_config.json
Logs: ./logs/overmind_vault.log

═══════════════════════════════════════════════════

🚨 SECURITY REMINDERS:

✅ Passwords are NOT stored on server
✅ Only encrypted files are deployed
✅ You control all decryption keys
✅ Server cannot access funds without your passwords
✅ All private keys are encrypted with your passwords

❌ Never store passwords in server files
❌ Never commit passwords to git
❌ Never share passwords via insecure channels
EOF

# Create deployment archive
echo -e "${YELLOW}📦 Creating deployment archive...${NC}"
tar -czf "${DEPLOY_DIR}.tar.gz" "$DEPLOY_DIR"

# Deploy to server
echo -e "${YELLOW}🚀 Deploying to server...${NC}"
echo "Server: $SERVER_USER@$SERVER_HOST"
echo "Path: $SERVER_PATH"

# Copy deployment package
scp "${DEPLOY_DIR}.tar.gz" "$SERVER_USER@$SERVER_HOST:/tmp/"

# Extract and setup on server
ssh "$SERVER_USER@$SERVER_HOST" << EOF
cd "$SERVER_PATH"

# Backup existing installation
if [ -d "overmind_vault_backup" ]; then
    rm -rf "overmind_vault_backup_old"
    mv "overmind_vault_backup" "overmind_vault_backup_old"
fi

# Extract new deployment
cd /tmp
tar -xzf "${DEPLOY_DIR}.tar.gz"
cd "$DEPLOY_DIR"

# Copy files to project directory
cp -r * "$SERVER_PATH/"

# Run server setup
cd "$SERVER_PATH"
./server_setup.sh

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "🔑 NEXT STEPS:"
echo "1. Set encryption passwords"
echo "2. Test wallet access"
echo "3. Start OVERMIND VAULT"
echo ""
echo "📖 Read: PASSWORD_SETUP_INSTRUCTIONS.txt"
EOF

# Cleanup local deployment files
rm -rf "$DEPLOY_DIR"
rm "${DEPLOY_DIR}.tar.gz"

echo ""
echo -e "${GREEN}🎉 DEPLOYMENT SUCCESSFUL!${NC}"
echo "========================="
echo ""
echo -e "${BLUE}📋 DEPLOYMENT SUMMARY:${NC}"
echo "Server: $SERVER_USER@$SERVER_HOST"
echo "Path: $SERVER_PATH"
echo "Status: ✅ Files deployed"
echo "Encrypted wallets: ✅ Copied"
echo "Backup files: ✅ Copied"
echo "Configuration: ✅ Set up"
echo ""
echo -e "${YELLOW}🔑 CRITICAL NEXT STEPS:${NC}"
echo "1. SSH to server: ssh $SERVER_USER@$SERVER_HOST"
echo "2. Read instructions: cat $SERVER_PATH/PASSWORD_SETUP_INSTRUCTIONS.txt"
echo "3. Set encryption passwords (from your offline backup)"
echo "4. Test wallet access"
echo "5. Start OVERMIND VAULT"
echo ""
echo -e "${RED}⚠️  SECURITY REMINDER:${NC}"
echo "Passwords are NOT on server - you must enter them manually!"
echo "Use your saved passwords from OVERMIND_VAULT_MASTER_KEYS.txt"
echo ""
echo -e "${GREEN}🚀 Ready to activate OVERMIND VAULT on server!${NC}"
