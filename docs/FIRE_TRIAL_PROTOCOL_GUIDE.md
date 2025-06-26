# 🔥 THE OVERMIND PROTOCOL - Fire Trial Protocol Guide

## 📋 **48-Hour Mainnet Paper Trading Validation**

**MISSION**: Execute THE OVERMIND PROTOCOL's ultimate test - a comprehensive 48-hour mainnet paper trading validation to gather statistical data on strategy effectiveness and system stability before potential live trading deployment.

**STATUS**: Ready for execution
**DURATION**: 48 hours continuous operation
**RISK LEVEL**: ZERO (Paper trading mode only)
**SUCCESS CRITERIA**: >5% theoretical return, >99% uptime, successful goal modification

---

## 🎯 **EXECUTION PHASES OVERVIEW**

### **Phase 1: Configuration & Launch** (50 minutes total)
- ⚙️ **1.1**: System Shutdown & Environment Preparation (15 min)
- 🌐 **1.2**: Mainnet Configuration Update (20 min)
- 🚀 **1.3**: Mainnet System Launch (15 min)

### **Phase 2: Verification & Setup** (70 minutes total)
- ✅ **2.1**: Service Health Verification (15 min)
- 📊 **2.2**: Mission Control Dashboard Validation (20 min)
- 💰 **2.3**: Mainnet Wallet & Balance Verification (15 min)
- 📋 **2.4**: Initial State Documentation (20 min)

### **Phase 3: 48-Hour Operation** (48 hours total)
- 🤖 **3.1**: Autonomous Trading Monitoring (Hours 0-12)
- 📈 **3.2**: Performance Analysis (Hours 12-24)
- 🎯 **3.3**: Dynamic Goal Testing (Hour 24 - 30 min)
- 🔄 **3.4**: Extended Operation Monitoring (Hours 24-48)

### **Phase 4: Analysis & Decision** (3 hours total)
- 📊 **4.1**: Data Export & Performance Analysis (45 min)
- 🧮 **4.2**: Profitability & Behavior Analysis (60 min)
- 🛡️ **4.3**: System Stability Assessment (45 min)
- 🎯 **4.4**: Final GO/NO-GO Decision (30 min)

---

## 🚀 **DETAILED EXECUTION PROCEDURES**

### **Phase 1.1: System Shutdown & Environment Preparation**

**COMMANDS TO EXECUTE:**
```bash
# SSH to production server
ssh marcin@89.117.53.53

# Navigate to project directory
cd overmind-protocol

# Save current system logs
mkdir -p fire-trial-backups/$(date +%Y%m%d_%H%M%S)
docker logs overmind-mission-control > fire-trial-backups/$(date +%Y%m%d_%H%M%S)/mission-control.log
docker logs sniperbot-dragonfly > fire-trial-backups/$(date +%Y%m%d_%H%M%S)/dragonfly.log

# Backup current configuration
cp .env fire-trial-backups/$(date +%Y%m%d_%H%M%S)/.env.backup

# Gracefully shutdown services
docker-compose -f infrastructure/compose/docker-compose.overmind.yml down
pkill -TERM overmind_hft_executor 2>/dev/null || echo "No executor running"

# Verify ports are free
ss -tlnp | grep -E ':(8080|8501|6379)' || echo "All ports available"
```

**ACCEPTANCE CRITERIA:**
- ✅ All Docker containers stopped gracefully
- ✅ System logs saved to backup directory
- ✅ Configuration backup created
- ✅ No processes running on ports 8080, 8501, 6379

### **Phase 1.2: Mainnet Configuration Update**

**CONFIGURATION CHANGES:**
```bash
# Edit .env file for mainnet
nano .env

# Required changes:
PAPER_TRADING_MODE=true                    # CRITICAL: Must remain true
SOLANA_MAINNET_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_MAINNET_WSS_URL=wss://api.mainnet-beta.solana.com
HELIUS_MAINNET_URL=https://mainnet.helius-rpc.com/?api-key=YOUR_KEY
QUICKNODE_MAINNET_URL=https://your-mainnet-endpoint.quiknode.pro/YOUR_KEY
SOLANA_WALLET_PRIVATE_KEY=your_mainnet_wallet_private_key
```

**VALIDATION COMMANDS:**
```bash
# Test mainnet RPC connectivity
curl -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}' \
  https://api.mainnet-beta.solana.com

# Verify wallet balance (should show mainnet balance)
solana balance --url mainnet-beta YOUR_WALLET_ADDRESS
```

**ACCEPTANCE CRITERIA:**
- ✅ PAPER_TRADING_MODE=true confirmed
- ✅ Mainnet RPC/WSS endpoints responding
- ✅ Wallet balance visible on mainnet
- ✅ API connectivity tests pass

### **Phase 1.3: Mainnet System Launch**

**LAUNCH COMMANDS:**
```bash
# Start Docker services
docker-compose -f infrastructure/compose/docker-compose.overmind.yml up -d

# Wait for services to initialize
sleep 30

# Start OVERMIND main application
RUST_LOG=info cargo run --profile contabo &

# Monitor startup logs
tail -f logs/overmind.log
```

**HEALTH CHECK COMMANDS:**
```bash
# Verify all services
docker ps | grep -E "(mission-control|dragonfly|prometheus|grafana)"

# Test health endpoints
curl http://localhost:8501/health
curl http://localhost:8080/health
echo "PING" | nc localhost 6379
```

**ACCEPTANCE CRITERIA:**
- ✅ All Docker services running and healthy
- ✅ OVERMIND application started successfully
- ✅ Health checks passing
- ✅ No error logs in startup sequence

---

## 📊 **MONITORING CHECKLIST**

### **Continuous Monitoring (Every 2 Hours)**

