# SNIPERCOR - Implementation Guide for Best Practices

This guide provides concrete examples of how to implement the best practices outlined in `BEST_PRACTICES.md` in the SNIPERCOR codebase.

## Implementing Rust Best Practices

### Example: Error Handling in Executor

Add proper error handling for RPC errors in the `execute_live_trade` function:

```rust
async fn execute_live_trade(&self, signal: ApprovedSignal) -> Result<ExecutionResult> {
    warn!("🔴 EXECUTING LIVE TRADE - Signal ID: {}", signal.original_signal.signal_id);
    
    // Build and send transaction
    let result = match self.send_transaction(&signal).await {
        Ok(signature) => {
            // Transaction sent successfully
            ExecutionResult {
                signal_id: signal.original_signal.signal_id,
                transaction_id: signature,
                status: ExecutionStatus::Confirmed,
                executed_quantity: signal.approved_quantity,
                executed_price: signal.original_signal.target_price,
                fees: signal.approved_quantity * signal.original_signal.target_price * 0.001,
                timestamp: chrono::Utc::now(),
                error_message: None,
            }
        },
        Err(e) => {
            // Handle transaction error
            error!("Failed to execute transaction: {}", e);
            ExecutionResult {
                signal_id: signal.original_signal.signal_id,
                transaction_id: format!("failed_{}", uuid::Uuid::new_v4()),
                status: ExecutionStatus::Failed,
                executed_quantity: 0.0,
                executed_price: 0.0,
                fees: 0.0,
                timestamp: chrono::Utc::now(),
                error_message: Some(e.to_string()),
            }
        }
    };
    
    Ok(result)
}

async fn send_transaction(&self, signal: &ApprovedSignal) -> Result<String> {
    // Implementation with retry logic for RPC errors
    let max_retries = 3;
    let mut retry_count = 0;
    let mut backoff_ms = 50;
    
    loop {
        match self.build_and_send_transaction(signal).await {
            Ok(signature) => return Ok(signature),
            Err(e) => {
                retry_count += 1;
                if retry_count >= max_retries {
                    return Err(anyhow::anyhow!("Max retries exceeded: {}", e));
                }
                
                // Exponential backoff
                tokio::time::sleep(tokio::time::Duration::from_millis(backoff_ms)).await;
                backoff_ms *= 2;
                warn!("Retrying transaction ({}/{}), backoff: {}ms", retry_count, max_retries, backoff_ms);
            }
        }
    }
}
```

### Example: Unit Test for Strategy Engine

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_calculate_slippage() {
        // Test normal case
        let slippage = calculate_slippage(100.0, 1000.0);
        assert_eq!(slippage, 0.1); // 10% slippage
        
        // Test zero liquidity
        let slippage = calculate_slippage(100.0, 0.0);
        assert_eq!(slippage, 1.0); // 100% slippage (max)
        
        // Test huge order
        let slippage = calculate_slippage(10000.0, 1000.0);
        assert_eq!(slippage, 1.0); // 100% slippage (capped)
    }
}
```

## Implementing AI Best Practices

### Example: Effective Prompt for Augment Code

```
Based on the knowledge from RULES.md and the existing code, perform the following task:

In the file src/modules/executor.rs, in the function send_transaction, add handling for the RpcError::TransactionError and implement retry logic 3 times with exponential backoff.

After making the changes, run 'cargo test --workspace' to confirm all tests pass. Present me with the final diff for approval.
```

## Implementing Testing Best Practices

### Example: Integration Test Between Modules

```rust
#[cfg(test)]
mod integration_tests {
    use super::*;
    use crate::modules::data_ingestor::MarketData;
    use crate::modules::strategy::StrategyEngine;
    use tokio::sync::mpsc;
    
    #[tokio::test]
    async fn test_data_to_strategy_flow() {
        // Setup channels
        let (market_data_tx, market_data_rx) = mpsc::unbounded_channel::<MarketData>();
        let (signal_tx, mut signal_rx) = mpsc::unbounded_channel::<TradingSignal>();
        
        // Initialize modules
        let mut strategy_engine = StrategyEngine::new(market_data_rx, signal_tx);
        
        // Start strategy engine in background
        let strategy_task = tokio::spawn(async move {
            strategy_engine.start().await.unwrap();
        });
        
        // Send market data
        let market_data = MarketData {
            symbol: "SOL/USDC".to_string(),
            price: 110.0, // Price that should trigger a signal
            volume: 1000.0,
            timestamp: chrono::Utc::now(),
            source: DataSource::Helius,
        };
        
        market_data_tx.send(market_data).unwrap();
        
        // Wait for signal
        let timeout = tokio::time::Duration::from_millis(100);
        let signal = tokio::time::timeout(timeout, signal_rx.recv()).await;
        
        // Clean up
        strategy_task.abort();
        
        // Assert
        assert!(signal.is_ok(), "Timed out waiting for signal");
        let signal = signal.unwrap();
        assert!(signal.is_some(), "No signal received");
        let signal = signal.unwrap();
        assert_eq!(signal.action, TradeAction::Buy);
    }
}
```

### Example: Mocking External Services

```rust
// Add mockall to Cargo.toml
// mockall = "0.11.3"

