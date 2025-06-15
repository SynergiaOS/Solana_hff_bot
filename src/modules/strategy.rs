// Strategy Engine Module
// Analyzes market data and generates trading signals

use crate::modules::data_ingestor::MarketData;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use tokio::sync::mpsc;
use tracing::{debug, error, info};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingSignal {
    pub signal_id: String,
    pub symbol: String,
    pub action: TradeAction,
    pub quantity: f64,
    pub target_price: f64,
    pub confidence: f64,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub strategy_type: StrategyType,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TradeAction {
    Buy,
    Sell,
    Hold,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum StrategyType {
    TokenSniping,
    Arbitrage,
    MomentumTrading,
    SoulMeteorSniping,
    MeteoraDAMM,
    DeveloperTracking,
    AxiomMemeCoin,
}

pub struct StrategyEngine {
    market_data_receiver: mpsc::UnboundedReceiver<MarketData>,
    signal_sender: mpsc::UnboundedSender<TradingSignal>,
    is_running: bool,
}

#[allow(dead_code)]
impl StrategyEngine {
    pub fn new(
        market_data_receiver: mpsc::UnboundedReceiver<MarketData>,
        signal_sender: mpsc::UnboundedSender<TradingSignal>,
    ) -> Self {
        Self {
            market_data_receiver,
            signal_sender,
            is_running: false,
        }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("🧠 StrategyEngine starting...");
        self.is_running = true;

        while self.is_running {
            if let Some(market_data) = self.market_data_receiver.recv().await {
                self.process_market_data(market_data).await?;
            }
        }

        Ok(())
    }

    pub async fn stop(&mut self) {
        info!("🛑 StrategyEngine stopping...");
        self.is_running = false;
    }

    async fn process_market_data(&self, data: MarketData) -> Result<()> {
        debug!("Processing market data for symbol: {}", data.symbol);

        // TODO: Implement actual trading strategies
        // For now, generate a simple signal occasionally
        if data.price > 105.0 {
            // Simple condition instead of random
            let quantity = 100.0;

            // Estimate liquidity (in a real implementation, this would come from market data)
            let estimated_liquidity = data.volume * 0.1; // Simplified estimation

            // Calculate expected slippage
            let slippage = self.calculate_slippage(quantity, estimated_liquidity, data.price);

            // Adjust target price based on slippage
            let target_price = data.price * (1.01 + slippage);

            let signal = TradingSignal {
                signal_id: uuid::Uuid::new_v4().to_string(),
                symbol: data.symbol,
                action: TradeAction::Buy,
                quantity,
                target_price,
                confidence: 0.7 * (1.0 - slippage), // Lower confidence with higher slippage
                timestamp: chrono::Utc::now(),
                strategy_type: StrategyType::TokenSniping,
            };

            if let Err(e) = self.signal_sender.send(signal) {
                error!("Failed to send trading signal: {}", e);
            }
        }

        Ok(())
    }

    /// Calculates expected slippage for a given order size and liquidity
    pub fn calculate_slippage(&self, order_size: f64, liquidity: f64, price: f64) -> f64 {
        // Guard against division by zero
        if liquidity <= 0.0 {
            return 1.0; // 100% slippage for zero liquidity
        }

        // Calculate impact ratio (order size relative to available liquidity)
        let impact_ratio = order_size / liquidity;

        // Apply non-linear slippage model
        // Small orders: minimal slippage
        // Large orders: exponentially increasing slippage
        let base_slippage = impact_ratio.min(0.5);

        // Apply additional factors based on price volatility
        // This is a simplified model - can be enhanced with historical volatility
        let price_factor = if price < 0.01 {
            // Micro-cap tokens have higher slippage
            1.5
        } else if price < 1.0 {
            // Low-priced tokens
            1.2
        } else {
            // Higher-priced tokens
            1.0
        };

        // Return slippage as a percentage (0.0 to 1.0)
        (base_slippage * price_factor).min(1.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_strategy_engine_creation() {
        let (_market_tx, market_rx) = mpsc::unbounded_channel();
        let (signal_tx, _signal_rx) = mpsc::unbounded_channel();

        let engine = StrategyEngine::new(market_rx, signal_tx);
        assert!(!engine.is_running);
    }

    #[test]
    fn test_calculate_slippage() {
        // Create a minimal StrategyEngine for testing
        let (_tx_market, rx_market) = mpsc::unbounded_channel();
        let (tx_signal, _) = mpsc::unbounded_channel();
        let strategy = StrategyEngine::new(rx_market, tx_signal);

        // Test case 1: Zero liquidity should result in 100% slippage
        assert_eq!(strategy.calculate_slippage(100.0, 0.0, 10.0), 1.0);

        // Test case 2: Small order relative to liquidity
        let small_order_slippage = strategy.calculate_slippage(100.0, 10000.0, 10.0);
        assert!(small_order_slippage < 0.05); // Should be less than 5%

        // Test case 3: Large order relative to liquidity
        let large_order_slippage = strategy.calculate_slippage(5000.0, 10000.0, 10.0);
        assert!(large_order_slippage > 0.2); // Should be significant

        // Test case 4: Micro-cap token (price < 0.01)
        let micro_cap_slippage = strategy.calculate_slippage(100.0, 1000.0, 0.001);
        let normal_token_slippage = strategy.calculate_slippage(100.0, 1000.0, 10.0);
        assert!(micro_cap_slippage > normal_token_slippage); // Should have higher slippage
    }
}
