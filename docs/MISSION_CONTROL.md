# 🎛️ THE OVERMIND PROTOCOL - Mission Control Dashboard

## 📊 **OVERVIEW**

Mission Control Dashboard provides centralized control and monitoring for THE OVERMIND PROTOCOL. It consists of two main components:

1. **Kestra Workflows** - System lifecycle management (start/stop)
2. **FastAPI Endpoints** - Real-time monitoring and control

---

## 🚀 **KESTRA WORKFLOWS**

### **Access Kestra Dashboard**
```
URL: http://localhost:8080 (or your server IP)
```

### **Available Workflows**

#### **1. start-overmind-system**
- **Purpose**: Start THE OVERMIND PROTOCOL
- **Namespace**: `operations.overmind`
- **Inputs**:
  - `environment`: devnet/mainnet
  - `trading_mode`: paper/live

#### **2. emergency-stop-system**
- **Purpose**: Emergency shutdown of all systems
- **Namespace**: `operations.overmind`
- **Inputs**:
  - `environment`: devnet/mainnet
  - `force_stop`: true/false (removes volumes)

### **How to Use Kestra**
1. Open Kestra dashboard in browser
2. Navigate to "Flows" section
3. Find the desired workflow
4. Click "Execute" button
5. Fill in required inputs
6. Monitor execution logs

---

## 🌐 **FASTAPI ENDPOINTS**

### **AI Brain API (Port 8000)**

#### **Health & Status**
```bash
# Basic health check
curl http://localhost:8000/health

# Comprehensive system status
curl http://localhost:8000/status
```

#### **Transaction Monitoring**
```bash
# Get recent transaction logs (last 50)
curl http://localhost:8000/logs/transactions

# Get specific number of transactions
curl "http://localhost:8000/logs/transactions?limit=100"
```

#### **Wallet Monitoring**
```bash
# Get wallet balances
curl http://localhost:8000/wallets/status
```

#### **Emergency Controls**
```bash
# Emergency stop
curl -X POST http://localhost:8000/control/emergency-stop \
  -H "Content-Type: application/json" \
  -d '{"reason": "Manual emergency stop"}'

# Resume trading
curl -X POST http://localhost:8000/control/resume
```

### **Rust Executor API (Port 8080)**

#### **Health & Metrics**
```bash
# Health check
curl http://localhost:8080/health

# System metrics
curl http://localhost:8080/metrics

# System status
curl http://localhost:8080/status
```

---

## 📊 **MONITORING COMMANDS**

### **System Status Overview**
```bash
#!/bin/bash
echo "🎯 THE OVERMIND PROTOCOL - System Status"
echo "========================================"

echo "🧠 AI Brain Status:"
curl -s http://localhost:8000/status | jq '.ai_brain_status'

echo "⚡ Rust Executor Status:"
curl -s http://localhost:8080/health | jq '.status'

echo "💰 Wallet Balance:"
curl -s http://localhost:8000/wallets/status | jq '.main_trading_wallet.balance_sol'

echo "📊 Recent Transactions:"
curl -s http://localhost:8000/logs/transactions | jq 'length'
```

### **Docker Container Status**
```bash
# Check running containers
docker-compose -f docker-compose.devnet.yml ps

# View logs
docker-compose -f docker-compose.devnet.yml logs -f overmind-brain
docker-compose -f docker-compose.devnet.yml logs -f overmind-trading
```

### **Real-time Monitoring**
```bash
# Monitor AI Brain logs
tail -f logs/overmind.log

# Monitor system metrics
watch -n 5 'curl -s http://localhost:8080/metrics | jq .'

# Monitor wallet balance
watch -n 10 'curl -s http://localhost:8000/wallets/status | jq .main_trading_wallet'
```

---

## 🛡️ **EMERGENCY PROCEDURES**

### **Emergency Stop Sequence**
1. **Immediate Stop** (via API):
   ```bash
   curl -X POST http://localhost:8000/control/emergency-stop
   ```

2. **System Shutdown** (via Kestra):
   - Open Kestra dashboard
   - Execute `emergency-stop-system` workflow
   - Select `force_stop: true` if needed

3. **Manual Shutdown** (if APIs fail):
   ```bash
   docker-compose -f docker-compose.devnet.yml down -v
   ```

### **System Recovery**
1. **Check System State**:
   ```bash
   docker ps --filter "name=overmind"
   ```

2. **Restart System** (via Kestra):
   - Execute `start-overmind-system` workflow
   - Monitor startup logs

3. **Verify Health**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8080/health
   ```

---

## 📈 **PERFORMANCE MONITORING**

### **Key Metrics to Watch**
- **AI Brain Status**: Should be "RUNNING"
- **Executor Status**: Should be "RUNNING" 
- **Error Rate**: Should be < 1%
- **Wallet Balance**: Monitor for unexpected changes
- **Transaction Success Rate**: Should be > 95%

### **Alert Thresholds**
- **High Error Rate**: > 5%
- **Low Wallet Balance**: < 1 SOL
- **System Unresponsive**: No heartbeat for > 30s
- **Failed Transactions**: > 3 consecutive failures

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues**

#### **AI Brain Not Responding**
```bash
# Check container status
docker logs overmind-brain-devnet

# Restart AI Brain
docker-compose -f docker-compose.devnet.yml restart overmind-brain
```

#### **Rust Executor Not Responding**
```bash
# Check container status
docker logs overmind-trading-devnet

# Restart Executor
docker-compose -f docker-compose.devnet.yml restart overmind-trading
```

#### **DragonflyDB Connection Issues**
```bash
# Test DragonflyDB
docker exec overmind-dragonfly-devnet redis-cli ping

# Restart DragonflyDB
docker-compose -f docker-compose.devnet.yml restart overmind-dragonfly
```

### **Log Locations**
- **AI Brain**: `docker logs overmind-brain-devnet`
- **Rust Executor**: `docker logs overmind-trading-devnet`
- **DragonflyDB**: `docker logs overmind-dragonfly-devnet`
- **Local Logs**: `logs/overmind.log`

---

## 🎯 **QUICK REFERENCE**

### **Essential URLs**
- **Kestra Dashboard**: http://localhost:8080
- **AI Brain API**: http://localhost:8000
- **Rust Executor API**: http://localhost:8080
- **Vector Database**: http://localhost:8001

### **Essential Commands**
```bash
# Start system
# Use Kestra workflow: start-overmind-system

# Check status
curl http://localhost:8000/status

# Emergency stop
curl -X POST http://localhost:8000/control/emergency-stop

# View logs
docker-compose -f docker-compose.devnet.yml logs -f

# Stop system
# Use Kestra workflow: emergency-stop-system
```

---

**🎖️ MISSION CONTROL READY FOR OPERATION**

Your THE OVERMIND PROTOCOL system is now equipped with comprehensive monitoring and control capabilities. Use this dashboard to maintain operational excellence and ensure system reliability.
