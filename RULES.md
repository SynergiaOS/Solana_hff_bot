# SNIPERCOR Development Rules and Standards

## 🎯 Core Principles

### 1. Safety First
- **Default Paper Trading**: All trading functionality MUST default to paper trading mode
- **Explicit Live Mode**: Live trading requires explicit `SNIPER_TRADING_MODE=live` environment variable
- **Risk Limits**: All operations must respect configured risk parameters
- **Input Validation**: Every external input must be validated and sanitized

### 2. Performance Critical
- **Zero-Copy Operations**: Minimize memory allocations in hot paths
- **Async-First**: All I/O operations must be asynchronous
- **Channel Communication**: Use Tokio MPSC channels for inter-module communication
- **Memory Efficiency**: Target <8GB RAM usage under normal load

### 3. Reliability
- **Error Handling**: All operations return `Result<T, E>` with proper error propagation
- **Graceful Degradation**: System continues operating when non-critical components fail
- **Circuit Breakers**: Automatic halt on anomalous conditions
- **Comprehensive Logging**: All decisions and actions must be logged

## 🏗️ Architecture Rules

### Module Structure
```
src/
├── main.rs              # Application entry point
├── config.rs            # Configuration management
└── modules/
    ├── mod.rs           # Module declarations
    ├── data_ingestor.rs # Market data ingestion
    ├── strategy.rs      # Trading strategy engine
    ├── risk.rs          # Risk management
    ├── executor.rs      # Trade execution
    └── persistence.rs   # Data persistence
```

### Communication Channels
- `market_data_channel`: DataIngestor → Strategy
- `signal_channel`: Strategy → Risk
- `execution_channel`: Risk → Executor
- `persistence_channel`: All → Persistence

### Dependencies (Cargo.toml)
```toml
[dependencies]
# Core async runtime
tokio = { version = "1.35", features = ["full"] }

# Solana blockchain
solana-sdk = "1.18"
solana-client = "1.18"

# Web framework
axum = "0.7"

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# Error handling
anyhow = "1.0"
thiserror = "1.0"

# Logging
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

# Database
sqlx = { version = "0.7", features = ["runtime-tokio-rustls", "postgres", "chrono", "uuid"] }

# HTTP client
reqwest = { version = "0.11", features = ["json"] }

# WebSocket
tokio-tungstenite = "0.21"

# Time
chrono = { version = "0.4", features = ["serde"] }

# UUID
uuid = { version = "1.0", features = ["v4", "serde"] }

# Environment
dotenvy = "0.15"

[profile.release]
lto = true
codegen-units = 1
panic = "abort"

[profile.contabo]
inherits = "release"
opt-level = 3
target-cpu = "native"
```

## 🔒 Security Rules

### Secret Management
- **Environment Variables**: All secrets via environment variables with `SNIPER_` prefix
- **No Hardcoding**: Never hardcode API keys, private keys, or passwords
- **Validation**: Validate all secrets at startup

### Required Environment Variables
```bash
# Trading Configuration
SNIPER_TRADING_MODE=paper          # paper|live
SNIPER_MAX_POSITION_SIZE=1000      # USD
SNIPER_MAX_DAILY_LOSS=500          # USD

# Solana Configuration
SNIPER_SOLANA_RPC_URL=             # Required
SNIPER_WALLET_PRIVATE_KEY=         # Required for live trading

# API Keys
SNIPER_HELIUS_API_KEY=             # Required
SNIPER_QUICKNODE_API_KEY=          # Required

# Database
SNIPER_DATABASE_URL=               # PostgreSQL connection string

# Server
SNIPER_SERVER_PORT=8080            # API server port
```

### Input Validation
- **Sanitize All Inputs**: Use proper parsing and validation
- **Range Checks**: Validate numeric ranges
- **Type Safety**: Leverage Rust's type system for validation

## 📊 Performance Rules

### Latency Targets
- **Order Processing**: <50ms end-to-end
- **Market Data**: <10ms ingestion to strategy
- **Risk Check**: <5ms per signal
- **Execution**: <20ms signal to blockchain

### Memory Management
- **Bounded Channels**: Use bounded channels to prevent memory leaks
- **Resource Cleanup**: Implement proper Drop traits
- **Memory Monitoring**: Track memory usage in production

### Optimization Profiles
- **Development**: Fast compilation, debug symbols
- **Release**: Standard optimizations
- **Contabo**: Optimized for 6 vCPU, 24GB RAM VDS

## 🧪 Testing Rules

### Test Coverage
- **Unit Tests**: Every public function must have unit tests
- **Integration Tests**: Test module interactions
- **Performance Tests**: Benchmark critical paths
- **Paper Trading Tests**: Validate all strategies in simulation

### Test Structure
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_function_name() {
        // Arrange
        // Act
        // Assert
    }
}
```

## 📝 Logging Rules

### Log Levels
- **ERROR**: System failures, trading halts
- **WARN**: Risk limit breaches, degraded performance
- **INFO**: Trading decisions, system state changes
- **DEBUG**: Detailed execution flow
- **TRACE**: Performance metrics, raw data

### Log Format
```rust
use tracing::{info, warn, error, debug, trace};

// Include correlation IDs
info!(
    correlation_id = %correlation_id,
    symbol = %symbol,
    action = %action,
    "Trade signal generated"
);
```

### Structured Logging
- **JSON Format**: Use structured JSON logging in production
- **Correlation IDs**: Track requests across modules
- **Performance Metrics**: Log execution times for critical operations

## 🚀 Deployment Rules

### Build Process
```bash
# Development
cargo build

# Production (Contabo optimized)
cargo build --profile contabo

# Docker
docker build -t snipercor:latest .
```

### Runtime Configuration
- **Resource Limits**: Configure appropriate CPU and memory limits
- **Health Checks**: Implement comprehensive health endpoints
- **Graceful Shutdown**: Handle SIGTERM for clean shutdown

## 🔧 Code Style Rules

### Rust Conventions
- **snake_case**: Functions, variables, modules
- **PascalCase**: Types, structs, enums
- **SCREAMING_SNAKE_CASE**: Constants
- **Documentation**: All public items must have doc comments

### Error Handling
```rust
use anyhow::{Result, Context};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum TradingError {
    #[error("Invalid signal: {0}")]
    InvalidSignal(String),
    #[error("Risk limit exceeded")]
    RiskLimitExceeded,
}

pub async fn process_signal(signal: Signal) -> Result<()> {
    validate_signal(&signal)
        .context("Failed to validate trading signal")?;
    Ok(())
}
```

### Async Patterns
```rust
// Prefer async/await over manual Future implementation
pub async fn fetch_market_data() -> Result<MarketData> {
    let response = reqwest::get("https://api.example.com/data").await?;
    let data = response.json().await?;
    Ok(data)
}
```

## ⚠️ Critical Safety Rules

### Trading Safety
1. **Paper Trading Default**: System MUST start in paper trading mode
2. **Live Trading Confirmation**: Require explicit confirmation for live trading
3. **Emergency Stop**: Implement immediate trading halt capability
4. **Position Limits**: Enforce maximum position sizes
5. **Loss Limits**: Implement daily and total loss limits

### System Safety
1. **Graceful Degradation**: Continue operating with reduced functionality
2. **Circuit Breakers**: Automatic halt on anomalous conditions
3. **Resource Monitoring**: Monitor CPU, memory, and network usage
4. **Backup Systems**: Implement fallback mechanisms for critical components

---

**🛡️ These rules are non-negotiable. Violations may result in financial loss or system failure.**
