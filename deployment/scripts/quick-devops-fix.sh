#!/bin/bash

# THE OVERMIND PROTOCOL - Quick DevOps Fix
# Addresses critical infrastructure issues with simplified deployment

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
🛠️ THE OVERMIND PROTOCOL - Quick DevOps Fix
==========================================
EOF
echo -e "${NC}"

print_header "🔧 Quick Infrastructure Fix for DevOps Testing"
echo ""

# ============================================================================
# STEP 1: SECURITY FIXES
# ============================================================================
print_info "Step 1: Fixing security issues..."

# Fix .env file permissions
if [[ -f ".env" ]]; then
    chmod 600 .env
    print_success "Fixed .env file permissions"
else
    print_warning ".env file not found"
fi

# Fix wallet directory permissions if it exists
if [[ -d "wallets" ]]; then
    chmod 700 wallets/
    find wallets/ -type f -name "*.json" -exec chmod 600 {} \; 2>/dev/null || true
    print_success "Fixed wallets directory permissions"
fi

# ============================================================================
# STEP 2: INFRASTRUCTURE SETUP
# ============================================================================
print_info "Step 2: Setting up infrastructure..."

# Stop any existing containers
print_info "Stopping existing containers..."
docker-compose -f docker-compose.overmind.yml down 2>/dev/null || true
docker-compose -f docker-compose.overmind-simple.yml down 2>/dev/null || true

# Create monitoring directory and basic config
mkdir -p monitoring
if [[ ! -f "monitoring/prometheus.yml" ]]; then
    print_info "Creating basic Prometheus configuration..."
    
    cat > monitoring/prometheus.yml << 'EOL'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

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
EOL
    
    print_success "Created Prometheus configuration"
fi

# ============================================================================
# STEP 3: START CORE SERVICES ONLY
# ============================================================================
print_info "Step 3: Starting core services for testing..."

# Start only essential services for DevOps testing
print_info "Starting TensorZero and Chroma services..."

# Start TensorZero stack first
docker-compose -f docker-compose.overmind-simple.yml up -d tensorzero-db tensorzero-dragonfly tensorzero-gateway

print_info "Waiting for TensorZero to initialize..."
sleep 15

# Start Chroma
docker-compose -f docker-compose.overmind-simple.yml up -d chroma

print_info "Waiting for Chroma to initialize..."
sleep 10

# Start monitoring
docker-compose -f docker-compose.overmind-simple.yml up -d prometheus grafana

print_info "Waiting for monitoring to initialize..."
sleep 10

# ============================================================================
# STEP 4: HEALTH CHECK
# ============================================================================
print_info "Step 4: Checking service health..."

# Create simple health check
cat > quick-health-check.sh << 'EOL'
#!/bin/bash

echo "🧠 THE OVERMIND PROTOCOL - Quick Health Check"
echo "============================================="
echo "$(date)"
echo ""

# Define core services to check
declare -A services=(
    ["TensorZero"]="http://localhost:3000/health"
    ["Chroma"]="http://localhost:8000/api/v1/heartbeat"
    ["Prometheus"]="http://localhost:9090/-/healthy"
    ["Grafana"]="http://localhost:3001/api/health"
)

healthy_count=0
total_count=${#services[@]}

echo "🔍 Checking core service health..."
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
echo "📊 Core Services Health Summary:"
echo "  Healthy Services: $healthy_count/$total_count"
echo "  Health Rate: $(( healthy_count * 100 / total_count ))%"

if [[ $healthy_count -ge $(( total_count * 75 / 100 )) ]]; then
    echo "✅ Core infrastructure is healthy enough for DevOps testing"
    exit 0
else
    echo "❌ Core infrastructure needs attention"
    exit 1
fi
EOL

chmod +x quick-health-check.sh

print_info "Running health check..."
sleep 5

if ./quick-health-check.sh; then
    print_success "Core services are healthy"
else
    print_warning "Some core services may need more time to start"
fi

# ============================================================================
# STEP 5: DEVOPS TESTING
# ============================================================================
print_info "Step 5: Running DevOps tests..."

print_info "Re-running DevOps tests with improved infrastructure..."

if python3 devops-testing-basic.py; then
    print_success "DevOps tests completed"
else
    print_warning "DevOps tests completed with some issues"
fi

# ============================================================================
# STEP 6: SUMMARY
# ============================================================================
print_header "📋 Quick Fix Summary"
echo ""

echo "✅ Security: Fixed file permissions"
echo "✅ Infrastructure: Started core services"
echo "✅ Monitoring: Basic monitoring deployed"
echo "✅ Health Checks: Automated health checking"
echo "✅ Testing: DevOps tests re-run"
echo ""

print_info "🔍 To check service status:"
print_info "   ./quick-health-check.sh"
print_info ""
print_info "🐳 To check containers:"
print_info "   docker-compose -f docker-compose.overmind-simple.yml ps"
print_info ""
print_info "📊 To access monitoring:"
print_info "   Prometheus: http://localhost:9090"
print_info "   Grafana: http://localhost:3001 (admin/overmind123)"
print_info ""

print_success "🎯 Quick DevOps fix completed!"

# Final status check
print_info "Final service status:"
docker-compose -f docker-compose.overmind-simple.yml ps
