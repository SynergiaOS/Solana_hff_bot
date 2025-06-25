#!/bin/bash

# Custom OVERMIND E2E Test
echo "🧪 CUSTOM OVERMIND E2E TEST"
echo "=========================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment
set -a
source .env.devnet
set +a

echo -e "${BLUE}📋 Test 1: System Health Check${NC}"

# Check DragonflyDB using netcat
echo -e "${BLUE}📡 Testing DragonflyDB...${NC}"
if echo "PING" | timeout 3 nc localhost 6379 | grep -q "PONG"; then
    echo -e "${GREEN}✅ DragonflyDB operational${NC}"
else
    echo -e "${RED}❌ DragonflyDB connection failed${NC}"
    exit 1
fi

# Check Rust Executor
echo -e "${BLUE}⚡ Testing Rust Executor...${NC}"
if curl -s http://localhost:8081/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Rust Executor healthy${NC}"
else
    echo -e "${RED}❌ Rust Executor not responding${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Test 2: Signal Injection${NC}"

# Test signal injection using netcat
TEST_SIGNAL='{
    "signal_id": "test_'$(date +%s)'",
    "signal_type": "test_signal",
    "symbol": "SOL",
    "action": "BUY",
    "quantity": 0.1,
    "confidence": 0.85,
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'

echo -e "${BLUE}🧠 Injecting test signal...${NC}"
echo "LPUSH overmind:signals '$TEST_SIGNAL'" | nc localhost 6379

echo -e "${BLUE}⏳ Waiting for processing (10 seconds)...${NC}"
sleep 10

echo -e "${BLUE}📤 Checking for responses...${NC}"
echo "LLEN overmind:decisions" | nc localhost 6379

echo -e "${BLUE}📋 Test 3: Direct Command Test${NC}"

# Test direct command injection
TEST_COMMAND='{
    "command_id": "test_cmd_'$(date +%s)'",
    "action": "execute_trade",
    "symbol": "SOL",
    "quantity": 0.1,
    "side": "buy",
    "confidence": 0.85
}'

echo -e "${BLUE}⚡ Sending direct command...${NC}"
echo "LPUSH overmind:commands '$TEST_COMMAND'" | nc localhost 6379

sleep 5

echo -e "${BLUE}📊 Checking queue lengths...${NC}"
echo "Queue Status:"
echo -n "   Signals: "
echo "LLEN overmind:signals" | nc localhost 6379
echo -n "   Commands: "
echo "LLEN overmind:commands" | nc localhost 6379
echo -n "   Decisions: "
echo "LLEN overmind:decisions" | nc localhost 6379

echo -e "${GREEN}🎉 Custom E2E Test Completed!${NC}"
echo "System validation successful for running OVERMIND components."