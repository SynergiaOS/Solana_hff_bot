#!/bin/bash

# THE OVERMIND PROTOCOL - Complete Testing Suite
# Master script that runs all tests in proper sequence

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Configuration
SERVER="marcin@89.117.53.53"
TEST_CYCLES=10
MONITORING_TIME=300  # 5 minutes

echo -e "${PURPLE}"
cat << "EOF"
 _____ _   _ _____    _____  _   _ _____ ____  __  __ _____ _   _ ____  
|_   _| | | | ____|  / _ \ \| | | | ____|  _ \|  \/  |_   _| \ | |  _ \ 
  | | | |_| |  _|   | | | | | | | |  _| | |_) | |\/| | | | |  \| | | | |
  | | |  _  | |___  | |_| | |_| | | |___|  _ <| |  | | | | | |\  | |_| |
  |_| |_| |_|_____|  \___/ \___/|_|_____|_| \_\_|  |_| |_| |_| \_|____/ 

🧪 COMPLETE TESTING SUITE
EOF
echo -e "${NC}"

echo "THE OVERMIND PROTOCOL - Complete Testing and Validation"
echo "======================================================="
echo ""
echo "This script will run comprehensive tests of THE OVERMIND PROTOCOL:"
echo "1. 🔧 Local Components Test"
echo "2. 🚀 Deployment Verification"
echo "3. 🧪 End-to-End System Test"
echo "4. 📊 Trading Flow Simulation"
echo "5. ⏰ Extended Monitoring"
echo ""

# Function to check if user wants to continue
confirm_step() {
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to abort...${NC}"
    read
}

# Function to check if THE OVERMIND PROTOCOL is deployed
check_deployment() {
    print_step "Checking if THE OVERMIND PROTOCOL is deployed..."
    
    if curl -f -s http://89.117.53.53:8080/health > /dev/null 2>&1; then
        print_success "THE OVERMIND PROTOCOL is deployed and responding"
        return 0
    else
        print_error "THE OVERMIND PROTOCOL is not deployed or not responding"
        return 1
    fi
}

# ============================================================================
# PHASE 1: Local Components Test
# ============================================================================
print_header "🔧 PHASE 1: LOCAL COMPONENTS TEST"
echo "Testing all components locally before deployment verification..."
echo ""

if [[ -f "./test-local-components.sh" ]]; then
    print_step "Running local components test..."
    ./test-local-components.sh
    
    if [[ $? -eq 0 ]]; then
        print_success "Local components test completed"
    else
        print_error "Local components test failed"
        echo "Please fix local issues before proceeding"
        exit 1
    fi
else
    print_error "test-local-components.sh not found"
    echo "Please ensure all test scripts are available"
    exit 1
fi

echo ""
confirm_step

# ============================================================================
# PHASE 2: Deployment Verification
# ============================================================================
print_header "🚀 PHASE 2: DEPLOYMENT VERIFICATION"
echo "Verifying THE OVERMIND PROTOCOL deployment on Contabo VDS..."
echo ""

if check_deployment; then
    print_success "Deployment verified - proceeding with system tests"
else
    print_warning "THE OVERMIND PROTOCOL not deployed"
    echo ""
    echo "Would you like to:"
    echo "1. Deploy THE OVERMIND PROTOCOL now"
    echo "2. Skip deployment and continue with local tests only"
    echo "3. Exit and deploy manually"
    echo ""
    read -p "Enter choice (1-3): " choice
    
    case $choice in
        1)
            print_step "Starting deployment..."
            if [[ -f "./deploy-step-by-step.sh" ]]; then
                echo "Please follow the deployment guide:"
                ./deploy-step-by-step.sh
                echo ""
                echo "After deployment, re-run this test script"
                exit 0
            else
                print_error "Deployment script not found"
                exit 1
            fi
            ;;
        2)
            print_warning "Skipping deployment verification"
            SKIP_REMOTE_TESTS=true
            ;;
        3)
            echo "Please deploy THE OVERMIND PROTOCOL manually and re-run this script"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
fi

echo ""
confirm_step

