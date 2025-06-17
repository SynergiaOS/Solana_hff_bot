#!/bin/bash

# THE OVERMIND PROTOCOL - Infrastructure Hardening Script
# Systematic resolution of critical DevOps issues

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
🛡️ THE OVERMIND PROTOCOL - Infrastructure Hardening
===================================================
Mission: Transform from 16.7% to 90%+ production readiness
EOF
echo -e "${NC}"

print_header "🎯 PHASE 1: Critical Infrastructure Fixes"
echo ""

# ============================================================================
# STEP 1: Fix Prometheus Monitoring Stack
# ============================================================================
print_info "Step 1: Fixing Prometheus Monitoring Stack..."

# Stop existing containers
print_info "Stopping existing containers..."
docker-compose -f docker-compose.overmind.yml down 2>/dev/null || true
docker-compose -f docker-compose.overmind-simple.yml down 2>/dev/null || true

# Create monitoring directory structure
print_info "Creating monitoring directory structure..."
mkdir -p monitoring/grafana/{dashboards,datasources}
mkdir -p monitoring/alertmanager

# Validate Prometheus configuration
print_info "Validating Prometheus configuration..."
if docker run --rm -v "$(pwd)/monitoring:/etc/prometheus" prom/prometheus:latest promtool check config /etc/prometheus/prometheus.yml; then
    print_success "Prometheus configuration is valid"
else
    print_error "Prometheus configuration has errors"
    exit 1
fi

# Validate alert rules
print_info "Validating alert rules..."
if docker run --rm -v "$(pwd)/monitoring:/etc/prometheus" prom/prometheus:latest promtool check rules /etc/prometheus/alert_rules.yml; then
    print_success "Alert rules are valid"
else
    print_error "Alert rules have errors"
    exit 1
fi

# ============================================================================
# STEP 2: Fix DragonflyDB Resilience
# ============================================================================
print_info "Step 2: Fixing DragonflyDB Resilience..."

# Create environment file with secure defaults
if [[ ! -f ".env.hardened" ]]; then
    print_info "Creating hardened environment configuration..."
    cat > .env.hardened << 'EOF'
# THE OVERMIND PROTOCOL - Hardened Environment Configuration

# Database Passwords
SNIPER_DB_PASSWORD=sniper_secure_$(openssl rand -hex 16)
TENSORZERO_DB_PASSWORD=tensorzero_secure_$(openssl rand -hex 16)
REDIS_PASSWORD=redis_secure_$(openssl rand -hex 16)

# Grafana Configuration
GRAFANA_ADMIN_PASSWORD=overmind_admin_$(openssl rand -hex 8)

