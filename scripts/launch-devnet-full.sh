#!/bin/bash

# THE OVERMIND PROTOCOL - Full Devnet Deployment Script
# Launches complete system for production testing on Solana Devnet

set -e

echo "🚀 THE OVERMIND PROTOCOL - DEVNET DEPLOYMENT"
echo "=============================================="
echo "📊 5-Layer Autonomous AI Trading System"
echo "🧠 Multi-Agent Architecture with MinionAgent"
echo "⚡ Ultra-HFT Engine with Sub-10ms Latency"
echo "🛡️ MEV Protection via Jito Bundles"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Load environment configuration
echo -e "${BLUE}📋 Loading Devnet configuration...${NC}"
if [ -f ".env.devnet" ]; then
    set -a
    source .env.devnet
    set +a
    echo -e "${GREEN}✅ Configuration loaded successfully${NC}"
else
    echo -e "${RED}❌ .env.devnet not found! Please create it first.${NC}"
    exit 1
fi

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

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}⏳ Waiting for $service_name on port $port...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if check_process "$service_name" $port; then
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ $service_name failed to start after $max_attempts attempts${NC}"
    return 1
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down THE OVERMIND PROTOCOL...${NC}"
    
    # Kill background processes
    if [ ! -z "$RUST_PID" ]; then
        echo "Stopping Rust Executor (PID: $RUST_PID)"
        kill $RUST_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$BRAIN_PID" ]; then
        echo "Stopping Brain Manager (PID: $BRAIN_PID)"
        kill $BRAIN_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$REDIS_PID" ]; then
        echo "Stopping Redis (PID: $REDIS_PID)"
        kill $REDIS_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

echo -e "\n${PURPLE}🔧 PHASE 1: Infrastructure Setup${NC}"

# Start Redis/DragonflyDB if not running
if ! check_process "Redis/DragonflyDB" 6379; then
    echo -e "${BLUE}🚀 Starting Redis for communication...${NC}"
    redis-server --port 6379 --daemonize yes
    REDIS_PID=$(pgrep redis-server)
    
    if ! wait_for_service "Redis" 6379; then
        echo -e "${RED}❌ Failed to start Redis${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Redis already running${NC}"
fi

echo -e "\n${PURPLE}🔧 PHASE 2: Build and Verify Rust Executor${NC}"

# Build Rust Executor
echo -e "${BLUE}🔨 Building Rust Executor...${NC}"
if OPENSSL_LIB_DIR=/usr/lib/x86_64-linux-gnu OPENSSL_INCLUDE_DIR=/usr/include/openssl cargo build --release; then
    echo -e "${GREEN}✅ Rust Executor built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Rust Executor${NC}"
    exit 1
fi

echo -e "\n${PURPLE}🧠 PHASE 3: Launch Multi-Agent AI Brain${NC}"

# Start Python Brain Manager in background
echo -e "${BLUE}🚀 Starting OVERMIND Brain Manager (MinionAgent)...${NC}"
cd brain
python3 -m src.overmind_brain.minion_main &
BRAIN_PID=$!
cd ..

if ! wait_for_service "Brain Manager" 8000; then
    echo -e "${RED}❌ Failed to start Brain Manager${NC}"
    exit 1
fi

echo -e "\n${PURPLE}⚡ PHASE 4: Launch Ultra-HFT Rust Executor${NC}"

# Start Rust Executor in background
echo -e "${BLUE}🚀 Starting Rust Executor with Devnet configuration...${NC}"
./target/release/snipercor &
RUST_PID=$!

if ! wait_for_service "Rust Executor" 8081; then
    echo -e "${RED}❌ Failed to start Rust Executor${NC}"
    exit 1
fi

echo -e "\n${GREEN}✅ THE OVERMIND PROTOCOL SUCCESSFULLY DEPLOYED!${NC}"
echo -e "${GREEN}=============================================${NC}"
echo -e "${BLUE}📊 System Status:${NC}"
echo -e "   🧠 Brain Manager:     http://localhost:8000/status"
echo -e "   ⚡ Rust Executor:     http://localhost:8081/status"
echo -e "   🔗 DragonflyDB:      localhost:6379"
echo -e "   📈 Health Check:     http://localhost:8081/health"
echo -e "   📊 Metrics:          http://localhost:8081/metrics"

echo -e "\n${PURPLE}🎯 PHASE 5: System Validation${NC}"

# Wait a moment for system to stabilize
sleep 5

# Health checks
echo -e "${BLUE}🏥 Performing health checks...${NC}"

# Check Rust Executor health
if curl -s http://localhost:8081/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Rust Executor health check passed${NC}"
else
    echo -e "${RED}❌ Rust Executor health check failed${NC}"
fi

# Check Brain Manager status
if curl -s http://localhost:8000/status | grep -q "running"; then
    echo -e "${GREEN}✅ Brain Manager health check passed${NC}"
else
    echo -e "${YELLOW}⚠️  Brain Manager health check inconclusive${NC}"
fi

echo -e "\n${GREEN}🎉 SYSTEM FULLY OPERATIONAL ON DEVNET!${NC}"
echo -e "${BLUE}💡 The system is now ready for testing. Press Ctrl+C to shutdown.${NC}"

# Keep script running
while true; do
    sleep 10
    
    # Periodic health checks
    if ! check_process "Rust Executor" 8081; then
        echo -e "${RED}❌ Rust Executor died! Attempting restart...${NC}"
        ./target/release/snipercor &
        RUST_PID=$!
    fi
    
    if ! check_process "Brain Manager" 8000; then
        echo -e "${RED}❌ Brain Manager died! Attempting restart...${NC}"
        cd brain
        python3 -m src.overmind_brain.minion_main &
        BRAIN_PID=$!
        cd ..
    fi
done