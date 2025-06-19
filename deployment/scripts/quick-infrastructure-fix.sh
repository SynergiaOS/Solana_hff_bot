#!/bin/bash

# THE OVERMIND PROTOCOL - Quick Infrastructure Fix
# Rapid resolution of critical DevOps issues

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
🛡️ THE OVERMIND PROTOCOL - Quick Infrastructure Fix
==================================================
Mission: Rapid infrastructure hardening
EOF
echo -e "${NC}"

print_header "🎯 Quick Infrastructure Fixes"
echo ""

# ============================================================================
# STEP 1: Stop existing containers and clean up
# ============================================================================
print_info "Step 1: Cleaning up existing containers..."

docker-compose -f docker-compose.overmind.yml down 2>/dev/null || true
docker-compose -f docker-compose.overmind-simple.yml down 2>/dev/null || true
docker-compose -f docker-compose.overmind-hardened.yml down 2>/dev/null || true

print_success "Cleaned up existing containers"

# ============================================================================
# STEP 2: Fix file permissions and security
# ============================================================================
print_info "Step 2: Fixing file permissions and security..."

# Fix .env file permissions
if [[ -f ".env" ]]; then
    chmod 600 .env
    print_success "Fixed .env file permissions"
fi

# Fix wallet directory permissions if it exists
if [[ -d "wallets" ]]; then
    chmod 700 wallets/
    find wallets/ -type f -name "*.json" -exec chmod 600 {} \; 2>/dev/null || true
    print_success "Fixed wallets directory permissions"
fi

# ============================================================================
# STEP 3: Create monitoring directory structure
# ============================================================================
print_info "Step 3: Creating monitoring directory structure..."

mkdir -p monitoring/grafana/{dashboards,datasources}
mkdir -p monitoring/alertmanager

# Create basic alertmanager config
cat > monitoring/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'overmind@localhost'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://127.0.0.1:5001/'
EOF

print_success "Created monitoring directory structure"

# ============================================================================
# STEP 4: Start core services with hardened configuration
# ============================================================================
print_info "Step 4: Starting core services..."

# Start monitoring first
print_info "Starting Prometheus..."
docker-compose -f docker-compose.overmind-hardened.yml up -d prometheus

sleep 10

# Check if Prometheus started
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    print_success "Prometheus started successfully"
else
    print_warning "Prometheus may need more time to start"
fi

# Start Grafana
print_info "Starting Grafana..."
docker-compose -f docker-compose.overmind-hardened.yml up -d grafana

sleep 10

# Check if Grafana started
if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
    print_success "Grafana started successfully"
else
    print_warning "Grafana may need more time to start"
fi

# Start databases
print_info "Starting databases..."
docker-compose -f docker-compose.overmind-hardened.yml up -d overmind-db overmind-dragonfly

sleep 15

# Check database health
db_healthy=0
if docker exec overmind-database pg_isready -U sniper > /dev/null 2>&1; then
    print_success "PostgreSQL is healthy"
    ((db_healthy++))
else
    print_warning "PostgreSQL is not ready yet"
fi

if docker exec overmind-dragonfly redis-cli ping > /dev/null 2>&1; then
    print_success "DragonflyDB is healthy"
    ((db_healthy++))
else
    print_warning "DragonflyDB is not ready yet"
fi

# Start AI services
print_info "Starting AI services..."
docker-compose -f docker-compose.overmind-hardened.yml up -d chroma

sleep 10

# Check AI services
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
    print_success "Chroma Vector DB is healthy"
else
    print_warning "Chroma Vector DB is not ready yet"
fi

# ============================================================================
# STEP 5: Test network security
# ============================================================================
print_info "Step 5: Testing network security..."

network_secure=true

# Test that internal ports are bound to localhost only
internal_ports=(5432 6379 8000 9090 3001)
for port in "${internal_ports[@]}"; do
    if netstat -tlnp 2>/dev/null | grep ":$port " | grep "0.0.0.0" > /dev/null; then
        print_warning "Port $port is exposed to all interfaces"
        network_secure=false
    else
        print_success "Port $port is properly secured"
    fi
done

# ============================================================================
# STEP 6: Generate quick assessment
# ============================================================================
print_header "📊 Quick Infrastructure Assessment"
echo ""

# Count running containers
running_containers=$(docker ps --filter name=overmind --format "{{.Names}}" | wc -l)
print_info "Running OVERMIND containers: $running_containers"

# Test key endpoints
endpoints_healthy=0
total_endpoints=0

# Test Prometheus
((total_endpoints++))
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    print_success "Prometheus: Healthy"
    ((endpoints_healthy++))
else
    print_warning "Prometheus: Not responding"
fi

# Test Grafana
((total_endpoints++))
if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
    print_success "Grafana: Healthy"
    ((endpoints_healthy++))
else
    print_warning "Grafana: Not responding"
fi

# Test Chroma
((total_endpoints++))
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
    print_success "Chroma: Healthy"
    ((endpoints_healthy++))
else
    print_warning "Chroma: Not responding"
fi

# Calculate health rate
health_rate=$((endpoints_healthy * 100 / total_endpoints))

echo ""
echo "Infrastructure Health Summary:"
echo "  Healthy Endpoints: $endpoints_healthy/$total_endpoints"
echo "  Health Rate: ${health_rate}%"
echo "  Network Security: $(if $network_secure; then echo "Secured"; else echo "Needs work"; fi)"
echo "  Running Containers: $running_containers"

# ============================================================================
# STEP 7: Run quick DevOps validation
# ============================================================================
print_info "Step 7: Running quick DevOps validation..."

if python3 devops-testing-basic.py; then
    print_success "Basic DevOps testing completed successfully"
    validation_success=true
else
    print_warning "Basic DevOps testing completed with issues"
    validation_success=false
fi

# ============================================================================
# FINAL ASSESSMENT
# ============================================================================
print_header "🎯 Infrastructure Hardening Results"
echo ""

if [[ $health_rate -ge 66 && $network_secure == true && $validation_success == true ]]; then
    print_success "🎉 Infrastructure hardening SUCCESSFUL!"
    print_success "Significant improvement achieved - ready for comprehensive testing"
    
    echo ""
    print_info "Next steps:"
    print_info "1. Run comprehensive DevOps testing: python3 comprehensive-devops-testing.py"
    print_info "2. Start remaining services: docker-compose -f docker-compose.overmind-hardened.yml up -d"
    print_info "3. Monitor system health: docker-compose ps"
    
    exit 0
elif [[ $health_rate -ge 33 ]]; then
    print_warning "⚠️ Infrastructure hardening PARTIAL success"
    print_warning "Some services started but issues remain"
    
    echo ""
    print_info "Issues to address:"
    if [[ $health_rate -lt 66 ]]; then
        print_info "- Some services not responding (wait longer or check logs)"
    fi
    if [[ $network_secure == false ]]; then
        print_info "- Network security needs improvement"
    fi
    if [[ $validation_success == false ]]; then
        print_info "- DevOps validation found issues"
    fi
    
    exit 1
else
    print_error "❌ Infrastructure hardening needs more work"
    print_error "Critical services failed to start"
    
    echo ""
    print_info "Troubleshooting steps:"
    print_info "1. Check Docker logs: docker-compose logs"
    print_info "2. Verify Docker is running: docker ps"
    print_info "3. Check system resources: df -h && free -h"
    print_info "4. Review error messages above"
    
    exit 2
fi
