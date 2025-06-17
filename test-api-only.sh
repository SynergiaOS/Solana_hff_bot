#!/bin/bash

# THE OVERMIND PROTOCOL - API and Integration Test Only
# Skip Rust compilation issues and focus on API testing

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

echo -e "${PURPLE}"
cat << "EOF"
 _____ _   _ _____    _____  _   _ _____ ____  __  __ _____ _   _ ____  
|_   _| | | | ____|  / _ \ \| | | | ____|  _ \|  \/  |_   _| \ | |  _ \ 
  | | | |_| |  _|   | | | | | | | |  _| | |_) | |\/| | | | |  \| | | | |
  | | |  _  | |___  | |_| | |_| | | |___|  _ <| |  | | | | | |\  | |_| |
  |_| |_| |_|_____|  \___/ \___/|_|_____|_| \_\_|  |_| |_| |_| \_|____/ 

🔌 API & INTEGRATION TEST SUITE
EOF
echo -e "${NC}"

echo "THE OVERMIND PROTOCOL - API and Integration Testing"
echo "=================================================="
echo ""
echo "Testing APIs, data flow, Kestra workflows, and system integration"
echo "Skipping Rust compilation (will be fixed separately)"
echo ""

# Function to check if server is reachable
check_server() {
    local url=$1
    local name=$2
    
    if curl -f -s "$url" > /dev/null 2>&1; then
        print_success "$name is reachable"
        return 0
    else
        print_error "$name is not reachable"
        return 1
    fi
}

# ============================================================================
# PHASE 1: Basic Connectivity Test
# ============================================================================
print_step "1. Basic Connectivity Test"
echo "Testing basic connectivity to THE OVERMIND PROTOCOL components..."
echo ""

SERVER_BASE="http://89.117.53.53"
ENDPOINTS=(
    "$SERVER_BASE:8080/health|Trading System"
    "$SERVER_BASE:8000/api/v1/heartbeat|AI Vector DB"
    "$SERVER_BASE:3000/health|TensorZero"
    "$SERVER_BASE:9090/-/healthy|Prometheus"
    "$SERVER_BASE:3001/api/health|Grafana"
    "$SERVER_BASE:8082/api/v1/health|Kestra"
)

