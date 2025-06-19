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
