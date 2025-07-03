#!/bin/bash
# 🚀 OVERMIND VAULT STARTUP SCRIPT
# Start THE OVERMIND PROTOCOL with maximum security

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 STARTING OVERMIND VAULT${NC}"
echo "=========================="

# Check if vault is initialized
VAULT_DIR="$HOME/.overmind_vault"
if [ ! -d "$VAULT_DIR" ]; then
    echo -e "${RED}❌ Vault not initialized${NC}"
    echo "Run: ./scripts/setup_secure_cold_storage.sh"
    exit 1
fi

# Load vault configuration
if [ -f "$VAULT_DIR/.env.vault" ]; then
    echo -e "${YELLOW}📋 Loading vault configuration...${NC}"
    source "$VAULT_DIR/.env.vault"
    echo -e "${GREEN}✅ Vault configuration loaded${NC}"
else
    echo -e "${RED}❌ Vault configuration not found${NC}"
    exit 1
fi

# Check wallet balances
echo -e "${YELLOW}💰 Checking wallet balances...${NC}"

check_balance() {
    local address=$1
    local name=$2
    local balance=$(solana balance $address --url https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580 2>/dev/null | grep -o '[0-9.]*' | head -1)
    echo -e "${BLUE}$name:${NC} $balance SOL ($address)"
    echo $balance
}

COLD_BALANCE=$(check_balance $COLD_STORAGE_ADDRESS "Cold Storage")
PRIMARY_BALANCE=$(check_balance $PRIMARY_TRADING_ADDRESS "Primary Trading")
HFT_BALANCE=$(check_balance $HFT_TRADING_ADDRESS "HFT Trading")
EXPERIMENTAL_BALANCE=$(check_balance $EXPERIMENTAL_ADDRESS "Experimental")

# Calculate total
TOTAL_BALANCE=$(echo "$COLD_BALANCE + $PRIMARY_BALANCE + $HFT_BALANCE + $EXPERIMENTAL_BALANCE" | bc -l)
TOTAL_USD=$(echo "$TOTAL_BALANCE * 155" | bc -l)

echo ""
echo -e "${GREEN}💎 Total Vault Value: $TOTAL_BALANCE SOL (~\$${TOTAL_USD} USD)${NC}"
echo ""

# Security checks
echo -e "${YELLOW}🔐 Performing security checks...${NC}"

# Check file permissions
if [ "$(stat -c %a $VAULT_DIR)" != "700" ]; then
    echo -e "${RED}⚠️ Fixing vault directory permissions${NC}"
    chmod 700 "$VAULT_DIR"
fi

# Check if encrypted files exist
SECURITY_SCORE=0
if [ -f "$COLD_STORAGE_ENCRYPTED_FILE" ]; then
    SECURITY_SCORE=$((SECURITY_SCORE + 25))
    echo -e "${GREEN}✅ Cold storage encrypted${NC}"
else
    echo -e "${RED}❌ Cold storage not encrypted${NC}"
fi

if [ -f "$PRIMARY_TRADING_ENCRYPTED_FILE" ]; then
    SECURITY_SCORE=$((SECURITY_SCORE + 25))
    echo -e "${GREEN}✅ Primary trading encrypted${NC}"
else
    echo -e "${RED}❌ Primary trading not encrypted${NC}"
fi

if [ -f "$HFT_TRADING_ENCRYPTED_FILE" ]; then
    SECURITY_SCORE=$((SECURITY_SCORE + 25))
    echo -e "${GREEN}✅ HFT trading encrypted${NC}"
else
    echo -e "${RED}❌ HFT trading not encrypted${NC}"
fi

if [ -f "$EXPERIMENTAL_ENCRYPTED_FILE" ]; then
    SECURITY_SCORE=$((SECURITY_SCORE + 25))
    echo -e "${GREEN}✅ Experimental encrypted${NC}"
else
    echo -e "${RED}❌ Experimental not encrypted${NC}"
fi

echo -e "${BLUE}🛡️ Security Score: $SECURITY_SCORE/100${NC}"

if [ $SECURITY_SCORE -lt 100 ]; then
    echo -e "${YELLOW}⚠️ Some security features missing${NC}"
fi

# Check if we need to setup hot wallets
HOT_WALLET_SETUP_NEEDED=false
if (( $(echo "$PRIMARY_BALANCE < 0.1" | bc -l) )); then
    echo -e "${YELLOW}⚠️ Primary trading wallet needs funding${NC}"
    HOT_WALLET_SETUP_NEEDED=true
fi

if (( $(echo "$HFT_BALANCE < 0.05" | bc -l) )); then
    echo -e "${YELLOW}⚠️ HFT trading wallet needs funding${NC}"
    HOT_WALLET_SETUP_NEEDED=true
fi

if [ "$HOT_WALLET_SETUP_NEEDED" = true ]; then
    echo ""
    echo -e "${YELLOW}💡 Hot wallets need funding. Run:${NC}"
    echo "python3 scripts/secure_wallet_access.py"
    echo ""
fi

# Create runtime environment
echo -e "${YELLOW}⚙️ Setting up runtime environment...${NC}"

