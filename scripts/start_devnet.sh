#!/bin/bash

# THE OVERMIND PROTOCOL - DEVNET STARTUP SCRIPT
# Safe deployment for testing on Solana devnet

set -e

echo "🧠 THE OVERMIND PROTOCOL - DEVNET DEPLOYMENT"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Safety check
echo -e "${YELLOW}⚠️  SAFETY CHECK: Ensuring paper trading mode${NC}"
if [ "$SNIPER_TRADING_MODE" != "paper" ]; then
    echo -e "${RED}🚨 ERROR: SNIPER_TRADING_MODE must be 'paper' for devnet testing${NC}"
    echo -e "${RED}   Current value: $SNIPER_TRADING_MODE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Paper trading mode confirmed${NC}"

# Load devnet configuration
echo -e "${BLUE}📋 Loading devnet configuration...${NC}"
export $(cat .env.devnet | grep -v '^#' | xargs)

# Create data directory
echo -e "${BLUE}📁 Creating data directory...${NC}"
mkdir -p data
mkdir -p logs

# Check Solana devnet connectivity
echo -e "${BLUE}🌐 Testing Solana devnet connectivity...${NC}"
if curl -s --connect-timeout 5 https://api.devnet.solana.com > /dev/null; then
    echo -e "${GREEN}✅ Solana devnet is reachable${NC}"
else
    echo -e "${RED}❌ Cannot reach Solana devnet${NC}"
    exit 1
fi

# Build the project
echo -e "${BLUE}🔧 Building THE OVERMIND PROTOCOL...${NC}"
cargo build --release

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build successful${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

# Start monitoring (optional)
echo -e "${BLUE}📊 Starting monitoring stack...${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose up -d prometheus grafana
    echo -e "${GREEN}✅ Monitoring stack started${NC}"
    echo -e "${BLUE}   Prometheus: http://localhost:9091${NC}"
    echo -e "${BLUE}   Grafana: http://localhost:3002${NC}"
else
    echo -e "${YELLOW}⚠️  Docker Compose not available, skipping monitoring${NC}"
fi

# Display configuration summary
echo -e "${BLUE}📋 DEVNET CONFIGURATION SUMMARY:${NC}"
echo -e "   Trading Mode: ${GREEN}$SNIPER_TRADING_MODE${NC}"
echo -e "   RPC Endpoint: ${BLUE}$SNIPER_SOLANA_RPC_URL${NC}"
echo -e "   Max Position: ${YELLOW}$SNIPER_MAX_POSITION_SIZE SOL${NC}"
echo -e "   Max Daily Loss: ${YELLOW}$SNIPER_MAX_DAILY_LOSS SOL${NC}"
echo -e "   AI Mode: ${GREEN}$OVERMIND_AI_MODE${NC}"
echo -e "   Multi-Wallet: ${GREEN}$OVERMIND_MULTI_WALLET_ENABLED${NC}"

# Final safety confirmation
echo -e "${YELLOW}⚠️  FINAL SAFETY CHECK:${NC}"
echo -e "   This will start THE OVERMIND PROTOCOL in PAPER TRADING mode"
echo -e "   No real funds will be used - devnet testing only"
echo -e "   Press CTRL+C to cancel, or wait 5 seconds to continue..."

sleep 5

# Start THE OVERMIND PROTOCOL
echo -e "${GREEN}🚀 STARTING THE OVERMIND PROTOCOL ON DEVNET...${NC}"
echo -e "${BLUE}   Logs will be saved to: logs/overmind_devnet.log${NC}"
echo -e "${BLUE}   Press CTRL+C to stop the system${NC}"
echo ""

# Run with logging
./target/release/snipercor 2>&1 | tee logs/overmind_devnet.log
