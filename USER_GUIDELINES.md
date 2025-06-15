# 🎯 USER GUIDELINES - THE OVERMIND PROTOCOL

## 📋 **OVERVIEW**

This document provides comprehensive guidelines for operators and developers working with THE OVERMIND PROTOCOL - the ultimate 5-layer autonomous AI trading system. These guidelines ensure safe, efficient, and profitable operation of the AI-enhanced trading system.

**Motto:** "Czytaj → Planuj → Testuj → Implementuj → Weryfikuj"
**Status:** PRODUCTION GUIDELINES
**Use Case:** Safe Operation of THE OVERMIND PROTOCOL

## 👥 **ROLES AND RESPONSIBILITIES**

### **System Operator (Captain) - THE OVERMIND COMMANDER**
- **Strategic Decisions**: AI model selection, trading parameters, risk limits
- **System Monitoring**: 5-layer architecture performance, AI decision quality
- **Risk Management**: AI safety parameters, position limits, emergency stops
- **Final Authority**: All AI decisions validation and system configuration
- **AI Oversight**: Monitor AI Brain performance and vector memory health

### **AI Assistant (Co-Pilot) - AUGMENT AGENT**
- **Code Generation**: THE OVERMIND PROTOCOL implementation, TensorZero integration
- **Testing**: Comprehensive testing of AI-enhanced trading modules
- **Analysis**: AI performance analysis, vector memory optimization
- **Documentation**: THE OVERMIND PROTOCOL documentation, AI integration guides
- **MANDATORY**: Always read documentation and memory before any task

## 🚀 **THE OVERMIND PROTOCOL OPERATIONAL PROCEDURES**

### **📚 MANDATORY PRE-TASK CHECKLIST**

#### **BEFORE ANY TASK - ALWAYS:**

1. **Read Documentation**
```bash
# ZAWSZE zacznij od przeczytania odpowiedniej dokumentacji
cat library/README.md                    # Przegląd bibliotek
cat library/ai/overmind-protocol.md      # Główna architektura
cat RULES.md                             # Zasady rozwoju
```

2. **Check Memory & Context**
```bash
# Sprawdź co system już wie
- THE OVERMIND PROTOCOL architecture (5 warstw)
- Existing codebase structure
- Previous decisions and patterns
- Known issues and solutions
```

3. **Formulate Precise Tasks**
```
❌ ZŁE: "napraw bug"
✅ DOBRE: "W pliku src/modules/executor.rs, w funkcji send_transaction,
          dodaj obsługę RpcError::TransactionError i implementuj retry logic
          3 razy z exponential backoff"
```

### **Daily Startup Checklist - THE OVERMIND PROTOCOL**

1. **5-Layer System Health Check**
```bash
# Warstwa 1: Infrastructure
docker-compose ps
docker stats

# Warstwa 2: Intelligence
ping -c 3 api.mainnet-beta.solana.com
curl -s http://localhost:8000/health  # Chroma Vector DB

# Warstwa 3: AI Brain
curl -s http://localhost:3000/health  # TensorZero
python -c "import ai_hedge_fund; print('AI Brain OK')"

# Warstwa 4: Executor
cargo check
curl -s http://localhost:8080/health  # Rust HFT

# Warstwa 5: Control
curl -s http://localhost:9090/health  # Prometheus
```

2. **Configuration Verification**
```bash
# Verify OVERMIND environment variables
env | grep OVERMIND_
env | grep SNIPER_

# Check trading mode (MUST be paper for initial testing)
echo $SNIPER_TRADING_MODE
echo $OVERMIND_AI_MODE
```

3. **Start THE OVERMIND PROTOCOL**
```bash
# Start in paper trading mode with AI
SNIPER_TRADING_MODE=paper OVERMIND_AI_MODE=enabled cargo run --profile contabo

# Monitor OVERMIND logs
tail -f logs/overmind.log
tail -f logs/ai-brain.log
```

### **Pre-Live Trading Checklist - THE OVERMIND PROTOCOL**

⚠️ **CRITICAL**: Complete ALL items before enabling live AI trading

- [ ] THE OVERMIND PROTOCOL running stable in paper trading for 48+ hours
- [ ] All 5 layers functioning correctly and monitored
- [ ] AI Brain making consistent profitable decisions
- [ ] Vector memory populated with sufficient historical data
- [ ] TensorZero optimization showing performance gains
- [ ] All risk limits properly configured and AI-tested
- [ ] Emergency stop procedures tested for AI scenarios
- [ ] Sufficient account balance for trading + safety margin
- [ ] Network connectivity stable and redundant
- [ ] All monitoring systems active and alerting
- [ ] Backup systems tested and ready
- [ ] AI model performance validated on devnet

