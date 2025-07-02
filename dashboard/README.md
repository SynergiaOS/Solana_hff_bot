# 🧠 THE OVERMIND PROTOCOL - Comprehensive Dashboard

Advanced real-time monitoring interface for THE OVERMIND PROTOCOL with strategy heat maps, risk management, and intelligence metrics.

## 🚀 Features

### 📊 **Overview Tab**
- Real-time system status monitoring
- Portfolio performance tracking
- Key performance indicators
- System health indicators

### 🔥 **Strategy Heat Map Tab**
- Strategy performance matrix by market regime
- Real-time strategy status
- Confidence level tracking
- Performance analytics

### 🛡️ **Risk Management Tab**
- Hedging layer monitoring
- MEV protection metrics
- Risk score tracking
- Active hedge positions

### 📊 **Correlation Analysis Tab**
- Real-time correlation matrix
- Asset correlation heat maps
- Correlation clusters
- Hedge opportunity identification

### 📈 **Performance Analytics Tab**
- Portfolio performance vs benchmarks
- Strategy performance breakdown
- Risk-adjusted returns
- Sharpe ratio tracking

### 🧠 **Intelligence Layer Tab**
- AI decision monitoring
- Post-trade intelligence
- Vector memory statistics
- Learning rate tracking

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Redis/DragonflyDB running on localhost:6379
- OVERMIND Brain API running on localhost:8001
- Rust Executor running on localhost:8080

### Install Dependencies
```bash
cd dashboard
pip install -r requirements.txt
```

## 🚀 Quick Start

### Method 1: Using the Startup Script
```bash
cd dashboard
python start_dashboard.py
```

### Method 2: Direct Streamlit Launch
```bash
cd dashboard
streamlit run comprehensive_overmind_dashboard.py --server.port 8501
```

### Method 3: Custom Configuration
```bash
export DASHBOARD_HOST=0.0.0.0
export DASHBOARD_PORT=8501
export REDIS_HOST=localhost
export BRAIN_API_URL=http://localhost:8001
python start_dashboard.py
```

## 📱 Access

Once started, the dashboard will be available at:
- **Local**: http://localhost:8501
- **Network**: http://YOUR_IP:8501

## ⚙️ Configuration

### Environment Variables
```bash
# Dashboard settings
DASHBOARD_HOST=0.0.0.0          # Dashboard host
DASHBOARD_PORT=8501             # Dashboard port

# Redis/DragonflyDB settings
REDIS_HOST=localhost            # Redis host
REDIS_PORT=6379                 # Redis port

# API endpoints
BRAIN_API_URL=http://localhost:8001      # OVERMIND Brain API
EXECUTOR_API_URL=http://localhost:8080   # Rust Executor API
```

### Configuration File
Edit `dashboard_config.py` to customize:
- Refresh intervals
- Alert thresholds
- Color schemes
- Chart settings

## 📊 Dashboard Components

### Data Connectors
- **OVERMINDDataConnector**: Fetches data from Redis and APIs
- **SystemHealthMonitor**: Monitors system component status
- **PerformanceTracker**: Tracks portfolio and strategy performance

### Visualization Components
- **Heat Maps**: Strategy performance and correlation matrices
- **Real-time Charts**: Portfolio value, risk scores, MEV metrics
- **Status Cards**: System health and key metrics
- **Data Tables**: Strategy details, hedge positions, AI decisions

### Real-time Features
- **Auto-refresh**: Configurable refresh intervals
- **Live Updates**: Real-time metric updates
- **Interactive Controls**: Zoom, pan, filter capabilities
- **Alert Notifications**: Visual alerts for important events

## 🔧 Troubleshooting

### Common Issues

#### Dashboard Won't Start
```bash
# Check dependencies
pip install -r requirements.txt

# Check if ports are available
netstat -an | grep 8501
```

#### No Data Displayed
```bash
# Check Redis connection
redis-cli ping

# Check API endpoints
curl http://localhost:8001/health
curl http://localhost:8080/health
```

#### Performance Issues
```bash
# Reduce refresh frequency in dashboard_config.py
auto_refresh_interval = 60  # Increase from 30 to 60 seconds

# Limit chart data points
max_chart_points = 50  # Reduce from 100 to 50
```

### System Requirements
- **Minimum**: 2GB RAM, 2 CPU cores
- **Recommended**: 4GB RAM, 4 CPU cores
- **Network**: Low latency connection to OVERMIND components

## 📈 Performance Optimization

### For Large Datasets
1. Increase `data_cache_ttl` in configuration
2. Reduce `max_chart_points` for better performance
3. Use data sampling for historical charts

### For Multiple Users
1. Deploy with reverse proxy (nginx)
2. Use session state management
3. Implement user authentication if needed

## 🔒 Security Considerations

### Production Deployment
- Use HTTPS with SSL certificates
- Implement authentication/authorization
- Restrict network access to trusted IPs
- Use environment variables for sensitive data

### Data Privacy
- Dashboard displays aggregated metrics only
- No private keys or sensitive data exposed
- All data fetched from local Redis/APIs

## 🧪 Development

### Adding New Metrics
1. Add data fetching method to `OVERMINDDataConnector`
2. Create visualization component
3. Add to appropriate dashboard tab
4. Update configuration if needed

### Custom Visualizations
```python
# Example: Adding a new chart
async def render_custom_chart(self):
    data = await self.data_connector.get_custom_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['x'], y=data['y']))
    
    st.plotly_chart(fig, use_container_width=True)
```

### Testing
```bash
# Run dashboard in development mode
streamlit run comprehensive_overmind_dashboard.py --server.runOnSave true
```

## 📚 API Reference

### Data Connector Methods
- `get_system_health()`: System component status
- `get_hedging_status()`: Hedging layer metrics
- `get_mev_protection_metrics()`: MEV protection data
- `get_strategy_performance()`: Strategy performance data
- `get_portfolio_metrics()`: Portfolio metrics

### Configuration Classes
- `DashboardConfig`: Main dashboard settings
- `VisualizationConfig`: Chart and color settings
- `MonitoringConfig`: Monitoring thresholds

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add new dashboard components
4. Test thoroughly
5. Submit pull request

## 📄 License

Part of THE OVERMIND PROTOCOL - Advanced AI Trading System

## 🆘 Support

For issues and questions:
1. Check troubleshooting section
2. Review configuration settings
3. Check system component status
4. Verify network connectivity

---

**🧠 THE OVERMIND PROTOCOL Dashboard - Real-time Intelligence at Your Fingertips** 🚀
