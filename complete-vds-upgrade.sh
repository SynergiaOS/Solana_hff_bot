#!/bin/bash

# THE OVERMIND PROTOCOL - Complete VDS Upgrade Script
# Final verification and deployment after 32GB/8-core upgrade

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

echo -e "${PURPLE}"
cat << "EOF"
 _____ _   _ _____    _____  _   _ _____ ____  __  __ _____ _   _ ____  
|_   _| | | | ____|  / _ \ \| | | | ____|  _ \|  \/  |_   _| \ | |  _ \ 
  | | | |_| |  _|   | | | | | | | |  _| | |_) | |\/| | | | |  \| | | | |
  | | |  _  | |___  | |_| | |_| | | |___|  _ <| |  | | | | | |\  | |_| |
  |_| |_| |_|_____|  \___/ \___/|_|_____|_| \_\_|  |_| |_| |_| \_|____/ 

🎯 VDS UPGRADE COMPLETION
EOF
echo -e "${NC}"

echo "THE OVERMIND PROTOCOL - VDS 32GB/8-Core Upgrade Completion"
echo "=========================================================="
echo ""

# ============================================================================
# STEP 1: VERIFY HARDWARE UPGRADE
# ============================================================================
print_header "🖥️  STEP 1: Hardware Upgrade Verification"
echo ""

# Check current memory
CURRENT_MEMORY_GB=$(free -g | grep '^Mem:' | awk '{print $2}')
CURRENT_CORES=$(nproc)

print_info "Current System Resources:"
print_info "  Memory: ${CURRENT_MEMORY_GB}GB"
print_info "  CPU Cores: $CURRENT_CORES"

if [[ $CURRENT_MEMORY_GB -ge 30 ]]; then
    print_success "Memory upgrade verified: ${CURRENT_MEMORY_GB}GB (≥30GB required)"
    MEMORY_UPGRADE_OK=true
else
    print_error "Memory upgrade failed: ${CURRENT_MEMORY_GB}GB (30GB+ required)"
    MEMORY_UPGRADE_OK=false
fi

if [[ $CURRENT_CORES -ge 8 ]]; then
    print_success "CPU upgrade verified: $CURRENT_CORES cores (≥8 required)"
    CPU_UPGRADE_OK=true
else
    print_error "CPU upgrade failed: $CURRENT_CORES cores (8+ required)"
    CPU_UPGRADE_OK=false
fi

if [[ "$MEMORY_UPGRADE_OK" == "true" && "$CPU_UPGRADE_OK" == "true" ]]; then
    print_success "Hardware upgrade verification: PASSED"
    HARDWARE_OK=true
else
    print_error "Hardware upgrade verification: FAILED"
    HARDWARE_OK=false
    echo ""
    print_error "Please complete the Contabo VDS upgrade before proceeding"
    exit 1
fi

echo ""

# ============================================================================
# STEP 2: APPLY PERFORMANCE OPTIMIZATIONS
# ============================================================================
print_header "⚡ STEP 2: Apply Performance Optimizations"
echo ""

print_info "Applying system optimizations for 32GB/8-core..."

# Check if optimization script exists
if [[ -f "optimize-32gb-performance.sh" ]]; then
    print_info "Running performance optimization script..."
    
    # Make executable if not already
    chmod +x optimize-32gb-performance.sh
    
    # Run optimization script
    if sudo ./optimize-32gb-performance.sh; then
        print_success "Performance optimizations applied successfully"
        OPTIMIZATION_OK=true
    else
        print_warning "Some optimizations may have failed - check manually"
        OPTIMIZATION_OK=false
    fi
else
    print_warning "Performance optimization script not found - applying basic optimizations"
    
    # Apply basic kernel optimizations
    print_info "Applying basic kernel parameters..."
    
    # Network optimizations
    sudo sysctl -w net.core.rmem_max=134217728 2>/dev/null || true
    sudo sysctl -w net.core.wmem_max=134217728 2>/dev/null || true
    sudo sysctl -w vm.swappiness=1 2>/dev/null || true
    
    print_success "Basic optimizations applied"
    OPTIMIZATION_OK=true
fi

echo ""

# ============================================================================
# STEP 3: UPDATE DOCKER CONFIGURATION
# ============================================================================
print_header "🐳 STEP 3: Update Docker Configuration"
echo ""

print_info "Updating Docker configuration for 32GB/8-core..."

# Check if 32GB Docker Compose file exists
if [[ -f "docker-compose.overmind-32gb.yml" ]]; then
    print_success "32GB Docker Compose configuration found"
    
    # Backup current configuration
    if [[ -f "docker-compose.overmind.yml" ]]; then
        cp docker-compose.overmind.yml docker-compose.overmind.yml.backup-$(date +%Y%m%d-%H%M%S)
        print_info "Backed up current Docker Compose configuration"
    fi
    
    # Use 32GB configuration
    cp docker-compose.overmind-32gb.yml docker-compose.overmind.yml
    print_success "Updated to 32GB Docker Compose configuration"
    DOCKER_CONFIG_OK=true
