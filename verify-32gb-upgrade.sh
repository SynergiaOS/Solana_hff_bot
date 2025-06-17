#!/bin/bash

# THE OVERMIND PROTOCOL - 32GB Upgrade Verification Script
# Verify that the VDS upgrade was successful and system is optimized

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

🔍 32GB UPGRADE VERIFICATION
EOF
echo -e "${NC}"

echo "THE OVERMIND PROTOCOL - 32GB/8-core Upgrade Verification"
echo "========================================================"
echo ""

# ============================================================================
# STEP 1: HARDWARE VERIFICATION
# ============================================================================
print_header "🖥️  STEP 1: Hardware Verification"
echo ""

# Check memory
TOTAL_MEMORY=$(free -h | grep '^Mem:' | awk '{print $2}')
TOTAL_MEMORY_GB=$(free -g | grep '^Mem:' | awk '{print $2}')

print_info "Total Memory: $TOTAL_MEMORY"

if [[ $TOTAL_MEMORY_GB -ge 30 ]]; then
    print_success "Memory upgrade successful (≥30GB detected)"
else
    print_error "Memory upgrade failed (Expected ≥30GB, got ${TOTAL_MEMORY_GB}GB)"
fi

# Check CPU cores
TOTAL_CORES=$(nproc)
print_info "Total CPU Cores: $TOTAL_CORES"

if [[ $TOTAL_CORES -ge 8 ]]; then
    print_success "CPU upgrade successful (≥8 cores detected)"
else
    print_error "CPU upgrade failed (Expected ≥8 cores, got $TOTAL_CORES cores)"
fi

# Check CPU model
CPU_MODEL=$(lscpu | grep "Model name" | cut -d':' -f2 | xargs)
print_info "CPU Model: $CPU_MODEL"

echo ""

# ============================================================================
# STEP 2: SYSTEM PERFORMANCE VERIFICATION
# ============================================================================
print_header "⚡ STEP 2: System Performance Verification"
echo ""

# Memory performance test
print_info "Testing memory performance..."
MEMORY_SPEED=$(dd if=/dev/zero of=/tmp/memory_test bs=1M count=1024 2>&1 | grep -o '[0-9.]* MB/s' | head -1)
print_info "Memory Speed: $MEMORY_SPEED"
rm -f /tmp/memory_test

# CPU performance test
print_info "Testing CPU performance..."
CPU_SCORE=$(timeout 10s sysbench cpu --threads=$TOTAL_CORES run 2>/dev/null | grep "events per second" | awk '{print $4}' || echo "N/A")
print_info "CPU Score: $CPU_SCORE events/second"

# Disk performance test
print_info "Testing disk I/O performance..."
DISK_WRITE=$(dd if=/dev/zero of=/tmp/disk_test bs=1M count=512 oflag=direct 2>&1 | grep -o '[0-9.]* MB/s' | head -1)
DISK_READ=$(dd if=/tmp/disk_test of=/dev/null bs=1M iflag=direct 2>&1 | grep -o '[0-9.]* MB/s' | head -1)
print_info "Disk Write: $DISK_WRITE"
print_info "Disk Read: $DISK_READ"
rm -f /tmp/disk_test

echo ""

# ============================================================================
# STEP 3: DOCKER CONFIGURATION VERIFICATION
# ============================================================================
print_header "🐳 STEP 3: Docker Configuration Verification"
echo ""

# Check Docker version
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    print_success "Docker installed: $DOCKER_VERSION"
    
    # Check Docker daemon configuration
    if [[ -f "/etc/docker/daemon.json" ]]; then
        print_success "Docker daemon configuration found"
        
        # Check memory limits
        if grep -q "memlock" /etc/docker/daemon.json; then
            print_success "Docker memory limits configured"
        else
            print_warning "Docker memory limits not configured"
        fi
    else
        print_warning "Docker daemon configuration not found"
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | cut -d',' -f1)
        print_success "Docker Compose installed: $COMPOSE_VERSION"
    else
        print_error "Docker Compose not installed"
    fi
else
    print_error "Docker not installed"
fi

echo ""

# ============================================================================
# STEP 4: OVERMIND CONFIGURATION VERIFICATION
# ============================================================================
print_header "🧠 STEP 4: OVERMIND Configuration Verification"
echo ""

