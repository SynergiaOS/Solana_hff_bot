//! MEV Arbitrage Strategy Module
//!
//! Advanced MEV (Maximal Extractable Value) arbitrage strategy that identifies
//! and exploits price differences across multiple DEXes on Solana.
//! This strategy focuses on atomic arbitrage opportunities with minimal risk.

use crate::modules::strategy::{StrategyType, TradeAction, TradingSignal};
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tokio::sync::mpsc;
use tracing::{debug, info};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MEVOpportunity {
    pub opportunity_id: String,
    pub token_mint: String,
    pub buy_dex: DexType,
    pub sell_dex: DexType,
    pub buy_price: f64,
    pub sell_price: f64,
    pub profit_percentage: f64,
    pub max_trade_size: f64,
    pub estimated_gas_cost: f64,
    pub confidence_score: f64,
    pub expiry_time: DateTime<Utc>,
    pub liquidity_depth: LiquidityDepth,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum DexType {
    Raydium,
    Jupiter,
    Orca,
    Serum,
    Meteora,
    Phoenix,
    Lifinity,
    Aldrin,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquidityDepth {
    pub buy_side_depth: f64,
    pub sell_side_depth: f64,
    pub spread_percentage: f64,
    pub volume_24h: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriceData {
    pub dex: DexType,
    pub price: f64,
    pub liquidity: f64,
    pub timestamp: DateTime<Utc>,
    pub volume_24h: f64,
    pub bid: f64,
    pub ask: f64,
}

pub struct MEVArbitrageStrategy {
    price_feeds: HashMap<String, Vec<PriceData>>,
    opportunity_sender: mpsc::UnboundedSender<MEVOpportunity>,
    signal_sender: mpsc::UnboundedSender<TradingSignal>,
    config: MEVConfig,
    active_opportunities: Vec<MEVOpportunity>,
}

#[derive(Debug, Clone)]
pub struct MEVConfig {
    pub min_profit_percentage: f64,
    pub max_trade_size_sol: f64,
    pub max_gas_cost_sol: f64,
    pub min_liquidity_depth: f64,
    pub opportunity_timeout_seconds: u64,
    pub supported_dexes: Vec<DexType>,
    pub min_confidence_score: f64,
}

impl Default for MEVConfig {
    fn default() -> Self {
        Self {
            min_profit_percentage: 0.5,      // 0.5% minimum profit
            max_trade_size_sol: 100.0,       // 100 SOL max per trade
            max_gas_cost_sol: 0.1,           // 0.1 SOL max gas cost
            min_liquidity_depth: 1000.0,     // 1000 SOL minimum liquidity
            opportunity_timeout_seconds: 30, // 30 seconds max opportunity lifetime
            supported_dexes: vec![
                DexType::Raydium,
                DexType::Jupiter,
                DexType::Orca,
                DexType::Serum,
                DexType::Meteora,
            ],
            min_confidence_score: 0.7, // 70% minimum confidence
        }
    }
}

impl MEVArbitrageStrategy {
    pub fn new(
        opportunity_sender: mpsc::UnboundedSender<MEVOpportunity>,
        signal_sender: mpsc::UnboundedSender<TradingSignal>,
        config: Option<MEVConfig>,
    ) -> Self {
        Self {
            price_feeds: HashMap::new(),
            opportunity_sender,
            signal_sender,
            config: config.unwrap_or_default(),
            active_opportunities: Vec::new(),
        }
    }

    /// Update price data from a specific DEX
    pub async fn update_price_data(
        &mut self,
        token_mint: String,
        price_data: PriceData,
    ) -> Result<()> {
        let prices = self
            .price_feeds
            .entry(token_mint.clone())
            .or_insert_with(Vec::new);

        // Remove old price data (older than 1 minute)
        let cutoff_time = Utc::now() - chrono::Duration::minutes(1);
        prices.retain(|p| p.timestamp > cutoff_time);

        // Add new price data
        prices.push(price_data);

        // Check for arbitrage opportunities
        self.scan_for_opportunities(&token_mint).await?;

        Ok(())
    }

    /// Scan for MEV arbitrage opportunities
    async fn scan_for_opportunities(&mut self, token_mint: &str) -> Result<()> {
        let prices = match self.price_feeds.get(token_mint) {
            Some(prices) if prices.len() >= 2 => prices,
            _ => return Ok(()), // Need at least 2 price sources
        };

        // Find best buy and sell opportunities
        let mut best_buy: Option<&PriceData> = None;
        let mut best_sell: Option<&PriceData> = None;

        for price in prices {
            // Find lowest ask (best buy price)
            if best_buy.is_none() || price.ask < best_buy.unwrap().ask {
                if price.liquidity >= self.config.min_liquidity_depth {
                    best_buy = Some(price);
                }
            }

            // Find highest bid (best sell price)
            if best_sell.is_none() || price.bid > best_sell.unwrap().bid {
                if price.liquidity >= self.config.min_liquidity_depth {
                    best_sell = Some(price);
                }
            }
        }

        if let (Some(buy), Some(sell)) = (best_buy, best_sell) {
            // Calculate potential profit
            let profit_percentage = ((sell.bid - buy.ask) / buy.ask) * 100.0;

            if profit_percentage >= self.config.min_profit_percentage {
                let opportunity = self
                    .create_mev_opportunity(token_mint.to_string(), buy, sell, profit_percentage)
                    .await?;

                if opportunity.confidence_score >= self.config.min_confidence_score {
                    info!(
                        "🎯 MEV Opportunity found: {:.2}% profit on {}",
                        profit_percentage, token_mint
                    );

                    // Send opportunity for execution
                    self.opportunity_sender
                        .send(opportunity.clone())
                        .context("Failed to send MEV opportunity")?;

                    // Generate trading signal
                    let signal = self.create_trading_signal(&opportunity).await?;
                    self.signal_sender
                        .send(signal)
                        .context("Failed to send trading signal")?;

                    self.active_opportunities.push(opportunity);
                }
            }
        }

        Ok(())
    }

    /// Create MEV opportunity from price data
    async fn create_mev_opportunity(
        &self,
        token_mint: String,
        buy_price_data: &PriceData,
        sell_price_data: &PriceData,
        profit_percentage: f64,
    ) -> Result<MEVOpportunity> {
        // Calculate maximum trade size based on liquidity
        let max_trade_size = (buy_price_data.liquidity.min(sell_price_data.liquidity) * 0.1)
            .min(self.config.max_trade_size_sol);

        // Estimate gas costs (simplified)
        let estimated_gas_cost = 0.01 + (max_trade_size * 0.0001); // Base + proportional

        // Calculate confidence score
        let confidence_score =
            self.calculate_confidence_score(buy_price_data, sell_price_data, profit_percentage);

        // Create liquidity depth analysis
        let liquidity_depth = LiquidityDepth {
            buy_side_depth: buy_price_data.liquidity,
            sell_side_depth: sell_price_data.liquidity,
            spread_percentage: ((sell_price_data.ask - buy_price_data.bid) / buy_price_data.bid)
                * 100.0,
            volume_24h: (buy_price_data.volume_24h + sell_price_data.volume_24h) / 2.0,
        };

        Ok(MEVOpportunity {
            opportunity_id: uuid::Uuid::new_v4().to_string(),
            token_mint,
            buy_dex: buy_price_data.dex.clone(),
            sell_dex: sell_price_data.dex.clone(),
            buy_price: buy_price_data.ask,
            sell_price: sell_price_data.bid,
            profit_percentage,
            max_trade_size,
            estimated_gas_cost,
            confidence_score,
            expiry_time: Utc::now()
                + chrono::Duration::seconds(self.config.opportunity_timeout_seconds as i64),
            liquidity_depth,
        })
    }

    /// Calculate confidence score for the opportunity
    fn calculate_confidence_score(
        &self,
        buy_data: &PriceData,
        sell_data: &PriceData,
        profit_percentage: f64,
    ) -> f64 {
        let mut score = 0.0;

        // Profit margin score (higher profit = higher confidence)
        score += (profit_percentage / 10.0).min(0.3);

        // Liquidity score
        let min_liquidity = buy_data.liquidity.min(sell_data.liquidity);
        score += (min_liquidity / 10000.0).min(0.25);

        // Volume score
        let avg_volume = (buy_data.volume_24h + sell_data.volume_24h) / 2.0;
        score += (avg_volume / 100000.0).min(0.2);

        // Time freshness score
        let now = Utc::now();
        let buy_age = (now - buy_data.timestamp).num_seconds() as f64;
        let sell_age = (now - sell_data.timestamp).num_seconds() as f64;
        let max_age = buy_age.max(sell_age);
        score += (1.0 - (max_age / 60.0)).max(0.0).min(0.25); // Fresher = better

        score.min(1.0)
    }

    /// Create trading signal from MEV opportunity
    async fn create_trading_signal(&self, opportunity: &MEVOpportunity) -> Result<TradingSignal> {
        Ok(TradingSignal {
            signal_id: uuid::Uuid::new_v4().to_string(),
            symbol: opportunity.token_mint.clone(),
            action: TradeAction::Buy, // Start with buy on cheaper DEX
            quantity: opportunity.max_trade_size,
            target_price: opportunity.buy_price,
            confidence: opportunity.confidence_score,
            timestamp: Utc::now(),
            strategy_type: StrategyType::MEVArbitrage,
        })
    }

    /// Clean up expired opportunities
    pub async fn cleanup_expired_opportunities(&mut self) {
        let now = Utc::now();
        let initial_count = self.active_opportunities.len();

        self.active_opportunities
            .retain(|opp| opp.expiry_time > now);

        let removed_count = initial_count - self.active_opportunities.len();
        if removed_count > 0 {
            debug!("Cleaned up {} expired MEV opportunities", removed_count);
        }
    }

    /// Get active opportunities count
    pub fn get_active_opportunities_count(&self) -> usize {
        self.active_opportunities.len()
    }

    /// Get strategy statistics
    pub fn get_strategy_stats(&self) -> MEVStrategyStats {
        let total_opportunities = self.active_opportunities.len();
        let avg_profit = if total_opportunities > 0 {
            self.active_opportunities
                .iter()
                .map(|opp| opp.profit_percentage)
                .sum::<f64>()
                / total_opportunities as f64
        } else {
            0.0
        };

        MEVStrategyStats {
            active_opportunities: total_opportunities,
            average_profit_percentage: avg_profit,
            total_tokens_monitored: self.price_feeds.len(),
            supported_dexes: self.config.supported_dexes.len(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MEVStrategyStats {
    pub active_opportunities: usize,
    pub average_profit_percentage: f64,
    pub total_tokens_monitored: usize,
    pub supported_dexes: usize,
}
