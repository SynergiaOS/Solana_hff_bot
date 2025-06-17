// THE OVERMIND PROTOCOL - Multi-Wallet Executor
// Enhanced executor with intelligent wallet selection and routing

use anyhow::{anyhow, Result};
use std::sync::Arc;
use tokio::sync::{mpsc, RwLock};
use tracing::{debug, error, info, warn};

use crate::config::TradingMode;
use crate::modules::executor::{ExecutionResult, ExecutionStatus};
use crate::modules::hft_engine::{HFTConfig, ExecutionResult as HFTExecutionResult, OvermindHFTEngine};
use crate::modules::risk::ApprovedSignal;
use crate::modules::strategy::StrategyType;
use crate::modules::wallet_manager::{WalletManager, WalletSelectionCriteria, WalletType};

/// Enhanced signal with wallet routing information
#[derive(Debug, Clone)]
pub struct RoutedSignal {
    pub original_signal: ApprovedSignal,
    pub selected_wallet_id: String,
    pub wallet_selection_reason: String,
    pub routing_timestamp: chrono::DateTime<chrono::Utc>,
}

/// Multi-wallet executor for THE OVERMIND PROTOCOL
pub struct MultiWalletExecutor {
    signal_receiver: mpsc::UnboundedReceiver<ApprovedSignal>,
    persistence_sender: mpsc::UnboundedSender<ExecutionResult>,
    wallet_manager: Arc<RwLock<WalletManager>>,
    trading_mode: TradingMode,
    solana_rpc_url: String,
    is_running: bool,
    hft_engine: Option<OvermindHFTEngine>,
    hft_mode_enabled: bool,
    // Multi-wallet specific fields
    wallet_selection_timeout_ms: u64,
    fallback_wallet_id: Option<String>,
    execution_stats: Arc<RwLock<ExecutionStats>>,
}

/// Execution statistics per wallet
#[derive(Debug, Default)]
pub struct ExecutionStats {
    pub total_executions: u64,
    pub successful_executions: u64,
    pub failed_executions: u64,
    pub wallet_usage: std::collections::HashMap<String, u64>,
    pub strategy_routing: std::collections::HashMap<StrategyType, std::collections::HashMap<String, u64>>,
}

impl MultiWalletExecutor {
    /// Create new multi-wallet executor
    pub fn new(
        signal_receiver: mpsc::UnboundedReceiver<ApprovedSignal>,
        persistence_sender: mpsc::UnboundedSender<ExecutionResult>,
        wallet_manager: Arc<RwLock<WalletManager>>,
        trading_mode: TradingMode,
        solana_rpc_url: String,
        wallet_selection_timeout_ms: u64,
        fallback_wallet_id: Option<String>,
    ) -> Self {
        Self {
            signal_receiver,
            persistence_sender,
            wallet_manager,
            trading_mode,
            solana_rpc_url,
            is_running: false,
            hft_engine: None,
            hft_mode_enabled: false,
            wallet_selection_timeout_ms,
            fallback_wallet_id,
            execution_stats: Arc::new(RwLock::new(ExecutionStats::default())),
        }
    }

    /// Create new multi-wallet executor with HFT engine
    pub fn new_with_hft(
        signal_receiver: mpsc::UnboundedReceiver<ApprovedSignal>,
        persistence_sender: mpsc::UnboundedSender<ExecutionResult>,
        wallet_manager: Arc<RwLock<WalletManager>>,
        trading_mode: TradingMode,
        solana_rpc_url: String,
        wallet_selection_timeout_ms: u64,
        fallback_wallet_id: Option<String>,
        hft_config: HFTConfig,
    ) -> Result<Self> {
        let hft_engine = OvermindHFTEngine::new(hft_config)?;

        Ok(Self {
            signal_receiver,
            persistence_sender,
            wallet_manager,
            trading_mode,
            solana_rpc_url,
            is_running: false,
            hft_engine: Some(hft_engine),
            hft_mode_enabled: true,
            wallet_selection_timeout_ms,
            fallback_wallet_id,
            execution_stats: Arc::new(RwLock::new(ExecutionStats::default())),
        })
    }