# Create .env for THE OVERMIND PROTOCOL
cat > .env << EOF
# 🔐 OVERMIND VAULT RUNTIME CONFIGURATION
# Generated automatically - DO NOT EDIT MANUALLY

# Security Mode
OVERMIND_SECURITY_MODE=MAXIMUM
OVERMIND_VAULT_ENABLED=true

# Wallet Addresses (Public)
COLD_STORAGE_ADDRESS=$COLD_STORAGE_ADDRESS
PRIMARY_TRADING_ADDRESS=$PRIMARY_TRADING_ADDRESS
HFT_TRADING_ADDRESS=$HFT_TRADING_ADDRESS
EXPERIMENTAL_ADDRESS=$EXPERIMENTAL_ADDRESS

# Trading Configuration
SNIPER_TRADING_MODE=paper
SNIPER_MAX_POSITION_SIZE=0.1
SNIPER_MAX_DAILY_LOSS=0.5

# Profit Management
PROFIT_WALLET_ADDRESS=$COLD_STORAGE_ADDRESS
PROFIT_TRANSFER_ENABLED=true
PROFIT_TRANSFER_THRESHOLD=0.05
PROFIT_TRANSFER_PERCENTAGE=90.0

# Risk Management
RISK_MAX_POSITION_PERCENTAGE=0.05
RISK_MAX_DAILY_LOSS_PERCENTAGE=0.10
EMERGENCY_STOP_ENABLED=true

# API Configuration
SOLANA_RPC_URL=https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580
SOLANA_WSS_URL=wss://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580

# Monitoring
GRAFANA_ENABLED=true
PROMETHEUS_ENABLED=true
LOGGING_LEVEL=INFO
EOF

echo -e "${GREEN}✅ Runtime environment configured${NC}"

# Start services
echo ""
echo -e "${BLUE}🚀 STARTING OVERMIND VAULT SERVICES${NC}"
echo "=================================="

# Check if we should start in paper or live mode
if (( $(echo "$PRIMARY_BALANCE > 0.5" | bc -l) )) && (( $(echo "$HFT_BALANCE > 0.2" | bc -l) )); then
    echo -e "${GREEN}💰 Sufficient hot wallet balances detected${NC}"
    echo -e "${YELLOW}⚠️ Ready for LIVE TRADING mode${NC}"
    echo ""
    read -p "Start in LIVE trading mode? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sed -i 's/SNIPER_TRADING_MODE=paper/SNIPER_TRADING_MODE=live/' .env
        echo -e "${RED}🔴 LIVE TRADING MODE ACTIVATED${NC}"
    else
        echo -e "${BLUE}📝 Starting in PAPER TRADING mode${NC}"
    fi
else
    echo -e "${BLUE}📝 Starting in PAPER TRADING mode (insufficient hot wallet balances)${NC}"
fi

# Start THE OVERMIND PROTOCOL
echo ""
echo -e "${GREEN}🧠 Starting THE OVERMIND PROTOCOL...${NC}"

# Check if we have the binary
if [ -f "target/release/snipercor" ]; then
    echo -e "${GREEN}✅ Using optimized release binary${NC}"
    BINARY="target/release/snipercor"
elif [ -f "target/debug/snipercor" ]; then
    echo -e "${YELLOW}⚠️ Using debug binary${NC}"
    BINARY="target/debug/snipercor"
else
    echo -e "${YELLOW}🔨 Building THE OVERMIND PROTOCOL...${NC}"
    cargo build --release
    BINARY="target/release/snipercor"
fi

# Create logs directory
mkdir -p logs

# Start with monitoring
echo -e "${BLUE}📊 Starting with full monitoring...${NC}"

# Start in background with logging
nohup $BINARY > logs/overmind_vault.log 2>&1 &
OVERMIND_PID=$!

echo -e "${GREEN}✅ OVERMIND VAULT STARTED${NC}"
echo "PID: $OVERMIND_PID"
echo "Logs: tail -f logs/overmind_vault.log"
echo ""

# Show monitoring commands
echo -e "${BLUE}📊 MONITORING COMMANDS:${NC}"
echo "Status:     python3 scripts/secure_wallet_access.py"
echo "Logs:       tail -f logs/overmind_vault.log"
echo "Stop:       kill $OVERMIND_PID"
echo "Emergency:  python3 scripts/secure_wallet_access.py"
echo ""

# Save PID for later
echo $OVERMIND_PID > .overmind_vault.pid

echo -e "${GREEN}🎉 OVERMIND VAULT IS RUNNING!${NC}"
echo ""
echo -e "${YELLOW}💡 NEXT STEPS:${NC}"
echo "1. Monitor logs: tail -f logs/overmind_vault.log"
echo "2. Check status: python3 scripts/secure_wallet_access.py"
echo "3. Fund hot wallets if needed"
echo "4. Monitor profits and security events"
echo ""
echo -e "${RED}⚠️ SECURITY REMINDERS:${NC}"
echo "• Keep encryption passwords safe"
echo "• Monitor wallet balances regularly"
echo "• Check security logs daily"
echo "• Backup encrypted files regularly"
