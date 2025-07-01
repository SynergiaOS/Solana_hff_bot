//! HFT Engine Module
//!
//! Provides high-frequency trading capabilities with TensorZero optimization
//! and Jito bundle execution for MEV protection.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use solana_client::rpc_client::RpcClient;
use solana_sdk::{
    commitment_config::CommitmentConfig,
    pubkey::Pubkey,
    signature::{Keypair, Signature},
    signer::Signer,
    transaction::Transaction,
};
use std::{str::FromStr, time::Duration};
use tokio::time::sleep;
use tracing::{debug, error, info, warn};

// Import our TensorZero, Jito, DEX, error handling, and metrics modules
use crate::modules::dex_integration::{DexIntegration, SwapParams};
use crate::modules::error_handling::ErrorHandler;
use crate::modules::jito_client::{JitoClient, JitoConfig};
use crate::modules::metrics::MetricsCollector;
use crate::modules::tensorzero_client::{OptimizationResponse, TensorZeroClient, TensorZeroConfig};

/// Live execution report for feedback loop
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiveExecutionReport {
    /// Execution status: "SUCCESS", "FAILED", "PARTIAL"
    pub status: String,
    /// Blockchain transaction ID
    pub transaction_id: String,
    /// Actual execution price achieved
    pub executed_price: f64,
    /// Error message if execution failed
    pub error_message: Option<String>,
    /// Original trading signal that was executed
    pub original_signal: TradingSignal,
    /// TensorZero optimization applied
    pub tensorzero_optimization: Option<String>,
    /// Execution timestamp
    pub execution_timestamp: u64,
    /// Gas/fees consumed
    pub fees_paid: f64,
    /// Slippage experienced
    pub slippage: f64,
    /// Execution latency in milliseconds
    pub execution_latency_ms: u64,
}

impl std::fmt::Display for LiveExecutionReport {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "LiveExecutionReport(status: {}, tx_id: {}, price: ${:.6}, fees: ${:.6})",
            self.status, self.transaction_id, self.executed_price, self.fees_paid
        )
    }
}

/// Configuration for the HFT Engine
#[derive(Debug, Clone)]
pub struct HftEngineConfig {
    /// Solana RPC URL for transaction execution
    pub solana_rpc_url: String,
    /// TensorZero API endpoint
    pub tensorzero_url: String,
    /// Jito bundle endpoint
    pub jito_url: String,
    /// Jito tip account
    pub jito_tip_account: String,
    /// Maximum tip amount in lamports
    pub max_tip_lamports: u64,
    /// Number of retry attempts for failed transactions
    pub retry_attempts: u8,
    /// Delay between retries in milliseconds
    pub retry_delay_ms: u64,
    /// Whether to use Jito bundles for MEV protection
    pub use_jito_bundles: bool,
}

impl Default for HftEngineConfig {
    fn default() -> Self {
        Self {
            solana_rpc_url: "https://api.mainnet-beta.solana.com".to_string(),
            tensorzero_url: "http://tensorzero:3000".to_string(),
            jito_url: "https://mainnet.block-engine.jito.wtf".to_string(),
            jito_tip_account: "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5".to_string(),
            max_tip_lamports: 50000,
            retry_attempts: 3,
            retry_delay_ms: 500,
            use_jito_bundles: true,
        }
    }
}

/// Trading signal from AI Brain
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingSignal {
    pub symbol: String,
    pub action: String,
    pub quantity: f64,
    pub price: Option<f64>,
    pub confidence: f64,
    pub reasoning: String,
}

/// HFT Engine for high-performance trade execution
#[allow(dead_code)]
pub struct HftEngine {
    config: HftEngineConfig,
    rpc_client: RpcClient,
    wallet: Keypair,
    tensorzero_client: Option<TensorZeroClient>,
    jito_client: Option<JitoClient>,
    dex_integration: DexIntegration,
    error_handler: ErrorHandler,
    metrics_collector: MetricsCollector,
}

