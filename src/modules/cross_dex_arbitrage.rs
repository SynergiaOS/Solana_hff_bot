//! Cross-DEX Arbitrage Strategy Module
//!
//! Specialized strategy for identifying and executing arbitrage opportunities
//! across different Solana DEXes with advanced routing and execution optimization.

use crate::modules::mev_arbitrage::{DexType, PriceData};
use crate::modules::strategy::{StrategyType, TradeAction, TradingSignal};
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap};
use tokio::sync::mpsc;
use tracing::{debug, info};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CrossDexOpportunity {
    pub opportunity_id: String,
    pub token_mint: String,
    pub arbitrage_path: ArbitragePath,
    pub expected_profit_sol: f64,
    pub profit_percentage: f64,
    pub execution_complexity: ExecutionComplexity,
    pub risk_score: f64,
    pub estimated_execution_time_ms: u64,
    pub required_capital_sol: f64,
    pub confidence_score: f64,
    pub discovery_time: DateTime<Utc>,
    pub expiry_time: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArbitragePath {
    pub steps: Vec<ArbitrageStep>,
    pub total_hops: usize,
    pub estimated_slippage: f64,
    pub estimated_fees: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArbitrageStep {
    pub step_number: usize,
    pub dex: DexType,
    pub action: TradeAction,
    pub input_token: String,
    pub output_token: String,
    pub input_amount: f64,
    pub expected_output: f64,
    pub price_impact: f64,
    pub estimated_gas: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExecutionComplexity {
    Simple,     // Direct A->B arbitrage
    Medium,     // 2-3 hop arbitrage
    Complex,    // 4+ hop arbitrage
    MultiToken, // Multiple token pairs
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DexPairData {
    pub dex_a: DexType,
    pub dex_b: DexType,
    pub price_difference: f64,
    pub liquidity_ratio: f64,
    pub volume_ratio: f64,
    pub historical_reliability: f64,
}

pub struct CrossDexArbitrageStrategy {
    price_matrix: HashMap<String, BTreeMap<DexType, PriceData>>,
    opportunity_sender: mpsc::UnboundedSender<CrossDexOpportunity>,
    signal_sender: mpsc::UnboundedSender<TradingSignal>,
    config: CrossDexConfig,
    active_opportunities: Vec<CrossDexOpportunity>,
    dex_performance_metrics: HashMap<DexType, DexPerformanceMetrics>,
}

#[derive(Debug, Clone)]
pub struct CrossDexConfig {
    pub min_profit_sol: f64,
    pub min_profit_percentage: f64,
    pub max_execution_hops: usize,
    pub max_execution_time_ms: u64,
    pub max_slippage_percentage: f64,
    pub supported_token_pairs: Vec<String>,
    pub dex_priority: Vec<DexType>,
    pub risk_tolerance: RiskTolerance,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RiskTolerance {
    Conservative, // Only simple, high-confidence arbitrage
    Moderate,     // Medium complexity with good profit
    Aggressive,   // High complexity, high profit potential
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DexPerformanceMetrics {
    pub average_execution_time_ms: f64,
    pub success_rate: f64,
    pub average_slippage: f64,
    pub liquidity_score: f64,
    pub reliability_score: f64,
    pub last_updated: DateTime<Utc>,
}

impl Default for CrossDexConfig {
    fn default() -> Self {
        Self {
            min_profit_sol: 0.1,
            min_profit_percentage: 0.3,
            max_execution_hops: 3,
            max_execution_time_ms: 5000,
            max_slippage_percentage: 2.0,
            supported_token_pairs: vec![
                "SOL/USDC".to_string(),
                "SOL/USDT".to_string(),
                "BONK/SOL".to_string(),
                "RAY/SOL".to_string(),
                "ORCA/SOL".to_string(),
            ],
            dex_priority: vec![
                DexType::Jupiter,
                DexType::Raydium,
                DexType::Orca,
                DexType::Serum,
                DexType::Meteora,
            ],
            risk_tolerance: RiskTolerance::Moderate,
        }
    }
}

impl CrossDexArbitrageStrategy {
    pub fn new(
        opportunity_sender: mpsc::UnboundedSender<CrossDexOpportunity>,
        signal_sender: mpsc::UnboundedSender<TradingSignal>,
        config: Option<CrossDexConfig>,
    ) -> Self {
        Self {
            price_matrix: HashMap::new(),
            opportunity_sender,
            signal_sender,
            config: config.unwrap_or_default(),
            active_opportunities: Vec::new(),
            dex_performance_metrics: HashMap::new(),
        }
    }

    /// Update price data and scan for opportunities
    pub async fn update_price_data(
        &mut self,
        token_mint: String,
        price_data: PriceData,
    ) -> Result<()> {
        // Update price matrix
        let dex_prices = self
            .price_matrix
            .entry(token_mint.clone())
            .or_insert_with(BTreeMap::new);
        dex_prices.insert(price_data.dex.clone(), price_data);

        // Clean old data (older than 30 seconds)
        let cutoff_time = Utc::now() - chrono::Duration::seconds(30);
        dex_prices.retain(|_, price| price.timestamp > cutoff_time);

        // Scan for arbitrage opportunities
        self.scan_cross_dex_opportunities(&token_mint).await?;

        Ok(())
    }

    /// Scan for cross-DEX arbitrage opportunities
    async fn scan_cross_dex_opportunities(&mut self, token_mint: &str) -> Result<()> {
        // Clone the price data to avoid borrowing issues
        let dex_prices = match self.price_matrix.get(token_mint) {
            Some(prices) if prices.len() >= 2 => prices.clone(),
            _ => return Ok(()), // Need at least 2 DEXes
        };

        // Find all possible arbitrage pairs
        let dex_list: Vec<_> = dex_prices.keys().collect();

        for i in 0..dex_list.len() {
            for j in (i + 1)..dex_list.len() {
                let dex_a = dex_list[i];
                let dex_b = dex_list[j];

                if let (Some(price_a), Some(price_b)) =
                    (dex_prices.get(dex_a), dex_prices.get(dex_b))
                {
                    // Check both directions
                    self.evaluate_arbitrage_direction(token_mint, price_a, price_b)
                        .await?;
                    self.evaluate_arbitrage_direction(token_mint, price_b, price_a)
                        .await?;
                }
            }
        }

        Ok(())
    }

    /// Evaluate arbitrage in one direction
    async fn evaluate_arbitrage_direction(
        &mut self,
        token_mint: &str,
        buy_price: &PriceData,
        sell_price: &PriceData,
    ) -> Result<()> {
        // Calculate basic profit
        let price_diff = sell_price.bid - buy_price.ask;
        let profit_percentage = (price_diff / buy_price.ask) * 100.0;

        if profit_percentage < self.config.min_profit_percentage {
            return Ok(());
        }

        // Calculate optimal trade size
        let max_trade_size = self.calculate_optimal_trade_size(buy_price, sell_price);
        let expected_profit_sol = price_diff * max_trade_size;

        if expected_profit_sol < self.config.min_profit_sol {
            return Ok(());
        }

        // Create arbitrage path
        let arbitrage_path = self
            .create_arbitrage_path(token_mint, buy_price, sell_price, max_trade_size)
            .await?;

        // Calculate execution complexity and risk
        let execution_complexity = self.determine_execution_complexity(&arbitrage_path);
        let risk_score = self.calculate_risk_score(&arbitrage_path, buy_price, sell_price);

        // Check if opportunity meets risk tolerance
        if !self.meets_risk_tolerance(&execution_complexity, risk_score) {
            return Ok(());
        }

        // Calculate confidence score
        let confidence_score = self.calculate_confidence_score(
            profit_percentage,
            &arbitrage_path,
            buy_price,
            sell_price,
        );

        // Create opportunity
        let opportunity = CrossDexOpportunity {
            opportunity_id: uuid::Uuid::new_v4().to_string(),
            token_mint: token_mint.to_string(),
            arbitrage_path,
            expected_profit_sol,
            profit_percentage,
            execution_complexity,
            risk_score,
            estimated_execution_time_ms: self
                .estimate_execution_time(&buy_price.dex, &sell_price.dex),
            required_capital_sol: max_trade_size * buy_price.ask,
            confidence_score,
            discovery_time: Utc::now(),
            expiry_time: Utc::now() + chrono::Duration::seconds(30),
        };

        if confidence_score >= 0.7 {
            info!(
                "🎯 Cross-DEX Arbitrage: {:.2}% profit on {} ({:?} -> {:?})",
                profit_percentage, token_mint, buy_price.dex, sell_price.dex
            );

            // Send opportunity
            self.opportunity_sender
                .send(opportunity.clone())
                .context("Failed to send cross-DEX opportunity")?;

            // Generate trading signal
            let signal = self.create_trading_signal(&opportunity).await?;
            self.signal_sender
                .send(signal)
                .context("Failed to send trading signal")?;

            self.active_opportunities.push(opportunity);
        }

        Ok(())
    }

    /// Calculate optimal trade size based on liquidity
    fn calculate_optimal_trade_size(&self, buy_price: &PriceData, sell_price: &PriceData) -> f64 {
        // Use Kelly criterion for optimal sizing
        let min_liquidity = buy_price.liquidity.min(sell_price.liquidity);
        let conservative_size = min_liquidity * 0.05; // 5% of minimum liquidity

        // Cap at reasonable maximum
        conservative_size.min(50.0) // Max 50 SOL per trade
    }

    /// Create arbitrage execution path
    async fn create_arbitrage_path(
        &self,
        token_mint: &str,
        buy_price: &PriceData,
        sell_price: &PriceData,
        trade_size: f64,
    ) -> Result<ArbitragePath> {
        let mut steps = Vec::new();

        // Step 1: Buy on cheaper DEX
        steps.push(ArbitrageStep {
            step_number: 1,
            dex: buy_price.dex.clone(),
            action: TradeAction::Buy,
            input_token: "SOL".to_string(),
            output_token: token_mint.to_string(),
            input_amount: trade_size * buy_price.ask,
            expected_output: trade_size,
            price_impact: self.estimate_price_impact(trade_size, buy_price.liquidity),
            estimated_gas: 0.005, // 0.005 SOL estimated gas
        });

        // Step 2: Sell on more expensive DEX
        steps.push(ArbitrageStep {
            step_number: 2,
            dex: sell_price.dex.clone(),
            action: TradeAction::Sell,
            input_token: token_mint.to_string(),
            output_token: "SOL".to_string(),
            input_amount: trade_size,
            expected_output: trade_size * sell_price.bid,
            price_impact: self.estimate_price_impact(trade_size, sell_price.liquidity),
            estimated_gas: 0.005,
        });

        let total_slippage = steps.iter().map(|s| s.price_impact).sum();
        let total_fees = steps.iter().map(|s| s.estimated_gas).sum();

        Ok(ArbitragePath {
            steps,
            total_hops: 2,
            estimated_slippage: total_slippage,
            estimated_fees: total_fees,
        })
    }

    /// Estimate price impact based on trade size and liquidity
    fn estimate_price_impact(&self, trade_size: f64, liquidity: f64) -> f64 {
        if liquidity <= 0.0 {
            return 1.0; // 100% impact for zero liquidity
        }

        let impact_ratio = trade_size / liquidity;
        // Square root model for price impact
        (impact_ratio.sqrt() * 0.1).min(0.5) // Max 50% impact
    }

    /// Determine execution complexity
    fn determine_execution_complexity(&self, path: &ArbitragePath) -> ExecutionComplexity {
        match path.total_hops {
            1..=2 => ExecutionComplexity::Simple,
            3 => ExecutionComplexity::Medium,
            4..=5 => ExecutionComplexity::Complex,
            _ => ExecutionComplexity::MultiToken,
        }
    }

    /// Calculate risk score
    fn calculate_risk_score(
        &self,
        path: &ArbitragePath,
        buy_price: &PriceData,
        sell_price: &PriceData,
    ) -> f64 {
        let mut risk = 0.0;

        // Slippage risk
        risk += path.estimated_slippage * 0.3;

        // Execution complexity risk
        risk += match path.total_hops {
            1..=2 => 0.1,
            3 => 0.2,
            4..=5 => 0.4,
            _ => 0.6,
        };

        // Liquidity risk
        let min_liquidity = buy_price.liquidity.min(sell_price.liquidity);
        if min_liquidity < 1000.0 {
            risk += 0.3;
        } else if min_liquidity < 5000.0 {
            risk += 0.1;
        }

        // Time risk (data freshness)
        let now = Utc::now();
        let max_age = (now - buy_price.timestamp)
            .max(now - sell_price.timestamp)
            .num_seconds();
        if max_age > 10 {
            risk += 0.2;
        }

        risk.min(1.0)
    }

    /// Check if opportunity meets risk tolerance
    fn meets_risk_tolerance(&self, complexity: &ExecutionComplexity, risk_score: f64) -> bool {
        match self.config.risk_tolerance {
            RiskTolerance::Conservative => {
                matches!(complexity, ExecutionComplexity::Simple) && risk_score < 0.3
            }
            RiskTolerance::Moderate => {
                matches!(
                    complexity,
                    ExecutionComplexity::Simple | ExecutionComplexity::Medium
                ) && risk_score < 0.5
            }
            RiskTolerance::Aggressive => risk_score < 0.8,
        }
    }

    /// Calculate confidence score
    fn calculate_confidence_score(
        &self,
        profit_percentage: f64,
        path: &ArbitragePath,
        buy_price: &PriceData,
        sell_price: &PriceData,
    ) -> f64 {
        let mut score = 0.0;

        // Profit score
        score += (profit_percentage / 5.0).min(0.3);

        // Liquidity score
        let min_liquidity = buy_price.liquidity.min(sell_price.liquidity);
        score += (min_liquidity / 10000.0).min(0.25);

        // Execution simplicity score
        score += match path.total_hops {
            1..=2 => 0.25,
            3 => 0.15,
            _ => 0.05,
        };

        // Data freshness score
        let now = Utc::now();
        let max_age = (now - buy_price.timestamp)
            .max(now - sell_price.timestamp)
            .num_seconds() as f64;
        score += (1.0 - (max_age / 30.0)).max(0.0).min(0.2);

        score.min(1.0)
    }

    /// Estimate execution time
    fn estimate_execution_time(&self, _buy_dex: &DexType, _sell_dex: &DexType) -> u64 {
        // Base execution time per DEX
        let base_time = 1000; // 1 second base
        let dex_multiplier = 2; // 2 DEXes

        base_time * dex_multiplier
    }

    /// Create trading signal from opportunity
    async fn create_trading_signal(
        &self,
        opportunity: &CrossDexOpportunity,
    ) -> Result<TradingSignal> {
        let first_step = &opportunity.arbitrage_path.steps[0];

        Ok(TradingSignal {
            signal_id: uuid::Uuid::new_v4().to_string(),
            symbol: opportunity.token_mint.clone(),
            action: first_step.action.clone(),
            quantity: first_step.input_amount,
            target_price: first_step.expected_output / first_step.input_amount,
            confidence: opportunity.confidence_score,
            timestamp: Utc::now(),
            strategy_type: StrategyType::CrossDexArbitrage,
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
            debug!(
                "Cleaned up {} expired cross-DEX opportunities",
                removed_count
            );
        }
    }
}
