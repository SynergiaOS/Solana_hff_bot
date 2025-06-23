# 🎯 THE OVERMIND PROTOCOL - Production Deployment Instructions

**Target Server:** marcin@89.117.53.53  
**Mission:** Deploy and validate THE OVERMIND PROTOCOL in production environment  
**Duration:** 48-hour validation period in paper trading mode

---

## ⭐ **PHASE 1: SERVER PREPARATION**

### **Step 1: Connect to Production Server**

```bash
# Connect to your VDS server
ssh marcin@89.117.53.53
```

### **Step 2: System Prerequisites**

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git curl wget htop docker.io docker-compose

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker marcin

# Logout and login again for group changes to take effect
exit
ssh marcin@89.117.53.53
```

---

## ⭐ **PHASE 2: PROJECT DEPLOYMENT**

### **Step 3: Download and Execute Deployment**

```bash
# Create project directory
sudo mkdir -p /opt/overmind
sudo chown marcin:marcin /opt/overmind
cd /opt/overmind

# Clone THE OVERMIND PROTOCOL
git clone https://github.com/SynergiaOS/Solana_hff_bot.git .

# Make deployment script executable
chmod +x scripts/deploy_production.sh

# Copy production environment template
cp .env.production .env
```

### **Step 4: Configure Production Environment**

**CRITICAL:** Edit the `.env` file with your actual production values:

```bash
nano .env
```

**Required Configuration:**

1. **Trading Configuration:**
   ```env
   SNIPER_TRADING_MODE=paper  # MUST be 'paper' for validation
   SNIPER_MAX_POSITION_SIZE=1000.0
   SNIPER_MAX_DAILY_LOSS=500.0
   ```

2. **Solana Mainnet (Replace with your URLs):**
   ```env
   SOLANA_MAINNET_RPC_URL=https://your-helius-mainnet-url.com
   SOLANA_MAINNET_WSS_URL=wss://your-helius-mainnet-wss.com
   SOLANA_WALLET_PRIVATE_KEY=your_base58_private_key_here
   ```

3. **API Keys:**
   ```env
   OPENAI_API_KEY=sk-your-openai-key-here
   HELIUS_API_KEY=your-helius-api-key-here
   QUICKNODE_API_KEY=your-quicknode-api-key-here
   ```

4. **Security (Generate strong passwords):**
   ```env
   SNIPER_DB_PASSWORD=your_strong_postgres_password_here
   GRAFANA_ADMIN_PASSWORD=your_strong_grafana_password_here
   REDIS_PASSWORD=your_strong_redis_password_here
   ```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

### **Step 5: Execute Deployment**

```bash
# Run the automated deployment script
./scripts/deploy_production.sh
```

**Expected Output:**
- ✅ Pre-deployment checks passed
- ✅ Project setup completed
- ✅ Environment configuration validated
- ✅ Infrastructure preparation completed
- ✅ THE OVERMIND PROTOCOL deployment completed
- ✅ Deployment verification completed

---

## ⭐ **PHASE 3: VALIDATION MONITORING**

### **Step 6: Start 48-Hour Validation**

```bash
# Make monitoring script executable
chmod +x scripts/monitor_validation.sh

# Start validation timer
./scripts/monitor_validation.sh start

# Begin continuous monitoring
./scripts/monitor_validation.sh continuous
```

### **Step 7: Access Monitoring Dashboards**

Open in your browser:

- **Grafana Dashboard:** http://89.117.53.53:3001
  - Username: `admin`
  - Password: [your GRAFANA_ADMIN_PASSWORD from .env]

- **Trading System API:** http://89.117.53.53:8080/health
- **Prometheus Metrics:** http://89.117.53.53:9090

### **Step 8: Validation Checklist**

Monitor these metrics during 48-hour validation:

#### **System Health (Every 4 hours):**
- [ ] All containers running (check with `docker-compose ps`)
- [ ] No critical errors in logs
- [ ] API endpoints responding
- [ ] System resources within limits

#### **Trading Performance (Daily):**
- [ ] Signals being processed from mainnet
- [ ] AI decisions being made
- [ ] Paper trades being executed
- [ ] No failed transactions
- [ ] Risk limits being respected

#### **AI Brain Performance:**
- [ ] Vector memory functioning
- [ ] Decision confidence scores healthy (>0.7)
- [ ] Learning from market data
- [ ] No AI model errors

---

## ⭐ **PHASE 4: MONITORING COMMANDS**

### **Essential Commands:**

```bash
# Check system status
./scripts/monitor_validation.sh health

# View live logs
docker-compose logs -f

# Check specific service logs
docker-compose logs -f overmind-trading
docker-compose logs -f overmind-brain

# Check container status
docker-compose ps

# Restart if needed
docker-compose restart

# Emergency stop
docker-compose down
```

### **Health Check URLs:**

```bash
# Trading system health
curl http://localhost:8080/health

# Get trading metrics
curl http://localhost:8080/metrics

# Vector database health
curl http://localhost:8000/api/v1/heartbeat
```

---

## ⭐ **PHASE 5: VALIDATION SUCCESS CRITERIA**

### **After 48 Hours, Verify:**

1. **System Stability:**
   - [ ] 99%+ uptime achieved
   - [ ] No critical errors
   - [ ] All services operational

2. **Trading Performance:**
   - [ ] >100 signals processed
   - [ ] >50 AI decisions made
   - [ ] >10 paper trades executed
   - [ ] 0 failed transactions

3. **AI Quality:**
   - [ ] Decision confidence >0.7 average
   - [ ] Vector memory populated (>1000 memories)
   - [ ] Learning patterns visible

4. **Resource Usage:**
   - [ ] CPU usage <70% average
   - [ ] Memory usage <80%
   - [ ] Disk space sufficient

---

## ⭐ **PHASE 6: GO-LIVE PREPARATION**

### **If Validation Successful:**

1. **Update Trading Mode:**
   ```bash
   nano .env
   # Change: SNIPER_TRADING_MODE=live
   ```

2. **Restart System:**
   ```bash
   docker-compose restart
   ```

3. **Monitor Closely:**
   - Watch first live trades carefully
   - Verify real transaction execution
   - Monitor P&L and risk metrics

### **If Issues Found:**
- Document all issues
- Fix configuration problems
- Restart validation period
- Do NOT proceed to live trading

---

## 🚨 **EMERGENCY PROCEDURES**

### **Emergency Stop:**
```bash
# Immediate system shutdown
docker-compose down

# Or use monitoring script
./scripts/monitor_validation.sh stop
```

### **Rollback:**
```bash
# Stop system
docker-compose down

# Reset to previous state
git reset --hard HEAD~1

# Restart
docker-compose up -d
```

### **Support:**
- Check logs: `docker-compose logs`
- System status: `docker-compose ps`
- Resource usage: `htop`

---

## ✅ **SUCCESS CONFIRMATION**

**When validation is complete and successful:**

1. ✅ System ran stable for 48+ hours
2. ✅ All health checks passed
3. ✅ Trading metrics within expected ranges
4. ✅ AI performance satisfactory
5. ✅ No critical errors or failures

**Status:** 🎯 **READY FOR LIVE TRADING DEPLOYMENT**

---

**🎯 THE OVERMIND PROTOCOL Production Deployment Complete**

*Execute with precision. Monitor continuously. Trade with confidence.*