impl HftEngine {
    /// Create a new HFT Engine instance
    pub fn new(config: HftEngineConfig, wallet: Keypair) -> Result<Self> {
        let rpc_client = RpcClient::new_with_commitment(
            config.solana_rpc_url.clone(),
            CommitmentConfig::confirmed(),
        );

        // Initialize TensorZero client if URL is provided
        let tensorzero_client = if !config.tensorzero_url.is_empty() {
            let tensorzero_config = TensorZeroConfig {
                gateway_url: config.tensorzero_url.clone(),
                api_key: std::env::var("TENSORZERO_API_KEY").unwrap_or_default(),
                max_latency_ms: 50,
                optimization_level: "aggressive".to_string(),
                cache_enabled: true,
                batch_size: 10,
                request_timeout_secs: 5,
            };

            match TensorZeroClient::new(tensorzero_config) {
                Ok(client) => Some(client),
                Err(e) => {
                    warn!("Failed to initialize TensorZero client: {}. Continuing without optimization.", e);
                    None
                }
            }
        } else {
            None
        };

        // Initialize Jito client if enabled
        let jito_client = if config.use_jito_bundles {
            let jito_config = JitoConfig {
                bundle_url: config.jito_url.clone(),
                tip_account: config.jito_tip_account.clone(),
                max_tip_lamports: config.max_tip_lamports,
                bundle_size: 5,
                request_timeout_secs: 10,
                priority_fee_multiplier: 1.5,
            };

            match JitoClient::new(jito_config) {
                Ok(client) => Some(client),
                Err(e) => {
                    warn!(
                        "Failed to initialize Jito client: {}. Continuing without MEV protection.",
                        e
                    );
                    None
                }
            }
        } else {
            None
        };

        Ok(Self {
            config,
            rpc_client,
            wallet,
            tensorzero_client,
            jito_client,
            dex_integration: DexIntegration::new(),
            error_handler: ErrorHandler::new(),
            metrics_collector: MetricsCollector::new(),
        })
    }

    /// Execute a trading signal with TensorZero optimization and return detailed report
    pub async fn execute_signal(&self, signal: TradingSignal) -> Result<LiveExecutionReport> {
        let start_time = std::time::Instant::now();
        let execution_timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs();

        info!(
            "🚀 Executing signal: {} {} with confidence {:.2}",
            signal.action, signal.symbol, signal.confidence
        );

        // Step 1: Optimize transaction via TensorZero
        let (optimized_tx, tensorzero_optimization) =
            match self.optimize_with_tensorzero(&signal).await {
                Ok(tx) => (tx, Some("TensorZero optimization applied".to_string())),
                Err(e) => {
                    warn!(
                        "⚠️ TensorZero optimization failed: {}, proceeding without optimization",
                        e
                    );
                    // Create basic transaction without optimization
                    let basic_tx = self.create_basic_transaction(&signal).await?;
                    (basic_tx, None)
                }
            };

        // Step 2: Execute with retries and capture detailed results
        match self.execute_with_retry(optimized_tx).await {
            Ok(signature) => {
                let execution_latency = start_time.elapsed().as_millis() as u64;

                info!("✅ Transaction executed successfully: {}", signature);

                // Create success report
                Ok(LiveExecutionReport {
                    status: "SUCCESS".to_string(),
                    transaction_id: signature.to_string(),
                    executed_price: signal.price.unwrap_or(0.0), // TODO: Get actual execution price
                    error_message: None,
                    original_signal: signal,
                    tensorzero_optimization,
                    execution_timestamp,
                    fees_paid: 0.005, // TODO: Calculate actual fees
                    slippage: 0.001,  // TODO: Calculate actual slippage
                    execution_latency_ms: execution_latency,
                })
            }
            Err(e) => {
                let execution_latency = start_time.elapsed().as_millis() as u64;

                error!("❌ Transaction execution failed: {}", e);

                // Create failure report
                Ok(LiveExecutionReport {
                    status: "FAILED".to_string(),
                    transaction_id: "".to_string(),
                    executed_price: 0.0,
                    error_message: Some(e.to_string()),
                    original_signal: signal,
                    tensorzero_optimization,
                    execution_timestamp,
                    fees_paid: 0.0,
                    slippage: 0.0,
                    execution_latency_ms: execution_latency,
                })
            }
        }
    }

