#!/bin/bash

# THE OVERMIND PROTOCOL - Infrastructure Hardening with Alternative Ports
# Resolves port conflicts and implements infrastructure hardening

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
🛡️ THE OVERMIND PROTOCOL - Infrastructure Hardening (Alternative Ports)
======================================================================
Mission: Resolve port conflicts and implement infrastructure hardening
EOF
echo -e "${NC}"

print_header "🎯 Infrastructure Hardening with Port Resolution"
echo ""

# ============================================================================
# STEP 1: Identify and resolve port conflicts
# ============================================================================
print_info "Step 1: Identifying port conflicts..."

# Check what's using the ports
print_info "Checking port usage..."
echo "Port 3000:" && ss -tlnp | grep :3000 || echo "  Not in use"
echo "Port 5432:" && ss -tlnp | grep :5432 || echo "  Not in use"
echo "Port 6379:" && ss -tlnp | grep :6379 || echo "  Not in use"

# Stop all existing containers
print_info "Stopping all existing containers..."
docker stop $(docker ps -q) 2>/dev/null || true
docker-compose -f docker-compose.overmind.yml down 2>/dev/null || true
docker-compose -f docker-compose.overmind-simple.yml down 2>/dev/null || true
docker-compose -f docker-compose.overmind-hardened.yml down 2>/dev/null || true

print_success "Stopped existing containers"

# ============================================================================
# STEP 2: Create alternative port configuration
# ============================================================================
print_info "Step 2: Creating alternative port configuration..."

# Create a simplified Docker Compose with alternative ports
cat > docker-compose.infrastructure-test.yml << 'EOF'
version: '3.8'

services:
  # Prometheus - Alternative port 9091
  prometheus:
    image: prom/prometheus:latest
    container_name: overmind-prometheus-test
    ports:
      - "127.0.0.1:9091:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-test-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - overmind-test-network

  # Grafana - Alternative port 3002
  grafana:
    image: grafana/grafana:latest
    container_name: overmind-grafana-test
    ports:
      - "127.0.0.1:3002:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=overmind123
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SECURITY_DISABLE_GRAVATAR=true
    volumes:
      - grafana-test-data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - overmind-test-network

  # PostgreSQL - Alternative port 5433
  postgres:
    image: postgres:15-alpine
    container_name: overmind-postgres-test
    environment:
      - POSTGRES_DB=snipercor
      - POSTGRES_USER=sniper
      - POSTGRES_PASSWORD=sniper123
    volumes:
      - postgres-test-data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5433:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sniper"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - overmind-test-network

  # DragonflyDB - Alternative port 6380
  dragonfly:
    image: docker.dragonflydb.io/dragonflydb/dragonfly:latest
    container_name: overmind-dragonfly-test
    command: dragonfly --logtostderr
    volumes:
      - dragonfly-test-data:/data
    ports:
      - "127.0.0.1:6380:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-p", "6379", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - overmind-test-network
    ulimits:
      memlock: -1

  # Chroma Vector DB - Alternative port 8001
  chroma:
    image: chromadb/chroma:latest
    container_name: overmind-chroma-test
    ports:
      - "127.0.0.1:8001:8000"
    volumes:
      - chroma-test-data:/chroma/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - overmind-test-network

networks:
  overmind-test-network:
    driver: bridge

volumes:
  prometheus-test-data:
  grafana-test-data:
  postgres-test-data:
  dragonfly-test-data:
  chroma-test-data:
EOF

print_success "Created alternative port configuration"

# ============================================================================
# STEP 3: Start infrastructure with alternative ports
# ============================================================================
print_info "Step 3: Starting infrastructure with alternative ports..."

# Start services one by one
print_info "Starting Prometheus on port 9091..."
docker-compose -f docker-compose.infrastructure-test.yml up -d prometheus

sleep 15

# Check Prometheus
if curl -s http://localhost:9091/-/healthy > /dev/null 2>&1; then
    print_success "Prometheus started successfully on port 9091"
    prometheus_healthy=true
else
    print_warning "Prometheus not responding on port 9091"
    prometheus_healthy=false
fi