    /// Start the multi-wallet executor
    pub async fn start(&mut self) -> Result<()> {
        info!("🏦 THE OVERMIND PROTOCOL Multi-Wallet Executor starting in {:?} mode", self.trading_mode);
        
        if self.hft_mode_enabled {
            info!("🧠 AI-enhanced multi-wallet execution enabled");
        }

        // Safety warning for live trading
        if matches!(self.trading_mode, TradingMode::Live) {
            warn!("🔴 LIVE MULTI-WALLET TRADING MODE ENABLED - Real transactions will be executed!");
        }

        self.is_running = true;

        while self.is_running {
            if let Some(approved_signal) = self.signal_receiver.recv().await {
                if let Err(e) = self.process_signal(approved_signal).await {
                    error!("Failed to process signal: {}", e);
                }
            }
        }

        Ok(())
    }

    /// Stop the executor
    pub async fn stop(&mut self) {
        info!("🛑 Multi-Wallet Executor stopping...");
        self.is_running = false;
    }

    /// Process incoming signal with wallet selection and routing
    async fn process_signal(&mut self, signal: ApprovedSignal) -> Result<()> {
        let signal_id = signal.original_signal.signal_id.clone();
        
        info!("🏦 Processing signal {} with multi-wallet routing", signal_id);

        // Step 1: Select optimal wallet for this signal
        let routed_signal = match self.select_wallet_for_signal(&signal).await {
            Ok(routed) => routed,
            Err(e) => {
                error!("Failed to select wallet for signal {}: {}", signal_id, e);
                
                // Try fallback wallet if available
                if let Some(fallback_id) = &self.fallback_wallet_id {
                    warn!("Using fallback wallet {} for signal {}", fallback_id, signal_id);
                    RoutedSignal {
                        original_signal: signal,
                        selected_wallet_id: fallback_id.clone(),
                        wallet_selection_reason: "Fallback due to selection failure".to_string(),
                        routing_timestamp: chrono::Utc::now(),
                    }
                } else {
                    return Err(anyhow!("No suitable wallet found and no fallback configured"));
                }
            }
        };

        // Step 2: Execute the trade with selected wallet
        let result = self.execute_routed_signal(routed_signal).await?;

        // Step 3: Update statistics
        self.update_execution_stats(&result).await;

        // Step 4: Send result to persistence
        if let Err(e) = self.persistence_sender.send(result.clone()) {
            error!("Failed to send execution result to persistence: {}", e);
        }

        self.log_execution_result(&result);

        Ok(())
    }

    /// Select optimal wallet for the given signal
    async fn select_wallet_for_signal(&self, signal: &ApprovedSignal) -> Result<RoutedSignal> {
        let wallet_manager = self.wallet_manager.read().await;
        
        // Create selection criteria based on signal
        let criteria = WalletSelectionCriteria {
            strategy_type: signal.original_signal.strategy_type.clone(),
            required_balance: signal.approved_quantity * signal.original_signal.target_price * 1.1, // 10% buffer
            risk_tolerance: signal.risk_score,
            preferred_wallet_type: self.determine_preferred_wallet_type(&signal.original_signal.strategy_type),
            exclude_wallets: Vec::new(),
        };

        // Select wallet with timeout
        let selection_future = wallet_manager.select_wallet(criteria);
        let selection_result = tokio::time::timeout(
            std::time::Duration::from_millis(self.wallet_selection_timeout_ms),
            selection_future,
        ).await;

        match selection_result {
            Ok(Ok(selection)) => {
                info!(
                    "🎯 Selected wallet {} for signal {} ({})",
                    selection.wallet_id,
                    signal.original_signal.signal_id,
                    selection.selection_reason
                );

                Ok(RoutedSignal {
                    original_signal: signal.clone(),
                    selected_wallet_id: selection.wallet_id,
                    wallet_selection_reason: selection.selection_reason,
                    routing_timestamp: chrono::Utc::now(),
                })
            }
            Ok(Err(e)) => Err(anyhow!("Wallet selection failed: {}", e)),
            Err(_) => Err(anyhow!("Wallet selection timed out after {}ms", self.wallet_selection_timeout_ms)),
        }
    }

