# SNIPERCOR - High-Frequency Trading System for Solana

## 🎯 Overview

SNIPERCOR is a high-performance, monolithic trading system built in Rust, specifically designed for high-frequency trading (HFT) on the Solana blockchain. The system specializes in token sniping, arbitrage opportunities, and ultra-low latency trade execution.

## 🏗️ Architecture

### Core Components

- **DataIngestor**: Real-time market data ingestion from Helius and QuickNode
- **StrategyEngine**: Advanced trading algorithms and signal generation
- **RiskManager**: Real-time risk assessment and position management
- **Executor**: Ultra-low latency trade execution with Solana optimizations
- **Persistence**: High-performance data storage and retrieval

### Communication

All modules communicate through Tokio MPSC channels for zero-latency inter-module communication:
- `market_data_channel`: DataIngestor → StrategyEngine
- `signal_channel`: StrategyEngine → RiskManager
- `execution_channel`: RiskManager → Executor
- `persistence_channel`: All modules → Persistence

## 🚀 Quick Start

### Prerequisites

- Rust 1.75+ with nightly toolchain
- Docker and Docker Compose
- 16GB+ RAM (recommended for production)
- SSD storage for optimal performance

### Installation

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd snipercor
chmod +x scripts/system.sh
./scripts/system.sh
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Build and run:**
```bash
# Development build
cargo build

# Production build (optimized for Contabo VDS)
cargo build --profile contabo

# Run with paper trading (default)
SNIPER_TRADING_MODE=paper cargo run

# Run with live trading (⚠️ REAL MONEY)
SNIPER_TRADING_MODE=live cargo run
```

## 📊 Performance Targets

- **Latency**: <50ms order-to-execution
- **Throughput**: 1000+ orders/second
- **Uptime**: 99.9%+ availability
- **Memory**: <8GB RAM usage under normal load

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SNIPER_TRADING_MODE` | Trading mode: `paper` or `live` | `paper` |
| `SNIPER_MAX_POSITION_SIZE` | Maximum position size in USD | `1000` |
| `SNIPER_MAX_DAILY_LOSS` | Maximum daily loss limit | `500` |
| `SNIPER_SOLANA_RPC_URL` | Solana RPC endpoint | Required |
| `SNIPER_HELIUS_API_KEY` | Helius API key | Required |
| `SNIPER_QUICKNODE_API_KEY` | QuickNode API key | Required |

### Build Profiles

- **dev**: Development with debug symbols
- **release**: Standard release optimization
- **contabo**: Optimized for Contabo VDS (6 vCPU, 24GB RAM)

## 🛡️ Safety Features

- **Paper Trading Default**: All trading starts in simulation mode
- **Risk Limits**: Configurable position and loss limits
- **Circuit Breakers**: Automatic trading halt on anomalies
- **Audit Logging**: Complete transaction and decision audit trail

## 📈 Monitoring

- **Health Endpoint**: `GET /health` - System status
- **Metrics Endpoint**: `GET /metrics` - Performance metrics
- **Positions Endpoint**: `GET /positions` - Current positions
- **Logs**: Structured JSON logging with correlation IDs

## 🔒 Security

- **Secret Management**: All secrets via environment variables
- **Input Validation**: Comprehensive data sanitization
- **Rate Limiting**: API and execution rate limits
- **Audit Trail**: Complete operation logging

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## ⚠️ Disclaimer

This software is for educational and research purposes. Trading cryptocurrencies involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/snipercor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/snipercor/discussions)
- **Security**: security@yourcompany.com

---

**⚡ Built for speed. Designed for profit. Engineered for reliability.**