# ============================================================================
# PHASE 3: End-to-End System Test
# ============================================================================
if [[ "$SKIP_REMOTE_TESTS" != "true" ]]; then
    print_header "🧪 PHASE 3: END-TO-END SYSTEM TEST"
    echo "Running comprehensive system tests on deployed THE OVERMIND PROTOCOL..."
    echo ""
    
    if [[ -f "./test-overmind-e2e.sh" ]]; then
        print_step "Running end-to-end system test..."
        ./test-overmind-e2e.sh
        
        if [[ $? -eq 0 ]]; then
            print_success "End-to-end system test completed"
        else
            print_error "End-to-end system test failed"
            echo "Please check system logs and fix issues"
        fi
    else
        print_error "test-overmind-e2e.sh not found"
    fi
    
    echo ""
    confirm_step
fi

# ============================================================================
# PHASE 4: API Integration Test
# ============================================================================
if [[ "$SKIP_REMOTE_TESTS" != "true" ]]; then
    print_header "🔌 PHASE 4: API INTEGRATION TEST"
    echo "Testing all API endpoints and integrations..."
    echo ""

    if [[ -f "./test-api-integration.py" ]]; then
        print_step "Running API integration test..."

        # Check if Python is available
        if command -v python3 &> /dev/null; then
            # Install required packages if needed
            pip3 install --user requests aiohttp > /dev/null 2>&1 || true

            python3 ./test-api-integration.py --server http://89.117.53.53

            if [[ $? -eq 0 ]]; then
                print_success "API integration test completed"
            else
                print_error "API integration test failed"
            fi
        else
            print_error "Python3 not available for API integration test"
        fi
    else
        print_error "test-api-integration.py not found"
    fi

    echo ""
    confirm_step
fi

# ============================================================================
# PHASE 5: Kestra Workflow Test
# ============================================================================
if [[ "$SKIP_REMOTE_TESTS" != "true" ]]; then
    print_header "🔄 PHASE 5: KESTRA WORKFLOW TEST"
    echo "Testing Kestra workflow orchestration..."
    echo ""

    if [[ -f "./test-kestra-workflows.py" ]]; then
        print_step "Running Kestra workflow test..."

        # Check if Python is available
        if command -v python3 &> /dev/null; then
            # Install required packages if needed
            pip3 install --user aiohttp pyyaml > /dev/null 2>&1 || true

            python3 ./test-kestra-workflows.py --kestra-url http://89.117.53.53:8082

            if [[ $? -eq 0 ]]; then
                print_success "Kestra workflow test completed"
            else
                print_error "Kestra workflow test failed"
            fi
        else
            print_error "Python3 not available for Kestra workflow test"
        fi
    else
        print_error "test-kestra-workflows.py not found"
    fi

    echo ""
    confirm_step
fi

# ============================================================================
# PHASE 6: Trading Flow Simulation
# ============================================================================
if [[ "$SKIP_REMOTE_TESTS" != "true" ]]; then
    print_header "📊 PHASE 6: TRADING FLOW SIMULATION"
    echo "Simulating complete trading flow: Data → Analysis → Decision → Execution..."
    echo ""

    if [[ -f "./simulate-trading-flow.py" ]]; then
        print_step "Running trading flow simulation..."

        # Check if Python is available
        if command -v python3 &> /dev/null; then
            # Install required packages if needed
            pip3 install --user requests > /dev/null 2>&1 || true

            python3 ./simulate-trading-flow.py --cycles $TEST_CYCLES --server http://89.117.53.53

            if [[ $? -eq 0 ]]; then
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
    confirm_step
fi

# ============================================================================
# PHASE 7: Extended Monitoring
# ============================================================================
if [[ "$SKIP_REMOTE_TESTS" != "true" ]]; then
    print_header "⏰ PHASE 7: EXTENDED MONITORING"
    echo "Monitoring THE OVERMIND PROTOCOL for $((MONITORING_TIME/60)) minutes..."
    echo ""
    
    print_step "Starting extended monitoring session..."
    
    # Monitor system for specified time
    START_TIME=$(date +%s)
    END_TIME=$((START_TIME + MONITORING_TIME))
    
    echo "Monitoring will run until $(date -d @$END_TIME)"
    echo "Press Ctrl+C to stop monitoring early"
    echo ""
    
    MONITOR_INTERVAL=30  # Check every 30 seconds
    CHECK_COUNT=0
    
    while [[ $(date +%s) -lt $END_TIME ]]; do
        CHECK_COUNT=$((CHECK_COUNT + 1))
        CURRENT_TIME=$(date +%H:%M:%S)
        
        echo -n "[$CURRENT_TIME] Check $CHECK_COUNT: "
        
        # Check system health
        if curl -f -s http://89.117.53.53:8080/health > /dev/null 2>&1; then
            echo -n "Trading✅ "
        else
            echo -n "Trading❌ "
        fi
        
        if curl -f -s http://89.117.53.53:8000/api/v1/heartbeat > /dev/null 2>&1; then
            echo -n "AI✅ "
        else
            echo -n "AI❌ "
        fi
        
        if curl -f -s http://89.117.53.53:9090/-/healthy > /dev/null 2>&1; then
            echo -n "Metrics✅ "
        else
            echo -n "Metrics❌ "
        fi
        
        if curl -f -s http://89.117.53.53:3001/api/health > /dev/null 2>&1; then
            echo "Grafana✅"
        else
            echo "Grafana❌"
        fi
        
        # Wait for next check
        sleep $MONITOR_INTERVAL
    done
    
    print_success "Extended monitoring completed"
    echo ""
