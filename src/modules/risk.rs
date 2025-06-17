// Risk Manager Module
// Evaluates trading signals against risk parameters

use crate::modules::strategy::TradingSignal;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use tokio::sync::mpsc;
use tracing::{debug, error, info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskParameters {
    pub max_position_size: f64,
    pub max_daily_loss: f64,
    pub min_confidence_threshold: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApprovedSignal {
    pub original_signal: TradingSignal,
    pub approved_quantity: f64,
    pub risk_score: f64,
    pub approval_timestamp: chrono::DateTime<chrono::Utc>,
}

pub struct RiskManager {
    signal_receiver: mpsc::UnboundedReceiver<TradingSignal>,
    execution_sender: mpsc::UnboundedSender<ApprovedSignal>,
    risk_params: RiskParameters,
    daily_pnl: f64,
    is_running: bool,
}

#[allow(dead_code)]
impl RiskManager {
    pub fn new(
        signal_receiver: mpsc::UnboundedReceiver<TradingSignal>,
        execution_sender: mpsc::UnboundedSender<ApprovedSignal>,
        risk_params: RiskParameters,
    ) -> Self {
        Self {
            signal_receiver,
            execution_sender,
            risk_params,
            daily_pnl: 0.0,
            is_running: false,
        }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!(
            "🛡️ RiskManager starting with params: {:?}",
            self.risk_params
        );
        self.is_running = true;

        while self.is_running {
            if let Some(signal) = self.signal_receiver.recv().await {
                self.evaluate_signal(signal).await?;
            }
        }

        Ok(())
    }

    pub async fn stop(&mut self) {
        info!("🛑 RiskManager stopping...");
        self.is_running = false;
    }

    async fn evaluate_signal(&mut self, signal: TradingSignal) -> Result<()> {
        debug!("Evaluating signal: {}", signal.signal_id);

        // Check confidence threshold
        if signal.confidence < self.risk_params.min_confidence_threshold {
            warn!(
                "Signal {} rejected: confidence {} below threshold {}",
                signal.signal_id, signal.confidence, self.risk_params.min_confidence_threshold
            );
            return Ok(());
        }

        // Check position size limits
        let approved_quantity = self.check_position_limits(&signal)?;
        if approved_quantity <= 0.0 {
            warn!(
                "Signal {} rejected: position size limits exceeded",
                signal.signal_id
            );
            return Ok(());
        }

        // Check daily loss limits
        if !self.check_daily_loss_limits()? {
            warn!(
                "Signal {} rejected: daily loss limits exceeded",
                signal.signal_id
            );
            return Ok(());
        }

        // Calculate risk score
        let risk_score = self.calculate_risk_score(&signal)?;

        // Approve signal
        let approved_signal = ApprovedSignal {
            original_signal: signal.clone(),
            approved_quantity,
            risk_score,
            approval_timestamp: chrono::Utc::now(),
        };

        self.send_approved_signal(approved_signal).await?;
        info!(
            "✅ Signal {} approved with quantity {}",
            signal.signal_id, approved_quantity
        );

        Ok(())
    }

    fn check_position_limits(&self, signal: &TradingSignal) -> Result<f64> {
        if signal.quantity > self.risk_params.max_position_size {
            return Ok(self.risk_params.max_position_size);
        }
        Ok(signal.quantity)
    }

    fn check_daily_loss_limits(&self) -> Result<bool> {
        Ok(self.daily_pnl > -self.risk_params.max_daily_loss)
    }

    fn calculate_risk_score(&self, signal: &TradingSignal) -> Result<f64> {
        let mut risk_score = 0.0;

        // Base risk from confidence (lower confidence = higher risk)
        risk_score += (1.0 - signal.confidence) * 0.4;

        // Position size risk
        let position_ratio = signal.quantity / self.risk_params.max_position_size;
        risk_score += position_ratio * 0.3;

        // Strategy type risk
        risk_score += match signal.strategy_type {
            crate::modules::strategy::StrategyType::TokenSniping => 0.3,
            crate::modules::strategy::StrategyType::Arbitrage => 0.1,
            crate::modules::strategy::StrategyType::MomentumTrading => 0.2,
            crate::modules::strategy::StrategyType::SoulMeteorSniping => 0.25,
            crate::modules::strategy::StrategyType::MeteoraDAMM => 0.8, // Very high risk
            crate::modules::strategy::StrategyType::DeveloperTracking => 0.7, // High risk
            crate::modules::strategy::StrategyType::AxiomMemeCoin => 0.9, // Extreme risk
            crate::modules::strategy::StrategyType::AIDecision => 0.7, // AI decisions have moderate-high risk
        };

        Ok(risk_score.min(1.0))
    }

    async fn send_approved_signal(&self, signal: ApprovedSignal) -> Result<()> {
        if let Err(e) = self.execution_sender.send(signal) {
            error!("Failed to send approved signal: {}", e);
            return Err(anyhow::anyhow!("Failed to send approved signal"));
        }
        Ok(())
    }

    pub fn update_daily_pnl(&mut self, pnl_change: f64) {
        self.daily_pnl += pnl_change;
    }

    pub fn get_daily_pnl(&self) -> f64 {
        self.daily_pnl
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    // use crate::modules::strategy::{StrategyType, TradeAction};

    #[tokio::test]
    async fn test_risk_manager_creation() {
        let (_signal_tx, signal_rx) = mpsc::unbounded_channel();
        let (execution_tx, _execution_rx) = mpsc::unbounded_channel();

        let risk_params = RiskParameters {
            max_position_size: 1000.0,
            max_daily_loss: 500.0,
            min_confidence_threshold: 0.6,
        };

        let manager = RiskManager::new(signal_rx, execution_tx, risk_params);
        assert!(!manager.is_running);
        assert_eq!(manager.daily_pnl, 0.0);
    }
}
