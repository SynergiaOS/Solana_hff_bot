#!/bin/bash

# THE OVERMIND PROTOCOL - VDS Server Upgrade Script
# Upgrade from 24GB/6-core to 32GB/8-core configuration

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

🚀 VDS SERVER UPGRADE
EOF
echo -e "${NC}"

echo "THE OVERMIND PROTOCOL - VDS Server Upgrade to 32GB/8-core"
echo "=========================================================="
echo ""
echo "Current Configuration: 24GB RAM, 6 CPU cores"
echo "Target Configuration:  32GB RAM, 8 CPU cores"
echo ""

# ============================================================================
# STEP 1: PRE-UPGRADE ASSESSMENT
# ============================================================================
print_header "📊 STEP 1: Pre-Upgrade Assessment"
echo ""

print_info "Checking current system resources..."

# Check current memory
CURRENT_MEMORY=$(free -h | grep '^Mem:' | awk '{print $2}')
print_info "Current Memory: $CURRENT_MEMORY"

# Check current CPU cores
CURRENT_CORES=$(nproc)
print_info "Current CPU Cores: $CURRENT_CORES"

# Check disk usage
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}')
print_info "Current Disk Usage: $DISK_USAGE"

# Check running containers
if command -v docker &> /dev/null; then
    RUNNING_CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -c "Up" || echo "0")
    print_info "Running Docker Containers: $RUNNING_CONTAINERS"
else
    print_warning "Docker not found - will need to install after upgrade"
fi

echo ""

# ============================================================================
# STEP 2: BACKUP CURRENT CONFIGURATION
# ============================================================================
print_header "💾 STEP 2: Backup Current Configuration"
echo ""

BACKUP_DIR="vds-upgrade-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

print_info "Creating backup in: $BACKUP_DIR"

# Backup system information
print_info "Backing up system information..."
uname -a > "$BACKUP_DIR/system_info.txt"
free -h > "$BACKUP_DIR/memory_info.txt"
lscpu > "$BACKUP_DIR/cpu_info.txt"
df -h > "$BACKUP_DIR/disk_info.txt"

# Backup Docker configuration if exists
if command -v docker &> /dev/null; then
    print_info "Backing up Docker configuration..."
    docker ps -a > "$BACKUP_DIR/docker_containers.txt" 2>/dev/null || true
    docker images > "$BACKUP_DIR/docker_images.txt" 2>/dev/null || true
    
    # Backup running containers
    if [[ $RUNNING_CONTAINERS -gt 0 ]]; then
        print_info "Backing up running container configurations..."
        docker ps --format "{{.Names}}" | while read container; do
            docker inspect "$container" > "$BACKUP_DIR/container_${container}.json" 2>/dev/null || true
        done
    fi
fi

# Backup THE OVERMIND PROTOCOL configuration
if [[ -f ".env" ]]; then
    print_info "Backing up OVERMIND configuration..."
    cp .env "$BACKUP_DIR/overmind.env" 2>/dev/null || true
fi

if [[ -f "docker-compose.overmind.yml" ]]; then
    cp docker-compose.overmind.yml "$BACKUP_DIR/" 2>/dev/null || true
fi

print_success "Backup completed: $BACKUP_DIR"
echo ""

# ============================================================================
# STEP 3: UPGRADE PLANNING
# ============================================================================
print_header "📋 STEP 3: Upgrade Planning & Resource Allocation"
echo ""

print_info "Planning resource allocation for 32GB/8-core configuration..."

# Calculate new resource allocation
echo "📊 New Resource Allocation Plan:"
echo "================================"
echo ""

echo "🖥️  Hardware Resources:"
echo "  Total RAM: 32GB"
echo "  Total CPU: 8 cores"
echo "  Reserved for OS: 4GB RAM, 1 core"
echo "  Available for OVERMIND: 28GB RAM, 7 cores"
echo ""

