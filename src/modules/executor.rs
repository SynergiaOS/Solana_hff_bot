// Executor Module
// Handles trade execution on Solana blockchain

use crate::config::TradingMode;
use crate::modules::risk::ApprovedSignal;
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

pub struct Executor {
    signal_receiver: mpsc::UnboundedReceiver<ApprovedSignal>,
    persistence_sender: mpsc::UnboundedSender<ExecutionResult>,
    trading_mode: TradingMode,
    solana_rpc_url: String,
    wallet_private_key: String,
    is_running: bool,
}

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
        }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("⚡ Executor starting in {:?} mode...", self.trading_mode);

        // Safety warning for live trading
        if matches!(self.trading_mode, TradingMode::Live) {
            warn!("🔴 LIVE TRADING MODE ENABLED - Real transactions will be executed!");
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

    async fn execute_signal(&self, signal: ApprovedSignal) -> Result<()> {
        let signal_id = signal.original_signal.signal_id.clone();
        info!(
            "🎯 Executing signal: {} with quantity: {}",
            signal_id, signal.approved_quantity
        );

        let result = match self.trading_mode {
            TradingMode::Paper => self.execute_paper_trade(signal).await?,
            TradingMode::Live => self.execute_live_trade(signal).await?,
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