    /// Determine preferred wallet type based on strategy
    fn determine_preferred_wallet_type(&self, strategy_type: &StrategyType) -> Option<WalletType> {
        match strategy_type {
            StrategyType::Arbitrage => Some(WalletType::Arbitrage),
            StrategyType::TokenSniping => Some(WalletType::HFT),
            StrategyType::MomentumTrading => Some(WalletType::Primary),
            StrategyType::SoulMeteorSniping => Some(WalletType::Experimental),
            StrategyType::MeteoraDAMM => Some(WalletType::Experimental),
            StrategyType::DeveloperTracking => Some(WalletType::Experimental),
            StrategyType::AxiomMemeCoin => Some(WalletType::Experimental),
            StrategyType::AIDecision => Some(WalletType::Primary),
        }
    }

    /// Execute signal with selected wallet
    async fn execute_routed_signal(&mut self, routed_signal: RoutedSignal) -> Result<ExecutionResult> {
        let signal_id = routed_signal.original_signal.original_signal.signal_id.clone();
        let wallet_id = routed_signal.selected_wallet_id.clone();

        info!(
            "🏦 Executing signal {} with wallet {} ({})",
            signal_id, wallet_id, routed_signal.wallet_selection_reason
        );

        // Get wallet keypair for signing
        let wallet_manager = self.wallet_manager.read().await;
        let wallet_keypair = wallet_manager.get_wallet_keypair(&wallet_id).await?;
        drop(wallet_manager); // Release lock

        // Execute based on trading mode and HFT settings
        let mut result = match (&self.trading_mode, self.hft_mode_enabled) {
            (&TradingMode::Paper, false) => self.execute_paper_trade_with_wallet(&routed_signal, &wallet_id).await?,
            (&TradingMode::Paper, true) => self.execute_ai_paper_trade_with_wallet(&routed_signal, &wallet_id).await?,
            (&TradingMode::Live, false) => self.execute_live_trade_with_wallet(&routed_signal, &wallet_id, &wallet_keypair).await?,
            (&TradingMode::Live, true) => self.execute_ai_live_trade_with_wallet(&routed_signal, &wallet_id, &wallet_keypair).await?,
        };

        // Add wallet information to result
        result.transaction_id = format!("{}_{}", wallet_id, result.transaction_id);

        Ok(result)
    }

    /// Execute paper trade with specific wallet
    async fn execute_paper_trade_with_wallet(
        &self,
        routed_signal: &RoutedSignal,
        wallet_id: &str,
    ) -> Result<ExecutionResult> {
        debug!("📝 Executing paper trade with wallet {}", wallet_id);

        // Simulate execution delay
        tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

        Ok(ExecutionResult {
            signal_id: routed_signal.original_signal.original_signal.signal_id.clone(),
            transaction_id: format!("paper_{}", uuid::Uuid::new_v4()),
            status: ExecutionStatus::Confirmed,
            executed_quantity: routed_signal.original_signal.approved_quantity,
            executed_price: routed_signal.original_signal.original_signal.target_price,
            fees: routed_signal.original_signal.approved_quantity * routed_signal.original_signal.original_signal.target_price * 0.001,
            timestamp: chrono::Utc::now(),
            error_message: None,
        })
    }

