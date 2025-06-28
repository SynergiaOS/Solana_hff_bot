#!/bin/bash

echo "🔧 OVERMIND PROTOCOL - Emergency Monitoring Access Fix"
echo "====================================================="

# Check if we can determine the firewall system
if command -v ufw >/dev/null 2>&1; then
    echo "📋 Detected UFW firewall"
    echo "Opening required ports for monitoring..."
    
    sudo ufw allow 3000/tcp comment "Grafana OVERMIND"
    sudo ufw allow 9090/tcp comment "Prometheus OVERMIND" 
    sudo ufw allow 8000/tcp comment "ChromaDB OVERMIND"
    sudo ufw status
    
elif command -v firewall-cmd >/dev/null 2>&1; then
    echo "📋 Detected firewalld"
    echo "Opening required ports for monitoring..."
    
    sudo firewall-cmd --permanent --add-port=3000/tcp
    sudo firewall-cmd --permanent --add-port=9090/tcp
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --reload
    sudo firewall-cmd --list-ports
    
else
    echo "⚠️ Firewall system not detected or accessible"
    echo "Manual configuration may be required on VDS provider panel"
fi

echo ""
echo "🔍 Testing local access..."
curl -s http://localhost:3000 >/dev/null && echo "✅ Grafana accessible locally" || echo "❌ Grafana not accessible"
curl -s http://localhost:9090 >/dev/null && echo "✅ Prometheus accessible locally" || echo "❌ Prometheus not accessible"

echo ""
echo "📊 Open ports on system:"
ss -tlnp | grep -E ":3000|:9090|:8000"

echo ""
echo "🚨 If still not accessible from external IP:"
echo "1. Check VDS provider firewall settings"
echo "2. Ensure ports 3000, 9090, 8000 are open"
echo "3. Try alternative monitoring setup"

echo ""
echo "🌐 Expected access URLs:"
echo "   Grafana: http://89.117.53.53:3000"
echo "   Prometheus: http://89.117.53.53:9090"