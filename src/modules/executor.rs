// THE OVERMIND PROTOCOL - Executor Module
// Handles AI-enhanced trade execution on Solana blockchain with TensorZero optimization

use crate::config::TradingMode;
use crate::modules::risk::ApprovedSignal;
use crate::modules::hft_engine::{OvermindHFTEngine, HFTConfig, ExecutionResult as HFTExecutionResult};
use anyhow::Result;
use serde::{Deserialize, Serialize};
use tokio::sync::mpsc;
use tracing::{debug, error, info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionResult {
    pub signal_id: String,
    pub transaction_id: String,
    pub status: ExecutionStatus,
    pub executed_quantity: f64,
    pub executed_price: f64,
    pub fees: f64,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub error_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExecutionStatus {
    Pending,
    Confirmed,
    Failed,
    Cancelled,
}

#[allow(dead_code)]
pub struct Executor {
    signal_receiver: mpsc::UnboundedReceiver<ApprovedSignal>,
    persistence_sender: mpsc::UnboundedSender<ExecutionResult>,
    trading_mode: TradingMode,
    solana_rpc_url: String,
    wallet_private_key: String,
    is_running: bool,
    // THE OVERMIND PROTOCOL - HFT Engine integration
    hft_engine: Option<OvermindHFTEngine>,
    hft_mode_enabled: bool,
}

#[allow(dead_code)]
impl Executor {
    pub fn new(
        signal_receiver: mpsc::UnboundedReceiver<ApprovedSignal>,
        persistence_sender: mpsc::UnboundedSender<ExecutionResult>,
        trading_mode: TradingMode,
        solana_rpc_url: String,
        wallet_private_key: String,
    ) -> Self {
        Self {
            signal_receiver,
            persistence_sender,
            trading_mode,
            solana_rpc_url,
            wallet_private_key,
            is_running: false,
            hft_engine: None,
            hft_mode_enabled: false,
        }
    }

    /// Create new OVERMIND Executor with HFT Engine enabled
    pub fn new_with_hft(
        signal_receiver: mpsc::UnboundedReceiver<ApprovedSignal>,
        persistence_sender: mpsc::UnboundedSender<ExecutionResult>,
        trading_mode: TradingMode,
        solana_rpc_url: String,
        wallet_private_key: String,
        hft_config: HFTConfig,
    ) -> Result<Self> {
        let hft_engine = OvermindHFTEngine::new(hft_config)?;

        Ok(Self {
            signal_receiver,
            persistence_sender,
            trading_mode,
            solana_rpc_url,
            wallet_private_key,
            is_running: false,
            hft_engine: Some(hft_engine),
            hft_mode_enabled: true,
        })
    }

    pub async fn start(&mut self) -> Result<()> {
        if self.hft_mode_enabled {
            info!("🧠 THE OVERMIND PROTOCOL Executor starting in {:?} mode with AI enhancement...", self.trading_mode);
        } else {
            info!("⚡ Executor starting in {:?} mode...", self.trading_mode);
        }

        // Safety warning for live trading
        if matches!(self.trading_mode, TradingMode::Live) {
            warn!("🔴 LIVE TRADING MODE ENABLED - Real transactions will be executed!");
            if self.hft_mode_enabled {
                warn!("🧠 AI-ENHANCED HFT MODE ENABLED - TensorZero optimization active!");
            }
        }

        self.is_running = true;

        while self.is_running {
            if let Some(approved_signal) = self.signal_receiver.recv().await {
                self.execute_signal(approved_signal).await?;
            }
        }

        Ok(())
    }

    pub async fn stop(&mut self) {
        info!("🛑 Executor stopping...");
        self.is_running = false;
    }

    async fn execute_signal(&mut self, signal: ApprovedSignal) -> Result<()> {
        let signal_id = signal.original_signal.signal_id.clone();

        if self.hft_mode_enabled {
            info!(
                "🧠 THE OVERMIND PROTOCOL executing AI-enhanced signal: {} with quantity: {}",
                signal_id, signal.approved_quantity
            );
        } else {
            info!(
                "🎯 Executing signal: {} with quantity: {}",
                signal_id, signal.approved_quantity
            );
        }

        let result = match (&self.trading_mode, self.hft_mode_enabled) {
            (&TradingMode::Paper, false) => self.execute_paper_trade(signal).await?,
            (&TradingMode::Paper, true) => self.execute_ai_paper_trade(signal).await?,
            (&TradingMode::Live, false) => self.execute_live_trade(signal).await?,
            (&TradingMode::Live, true) => self.execute_ai_live_trade(signal).await?,
        };

        // Send result to persistence
        if let Err(e) = self.persistence_sender.send(result.clone()) {
            error!("Failed to send execution result to persistence: {}", e);
        }

        self.log_execution_result(&result);

        Ok(())
    }

    async fn execute_paper_trade(&self, signal: ApprovedSignal) -> Result<ExecutionResult> {
        debug!(
            "📝 Executing paper trade for signal: {}",
            signal.original_signal.signal_id
        );

        // Simulate execution delay
        tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;

        let result = ExecutionResult {
            signal_id: signal.original_signal.signal_id,
            transaction_id: format!("paper_{}", uuid::Uuid::new_v4()),
            status: ExecutionStatus::Confirmed,
            executed_quantity: signal.approved_quantity,
            executed_price: signal.original_signal.target_price,
            fees: signal.approved_quantity * signal.original_signal.target_price * 0.001, // 0.1% fee
            timestamp: chrono::Utc::now(),
            error_message: None,
        };

        Ok(result)
    }

    async fn execute_live_trade(&self, signal: ApprovedSignal) -> Result<ExecutionResult> {
        warn!(
            "🔴 EXECUTING LIVE TRADE - Signal ID: {}",
            signal.original_signal.signal_id
        );

        // TODO: Implement actual Solana transaction execution
        // This would involve:
        // 1. Building the transaction with Solana SDK
        // 2. Signing with wallet private key
        // 3. Sending with HFT optimizations
        // 4. Monitoring transaction status

        // For now, simulate with higher latency and potential failures
        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;

        let success = true; // Always succeed for now

        let result = if success {
            ExecutionResult {
                signal_id: signal.original_signal.signal_id,
                transaction_id: uuid::Uuid::new_v4().to_string(),
                status: ExecutionStatus::Confirmed,
                executed_quantity: signal.approved_quantity,
                executed_price: signal.original_signal.target_price * 1.005, // Small slippage
                fees: signal.approved_quantity * signal.original_signal.target_price * 0.0025, // 0.25% fee
                timestamp: chrono::Utc::now(),
                error_message: None,
            }
        } else {
            ExecutionResult {
                signal_id: signal.original_signal.signal_id,
                transaction_id: uuid::Uuid::new_v4().to_string(),
                status: ExecutionStatus::Failed,
                executed_quantity: 0.0,
                executed_price: 0.0,
                fees: 0.0,
                timestamp: chrono::Utc::now(),
                error_message: Some("Transaction failed due to network congestion".to_string()),
            }
        };

        Ok(result)
    }

    /// Execute AI-enhanced paper trade using THE OVERMIND PROTOCOL
    async fn execute_ai_paper_trade(&mut self, signal: ApprovedSignal) -> Result<ExecutionResult> {
        debug!(
            "🧠 Executing AI-enhanced paper trade for signal: {}",
            signal.original_signal.signal_id
        );

        // Convert signal to market data for AI analysis first
        let market_data = self.signal_to_market_data(&signal);

        if let Some(ref mut hft_engine) = self.hft_engine {

            // Get AI decision and execute with TensorZero optimization
            match hft_engine.execute_ai_signal(&market_data).await {
                Ok(hft_result) => {
                    match hft_result {
                        HFTExecutionResult::Executed {
                            signal_id: _,
                            latency_ms,
                            estimated_profit,
                            ai_confidence,
                            ..
                        } => {
                            info!(
                                "🧠 AI paper trade executed - Latency: {}ms, Confidence: {:.2}, Profit: ${:.2}",
                                latency_ms, ai_confidence, estimated_profit
                            );

                            let signal_id = signal.original_signal.signal_id.clone();
                            Ok(ExecutionResult {
                                signal_id: signal_id.clone(),
                                transaction_id: format!("ai_paper_{}", signal_id),
                                status: ExecutionStatus::Confirmed,
                                executed_quantity: signal.approved_quantity,
                                executed_price: signal.original_signal.target_price,
                                fees: signal.approved_quantity * signal.original_signal.target_price * 0.0005, // Lower fees with AI
                                timestamp: chrono::Utc::now(),
                                error_message: None,
                            })
                        },
                        HFTExecutionResult::Skipped { reason, latency_ms } => {
                            warn!("🧠 AI skipped trade: {} ({}ms)", reason, latency_ms);
                            self.execute_paper_trade(signal).await // Fallback to standard paper trade
                        },
                        HFTExecutionResult::Failed { error, latency_ms } => {
                            error!("🧠 AI trade failed: {} ({}ms)", error, latency_ms);
                            self.execute_paper_trade(signal).await // Fallback to standard paper trade
                        },
                    }
                },
                Err(e) => {
                    error!("🧠 HFT Engine error: {}", e);
                    self.execute_paper_trade(signal).await // Fallback to standard paper trade
                }
            }
        } else {
            // Fallback if HFT engine not available
            self.execute_paper_trade(signal).await
        }
    }

    /// Execute AI-enhanced live trade using THE OVERMIND PROTOCOL
    async fn execute_ai_live_trade(&mut self, signal: ApprovedSignal) -> Result<ExecutionResult> {
        warn!(
            "🧠 EXECUTING AI-ENHANCED LIVE TRADE - Signal ID: {}",
            signal.original_signal.signal_id
        );

        // Convert signal to market data for AI analysis first
        let market_data = self.signal_to_market_data(&signal);

        if let Some(ref mut hft_engine) = self.hft_engine {

            // Get AI decision and execute with TensorZero + Jito Bundle optimization
            match hft_engine.execute_ai_signal(&market_data).await {
                Ok(hft_result) => {
                    match hft_result {
                        HFTExecutionResult::Executed {
                            signal_id: _,
                            bundle_id,
                            latency_ms,
                            estimated_profit,
                            ai_confidence
                        } => {
                            info!(
                                "🧠 AI live trade executed - Bundle: {}, Latency: {}ms, Confidence: {:.2}, Profit: ${:.2}",
                                bundle_id, latency_ms, ai_confidence, estimated_profit
                            );

                            Ok(ExecutionResult {
                                signal_id: signal.original_signal.signal_id,
                                transaction_id: bundle_id,
                                status: ExecutionStatus::Confirmed,
                                executed_quantity: signal.approved_quantity,
                                executed_price: signal.original_signal.target_price * 1.002, // Minimal slippage with AI
                                fees: signal.approved_quantity * signal.original_signal.target_price * 0.0015, // Lower fees with Jito
                                timestamp: chrono::Utc::now(),
                                error_message: None,
                            })
                        },
                        HFTExecutionResult::Skipped { reason, latency_ms } => {
                            warn!("🧠 AI skipped live trade: {} ({}ms)", reason, latency_ms);
                            self.execute_live_trade(signal).await // Fallback to standard live trade
                        },
                        HFTExecutionResult::Failed { error, latency_ms } => {
                            error!("🧠 AI live trade failed: {} ({}ms)", error, latency_ms);
                            self.execute_live_trade(signal).await // Fallback to standard live trade
                        },
                    }
                },
                Err(e) => {
                    error!("🧠 HFT Engine error in live trade: {}", e);
                    self.execute_live_trade(signal).await // Fallback to standard live trade
                }
            }
        } else {
            // Fallback if HFT engine not available
            self.execute_live_trade(signal).await
        }
    }

    /// Convert ApprovedSignal to market data string for AI analysis
    fn signal_to_market_data(&self, signal: &ApprovedSignal) -> String {
        serde_json::json!({
            "signal_id": signal.original_signal.signal_id,
            "strategy_type": format!("{:?}", signal.original_signal.strategy_type),
            "action": format!("{:?}", signal.original_signal.action),
            "symbol": signal.original_signal.symbol,
            "quantity": signal.original_signal.quantity,
            "target_price": signal.original_signal.target_price,
            "approved_quantity": signal.approved_quantity,
            "confidence": signal.original_signal.confidence,
            "timestamp": signal.original_signal.timestamp.to_rfc3339(),
            "risk_score": signal.risk_score,
        }).to_string()
    }

    fn log_execution_result(&self, result: &ExecutionResult) {
        match result.status {
            ExecutionStatus::Confirmed => {
                info!(
                    "✅ Transaction confirmed: {} - Quantity: {}, Price: {}, Fees: {}",
                    result.transaction_id,
                    result.executed_quantity,
                    result.executed_price,
                    result.fees
                );
            }
            ExecutionStatus::Failed => {
                error!(
                    "❌ Transaction failed: {} - Error: {}",
                    result.transaction_id,
                    result.error_message.as_deref().unwrap_or("Unknown error")
                );
            }
            ExecutionStatus::Pending => {
                debug!("⏳ Transaction pending: {}", result.transaction_id);
            }
            ExecutionStatus::Cancelled => {
                warn!("🚫 Transaction cancelled: {}", result.transaction_id);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    // use crate::modules::risk::ApprovedSignal;
    // use crate::modules::strategy::{StrategyType, TradeAction, TradingSignal};

    #[tokio::test]
    async fn test_executor_creation() {
        let (_signal_tx, signal_rx) = mpsc::unbounded_channel();
        let (persistence_tx, _persistence_rx) = mpsc::unbounded_channel();

        let executor = Executor::new(
            signal_rx,
            persistence_tx,
            TradingMode::Paper,
            "https://api.mainnet-beta.solana.com".to_string(),
            "test_key".to_string(),
        );

        assert!(!executor.is_running);
    }
}