print_info "Starting Grafana on port 3002..."
docker-compose -f docker-compose.infrastructure-test.yml up -d grafana

sleep 15

# Check Grafana
if curl -s http://localhost:3002/api/health > /dev/null 2>&1; then
    print_success "Grafana started successfully on port 3002"
    grafana_healthy=true
else
    print_warning "Grafana not responding on port 3002"
    grafana_healthy=false
fi

print_info "Starting PostgreSQL on port 5433..."
docker-compose -f docker-compose.infrastructure-test.yml up -d postgres

sleep 15

# Check PostgreSQL
if docker exec overmind-postgres-test pg_isready -U sniper > /dev/null 2>&1; then
    print_success "PostgreSQL started successfully on port 5433"
    postgres_healthy=true
else
    print_warning "PostgreSQL not responding on port 5433"
    postgres_healthy=false
fi

print_info "Starting DragonflyDB on port 6380..."
docker-compose -f docker-compose.infrastructure-test.yml up -d dragonfly

sleep 15

# Check DragonflyDB
if docker exec overmind-dragonfly-test redis-cli ping > /dev/null 2>&1; then
    print_success "DragonflyDB started successfully on port 6380"
    dragonfly_healthy=true
else
    print_warning "DragonflyDB not responding on port 6380"
    dragonfly_healthy=false
fi

print_info "Starting Chroma Vector DB on port 8001..."
docker-compose -f docker-compose.infrastructure-test.yml up -d chroma

sleep 15

# Check Chroma
if curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
    print_success "Chroma Vector DB started successfully on port 8001"
    chroma_healthy=true
else
    print_warning "Chroma Vector DB not responding on port 8001"
    chroma_healthy=false
fi

# ============================================================================
# STEP 4: Test network security
# ============================================================================
print_info "Step 4: Testing network security..."

network_secure=true

# Test that services are bound to localhost only
test_ports=(9091 3002 5433 6380 8001)
for port in "${test_ports[@]}"; do
    if ss -tlnp | grep ":$port " | grep "127.0.0.1" > /dev/null; then
        print_success "Port $port is properly secured (localhost only)"
    else
        print_warning "Port $port may not be properly secured"
        network_secure=false
    fi
done

# ============================================================================
# STEP 5: Create infrastructure health test
# ============================================================================
print_info "Step 5: Creating infrastructure health test..."

cat > test-infrastructure-health.py << 'EOF'
#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Infrastructure Health Test
Test infrastructure components with alternative ports
"""

import requests
import time
import subprocess
import sys

def test_endpoint(name, url, timeout=10):
    """Test if endpoint is healthy"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            print(f"✅ {name}: Healthy ({response.status_code})")
            return True
        else:
            print(f"⚠️ {name}: Responding but not healthy ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: Not responding ({str(e)})")
        return False

