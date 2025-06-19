#!/bin/bash

# THE OVERMIND PROTOCOL - Critical DevOps Issues Fix Script
# Addresses immediate issues found in DevOps testing

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

🛠️ CRITICAL DEVOPS ISSUES FIX
EOF
echo -e "${NC}"

echo "THE OVERMIND PROTOCOL - Critical DevOps Issues Fix"
echo "=================================================="
echo ""

# ============================================================================
# STEP 1: SECURITY FIXES
# ============================================================================
print_header "🔒 STEP 1: Security Fixes"
echo ""

print_info "Fixing file permissions for sensitive files..."

# Fix .env file permissions
if [[ -f ".env" ]]; then
    chmod 600 .env
    print_success "Fixed .env file permissions (600)"
else
    print_warning ".env file not found"
fi

# Fix wallet directory permissions
if [[ -d "wallets" ]]; then
    chmod 700 wallets/
    find wallets/ -type f -name "*.json" -exec chmod 600 {} \; 2>/dev/null || true
    print_success "Fixed wallets directory permissions"
else
    print_info "Wallets directory not found (will be created when needed)"
fi

# Fix any private key files
find . -name "*.key" -exec chmod 600 {} \; 2>/dev/null || true
find . -name "*private*" -type f -exec chmod 600 {} \; 2>/dev/null || true

print_success "Security fixes completed"
echo ""

# ============================================================================
# STEP 2: INFRASTRUCTURE FIXES
# ============================================================================
print_header "🏗️ STEP 2: Infrastructure Fixes"
echo ""

print_info "Checking Docker and Docker Compose availability..."

# Check Docker
if command -v docker &> /dev/null; then
    print_success "Docker is available: $(docker --version)"
else
    print_error "Docker is not available - please install Docker first"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    print_success "Docker Compose is available: $(docker-compose --version)"
else
    print_error "Docker Compose is not available - please install Docker Compose first"
    exit 1
fi

print_info "Stopping any existing containers..."
docker-compose -f docker-compose.overmind.yml down 2>/dev/null || true

print_info "Starting THE OVERMIND PROTOCOL services..."

# Start services with proper error handling
if docker-compose -f docker-compose.overmind.yml up -d; then
    print_success "Services started successfully"
else
    print_error "Failed to start services - checking for issues..."
    
    # Try to diagnose the issue
    print_info "Checking Docker Compose file..."
    if [[ ! -f "docker-compose.overmind.yml" ]]; then
        print_error "docker-compose.overmind.yml not found"
        
        # Check for alternative compose files
        if [[ -f "docker-compose.yml" ]]; then
            print_info "Found docker-compose.yml - trying with that..."
            docker-compose up -d
        else
            print_error "No Docker Compose file found"
            exit 1
        fi
    fi
fi

print_info "Waiting for services to initialize..."
sleep 30

print_info "Checking service status..."
docker-compose ps

echo ""

# ============================================================================
# STEP 3: MONITORING SETUP
# ============================================================================
print_header "📊 STEP 3: Monitoring Setup"
echo ""

print_info "Setting up basic monitoring..."

# Create monitoring directory if it doesn't exist
mkdir -p monitoring

# Create basic Prometheus configuration if it doesn't exist
if [[ ! -f "monitoring/prometheus.yml" ]]; then
    print_info "Creating basic Prometheus configuration..."
    
    cat > monitoring/prometheus.yml << 'EOL'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'overmind-executor'
    static_configs:
      - targets: ['overmind-executor:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'overmind-brain'
    static_configs:
      - targets: ['overmind-brain:8001']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOL
    
    print_success "Created basic Prometheus configuration"
fi

# Try to start monitoring if compose file exists
if [[ -f "docker-compose.monitoring.yml" ]]; then
    print_info "Starting monitoring stack..."
    docker-compose -f docker-compose.monitoring.yml up -d || print_warning "Monitoring stack failed to start"
else
    print_warning "Monitoring compose file not found - monitoring setup incomplete"
fi

echo ""

# ============================================================================
# STEP 4: HEALTH CHECK CREATION
# ============================================================================
print_header "🏥 STEP 4: Health Check Automation"
echo ""

print_info "Creating automated health check script..."

cat > health-check-all.sh << 'EOL'
#!/bin/bash

# THE OVERMIND PROTOCOL - Comprehensive Health Check

echo "🧠 THE OVERMIND PROTOCOL - Health Check"
echo "======================================="
echo "$(date)"
echo ""

# Define services to check
declare -A services=(
    ["Executor"]="http://localhost:8080/health"
    ["Brain"]="http://localhost:8001/health"
    ["Chroma"]="http://localhost:8000/api/v1/heartbeat"
    ["TensorZero"]="http://localhost:3000/health"
    ["Prometheus"]="http://localhost:9090/-/healthy"
    ["Grafana"]="http://localhost:3001/api/health"
)

healthy_count=0
total_count=${#services[@]}

echo "🔍 Checking service health..."
echo ""

for service_name in "${!services[@]}"; do
    url="${services[$service_name]}"
    
    if curl -s --max-time 10 "$url" > /dev/null 2>&1; then
        echo "✅ $service_name: Healthy"
        ((healthy_count++))
    else
        echo "❌ $service_name: Unhealthy ($url)"
    fi
done

echo ""
echo "📊 Health Summary:"
echo "  Healthy Services: $healthy_count/$total_count"
echo "  Health Rate: $(( healthy_count * 100 / total_count ))%"

if [[ $healthy_count -eq $total_count ]]; then
    echo "🎉 All services are healthy!"
    exit 0
elif [[ $healthy_count -ge $(( total_count * 80 / 100 )) ]]; then
    echo "⚠️  Most services are healthy"
    exit 1
else
    echo "❌ Critical health issues detected"
    exit 2
fi
EOL

chmod +x health-check-all.sh
print_success "Created health check script: health-check-all.sh"

echo ""

# ============================================================================
# STEP 5: VALIDATION
# ============================================================================
print_header "✅ STEP 5: Validation"
echo ""

print_info "Running health checks..."
./health-check-all.sh

echo ""
print_info "Re-running DevOps tests to validate improvements..."

if python3 devops-testing-basic.py; then
    print_success "DevOps tests completed successfully"
else
    print_warning "DevOps tests completed with issues - check output above"
fi

echo ""

# ============================================================================
# STEP 6: SUMMARY AND NEXT STEPS
# ============================================================================
print_header "📋 STEP 6: Summary and Next Steps"
echo ""

echo "🎯 Critical Issues Fix Summary:"
echo "==============================="
echo ""
echo "✅ Security: Fixed file permissions for sensitive files"
echo "✅ Infrastructure: Started OVERMIND services"
echo "✅ Monitoring: Basic monitoring configuration created"
echo "✅ Health Checks: Automated health check script created"
echo "✅ Validation: DevOps tests re-run"
echo ""

echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. 🔍 Review DevOps test results above"
echo "2. 📊 Check service health: ./health-check-all.sh"
echo "3. 🐳 Monitor containers: docker-compose ps"
echo "4. 📈 Access monitoring (if available):"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana: http://localhost:3001"
echo ""

echo "🚀 For complete DevOps improvement:"
echo "   • Review: devops-improvement-plan.md"
echo "   • Continue with Phase 2 improvements"
echo "   • Deploy full monitoring stack"
echo "   • Implement backup procedures"
echo ""

print_success "Critical DevOps issues fix completed!"
echo ""

# Final health check
print_info "Final system status:"
docker-compose ps 2>/dev/null || echo "No containers running"

echo ""
print_info "🎯 THE OVERMIND PROTOCOL DevOps improvements applied successfully!"