**System Health:**
```bash
# Check service status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Monitor resource usage
docker stats --no-stream

# Check application logs
tail -20 logs/overmind.log | grep -E "(ERROR|WARN|TRADE|POSITION)"
```

**Trading Activity:**
- 📊 Access Mission Control: http://89.117.53.53:8501
- 📈 Check Grafana dashboards: http://89.117.53.53:3000
- 💰 Verify paper trading mode active
- 📋 Monitor transaction log for new positions

**Performance Metrics:**
- 🔍 CPU usage <80%
- 💾 Memory usage <90%
- 🌐 Network connectivity stable
- ⚡ Response times <50ms

### **Critical Alerts Setup**

**Automated Monitoring Script:**
```bash
#!/bin/bash
# fire-trial-monitor.sh
while true; do
    # Check if OVERMIND is running
    if ! pgrep -f "overmind_hft_executor" > /dev/null; then
        echo "ALERT: OVERMIND process not running!" | tee -a fire-trial-alerts.log
    fi
    
    # Check Docker services
    if [ $(docker ps | grep -c "Up") -lt 4 ]; then
        echo "ALERT: Docker services down!" | tee -a fire-trial-alerts.log
    fi
    
    # Check paper trading mode
    if ! grep -q "PAPER_TRADING_MODE=true" .env; then
        echo "CRITICAL: Paper trading mode disabled!" | tee -a fire-trial-alerts.log
    fi
    
    sleep 300  # Check every 5 minutes
done
```

---

## 📈 **SUCCESS METRICS & THRESHOLDS**

### **Performance Targets**

**Profitability Metrics:**
- 🎯 **Target**: >5% theoretical return over 48 hours
- 📊 **Measurement**: Total P&L from all paper trades
- 🔍 **Analysis**: Win rate, average trade size, strategy distribution

**System Stability Metrics:**
- 🕐 **Uptime**: >99.9% (max 7 minutes downtime)
- 💾 **Memory**: Stable usage, no leaks
- ⚡ **Performance**: <50ms API response times
- 🚫 **Errors**: <1% error rate

**Functional Metrics:**
- 🎯 **Goal Modification**: Successful zero-downtime transition
- 🔄 **Profile Switching**: Adaptive Cortex responds correctly
- 📊 **Data Integrity**: All trades logged accurately
- 🛡️ **Risk Management**: Stop losses and take profits execute

### **GO/NO-GO Decision Criteria**

**GO Criteria (All must be met):**
- ✅ Positive theoretical P&L (>5% return)
- ✅ System uptime >99%
- ✅ Successful goal modification test
- ✅ Consistent strategy execution
- ✅ No critical system failures
- ✅ Risk management functioning

**NO-GO Criteria (Any triggers NO-GO):**
- ❌ Negative or <2% theoretical return
- ❌ System uptime <95%
- ❌ Goal modification failure
- ❌ Critical system failures
- ❌ Risk management failures
- ❌ Data integrity issues

---

## 🛡️ **SAFETY PROTOCOLS**

### **Emergency Procedures**

**Immediate System Halt:**
```bash
# Emergency stop all trading
export OVERMIND_EMERGENCY_STOP=true
pkill -TERM overmind_hft_executor

# Stop all services
docker-compose -f infrastructure/compose/docker-compose.overmind.yml down
```

**Rollback to Devnet:**
```bash
# Restore devnet configuration
cp fire-trial-backups/TIMESTAMP/.env.backup .env

# Restart on devnet
docker-compose -f infrastructure/compose/docker-compose.overmind.yml up -d
cargo run --profile contabo &
```

### **Paper Trading Verification**

**Critical Safety Checks:**
```bash
# Verify paper trading mode every hour
grep "PAPER_TRADING_MODE=true" .env || echo "CRITICAL: Check trading mode!"

# Monitor for any real transactions (should be ZERO)
grep -i "real.*transaction" logs/overmind.log || echo "No real transactions (good)"

# Check wallet balance hasn't changed
solana balance --url mainnet-beta YOUR_WALLET_ADDRESS
```

---

## 📊 **REPORTING TEMPLATE**

### **Hourly Status Report**
```
HOUR: XX/48
STATUS: [OPERATIONAL/WARNING/CRITICAL]
UPTIME: XX.X%
POSITIONS: XX open, XX closed
P&L: +/-X.XX SOL (+/-$XXX)
ALERTS: [None/List any issues]
NEXT CHECK: [Time]
```

### **Final Report Template**
```
🔥 FIRE TRIAL PROTOCOL - FINAL REPORT
=====================================
DURATION: 48 hours
TOTAL UPTIME: XX.X%
TOTAL TRADES: XXX
WIN RATE: XX.X%
TOTAL P&L: +/-X.XX SOL (+/-$XXXX)
SHARPE RATIO: X.XX
MAX DRAWDOWN: X.XX%

DECISION: [GO/NO-GO]
REASONING: [Detailed analysis]
NEXT STEPS: [Recommendations]
```

---

## 🎯 **EXECUTION TIMELINE**

**Day 1:**
- 00:00 - Phase 1: Configuration & Launch
- 01:30 - Phase 2: Verification & Setup
- 03:00 - Phase 3.1: Begin 48-hour monitoring
- 15:00 - 12-hour checkpoint
- 24:00 - Phase 3.3: Dynamic goal testing

**Day 2:**
- 03:00 - 24-hour checkpoint
- 15:00 - 36-hour checkpoint
- 24:00 - Phase 3.4 complete

**Day 3:**
- 03:00 - Phase 4: Analysis begins
- 06:00 - Final GO/NO-GO decision

**🎊 THE OVERMIND PROTOCOL Fire Trial Protocol is ready for execution!**