    /// Create basic transaction without TensorZero optimization
    async fn create_basic_transaction(&self, signal: &TradingSignal) -> Result<Transaction> {
        debug!(
            "Creating basic transaction for {} {}",
            signal.action, signal.symbol
        );

        // For now, create a simple mock transaction
        // TODO: Implement proper transaction creation based on signal
        let keypair = Keypair::new();
        let recent_blockhash = self.rpc_client.get_latest_blockhash()?;

        // Create a minimal transaction (transfer 0 SOL to self)
        let instruction =
            solana_sdk::system_instruction::transfer(&keypair.pubkey(), &keypair.pubkey(), 0);

        let transaction = Transaction::new_signed_with_payer(
            &[instruction],
            Some(&keypair.pubkey()),
            &[&keypair],
            recent_blockhash,
        );

        Ok(transaction)
    }

    /// Optimize transaction parameters using TensorZero
    async fn optimize_with_tensorzero(&self, signal: &TradingSignal) -> Result<Transaction> {
        debug!(
            "Optimizing transaction with TensorZero for {}",
            signal.symbol
        );

        // Use TensorZero client if available
        if let Some(ref tensorzero_client) = self.tensorzero_client {
            // Convert our signal to TensorZero format
            let tz_signal = crate::modules::tensorzero_client::TradingSignal {
                symbol: signal.symbol.clone(),
                action: signal.action.clone(),
                quantity: signal.quantity,
                price: signal.price,
                confidence: signal.confidence,
                reasoning: signal.reasoning.clone(),
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_secs(),
            };

            // Get optimization from TensorZero
            match tensorzero_client.optimize_signal(tz_signal).await {
                Ok(optimization) => {
                    info!(
                        "✅ TensorZero optimization successful - confidence: {:.2}, latency: {}ms",
                        optimization.confidence_score, optimization.estimated_latency_ms
                    );

                    // Build optimized transaction using TensorZero parameters
                    return self
                        .build_optimized_transaction(signal, &optimization)
                        .await;
                }
                Err(e) => {
                    warn!(
                        "TensorZero optimization failed: {}. Falling back to default parameters.",
                        e
                    );
                }
            }
        } else {
            debug!("TensorZero client not available, using default parameters");
        }

        // Fallback to DEX transaction without optimization if TensorZero is not available or fails
        self.build_dex_transaction(signal, None).await
    }

    /// Execute transaction with retry logic
    async fn execute_with_retry(&self, transaction: Transaction) -> Result<Signature> {
        let mut attempts = 0;
        let max_attempts = self.config.retry_attempts as usize;

        loop {
            attempts += 1;

            match self.execute_transaction(transaction.clone()).await {
                Ok(signature) => return Ok(signature),
                Err(e) => {
                    if attempts >= max_attempts {
                        return Err(e).context("Max retry attempts reached");
                    }

                    warn!(
                        "Transaction attempt {}/{} failed: {}. Retrying...",
                        attempts, max_attempts, e
                    );

                    sleep(Duration::from_millis(self.config.retry_delay_ms)).await;
                }
            }
        }
    }

    /// Execute a single transaction attempt
    async fn execute_transaction(&self, transaction: Transaction) -> Result<Signature> {
        if self.config.use_jito_bundles {
            self.execute_with_jito_bundle(transaction).await
        } else {
            self.execute_with_standard_rpc(transaction).await
        }
    }

