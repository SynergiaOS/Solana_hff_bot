#!/bin/bash

# THE OVERMIND PROTOCOL - Monitoring Setup Script
# Creates comprehensive monitoring configuration for production

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo -e "${BLUE}🔧 Setting up THE OVERMIND PROTOCOL monitoring configuration...${NC}"

# Create monitoring directory structure
create_monitoring_structure() {
    print_status "Creating monitoring directory structure..."
    
    mkdir -p monitoring/{prometheus,grafana,alertmanager}
    mkdir -p monitoring/grafana/{dashboards,datasources}
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/alertmanager
    
    print_success "Monitoring directories created"
}

# Setup Prometheus configuration
setup_prometheus() {
    print_status "Setting up Prometheus configuration..."
    
    cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'overmind-production'
    environment: 'cloud'

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # OVERMIND Trading System
  - job_name: 'overmind-executor'
    static_configs:
      - targets: ['overmind-executor:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s
    scrape_timeout: 3s

  # OVERMIND AI Brain
  - job_name: 'overmind-brain'
    static_configs:
      - targets: ['overmind-brain:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  # TensorZero Gateway
  - job_name: 'tensorzero-gateway'
    static_configs:
      - targets: ['tensorzero-gateway:3000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # Chroma Vector Database
  - job_name: 'chroma-db'
    static_configs:
      - targets: ['overmind-chroma:8000']
    metrics_path: '/api/v1/metrics'
    scrape_interval: 30s

  # System Metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  # DragonflyDB
  - job_name: 'dragonfly'
    static_configs:
      - targets: ['overmind-dragonfly:6379']
    scrape_interval: 30s

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['overmind-postgres:5432']
    scrape_interval: 30s
EOF

    # Setup alert rules
    cat > monitoring/prometheus/alert_rules.yml << 'EOF'
groups:
  - name: overmind_critical_alerts
    rules:
      - alert: TradingSystemDown
        expr: up{job="overmind-executor"} == 0
        for: 30s
        labels:
          severity: critical
          component: trading-system
        annotations:
          summary: "🚨 OVERMIND Trading System is DOWN"
          description: "The main trading system has been unreachable for {{ $for }}"

      - alert: AIBrainDown
        expr: up{job="overmind-brain"} == 0
        for: 1m
        labels:
          severity: critical
          component: ai-brain
        annotations:
          summary: "🧠 OVERMIND AI Brain is DOWN"
          description: "The AI Brain has been unreachable for {{ $for }}"

      - alert: VectorDatabaseDown
        expr: up{job="chroma-db"} == 0
        for: 2m
        labels:
          severity: critical
          component: vector-db
        annotations:
          summary: "🗄️ Vector Database is DOWN"
          description: "Chroma vector database is unreachable - AI memory affected"

  - name: overmind_performance_alerts
    rules:
      - alert: HighExecutionLatency
        expr: overmind_execution_latency_ms > 100
        for: 2m
        labels:
          severity: warning
          component: execution
        annotations:
          summary: "⚡ High execution latency detected"
          description: "Execution latency is {{ $value }}ms (threshold: 100ms)"

      - alert: LowAIConfidence
        expr: avg_over_time(overmind_ai_confidence[5m]) < 0.6
        for: 3m
        labels:
          severity: warning
          component: ai-brain
        annotations:
          summary: "🤖 Low AI confidence detected"
          description: "Average AI confidence is {{ $value }} (threshold: 0.6)"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          component: system
        annotations:
          summary: "💾 High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

  - name: overmind_trading_alerts
    rules:
      - alert: DailyLossLimitApproaching
        expr: overmind_daily_pnl < -800
        for: 1m
        labels:
          severity: warning
          component: risk-management
        annotations:
          summary: "📉 Daily loss limit approaching"
          description: "Daily P&L is {{ $value }} (limit: -1000)"

      - alert: DailyLossLimitExceeded
        expr: overmind_daily_pnl < -1000
        for: 0s
        labels:
          severity: critical
          component: risk-management
        annotations:
          summary: "🛑 DAILY LOSS LIMIT EXCEEDED"
          description: "Daily P&L is {{ $value }} - EMERGENCY STOP REQUIRED"

      - alert: NoTradingActivity
        expr: increase(overmind_trades_total[1h]) == 0
        for: 2h
        labels:
          severity: warning
          component: trading
        annotations:
          summary: "📊 No trading activity detected"
          description: "No trades executed in the last 2 hours"
EOF

    print_success "Prometheus configuration created"
}

# Setup Grafana dashboards
setup_grafana() {
    print_status "Setting up Grafana dashboards..."
    
    # Datasource configuration
    cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # Dashboard provisioning
    cat > monitoring/grafana/dashboards/dashboard.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'overmind-dashboards'
    orgId: 1
    folder: 'OVERMIND'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    # Main OVERMIND dashboard
    cat > monitoring/grafana/dashboards/overmind-main.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "THE OVERMIND PROTOCOL - Main Dashboard",
    "tags": ["overmind", "trading", "ai"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "System Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"overmind-executor\"}",
            "legendFormat": "Trading System"
          },
          {
            "expr": "up{job=\"overmind-brain\"}",
            "legendFormat": "AI Brain"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Daily P&L",
        "type": "stat",
        "targets": [
          {
            "expr": "overmind_daily_pnl",
            "legendFormat": "P&L"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Execution Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "overmind_execution_latency_ms",
            "legendFormat": "Latency (ms)"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "AI Confidence",
        "type": "graph",
        "targets": [
          {
            "expr": "overmind_ai_confidence",
            "legendFormat": "Confidence"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "id": 5,
        "title": "Trade Volume",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(overmind_trades_total[5m])",
            "legendFormat": "Trades/sec"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF

    print_success "Grafana dashboards created"
}

# Setup AlertManager
setup_alertmanager() {
    print_status "Setting up AlertManager configuration..."
    
    cat > monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'overmind@yourdomain.com'

route:
  group_by: ['alertname', 'component']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        component: trading-system
      receiver: 'trading-alerts'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'

  - name: 'critical-alerts'
    webhook_configs:
      - url: 'http://localhost:5001/critical'
        title: '🚨 OVERMIND CRITICAL ALERT'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: 'trading-alerts'
    webhook_configs:
      - url: 'http://localhost:5001/trading'
        title: '📊 OVERMIND Trading Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'component']
EOF

    print_success "AlertManager configuration created"
}

# Create monitoring startup script
create_monitoring_startup() {
    print_status "Creating monitoring startup script..."
    
    cat > monitoring/start-monitoring.sh << 'EOF'
#!/bin/bash

# THE OVERMIND PROTOCOL - Monitoring Startup Script

echo "🔧 Starting THE OVERMIND PROTOCOL monitoring stack..."

# Start monitoring services
docker-compose -f docker-compose.production.yml up -d \
    prometheus \
    grafana \
    alertmanager \
    node-exporter

echo "✅ Monitoring stack started"
echo ""
echo "📊 Access URLs:"
echo "  Grafana:      http://localhost:3001"
echo "  Prometheus:   http://localhost:9090"
echo "  AlertManager: http://localhost:9093"
echo ""
echo "🔑 Default Grafana credentials: admin / (check .env file)"
EOF

    chmod +x monitoring/start-monitoring.sh
    
    print_success "Monitoring startup script created"
}

# Main execution
main() {
    create_monitoring_structure
    setup_prometheus
    setup_grafana
    setup_alertmanager
    create_monitoring_startup
    
    echo ""
    print_success "🎯 THE OVERMIND PROTOCOL monitoring setup completed!"
    echo ""
    print_status "Next steps:"
    echo "1. Review monitoring configuration files"
    echo "2. Customize alert thresholds if needed"
    echo "3. Configure notification channels (email, Slack, etc.)"
    echo "4. Start monitoring with: ./monitoring/start-monitoring.sh"
    echo ""
    print_warning "⚠️  Remember to secure Grafana with strong passwords"
}

# Execute main function
main "$@"
