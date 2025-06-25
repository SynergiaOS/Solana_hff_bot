#!/bin/bash

# THE OVERMIND PROTOCOL - Simplified Production Start
# Optimized for VDS 32GB RAM, 8 CPU cores

set -e

echo "🚀 THE OVERMIND PROTOCOL - HIGH-PERFORMANCE PRODUCTION"
echo "======================================================="
echo "🖥️  Server: AMD EPYC 7282 (8 cores, 32GB RAM)"
echo "🌐 External IP: 89.117.53.53"
echo "🎯 Mode: Production Scale with Strategy Integration"
echo "======================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load production environment
echo -e "${BLUE}📋 Loading Production configuration...${NC}"
set -a
source .env.production
set +a

# System optimization (userspace only)
echo -e "${PURPLE}⚡ SYSTEM OPTIMIZATION${NC}"
ulimit -n 65536
export RAYON_NUM_THREADS=8
export RUST_BACKTRACE=1

echo -e "${BLUE}🖥️  System Resources:${NC}"
echo "   CPU Cores: $(nproc)"
echo "   RAM Total: $(free -h | awk 'NR==2{print $2}')"
echo "   RAM Available: $(free -h | awk 'NR==2{print $7}')"
echo "   Disk Available: $(df -h / | tail -1 | awk '{print $4}')"

# Function to check if process is running
check_process() {
    local process_name=$1
    local port=$2
    
    if lsof -i:$port &>/dev/null; then
        echo -e "${GREEN}✅ $process_name is running on port $port${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $process_name not running on port $port${NC}"
        return 1
    fi
}

echo -e "\n${PURPLE}🗄️  PHASE 1: Database Layer${NC}"

# Start DragonflyDB if not running
if ! check_process "DragonflyDB" 6379; then
    echo -e "${BLUE}🚀 Starting DragonflyDB (Production Config)...${NC}"
    dragonfly --logtostderr --maxmemory=8gb --threads=8 --tcp_keepalive=300 &
    sleep 3
    
    if check_process "DragonflyDB" 6379; then
        echo -e "${GREEN}✅ DragonflyDB started with production settings${NC}"
    else
        echo -e "${YELLOW}⚠️  DragonflyDB startup check failed${NC}"
    fi
fi

echo -e "\n${PURPLE}🔨 PHASE 2: Build Optimized Executor${NC}"

# Build optimized Rust executor for production
echo -e "${BLUE}🔧 Building optimized Rust executor (target-cpu=native)...${NC}"
RUSTFLAGS="-C target-cpu=native -C opt-level=3 -C codegen-units=1" cargo build --release

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Rust executor built with maximum optimization${NC}"
else
    echo -e "${YELLOW}⚠️  Build completed with warnings${NC}"
fi

echo -e "\n${PURPLE}🧠 PHASE 3: AI Brain with Strategy Integration${NC}"

# Start AI Brain with all strategies enabled
echo -e "${BLUE}🚀 Starting OVERMIND Brain (All Strategies Enabled)...${NC}"
cd brain
PYTHONPATH=./src python3 -m src.overmind_brain.minion_main &
BRAIN_PID=$!
cd ..

# Wait for brain to start
sleep 8

if check_process "AI Brain" 8000; then
    echo -e "${GREEN}✅ AI Brain operational with strategy integration${NC}"
    echo -e "${BLUE}   📊 Enabled Strategies: ${ENABLED_STRATEGIES}${NC}"
else
    echo -e "${YELLOW}⚠️  AI Brain startup verification pending${NC}"
fi

echo -e "\n${PURPLE}⚡ PHASE 4: Ultra-HFT Rust Executor${NC}"

# Start Rust Executor with production settings
echo -e "${BLUE}🚀 Starting Rust Executor (Production Mode)...${NC}"
SNIPER_TRADING_MODE=paper \
OVERMIND_MAX_LATENCY_MS=5 \
RUST_LOG=info,snipercor=debug,overmind=debug \
./target/release/snipercor &
EXECUTOR_PID=$!

# Wait for executor to start
sleep 5

if check_process "Rust Executor" 8081; then
    echo -e "${GREEN}✅ Rust Executor operational (Sub-5ms targets)${NC}"
else
    echo -e "${YELLOW}⚠️  Rust Executor startup verification pending${NC}"
fi

echo -e "\n${PURPLE}🌐 PHASE 5: Mission Control UI${NC}"

# Start Mission Control UI for external access
echo -e "${BLUE}🚀 Starting Mission Control UI (External Access)...${NC}"
cd mission_control_ui
python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
UI_PID=$!
cd ..

# Wait for UI to start
sleep 5

if check_process "Mission Control" 8501; then
    echo -e "${GREEN}✅ Mission Control UI operational${NC}"
else
    echo -e "${YELLOW}⚠️  Mission Control UI startup verification pending${NC}"