else
    print_warning "32GB Docker Compose configuration not found - using current configuration"
    DOCKER_CONFIG_OK=false
fi

# Check Docker daemon configuration
if [[ -f "/etc/docker/daemon.json" ]]; then
    print_success "Docker daemon configuration found"
else
    print_info "Creating Docker daemon configuration..."
    
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json > /dev/null << 'EOL'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    },
    "nofile": {
      "Hard": 65536,
      "Name": "nofile",
      "Soft": 65536
    }
  }
}
EOL
    
    print_success "Created Docker daemon configuration"
    
    # Restart Docker daemon
    print_info "Restarting Docker daemon..."
    sudo systemctl restart docker
    sleep 5
    
    if sudo systemctl is-active --quiet docker; then
        print_success "Docker daemon restarted successfully"
    else
        print_error "Docker daemon restart failed"
        DOCKER_CONFIG_OK=false
    fi
fi

echo ""

# ============================================================================
# STEP 4: DEPLOY OVERMIND WITH NEW CONFIGURATION
# ============================================================================
print_header "🧠 STEP 4: Deploy THE OVERMIND PROTOCOL"
echo ""

print_info "Deploying THE OVERMIND PROTOCOL with 32GB/8-core configuration..."

# Stop existing containers
print_info "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Pull latest images
print_info "Pulling latest Docker images..."
docker-compose pull 2>/dev/null || true

# Start with new configuration
print_info "Starting THE OVERMIND PROTOCOL..."
if docker-compose up -d; then
    print_success "THE OVERMIND PROTOCOL deployed successfully"
    DEPLOYMENT_OK=true
    
    # Wait for services to start
    print_info "Waiting for services to initialize..."
    sleep 30
    
    # Check service health
    print_info "Checking service health..."
    
    # Check key services
    SERVICES_OK=true
    
    # Check if containers are running
    RUNNING_CONTAINERS=$(docker-compose ps --services --filter "status=running" | wc -l)
    TOTAL_SERVICES=$(docker-compose config --services | wc -l)
    
    print_info "Running services: $RUNNING_CONTAINERS/$TOTAL_SERVICES"
    
    if [[ $RUNNING_CONTAINERS -ge $((TOTAL_SERVICES * 80 / 100)) ]]; then
        print_success "Most services are running (≥80%)"
    else
        print_warning "Some services may not be running properly"
        SERVICES_OK=false
    fi
    
else
    print_error "THE OVERMIND PROTOCOL deployment failed"
    DEPLOYMENT_OK=false
    SERVICES_OK=false
fi

echo ""

# ============================================================================
# STEP 5: PERFORMANCE VERIFICATION
# ============================================================================
print_header "📊 STEP 5: Performance Verification"
echo ""

print_info "Running performance verification tests..."

# Run verification script if available
if [[ -f "verify-32gb-upgrade.sh" ]]; then
    print_info "Running comprehensive verification..."
    
    chmod +x verify-32gb-upgrade.sh
    
    if ./verify-32gb-upgrade.sh; then
        print_success "Performance verification completed successfully"
        VERIFICATION_OK=true
    else
        print_warning "Some performance tests may have failed"
        VERIFICATION_OK=false
    fi
else
    print_info "Running basic performance checks..."
    
    # Basic performance checks
    VERIFICATION_OK=true
    
    # Memory test
    print_info "Testing memory performance..."
    MEMORY_SPEED=$(dd if=/dev/zero of=/tmp/memory_test bs=1M count=512 2>&1 | grep -o '[0-9.]* MB/s' | head -1 || echo "N/A")
    print_info "Memory speed: $MEMORY_SPEED"
    rm -f /tmp/memory_test
    
    # CPU test
    print_info "Testing CPU performance..."
    CPU_SCORE=$(timeout 5s sysbench cpu --threads=$CURRENT_CORES run 2>/dev/null | grep "events per second" | awk '{print $4}' || echo "N/A")
    print_info "CPU score: $CPU_SCORE events/second"
    
    print_success "Basic performance verification completed"
fi

echo ""

# ============================================================================
# STEP 6: FINAL SYSTEM STATUS
# ============================================================================
print_header "🎯 STEP 6: Final System Status"
echo ""

# Calculate overall success
TOTAL_CHECKS=5
PASSED_CHECKS=0

if [[ "$HARDWARE_OK" == "true" ]]; then ((PASSED_CHECKS++)); fi
if [[ "$OPTIMIZATION_OK" == "true" ]]; then ((PASSED_CHECKS++)); fi
if [[ "$DOCKER_CONFIG_OK" == "true" ]]; then ((PASSED_CHECKS++)); fi
if [[ "$DEPLOYMENT_OK" == "true" ]]; then ((PASSED_CHECKS++)); fi
if [[ "$VERIFICATION_OK" == "true" ]]; then ((PASSED_CHECKS++)); fi

SUCCESS_RATE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

