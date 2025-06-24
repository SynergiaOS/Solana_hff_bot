#!/bin/bash
# THE OVERMIND PROTOCOL - Command Line Control Interface
# Usage: ./overmind-control.sh [command]

# Configuration
API_HOST="localhost"
API_PORT="8000"
KESTRA_HOST="localhost"
KESTRA_PORT="8080"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed.${NC}"
    echo "Please install jq with: sudo apt install jq"
    exit 1
fi

# Function to display help
show_help() {
    echo -e "${BLUE}THE OVERMIND PROTOCOL - Command Line Control${NC}"
    echo ""
    echo "Usage: ./overmind-control.sh [command]"
    echo ""
    echo "Commands:"
    echo "  status              - Show system status"
    echo "  transactions        - Show recent transactions"
    echo "  wallets             - Show wallet balances"
    echo "  start [paper|live]  - Start the system (paper trading by default)"
    echo "  stop                - Emergency stop (soft - stops new trades)"
    echo "  stop-hard           - Hard emergency stop (shuts down system)"
    echo "  resume              - Resume trading after soft stop"
    echo "  help                - Show this help message"
    echo ""
}

# Function to check API health
check_api_health() {
    if ! curl -s "http://${API_HOST}:${API_PORT}/health" > /dev/null; then
        echo -e "${RED}Error: Cannot connect to THE OVERMIND PROTOCOL API.${NC}"
        echo "Make sure the system is running and API is accessible."
        return 1
    fi
    return 0
}

# Function to get system status
get_status() {
    check_api_health || return 1
    
    echo -e "${BLUE}THE OVERMIND PROTOCOL - System Status${NC}"
    echo ""
    
    # Get status from API
    STATUS=$(curl -s "http://${API_HOST}:${API_PORT}/status")
    
    # Extract and display key information
    SYSTEM_STATUS=$(echo $STATUS | jq -r '.status')
    AI_STATUS=$(echo $STATUS | jq -r '.ai_brain_status')
    EXECUTOR_STATUS=$(echo $STATUS | jq -r '.rust_executor_status')
    EMERGENCY=$(echo $STATUS | jq -r '.emergency_stop_active')
    PNL=$(echo $STATUS | jq -r '.total_pnl_24h')
    POSITIONS=$(echo $STATUS | jq -r '.open_positions')
    
    # Display status with colors
    if [[ "$SYSTEM_STATUS" == "OPERATIONAL" ]]; then
        echo -e "System Status: ${GREEN}$SYSTEM_STATUS${NC}"
    else
        echo -e "System Status: ${RED}$SYSTEM_STATUS${NC}"
    fi
    
    echo -e "AI Brain: ${BLUE}$AI_STATUS${NC}"
    echo -e "Rust Executor: ${BLUE}$EXECUTOR_STATUS${NC}"
    
    if [[ "$EMERGENCY" == "true" ]]; then
        echo -e "Emergency Stop: ${RED}ACTIVE${NC}"
    else
        echo -e "Emergency Stop: ${GREEN}INACTIVE${NC}"
    fi
    
    echo ""
    echo -e "24h PnL: ${BLUE}$PNL USDC${NC}"
    echo -e "Open Positions: ${BLUE}$POSITIONS${NC}"
    
    # Show detailed memory stats
    echo ""
    echo -e "${BLUE}Memory Stats:${NC}"
    echo $STATUS | jq -r '.detailed_brain_status.memory_stats'
    
    return 0
}

# Function to get recent transactions
get_transactions() {
    check_api_health || return 1
    
    echo -e "${BLUE}THE OVERMIND PROTOCOL - Recent Transactions${NC}"
    echo ""
    
    # Get transactions from API
    TRANSACTIONS=$(curl -s "http://${API_HOST}:${API_PORT}/logs/transactions?limit=10")
    
    # Check if we got valid JSON
    if ! echo $TRANSACTIONS | jq . > /dev/null 2>&1; then
        echo -e "${RED}Error: Failed to get transaction data.${NC}"
        return 1
    fi
    
    # Check if we have any transactions
    if [[ $(echo $TRANSACTIONS | jq '. | length') -eq 0 ]]; then
        echo -e "${YELLOW}No transactions found.${NC}"
        return 0
    fi
    
    # Display transactions in a table format
    echo -e "TIME\t\t\tACTION\tSYMBOL\tPRICE\t\tQUANTITY\tRESULT\tPNL"
    echo -e "----\t\t\t------\t------\t-----\t\t--------\t------\t---"
    
    echo $TRANSACTIONS | jq -r '.[] | "\(.timestamp)\t\(.action)\t\(.symbol)\t\(.price)\t\(.quantity)\t\(.result)\t\(.pnl)"'
    
    return 0
}

