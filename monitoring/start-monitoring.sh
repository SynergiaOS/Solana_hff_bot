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