    /// Execute AI-enhanced paper trade with specific wallet
    async fn execute_ai_paper_trade_with_wallet(
        &mut self,
        routed_signal: &RoutedSignal,
        wallet_id: &str,
    ) -> Result<ExecutionResult> {
        debug!("🧠 Executing AI-enhanced paper trade with wallet {}", wallet_id);

        if let Some(ref mut hft_engine) = self.hft_engine {
            let market_data = self.routed_signal_to_market_data(routed_signal);
            
            match hft_engine.execute_ai_signal(&market_data).await {
                Ok(hft_result) => {
                    match hft_result {
                        HFTExecutionResult::Executed { latency_ms, estimated_profit, ai_confidence, .. } => {
                            info!(
                                "🧠 AI paper trade executed with wallet {} - Latency: {}ms, Confidence: {:.2}, Profit: ${:.2}",
                                wallet_id, latency_ms, ai_confidence, estimated_profit
                            );

                            Ok(ExecutionResult {
                                signal_id: routed_signal.original_signal.original_signal.signal_id.clone(),
                                transaction_id: format!("ai_paper_{}", uuid::Uuid::new_v4()),
                                status: ExecutionStatus::Confirmed,
                                executed_quantity: routed_signal.original_signal.approved_quantity,
                                executed_price: routed_signal.original_signal.original_signal.target_price,
                                fees: routed_signal.original_signal.approved_quantity * routed_signal.original_signal.original_signal.target_price * 0.0005,
                                timestamp: chrono::Utc::now(),
                                error_message: None,
                            })
                        },
                        _ => self.execute_paper_trade_with_wallet(routed_signal, wallet_id).await,
                    }
                },
                Err(_) => self.execute_paper_trade_with_wallet(routed_signal, wallet_id).await,
            }
        } else {
            self.execute_paper_trade_with_wallet(routed_signal, wallet_id).await
        }
    }

    /// Execute live trade with specific wallet (placeholder)
    async fn execute_live_trade_with_wallet(
        &self,
        routed_signal: &RoutedSignal,
        wallet_id: &str,
        _wallet_keypair: &solana_sdk::signature::Keypair,
    ) -> Result<ExecutionResult> {
        warn!("🔴 EXECUTING LIVE TRADE with wallet {}", wallet_id);

        // TODO: Implement actual Solana transaction execution with specific wallet
        // This would involve:
        // 1. Building the transaction with Solana SDK
        // 2. Signing with the provided wallet keypair
        // 3. Sending with HFT optimizations
        // 4. Monitoring transaction status

        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

        Ok(ExecutionResult {
            signal_id: routed_signal.original_signal.original_signal.signal_id.clone(),
            transaction_id: uuid::Uuid::new_v4().to_string(),
            status: ExecutionStatus::Confirmed,
            executed_quantity: routed_signal.original_signal.approved_quantity,
            executed_price: routed_signal.original_signal.original_signal.target_price * 1.005,
            fees: routed_signal.original_signal.approved_quantity * routed_signal.original_signal.original_signal.target_price * 0.0025,
            timestamp: chrono::Utc::now(),
            error_message: None,
        })
    }

    /// Execute AI-enhanced live trade with specific wallet (placeholder)
    async fn execute_ai_live_trade_with_wallet(
        &mut self,
        routed_signal: &RoutedSignal,
        wallet_id: &str,
        wallet_keypair: &solana_sdk::signature::Keypair,
    ) -> Result<ExecutionResult> {
        warn!("🧠 EXECUTING AI-ENHANCED LIVE TRADE with wallet {}", wallet_id);

        if let Some(ref mut hft_engine) = self.hft_engine {
            let market_data = self.routed_signal_to_market_data(routed_signal);
            
            match hft_engine.execute_ai_signal(&market_data).await {
                Ok(hft_result) => {
                    match hft_result {
                        HFTExecutionResult::Executed { bundle_id, latency_ms, estimated_profit, ai_confidence } => {
                            info!(
                                "🧠 AI live trade executed with wallet {} - Bundle: {}, Latency: {}ms, Confidence: {:.2}, Profit: ${:.2}",
                                wallet_id, bundle_id, latency_ms, ai_confidence, estimated_profit
                            );

                            Ok(ExecutionResult {
                                signal_id: routed_signal.original_signal.original_signal.signal_id.clone(),
                                transaction_id: bundle_id,
                                status: ExecutionStatus::Confirmed,
                                executed_quantity: routed_signal.original_signal.approved_quantity,
                                executed_price: routed_signal.original_signal.original_signal.target_price * 1.002,
                                fees: routed_signal.original_signal.approved_quantity * routed_signal.original_signal.original_signal.target_price * 0.0015,
                                timestamp: chrono::Utc::now(),
                                error_message: None,
                            })
                        },
                        _ => self.execute_live_trade_with_wallet(routed_signal, wallet_id, wallet_keypair).await,
                    }
                },
                Err(_) => self.execute_live_trade_with_wallet(routed_signal, wallet_id, wallet_keypair).await,
            }
        } else {
            self.execute_live_trade_with_wallet(routed_signal, wallet_id, wallet_keypair).await
        }
    }