# Function to get wallet balances
get_wallets() {
    check_api_health || return 1
    
    echo -e "${BLUE}THE OVERMIND PROTOCOL - Wallet Balances${NC}"
    echo ""
    
    # Get wallet balances from API
    WALLETS=$(curl -s "http://${API_HOST}:${API_PORT}/wallets/status")
    
    # Check if we got valid JSON
    if ! echo $WALLETS | jq . > /dev/null 2>&1; then
        echo -e "${RED}Error: Failed to get wallet data.${NC}"
        return 1
    fi
    
    # Display wallet balances
    echo $WALLETS | jq -r 'to_entries[] | "\(.key):\n  Address: \(.value.address)\n  SOL: \(.value.balance_sol)\n  USDC: \(.value.balance_usdc)\n"'
    
    return 0
}

# Function to start the system
start_system() {
    MODE=${1:-paper}
    
    echo -e "${BLUE}Starting THE OVERMIND PROTOCOL in ${MODE} mode...${NC}"
    
    # Use Kestra API to trigger the workflow
    WORKFLOW_ID="start-overmind-protocol"
    NAMESPACE="operations.overmind"
    
    # Prepare inputs
    INPUTS="{\"trading_mode\":\"${MODE}\",\"ai_mode\":\"enabled\"}"
    
    # Trigger workflow
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"namespace\":\"${NAMESPACE}\",\"flowId\":\"${WORKFLOW_ID}\",\"inputs\":${INPUTS}}" \
        "http://${KESTRA_HOST}:${KESTRA_PORT}/api/v1/executions")
    
    # Check response
    if echo $RESPONSE | jq -e '.id' > /dev/null 2>&1; then
        EXECUTION_ID=$(echo $RESPONSE | jq -r '.id')
        echo -e "${GREEN}System startup initiated. Execution ID: ${EXECUTION_ID}${NC}"
        echo "Waiting for system to start..."
        
        # Wait for system to start (up to 30 seconds)
        for i in {1..30}; do
            sleep 1
            if curl -s "http://${API_HOST}:${API_PORT}/health" > /dev/null 2>&1; then
                echo -e "${GREEN}System started successfully!${NC}"
                get_status
                return 0
            fi
            echo -n "."
        done
        
        echo -e "${YELLOW}Timeout waiting for system to start. Check Kestra logs.${NC}"
    else
        echo -e "${RED}Failed to start system. Response: ${RESPONSE}${NC}"
        return 1
    fi
}

# Function to stop the system (soft)
stop_system_soft() {
    check_api_health || return 1
    
    echo -e "${YELLOW}Activating emergency stop (soft - no new trades)...${NC}"
    
    # Call emergency stop API
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"reason":"Manual emergency stop via CLI"}' \
        "http://${API_HOST}:${API_PORT}/control/emergency-stop")
    
    # Check response
    if echo $RESPONSE | jq -e '.status' > /dev/null 2>&1; then
        echo -e "${GREEN}Emergency stop activated successfully.${NC}"
        echo "System will not open new positions but will continue running."
        return 0
    else
        echo -e "${RED}Failed to activate emergency stop. Response: ${RESPONSE}${NC}"
        return 1
    fi
}

# Function to stop the system (hard)
stop_system_hard() {
    echo -e "${RED}Activating HARD emergency stop (shutting down system)...${NC}"
    
    # Use Kestra API to trigger the workflow
    WORKFLOW_ID="emergency-stop-overmind"
    NAMESPACE="operations.overmind"
    
    # Prepare inputs
    INPUTS="{\"stop_type\":\"hard\"}"
    
    # Trigger workflow
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "{\"namespace\":\"${NAMESPACE}\",\"flowId\":\"${WORKFLOW_ID}\",\"inputs\":${INPUTS}}" \
        "http://${KESTRA_HOST}:${KESTRA_PORT}/api/v1/executions")
    
    # Check response
    if echo $RESPONSE | jq -e '.id' > /dev/null 2>&1; then
        EXECUTION_ID=$(echo $RESPONSE | jq -r '.id')
        echo -e "${GREEN}Hard stop initiated. Execution ID: ${EXECUTION_ID}${NC}"
        echo "System is shutting down..."
        return 0
    else
        echo -e "${RED}Failed to initiate hard stop. Response: ${RESPONSE}${NC}"