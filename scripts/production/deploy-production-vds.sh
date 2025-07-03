#!/bin/bash

# THE OVERMIND PROTOCOL - Production VDS Deployment Script
# Optimized for 32GB RAM, 8 CPU cores, AMD EPYC 7282

set -e

echo "🚀 THE OVERMIND PROTOCOL - PRODUCTION VDS DEPLOYMENT"
echo "====================================================="
echo "🖥️  Server: AMD EPYC 7282 (8 cores, 32GB RAM)"
echo "🌐 IP: 89.117.53.53"
echo "🎯 Mode: High-Performance Production Setup"
echo "====================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Load production environment
echo -e "${BLUE}📋 Loading Production configuration...${NC}"
if [ -f ".env.production" ]; then
    set -a
    source .env.production
    set +a
    echo -e "${GREEN}✅ Production configuration loaded${NC}"
else
    echo -e "${RED}❌ .env.production not found! Creating from template...${NC}"
    cp .env.devnet .env.production
    echo -e "${YELLOW}⚠️  Please edit .env.production with production settings${NC}"
fi

# Function to check system resources
check_system_resources() {
    echo -e "${PURPLE}🔧 SYSTEM RESOURCE CHECK${NC}"
    
    # RAM Check
    TOTAL_RAM=$(free -g | awk 'NR==2{printf "%.0f", $2}')
    echo -e "${BLUE}💾 RAM: ${TOTAL_RAM}GB${NC}"
    
    if [ $TOTAL_RAM -lt 30 ]; then
        echo -e "${YELLOW}⚠️  Warning: Less than 32GB RAM detected${NC}"
    else
        echo -e "${GREEN}✅ RAM: Sufficient for production${NC}"
    fi
    
    # CPU Check
    CPU_CORES=$(nproc)
    echo -e "${BLUE}🔧 CPU Cores: ${CPU_CORES}${NC}"
    
    if [ $CPU_CORES -lt 8 ]; then
        echo -e "${YELLOW}⚠️  Warning: Less than 8 CPU cores detected${NC}"
    else
        echo -e "${GREEN}✅ CPU: Sufficient for production${NC}"
    fi
    
    # Disk Check
    DISK_AVAIL=$(df / | tail -1 | awk '{print $4}')
    DISK_AVAIL_GB=$((DISK_AVAIL / 1024 / 1024))
    echo -e "${BLUE}💿 Disk Available: ${DISK_AVAIL_GB}GB${NC}"
    
    if [ $DISK_AVAIL_GB -lt 50 ]; then
        echo -e "${YELLOW}⚠️  Warning: Less than 50GB disk space available${NC}"
    else
        echo -e "${GREEN}✅ Disk: Sufficient for production${NC}"
    fi
}

# Function to optimize system settings
optimize_system() {
    echo -e "${PURPLE}⚡ SYSTEM OPTIMIZATION${NC}"
    
    # Set ulimits for high-performance trading
    echo -e "${BLUE}🔧 Setting system limits for high-performance...${NC}"
    
    # File descriptor limits
    ulimit -n 65536
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    
    # Memory overcommit for high-frequency trading
    echo 'vm.overcommit_memory = 1' | sudo tee -a /etc/sysctl.conf
    echo 'vm.swappiness = 1' | sudo tee -a /etc/sysctl.conf
    
    # Network optimizations
    echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
    echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
    
    sudo sysctl -p
    
    echo -e "${GREEN}✅ System optimizations applied${NC}"
}

# Function to setup monitoring
setup_monitoring() {
    echo -e "${PURPLE}📊 MONITORING SETUP${NC}"
    
    # Create log directories
    sudo mkdir -p /var/log/overmind
    sudo chown $USER:$USER /var/log/overmind
    
    # Setup log rotation
    cat << EOF | sudo tee /etc/logrotate.d/overmind
/var/log/overmind/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF
    
    echo -e "${GREEN}✅ Monitoring setup complete${NC}"
}