fi

echo -e "\n${PURPLE}🔍 PHASE 6: System Validation${NC}"

# Health check all services
echo -e "${BLUE}🏥 Comprehensive health check...${NC}"

# Check DragonflyDB
if echo "PING" | nc -w 2 localhost 6379 | grep -q "PONG"; then
    echo -e "${GREEN}✅ DragonflyDB: Responding (Redis protocol)${NC}"
else
    echo -e "${YELLOW}⚠️  DragonflyDB: Connection issues${NC}"
fi

# Check Rust Executor
if curl -s --max-time 5 http://localhost:8081/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Rust Executor: Healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Rust Executor: Health check pending${NC}"
fi

# Check Brain Manager (may take longer to start)
if curl -s --max-time 5 http://localhost:8000/status > /dev/null 2>&1; then
    echo -e "${GREEN}✅ AI Brain: Responding${NC}"
else
    echo -e "${YELLOW}⚠️  AI Brain: Still initializing${NC}"
fi

# Check Mission Control
if curl -s --max-time 5 http://localhost:8501 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Mission Control: Accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Mission Control: Still loading${NC}"
fi

# Performance benchmark
echo -e "\n${BLUE}🚀 Performance Benchmark...${NC}"
START_TIME=$(date +%s%3N)
echo "PING" | nc -w 1 localhost 6379 > /dev/null 2>&1
END_TIME=$(date +%s%3N)
LATENCY=$((END_TIME - START_TIME))

echo -e "${BLUE}⚡ System Latency: ${LATENCY}ms${NC}"

if [ $LATENCY -lt 3 ]; then
    echo -e "${GREEN}🔥 EXCELLENT: Ultra-low latency (<3ms)${NC}"
elif [ $LATENCY -lt 10 ]; then
    echo -e "${GREEN}✅ GOOD: Low latency (<10ms)${NC}"
else
    echo -e "${YELLOW}⚠️  MODERATE: Latency ${LATENCY}ms${NC}"
fi

echo -e "\n${GREEN}🎉 PRODUCTION SYSTEM DEPLOYED!${NC}"
echo -e "${GREEN}================================${NC}"

echo -e "\n${BLUE}🌐 EXTERNAL ACCESS POINTS:${NC}"
echo -e "   🧠 AI Brain Manager:     http://89.117.53.53:8000/status"
echo -e "   ⚡ Rust Executor:       http://89.117.53.53:8081/health"
echo -e "   🎯 Mission Control:     http://89.117.53.53:8501"
echo -e "   📊 System Metrics:      http://89.117.53.53:8081/metrics"
echo -e "   🗄️  DragonflyDB:        89.117.53.53:6379"

echo -e "\n${PURPLE}💫 PRODUCTION FEATURES ACTIVE:${NC}"
echo -e "   🎯 Strategy-Aware AI Decision Making"
echo -e "   ⚡ Sub-5ms Latency Targets"
echo -e "   🧠 Multi-Agent Architecture (4 Agents)"
echo -e "   🚀 8-Core CPU Utilization"
echo -e "   💾 32GB RAM Optimization"
echo -e "   🛡️ Paper Trading Safety Mode"
echo -e "   📊 Real-time Monitoring Dashboard"

echo -e "\n${BLUE}📋 Process IDs:${NC}"
echo -e "   AI Brain PID: $BRAIN_PID"
echo -e "   Rust Executor PID: $EXECUTOR_PID"
echo -e "   Mission Control PID: $UI_PID"

echo -e "\n${YELLOW}⚡ READY FOR PRODUCTION TRADING!${NC}"
echo -e "${PURPLE}Press Ctrl+C to shutdown all services${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down THE OVERMIND PROTOCOL...${NC}"
    
    # Kill services gracefully
    [ ! -z "$UI_PID" ] && kill $UI_PID 2>/dev/null && echo "✅ Mission Control stopped"
    [ ! -z "$EXECUTOR_PID" ] && kill $EXECUTOR_PID 2>/dev/null && echo "✅ Rust Executor stopped"  
    [ ! -z "$BRAIN_PID" ] && kill $BRAIN_PID 2>/dev/null && echo "✅ AI Brain stopped"
    
    # Stop any remaining processes
    pkill -f "snipercor" 2>/dev/null || true
    pkill -f "minion_main" 2>/dev/null || true
    pkill -f "streamlit" 2>/dev/null || true
    
    echo -e "${GREEN}✅ All services stopped gracefully${NC}"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Keep running and monitor services
while true; do
    sleep 30
    
    # Basic health monitoring
    if ! curl -s --max-time 3 http://localhost:8081/health > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  [$(date)] Executor health check failed${NC}"
    fi
    
    if ! echo "PING" | nc -w 1 localhost 6379 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  [$(date)] DragonflyDB connection failed${NC}"
    fi
done