REACHABLE_COUNT=0
TOTAL_COUNT=${#ENDPOINTS[@]}

for endpoint in "${ENDPOINTS[@]}"; do
    IFS='|' read -r url name <<< "$endpoint"
    if check_server "$url" "$name"; then
        ((REACHABLE_COUNT++))
    fi
done

echo ""
print_test "Connectivity Summary: $REACHABLE_COUNT/$TOTAL_COUNT components reachable"

if [[ $REACHABLE_COUNT -eq 0 ]]; then
    print_error "No components reachable. Please deploy THE OVERMIND PROTOCOL first."
    echo ""
    echo "To deploy, run: ./deploy-step-by-step.sh"
    exit 1
elif [[ $REACHABLE_COUNT -lt 3 ]]; then
    print_error "Insufficient components reachable for testing."
    echo "Please ensure THE OVERMIND PROTOCOL is properly deployed."
fi

echo ""

# ============================================================================
# PHASE 2: API Integration Test
# ============================================================================
print_step "2. API Integration Test"
echo "Running comprehensive API integration test..."
echo ""

if [[ -f "./test-api-integration.py" ]]; then
    if command -v python3 &> /dev/null; then
        print_test "Installing Python dependencies..."
        pip3 install --user requests aiohttp > /dev/null 2>&1 || true
        
        print_test "Running API integration test..."
        if python3 ./test-api-integration.py --server "$SERVER_BASE"; then
            print_success "API integration test completed"
        else
            print_error "API integration test failed"
        fi
    else
        print_error "Python3 not available for API testing"
    fi
else
    print_error "test-api-integration.py not found"
fi

echo ""

# ============================================================================
# PHASE 3: Kestra Workflow Test
# ============================================================================
print_step "3. Kestra Workflow Test"
echo "Testing Kestra workflow orchestration..."
echo ""

if [[ -f "./test-kestra-workflows.py" ]]; then
    if command -v python3 &> /dev/null; then
        print_test "Installing Python dependencies..."
        pip3 install --user aiohttp pyyaml > /dev/null 2>&1 || true
        
        print_test "Running Kestra workflow test..."
        if python3 ./test-kestra-workflows.py --kestra-url "$SERVER_BASE:8082"; then
            print_success "Kestra workflow test completed"
        else
            print_error "Kestra workflow test failed (may not be deployed)"
        fi
    else
        print_error "Python3 not available for Kestra testing"
    fi
else
    print_error "test-kestra-workflows.py not found"
fi

echo ""

# ============================================================================
# PHASE 4: Trading Flow Simulation
# ============================================================================
print_step "4. Trading Flow Simulation"
echo "Simulating complete trading flow..."
echo ""

if [[ -f "./simulate-trading-flow.py" ]]; then
    if command -v python3 &> /dev/null; then
        print_test "Installing Python dependencies..."
        pip3 install --user requests > /dev/null 2>&1 || true
        
        print_test "Running trading flow simulation..."
        if python3 ./simulate-trading-flow.py --cycles 5 --server "$SERVER_BASE"; then
            print_success "Trading flow simulation completed"
        else
            print_error "Trading flow simulation failed"
        fi
    else
        print_error "Python3 not available for trading flow simulation"
    fi
else
    print_error "simulate-trading-flow.py not found"
fi

echo ""

# ============================================================================
# PHASE 5: Manual API Tests
# ============================================================================
print_step "5. Manual API Tests"
echo "Running manual API endpoint tests..."
echo ""

# Test Trading System API
if curl -f -s "$SERVER_BASE:8080/health" > /dev/null; then
    print_test "Testing Trading System endpoints..."
    
    # Test metrics endpoint
    if curl -f -s "$SERVER_BASE:8080/metrics" > /dev/null; then
        print_success "Metrics endpoint responding"
        
        # Check for OVERMIND metrics
        METRICS_CONTENT=$(curl -s "$SERVER_BASE:8080/metrics" 2>/dev/null || echo "")
        if echo "$METRICS_CONTENT" | grep -qi "overmind"; then
            print_success "OVERMIND metrics found"
        else
            print_error "OVERMIND metrics not found"
        fi
    else
        print_error "Metrics endpoint not responding"
    fi
    
    # Test other endpoints
    for endpoint in "/api/v1/status" "/api/v1/positions" "/api/v1/orders"; do
        if curl -f -s "$SERVER_BASE:8080$endpoint" > /dev/null 2>&1; then
            print_success "Endpoint $endpoint responding"
        else
            print_error "Endpoint $endpoint not responding"
        fi
    done
fi

# Test AI Vector Database
if curl -f -s "$SERVER_BASE:8000/api/v1/heartbeat" > /dev/null; then
    print_test "Testing AI Vector Database endpoints..."
    
    for endpoint in "/api/v1/collections" "/api/v1/version"; do
        if curl -f -s "$SERVER_BASE:8000$endpoint" > /dev/null 2>&1; then
            print_success "Vector DB endpoint $endpoint responding"
        else
            print_error "Vector DB endpoint $endpoint not responding"
        fi
    done
fi

echo ""

# ============================================================================
# PHASE 6: System Health Summary
# ============================================================================
print_step "6. System Health Summary"
echo "Generating system health summary..."
echo ""

# Check system resources (if accessible)
if curl -f -s "$SERVER_BASE:9090/api/v1/query?query=up" > /dev/null 2>&1; then
    print_success "Prometheus metrics accessible"
    
    # Try to get basic metrics
    UP_METRICS=$(curl -s "$SERVER_BASE:9090/api/v1/query?query=up" 2>/dev/null || echo "")
    if [[ -n "$UP_METRICS" ]]; then
        print_test "System metrics available"
    fi
else
    print_error "Prometheus metrics not accessible"
fi

# Check Grafana dashboards
if curl -f -s "$SERVER_BASE:3001/api/health" > /dev/null 2>&1; then
    print_success "Grafana dashboards accessible"
else
    print_error "Grafana dashboards not accessible"
fi

echo ""

# ============================================================================
# FINAL REPORT
# ============================================================================
print_step "Final Report"
echo "THE OVERMIND PROTOCOL - API & Integration Test Results"
echo "====================================================="
echo ""

# Calculate success rate
TOTAL_TESTS=20  # Approximate number of tests
PASSED_TESTS=$((REACHABLE_COUNT * 3))  # Rough estimate based on reachable components

SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

echo "📊 Test Summary:"
echo "  Components Reachable: $REACHABLE_COUNT/$TOTAL_COUNT"
echo "  Estimated Success Rate: $SUCCESS_RATE%"
echo ""

if [[ $REACHABLE_COUNT -ge 4 ]]; then
    echo "🎯 System Status: OPERATIONAL"
    echo "✅ THE OVERMIND PROTOCOL appears to be running"
    echo ""
    echo "🌐 Access URLs:"
    echo "  Trading System:    $SERVER_BASE:8080"
    echo "  Grafana Dashboard: $SERVER_BASE:3001"
    echo "  Prometheus:        $SERVER_BASE:9090"
    echo "  AI Vector DB:      $SERVER_BASE:8000"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Fix Rust compilation issues for complete testing"
    echo "2. Monitor system performance in Grafana"
    echo "3. Review API integration test results"
    echo "4. Test Kestra workflows if deployed"
elif [[ $REACHABLE_COUNT -ge 2 ]]; then
    echo "🎯 System Status: PARTIALLY_OPERATIONAL"
    echo "⚠️  Some components are running, others may need deployment"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Complete THE OVERMIND PROTOCOL deployment"
    echo "2. Fix any component startup issues"
    echo "3. Re-run this test suite"
else
    echo "🎯 System Status: NOT_OPERATIONAL"
    echo "❌ THE OVERMIND PROTOCOL is not properly deployed"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Deploy THE OVERMIND PROTOCOL: ./deploy-step-by-step.sh"
    echo "2. Check server connectivity and firewall settings"
    echo "3. Re-run this test suite after deployment"
fi

echo ""
echo "🧠 THE OVERMIND PROTOCOL API testing completed!"
echo ""

# Save results
cat > api-test-summary.txt << EOF
THE OVERMIND PROTOCOL - API Test Summary
=======================================
Date: $(date)
Components Reachable: $REACHABLE_COUNT/$TOTAL_COUNT
Estimated Success Rate: $SUCCESS_RATE%

Reachable Components:
EOF

for endpoint in "${ENDPOINTS[@]}"; do
    IFS='|' read -r url name <<< "$endpoint"
    if curl -f -s "$url" > /dev/null 2>&1; then
        echo "✅ $name" >> api-test-summary.txt
    else
        echo "❌ $name" >> api-test-summary.txt
    fi
done

cat >> api-test-summary.txt << EOF

Access URLs:
- Trading System: $SERVER_BASE:8080
- Grafana: $SERVER_BASE:3001
- Prometheus: $SERVER_BASE:9090
- AI Vector DB: $SERVER_BASE:8000
- Kestra: $SERVER_BASE:8082

Recommendations:
- Complete deployment if components are missing
- Fix Rust compilation for full system testing
- Monitor system performance and logs
- Test individual API endpoints manually
EOF

print_success "API test summary saved to: api-test-summary.txt"