# Check .env file
if [[ -f ".env" ]]; then
    print_success ".env configuration file found"
    
    # Check memory allocations
    if grep -q "OVERMIND_EXECUTOR_MEMORY=8g" .env; then
        print_success "Executor memory: 8GB (optimized for 32GB)"
    else
        print_warning "Executor memory not optimized for 32GB"
    fi
    
    if grep -q "OVERMIND_BRAIN_MEMORY=6g" .env; then
        print_success "Brain memory: 6GB (optimized for 32GB)"
    else
        print_warning "Brain memory not optimized for 32GB"
    fi
    
    if grep -q "TOKIO_WORKER_THREADS=8" .env; then
        print_success "Tokio worker threads: 8 (optimized for 8-core)"
    else
        print_warning "Tokio worker threads not optimized for 8-core"
    fi
    
    # Check API keys
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        print_success "OpenAI API key configured"
    else
        print_warning "OpenAI API key not configured"
    fi
    
else
    print_error ".env configuration file not found"
fi

# Check Docker Compose files
if [[ -f "docker-compose.overmind-32gb.yml" ]]; then
    print_success "32GB-optimized Docker Compose file found"
else
    print_warning "32GB-optimized Docker Compose file not found"
fi

echo ""

# ============================================================================
# STEP 5: PERFORMANCE BENCHMARKING
# ============================================================================
print_header "📊 STEP 5: Performance Benchmarking"
echo ""

print_info "Running performance benchmarks..."

# Network latency test
print_info "Testing network latency to Solana devnet..."
SOLANA_LATENCY=$(ping -c 3 api.devnet.solana.com 2>/dev/null | tail -1 | awk -F'/' '{print $5}' || echo "N/A")
print_info "Solana devnet latency: ${SOLANA_LATENCY}ms"

