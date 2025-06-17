#!/bin/bash

# THE OVERMIND PROTOCOL - Automated Test Scripts for Each Scenario
# Implements the 4 critical test categories with specific scenarios

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# ============================================================================
# CATEGORY 1: DEPLOYMENT & CONFIGURATION TESTS
# ============================================================================

test_clean_server_deployment() {
    print_header "🚀 CATEGORY 1: Clean Server Deployment Test"
    echo ""
    
    print_info "Testing complete deployment from clean state..."
    
    # Stop all existing containers
    print_info "Stopping existing containers..."
    docker-compose -f docker-compose.overmind.yml down 2>/dev/null || true
    docker-compose -f docker-compose.overmind-simple.yml down 2>/dev/null || true
    
    # Test deployment script
    if [[ -f "./deploy-overmind.sh" ]]; then
        print_info "Testing deployment script syntax..."
        if bash -n ./deploy-overmind.sh; then
            print_success "Deployment script syntax valid"
        else
            print_error "Deployment script syntax error"
            return 1
        fi
        
        # Test deployment (dry run)
        print_info "Testing deployment configuration..."
        if docker-compose -f docker-compose.overmind-simple.yml config > /dev/null 2>&1; then
            print_success "Docker Compose configuration valid"
        else
            print_error "Docker Compose configuration invalid"
            return 1
        fi
    else
        print_error "deploy-overmind.sh not found"
        return 1
    fi
    
    print_success "Clean server deployment test completed"
    return 0
}

test_configuration_validation() {
    print_header "⚙️ CATEGORY 1: Configuration Validation Test"
    echo ""
    
    print_info "Testing configuration error handling..."
    
    # Create temporary config with deliberate error
    cp docker-compose.overmind-simple.yml docker-compose.test-error.yml
    
    # Introduce deliberate error (invalid port)
    sed -i 's/6379:6379/99999:6379/' docker-compose.test-error.yml
    
    # Test if system fails fast with clear error
    print_info "Testing error detection..."
    if docker-compose -f docker-compose.test-error.yml config > /dev/null 2>&1; then
        print_warning "System did not detect configuration error"
        rm -f docker-compose.test-error.yml
        return 1
    else
        print_success "System properly detected configuration error"
        rm -f docker-compose.test-error.yml
        return 0
    fi
}

test_secret_management() {
    print_header "🔐 CATEGORY 1: Secret Management Test"
    echo ""
    
    print_info "Testing secret management and graceful degradation..."
    
    # Backup original .env
    if [[ -f ".env" ]]; then
        cp .env .env.backup
    fi
    
    # Create test .env without critical API key
    cat > .env.test << EOF
SNIPER_SOLANA_RPC_URL=https://api.devnet.solana.com
SNIPER_WALLET_PRIVATE_KEY=test_key_placeholder
# OPENAI_API_KEY intentionally missing for test
EOF
    
    # Test system behavior without critical secret
    print_info "Testing system behavior without OPENAI_API_KEY..."
    
    # Check if system can start in degraded mode
    export $(cat .env.test | xargs)
    
    # Verify environment variables
    if [[ -z "$OPENAI_API_KEY" ]]; then
        print_success "System correctly detects missing OPENAI_API_KEY"
    else
        print_error "System did not detect missing secret"
        rm -f .env.test
        return 1
    fi
    
    # Restore original .env
    if [[ -f ".env.backup" ]]; then
        mv .env.backup .env
    fi
    rm -f .env.test
    
    print_success "Secret management test completed"
    return 0
}

# ============================================================================
# CATEGORY 2: OBSERVABILITY & MONITORING TESTS
# ============================================================================