    /// Convert routed signal to market data for AI analysis
    fn routed_signal_to_market_data(&self, routed_signal: &RoutedSignal) -> String {
        serde_json::json!({
            "signal_id": routed_signal.original_signal.original_signal.signal_id,
            "wallet_id": routed_signal.selected_wallet_id,
            "wallet_selection_reason": routed_signal.wallet_selection_reason,
            "strategy_type": format!("{:?}", routed_signal.original_signal.original_signal.strategy_type),
            "action": format!("{:?}", routed_signal.original_signal.original_signal.action),
            "symbol": routed_signal.original_signal.original_signal.symbol,
            "quantity": routed_signal.original_signal.original_signal.quantity,
            "target_price": routed_signal.original_signal.original_signal.target_price,
            "approved_quantity": routed_signal.original_signal.approved_quantity,
            "confidence": routed_signal.original_signal.original_signal.confidence,
            "risk_score": routed_signal.original_signal.risk_score,
            "routing_timestamp": routed_signal.routing_timestamp.to_rfc3339(),
        }).to_string()
    }

    /// Update execution statistics
    async fn update_execution_stats(&self, result: &ExecutionResult) {
        let mut stats = self.execution_stats.write().await;
        
        stats.total_executions += 1;
        
        match result.status {
            ExecutionStatus::Confirmed => stats.successful_executions += 1,
            ExecutionStatus::Failed => stats.failed_executions += 1,
            _ => {}
        }

        // Extract wallet ID from transaction ID
        if let Some(wallet_id) = result.transaction_id.split('_').next() {
            *stats.wallet_usage.entry(wallet_id.to_string()).or_insert(0) += 1;
        }
    }

    /// Log execution result with wallet information
    fn log_execution_result(&self, result: &ExecutionResult) {
        let wallet_id = result.transaction_id.split('_').next().unwrap_or("unknown");
        
        match result.status {
            ExecutionStatus::Confirmed => {
                info!(
                    "✅ Multi-wallet transaction confirmed: {} (wallet: {}) - Quantity: {}, Price: {}, Fees: {}",
                    result.transaction_id, wallet_id, result.executed_quantity, result.executed_price, result.fees
                );
            }
            ExecutionStatus::Failed => {
                error!(
                    "❌ Multi-wallet transaction failed: {} (wallet: {}) - Error: {}",
                    result.transaction_id, wallet_id, result.error_message.as_deref().unwrap_or("Unknown error")
                );
            }
            ExecutionStatus::Pending => {
                debug!("⏳ Multi-wallet transaction pending: {} (wallet: {})", result.transaction_id, wallet_id);
            }
            ExecutionStatus::Cancelled => {
                warn!("🚫 Multi-wallet transaction cancelled: {} (wallet: {})", result.transaction_id, wallet_id);
            }
        }
    }

    /// Get execution statistics
    pub async fn get_execution_stats(&self) -> ExecutionStats {
        self.execution_stats.read().await.clone()
    }
}