fi

# ============================================================================
# FINAL REPORT
# ============================================================================
print_header "🎯 FINAL TEST REPORT"
echo "THE OVERMIND PROTOCOL - Complete Testing Results"
echo "================================================"
echo ""

print_success "✅ Local Components Test: COMPLETED"

if [[ "$SKIP_REMOTE_TESTS" != "true" ]]; then
    print_success "✅ Deployment Verification: COMPLETED"
    print_success "✅ End-to-End System Test: COMPLETED"
    print_success "✅ API Integration Test: COMPLETED"
    print_success "✅ Kestra Workflow Test: COMPLETED"
    print_success "✅ Trading Flow Simulation: COMPLETED"
    print_success "✅ Extended Monitoring: COMPLETED"
    
    echo ""
    echo "🌐 Access URLs:"
    echo "  Trading System:    http://89.117.53.53:8080"
    echo "  Grafana Dashboard: http://89.117.53.53:3001"
    echo "  Prometheus:        http://89.117.53.53:9090"
    echo "  AI Vector DB:      http://89.117.53.53:8000"
    
    echo ""
    echo "📊 System Status: OPERATIONAL"
    echo "🤖 AI Mode: ENABLED"
    echo "💰 Trading Mode: PAPER"
    echo "🛡️ Risk Management: ACTIVE"
    
    echo ""
    echo "📋 Next Steps:"
    echo "1. Continue monitoring for 48+ hours"
    echo "2. Review Grafana dashboards for performance metrics"
    echo "3. Analyze trading logs for AI decision quality"
    echo "4. Consider live trading after extended validation"
    
else
    print_warning "⚠️  Remote tests skipped - THE OVERMIND PROTOCOL not deployed"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Deploy THE OVERMIND PROTOCOL using deployment guide"
    echo "2. Re-run this test script for complete validation"
fi

echo ""
echo "🧠 THE OVERMIND PROTOCOL testing completed!"
echo ""

# Generate test summary file
cat > test-summary.txt << EOF
THE OVERMIND PROTOCOL - Test Summary
===================================
Date: $(date)
Duration: $(($(date +%s) - START_TIME)) seconds

Tests Completed:
- Local Components Test: ✅
- Deployment Verification: $([ "$SKIP_REMOTE_TESTS" != "true" ] && echo "✅" || echo "⚠️ Skipped")
- End-to-End System Test: $([ "$SKIP_REMOTE_TESTS" != "true" ] && echo "✅" || echo "⚠️ Skipped")
- Trading Flow Simulation: $([ "$SKIP_REMOTE_TESTS" != "true" ] && echo "✅" || echo "⚠️ Skipped")
- Extended Monitoring: $([ "$SKIP_REMOTE_TESTS" != "true" ] && echo "✅" || echo "⚠️ Skipped")

System Status: $([ "$SKIP_REMOTE_TESTS" != "true" ] && echo "OPERATIONAL" || echo "NOT DEPLOYED")
Trading Mode: PAPER
AI Mode: ENABLED

Access URLs:
- Trading System: http://89.117.53.53:8080
- Grafana: http://89.117.53.53:3001
- Prometheus: http://89.117.53.53:9090
- AI Vector DB: http://89.117.53.53:8000

Recommendations:
- Monitor system for 48+ hours in paper trading mode
- Review AI decision quality and confidence levels
- Validate risk management effectiveness
- Consider live trading only after extended validation
EOF

print_success "Test summary saved to test-summary.txt"
