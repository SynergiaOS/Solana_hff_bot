#!/bin/bash
# THE OVERMIND PROTOCOL - Complete System Demonstration
# Autonomous AI-driven high-frequency trading system

set -e

echo "🚀 THE OVERMIND PROTOCOL - System Demonstration"
echo "================================================================"
echo "Hybrid AI-HFT Architecture for Solana Blockchain"
echo "================================================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}🔧 Checking Prerequisites...${NC}"

# Check if DragonflyDB is running
if ! nc -z localhost 6379 2>/dev/null; then
    echo -e "${YELLOW}⚠️ DragonflyDB not running. Starting container...${NC}"
    docker run -d --name overmind-dragonfly -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly
    sleep 3
    echo -e "${GREEN}✅ DragonflyDB started${NC}"
else
    echo -e "${GREEN}✅ DragonflyDB is running${NC}"
fi

# Check Python dependencies
if ! python3 -c "import redis, asyncio" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Installing Python dependencies...${NC}"
    pip3 install redis asyncio
fi

# Check Rust installation
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}❌ Rust/Cargo not found. Please install: https://rustup.rs/${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites satisfied${NC}"
echo ""

# Show architecture overview
echo -e "${BLUE}🏗️ OVERMIND PROTOCOL Architecture:${NC}"
echo "   Warstwa 2 (Zmysły): Market signal detection"
echo "   Warstwa 3 (Mózg AI): Multi-agent decision engine (Python)"
echo "   Warstwa 4 (Mięśnie): Ultra-fast executor (Rust)"
echo "   Komunikacja: DragonflyDB async message passing"
echo ""

# Demonstrate the system components
echo -e "${BLUE}📁 System Components Created:${NC}"
echo "   ✅ agent_brain/main.py - AI Brain with sub-agent swarm"
echo "   ✅ solana_executor/src/main.rs - HFT Executor (Rust)"
echo "   ✅ test_overmind_protocol_e2e.py - Integration test"
echo ""

echo -e "${BLUE}🎯 Key Features Implemented:${NC}"
echo "   🧠 Multi-Agent AI Brain (MarketData, Sentiment, Risk agents)"
echo "   📊 Vector Memory RAG for historical context"
echo "   ⚡ Sub-25ms HFT execution simulation"
echo "   🔄 Complete learning loop (signals → decisions → execution → memory)"
echo "   📈 Real-time performance metrics"
echo "   🛡️ Comprehensive error handling and validation"
echo ""

# Demo mode selection
echo -e "${YELLOW}📋 Demo Options:${NC}"
echo "1. Quick architecture overview"
echo "2. Run AI Brain component only"
echo "3. Run HFT Executor component only"
echo "4. Full system integration test"
echo "5. Code review and explanation"

read -p "Choose demo mode (1-5): " demo_choice

case $demo_choice in
    1)
        echo -e "${BLUE}🏗️ OVERMIND PROTOCOL Architecture Overview${NC}"
        echo ""
        echo "Signal Flow:"
        echo "  events:raw → AI Brain → overmind:commands → HFT Executor → execution:results"
        echo ""
        echo "AI Brain Pipeline:"
        echo "  1. Signal reception and parsing"
        echo "  2. Multi-agent analysis (market data, sentiment, risk)"
        echo "  3. Vector memory context retrieval"
        echo "  4. Strategic decision synthesis"
        echo "  5. Precise command generation"
        echo ""
        echo "HFT Executor Pipeline:"
        echo "  1. Command validation (<5ms)"
        echo "  2. Trade execution simulation (<25ms)"
        echo "  3. Result reporting and metrics"
        echo ""
        echo "Example Signal → Decision Flow:"
        echo '  {"type": "new_pool", "symbol": "WIF"} → BUY decision → Execution'
        ;;
        
    2)
        echo -e "${BLUE}🧠 Starting AI Brain Component...${NC}"
        echo "Press Ctrl+C to stop"
        cd /opt/overmind
        python3 agent_brain/main.py
        ;;
        
    3)
        echo -e "${BLUE}⚡ Starting HFT Executor Component...${NC}"
        echo "Press Ctrl+C to stop"
        cd /opt/overmind/solana_executor
        cargo run --release
        ;;
        
    4)
        echo -e "${BLUE}🔄 Running Full System Integration Test...${NC}"
        echo ""
        echo "This will start both components and test the complete flow:"
        echo "  1. AI Brain listening for signals"
        echo "  2. HFT Executor listening for commands"
        echo "  3. Inject test market signals"
        echo "  4. Verify end-to-end processing"
        echo ""
        
        # Start components in background
        echo -e "${YELLOW}Starting AI Brain...${NC}"
        cd /opt/overmind
        python3 agent_brain/main.py &
        BRAIN_PID=$!
        
        echo -e "${YELLOW}Starting HFT Executor...${NC}"
        cd /opt/overmind/solana_executor
        cargo run --release &
        EXECUTOR_PID=$!
        
        # Wait for startup
        sleep 5
        
        echo -e "${YELLOW}Running integration test...${NC}"
        cd /opt/overmind
        python3 test_overmind_protocol_e2e.py
        
        # Cleanup
        kill $BRAIN_PID $EXECUTOR_PID 2>/dev/null || true
        ;;
        
    5)
        echo -e "${BLUE}📖 Code Review and Explanation${NC}"
        echo ""
        echo "🧠 AI Brain (agent_brain/main.py):"
        echo "   - Asynchronous event processing with Redis BLPOP"
        echo "   - Multi-agent swarm simulation (market, sentiment, risk)"
        echo "   - Vector memory RAG for historical context"
        echo "   - Strategic decision logic with confidence scoring"
        echo "   - Precise command generation with risk management"
        echo ""
        echo "⚡ HFT Executor (solana_executor/src/main.rs):"
        echo "   - Ultra-fast async command processing"
        echo "   - Comprehensive validation and error handling"
        echo "   - Realistic execution simulation with market conditions"
        echo "   - Performance metrics and monitoring"
        echo "   - Paper trading mode for safe testing"
        echo ""
        echo "🔄 Communication Flow:"
        echo "   - events:raw: Market signals → AI Brain"
        echo "   - overmind:commands: AI decisions → HFT Executor"
        echo "   - execution:results: Trade results → AI Brain learning"
        echo ""
        echo "📊 Key Data Structures:"
        head -30 /opt/overmind/agent_brain/main.py | grep -A 10 "@dataclass"
        ;;
        
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 OVERMIND PROTOCOL Demo Complete!${NC}"
echo -e "${BLUE}📚 Next Steps:${NC}"
echo "   - Review the code implementations"
echo "   - Customize trading strategies and risk parameters"
echo "   - Integrate with real Solana RPC endpoints"
echo "   - Deploy to production with live trading"
echo ""
echo -e "${YELLOW}⚠️ Note: This is a PAPER TRADING simulation${NC}"
echo "   All trades are simulated for safety and demonstration"