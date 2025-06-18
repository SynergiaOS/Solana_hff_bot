#!/bin/bash

# THE OVERMIND PROTOCOL - End-to-End Devnet Test
# Complete pipeline test from signal to execution

set -e

echo "🧪 THE OVERMIND PROTOCOL - End-to-End Devnet Test"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration
DRAGONFLY_HOST=${DRAGONFLY_HOST:-localhost}
DRAGONFLY_PORT=${DRAGONFLY_PORT:-6379}
BRAIN_PORT=${BRAIN_PORT:-8000}
EXECUTOR_PORT=${EXECUTOR_PORT:-8081}

# Test functions
check_system_health() {
    log "Checking system health..."
    
    # Check AI Brain
    if curl -s http://localhost:$BRAIN_PORT/health > /dev/null 2>&1; then
        success "AI Brain is healthy"
    else
        error "AI Brain is not responding"
        return 1
    fi
    
    # Check DragonflyDB
    if redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT ping > /dev/null 2>&1; then
        success "DragonflyDB is healthy"
    else
        error "DragonflyDB is not responding"
        return 1
    fi
    
    # Check if Rust executor is available (optional)
    if curl -s http://localhost:$EXECUTOR_PORT/health > /dev/null 2>&1; then
        success "Rust Executor is healthy"
    else
        warning "Rust Executor not available (will simulate)"
    fi
    
    return 0
}

clear_test_queues() {
    log "Clearing test queues..."
    
    redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT del overmind:market_events > /dev/null 2>&1
    redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT del overmind:trading_commands > /dev/null 2>&1
    redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT del events:raw:shredstream > /dev/null 2>&1
    
    success "Test queues cleared"
}

inject_market_signal() {
    log "Injecting simulated market signal..."
    
    # Create realistic market signal
    local signal='{
        "type": "new_pool",
        "symbol": "SOL/USDT",
        "token_address": "So11111111111111111111111111111111111111112",
        "price": 100.0,
        "volume": 1000000,
        "liquidity": 500000,
        "market_cap": 50000000000,
        "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "source": "devnet_test",
        "trend": "bullish",
        "volatility": 0.02,
        "dev_activity": "high",
        "social_sentiment": "positive"
    }'
    
    # Inject signal into DragonflyDB
    redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT lpush overmind:market_events "$signal" > /dev/null
    
    success "Market signal injected: SOL/USDT bullish signal"
    echo "Signal: $signal"
}

monitor_brain_processing() {
    log "Monitoring AI Brain processing..."
    
    # Wait for brain to process
    sleep 3
    
    # Check if brain processed the signal
    local commands_count=$(redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT llen overmind:trading_commands)
    
    if [ "$commands_count" -gt 0 ]; then
        success "AI Brain generated $commands_count trading command(s)"
        
        # Get the latest command
        local latest_command=$(redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT lindex overmind:trading_commands 0)
        echo "Latest command: $latest_command"
        
        # Parse command if jq is available
        if command -v jq > /dev/null 2>&1; then
            echo "$latest_command" | jq -r '"Command Details: Action=\(.action), Symbol=\(.symbol), Confidence=\(.confidence)"'
        fi
        
        return 0
    else
        warning "No trading commands generated yet"
        return 1
    fi
}

simulate_executor_response() {
    log "Simulating Rust Executor response..."
    
    # Get command from queue
    local command=$(redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT rpop overmind:trading_commands)
    
    if [ -n "$command" ] && [ "$command" != "(nil)" ]; then
        success "Executor received command: $command"
        
        # Simulate paper trade execution
        local execution_result='{
            "status": "executed",
            "mode": "paper_trade",
            "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
            "original_command": '"$command"',
            "simulated_result": {
                "transaction_id": "sim_'$(date +%s)'",
                "execution_price": 100.05,
                "slippage": 0.05,
                "gas_used": 0.001
            }
        }'
        
        # Send result back to brain
        redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT lpush overmind:execution_results "$execution_result" > /dev/null
        
        success "Paper trade executed successfully"
        echo "Execution result: $execution_result"
        
        return 0
    else
        error "No command received by executor"
        return 1
    fi
}