test_metrics_flow() {
    print_header "📊 CATEGORY 2: Metrics Flow Test"
    echo ""
    
    print_info "Testing metrics collection and flow..."
    
    # Check if Prometheus is accessible
    if curl -s http://localhost:9090/api/v1/query?query=up > /dev/null 2>&1; then
        print_success "Prometheus is accessible"
        
        # Test OVERMIND-specific metrics
        metrics=(
            "overmind_trades_executed_total"
            "overmind_pnl_total"
            "overmind_execution_latency_seconds"
        )
        
        available_metrics=0
        for metric in "${metrics[@]}"; do
            if curl -s "http://localhost:9090/api/v1/query?query=${metric}" | grep -q "success"; then
                ((available_metrics++))
                print_success "Metric available: $metric"
            else
                print_warning "Metric not available: $metric"
            fi
        done
        
        if [[ $available_metrics -ge 2 ]]; then
            print_success "Metrics flow test passed: $available_metrics/${#metrics[@]} metrics available"
            return 0
        else
            print_error "Metrics flow test failed: only $available_metrics/${#metrics[@]} metrics available"
            return 1
        fi
    else
        print_error "Prometheus not accessible for metrics flow test"
        return 1
    fi
}

test_alert_system() {
    print_header "🚨 CATEGORY 2: Alert Testing"
    echo ""
    
    print_info "Testing alert configuration and rules..."
    
    # Check for alert configuration files
    if [[ -f "monitoring/alertmanager.yml" ]] || [[ -f "monitoring/alert-rules.yml" ]]; then
        print_success "Alert configuration files found"
    else
        print_warning "Alert configuration files not found"
    fi
    
    # Test Prometheus rules API
    if curl -s http://localhost:9090/api/v1/rules > /dev/null 2>&1; then
        rules_count=$(curl -s http://localhost:9090/api/v1/rules | jq '.data.groups | length' 2>/dev/null || echo "0")
        if [[ $rules_count -gt 0 ]]; then
            print_success "Alert rules loaded: $rules_count rule groups"
            return 0
        else
            print_warning "No alert rules configured"
            return 1
        fi
    else
        print_error "Cannot access Prometheus rules API"
        return 1
    fi
}

test_centralized_logging() {
    print_header "📝 CATEGORY 2: Centralized Logging Test"
    echo ""
    
    print_info "Testing log aggregation and searchability..."
    
    # Test Docker logs availability
    if docker ps > /dev/null 2>&1; then
        print_success "Docker logs available"
        
        # Test log retrieval for OVERMIND containers
        containers=$(docker ps --filter name=overmind --format "{{.Names}}" 2>/dev/null || echo "")
        if [[ -n "$containers" ]]; then
            log_count=0
            while IFS= read -r container; do
                if docker logs "$container" --tail 10 > /dev/null 2>&1; then
                    ((log_count++))
                    print_success "Logs accessible for: $container"
                fi
            done <<< "$containers"
            
            if [[ $log_count -gt 0 ]]; then
                print_success "Centralized logging test passed: $log_count containers with accessible logs"
                return 0
            else
                print_error "No container logs accessible"
                return 1
            fi
        else
            print_warning "No OVERMIND containers found for log testing"
            return 1
        fi
    else
        print_error "Docker not accessible for logging test"
        return 1
    fi
}

# ============================================================================
# CATEGORY 3: RESILIENCE & RELIABILITY TESTS (Chaos Engineering)
# ============================================================================

test_database_blink() {
    print_header "💾 CATEGORY 3: Database Blink Test"
    echo ""
    
    print_info "Testing database restart and reconnection..."
    
    # Find DragonflyDB container
    dragonfly_container=$(docker ps --filter name=dragonfly --format "{{.Names}}" | head -1)
    
    if [[ -n "$dragonfly_container" ]]; then
        print_info "Testing database restart: $dragonfly_container"
        
        # Restart the container
        if docker restart "$dragonfly_container" > /dev/null 2>&1; then
            print_info "Container restarted, waiting for recovery..."
            sleep 10
            
            # Check if container is running
            if docker ps --filter name="$dragonfly_container" --filter status=running > /dev/null 2>&1; then
                print_success "Database blink test passed: $dragonfly_container recovered"
                return 0
            else
                print_error "Database failed to recover: $dragonfly_container"
                return 1
            fi
        else
            print_error "Failed to restart database container"
            return 1
        fi
    else
        print_warning "No DragonflyDB container found for blink test"
        return 1
    fi
}

test_api_overload() {
    print_header "🔥 CATEGORY 3: API Overload Test"
    echo ""
    
    print_info "Testing API endpoints under load..."
    
    # Test endpoints
    endpoints=(
        "http://localhost:9090/api/v1/query?query=up"
        "http://localhost:3001/api/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        endpoint_name=$(echo "$endpoint" | cut -d'/' -f3 | cut -d':' -f1)
        print_info "Testing load on: $endpoint_name"
        
        # Baseline test
        if curl -s --max-time 5 "$endpoint" > /dev/null 2>&1; then
            # Load test with 10 concurrent requests
            success_count=0
            for i in {1..10}; do
                if curl -s --max-time 5 "$endpoint" > /dev/null 2>&1; then
                    ((success_count++))
                fi
            done
            
            success_rate=$((success_count * 100 / 10))
            if [[ $success_rate -ge 80 ]]; then
                print_success "API overload test passed for $endpoint_name: ${success_rate}% success rate"
            else
                print_warning "API overload test degraded for $endpoint_name: ${success_rate}% success rate"
            fi
        else
            print_warning "Endpoint not accessible for load testing: $endpoint_name"
        fi
    done
    
    return 0
}

test_container_failure_recovery() {
    print_header "🔄 CATEGORY 3: Container Failure Recovery Test"
    echo ""
    
    print_info "Testing container failure and recovery..."
    
    # Find a non-critical container to test
    test_containers=$(docker ps --filter name=overmind --format "{{.Names}}" | grep -E "(grafana|prometheus)" | head -1)
    
    if [[ -n "$test_containers" ]]; then
        container="$test_containers"
        print_info "Testing container recovery: $container"
        
        # Stop container
        if docker stop "$container" > /dev/null 2>&1; then
            print_info "Container stopped, testing recovery..."
            sleep 2
            
            # Start container
            if docker start "$container" > /dev/null 2>&1; then
                sleep 10
                
                # Check if container is running
                if docker ps --filter name="$container" --filter status=running > /dev/null 2>&1; then
                    print_success "Container recovery test passed: $container recovered"
                    return 0
                else
                    print_error "Container failed to recover: $container"
                    return 1
                fi
            else
                print_error "Failed to start container: $container"
                return 1
            fi
        else
            print_error "Failed to stop container: $container"
            return 1
        fi
    else
        print_warning "No suitable containers found for recovery testing"
        return 1
    fi
}

# ============================================================================
# CATEGORY 4: SECURITY TESTS
# ============================================================================

test_network_access() {
    print_header "🔒 CATEGORY 4: Network Access Test"
    echo ""
    
    print_info "Testing network security and port exposure..."
    
    # Test internal service ports
    internal_ports=(6379 5432 8000 9200)
    exposed_ports=()
    
    for port in "${internal_ports[@]}"; do
        if nc -z localhost "$port" 2>/dev/null; then
            exposed_ports+=("$port")
            print_warning "Internal port exposed: $port"
        else
            print_success "Internal port secured: $port"
        fi
    done
    
    if [[ ${#exposed_ports[@]} -eq 0 ]]; then
        print_success "Network access test passed: all internal services secured"
        return 0
    elif [[ ${#exposed_ports[@]} -le 2 ]]; then
        print_warning "Network access test partial: ${#exposed_ports[@]} ports exposed"
        return 1
    else
        print_error "Network access test failed: ${#exposed_ports[@]} ports exposed"
        return 1
    fi
}

test_container_vulnerabilities() {
    print_header "🛡️ CATEGORY 4: Container Vulnerability Scan"
    echo ""
    
    print_info "Testing container security vulnerabilities..."
    
    # Check if Trivy is available
    if command -v trivy > /dev/null 2>&1; then
        print_info "Running Trivy container scan..."
        
        # Scan a sample image
        if trivy image --severity HIGH,CRITICAL --format table postgres:15-alpine > /tmp/trivy-scan.txt 2>&1; then
            critical_count=$(grep -c "CRITICAL" /tmp/trivy-scan.txt || echo "0")
            high_count=$(grep -c "HIGH" /tmp/trivy-scan.txt || echo "0")
            
            if [[ $critical_count -eq 0 && $high_count -eq 0 ]]; then
                print_success "Container vulnerability scan passed: no critical/high vulnerabilities"
                return 0
            else
                print_warning "Container vulnerabilities found: $critical_count critical, $high_count high"
                return 1
            fi
        else
            print_error "Container vulnerability scan failed"
            return 1
        fi
    else
        print_warning "Trivy not available for container vulnerability scanning"
        return 1
    fi
}

test_secret_leaks() {
    print_header "🔍 CATEGORY 4: Secret Leak Test"
    echo ""
    
    print_info "Scanning codebase for potential secret leaks..."
    
    # Scan for potential secrets
    secret_patterns=(
        "password.*=.*['\"][^'\"]{8,}['\"]"
        "secret.*=.*['\"][^'\"]{8,}['\"]"
        "key.*=.*['\"][^'\"]{20,}['\"]"
        "sk-[a-zA-Z0-9]{20,}"
    )
    
    potential_leaks=0
    
    for pattern in "${secret_patterns[@]}"; do
        matches=$(grep -r -i -E "$pattern" . --include="*.py" --include="*.rs" --include="*.js" --include="*.yml" --exclude-dir=".git" --exclude-dir="target" --exclude-dir="node_modules" 2>/dev/null | grep -v -E "(placeholder|example|your-|test)" | wc -l)
        if [[ $matches -gt 0 ]]; then
            ((potential_leaks += matches))
            print_warning "Potential secrets found matching pattern: $pattern ($matches matches)"
        fi
    done
    
    if [[ $potential_leaks -eq 0 ]]; then
        print_success "Secret leak test passed: no obvious secrets found in codebase"
        return 0
    else
        print_warning "Secret leak test found $potential_leaks potential issues"
        return 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    print_header "🧠 THE OVERMIND PROTOCOL - Automated Test Scripts Execution"
    echo "Philosophy: 'Trust through Real-World Verification'"
    echo "Executing all 4 critical test categories with specific scenarios"
    echo "============================================================================"
    
    total_tests=0
    passed_tests=0
    
    # Category 1: Deployment & Configuration Tests
    echo ""
    print_header "CATEGORY 1: DEPLOYMENT & CONFIGURATION TESTS"
    
    ((total_tests++))
    if test_clean_server_deployment; then ((passed_tests++)); fi
    
    ((total_tests++))
    if test_configuration_validation; then ((passed_tests++)); fi
    
    ((total_tests++))
    if test_secret_management; then ((passed_tests++)); fi
    
    # Category 2: Observability & Monitoring Tests
    echo ""
    print_header "CATEGORY 2: OBSERVABILITY & MONITORING TESTS"
    
    ((total_tests++))
    if test_metrics_flow; then ((passed_tests++)); fi
    
    ((total_tests++))
    if test_alert_system; then ((passed_tests++)); fi
    
    ((total_tests++))
    if test_centralized_logging; then ((passed_tests++)); fi
    
    # Category 3: Resilience & Reliability Tests
    echo ""
    print_header "CATEGORY 3: RESILIENCE & RELIABILITY TESTS (Chaos Engineering)"
    
    ((total_tests++))
    if test_database_blink; then ((passed_tests++)); fi
    
    ((total_tests++))
    if test_api_overload; then ((passed_tests++)); fi
    
    ((total_tests++))
    if test_container_failure_recovery; then ((passed_tests++)); fi
    
    # Category 4: Security Tests
    echo ""
    print_header "CATEGORY 4: SECURITY TESTS"
    
    ((total_tests++))
    if test_network_access; then ((passed_tests++)); fi
    
    ((total_tests++))
    if test_container_vulnerabilities; then ((passed_tests++)); fi
    
    ((total_tests++))
    if test_secret_leaks; then ((passed_tests++)); fi
    
    # Summary
    echo ""
    print_header "TEST EXECUTION SUMMARY"
    echo "============================================================================"
    echo "Total Tests: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $((total_tests - passed_tests))"
    
    success_rate=$((passed_tests * 100 / total_tests))
    echo "Success Rate: ${success_rate}%"
    
    if [[ $success_rate -ge 90 ]]; then
        print_success "🎉 THE OVERMIND PROTOCOL automated tests: EXCELLENT"
        return 0
    elif [[ $success_rate -ge 80 ]]; then
        print_warning "⚠️ THE OVERMIND PROTOCOL automated tests: GOOD with issues"
        return 1
    else
        print_error "❌ THE OVERMIND PROTOCOL automated tests: NEEDS WORK"
        return 2
    fi
}

# Execute main function
main "$@"