### **Live Trading Activation - THE OVERMIND PROTOCOL**

```bash
# ONLY after completing pre-live checklist
SNIPER_TRADING_MODE=live OVERMIND_AI_MODE=enabled cargo run --profile contabo

# Monitor AI decision quality
tail -f logs/ai-decisions.log
```

## 📊 Monitoring and Alerting

### Key Metrics to Monitor

1. **Performance Metrics**
   - Order-to-execution latency (<50ms target)
   - Market data ingestion rate
   - System CPU and memory usage
   - Network latency to exchanges

2. **Trading Metrics**
   - Daily P&L
   - Position sizes and exposure
   - Win rate and average trade size
   - Risk-adjusted returns

3. **System Health**
   - Error rates and types
   - System uptime
   - Database performance
   - API rate limit usage

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Daily Loss | 50% of limit | 80% of limit |
| Position Size | 80% of limit | 95% of limit |
| Latency | >75ms | >100ms |
| Error Rate | >1% | >5% |
| Memory Usage | >80% | >90% |

## 🛡️ Risk Management

### Position Sizing Rules

1. **Maximum Position Size**: Never exceed configured `SNIPER_MAX_POSITION_SIZE`
2. **Diversification**: No more than 20% of capital in single asset
3. **Correlation Limits**: Monitor correlated positions
4. **Leverage Limits**: Maximum 2:1 leverage on any position

### Loss Management

1. **Daily Loss Limit**: Hard stop at `SNIPER_MAX_DAILY_LOSS`
2. **Drawdown Monitoring**: Alert at 10% portfolio drawdown
3. **Position Stops**: Individual position stop-losses
4. **Emergency Procedures**: Immediate position closure protocols

### Risk Monitoring Commands

```bash
# Check current positions
curl http://localhost:8080/positions

# Check daily P&L
curl http://localhost:8080/metrics | grep daily_pnl

# Emergency stop (if needed)
curl -X POST http://localhost:8080/emergency_stop
```

## 🔧 Troubleshooting

### Common Issues and Solutions

1. **High Latency**
   - Check network connectivity
   - Verify RPC endpoint performance
   - Monitor system resource usage
   - Consider switching to backup RPC

2. **Failed Transactions**
   - Check Solana network status
   - Verify account balance and SOL for fees
   - Review transaction parameters
   - Check for network congestion

3. **Memory Issues**
   - Monitor for memory leaks
   - Check channel buffer sizes
   - Review data retention policies
   - Restart system if necessary

4. **API Rate Limits**
   - Monitor API usage rates
   - Implement request throttling
   - Use multiple API keys if available
   - Switch to backup providers

### Emergency Procedures

#### Immediate Trading Halt
```bash
# Method 1: API endpoint
curl -X POST http://localhost:8080/emergency_stop

# Method 2: Environment variable
export SNIPER_EMERGENCY_STOP=true

# Method 3: Process termination
pkill -TERM snipercor
```

#### System Recovery
1. **Assess Situation**: Review logs and system state
2. **Fix Issues**: Address root cause of problems
3. **Test in Paper Mode**: Verify fixes in simulation
4. **Gradual Restart**: Resume with reduced position sizes
5. **Monitor Closely**: Increased monitoring for 24 hours

## 📈 Performance Optimization

### System Tuning

1. **CPU Optimization**
   - Set CPU governor to performance mode
   - Pin critical processes to specific cores
   - Disable unnecessary system services

2. **Memory Optimization**
   - Increase system memory limits
   - Configure swap appropriately
   - Monitor for memory fragmentation

3. **Network Optimization**
   - Use dedicated network interfaces
   - Optimize TCP settings for low latency
   - Consider network acceleration hardware

### Application Tuning

1. **Rust Optimizations**
   - Use profile-guided optimization (PGO)
   - Enable link-time optimization (LTO)
   - Optimize for target CPU architecture

2. **Database Tuning**
   - Optimize PostgreSQL configuration
   - Use appropriate indexes
   - Monitor query performance

## 📚 Best Practices

### Development Workflow

1. **Feature Development**
   - Create feature branch
   - Implement with comprehensive tests
   - Test in paper trading environment
   - Code review and approval
   - Deploy to production

