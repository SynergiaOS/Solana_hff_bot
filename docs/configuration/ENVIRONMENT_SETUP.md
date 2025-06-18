# THE OVERMIND PROTOCOL - Environment Setup Guide

**Status:** 🔧 CONFIGURATION READY  
**Date:** 2025-06-17  
**Purpose:** Complete environment configuration for THE OVERMIND PROTOCOL  

## 🎯 Overview

This guide covers the complete environment setup for THE OVERMIND PROTOCOL, including all necessary configuration files, API keys, and system parameters.

## 📁 Configuration Files Created

### **Main Configuration Files:**
- ✅ `.env` - Main environment configuration
- ✅ `.env.example` - Template for new deployments
- ✅ `brain/.env` - AI Brain specific configuration
- ✅ `scripts/setup_environment.sh` - Automated setup script

## 🚀 Quick Setup

### **Option 1: Automated Setup (Recommended)**
```bash
# Run the interactive setup script
./scripts/setup_environment.sh
```

### **Option 2: Manual Setup**
```bash
# Copy template and edit manually
cp .env.example .env
nano .env

# Copy brain configuration
cp brain/.env.example brain/.env
nano brain/.env
```

## 🔑 Required API Keys

### **Essential Keys:**
1. **OpenAI API Key** (REQUIRED)
   - Get from: https://platform.openai.com/account/api-keys
   - Format: `sk-...` (starts with sk-)
   - Used for: AI Brain decision making

2. **Solana RPC Endpoints** (RECOMMENDED)
   - QuickNode Premium endpoints provided
   - Alternative: Use public endpoints (slower)

### **Optional Keys:**
- Mistral API Key (alternative AI model)
- Google API Key (additional AI capabilities)
- Perplexity API Key (research enhancement)

## ⚙️ Configuration Sections

### **🧠 AI Brain Configuration**
```bash
# Core AI Settings
OPENAI_API_KEY=sk-your-key-here
DECISION_CONFIDENCE_THRESHOLD=0.6
MAX_PORTFOLIO_RISK_PERCENTAGE=2.0

# Vector Memory
CHROMA_COLLECTION_NAME=overmind_memory
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Performance
MAX_CONCURRENT_ANALYSES=5
ANALYSIS_TIMEOUT_SECONDS=30
```

### **🐉 DragonflyDB Configuration**
```bash
# Connection Settings
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
DRAGONFLY_PASSWORD=

# Message Queues
OVERMIND_MARKET_EVENTS_QUEUE=overmind:market_events
OVERMIND_TRADING_COMMANDS_QUEUE=overmind:trading_commands
OVERMIND_EXECUTION_RESULTS_QUEUE=overmind:execution_results
```

### **⚡ Rust Executor Configuration**
```bash
# Trading Mode (IMPORTANT!)
SNIPER_TRADING_MODE=paper  # Start with paper trading!
SNIPER_ENVIRONMENT=devnet  # Start with devnet!

# Risk Limits
SNIPER_MAX_POSITION_SIZE=0.1
SNIPER_MAX_DAILY_LOSS=1.0
SNIPER_MAX_SLIPPAGE_BPS=100
```

### **🌐 Network Configuration**
```bash
# Devnet (for testing)
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WS_URL=wss://api.devnet.solana.com

# Mainnet (for production)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WS_URL=wss://api.mainnet-beta.solana.com

# QuickNode Premium
QUICKNODE_RPC_URL=https://your-endpoint.quiknode.pro/your-key
QUICKNODE_WS_URL=wss://your-endpoint.quiknode.pro/your-key
```

## 🔒 Security Best Practices

### **API Key Security:**
- ✅ Never commit `.env` files to version control
- ✅ Use different keys for development/production
- ✅ Rotate keys regularly
- ✅ Monitor API usage and costs

### **Wallet Security:**
```bash
# Create secure wallets
mkdir -p wallets
solana-keygen new --outfile wallets/trading-wallet.json
solana-keygen new --outfile wallets/backup-wallet.json

# Set proper permissions
chmod 600 wallets/*.json
```

### **Environment Isolation:**
```bash
# Development
ENVIRONMENT=development
SNIPER_TRADING_MODE=paper
DEBUG_MODE=true

# Production
ENVIRONMENT=production
SNIPER_TRADING_MODE=live
DEBUG_MODE=false
```

## 🎯 Environment Types

### **Development Environment:**
```bash
NODE_ENV=development
SNIPER_TRADING_MODE=paper
SNIPER_ENVIRONMENT=devnet
DEBUG_MODE=true
LOG_LEVEL=DEBUG
ENABLE_TEST_MODE=true
```

