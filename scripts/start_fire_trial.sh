#!/bin/bash
# THE OVERMIND PROTOCOL - Fire Trial Quick Start Script
# Automated execution of Phase 1 & 2 tasks for 48-hour mainnet paper trading validation

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="fire-trial-backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="fire-trial-startup.log"

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Function to print section header
print_header() {
    echo -e "\n${BLUE}${BOLD}$1${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..60})${NC}"
}

# Function to check if we're on production server
check_environment() {
    if [[ $(hostname) != *"89.117.53.53"* ]] && [[ $(hostname) != *"contabo"* ]]; then
        echo -e "${YELLOW}⚠️ Warning: This script should be run on the production server (89.117.53.53)${NC}"
        echo -e "Current hostname: $(hostname)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to create backup
create_backup() {
    print_header "📦 Phase 1.1: System Shutdown & Environment Preparation"
    
    log_message "Creating backup directory: $BACKUP_DIR"
    mkdir -p $BACKUP_DIR
    
    # Save current system logs
    if docker ps | grep -q overmind-mission-control; then
        log_message "Backing up Mission Control logs"
        docker logs overmind-mission-control > $BACKUP_DIR/mission-control.log 2>&1
    fi
    
    if docker ps | grep -q sniperbot-dragonfly; then
        log_message "Backing up DragonflyDB logs"
        docker logs sniperbot-dragonfly > $BACKUP_DIR/dragonfly.log 2>&1
    fi
    
    # Backup current configuration
    if [ -f ".env" ]; then
        log_message "Backing up .env configuration"
        cp .env $BACKUP_DIR/.env.backup
    fi
    
    # Backup current system state
    log_message "Saving system state"
    docker ps > $BACKUP_DIR/docker-ps.txt
    ss -tlnp > $BACKUP_DIR/ports.txt
    ps aux | grep overmind > $BACKUP_DIR/processes.txt
    
    echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
}

# Function to shutdown services
shutdown_services() {
    log_message "Shutting down current services"
    
    # Stop OVERMIND process
    if pgrep -f "overmind_hft_executor" > /dev/null; then
        log_message "Stopping OVERMIND executor"
        pkill -TERM overmind_hft_executor || true
        sleep 5
    fi
    
    # Stop Docker services
    if [ -f "infrastructure/compose/docker-compose.overmind.yml" ]; then
        log_message "Stopping Docker services"
        docker-compose -f infrastructure/compose/docker-compose.overmind.yml down || true
    fi
    
    # Verify ports are free
    log_message "Verifying ports are available"
    for port in 8080 8501 6379; do
        if ss -tlnp | grep -q ":$port "; then
            echo -e "${YELLOW}⚠️ Port $port still in use${NC}"
        else
            echo -e "${GREEN}✅ Port $port available${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Services shutdown complete${NC}"
}

# Function to update configuration for mainnet
update_configuration() {
    print_header "🌐 Phase 1.2: Mainnet Configuration Update"
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ .env file not found${NC}"
        exit 1
    fi
    
    log_message "Updating configuration for mainnet"
    
    # Create temporary .env file
    cp .env .env.temp
    
    # Update configuration (keeping paper trading mode)
    log_message "Setting paper trading mode"
    sed -i 's/^PAPER_TRADING_MODE=.*/PAPER_TRADING_MODE=true/' .env.temp
    
    # Update RPC endpoints to mainnet
    log_message "Updating RPC endpoints to mainnet"
    sed -i 's/^SOLANA_RPC_URL=.*/SOLANA_RPC_URL=https:\/\/api.mainnet-beta.solana.com/' .env.temp
    sed -i 's/^SOLANA_WSS_URL=.*/SOLANA_WSS_URL=wss:\/\/api.mainnet-beta.solana.com/' .env.temp
    
    # Verify critical settings
    if ! grep -q "PAPER_TRADING_MODE=true" .env.temp; then
        echo -e "${RED}❌ CRITICAL: Paper trading mode not set correctly${NC}"
        exit 1
    fi
    
    # Apply changes
    mv .env.temp .env
    
    echo -e "${GREEN}✅ Configuration updated for mainnet${NC}"
    echo -e "${BOLD}📋 Configuration Summary:${NC}"
    echo -e "   Paper Trading: $(grep PAPER_TRADING_MODE .env)"
    echo -e "   RPC URL: $(grep SOLANA_RPC_URL .env)"
    echo -e "   WSS URL: $(grep SOLANA_WSS_URL .env)"
}

# Function to test connectivity
test_connectivity() {
    log_message "Testing mainnet connectivity"
    
    # Test mainnet RPC
    if curl -s -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' \
        https://api.mainnet-beta.solana.com | grep -q "ok"; then
        echo -e "${GREEN}✅ Mainnet RPC connectivity OK${NC}"
    else
        echo -e "${YELLOW}⚠️ Mainnet RPC connectivity issue${NC}"
    fi
    
    # Test if we can reach the endpoints
    if curl -s --connect-timeout 5 https://api.mainnet-beta.solana.com > /dev/null; then
        echo -e "${GREEN}✅ Mainnet endpoint reachable${NC}"
    else
        echo -e "${RED}❌ Cannot reach mainnet endpoint${NC}"
        exit 1
    fi
}

# Function to launch system
launch_system() {
    print_header "🚀 Phase 1.3: Mainnet System Launch"
    
    log_message "Starting Docker services"
    
    # Start Docker services
    if [ -f "infrastructure/compose/docker-compose.overmind.yml" ]; then
        docker-compose -f infrastructure/compose/docker-compose.overmind.yml up -d
        sleep 30  # Wait for services to initialize
    else
        echo -e "${RED}❌ Docker compose file not found${NC}"
        exit 1
    fi
    
    # Start OVERMIND application
    log_message "Starting OVERMIND application"
    if [ -f "Cargo.toml" ]; then
        RUST_LOG=info nohup cargo run --profile contabo > logs/overmind.log 2>&1 &
        echo $! > overmind.pid
        sleep 10  # Wait for application to start
    else
        echo -e "${RED}❌ Cargo.toml not found - not in project directory?${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ System launch initiated${NC}"
}

# Function to verify system health
verify_system_health() {
    print_header "✅ Phase 2.1: Service Health Verification"
    
    log_message "Verifying system health"
    
    # Check Docker services
    local docker_services=$(docker ps --filter "status=running" | grep -c -E "(mission-control|dragonfly|prometheus|grafana)" || echo "0")
    echo -e "Docker services running: $docker_services"
    
    # Check Mission Control
    if curl -s -f http://localhost:8501/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Mission Control accessible${NC}"
    else
        echo -e "${YELLOW}⚠️ Mission Control not yet accessible${NC}"
    fi
    
    # Check DragonflyDB
    if echo "PING" | nc -w 2 localhost 6379 | grep -q "PONG" 2>/dev/null; then
        echo -e "${GREEN}✅ DragonflyDB responding${NC}"
    else
        echo -e "${YELLOW}⚠️ DragonflyDB not responding${NC}"
    fi
    
    # Check OVERMIND process
    if pgrep -f "overmind_hft_executor" > /dev/null; then
        echo -e "${GREEN}✅ OVERMIND process running${NC}"
    else
        echo -e "${YELLOW}⚠️ OVERMIND process not detected${NC}"
    fi
    
    echo -e "${GREEN}✅ Health verification complete${NC}"
}

# Function to display final status
display_final_status() {
    print_header "🎯 Fire Trial Protocol - Ready for Execution"
    
    echo -e "${BOLD}📊 System Status:${NC}"
    echo -e "   Mission Control: http://$(hostname -I | awk '{print $1}'):8501"
    echo -e "   Grafana Dashboard: http://$(hostname -I | awk '{print $1}'):3000"
    echo -e "   Paper Trading Mode: ${GREEN}ENABLED${NC}"
    echo -e "   Backup Location: $BACKUP_DIR"
    
    echo -e "\n${BOLD}📋 Next Steps:${NC}"
    echo -e "   1. Access Mission Control dashboard to verify mainnet data"
    echo -e "   2. Start monitoring script: ./scripts/fire_trial_monitor.sh --daemon"
    echo -e "   3. Begin 48-hour autonomous operation monitoring"
    echo -e "   4. Test dynamic goal modification at 24-hour mark"
    
    echo -e "\n${BOLD}🛡️ Safety Reminders:${NC}"
    echo -e "   • Paper trading mode is ENABLED - no real transactions"
    echo -e "   • Monitor system health every 2 hours"
    echo -e "   • Emergency stop: export OVERMIND_EMERGENCY_STOP=true"
    echo -e "   • Rollback available: cp $BACKUP_DIR/.env.backup .env"
    
    echo -e "\n${GREEN}🔥 THE OVERMIND PROTOCOL Fire Trial is ready to begin!${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}${BOLD}🔥 THE OVERMIND PROTOCOL - Fire Trial Quick Start${NC}"
    echo -e "${GREEN}${BOLD}=================================================${NC}"
    echo -e "Starting automated setup for 48-hour mainnet paper trading validation\n"
    
    # Check environment
    check_environment
    
    # Confirm execution
    echo -e "${YELLOW}This will:${NC}"
    echo -e "  • Shutdown current services"
    echo -e "  • Switch to mainnet configuration (PAPER TRADING MODE)"
    echo -e "  • Launch THE OVERMIND PROTOCOL on mainnet"
    echo -e "  • Verify system health"
    echo ""
    read -p "Continue with Fire Trial setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Fire Trial setup cancelled"
        exit 0
    fi
    
    # Execute phases
    create_backup
    shutdown_services
    update_configuration
    test_connectivity
    launch_system
    sleep 30  # Wait for full initialization
    verify_system_health
    display_final_status
    
    log_message "Fire Trial quick start completed successfully"
}

# Handle script termination
cleanup() {
    echo -e "\n${YELLOW}Fire Trial setup interrupted${NC}"
    log_message "Fire Trial setup interrupted by user"
    exit 1
}

trap cleanup SIGINT SIGTERM

# Run main function
main "$@"