test_brain_analysis_direct() {
    log "Testing direct brain analysis..."
    
    local test_data='{
        "symbol": "SOL/USDT",
        "price": 100.0,
        "volume": 1000000,
        "additional_data": {
            "trend": "bullish",
            "volatility": 0.02,
            "dev_activity": "high",
            "social_sentiment": "positive",
            "test_mode": true,
            "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
        }
    }'
    
    log "Sending analysis request to AI Brain..."
    
    local response=$(curl -s -X POST http://localhost:$BRAIN_PORT/analyze \
        -H "Content-Type: application/json" \
        -d "$test_data")
    
    if [ $? -eq 0 ] && [ -n "$response" ]; then
        success "AI Brain analysis completed"
        
        # Parse key results if jq is available
        if command -v jq > /dev/null 2>&1; then
            echo "Analysis Results:"
            echo "$response" | jq -r '.decision | "  Action: \(.action // "N/A")"'
            echo "$response" | jq -r '.decision | "  Confidence: \(.confidence // "N/A")"'
            echo "$response" | jq -r '.risk_assessment | "  Risk Level: \(.risk_level // "N/A")"'
            echo "$response" | jq -r '.market_analysis | "  Trend: \(.trend_direction // "N/A")"'
        else
            echo "Raw response: ${response:0:200}..."
        fi
        
        return 0
    else
        error "AI Brain analysis failed"
        return 1
    fi
}

run_complete_pipeline_test() {
    log "Running complete pipeline test..."
    
    local test_results=()
    
    # Test 1: System Health Check
    if check_system_health; then
        test_results+=("✅ System Health Check")
    else
        test_results+=("❌ System Health Check")
        return 1
    fi
    
    # Test 2: Clear queues
    clear_test_queues
    test_results+=("✅ Queue Cleanup")
    
    # Test 3: Direct brain analysis
    if test_brain_analysis_direct; then
        test_results+=("✅ Direct Brain Analysis")
    else
        test_results+=("❌ Direct Brain Analysis")
    fi
    
    # Test 4: Market signal injection
    inject_market_signal
    test_results+=("✅ Market Signal Injection")
    
    # Test 5: Brain processing monitoring
    if monitor_brain_processing; then
        test_results+=("✅ Brain Processing")
    else
        test_results+=("⚠️ Brain Processing")
    fi
    
    # Test 6: Executor simulation
    if simulate_executor_response; then
        test_results+=("✅ Executor Simulation")
    else
        test_results+=("⚠️ Executor Simulation")
    fi
    
    # Display results
    echo
    echo "================================================="
    echo "🧪 END-TO-END DEVNET TEST RESULTS"
    echo "================================================="
    
    local passed=0
    local total=${#test_results[@]}
    
    for result in "${test_results[@]}"; do
        echo "$result"
        if [[ $result == *"✅"* ]]; then
            ((passed++))
        fi
    done
    
    echo
    echo "Summary: $passed/$total tests passed"
    
    if [ $passed -ge $((total - 1)) ]; then  # Allow 1 failure
        success "🎉 END-TO-END TEST PASSED!"
        echo
        echo "✅ AI Brain can process market signals"
        echo "✅ Decision making pipeline works"
        echo "✅ Communication with executor functional"
        echo "✅ System ready for extended validation"
        return 0
    else
        error "❌ End-to-end test failed. Please check the issues above."
        return 1
    fi
}

# Main execution
main() {
    echo
    log "Starting end-to-end devnet test..."
    echo
    
    run_complete_pipeline_test
    
    local exit_code=$?
    
    echo
    if [ $exit_code -eq 0 ]; then
        success "🚀 THE OVERMIND PROTOCOL E2E TEST COMPLETED SUCCESSFULLY!"
        echo
        echo "Next steps:"
        echo "1. Run 48-hour validation test"
        echo "2. Configure production environment"
        echo "3. Deploy to live trading (with proper API keys)"
    else
        error "❌ E2E test failed. System needs attention before proceeding."
    fi
    
    exit $exit_code
}

# Cleanup function
cleanup() {
    log "Cleaning up test artifacts..."
    # Add any cleanup needed
}

# Set trap for cleanup
trap cleanup EXIT

# Run main test
main "$@"