### **Production Environment:**
```bash
NODE_ENV=production
SNIPER_TRADING_MODE=live
SNIPER_ENVIRONMENT=mainnet
DEBUG_MODE=false
LOG_LEVEL=INFO
ENABLE_TEST_MODE=false
```

### **Testing Environment:**
```bash
NODE_ENV=testing
SNIPER_TRADING_MODE=mock
SNIPER_ENVIRONMENT=devnet
DEBUG_MODE=true
LOG_LEVEL=DEBUG
MOCK_TRADING_ENABLED=true
```

## 📊 Monitoring Configuration

### **Logging Settings:**
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=./logs/overmind.log
ENABLE_FILE_LOGGING=true
ENABLE_CONSOLE_LOGGING=true
```

### **Alerts Configuration:**
```bash
ENABLE_ALERTS=true
ALERT_EMAIL=your-email@example.com
ALERT_WEBHOOK_URL=https://hooks.slack.com/your-webhook

# Alert Thresholds
ALERT_DAILY_LOSS_THRESHOLD=50.0
ALERT_ERROR_RATE_THRESHOLD=5.0
ALERT_LATENCY_THRESHOLD_MS=1000
```

### **Performance Monitoring:**
```bash
PROMETHEUS_HOST=localhost
PROMETHEUS_PORT=9090
GRAFANA_HOST=localhost
GRAFANA_PORT=3000
ENABLE_PERFORMANCE_METRICS=true
```

## 🧪 Testing Configuration

### **Test Mode Settings:**
```bash
ENABLE_TEST_MODE=true
TEST_WALLET_PATH=./wallets/test-wallet.json
MOCK_TRADING_ENABLED=true
SIMULATION_MODE=true
```

### **Validation Settings:**
```bash
ENABLE_INPUT_VALIDATION=true
MAX_REQUEST_SIZE_MB=10
REQUEST_TIMEOUT_SECONDS=30
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=100
```

## 🚀 Deployment Checklist

### **Pre-Deployment:**
- [ ] All API keys configured and tested
- [ ] Wallets created and funded
- [ ] Network endpoints verified
- [ ] Risk limits set appropriately
- [ ] Monitoring configured
- [ ] Backup procedures tested

### **Development Deployment:**
```bash
# 1. Setup environment
./scripts/setup_environment.sh

# 2. Verify configuration
./scripts/verify_ai_brain_deployment.sh

# 3. Test communication
./scripts/test_communication.sh

# 4. Run end-to-end test
./scripts/test_e2e_devnet.sh
```

### **Production Deployment:**
```bash
# 1. Switch to production config
export NODE_ENV=production
export SNIPER_ENVIRONMENT=mainnet

# 2. Verify all systems
./scripts/verify_ai_brain_deployment.sh

# 3. Start with paper trading
export SNIPER_TRADING_MODE=paper

# 4. Monitor for 24 hours before live trading
./scripts/start_longterm_validation.sh --background
```

## 🔧 Troubleshooting

### **Common Issues:**

#### **OpenAI API Key Issues:**
```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Expected: List of available models
```

#### **DragonflyDB Connection Issues:**
```bash
# Test connection
redis-cli -h $DRAGONFLY_HOST -p $DRAGONFLY_PORT ping

# Expected: PONG
```

#### **Solana RPC Issues:**
```bash
# Test RPC endpoint
curl -X POST $SOLANA_RPC_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'

# Expected: {"result":"ok"}
```

### **Configuration Validation:**
```bash
# Validate .env file
./scripts/validate_configuration.sh

# Check all services
./scripts/health_check.sh

# Test complete pipeline
./scripts/test_communication.sh
```

## 📚 Additional Resources

### **Documentation:**
- [AI Brain Configuration Guide](./AI_BRAIN_CONFIGURATION.md)
- [Security Best Practices](./SECURITY_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

### **Scripts:**
- `scripts/setup_environment.sh` - Interactive setup
- `scripts/validate_configuration.sh` - Configuration validation
- `scripts/health_check.sh` - System health check
- `scripts/backup_configuration.sh` - Configuration backup

---

## 🎯 Quick Start Commands

```bash
# 1. Setup environment
./scripts/setup_environment.sh

# 2. Create wallets
mkdir -p wallets
solana-keygen new --outfile wallets/trading-wallet.json

# 3. Start services
docker run -d -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly
cd brain && python -m overmind_brain.main server &
cargo run --release &

# 4. Test system
./scripts/test_communication.sh
```

**🔧 THE OVERMIND PROTOCOL - ENVIRONMENT CONFIGURATION COMPLETE! 🚀**