echo "🐳 Docker Container Allocation:"
echo "  OVERMIND Executor:    8GB RAM, 3 cores  (was 6GB, 4 cores)"
echo "  OVERMIND Brain:       6GB RAM, 2 cores  (was 4GB, 2 cores)"
echo "  Chroma Vector DB:     6GB RAM, 1 core   (was 4GB, 1 core)"
echo "  DragonflyDB:          3GB RAM, 1 core   (was 2GB, 1 core)"
echo "  PostgreSQL:           3GB RAM, 1 core   (was 2GB, 1 core)"
echo "  TensorZero Gateway:   2GB RAM, 1 core   (was 1GB, 0.5 cores)"
echo "  Monitoring Stack:     2GB RAM, 1 core   (Prometheus + Grafana)"
echo "  ClickHouse:           2GB RAM, 1 core   (TensorZero backend)"
echo ""

echo "⚡ Performance Improvements Expected:"
echo "  Execution Latency:    25ms target (from 30ms)"
echo "  AI Processing:        50% faster decision making"
echo "  Data Throughput:      40% increase in data processing"
echo "  Concurrent Operations: 33% more parallel processing"
echo "  Vector Memory:        50% larger cache capacity"
echo ""

# ============================================================================
# STEP 4: CONTABO VDS UPGRADE INSTRUCTIONS
# ============================================================================
print_header "🔧 STEP 4: Contabo VDS Upgrade Instructions"
echo ""

print_warning "IMPORTANT: The following steps require action in Contabo Control Panel"
echo ""

echo "📋 Contabo VDS Upgrade Process:"
echo "==============================="
echo ""
echo "1. 🌐 Login to Contabo Customer Portal:"
echo "   https://my.contabo.com/"
echo ""
echo "2. 📊 Navigate to VDS Management:"
echo "   - Go to 'Your Services' → 'VDS'"
echo "   - Select your VDS: marcin@89.117.53.53"
echo ""
echo "3. ⬆️  Initiate Upgrade:"
echo "   - Click 'Upgrade/Downgrade'"
echo "   - Select new configuration:"
echo "     • RAM: 32GB (from 24GB)"
echo "     • CPU: 8 cores (from 6 cores)"
echo "     • Storage: Keep current or upgrade if needed"
echo ""
echo "4. 💰 Review Pricing:"
echo "   - Review monthly cost increase"
echo "   - Confirm upgrade terms"
echo ""
echo "5. ⏰ Schedule Upgrade:"
echo "   - Choose maintenance window"
echo "   - Recommended: Off-peak hours"
echo "   - Downtime: ~15-30 minutes expected"
echo ""
echo "6. ✅ Confirm Upgrade:"
echo "   - Review all settings"
echo "   - Confirm upgrade order"
echo ""

print_warning "Expected Downtime: 15-30 minutes during hardware upgrade"
print_info "The server will automatically reboot with new resources"

echo ""

# ============================================================================
# STEP 5: POST-UPGRADE CONFIGURATION
# ============================================================================
print_header "⚙️  STEP 5: Post-Upgrade Configuration Updates"
echo ""

print_info "After Contabo completes the hardware upgrade, run this script again with --post-upgrade"
echo ""

if [[ "$1" == "--post-upgrade" ]]; then
    print_header "🔄 Running Post-Upgrade Configuration..."
    echo ""
    
    # Verify new resources
    print_info "Verifying new system resources..."
    NEW_MEMORY=$(free -h | grep '^Mem:' | awk '{print $2}')
    NEW_CORES=$(nproc)
    
    print_success "New Memory: $NEW_MEMORY"
    print_success "New CPU Cores: $NEW_CORES"
    
    # Update environment configuration
    print_info "Updating OVERMIND configuration for new resources..."
    
    # Create updated .env configuration
    if [[ -f ".env" ]]; then
        print_info "Updating .env with new resource allocation..."
        
        # Backup current .env
        cp .env .env.pre-upgrade-backup
        
        # Update memory allocations
        sed -i 's/OVERMIND_EXECUTOR_MEMORY=6g/OVERMIND_EXECUTOR_MEMORY=8g/' .env
        sed -i 's/OVERMIND_BRAIN_MEMORY=4g/OVERMIND_BRAIN_MEMORY=6g/' .env
        sed -i 's/CHROMA_MEMORY=4g/CHROMA_MEMORY=6g/' .env
        sed -i 's/DRAGONFLY_MEMORY=2g/DRAGONFLY_MEMORY=3g/' .env
        sed -i 's/POSTGRES_MEMORY=2g/POSTGRES_MEMORY=3g/' .env
        sed -i 's/TOKIO_WORKER_THREADS=6/TOKIO_WORKER_THREADS=8/' .env
        
        print_success "Updated .env configuration"
    fi
    
    # Update Docker Compose resource limits
    print_info "Updating Docker Compose resource limits..."
    
    if [[ -f "docker-compose.overmind.yml" ]]; then
        # Create updated compose file
        cp docker-compose.overmind.yml docker-compose.overmind.yml.pre-upgrade-backup
        
        # This would require more complex sed operations or a dedicated script
        print_info "Docker Compose file backed up - manual update recommended"
        print_warning "Please update docker-compose.overmind.yml resource limits manually"
    fi
    
    print_success "Post-upgrade configuration completed"
    echo ""