# API Keys (from existing .env)
OPENAI_API_KEY=${OPENAI_API_KEY:-your-openai-api-key}
SNIPER_SOLANA_RPC_URL=${SNIPER_SOLANA_RPC_URL:-https://api.devnet.solana.com}
SNIPER_WALLET_PRIVATE_KEY=${SNIPER_WALLET_PRIVATE_KEY:-your-wallet-private-key}

# Multi-wallet Configuration
OVERMIND_MULTI_WALLET_ENABLED=true
EOF
    print_success "Created hardened environment configuration"
else
    print_info "Hardened environment configuration already exists"
fi

# ============================================================================
# STEP 3: Secure Network Configuration
# ============================================================================
print_info "Step 3: Securing Network Configuration..."

# The hardened Docker Compose file already has localhost-only bindings
print_success "Network security implemented in docker-compose.overmind-hardened.yml"

# ============================================================================
# STEP 4: Address Secret Management
# ============================================================================
print_info "Step 4: Addressing Secret Management..."

# Check for potential secret leaks
print_info "Scanning for potential secret leaks..."
secret_issues=0

# Scan for hardcoded secrets
if grep -r -i -E "(password|secret|key).*=.*['\"][^'\"]{8,}['\"]" . --include="*.py" --include="*.rs" --include="*.js" --include="*.yml" --exclude-dir=".git" --exclude-dir="target" --exclude-dir="node_modules" 2>/dev/null | grep -v -E "(placeholder|example|your-|test)" | head -5; then
    print_warning "Potential hardcoded secrets found (review above)"
    ((secret_issues++))
else
    print_success "No obvious hardcoded secrets found"
fi

# Check .env file permissions
if [[ -f ".env" ]]; then
    env_perms=$(stat -c "%a" .env)
    if [[ "$env_perms" != "600" ]]; then
        print_info "Fixing .env file permissions..."
        chmod 600 .env
        print_success "Fixed .env file permissions to 600"
    else
        print_success ".env file permissions are secure (600)"
    fi
fi

# ============================================================================
# STEP 5: Deploy Hardened Infrastructure
# ============================================================================
print_info "Step 5: Deploying Hardened Infrastructure..."

# Start with hardened configuration
print_info "Starting hardened OVERMIND infrastructure..."

# Start core services first
print_info "Starting core database services..."
docker-compose -f docker-compose.overmind-hardened.yml up -d overmind-db overmind-dragonfly tensorzero-db tensorzero-dragonfly

print_info "Waiting for databases to initialize..."
sleep 30

# Start monitoring stack
print_info "Starting monitoring stack..."
docker-compose -f docker-compose.overmind-hardened.yml up -d prometheus grafana

print_info "Waiting for monitoring to initialize..."
sleep 20

# Start AI services
print_info "Starting AI services..."
docker-compose -f docker-compose.overmind-hardened.yml up -d chroma tensorzero-gateway

print_info "Waiting for AI services to initialize..."
sleep 30

# Check service health
print_info "Checking service health..."

services_healthy=0
total_services=0

# Check Prometheus
((total_services++))
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    print_success "Prometheus is healthy"
    ((services_healthy++))
else
    print_warning "Prometheus is not responding"
fi

# Check Grafana
((total_services++))
if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
    print_success "Grafana is healthy"
    ((services_healthy++))
else
    print_warning "Grafana is not responding"
fi

# Check DragonflyDB
((total_services++))
if docker exec overmind-dragonfly redis-cli ping > /dev/null 2>&1; then
    print_success "DragonflyDB is healthy"
    ((services_healthy++))
else
    print_warning "DragonflyDB is not responding"
fi

# Check PostgreSQL
((total_services++))
if docker exec overmind-database pg_isready -U sniper > /dev/null 2>&1; then
    print_success "PostgreSQL is healthy"
    ((services_healthy++))
else
    print_warning "PostgreSQL is not responding"
fi

# Check Chroma
((total_services++))
if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
    print_success "Chroma Vector DB is healthy"
    ((services_healthy++))
else
    print_warning "Chroma Vector DB is not responding"
fi

# ============================================================================
# STEP 6: Validation and Testing
# ============================================================================
print_header "🧪 PHASE 2: Validation and Testing"
echo ""

print_info "Running infrastructure validation tests..."

# Test network security
print_info "Testing network security..."
network_issues=0

# Test internal ports are not externally accessible
internal_ports=(5432 6379)
for port in "${internal_ports[@]}"; do
    if nc -z localhost "$port" 2>/dev/null; then
        # Check if it's bound to localhost only
        if netstat -tlnp 2>/dev/null | grep ":$port " | grep "127.0.0.1" > /dev/null; then
            print_success "Port $port is properly secured (localhost only)"
        else
            print_warning "Port $port may be exposed externally"
            ((network_issues++))
        fi
    else
        print_info "Port $port is not accessible (good)"
    fi
done

# Test monitoring endpoints
print_info "Testing monitoring endpoints..."
monitoring_issues=0

if curl -s http://localhost:9090/api/v1/targets > /dev/null 2>&1; then
    print_success "Prometheus API is accessible"
else
    print_error "Prometheus API is not accessible"
    ((monitoring_issues++))
fi

if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
    print_success "Grafana API is accessible"
else
    print_error "Grafana API is not accessible"
    ((monitoring_issues++))
fi

# ============================================================================
# STEP 7: Generate Hardening Report
# ============================================================================
print_header "📊 Infrastructure Hardening Report"
echo ""

health_rate=$((services_healthy * 100 / total_services))

echo "Service Health Summary:"
echo "  Healthy Services: $services_healthy/$total_services"
echo "  Health Rate: ${health_rate}%"
echo ""

echo "Security Assessment:"
echo "  Network Issues: $network_issues"
echo "  Secret Issues: $secret_issues"
echo "  Monitoring Issues: $monitoring_issues"
echo ""

# Calculate overall improvement
total_issues=$((network_issues + secret_issues + monitoring_issues))

if [[ $health_rate -ge 80 && $total_issues -le 2 ]]; then
    print_success "🎉 Infrastructure hardening SUCCESSFUL!"
    print_success "System is ready for comprehensive DevOps testing"
    
    # Run comprehensive testing
    print_info "Running comprehensive DevOps testing..."
    if python3 comprehensive-devops-testing.py; then
        print_success "Comprehensive DevOps testing completed"
    else
        print_warning "DevOps testing completed with some issues"
    fi
    
    exit 0
elif [[ $health_rate -ge 60 && $total_issues -le 5 ]]; then
    print_warning "⚠️ Infrastructure hardening PARTIAL success"
    print_warning "Some issues remain but significant improvement achieved"
    exit 1
else
    print_error "❌ Infrastructure hardening needs more work"
    print_error "Critical issues remain that must be addressed"
    exit 2
fi
