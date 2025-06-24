# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Overmind Protocol is a production-ready AI-enhanced high-frequency trading system for Solana blockchain. It implements a hybrid Python-Rust architecture that separates AI decision-making from high-performance execution, achieving sub-10ms latency with GENIUS-level AI intelligence.

## Architecture

### Hybrid AI-Execution System
- **AI Brain (Python)**: Located in `/brain/` - handles decision-making, risk analysis, and vector memory storage using LangChain, OpenAI, and ChromaDB
- **Rust Executor**: Located in `/src/` - handles high-performance trade execution, DEX integration, and wallet management
- **Communication Layer**: DragonflyDB (Redis-compatible) for real-time message passing between Python and Rust components
- **External Integrations**: TensorZero (AI optimization), Jito (MEV protection), Helius (premium Solana data)

### Key Data Flow
Market events → AI Brain analysis → Risk assessment → Trading decisions → Rust Executor → Blockchain execution → Feedback loop to AI memory

## Development Commands

### Unified Project Management (Recommended)
The project uses **pixi** for unified environment management across Python and Rust:

```bash
# Environment setup
pixi shell                          # Activate development environment
pixi run setup-all                  # Complete system setup

# Development workflow  
pixi run dev-full                   # Start complete development stack
pixi run start-overmind             # Start production system
pixi run stop-overmind              # Stop system

# Testing
pixi run test-all                   # Run all tests (Python + Rust)
pixi run test-integration-full      # Complete integration test with Docker

# Component-specific development
pixi run dev-brain                  # Python AI Brain only
pixi run dev-executor               # Rust Executor only
```

### Rust Commands
```bash
# Build
cargo build --release              # Production build
cargo build --profile contabo      # Optimized for Contabo VDS deployment

# Testing
cargo test --workspace             # All Rust tests
cargo test --test integration_tests # Integration tests only
cargo clippy                       # Linting
cargo fmt                          # Code formatting

# Execution modes
SNIPER_TRADING_MODE=paper cargo run     # Paper trading mode (safe)
SNIPER_TRADING_MODE=live cargo run --profile contabo  # Live trading (requires setup)
```

### Python AI Brain Commands
```bash
# From /brain directory
python -m src.overmind_brain.main       # Start AI brain
python -m src.overmind_brain.simple_brain # Start simplified brain
pytest                                  # Run Python tests
```

### Docker Commands
```bash
# Development
docker-compose up -d                    # Basic development stack
docker-compose -f docker-compose.devnet.yml up -d  # Devnet testing

# Production  
docker-compose -f deployment/docker-compose/docker-compose.overmind.yml up -d
```

### Testing Scripts
```bash
# Comprehensive testing
./testing/scripts/test-overmind-complete.sh    # Complete system test
./testing/scripts/test-overmind-e2e.sh         # End-to-end test
./scripts/test_e2e_devnet.sh                   # Devnet integration test

# Component testing  
./testing/scripts/test-local-components.sh     # Local components only
./testing/scripts/test-api-only.sh             # API tests only
```

### System Control
```bash
# Overmind control script
./scripts/overmind-control.sh status           # System status
./scripts/overmind-control.sh start [paper|live] # Start trading
./scripts/overmind-control.sh stop             # Emergency stop
./scripts/overmind-control.sh wallets          # Wallet balances
./scripts/overmind-control.sh transactions     # Recent transactions
```

## Code Structure & Key Files

### Core Modules (`/src/modules/`)
- `hft_engine.rs` - Main HFT orchestrator with sub-25ms execution targets
- `ai_connector.rs` - Bridge between Python AI Brain and Rust Executor via DragonflyDB
- `multi_wallet_executor.rs` - Risk-distributed wallet management system
- `jito_client.rs` - MEV protection through Jito bundle execution
- `dex_integration.rs` - Multi-DEX routing (Jupiter, Raydium, Orca)
- `tensorzero_client.rs` - AI optimization for transaction parameters
- `real_price_fetcher.rs` - Real-time price data aggregation

### AI Brain Components (`/brain/src/overmind_brain/`)
- `decision_engine.py` - LangChain-based intelligent decision making
- `vector_memory.py` - ChromaDB-based experience storage and pattern recognition
- `risk_analyzer.py` - Portfolio risk assessment and position sizing
- `market_analyzer.py` - Real-time market data analysis
- `helius_integration.py` - Premium Solana blockchain data integration

### Configuration
- Environment variables prefixed with `SNIPER_`, `OVERMIND_`, loaded via `/src/config/env_loader.rs`
- Trading modes: `SNIPER_TRADING_MODE=paper|live`
- AI modes: `OVERMIND_MODE=enabled`, `OVERMIND_AI_MODE=enabled`

## Development Practices

### Safety & Security
- **Always default to paper trading mode** (`SNIPER_TRADING_MODE=paper`)
- Never hardcode API keys or private keys - use environment variables
- Multi-wallet architecture distributes risk across accounts
- Comprehensive circuit breakers and emergency stop mechanisms

### Performance Requirements
- **Target Latencies**: AI decisions <50ms, trade execution <25ms
- **Optimization focus**: Memory allocation in hot paths, connection pooling, async processing
- **Monitoring**: Prometheus metrics for latency, throughput, and system health

### Testing Strategy
- **Multi-level testing**: Unit tests, integration tests, E2E tests, performance tests
- **Mock services**: Mock TensorZero and Jito servers for isolated testing in `/tests/`
- **Paper trading validation**: Always test in paper mode before live deployment
- **Stress testing**: System validated for extreme load conditions

### Code Quality
- **Rust**: Use `cargo clippy` and `cargo fmt`, avoid `unsafe` code
- **Python**: Follow AI Brain patterns, use async/await for performance
- **Documentation**: Reference code locations as `file_path:line_number`

## Deployment

### Production Deployment
```bash
./deployment/scripts/deploy-overmind.sh        # Complete production deployment
./deployment/scripts/health-check-all.sh       # Verify deployment health
```

### Monitoring
```bash
./monitoring/start-monitoring.sh               # Start Prometheus/Grafana stack
# Access: Grafana at :3000, Prometheus at :9090
```

## Environment Modes

- **Development**: Full stack with hot reload and debug logging
- **Paper Trading**: Safe mode with simulated transactions (default)
- **Live Trading**: Production mode with real transactions (requires explicit configuration)
- **Testing**: Isolated environment with mock services

The system has achieved production-ready status with GENIUS-level AI performance, ultra-high throughput (90+ operations/sec), and 100% stress test success rate.