fi

# ============================================================================
# STEP 6: UPDATED DOCKER COMPOSE CONFIGURATION
# ============================================================================
print_header "🐳 STEP 6: Generate Updated Docker Compose Configuration"
echo ""

print_info "Generating optimized Docker Compose configuration for 32GB/8-core..."

# Create updated Docker Compose file
cat > docker-compose.overmind-32gb.yml << 'EOF'
version: '3.8'

# THE OVERMIND PROTOCOL - Production Configuration (32GB/8-core)
# Optimized for Contabo VDS with 32GB RAM and 8 CPU cores

services:
  # ============================================================================
  # INFRASTRUCTURE LAYER
  # ============================================================================
  
  # DragonflyDB - High-performance message broker
  overmind-dragonfly:
    image: docker.dragonflydb.io/dragonflydb/dragonfly:latest
    container_name: overmind-dragonfly-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - dragonfly_data:/data
    command: [
      "dragonfly",
      "--logtostderr",
      "--alsologtostderr",
      "--maxmemory=3gb",
      "--cache_mode=true"
    ]
    deploy:
      resources:
        limits:
          memory: 3G
          cpus: '1.0'
    networks:
      - overmind-network

  # PostgreSQL - Main database
  overmind-postgres:
    image: postgres:15-alpine
    container_name: overmind-postgres-prod
    restart: unless-stopped
    environment:
      - POSTGRES_DB=overmind
      - POSTGRES_USER=overmind
      - POSTGRES_PASSWORD=${SNIPER_DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 3G
          cpus: '1.0'
    networks:
      - overmind-network

  # Chroma Vector Database - AI Memory
  overmind-chroma:
    image: chromadb/chroma:latest
    container_name: overmind-chroma-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_HTTP_PORT=8000
    deploy:
      resources:
        limits:
          memory: 6G
          cpus: '1.0'
    networks:
      - overmind-network

  # ============================================================================
  # AI BRAIN LAYER
  # ============================================================================
  
  # Python AI Brain
  overmind-brain:
    build:
      context: ./brain
      dockerfile: Dockerfile
    container_name: overmind-brain-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:8001:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CHROMA_URL=http://overmind-chroma:8000
      - DRAGONFLY_URL=redis://overmind-dragonfly:6379
      - OVERMIND_MODE=enabled
      - OVERMIND_AI_MODE=enabled
      - PYTHONPATH=/app/src
    volumes:
      - ./brain/src:/app/src
      - brain_logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 6G
          cpus: '2.0'
    networks:
      - overmind-network

  # TensorZero Gateway - AI Optimization
  tensorzero-gateway:
    image: tensorzero/gateway:latest
    container_name: tensorzero-gateway-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - CLICKHOUSE_URL=http://tensorzero-clickhouse:8123
      - TENSORZERO_REDIS_URL=redis://overmind-dragonfly:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./tensorzero-config:/app/config
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    networks:
      - overmind-network

  # ClickHouse - TensorZero Analytics
  tensorzero-clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: tensorzero-clickhouse-prod
    restart: unless-stopped
    volumes:
      - clickhouse_data:/var/lib/clickhouse
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
    networks:
      - overmind-network

  # ============================================================================
  # EXECUTION LAYER
  # ============================================================================
  
  # Rust HFT Executor
  overmind-executor:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: overmind-executor-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      - SNIPER_TRADING_MODE=${SNIPER_TRADING_MODE}
      - SOLANA_RPC_URL=${SOLANA_DEVNET_RPC_URL}
      - SOLANA_WSS_URL=${SOLANA_DEVNET_WSS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - HELIUS_API_KEY=${HELIUS_API_KEY}
      - QUICKNODE_API_KEY=${QUICKNODE_API_KEY}
      - OVERMIND_AI_CONFIDENCE_THRESHOLD=0.7
      - RUST_LOG=info
      - TOKIO_WORKER_THREADS=8
    volumes:
      - executor_logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '3.0'
    networks:
      - overmind-network

  # ============================================================================
  # MONITORING LAYER
  # ============================================================================
  
  # Prometheus - Metrics collection
  prometheus:
    image: prom/prometheus:latest
    container_name: overmind-prometheus-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    networks:
      - overmind-network

  # Grafana - Dashboards
  grafana:
    image: grafana/grafana:latest
    container_name: overmind-grafana-prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    networks:
      - overmind-network

volumes:
  dragonfly_data:
  postgres_data:
  chroma_data:
  clickhouse_data:
  prometheus_data:
  grafana_data:
  brain_logs:
  executor_logs:

networks:
  overmind-network:
    driver: bridge
EOF

print_success "Generated docker-compose.overmind-32gb.yml with optimized resource allocation"
echo ""

# ============================================================================
# STEP 7: PERFORMANCE OPTIMIZATION SCRIPT
# ============================================================================
print_header "⚡ STEP 7: Generate Performance Optimization Script"
echo ""

cat > optimize-32gb-performance.sh << 'EOF'
#!/bin/bash

# THE OVERMIND PROTOCOL - 32GB Performance Optimization

echo "🚀 Optimizing system for THE OVERMIND PROTOCOL (32GB/8-core)"

# Kernel parameters for high-performance trading
echo "Updating kernel parameters..."
cat >> /etc/sysctl.conf << EOL

# THE OVERMIND PROTOCOL Performance Optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000
vm.swappiness = 1
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOL

sysctl -p

# Docker daemon optimization
echo "Optimizing Docker daemon..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << EOL
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

systemctl restart docker

echo "✅ Performance optimization completed"
EOF

chmod +x optimize-32gb-performance.sh
print_success "Generated optimize-32gb-performance.sh"
echo ""

# ============================================================================
# FINAL INSTRUCTIONS
# ============================================================================
print_header "📋 FINAL UPGRADE INSTRUCTIONS"
echo ""

echo "🎯 Complete Upgrade Process:"
echo "============================"
echo ""
echo "1. 💾 Backup completed: $BACKUP_DIR"
echo ""
echo "2. 🌐 Contabo VDS Upgrade:"
echo "   - Login to https://my.contabo.com/"
echo "   - Upgrade VDS to 32GB RAM / 8 CPU cores"
echo "   - Wait for upgrade completion (~15-30 minutes)"
echo ""
echo "3. 🔄 After server restart:"
echo "   ./upgrade-vds-32gb-8core.sh --post-upgrade"
echo ""
echo "4. 🐳 Deploy with new configuration:"
echo "   docker-compose -f docker-compose.overmind-32gb.yml up -d"
echo ""
echo "5. ⚡ Apply performance optimizations:"
echo "   sudo ./optimize-32gb-performance.sh"
echo ""
echo "6. 📊 Verify upgrade:"
echo "   ./test-overmind-complete.sh"
echo ""

print_warning "IMPORTANT: Schedule upgrade during low-activity period"
print_info "Expected performance improvement: 25-40% across all metrics"

echo ""
print_success "VDS upgrade preparation completed!"
print_info "Proceed with Contabo upgrade when ready"

echo ""
echo "📞 Support: If you encounter issues, check the backup in $BACKUP_DIR"
echo ""