2. **Testing Strategy**
   - Unit tests for all components
   - Integration tests for workflows
   - Performance tests for critical paths
   - Paper trading validation

3. **Deployment Process**
   - Blue-green deployment strategy
   - Gradual rollout with monitoring
   - Rollback procedures ready
   - Post-deployment validation

### Operational Excellence

1. **Documentation**
   - Keep runbooks updated
   - Document all configuration changes
   - Maintain incident post-mortems
   - Update procedures regularly

2. **Monitoring**
   - Comprehensive metrics collection
   - Proactive alerting
   - Regular system health checks
   - Performance trend analysis

3. **Security**
   - Regular security audits
   - Access control reviews
   - Secret rotation procedures
   - Incident response plans

## 🆘 Support and Escalation

### Support Levels

1. **Level 1**: Operational issues, configuration problems
2. **Level 2**: System failures, performance degradation
3. **Level 3**: Critical trading issues, financial impact

### Escalation Procedures

1. **Immediate**: Trading halts, system failures
2. **Urgent**: Performance degradation, risk limit breaches
3. **Normal**: Feature requests, optimization opportunities

### Contact Information

- **Operations Team**: ops@company.com
- **Development Team**: dev@company.com
- **Emergency Hotline**: +1-XXX-XXX-XXXX

## 🎯 **SYSTEMATIC TASK EXECUTION TEMPLATE**

### **Template for Every Task:**

#### **STEP 1: Information Gathering**
```
📚 DOCUMENTATION READ:
- [ ] Relevant library/*.md files
- [ ] Existing code patterns
- [ ] Architecture decisions

🧠 MEMORY CHECK:
- [ ] Previous implementations
- [ ] Known patterns
- [ ] User preferences

🌐 RESEARCH (if needed):
- [ ] Latest solutions
- [ ] Best practices
- [ ] Security considerations
```

#### **STEP 2: Planning**
```
🎯 TASK BREAKDOWN:
1. [ ] Specific goal definition
2. [ ] File-by-file change list
3. [ ] Dependency analysis
4. [ ] Risk assessment

📋 IMPLEMENTATION PLAN:
1. [ ] Module A: [specific changes]
2. [ ] Module B: [specific changes]
3. [ ] Tests: [test strategy]
4. [ ] Integration: [integration points]
```

#### **STEP 3: Implementation (Rozdział po Rozdziale)**
```
🔧 DEVELOPMENT:
- [ ] Implement Module A
- [ ] Write tests for Module A
- [ ] Verify Module A works
- [ ] Get user approval ✅
- [ ] Proceed to Module B

🧪 TESTING:
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Performance acceptable
- [ ] No regressions
```

#### **STEP 4: Verification**
```
✅ FINAL CHECKS:
- [ ] All tests pass
- [ ] Code follows patterns
- [ ] Documentation updated
- [ ] User approval received
```

## 🎯 **PRZYKŁAD DOBREGO PROMPTA:**

```
Bazując na wiedzy z RULES.md i library/ai/overmind-protocol.md, wykonaj następujące zadanie:

W pliku src/main.rs, zaktualizuj system do THE OVERMIND PROTOCOL:

1. Zmień komentarze z "SNIPERCOR" na "THE OVERMIND PROTOCOL"
2. Dodaj ai_connector module import
3. Dodaj kanał komunikacji z AI Brain
4. Zintegruj TensorZero gateway
5. Dodaj vector memory connector

Po wprowadzeniu zmian, uruchom 'cargo test --workspace' żeby potwierdzić
że wszystkie testy przechodzą. Przedstaw mi finalny diff do akceptacji.
```

## 🎯 **FINAL CHECKLIST**

### **Before Marking Task Complete:**
- [ ] Information gathering completed
- [ ] Detailed plan approved
- [ ] Implementation tested thoroughly
- [ ] All tests passing
- [ ] Performance verified
- [ ] Security reviewed
- [ ] Documentation updated
- [ ] User final approval received

---

**🎯 REMEMBER: "Czytaj → Planuj → Testuj → Implementuj → Weryfikuj"**

**🧠 ALWAYS start with documentation and memory**
**🤝 NEVER proceed without user approval at key decision points**
**🛡️ SAFETY FIRST in critical trading modules**

**⚡ Success in THE OVERMIND PROTOCOL requires discipline, preparation, AI oversight, and constant vigilance. Follow these guidelines religiously.**