# Function to start production services
start_production_services() {
    echo -e "${PURPLE}🚀 STARTING PRODUCTION SERVICES${NC}"
    
    # Build optimized Rust executor
    echo -e "${BLUE}🔨 Building optimized Rust executor...${NC}"
    RUSTFLAGS="-C target-cpu=native -C opt-level=3" cargo build --release
    
    # Start DragonflyDB with production settings
    echo -e "${BLUE}🗄️  Starting DragonflyDB with production config...${NC}"
    if ! pgrep -f "dragonfly" > /dev/null; then
        dragonfly --logtostderr --maxmemory=8gb --save_schedule="*/30 */6 */1" &
        sleep 3
    else
        echo -e "${GREEN}✅ DragonflyDB already running${NC}"
    fi
    
    # Start AI Brain with production settings
    echo -e "${BLUE}🧠 Starting OVERMIND Brain (Production Mode)...${NC}"
    cd brain
    PYTHONPATH=./src python3 -m src.overmind_brain.minion_main &
    BRAIN_PID=$!
    cd ..
    sleep 5
    
    # Start Rust Executor with production settings
    echo -e "${BLUE}⚡ Starting Rust Executor (Production Mode)...${NC}"
    SNIPER_TRADING_MODE=paper ./target/release/snipercor &
    EXECUTOR_PID=$!
    sleep 5
    
    # Start Mission Control UI
    echo -e "${BLUE}🌐 Starting Mission Control UI...${NC}"
    cd mission_control_ui
    python3 -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
    UI_PID=$!
    cd ..
    
    echo -e "${GREEN}✅ All production services started${NC}"
    echo -e "${BLUE}📊 Service PIDs: Brain=$BRAIN_PID, Executor=$EXECUTOR_PID, UI=$UI_PID${NC}"
}

# Function to verify deployment
verify_deployment() {
    echo -e "${PURPLE}🔍 DEPLOYMENT VERIFICATION${NC}"
    
    # Check service health
    services=(
        "http://localhost:8000/status:Brain Manager"
        "http://localhost:8081/health:Rust Executor"
        "http://localhost:8501:Mission Control UI"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service"
        echo -e "${BLUE}🔍 Checking $name...${NC}"
        
        if curl -s "$url" > /dev/null; then
            echo -e "${GREEN}✅ $name: Operational${NC}"
        else
            echo -e "${RED}❌ $name: Not responding${NC}"
        fi
    done
    
    # Check DragonflyDB
    echo -e "${BLUE}🔍 Checking DragonflyDB...${NC}"
    if echo "PING" | nc localhost 6379 | grep -q "PONG"; then
        echo -e "${GREEN}✅ DragonflyDB: Operational${NC}"
    else
        echo -e "${RED}❌ DragonflyDB: Not responding${NC}"
    fi
    
    # Performance test
    echo -e "${BLUE}🚀 Running performance test...${NC}"
    START_TIME=$(date +%s%3N)
    echo "PING" | nc localhost 6379 > /dev/null
    END_TIME=$(date +%s%3N)
    LATENCY=$((END_TIME - START_TIME))
    
    echo -e "${GREEN}⚡ System latency: ${LATENCY}ms${NC}"
    
    if [ $LATENCY -lt 5 ]; then
        echo -e "${GREEN}✅ Excellent latency (<5ms)${NC}"
    elif [ $LATENCY -lt 10 ]; then
        echo -e "${YELLOW}⚠️  Good latency (<10ms)${NC}"
    else
        echo -e "${RED}❌ High latency (>10ms)${NC}"
    fi
}

# Main deployment function
main() {
    echo -e "${GREEN}🎯 Starting Production VDS Deployment...${NC}"
    
    check_system_resources
    optimize_system
    setup_monitoring
    start_production_services
    verify_deployment
    
    echo -e "${GREEN}🎉 PRODUCTION DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}=================================${NC}"
    echo -e "${BLUE}📊 Access Points:${NC}"
    echo -e "   🧠 Brain Manager:     http://89.117.53.53:8000/status"
    echo -e "   ⚡ Rust Executor:     http://89.117.53.53:8081/health"
    echo -e "   🌐 Mission Control:   http://89.117.53.53:8501"
    echo -e "   📈 Metrics:          http://89.117.53.53:8081/metrics"
    echo -e "   🗄️  DragonflyDB:      89.117.53.53:6379"
    
    echo -e "\n${PURPLE}💡 PRODUCTION READY FEATURES:${NC}"
    echo -e "   🎯 Strategy-Aware Decision Making"
    echo -e "   🚀 Sub-10ms Latency Targets"
    echo -e "   🧠 Multi-Agent AI Architecture"
    echo -e "   🛡️ Comprehensive Risk Management"
    echo -e "   📊 Real-time Monitoring & Control"
    
    echo -e "\n${YELLOW}⚠️  SECURITY REMINDERS:${NC}"
    echo -e "   • Update .env.production with real API keys"
    echo -e "   • Configure SSL certificates for HTTPS"
    echo -e "   • Set up firewall rules"
    echo -e "   • Enable log monitoring"
    echo -e "   • Review trading parameters before live mode"
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    pkill -f "snipercor" || true
    pkill -f "minion_main" || true
    pkill -f "streamlit" || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Run main deployment
main

# Keep script running for monitoring
echo -e "\n${BLUE}💡 Deployment complete. Press Ctrl+C to shutdown.${NC}"
while true; do
    sleep 30
    # Basic health check
    if ! curl -s http://localhost:8081/health > /dev/null; then
        echo -e "${RED}⚠️  Executor health check failed at $(date)${NC}"
    fi
done