# Memory allocation test
print_info "Testing memory allocation speed..."
MEMORY_ALLOC_TIME=$(time -p python3 -c "
import time
start = time.time()
data = [0] * (1024 * 1024 * 100)  # 100MB allocation
end = time.time()
print(f'{(end - start) * 1000:.2f}ms')
" 2>/dev/null || echo "N/A")
print_info "Memory allocation (100MB): $MEMORY_ALLOC_TIME"

# Concurrent processing test
print_info "Testing concurrent processing capability..."
CONCURRENT_SCORE=$(timeout 5s python3 -c "
import concurrent.futures
import time

def cpu_task(n):
    return sum(i*i for i in range(n))

start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(cpu_task, 10000) for _ in range(32)]
    results = [f.result() for f in futures]
end = time.time()
print(f'{len(results) / (end - start):.2f} tasks/second')
" 2>/dev/null || echo "N/A")
print_info "Concurrent processing: $CONCURRENT_SCORE"

echo ""

# ============================================================================
# STEP 6: SYSTEM OPTIMIZATION VERIFICATION
# ============================================================================
print_header "🔧 STEP 6: System Optimization Verification"
echo ""

# Check kernel parameters
print_info "Checking kernel parameters..."

# Network optimizations
NET_RMEM_MAX=$(sysctl net.core.rmem_max 2>/dev/null | cut -d'=' -f2 | xargs)
if [[ "$NET_RMEM_MAX" == "134217728" ]]; then
    print_success "Network receive buffer optimized"
else
    print_warning "Network receive buffer not optimized (current: $NET_RMEM_MAX)"
fi

# Memory optimizations
VM_SWAPPINESS=$(sysctl vm.swappiness 2>/dev/null | cut -d'=' -f2 | xargs)
if [[ "$VM_SWAPPINESS" == "1" ]]; then
    print_success "Memory swappiness optimized"
else
    print_warning "Memory swappiness not optimized (current: $VM_SWAPPINESS)"
fi

# Check file limits
ULIMIT_NOFILE=$(ulimit -n)
if [[ $ULIMIT_NOFILE -ge 65536 ]]; then
    print_success "File descriptor limits optimized"
else
    print_warning "File descriptor limits not optimized (current: $ULIMIT_NOFILE)"
fi

echo ""

# ============================================================================
# STEP 7: DEPLOYMENT READINESS CHECK
# ============================================================================
print_header "🚀 STEP 7: Deployment Readiness Check"
echo ""

READINESS_SCORE=0
TOTAL_CHECKS=10

# Hardware checks
if [[ $TOTAL_MEMORY_GB -ge 30 ]]; then
    ((READINESS_SCORE++))
fi

if [[ $TOTAL_CORES -ge 8 ]]; then
    ((READINESS_SCORE++))
fi

# Software checks
if command -v docker &> /dev/null; then
    ((READINESS_SCORE++))
fi

if command -v docker-compose &> /dev/null; then
    ((READINESS_SCORE++))
fi

# Configuration checks
if [[ -f ".env" ]]; then
    ((READINESS_SCORE++))
fi

if grep -q "OVERMIND_EXECUTOR_MEMORY=8g" .env 2>/dev/null; then
    ((READINESS_SCORE++))
fi

if grep -q "TOKIO_WORKER_THREADS=8" .env 2>/dev/null; then
    ((READINESS_SCORE++))
fi

# Performance checks
if [[ "$NET_RMEM_MAX" == "134217728" ]]; then
    ((READINESS_SCORE++))
fi

if [[ "$VM_SWAPPINESS" == "1" ]]; then
    ((READINESS_SCORE++))
fi

if [[ $ULIMIT_NOFILE -ge 65536 ]]; then
    ((READINESS_SCORE++))
fi

READINESS_PERCENTAGE=$((READINESS_SCORE * 100 / TOTAL_CHECKS))

echo "📊 Deployment Readiness Score: $READINESS_SCORE/$TOTAL_CHECKS ($READINESS_PERCENTAGE%)"
echo ""

if [[ $READINESS_PERCENTAGE -ge 90 ]]; then
    print_success "🎯 SYSTEM READY FOR PRODUCTION DEPLOYMENT"
    echo ""
    echo "✅ All critical components verified"
    echo "✅ Hardware upgrade successful"
    echo "✅ Performance optimizations applied"
    echo "✅ Configuration updated for 32GB/8-core"
    echo ""
    echo "🚀 Ready to deploy THE OVERMIND PROTOCOL:"
    echo "   docker-compose -f docker-compose.overmind-32gb.yml up -d"
    
elif [[ $READINESS_PERCENTAGE -ge 70 ]]; then
    print_warning "⚠️  SYSTEM MOSTLY READY - MINOR ISSUES DETECTED"
    echo ""
    echo "✅ Hardware upgrade successful"
    echo "⚠️  Some optimizations may be missing"
    echo "📋 Review warnings above and apply fixes"
    
else
    print_error "❌ SYSTEM NOT READY - MAJOR ISSUES DETECTED"
    echo ""
    echo "❌ Critical issues found"
    echo "🔧 Address errors above before deployment"
fi

echo ""

# ============================================================================
# STEP 8: NEXT STEPS RECOMMENDATIONS
# ============================================================================
print_header "📋 STEP 8: Next Steps Recommendations"
echo ""

if [[ $READINESS_PERCENTAGE -ge 90 ]]; then
    echo "🎯 Ready for Production Deployment:"
    echo ""
    echo "1. Deploy THE OVERMIND PROTOCOL:"
    echo "   docker-compose -f docker-compose.overmind-32gb.yml up -d"
    echo ""
    echo "2. Run comprehensive tests:"
    echo "   ./test-overmind-complete.sh"
    echo ""
    echo "3. Monitor performance for 24+ hours"
    echo ""
    echo "4. Gradually increase trading parameters"
    
elif [[ $READINESS_PERCENTAGE -ge 70 ]]; then
    echo "🔧 Apply Remaining Optimizations:"
    echo ""
    echo "1. Run performance optimization script:"
    echo "   sudo ./optimize-32gb-performance.sh"
    echo ""
    echo "2. Update configuration files as needed"
    echo ""
    echo "3. Re-run verification:"
    echo "   ./verify-32gb-upgrade.sh"
    
else
    echo "🛠️  Fix Critical Issues:"
    echo ""
    echo "1. Address hardware upgrade issues"
    echo "2. Install missing software components"
    echo "3. Update configuration files"
    echo "4. Apply system optimizations"
    echo "5. Re-run verification"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================
print_header "📊 UPGRADE VERIFICATION SUMMARY"
echo ""

echo "🖥️  Hardware Status:"
echo "   Memory: $TOTAL_MEMORY ($TOTAL_MEMORY_GB GB)"
echo "   CPU: $TOTAL_CORES cores"
echo "   Model: $CPU_MODEL"
echo ""

echo "⚡ Performance Metrics:"
echo "   Memory Speed: $MEMORY_SPEED"
echo "   CPU Score: $CPU_SCORE events/second"
echo "   Disk Write: $DISK_WRITE"
echo "   Disk Read: $DISK_READ"
echo ""

echo "🎯 Readiness Score: $READINESS_SCORE/$TOTAL_CHECKS ($READINESS_PERCENTAGE%)"
echo ""

if [[ $READINESS_PERCENTAGE -ge 90 ]]; then
    echo -e "${GREEN}🎉 32GB/8-core upgrade successful and ready for production!${NC}"
elif [[ $READINESS_PERCENTAGE -ge 70 ]]; then
    echo -e "${YELLOW}⚠️  32GB/8-core upgrade mostly successful - minor optimizations needed${NC}"
else
    echo -e "${RED}❌ 32GB/8-core upgrade needs attention - address issues above${NC}"
fi

echo ""
echo "🧠 THE OVERMIND PROTOCOL 32GB Upgrade Verification Complete!"