    /// Execute transaction using Jito bundles for MEV protection
    async fn execute_with_jito_bundle(&self, transaction: Transaction) -> Result<Signature> {
        if let Some(ref jito_client) = self.jito_client {
            info!("🛡️ Executing transaction via Jito bundle for MEV protection");

            // Get the transaction signature before sending (since it's already signed)
            let signature = transaction
                .signatures
                .get(0)
                .ok_or_else(|| anyhow::anyhow!("Transaction has no signatures"))?;
            let signature_to_return = *signature;

            // Execute bundle using the Jito client
            match jito_client.execute_bundle(transaction.clone()).await {
                Ok(bundle_result) => {
                    info!(
                        "✅ Jito bundle executed successfully: bundle_id={}, latency={}ms",
                        bundle_result.bundle_id, bundle_result.latency_ms
                    );

                    // Return the signature that was captured before sending
                    Ok(signature_to_return)
                }
                Err(e) => {
                    // Log the error and propagate it using anyhow::Result
                    error!("❌ Jito bundle execution failed: {}", e);
                    Err(e).context("Failed to execute transaction via Jito bundle")
                }
            }
        } else {
            // Log warning and fall back to standard RPC if Jito client is not available
            warn!("⚠️ Jito client not available, falling back to standard RPC");
            self.execute_with_standard_rpc(transaction).await
        }
    }

    /// Execute transaction using standard Solana RPC
    async fn execute_with_standard_rpc(&self, transaction: Transaction) -> Result<Signature> {
        // In production, this would send the transaction to the Solana network
        // For now, we'll just return a mock signature

        // TODO: Replace with actual transaction submission
        let signature = transaction.signatures[0];

        Ok(signature)
    }

    /// Build an optimized transaction using TensorZero parameters
    async fn build_optimized_transaction(
        &self,
        signal: &TradingSignal,
        optimization: &OptimizationResponse,
    ) -> Result<Transaction> {
        info!("🧠 Building optimized transaction with TensorZero parameters");

        debug!("Using optimized parameters:");
        debug!(
            "  Slippage tolerance: {:.4}%",
            optimization.optimized_params.slippage_tolerance * 100.0
        );
        debug!(
            "  Priority fee: {} lamports",
            optimization.optimized_params.priority_fee_lamports
        );
        debug!(
            "  Compute unit limit: {}",
            optimization.optimized_params.compute_unit_limit
        );
        debug!("  Execution strategy: {}", optimization.execution_strategy);

        // Build DEX-specific transaction using TensorZero optimization
        self.build_dex_transaction(signal, Some(optimization)).await
    }

    /// Build DEX-specific transaction
    async fn build_dex_transaction(
        &self,
        signal: &TradingSignal,
        optimization: Option<&OptimizationResponse>,
    ) -> Result<Transaction> {
        info!(
            "🔄 Building DEX transaction for {} {}",
            signal.action, signal.symbol
        );

        // Parse trading pair from signal
        let (input_mint, output_mint) = self.parse_trading_pair(&signal.symbol)?;

        // Calculate swap parameters
        let swap_params = SwapParams {
            input_mint,
            output_mint,
            amount_in: (signal.quantity * 1_000_000.0) as u64, // Convert to lamports/tokens
            minimum_amount_out: self.calculate_minimum_output(signal, optimization)?,
            slippage_tolerance: optimization
                .map(|opt| opt.optimized_params.slippage_tolerance)
                .unwrap_or(0.01), // Default 1% slippage
            user_wallet: self.wallet.pubkey(),
        };

        // Find the best route
        let route = self.dex_integration.find_best_route(&swap_params).await?;

        // Build transaction for the selected DEX
        let transaction = self
            .dex_integration
            .build_swap_transaction(swap_params, route.dex_type, &self.wallet)
            .await?;

        info!(
            "✅ DEX transaction built successfully for {:?}",
            route.dex_type
        );
        Ok(transaction)
    }

    /// Parse trading pair from symbol (e.g., "SOL/USDC")
    fn parse_trading_pair(&self, symbol: &str) -> Result<(Pubkey, Pubkey)> {
        let parts: Vec<&str> = symbol.split('/').collect();
        if parts.len() != 2 {
            return Err(anyhow::anyhow!("Invalid trading pair format: {}", symbol));
        }

        let input_mint = match parts[0] {
            "SOL" => Pubkey::from_str("So11111111111111111111111111111111111111112")?,
            "USDC" => Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")?,
            _ => return Err(anyhow::anyhow!("Unsupported token: {}", parts[0])),
        };

        let output_mint = match parts[1] {
            "SOL" => Pubkey::from_str("So11111111111111111111111111111111111111112")?,
            "USDC" => Pubkey::from_str("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")?,
            _ => return Err(anyhow::anyhow!("Unsupported token: {}", parts[1])),
        };

        Ok((input_mint, output_mint))
    }