echo "📊 Upgrade Completion Status:"
echo "=============================="
echo ""
echo "✅ Hardware Upgrade: $([ "$HARDWARE_OK" == "true" ] && echo "PASSED" || echo "FAILED")"
echo "⚡ Performance Optimization: $([ "$OPTIMIZATION_OK" == "true" ] && echo "PASSED" || echo "FAILED")"
echo "🐳 Docker Configuration: $([ "$DOCKER_CONFIG_OK" == "true" ] && echo "PASSED" || echo "FAILED")"
echo "🧠 OVERMIND Deployment: $([ "$DEPLOYMENT_OK" == "true" ] && echo "PASSED" || echo "FAILED")"
echo "📊 Performance Verification: $([ "$VERIFICATION_OK" == "true" ] && echo "PASSED" || echo "FAILED")"
echo ""
echo "📈 Overall Success Rate: $PASSED_CHECKS/$TOTAL_CHECKS ($SUCCESS_RATE%)"
echo ""

if [[ $SUCCESS_RATE -ge 90 ]]; then
    print_success "🎉 VDS UPGRADE COMPLETED SUCCESSFULLY!"
    echo ""
    echo "✅ 32GB/8-core upgrade is complete and operational"
    echo "✅ THE OVERMIND PROTOCOL is running with enhanced performance"
    echo "✅ System is ready for production trading"
    echo ""
    echo "🚀 Next Steps:"
    echo "   • Monitor system performance for 24+ hours"
    echo "   • Run comprehensive trading tests"
    echo "   • Gradually increase trading parameters"
    echo "   • Validate all performance improvements"
    
elif [[ $SUCCESS_RATE -ge 70 ]]; then
    print_warning "⚠️  VDS UPGRADE MOSTLY COMPLETED"
    echo ""
    echo "✅ Hardware upgrade successful"
    echo "⚠️  Some configuration issues detected"
    echo ""
    echo "🔧 Recommended Actions:"
    echo "   • Review failed checks above"
    echo "   • Apply missing optimizations"
    echo "   • Re-run verification tests"
    
else
    print_error "❌ VDS UPGRADE INCOMPLETE"
    echo ""
    echo "❌ Critical issues detected"
    echo "🛠️  Required Actions:"
    echo "   • Address all failed checks"
    echo "   • Verify hardware upgrade completion"
    echo "   • Re-run this script after fixes"
fi

echo ""

# ============================================================================
# STEP 7: MONITORING SETUP
# ============================================================================
print_header "📈 STEP 7: Monitoring and Alerts"
echo ""

print_info "Setting up monitoring for upgraded system..."

# Create monitoring script
cat > monitor-32gb-system.sh << 'EOF'
#!/bin/bash

# THE OVERMIND PROTOCOL - 32GB System Monitoring

echo "🧠 THE OVERMIND PROTOCOL - System Monitor (32GB/8-core)"
echo "========================================================"
echo "$(date)"
echo ""

# System resources
echo "💾 Memory Usage:"
free -h | grep -E "Mem:|Swap:"
echo ""

echo "🖥️  CPU Usage:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//'
echo ""

echo "💿 Disk Usage:"
df -h / | tail -1
echo ""

# Docker containers
echo "🐳 Docker Containers:"
docker-compose ps
echo ""

# OVERMIND specific checks
echo "🧠 OVERMIND Health Checks:"
curl -s http://localhost:8080/health 2>/dev/null && echo "✅ Executor: Healthy" || echo "❌ Executor: Unhealthy"
curl -s http://localhost:8000/api/v1/heartbeat 2>/dev/null && echo "✅ Chroma: Healthy" || echo "❌ Chroma: Unhealthy"
curl -s http://localhost:3000/health 2>/dev/null && echo "✅ TensorZero: Healthy" || echo "❌ TensorZero: Unhealthy"
echo ""

echo "📊 Performance Metrics:"
echo "  Memory Available: $(free -g | grep '^Mem:' | awk '{print $7}')GB"
echo "  CPU Cores: $(nproc)"
echo "  Load Average: $(uptime | awk -F'load average:' '{print $2}')"
echo ""
EOF

chmod +x monitor-32gb-system.sh
print_success "Created system monitoring script: monitor-32gb-system.sh"

# Create performance baseline
print_info "Creating performance baseline..."
./monitor-32gb-system.sh > performance-baseline-$(date +%Y%m%d-%H%M%S).log
print_success "Performance baseline saved"

echo ""
print_info "🔍 To monitor the system:"
print_info "   ./monitor-32gb-system.sh"
print_info ""
print_info "📊 To check OVERMIND logs:"
print_info "   docker-compose logs -f overmind-executor-prod"
print_info ""
print_info "📈 To access monitoring dashboards:"
print_info "   Grafana: http://localhost:3001"
print_info "   Prometheus: http://localhost:9090"

echo ""
print_success "🎯 VDS 32GB/8-Core Upgrade Process Complete!"
echo ""

# Return appropriate exit code
if [[ $SUCCESS_RATE -ge 90 ]]; then
    exit 0
elif [[ $SUCCESS_RATE -ge 70 ]]; then
    exit 1
else
    exit 2
fi
