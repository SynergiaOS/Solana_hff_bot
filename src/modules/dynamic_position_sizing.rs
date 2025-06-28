//! Dynamic Position Sizing for THE OVERMIND PROTOCOL
//!
//! Advanced position sizing algorithms including Kelly Criterion, Risk Parity,
//! Volatility Targeting, and Machine Learning-based sizing.

#![allow(unused_parens)]

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
// Tracing imports removed - not used in this module

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PositionSizingConfig {
    pub method: SizingMethod,
    pub max_position_size: f64,    // Maximum position size (0.0-1.0)
    pub min_position_size: f64,    // Minimum position size (0.0-1.0)
    pub volatility_target: f64,    // Target portfolio volatility
    pub lookback_period: u32,      // Days for historical analysis
    pub confidence_threshold: f64, // Minimum confidence for position sizing
    pub kelly_fraction: f64,       // Kelly Criterion fraction (0.0-1.0)
    pub risk_free_rate: f64,       // Risk-free rate for calculations
    pub rebalance_frequency: u32,  // Hours between rebalancing
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SizingMethod {
    Kelly,               // Kelly Criterion
    RiskParity,          // Risk Parity
    VolatilityTargeting, // Volatility Targeting
    EqualWeight,         // Equal Weight
    MarketCapWeight,     // Market Cap Weighted
    MLBased,             // Machine Learning Based
    Hybrid,              // Combination of methods
}

impl Default for PositionSizingConfig {
    fn default() -> Self {
        Self {
            method: SizingMethod::Hybrid,
            max_position_size: 0.20,   // 20% max position
            min_position_size: 0.01,   // 1% min position
            volatility_target: 0.15,   // 15% annual volatility target
            lookback_period: 30,       // 30 days lookback
            confidence_threshold: 0.6, // 60% minimum confidence
            kelly_fraction: 0.25,      // 25% of Kelly recommendation
            risk_free_rate: 0.02,      // 2% annual risk-free rate
            rebalance_frequency: 24,   // Rebalance daily
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssetMetrics {
    pub symbol: String,
    pub expected_return: f64,
    pub volatility: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
    pub win_rate: f64,
    pub avg_win: f64,
    pub avg_loss: f64,
    pub correlation_with_portfolio: f64,
    pub liquidity_score: f64,
    pub momentum_score: f64,
    pub mean_reversion_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PositionSize {
    pub symbol: String,
    pub target_weight: f64,
    pub current_weight: f64,
    pub recommended_size: f64,
    pub confidence: f64,
    pub method_used: SizingMethod,
    pub risk_contribution: f64,
    pub expected_return: f64,
    pub reasoning: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PortfolioAllocation {
    pub positions: Vec<PositionSize>,
    pub total_allocation: f64,
    pub expected_portfolio_return: f64,
    pub expected_portfolio_volatility: f64,
    pub portfolio_sharpe_ratio: f64,
    pub diversification_ratio: f64,
    pub timestamp: u64,
}

pub struct DynamicPositionSizer {
    config: PositionSizingConfig,
    asset_metrics: Arc<RwLock<HashMap<String, AssetMetrics>>>,
    price_history: Arc<RwLock<HashMap<String, Vec<(u64, f64)>>>>,
    return_history: Arc<RwLock<HashMap<String, Vec<f64>>>>,
    correlation_matrix: Arc<RwLock<HashMap<String, HashMap<String, f64>>>>,
    ml_model_weights: Arc<RwLock<HashMap<String, f64>>>,
}

impl DynamicPositionSizer {
    pub fn new(config: PositionSizingConfig) -> Self {
        Self {
            config,
            asset_metrics: Arc::new(RwLock::new(HashMap::new())),
            price_history: Arc::new(RwLock::new(HashMap::new())),
            return_history: Arc::new(RwLock::new(HashMap::new())),
            correlation_matrix: Arc::new(RwLock::new(HashMap::new())),
            ml_model_weights: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn calculate_position_sizes(
        &self,
        symbols: &[String],
        portfolio_value: f64,
    ) -> Result<PortfolioAllocation> {
        // Update asset metrics
        self.update_asset_metrics(symbols).await?;

        // Calculate position sizes based on method
        let positions = match self.config.method {
            SizingMethod::Kelly => {
                self.kelly_criterion_sizing(symbols, portfolio_value)
                    .await?
            }
            SizingMethod::RiskParity => self.risk_parity_sizing(symbols, portfolio_value).await?,
            SizingMethod::VolatilityTargeting => {
                self.volatility_targeting_sizing(symbols, portfolio_value)
                    .await?
            }
            SizingMethod::EqualWeight => self.equal_weight_sizing(symbols, portfolio_value).await?,
            SizingMethod::MarketCapWeight => {
                self.market_cap_weight_sizing(symbols, portfolio_value)
                    .await?
            }
            SizingMethod::MLBased => self.ml_based_sizing(symbols, portfolio_value).await?,
            SizingMethod::Hybrid => self.hybrid_sizing(symbols, portfolio_value).await?,
        };

        // Calculate portfolio metrics
        let portfolio_metrics = self.calculate_portfolio_metrics(&positions).await?;

        Ok(PortfolioAllocation {
            positions,
            total_allocation: portfolio_metrics.0,
            expected_portfolio_return: portfolio_metrics.1,
            expected_portfolio_volatility: portfolio_metrics.2,
            portfolio_sharpe_ratio: portfolio_metrics.3,
            diversification_ratio: portfolio_metrics.4,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)?
                .as_secs(),
        })
    }

    async fn kelly_criterion_sizing(
        &self,
        symbols: &[String],
        portfolio_value: f64,
    ) -> Result<Vec<PositionSize>> {
        let mut positions = Vec::new();
        let asset_metrics_guard = self.asset_metrics.read().await;

        for symbol in symbols {
            if let Some(metrics) = asset_metrics_guard.get(symbol) {
                // Kelly Criterion: f = (bp - q) / b
                // where f = fraction to bet, b = odds, p = win probability, q = loss probability
                let win_prob = metrics.win_rate;
                let loss_prob = 1.0 - win_prob;
                let avg_win_ratio = metrics.avg_win;
                let avg_loss_ratio = metrics.avg_loss.abs();

                let kelly_fraction = if avg_loss_ratio > 0.0 {
                    (win_prob * avg_win_ratio - loss_prob * avg_loss_ratio) / avg_win_ratio
                } else {
                    0.0
                };

                // Apply Kelly fraction multiplier for safety
                let adjusted_kelly = kelly_fraction * self.config.kelly_fraction;

                // Clamp to min/max position size
                let position_size = adjusted_kelly
                    .max(self.config.min_position_size)
                    .min(self.config.max_position_size);

                positions.push(PositionSize {
                    symbol: symbol.clone(),
                    target_weight: position_size,
                    current_weight: 0.0, // Would be updated with current positions
                    recommended_size: position_size * portfolio_value,
                    confidence: metrics.win_rate,
                    method_used: SizingMethod::Kelly,
                    risk_contribution: position_size * metrics.volatility,
                    expected_return: metrics.expected_return,
                    reasoning: format!("Kelly Criterion: {:.2}% (Win Rate: {:.1}%, Avg Win: {:.2}%, Avg Loss: {:.2}%)",
                                     position_size * 100.0, metrics.win_rate * 100.0,
                                     metrics.avg_win * 100.0, metrics.avg_loss * 100.0),
                });
            }
        }

        Ok(positions)
    }

    async fn risk_parity_sizing(
        &self,
        symbols: &[String],
        portfolio_value: f64,
    ) -> Result<Vec<PositionSize>> {
        let mut positions = Vec::new();
        let asset_metrics_guard = self.asset_metrics.read().await;

        // Calculate inverse volatility weights
        let mut total_inv_vol = 0.0;
        let mut inv_volatilities = HashMap::new();

        for symbol in symbols {
            if let Some(metrics) = asset_metrics_guard.get(symbol) {
                let inv_vol = if metrics.volatility > 0.0 {
                    1.0 / metrics.volatility
                } else {
                    0.0
                };
                inv_volatilities.insert(symbol.clone(), inv_vol);
                total_inv_vol += inv_vol;
            }
        }

        // Normalize to get weights
        for symbol in symbols {
            if let (Some(inv_vol), Some(metrics)) = (
                inv_volatilities.get(symbol),
                asset_metrics_guard.get(symbol),
            ) {
                let weight = if total_inv_vol > 0.0 {
                    inv_vol / total_inv_vol
                } else {
                    0.0
                };

                // Apply min/max constraints
                let position_size = weight
                    .max(self.config.min_position_size)
                    .min(self.config.max_position_size);

                positions.push(PositionSize {
                    symbol: symbol.clone(),
                    target_weight: position_size,
                    current_weight: 0.0,
                    recommended_size: position_size * portfolio_value,
                    confidence: 0.8, // Risk parity has high confidence
                    method_used: SizingMethod::RiskParity,
                    risk_contribution: position_size * metrics.volatility,
                    expected_return: metrics.expected_return,
                    reasoning: format!(
                        "Risk Parity: {:.2}% (Volatility: {:.2}%)",
                        position_size * 100.0,
                        metrics.volatility * 100.0
                    ),
                });
            }
        }

        Ok(positions)
    }

    async fn volatility_targeting_sizing(
        &self,
        symbols: &[String],
        portfolio_value: f64,
    ) -> Result<Vec<PositionSize>> {
        let mut positions = Vec::new();
        let asset_metrics_guard = self.asset_metrics.read().await;

        for symbol in symbols {
            if let Some(metrics) = asset_metrics_guard.get(symbol) {
                // Target volatility sizing: weight = target_vol / asset_vol
                let target_vol = self.config.volatility_target;
                let position_size = if metrics.volatility > 0.0 {
                    (target_vol / metrics.volatility) / symbols.len() as f64
                } else {
                    0.0
                };

                // Apply constraints
                let constrained_size = position_size
                    .max(self.config.min_position_size)
                    .min(self.config.max_position_size);

                positions.push(PositionSize {
                    symbol: symbol.clone(),
                    target_weight: constrained_size,
                    current_weight: 0.0,
                    recommended_size: constrained_size * portfolio_value,
                    confidence: 0.7,
                    method_used: SizingMethod::VolatilityTargeting,
                    risk_contribution: constrained_size * metrics.volatility,
                    expected_return: metrics.expected_return,
                    reasoning: format!(
                        "Volatility Targeting: {:.2}% (Target Vol: {:.2}%, Asset Vol: {:.2}%)",
                        constrained_size * 100.0,
                        target_vol * 100.0,
                        metrics.volatility * 100.0
                    ),
                });
            }
        }

        Ok(positions)
    }

    async fn equal_weight_sizing(
        &self,
        symbols: &[String],
        portfolio_value: f64,
    ) -> Result<Vec<PositionSize>> {
        let mut positions = Vec::new();
        let asset_metrics_guard = self.asset_metrics.read().await;
        let equal_weight = 1.0 / symbols.len() as f64;

        for symbol in symbols {
            if let Some(metrics) = asset_metrics_guard.get(symbol) {
                let position_size = equal_weight
                    .max(self.config.min_position_size)
                    .min(self.config.max_position_size);

                positions.push(PositionSize {
                    symbol: symbol.clone(),
                    target_weight: position_size,
                    current_weight: 0.0,
                    recommended_size: position_size * portfolio_value,
                    confidence: 0.6,
                    method_used: SizingMethod::EqualWeight,
                    risk_contribution: position_size * metrics.volatility,
                    expected_return: metrics.expected_return,
                    reasoning: format!(
                        "Equal Weight: {:.2}% (1/{} assets)",
                        position_size * 100.0,
                        symbols.len()
                    ),
                });
            }
        }

        Ok(positions)
    }

    async fn market_cap_weight_sizing(
        &self,
        symbols: &[String],
        portfolio_value: f64,
    ) -> Result<Vec<PositionSize>> {
        // For crypto, we'll use a proxy based on liquidity scores
        let mut positions = Vec::new();
        let asset_metrics_guard = self.asset_metrics.read().await;

        let total_liquidity: f64 = symbols
            .iter()
            .filter_map(|s| asset_metrics_guard.get(s))
            .map(|m| m.liquidity_score)
            .sum();

        for symbol in symbols {
            if let Some(metrics) = asset_metrics_guard.get(symbol) {
                let weight = if total_liquidity > 0.0 {
                    metrics.liquidity_score / total_liquidity
                } else {
                    1.0 / symbols.len() as f64
                };

                let position_size = weight
                    .max(self.config.min_position_size)
                    .min(self.config.max_position_size);

                positions.push(PositionSize {
                    symbol: symbol.clone(),
                    target_weight: position_size,
                    current_weight: 0.0,
                    recommended_size: position_size * portfolio_value,
                    confidence: 0.7,
                    method_used: SizingMethod::MarketCapWeight,
                    risk_contribution: position_size * metrics.volatility,
                    expected_return: metrics.expected_return,
                    reasoning: format!(
                        "Market Cap Weight: {:.2}% (Liquidity Score: {:.2})",
                        position_size * 100.0,
                        metrics.liquidity_score
                    ),
                });
            }
        }

        Ok(positions)
    }

    async fn ml_based_sizing(
        &self,
        symbols: &[String],
        portfolio_value: f64,
    ) -> Result<Vec<PositionSize>> {
        let mut positions = Vec::new();
        let asset_metrics_guard = self.asset_metrics.read().await;
        let ml_weights_guard = self.ml_model_weights.read().await;

        for symbol in symbols {
            if let Some(metrics) = asset_metrics_guard.get(symbol) {
                // Use ML model weights if available, otherwise fall back to momentum + mean reversion
                let ml_score = ml_weights_guard.get(symbol).copied().unwrap_or_else(|| {
                    // Simple ML proxy: combine momentum and mean reversion scores
                    0.5 * metrics.momentum_score
                        + 0.3 * metrics.mean_reversion_score
                        + 0.2 * metrics.sharpe_ratio
                });

                // Normalize ML score to position size
                let position_size = (ml_score * 0.2) // Scale to reasonable position size
                    .max(self.config.min_position_size)
                    .min(self.config.max_position_size);

                positions.push(PositionSize {
                    symbol: symbol.clone(),
                    target_weight: position_size,
                    current_weight: 0.0,
                    recommended_size: position_size * portfolio_value,
                    confidence: ml_score.min(1.0),
                    method_used: SizingMethod::MLBased,
                    risk_contribution: position_size * metrics.volatility,
                    expected_return: metrics.expected_return,
                    reasoning: format!(
                        "ML-Based: {:.2}% (ML Score: {:.3}, Momentum: {:.2}, Mean Rev: {:.2})",
                        position_size * 100.0,
                        ml_score,
                        metrics.momentum_score,
                        metrics.mean_reversion_score
                    ),
                });
            }
        }

        Ok(positions)
    }

    async fn hybrid_sizing(
        &self,
        symbols: &[String],
        portfolio_value: f64,
    ) -> Result<Vec<PositionSize>> {
        // Combine multiple methods with weights
        let kelly_positions = self
            .kelly_criterion_sizing(symbols, portfolio_value)
            .await?;
        let risk_parity_positions = self.risk_parity_sizing(symbols, portfolio_value).await?;
        let vol_target_positions = self
            .volatility_targeting_sizing(symbols, portfolio_value)
            .await?;
        let ml_positions = self.ml_based_sizing(symbols, portfolio_value).await?;

        let mut hybrid_positions = Vec::new();
        let asset_metrics_guard = self.asset_metrics.read().await;

        // Weights for different methods
        let kelly_weight = 0.3;
        let risk_parity_weight = 0.3;
        let vol_target_weight = 0.2;
        let ml_weight = 0.2;

        for symbol in symbols {
            if let Some(metrics) = asset_metrics_guard.get(symbol) {
                let kelly_size = kelly_positions
                    .iter()
                    .find(|p| p.symbol == *symbol)
                    .map(|p| p.target_weight)
                    .unwrap_or(0.0);

                let rp_size = risk_parity_positions
                    .iter()
                    .find(|p| p.symbol == *symbol)
                    .map(|p| p.target_weight)
                    .unwrap_or(0.0);

                let vt_size = vol_target_positions
                    .iter()
                    .find(|p| p.symbol == *symbol)
                    .map(|p| p.target_weight)
                    .unwrap_or(0.0);

                let ml_size = ml_positions
                    .iter()
                    .find(|p| p.symbol == *symbol)
                    .map(|p| p.target_weight)
                    .unwrap_or(0.0);

                // Weighted combination
                let hybrid_size = (kelly_size * kelly_weight
                    + rp_size * risk_parity_weight
                    + vt_size * vol_target_weight
                    + ml_size * ml_weight)
                    .max(self.config.min_position_size)
                    .min(self.config.max_position_size);

                // Calculate confidence as weighted average
                let confidence = (metrics.win_rate * kelly_weight
                    + 0.8 * risk_parity_weight
                    + 0.7 * vol_target_weight
                    + ml_positions
                        .iter()
                        .find(|p| p.symbol == *symbol)
                        .map(|p| p.confidence)
                        .unwrap_or(0.5)
                        * ml_weight);

                hybrid_positions.push(PositionSize {
                    symbol: symbol.clone(),
                    target_weight: hybrid_size,
                    current_weight: 0.0,
                    recommended_size: hybrid_size * portfolio_value,
                    confidence,
                    method_used: SizingMethod::Hybrid,
                    risk_contribution: hybrid_size * metrics.volatility,
                    expected_return: metrics.expected_return,
                    reasoning: format!(
                        "Hybrid: {:.2}% (Kelly: {:.2}%, RP: {:.2}%, VT: {:.2}%, ML: {:.2}%)",
                        hybrid_size * 100.0,
                        kelly_size * 100.0,
                        rp_size * 100.0,
                        vt_size * 100.0,
                        ml_size * 100.0
                    ),
                });
            }
        }

        Ok(hybrid_positions)
    }

    async fn update_asset_metrics(&self, symbols: &[String]) -> Result<()> {
        let mut asset_metrics_guard = self.asset_metrics.write().await;
        let return_history_guard = self.return_history.read().await;

        for symbol in symbols {
            // Calculate metrics from return history
            if let Some(returns) = return_history_guard.get(symbol) {
                let metrics = self.calculate_asset_metrics(symbol, returns).await;
                asset_metrics_guard.insert(symbol.clone(), metrics);
            } else {
                // Create default metrics if no history available
                asset_metrics_guard.insert(
                    symbol.clone(),
                    AssetMetrics {
                        symbol: symbol.clone(),
                        expected_return: 0.05, // 5% default expected return
                        volatility: 0.20,      // 20% default volatility
                        sharpe_ratio: 0.25,    // Default Sharpe ratio
                        max_drawdown: 0.15,    // 15% default max drawdown
                        win_rate: 0.55,        // 55% default win rate
                        avg_win: 0.02,         // 2% average win
                        avg_loss: 0.015,       // 1.5% average loss
                        correlation_with_portfolio: 0.3,
                        liquidity_score: 0.8,      // Default liquidity score
                        momentum_score: 0.5,       // Neutral momentum
                        mean_reversion_score: 0.5, // Neutral mean reversion
                    },
                );
            }
        }

        Ok(())
    }

    async fn calculate_asset_metrics(&self, symbol: &str, returns: &[f64]) -> AssetMetrics {
        if returns.is_empty() {
            return AssetMetrics {
                symbol: symbol.to_string(),
                expected_return: 0.0,
                volatility: 0.0,
                sharpe_ratio: 0.0,
                max_drawdown: 0.0,
                win_rate: 0.5,
                avg_win: 0.0,
                avg_loss: 0.0,
                correlation_with_portfolio: 0.0,
                liquidity_score: 0.5,
                momentum_score: 0.5,
                mean_reversion_score: 0.5,
            };
        }

        // Calculate basic statistics
        let mean_return = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns
            .iter()
            .map(|r| (r - mean_return).powi(2))
            .sum::<f64>()
            / returns.len() as f64;
        let volatility = variance.sqrt();

        // Calculate Sharpe ratio
        let excess_return = mean_return - self.config.risk_free_rate / 252.0; // Daily risk-free rate
        let sharpe_ratio = if volatility > 0.0 {
            excess_return / volatility
        } else {
            0.0
        };

        // Calculate win rate and average win/loss
        let positive_returns: Vec<f64> = returns.iter().filter(|&&r| r > 0.0).copied().collect();
        let negative_returns: Vec<f64> = returns.iter().filter(|&&r| r < 0.0).copied().collect();

        let win_rate = positive_returns.len() as f64 / returns.len() as f64;
        let avg_win = if !positive_returns.is_empty() {
            positive_returns.iter().sum::<f64>() / positive_returns.len() as f64
        } else {
            0.0
        };
        let avg_loss = if !negative_returns.is_empty() {
            negative_returns.iter().sum::<f64>() / negative_returns.len() as f64
        } else {
            0.0
        };

        // Calculate max drawdown
        let mut peak = 0.0;
        let mut max_drawdown = 0.0;
        let mut cumulative_return = 0.0;

        for &ret in returns {
            cumulative_return += ret;
            if cumulative_return > peak {
                peak = cumulative_return;
            }
            let drawdown = peak - cumulative_return;
            if drawdown > max_drawdown {
                max_drawdown = drawdown;
            }
        }

        // Calculate momentum score (recent performance)
        let momentum_score = if returns.len() >= 10 {
            let recent_returns = &returns[returns.len() - 10..];
            let recent_mean = recent_returns.iter().sum::<f64>() / recent_returns.len() as f64;
            (recent_mean + 1.0).max(0.0).min(1.0) // Normalize to 0-1
        } else {
            0.5
        };

        // Calculate mean reversion score (volatility of returns)
        let mean_reversion_score = if volatility > 0.0 {
            (1.0 / (1.0 + volatility * 10.0)).max(0.0).min(1.0)
        } else {
            0.5
        };

        AssetMetrics {
            symbol: symbol.to_string(),
            expected_return: mean_return * 252.0, // Annualized
            volatility: volatility * (252.0_f64).sqrt(), // Annualized
            sharpe_ratio,
            max_drawdown,
            win_rate,
            avg_win,
            avg_loss,
            correlation_with_portfolio: 0.3, // Would be calculated with portfolio returns
            liquidity_score: 0.8,            // Would be calculated from volume data
            momentum_score,
            mean_reversion_score,
        }
    }

    async fn calculate_portfolio_metrics(
        &self,
        positions: &[PositionSize],
    ) -> Result<(f64, f64, f64, f64, f64)> {
        let total_allocation = positions.iter().map(|p| p.target_weight).sum();

        let expected_return = positions
            .iter()
            .map(|p| p.target_weight * p.expected_return)
            .sum();

        // Simplified portfolio volatility (assuming zero correlation)
        let portfolio_variance: f64 = positions
            .iter()
            .map(|p| (p.target_weight * p.risk_contribution).powi(2))
            .sum();
        let portfolio_volatility = portfolio_variance.sqrt();

        let sharpe_ratio = if portfolio_volatility > 0.0 {
            (expected_return - self.config.risk_free_rate) / portfolio_volatility
        } else {
            0.0
        };

        // Diversification ratio (simplified)
        let weighted_avg_vol = positions
            .iter()
            .map(|p| p.target_weight * p.risk_contribution)
            .sum::<f64>();
        let diversification_ratio = if portfolio_volatility > 0.0 {
            weighted_avg_vol / portfolio_volatility
        } else {
            1.0
        };

        Ok((
            total_allocation,
            expected_return,
            portfolio_volatility,
            sharpe_ratio,
            diversification_ratio,
        ))
    }

    pub async fn update_price_data(
        &self,
        symbol: String,
        price: f64,
        timestamp: u64,
    ) -> Result<()> {
        // Update price history
        let mut price_history_guard = self.price_history.write().await;
        let prices = price_history_guard
            .entry(symbol.clone())
            .or_insert_with(Vec::new);
        prices.push((timestamp, price));

        // Keep only recent data
        let cutoff_time = timestamp - (self.config.lookback_period as u64 * 24 * 3600);
        prices.retain(|(time, _)| *time > cutoff_time);

        // Calculate returns if we have enough data
        if prices.len() >= 2 {
            let mut return_history_guard = self.return_history.write().await;
            let returns = return_history_guard.entry(symbol).or_insert_with(Vec::new);

            // Calculate return from last two prices
            let last_price = prices[prices.len() - 2].1;
            let current_price = prices[prices.len() - 1].1;
            let return_rate = (current_price - last_price) / last_price;

            returns.push(return_rate);

            // Keep only recent returns
            if returns.len() > self.config.lookback_period as usize {
                returns.drain(0..returns.len() - self.config.lookback_period as usize);
            }
        }

        Ok(())
    }

    pub async fn get_position_size_recommendation(
        &self,
        symbol: &str,
        portfolio_value: f64,
        confidence: f64,
    ) -> Result<Option<PositionSize>> {
        if confidence < self.config.confidence_threshold {
            return Ok(None);
        }

        let allocation = self
            .calculate_position_sizes(&[symbol.to_string()], portfolio_value)
            .await?;
        Ok(allocation
            .positions
            .into_iter()
            .find(|p| p.symbol == symbol))
    }
}