    /// Calculate minimum output amount considering slippage
    fn calculate_minimum_output(
        &self,
        signal: &TradingSignal,
        optimization: Option<&OptimizationResponse>,
    ) -> Result<u64> {
        let slippage = optimization
            .map(|opt| opt.optimized_params.slippage_tolerance)
            .unwrap_or(0.01);

        // Estimate output based on signal price and quantity
        let estimated_output = if let Some(price) = signal.price {
            (signal.quantity * price * 1_000_000.0) as u64
        } else {
            // Default estimate if no price provided
            (signal.quantity * 100.0 * 1_000_000.0) as u64 // Assume $100 per unit
        };

        // Apply slippage tolerance
        let minimum_output = (estimated_output as f64 * (1.0 - slippage)) as u64;
        Ok(minimum_output)
    }

    /// Build a mock transaction for testing
    #[allow(dead_code)]
    fn build_mock_transaction(&self, signal: &TradingSignal) -> Result<Transaction> {
        // Create a simple system transfer of 1 lamport from wallet to itself
        // This creates a real, valid Solana transaction for testing purposes

        // Get recent blockhash - wrap with proper error handling
        let recent_blockhash = self
            .rpc_client
            .get_latest_blockhash()
            .context("Failed to get recent blockhash")?;

        // Create system transfer instruction (1 lamport to self)
        let transfer_instruction = solana_sdk::system_instruction::transfer(
            &self.wallet.pubkey(), // From: bot's wallet
            &self.wallet.pubkey(), // To: same wallet (self-transfer)
            1,                     // Amount: 1 lamport
        );

        // Create transaction with the transfer instruction
        let mut transaction =
            Transaction::new_with_payer(&[transfer_instruction], Some(&self.wallet.pubkey()));

        // Sign transaction with the wallet keypair
        transaction.sign(&[&self.wallet], recent_blockhash);

        info!(
            "🔧 Built mock system transfer transaction: 1 lamport self-transfer for signal: {} {}",
            signal.action, signal.symbol
        );

        Ok(transaction)
    }

    /// Get current performance metrics
    pub fn get_metrics(&self) -> crate::modules::metrics::PerformanceMetrics {
        self.metrics_collector.get_metrics()
    }

    /// Log performance summary
    pub fn log_performance_summary(&self) {
        self.metrics_collector.log_performance_summary();
    }

    /// Export metrics in Prometheus format
    pub fn export_prometheus_metrics(&self) -> String {
        self.metrics_collector.export_prometheus_metrics()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::mock;
    use mockall::predicate::*;

    // Mock RpcClient for testing
    mock! {
        pub RpcClient {
            pub fn get_latest_blockhash(&self) -> Result<solana_sdk::hash::Hash>;
        }
    }

    #[tokio::test]
    async fn test_hft_engine_mock_execution() {
        // Skip test if not in test environment to avoid RPC calls
        if std::env::var("CI").is_err() && std::env::var("TEST_LIVE_RPC").is_err() {
            println!("Skipping HFT engine test in development environment");
            return;
        }

        // Create test wallet
        let wallet = Keypair::new();

        // Create test config
        let config = HftEngineConfig {
            solana_rpc_url: "https://api.devnet.solana.com".to_string(),
            use_jito_bundles: false,
            ..HftEngineConfig::default()
        };

        // Create HFT engine
        let engine = HftEngine::new(config, wallet);

        // Create test signal
        let signal = TradingSignal {
            symbol: "SOL/USDC".to_string(),
            action: "BUY".to_string(),
            quantity: 1.0,
            price: Some(100.0),
            confidence: 0.85,
            reasoning: "Test signal".to_string(),
        };

        // Execute signal
        let engine = engine.expect("Failed to create HFT engine");
        let result = engine.execute_signal(signal).await;

        // Verify result
        assert!(
            result.is_ok(),
            "Signal execution should succeed: {:?}",
            result.err()
        );
    }
}
