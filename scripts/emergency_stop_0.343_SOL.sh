#!/bin/bash

# THE OVERMIND PROTOCOL - Emergency Stop Script for 0.343 SOL Portfolio
# =====================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Portfolio Configuration
INITIAL_BALANCE=0.343
MAX_DAILY_LOSS=0.051
EMERGENCY_THRESHOLD=0.069

echo -e "${RED}🚨 THE OVERMIND PROTOCOL - EMERGENCY STOP SYSTEM${NC}"
echo -e "${BLUE}Portfolio: ${INITIAL_BALANCE} SOL | Max Loss: ${MAX_DAILY_LOSS} SOL${NC}"
echo "=================================================================="

# Function to check current portfolio status
check_portfolio_status() {
    echo -e "${YELLOW}📊 Checking portfolio status...${NC}"
    
    # Get current balance from API
    CURRENT_BALANCE=$(curl -s http://localhost:8080/portfolio/balance | jq -r '.balance // 0.343')
    CURRENT_PNL=$(curl -s http://localhost:8080/portfolio/pnl | jq -r '.daily_pnl // 0')
    
    echo "Current Balance: ${CURRENT_BALANCE} SOL"
    echo "Daily P&L: ${CURRENT_PNL} SOL"
    
    # Calculate loss percentage
    LOSS_AMOUNT=$(echo "${INITIAL_BALANCE} - ${CURRENT_BALANCE}" | bc -l)
    LOSS_PERCENTAGE=$(echo "scale=2; ${LOSS_AMOUNT} / ${INITIAL_BALANCE} * 100" | bc -l)
    
    echo "Current Loss: ${LOSS_AMOUNT} SOL (${LOSS_PERCENTAGE}%)"
    
    # Check if emergency stop is needed
    if (( $(echo "${LOSS_AMOUNT} >= ${MAX_DAILY_LOSS}" | bc -l) )); then
        echo -e "${RED}⚠️ CRITICAL: Daily loss limit exceeded!${NC}"
        return 1
    elif (( $(echo "${LOSS_AMOUNT} >= ${EMERGENCY_THRESHOLD}" | bc -l) )); then
        echo -e "${RED}🚨 EMERGENCY: Emergency threshold reached!${NC}"
        return 2
    else
        echo -e "${GREEN}✅ Portfolio within safe limits${NC}"
        return 0
    fi
}

# Function to execute emergency stop
execute_emergency_stop() {
    local reason=$1
    echo -e "${RED}🛑 EXECUTING EMERGENCY STOP: ${reason}${NC}"
    
    # Stop AI Brain
    echo "Stopping AI Brain..."
    curl -X POST http://localhost:8000/control/emergency-stop \
        -H "Content-Type: application/json" \
        -d "{\"reason\": \"${reason}\"}" || echo "AI Brain not responding"
    
    # Stop Rust Executor
    echo "Stopping Rust Executor..."
    curl -X POST http://localhost:8080/emergency_stop \
        -H "Content-Type: application/json" \
        -d "{\"reason\": \"${reason}\"}" || echo "Rust Executor not responding"
    
    # Set emergency flag in Redis
    echo "Setting emergency flag..."
    redis-cli -h localhost -p 6379 set "overmind:emergency_stop" "true" || echo "Redis not responding"
    
    # Stop Docker containers
    echo "Stopping Docker containers..."
    cd /opt/overmind 2>/dev/null || cd .
    docker-compose -f docker-compose.overmind.yml down || echo "Docker not responding"
    
    echo -e "${GREEN}✅ Emergency stop completed${NC}"
}

# Function to send alerts
send_alerts() {
    local message=$1
    echo -e "${YELLOW}📢 Sending alerts...${NC}"
    
    # Log to file
    echo "$(date): ${message}" >> ./logs/emergency_stops.log
    
    # Send Slack notification (if configured)
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 THE OVERMIND PROTOCOL EMERGENCY: ${message}\"}" \
            "$SLACK_WEBHOOK_URL" || echo "Slack notification failed"
    fi
    
    echo "Alert sent: ${message}"
}

# Main execution
main() {
    case "${1:-check}" in
        "check")
            check_portfolio_status
            status=$?
            if [ $status -eq 1 ]; then
                send_alerts "Daily loss limit exceeded (${MAX_DAILY_LOSS} SOL)"
                execute_emergency_stop "Daily loss limit exceeded"
            elif [ $status -eq 2 ]; then
                send_alerts "Emergency threshold reached (${EMERGENCY_THRESHOLD} SOL)"
                execute_emergency_stop "Emergency threshold reached"
            fi
            ;;
        "force")
            send_alerts "Manual emergency stop activated"
            execute_emergency_stop "Manual emergency stop"
            ;;
        "status")
            check_portfolio_status
            ;;
        *)
            echo "Usage: $0 {check|force|status}"
            echo "  check  - Check portfolio and auto-stop if needed"
            echo "  force  - Force emergency stop"
            echo "  status - Show portfolio status only"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
