#!/bin/bash

# THE OVERMIND PROTOCOL - Communication Integration Test
# Tests communication between AI Brain and Rust Executor via DragonflyDB

set -e

echo "🚀 THE OVERMIND PROTOCOL - Communication Integration Test"
echo "========================================================"

# Configuration
DRAGONFLY_HOST=${DRAGONFLY_HOST:-localhost}
DRAGONFLY_PORT=${DRAGONFLY_PORT:-6379}
BRAIN_PORT=${BRAIN_PORT:-8000}
TEST_TIMEOUT=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Test functions
test_dragonfly_connection() {
    log "Testing DragonflyDB connection..."
    
    if redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT ping > /dev/null 2>&1; then
        success "DragonflyDB connection successful"
        return 0
    else
        error "DragonflyDB connection failed"
        return 1
    fi
}

test_brain_health() {
    log "Testing AI Brain health..."
    
    local response=$(curl -s -w "%{http_code}" http://localhost:$BRAIN_PORT/health -o /tmp/brain_health.json)
    
    if [ "$response" = "200" ]; then
        success "AI Brain health check passed"
        return 0
    else
        error "AI Brain health check failed (HTTP $response)"
        return 1
    fi
}

test_brain_status() {
    log "Getting AI Brain detailed status..."
    
    local response=$(curl -s -w "%{http_code}" http://localhost:$BRAIN_PORT/status -o /tmp/brain_status.json)
    
    if [ "$response" = "200" ]; then
        success "AI Brain status retrieved successfully"
        
        # Parse and display key status information
        if command -v jq > /dev/null 2>&1; then
            echo "Brain Components Status:"
            jq -r '.components | to_entries[] | "  \(.key): \(.value)"' /tmp/brain_status.json
            echo "Memory Stats:"
            jq -r '.memory_stats | "  Total experiences: \(.total_experiences // "N/A")"' /tmp/brain_status.json
        fi
        return 0
    else
        error "AI Brain status check failed (HTTP $response)"
        return 1
    fi
}

clear_dragonfly_queues() {
    log "Clearing DragonflyDB test queues..."
    
    redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT del overmind:market_events > /dev/null 2>&1
    redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT del overmind:trading_commands > /dev/null 2>&1
    redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT del overmind:test:market_events > /dev/null 2>&1
    redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT del overmind:test:trading_commands > /dev/null 2>&1
    
    success "DragonflyDB queues cleared"
}

test_brain_analysis() {
    log "Testing AI Brain market analysis..."
    
    # Prepare test market data
    local test_data='{
        "symbol": "SOL/USDT",
        "price": 100.0,
        "volume": 1000000,
        "additional_data": {
            "trend": "bullish",
            "volatility": 0.02,
            "test_mode": true,
            "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
        }
    }'
    
    log "Sending test market data to AI Brain..."
    echo "Test data: $test_data"
    
    local response=$(curl -s -w "%{http_code}" \
        -X POST http://localhost:$BRAIN_PORT/analyze \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        -o /tmp/brain_analysis.json)
    
    if [ "$response" = "200" ]; then
        success "AI Brain analysis completed successfully"
        
        # Display analysis results
        if command -v jq > /dev/null 2>&1; then
            echo "Analysis Results:"
            jq -r '.decision | "  Action: \(.action // "N/A")"' /tmp/brain_analysis.json
            jq -r '.decision | "  Confidence: \(.confidence // "N/A")"' /tmp/brain_analysis.json
            jq -r '.decision | "  Reasoning: \(.reasoning // "N/A")"' /tmp/brain_analysis.json
            jq -r '.risk_assessment | "  Risk Level: \(.risk_level // "N/A")"' /tmp/brain_analysis.json
        fi
        return 0
    else
        error "AI Brain analysis failed (HTTP $response)"
        if [ -f /tmp/brain_analysis.json ]; then
            cat /tmp/brain_analysis.json
        fi
        return 1
    fi
}

monitor_dragonfly_commands() {
    log "Monitoring DragonflyDB for trading commands..."
    
    # Check if any commands were sent to the trading queue
    local command_count=$(redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT llen overmind:trading_commands)
    
    if [ "$command_count" -gt 0 ]; then
        success "Found $command_count trading command(s) in queue"
        
        # Display the latest command
        local latest_command=$(redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT lindex overmind:trading_commands 0)
        echo "Latest command: $latest_command"
        
        # Parse command if jq is available
        if command -v jq > /dev/null 2>&1; then
            echo "$latest_command" | jq -r '"Command Details: Action=\(.action), Symbol=\(.symbol), Confidence=\(.confidence)"'
        fi
        return 0
    else
        warning "No trading commands found in queue"
        return 1
    fi
}

test_memory_functionality() {
    log "Testing AI Brain memory functionality..."
    
    # Test memory stats
    local response=$(curl -s -w "%{http_code}" http://localhost:$BRAIN_PORT/memory/stats -o /tmp/memory_stats.json)
    
    if [ "$response" = "200" ]; then
        success "Memory stats retrieved successfully"
        
        if command -v jq > /dev/null 2>&1; then
            echo "Memory Statistics:"
            jq -r '"  Total experiences: \(.total_experiences // "N/A")"' /tmp/memory_stats.json
            jq -r '"  Collection name: \(.collection_name // "N/A")"' /tmp/memory_stats.json
            jq -r '"  Embedding model: \(.embedding_model // "N/A")"' /tmp/memory_stats.json
        fi
        return 0
    else
        error "Memory stats retrieval failed (HTTP $response)"
        return 1
    fi
}

# Main test execution
main() {
    echo
    log "Starting communication integration tests..."
    echo
    
    local test_results=()
    
    # Test 1: DragonflyDB Connection
    if test_dragonfly_connection; then
        test_results+=("✅ DragonflyDB Connection")
    else
        test_results+=("❌ DragonflyDB Connection")
    fi
    
    # Test 2: AI Brain Health
    if test_brain_health; then
        test_results+=("✅ AI Brain Health")
    else
        test_results+=("❌ AI Brain Health")
        error "Cannot proceed without healthy AI Brain"
        exit 1
    fi
    
    # Test 3: AI Brain Status
    if test_brain_status; then
        test_results+=("✅ AI Brain Status")
    else
        test_results+=("❌ AI Brain Status")
    fi
    
    # Test 4: Clear queues for clean test
    clear_dragonfly_queues
    test_results+=("✅ Queue Cleanup")
    
    # Test 5: Memory functionality
    if test_memory_functionality; then
        test_results+=("✅ Memory Functionality")
    else
        test_results+=("❌ Memory Functionality")
    fi
    
    # Test 6: AI Brain Analysis (main test)
    if test_brain_analysis; then
        test_results+=("✅ AI Brain Analysis")
    else
        test_results+=("❌ AI Brain Analysis")
    fi
    
    # Test 7: Monitor DragonflyDB for commands
    sleep 2  # Give time for command to be sent
    if monitor_dragonfly_commands; then
        test_results+=("✅ Command Communication")
    else
        test_results+=("❌ Command Communication")
    fi
    
    # Display test results summary
    echo
    echo "========================================================"
    echo "🧪 COMMUNICATION INTEGRATION TEST RESULTS"
    echo "========================================================"
    
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
    
    if [ $passed -eq $total ]; then
        success "🎉 ALL COMMUNICATION TESTS PASSED!"
        echo
        echo "✅ AI Brain can successfully communicate with DragonflyDB"
        echo "✅ Trading commands are being generated and sent"
        echo "✅ System is ready for end-to-end testing"
        exit 0
    else
        error "❌ Some tests failed. Please check the issues above."
        exit 1
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up test artifacts..."
    rm -f /tmp/brain_*.json /tmp/memory_*.json
}

# Set trap for cleanup
trap cleanup EXIT

# Run main test
main "$@"