// In src/modules/executor.rs
#[cfg(test)]
use mockall::{automock, predicate::*};

#[cfg_attr(test, automock)]
trait SolanaClient {
    async fn send_transaction(&self, transaction: &[u8]) -> Result<String>;
    async fn get_balance(&self, pubkey: &str) -> Result<u64>;
}

struct RealSolanaClient {
    rpc_url: String,
    // other fields
}

impl SolanaClient for RealSolanaClient {
    async fn send_transaction(&self, transaction: &[u8]) -> Result<String> {
        // Real implementation
    }
    
    async fn get_balance(&self, pubkey: &str) -> Result<u64> {
        // Real implementation
    }
}

// In tests
#[tokio::test]
async fn test_executor_with_mock_client() {
    // Create mock
    let mut mock_client = MockSolanaClient::new();
    
    // Set expectations
    mock_client
        .expect_send_transaction()
        .returning(|_| Ok("transaction_signature".to_string()));
    
    // Create executor with mock
    let executor = Executor::new_with_client(
        execution_rx,
        execution_result_tx,
        TradingMode::Paper,
        Box::new(mock_client),
    );
    
    // Test execution
    // ...
}
```

### Example: E2E Test with Paper Trading

```rust
#[tokio::test]
async fn test_end_to_end_paper_trading() {
    // Set up environment
    std::env::set_var("SNIPER_TRADING_MODE", "paper");
    
    // Create channels
    let (market_data_tx, market_data_rx) = mpsc::unbounded_channel::<MarketData>();
    let (signal_tx, signal_rx) = mpsc::unbounded_channel::<TradingSignal>();
    let (execution_tx, execution_rx) = mpsc::unbounded_channel::<ApprovedSignal>();
    let (execution_result_tx, mut execution_result_rx) = mpsc::unbounded_channel::<ExecutionResult>();
    
    // Initialize modules with test configuration
    let strategy_engine = StrategyEngine::new(market_data_rx, signal_tx);
    let risk_manager = RiskManager::new(
        signal_rx,
        execution_tx,
        RiskParameters {
            max_position_size: 1000.0,
            max_daily_loss: 500.0,
            min_confidence_threshold: 0.5,
        },
    );
    let executor = Executor::new(
        execution_rx,
        execution_result_tx,
        TradingMode::Paper,
        "https://api.testnet.solana.com".to_string(),
        "dummy_key".to_string(),
    );
    
    // Start all modules in background
    let strategy_task = tokio::spawn(async move { strategy_engine.start().await });
    let risk_task = tokio::spawn(async move { risk_manager.start().await });
    let executor_task = tokio::spawn(async move { executor.start().await });
    
    // Send test market data
    let market_data = MarketData {
        symbol: "SOL/USDC".to_string(),
        price: 110.0, // Price that should trigger a signal
        volume: 1000.0,
        timestamp: chrono::Utc::now(),
        source: DataSource::Helius,
    };
    
    market_data_tx.send(market_data).unwrap();
    
    // Wait for a signal
    let timeout = tokio::time::Duration::from_millis(100);
    let signal = tokio::time::timeout(timeout, signal_rx.recv()).await;
    
    assert!(signal.is_ok(), "Timed out waiting for signal");
    let signal = signal.unwrap();
    assert!(signal.is_some(), "No signal received");
    let signal = signal.unwrap();
    
    // Assert that the signal is a buy order
    assert_eq!(signal.action, TradeAction::Buy);
    
    // Clean up
    strategy_task.abort();
    risk_task.abort();
    executor_task.abort();
}
```

## Implementing DevOps Best Practices

### Example: Docker Compose Configuration

```yaml
version: '3.8'

services:
  sniper-core:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - SNIPER_TRADING_MODE=paper
      - SNIPER_SOLANA_RPC_URL=${SNIPER_SOLANA_RPC_URL}
      - SNIPER_WALLET_PRIVATE_KEY=${SNIPER_WALLET_PRIVATE_KEY}
      - SNIPER_HELIUS_API_KEY=${SNIPER_HELIUS_API_KEY}
      - SNIPER_QUICKNODE_API_KEY=${SNIPER_QUICKNODE_API_KEY}
      - SNIPER_DATABASE_URL=postgresql://sniper:password@postgres:5432/snipercor
      - RUST_LOG=info
    depends_on:
      - postgres
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
      
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=sniper
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=snipercor
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped

volumes:
  postgres_data:
  grafana_data:
```

### Example: GitHub Actions Workflow

```yaml
name: SNIPERCOR CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Install Rust
      uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
        override: true
        components: clippy, rustfmt
    
    - name: Check formatting
      run: cargo fmt -- --check
    
    - name: Run Clippy
      run: cargo clippy --all-targets --all-features -- -D warnings
    
    - name: Run tests
      run: cargo test --workspace
    
    - name: Build
      run: cargo build --release
```

## Next Steps

1. Implement these examples in your codebase
2. Set up CI/CD pipelines for automated testing
3. Configure monitoring with Prometheus and Grafana
4. Document your AI prompts and results
5. Regularly review and update these practices as the project evolves
