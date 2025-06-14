# SNIPERCOR User Guidelines

## 🎯 Purpose

This document provides guidelines for operators and developers working with the SNIPERCOR high-frequency trading system. These guidelines ensure safe, efficient, and profitable operation of the trading system.

## 👥 Roles and Responsibilities

### System Operator (Captain)
- **Strategic Decisions**: Market selection, trading parameters, risk limits
- **System Monitoring**: Performance metrics, position management, P&L tracking
- **Risk Management**: Setting and adjusting risk parameters
- **Final Authority**: All trading decisions and system configuration

### AI Assistant (Co-Pilot)
- **Code Generation**: Implementing features, bug fixes, optimizations
- **Testing**: Writing and executing unit and integration tests
- **Analysis**: Performance analysis, log analysis, system diagnostics
- **Documentation**: Code documentation, technical specifications

## 🚀 Operational Procedures

### Daily Startup Checklist

1. **System Health Check**
```bash
# Check system resources
htop
df -h

# Verify network connectivity
ping -c 3 api.mainnet-beta.solana.com
ping -c 3 api.helius.xyz
```

2. **Configuration Verification**
```bash
# Verify environment variables
env | grep SNIPER_

# Check trading mode (MUST be paper for initial testing)
echo $SNIPER_TRADING_MODE
```

3. **Start System**
```bash
# Start in paper trading mode
SNIPER_TRADING_MODE=paper cargo run --profile contabo

# Monitor logs
tail -f logs/snipercor.log
```

### Pre-Live Trading Checklist

⚠️ **CRITICAL**: Complete ALL items before enabling live trading

- [ ] System running stable in paper trading for 24+ hours
- [ ] All risk limits properly configured and tested
- [ ] Emergency stop procedures tested and verified
- [ ] Sufficient account balance for trading + safety margin
- [ ] Network connectivity stable and redundant
- [ ] Monitoring systems active and alerting
- [ ] Backup systems tested and ready

### Live Trading Activation

```bash
# ONLY after completing pre-live checklist
SNIPER_TRADING_MODE=live cargo run --profile contabo
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

---

**⚡ Success in HFT requires discipline, preparation, and constant vigilance. Follow these guidelines religiously.**
