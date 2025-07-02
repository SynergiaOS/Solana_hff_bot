# 🧠 THE OVERMIND PROTOCOL - Dashboard User Guide

Complete guide for using the comprehensive monitoring dashboard.

## 🎯 Quick Start Guide

### 1. **Launch Dashboard**
```bash
cd dashboard
./launch.sh
```

### 2. **Access Dashboard**
Open your browser and navigate to: `http://localhost:8501`

### 3. **Navigate Tabs**
Use the tab navigation to explore different monitoring sections.

## 📊 Dashboard Sections

### **Overview Tab** 📊
**Purpose**: High-level system monitoring and portfolio overview

**Key Metrics**:
- System Status (Brain, Executor, Protection Layer)
- Portfolio Value and 24h Performance
- Active Strategies Count
- Risk Level Assessment

**Charts**:
- Portfolio Value Timeline (24h)
- Real-time Performance Indicators

**Use Cases**:
- Quick system health check
- Portfolio performance monitoring
- Daily trading overview

---

### **Strategy Heat Map Tab** 🔥
**Purpose**: Strategy performance analysis across market conditions

**Key Features**:
- Strategy vs Market Regime Performance Matrix
- Real-time Strategy Status Table
- Confidence Level Tracking
- Performance Color Coding

**Interpretation**:
- **Green**: High performance (>0.8)
- **Yellow**: Moderate performance (0.5-0.8)
- **Red**: Low performance (<0.5)

**Use Cases**:
- Strategy optimization
- Market regime analysis
- Performance comparison

---

### **Risk Management Tab** 🛡️
**Purpose**: Comprehensive risk monitoring and protection status

**Key Sections**:

1. **Protection Overview**:
   - Hedging Layer Status
   - MEV Protection Metrics
   - Risk Score Monitoring
   - Auto-rebalancing Status

2. **MEV Risk Timeline**:
   - Real-time MEV risk scores
   - Risk threshold indicators
   - Historical risk patterns

3. **Active Hedges Table**:
   - Current hedge positions
   - Hedge effectiveness
   - Rebalancing status

**Alert Levels**:
- **Green**: Low risk (<0.3)
- **Yellow**: Moderate risk (0.3-0.6)
- **Orange**: High risk (0.6-0.8)
- **Red**: Critical risk (>0.8)

---

### **Correlation Analysis Tab** 📊
**Purpose**: Asset correlation monitoring and hedge opportunity identification

**Key Features**:

1. **Correlation Matrix Heat Map**:
   - 30-day rolling correlations
   - Color-coded correlation strength
   - Asset relationship visualization

2. **Correlation Clusters**:
   - High correlation groups (>0.7)
   - Risk concentration identification
   - Diversification opportunities

3. **Hedge Opportunities**:
   - Natural hedge pairs
   - Counter-trend opportunities
   - Hedge coverage metrics

**Correlation Interpretation**:
- **Red**: Strong negative correlation
- **White**: No correlation
- **Blue**: Strong positive correlation

---

### **Performance Analytics Tab** 📈
**Purpose**: Detailed performance analysis and benchmarking

**Key Metrics**:
- Total Return vs Benchmarks
- Sharpe Ratio
- Maximum Drawdown
- Win Rate

**Charts**:
- Performance vs SOL/BTC benchmarks
- Strategy performance breakdown
- Risk-adjusted returns

**Performance Indicators**:
- **Excellent**: >10% returns
- **Good**: 5-10% returns
- **Neutral**: -2% to 5% returns
- **Poor**: <-2% returns

---

### **Intelligence Layer Tab** 🧠
**Purpose**: AI decision monitoring and learning analytics

**Key Sections**:

1. **AI Decision Metrics**:
   - 24h decision count
   - Execution rate
   - Average confidence
   - Learning rate

2. **Decision Confidence Distribution**:
   - High confidence decisions (>0.8)
   - Medium confidence (0.6-0.8)
   - Low confidence (<0.6)

3. **Post-Trade Intelligence**:
   - Position monitoring
   - News sentiment analysis
   - Whale movement tracking
   - AI feedback loop metrics

4. **Recent AI Decisions Table**:
   - Latest trading decisions
   - Execution status
   - P&L tracking

5. **Vector Memory Statistics**:
   - Total experiences stored
   - Memory utilization
   - Query accuracy

## 🔧 Dashboard Controls

### **Sidebar Controls**
- **🔄 Refresh Data**: Manual data refresh
- **⚙️ Settings**: Dashboard configuration
- **📊 Metrics**: Key performance indicators

### **Auto-Refresh**
- Dashboard auto-refreshes every 30 seconds
- Manual refresh available via sidebar button
- Real-time updates for critical metrics

### **Interactive Charts**
- **Zoom**: Mouse wheel or zoom controls
- **Pan**: Click and drag
- **Hover**: Detailed data points
- **Legend**: Click to show/hide series

## 📱 Mobile Responsiveness

The dashboard is optimized for:
- **Desktop**: Full feature set
- **Tablet**: Responsive layout
- **Mobile**: Essential metrics view

## 🚨 Alert System

### **Visual Alerts**
- **Color Coding**: Risk levels and performance
- **Status Indicators**: System health
- **Threshold Lines**: Risk and performance limits

### **Alert Types**
1. **System Alerts**: Component offline/online
2. **Risk Alerts**: High risk levels
3. **Performance Alerts**: Significant changes
4. **MEV Alerts**: High MEV risk detected

## 🔍 Troubleshooting

### **Common Issues**

#### **No Data Displayed**
1. Check Redis connection
2. Verify API endpoints
3. Check system components
4. Review error logs

#### **Slow Performance**
1. Reduce refresh frequency
2. Limit chart data points
3. Check system resources
4. Optimize network connection

#### **Charts Not Loading**
1. Clear browser cache
2. Check JavaScript console
3. Verify Plotly dependencies
4. Restart dashboard

### **System Requirements**
- **Browser**: Chrome, Firefox, Safari, Edge
- **RAM**: Minimum 2GB available
- **Network**: Stable connection to OVERMIND components
- **Screen**: Minimum 1024x768 resolution

## 📊 Data Sources

### **Real-time Data**
- Redis/DragonflyDB: System metrics
- OVERMIND Brain API: AI decisions
- Rust Executor API: Trading data

### **Historical Data**
- Portfolio performance history
- Strategy performance records
- Risk assessment history
- Correlation analysis data

## 🎨 Customization

### **Themes**
- Dark theme (default)
- Light theme option
- Custom color schemes

### **Layout**
- Responsive design
- Configurable refresh rates
- Customizable chart types

### **Metrics**
- Configurable thresholds
- Custom alert levels
- Personalized dashboards

## 📈 Best Practices

### **Monitoring Workflow**
1. **Daily**: Check Overview tab for system health
2. **Weekly**: Review Performance Analytics
3. **Monthly**: Analyze Strategy Heat Map
4. **Ongoing**: Monitor Risk Management tab

### **Performance Optimization**
1. Use appropriate refresh intervals
2. Focus on relevant metrics
3. Regular system maintenance
4. Monitor resource usage

### **Risk Management**
1. Set appropriate alert thresholds
2. Monitor correlation changes
3. Review hedge effectiveness
4. Track MEV protection metrics

## 🆘 Support

### **Getting Help**
1. Check this user guide
2. Review troubleshooting section
3. Check system logs
4. Verify component connectivity

### **Reporting Issues**
1. Note error messages
2. Check browser console
3. Verify system status
4. Document reproduction steps

---

**🧠 THE OVERMIND PROTOCOL Dashboard - Your Command Center for Intelligent Trading** 🚀
