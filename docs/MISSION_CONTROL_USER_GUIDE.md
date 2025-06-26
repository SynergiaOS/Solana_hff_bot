# 🎛️ THE OVERMIND PROTOCOL - Mission Control User Guide

## 📋 Table of Contents
1. [Quick Start Guide](#quick-start-guide)
2. [Dashboard Overview](#dashboard-overview)
3. [Goal Management](#goal-management)
4. [Portfolio Tracking](#portfolio-tracking)
5. [Trading Activity Monitor](#trading-activity-monitor)
6. [System Health](#system-health)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start Guide

### Accessing Mission Control

**Local Development:**
```bash
# Start Mission Control dashboard
pixi run start-mission-control

# Access via browser
http://localhost:8501
```

**Production Environment:**
```bash
# Access via nginx proxy
https://your-domain.com/mission-control/

# Or direct access (if firewall allows)
http://your-server:8501
```

### First Time Setup

1. **Verify System Status**: Check that all components show green status
2. **Set Initial Goal**: Configure your first trading goal
3. **Monitor Portfolio**: Ensure portfolio data is updating
4. **Review Settings**: Configure auto-refresh preferences

---

## 📊 Dashboard Overview

### Navigation Sidebar

The Mission Control dashboard consists of four main sections:

- **🎯 Goal Management**: Set and modify trading goals
- **📊 Portfolio Tracking**: Monitor real-time portfolio performance
- **📋 Trading Activity**: View trading transactions and AI decisions
- **🟢 System Health**: Monitor system components and performance

### Auto-Refresh Controls

Located in the sidebar:
- **Refresh Interval**: 5, 10, 30, or 60 seconds
- **Enable/Disable**: Toggle auto-refresh on/off
- **Manual Refresh**: Force immediate data update
- **Last Update**: Shows time since last refresh

### Status Indicators

Header status bar shows:
- **System Status**: 🟢 Online / 🔴 Offline
- **Current Goal**: Active goal type and target
- **Progress**: Goal completion percentage
- **Last Update**: Time since last data refresh

---

## 🎯 Goal Management

### Setting Your First Goal

1. **Navigate to Goal Management** section
2. **Select Goal Type**:
   - **🎯 Reach Target Balance**: Focus on achieving specific SOL amount
   - **🛡️ Capital Preservation**: Protect existing capital with low-risk strategies
   - **🚀 Maximize Profit**: Aggressive growth strategies for maximum returns

3. **Set Target Amount**:
   - Enter target SOL amount (0.1-100 range)
   - USD equivalent is calculated automatically
   - Consider your risk tolerance and timeline

4. **Provide Change Reason**:
   - Select from predefined reasons or enter custom
   - Required for audit trail and compliance

5. **Review Impact Assessment**:
   - Check percentage change from current goal
   - Review risk level modifications
   - Confirm strategy profile changes

6. **Confirm Changes**:
   - Check all confirmation boxes
   - Click "Confirm Goal Change"
   - Monitor system adaptation

### Goal Types Explained

#### 🎯 Reach Target Balance
- **Purpose**: Achieve specific SOL target amount
- **Strategy**: Balanced approach with moderate risk
- **Profile Switching**: 
  - 0-25% progress: AGGRESSIVE_GROWTH
  - 25-100% progress: BALANCED_RISK
  - 100%+ progress: CAPITAL_PRESERVATION

#### 🛡️ Capital Preservation
- **Purpose**: Protect existing capital
- **Strategy**: Conservative, low-risk approach
- **Profile**: Primarily CAPITAL_PRESERVATION
- **Use Case**: Bear markets, high volatility periods

#### 🚀 Maximize Profit
- **Purpose**: Aggressive growth and profit maximization
- **Strategy**: High-risk, high-reward approach
- **Profile**: Primarily AGGRESSIVE_GROWTH
- **Use Case**: Bull markets, high confidence periods

### Modifying Existing Goals

**When to Modify Goals:**
- Market conditions change significantly
- Risk tolerance adjustments needed
- Portfolio milestones reached
- Strategy performance review

**Best Practices:**
- Review impact assessment carefully
- Consider current market conditions
- Document reason for change
- Monitor system adaptation post-change

### Goal Change Impact Assessment

The system provides detailed impact analysis:

**Percentage Change:**
- **Minor (<10%)**: Low impact, minimal strategy adjustment
- **Moderate (10-20%)**: Moderate impact, some strategy changes
- **Significant (>20%)**: High impact, major strategy overhaul

**Risk Level Changes:**
- **Increased**: More aggressive strategies enabled
- **Decreased**: More conservative approach adopted
- **Modified**: Risk parameters adjusted for new goal type

**Profile Change Likelihood:**
- **High**: Immediate profile switch expected
- **Medium**: Profile switch possible based on progress
- **Low**: Current profile likely maintained

---

## 📊 Portfolio Tracking

### Real-time Portfolio Overview

**Key Metrics Displayed:**
- **Total SOL**: Current portfolio value in SOL
- **Total USD**: USD equivalent at current prices
- **Goal Progress**: Percentage toward current goal
- **Active Profile**: Current strategy profile
- **Last Update**: Data freshness indicator

### Portfolio Value Chart

**24-Hour Trend Analysis:**
- **SOL Value Line**: Primary portfolio value tracking
- **USD Value Line**: Secondary axis for USD equivalent
- **Time Markers**: Hourly progression with current time indicator
- **Trend Analysis**: Visual identification of growth patterns

### Goal Progress Visualization

**Progress Bar Features:**
- **Color Coding**: 
  - Red (0-25%): Aggressive growth phase
  - Yellow (25-100%): Balanced risk phase
  - Green (100%+): Capital preservation phase
- **Target Line**: Visual goal target indicator
- **Overflow Support**: Shows progress beyond 100%

### Strategy Profile Timeline

**6-Hour Profile History:**
- **Profile Switches**: Visual timeline of strategy changes
- **Progress Correlation**: Profile changes mapped to portfolio progress
- **Reason Tracking**: Hover details show switch reasons
- **Performance Impact**: Visual correlation with portfolio performance

### Portfolio Composition

**Asset Allocation:**
- **Pie Chart**: Visual breakdown of holdings
- **Asset Types**: SOL, USDC, other tokens
- **Percentage Distribution**: Numerical allocation percentages

**Performance Metrics:**
- **24h/7d/30d Returns**: Short to medium-term performance
- **Volatility**: Risk measurement
- **Max Drawdown**: Worst-case loss scenario
- **Sharpe Ratio**: Risk-adjusted return metric

---

## 📋 Trading Activity Monitor

### Real-time Transaction Log

**Transaction Table Columns:**
- **Timestamp**: When transaction occurred
- **Strategy**: Which trading strategy executed
- **Action**: BUY, SELL, STOP_LOSS, TAKE_PROFIT
- **Amount**: Transaction size in SOL
- **Status**: COMPLETED, PENDING, FAILED, CANCELLED
- **P&L**: Profit/loss for completed transactions

**Filtering Options:**
- **Strategy Filter**: Focus on specific trading strategies
- **Action Filter**: Filter by transaction type
- **Status Filter**: Show only specific statuses
- **Time Range**: 1 hour, 6 hours, 24 hours, all time

### Strategy Performance Metrics

**Performance Table:**
- **Total Trades**: Number of completed transactions
- **Win Rate**: Percentage of profitable trades
- **Average Profit**: Mean profit per trade
- **Total P&L**: Cumulative profit/loss

**Performance Charts:**
- **Win Rate Comparison**: Bar chart across strategies
- **Total P&L Comparison**: Profit/loss by strategy
- **Color Coding**: Green for profitable, red for losses

### AI Decision Tracking

**Recent AI Decisions:**
- **Decision Type**: ENTRY_SIGNAL, EXIT_SIGNAL, RISK_ADJUSTMENT, etc.
- **Confidence Level**: HIGH, MEDIUM, LOW
- **Confidence Score**: Numerical confidence (0.0-1.0)
- **Details**: Specific decision information
- **Status**: EXECUTED, PENDING, REJECTED

**AI Performance Metrics:**
- **Total Decisions**: Count of AI decisions in timeframe
- **Execution Rate**: Percentage of decisions executed
- **Average Confidence**: Mean confidence score
- **High Confidence Count**: Number of high-confidence decisions

### Activity Summary

**Real-time Statistics:**
- **Last Hour**: Recent trading activity summary
- **Performance**: Overall system performance metrics
- **System Status**: Current operational status

---

## 🟢 System Health

### Component Status Monitoring

**Core Components:**
- **Portfolio Monitor**: Portfolio data collection and processing
- **Strategy Mapper**: Profile determination and switching logic
- **Goal Manager**: Goal storage and change management
- **Risk Manager**: Risk parameter calculation and enforcement

**Status Indicators:**
- **🟢 Operational**: Component functioning normally
- **🟡 Warning**: Component has minor issues
- **🔴 Offline**: Component not responding

### Infrastructure Services

**Service Health Grid:**
- **DragonflyDB**: Real-time data storage and messaging
- **TensorZero**: AI model optimization and inference
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Visualization and alerting
- **Nginx**: Reverse proxy and load balancing
- **Mission Control**: Dashboard application status

**Metrics Displayed:**
- **Status**: healthy, warning, critical
- **Uptime**: Service availability percentage
- **Response Time**: Average response latency
- **Additional Info**: Service-specific metrics

### Performance Monitoring

**System Performance:**
- **CPU Usage**: Processor utilization gauge
- **Memory Usage**: RAM consumption percentage
- **Disk Usage**: Storage utilization
- **Network I/O**: Data transfer rates

**Trading Performance:**
- **Component Latency**: Individual component response times
- **Total Latency**: End-to-end decision latency
- **Decision Frequency**: Decisions per second
- **Sub-50ms Validation**: Latency threshold compliance

### Alert Management

**Alert Types:**
- **✅ SUCCESS**: Positive system events
- **ℹ️ INFO**: Informational messages
- **⚠️ WARNING**: Issues requiring attention
- **❌ ERROR**: Critical problems requiring immediate action

**Alert Information:**
- **Component**: Which system component generated alert
- **Message**: Detailed alert description
- **Timestamp**: When alert was generated
- **Severity**: Alert priority level

---

## 💡 Best Practices

### Goal Management Best Practices

1. **Start Conservative**: Begin with moderate goals and adjust based on performance
2. **Monitor Market Conditions**: Adjust goals based on market volatility and trends
3. **Document Changes**: Always provide clear reasons for goal modifications
4. **Review Impact**: Carefully review impact assessments before confirming changes
5. **Gradual Adjustments**: Make incremental changes rather than dramatic shifts

### Portfolio Monitoring Best Practices

1. **Regular Review**: Check portfolio progress at least daily
2. **Trend Analysis**: Use 24-hour charts to identify patterns
3. **Profile Awareness**: Understand which strategy profile is active and why
4. **Performance Tracking**: Monitor key metrics like win rate and P&L
5. **Risk Management**: Watch for excessive drawdowns or volatility

### System Health Best Practices

1. **Daily Health Checks**: Review system status indicators daily
2. **Alert Response**: Address warnings promptly before they become critical
3. **Performance Monitoring**: Ensure latency stays below 50ms threshold
4. **Uptime Tracking**: Monitor service availability and investigate outages
5. **Capacity Planning**: Watch resource utilization trends

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Dashboard Not Loading
**Symptoms**: Blank page or connection errors
**Solutions**:
1. Check if Mission Control service is running
2. Verify port 8501 is accessible
3. Check nginx proxy configuration
4. Review browser console for JavaScript errors

#### Data Not Updating
**Symptoms**: Stale data, "Last Update: Never"
**Solutions**:
1. Check auto-refresh settings
2. Verify API connectivity to AI Brain
3. Check DragonflyDB connection
4. Review system health indicators

#### Goal Changes Not Taking Effect
**Symptoms**: Goal change appears successful but behavior unchanged
**Solutions**:
1. Verify goal was stored in DragonflyDB
2. Check Strategy Mapper is detecting changes
3. Review goal change audit trail
4. Restart Strategy Mapper if necessary

#### Performance Issues
**Symptoms**: Slow dashboard response, high latency
**Solutions**:
1. Check system resource utilization
2. Review component latency metrics
3. Verify network connectivity
4. Consider reducing auto-refresh frequency

### Getting Help

**Log Locations:**
- Mission Control: `logs/mission-control.log`
- AI Brain: `logs/ai-brain.log`
- System: `logs/overmind.log`

**Support Channels:**
- Check system health dashboard first
- Review troubleshooting guide
- Consult ADAPTIVE_CORTEX_GUIDE.md for technical details
- Contact development team for critical issues

**Emergency Procedures:**
- Use emergency stop if trading behavior is unexpected
- Revert to previous goal if new goal causes issues
- Restart individual components if health checks fail
- Full system restart as last resort

---

## 📚 Additional Resources

- **[ADAPTIVE_CORTEX_GUIDE.md](./ADAPTIVE_CORTEX_GUIDE.md)**: Technical documentation
- **[API Documentation](./ADAPTIVE_CORTEX_GUIDE.md#api-endpoints-documentation)**: API endpoint reference
- **[Configuration Guide](./ADAPTIVE_CORTEX_GUIDE.md#configuration-options)**: System configuration options
- **[Performance Tuning](./ADAPTIVE_CORTEX_GUIDE.md#performance-tuning)**: Optimization guidelines

For technical support or feature requests, consult the development team or refer to the comprehensive technical documentation.