def test_database(name, container, command):
    """Test database connectivity"""
    try:
        result = subprocess.run(
            ["docker", "exec", container] + command,
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {name}: Healthy")
            return True
        else:
            print(f"❌ {name}: Not healthy ({result.stderr})")
            return False
    except Exception as e:
        print(f"❌ {name}: Error testing ({str(e)})")
        return False

def main():
    print("🧠 THE OVERMIND PROTOCOL - Infrastructure Health Test")
    print("=" * 60)
    
    # Test HTTP endpoints
    endpoints = [
        ("Prometheus", "http://localhost:9091/-/healthy"),
        ("Grafana", "http://localhost:3002/api/health"),
        ("Chroma Vector DB", "http://localhost:8001/api/v1/heartbeat")
    ]
    
    healthy_endpoints = 0
    for name, url in endpoints:
        if test_endpoint(name, url):
            healthy_endpoints += 1
    
    # Test databases
    databases = [
        ("PostgreSQL", "overmind-postgres-test", ["pg_isready", "-U", "sniper"]),
        ("DragonflyDB", "overmind-dragonfly-test", ["redis-cli", "ping"])
    ]
    
    healthy_databases = 0
    for name, container, command in databases:
        if test_database(name, container, command):
            healthy_databases += 1
    
    # Calculate overall health
    total_services = len(endpoints) + len(databases)
    healthy_services = healthy_endpoints + healthy_databases
    health_rate = (healthy_services / total_services) * 100
    
    print("\n📊 Infrastructure Health Summary:")
    print(f"  Healthy Services: {healthy_services}/{total_services}")
    print(f"  Health Rate: {health_rate:.1f}%")
    
    if health_rate >= 80:
        print("🎉 Infrastructure is healthy!")
        return 0
    elif health_rate >= 60:
        print("⚠️ Infrastructure has some issues")
        return 1
    else:
        print("❌ Infrastructure has critical issues")
        return 2

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x test-infrastructure-health.py

print_success "Created infrastructure health test"

# ============================================================================
# STEP 6: Run infrastructure health test
# ============================================================================
print_info "Step 6: Running infrastructure health test..."

if python3 test-infrastructure-health.py; then
    health_test_passed=true
    print_success "Infrastructure health test passed"
else
    health_test_passed=false
    print_warning "Infrastructure health test found issues"
fi

# ============================================================================
# STEP 7: Generate infrastructure hardening report
# ============================================================================
print_header "📊 Infrastructure Hardening Report"
echo ""

# Count healthy services
healthy_count=0
total_count=5

if $prometheus_healthy; then ((healthy_count++)); fi
if $grafana_healthy; then ((healthy_count++)); fi
if $postgres_healthy; then ((healthy_count++)); fi
if $dragonfly_healthy; then ((healthy_count++)); fi
if $chroma_healthy; then ((healthy_count++)); fi

health_rate=$((healthy_count * 100 / total_count))

echo "Infrastructure Health Summary:"
echo "  Healthy Services: $healthy_count/$total_count"
echo "  Health Rate: ${health_rate}%"
echo ""

echo "Service Status:"
echo "  Prometheus (9091): $(if $prometheus_healthy; then echo "✅ Healthy"; else echo "❌ Unhealthy"; fi)"
echo "  Grafana (3002): $(if $grafana_healthy; then echo "✅ Healthy"; else echo "❌ Unhealthy"; fi)"
echo "  PostgreSQL (5433): $(if $postgres_healthy; then echo "✅ Healthy"; else echo "❌ Unhealthy"; fi)"
echo "  DragonflyDB (6380): $(if $dragonfly_healthy; then echo "✅ Healthy"; else echo "❌ Unhealthy"; fi)"
echo "  Chroma (8001): $(if $chroma_healthy; then echo "✅ Healthy"; else echo "❌ Unhealthy"; fi)"
echo ""

echo "Security Assessment:"
echo "  Network Security: $(if $network_secure; then echo "✅ Secured"; else echo "⚠️ Needs work"; fi)"
echo "  Health Test: $(if $health_test_passed; then echo "✅ Passed"; else echo "❌ Failed"; fi)"

# ============================================================================
# FINAL ASSESSMENT
# ============================================================================
print_header "🎯 Infrastructure Hardening Results"
echo ""

if [[ $health_rate -ge 80 && $network_secure == true && $health_test_passed == true ]]; then
    print_success "🎉 Infrastructure hardening SUCCESSFUL!"
    print_success "Alternative ports resolved conflicts and services are healthy"
    
    echo ""
    print_info "Infrastructure is now ready for:"
    print_info "• Comprehensive DevOps testing"
    print_info "• Production deployment preparation"
    print_info "• AI Brain and trading system integration"
    
    echo ""
    print_info "Access points:"
    print_info "• Prometheus: http://localhost:9091"
    print_info "• Grafana: http://localhost:3002 (admin/overmind123)"
    print_info "• PostgreSQL: localhost:5433"
    print_info "• DragonflyDB: localhost:6380"
    print_info "• Chroma Vector DB: http://localhost:8001"
    
    exit 0
elif [[ $health_rate -ge 60 ]]; then
    print_warning "⚠️ Infrastructure hardening PARTIAL success"
    print_warning "Most services started but some issues remain"
    exit 1
else
    print_error "❌ Infrastructure hardening needs more work"
    print_error "Critical services failed to start"
    exit 2
fi
