//! Portfolio Rebalancing System for THE OVERMIND PROTOCOL
//!
//! Advanced portfolio rebalancing with multiple strategies, transaction cost optimization,
//! and intelligent timing algorithms.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::sync::{Mutex, RwLock};
use tracing::{info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RebalancingConfig {
    pub strategy: RebalancingStrategy,
    pub threshold_percentage: f64, // Deviation threshold for rebalancing
    pub min_rebalance_interval: Duration, // Minimum time between rebalances
    pub max_rebalance_interval: Duration, // Maximum time between rebalances
    pub transaction_cost_threshold: f64, // Minimum cost-benefit ratio
    pub volatility_adjustment: bool, // Adjust timing based on volatility
    pub momentum_consideration: bool, // Consider momentum in timing
    pub liquidity_requirement: f64, // Minimum liquidity for rebalancing
    pub max_trade_size: f64,       // Maximum single trade size
    pub slippage_tolerance: f64,   // Maximum acceptable slippage
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RebalancingStrategy {
    Threshold,     // Rebalance when deviation exceeds threshold
    Calendar,      // Rebalance at fixed intervals
    Volatility,    // Rebalance based on volatility
    Momentum,      // Rebalance based on momentum
    CostOptimized, // Rebalance when cost-effective
    Hybrid,        // Combination of strategies
}

impl Default for RebalancingConfig {
    fn default() -> Self {
        Self {
            strategy: RebalancingStrategy::Hybrid,
            threshold_percentage: 0.05, // 5% deviation threshold
            min_rebalance_interval: Duration::from_secs(3600), // 1 hour minimum
            max_rebalance_interval: Duration::from_secs(86400), // 24 hours maximum
            transaction_cost_threshold: 0.001, // 0.1% minimum cost-benefit
            volatility_adjustment: true,
            momentum_consideration: true,
            liquidity_requirement: 0.8, // 80% liquidity requirement
            max_trade_size: 0.1,        // 10% max trade size
            slippage_tolerance: 0.005,  // 0.5% slippage tolerance
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TargetAllocation {
    pub symbol: String,
    pub target_weight: f64,
    pub current_weight: f64,
    pub deviation: f64,
    pub priority: RebalancePriority,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RebalancePriority {
    High,
    Medium,
    Low,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RebalanceOrder {
    pub symbol: String,
    pub action: OrderAction,
    pub quantity: f64,
    pub estimated_cost: f64,
    pub expected_slippage: f64,
    pub urgency: f64,
    pub reasoning: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderAction {
    Buy,
    Sell,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RebalanceExecution {
    pub orders: Vec<RebalanceOrder>,
    pub total_cost: f64,
    pub expected_improvement: f64,
    pub execution_time: u64,
    pub strategy_used: RebalancingStrategy,
    pub risk_metrics: RebalanceRiskMetrics,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RebalanceRiskMetrics {
    pub portfolio_volatility_before: f64,
    pub portfolio_volatility_after: f64,
    pub tracking_error: f64,
    pub concentration_risk: f64,
    pub liquidity_risk: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketConditions {
    pub volatility_regime: VolatilityRegime,
    pub momentum_score: f64,
    pub liquidity_score: f64,
    pub market_stress_indicator: f64,
    pub correlation_environment: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum VolatilityRegime {
    Low,
    Medium,
    High,
    Extreme,
}

pub struct PortfolioRebalancer {
    config: RebalancingConfig,
    target_allocations: Arc<RwLock<HashMap<String, f64>>>,
    current_positions: Arc<RwLock<HashMap<String, f64>>>,
    market_conditions: Arc<RwLock<MarketConditions>>,
    rebalance_history: Arc<Mutex<Vec<RebalanceExecution>>>,
    last_rebalance: Arc<Mutex<Instant>>,
    transaction_costs: Arc<RwLock<HashMap<String, f64>>>,
    liquidity_scores: Arc<RwLock<HashMap<String, f64>>>,
}

impl PortfolioRebalancer {
    pub fn new(config: RebalancingConfig) -> Self {
        Self {
            config,
            target_allocations: Arc::new(RwLock::new(HashMap::new())),
            current_positions: Arc::new(RwLock::new(HashMap::new())),
            market_conditions: Arc::new(RwLock::new(MarketConditions {
                volatility_regime: VolatilityRegime::Medium,
                momentum_score: 0.5,
                liquidity_score: 0.8,
                market_stress_indicator: 0.3,
                correlation_environment: 0.5,
            })),
            rebalance_history: Arc::new(Mutex::new(Vec::new())),
            last_rebalance: Arc::new(Mutex::new(Instant::now())),
            transaction_costs: Arc::new(RwLock::new(HashMap::new())),
            liquidity_scores: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("🔄 Starting Portfolio Rebalancing System for THE OVERMIND PROTOCOL");

        // Start rebalancing monitoring
        self.start_rebalance_monitoring().await;

        // Start market conditions monitoring
        self.start_market_conditions_monitoring().await;

        info!("✅ Portfolio Rebalancing System started successfully");
        Ok(())
    }

    async fn start_rebalance_monitoring(&self) {
        let target_allocations = self.target_allocations.clone();
        let current_positions = self.current_positions.clone();
        let market_conditions = self.market_conditions.clone();
        let last_rebalance = self.last_rebalance.clone();
        let config = self.config.clone();
        let rebalance_history = self.rebalance_history.clone();
        let transaction_costs = self.transaction_costs.clone();
        let liquidity_scores = self.liquidity_scores.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(60)); // Check every minute

            loop {
                interval.tick().await;

                let should_rebalance = Self::should_rebalance(
                    &target_allocations,
                    &current_positions,
                    &market_conditions,
                    &last_rebalance,
                    &config,
                )
                .await;

                if should_rebalance {
                    match Self::execute_rebalance(
                        &target_allocations,
                        &current_positions,
                        &market_conditions,
                        &transaction_costs,
                        &liquidity_scores,
                        &config,
                    )
                    .await
                    {
                        Ok(execution) => {
                            info!(
                                "🔄 Portfolio rebalanced successfully: {} orders, cost: {:.4}%",
                                execution.orders.len(),
                                execution.total_cost * 100.0
                            );

                            // Update last rebalance time
                            {
                                let mut last_rebalance_guard = last_rebalance.lock().await;
                                *last_rebalance_guard = Instant::now();
                            }

                            // Store execution history
                            {
                                let mut history_guard = rebalance_history.lock().await;
                                history_guard.push(execution);

                                // Keep only last 100 rebalances
                                if history_guard.len() > 100 {
                                    let len = history_guard.len();
                                    history_guard.drain(0..len - 100);
                                }
                            }
                        }
                        Err(e) => {
                            warn!("❌ Rebalancing failed: {}", e);
                        }
                    }
                }
            }
        });
    }

    async fn start_market_conditions_monitoring(&self) {
        let market_conditions = self.market_conditions.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(300)); // Update every 5 minutes

            loop {
                interval.tick().await;

                // Update market conditions (simplified)
                let new_conditions = Self::assess_market_conditions().await;

                {
                    let mut conditions_guard = market_conditions.write().await;
                    *conditions_guard = new_conditions;
                }
            }
        });
    }

    async fn should_rebalance(
        target_allocations: &Arc<RwLock<HashMap<String, f64>>>,
        current_positions: &Arc<RwLock<HashMap<String, f64>>>,
        market_conditions: &Arc<RwLock<MarketConditions>>,
        last_rebalance: &Arc<Mutex<Instant>>,
        config: &RebalancingConfig,
    ) -> bool {
        // Check minimum time interval
        {
            let last_rebalance_guard = last_rebalance.lock().await;
            if last_rebalance_guard.elapsed() < config.min_rebalance_interval {
                return false;
            }
        }

        // Check maximum time interval
        {
            let last_rebalance_guard = last_rebalance.lock().await;
            if last_rebalance_guard.elapsed() > config.max_rebalance_interval {
                return true;
            }
        }

        match config.strategy {
            RebalancingStrategy::Threshold => {
                Self::check_threshold_rebalance(target_allocations, current_positions, config).await
            }
            RebalancingStrategy::Calendar => {
                Self::check_calendar_rebalance(last_rebalance, config).await
            }
            RebalancingStrategy::Volatility => {
                Self::check_volatility_rebalance(market_conditions, config).await
            }
            RebalancingStrategy::Momentum => {
                Self::check_momentum_rebalance(market_conditions, config).await
            }
            RebalancingStrategy::CostOptimized => {
                Self::check_cost_optimized_rebalance(target_allocations, current_positions, config)
                    .await
            }
            RebalancingStrategy::Hybrid => {
                Self::check_hybrid_rebalance(
                    target_allocations,
                    current_positions,
                    market_conditions,
                    last_rebalance,
                    config,
                )
                .await
            }
        }
    }

    async fn check_threshold_rebalance(
        target_allocations: &Arc<RwLock<HashMap<String, f64>>>,
        current_positions: &Arc<RwLock<HashMap<String, f64>>>,
        config: &RebalancingConfig,
    ) -> bool {
        let target_guard = target_allocations.read().await;
        let current_guard = current_positions.read().await;

        for (symbol, &target_weight) in target_guard.iter() {
            let current_weight = current_guard.get(symbol).copied().unwrap_or(0.0);
            let deviation = (current_weight - target_weight).abs();

            if deviation > config.threshold_percentage {
                return true;
            }
        }

        false
    }

    async fn check_calendar_rebalance(
        last_rebalance: &Arc<Mutex<Instant>>,
        config: &RebalancingConfig,
    ) -> bool {
        let last_rebalance_guard = last_rebalance.lock().await;
        last_rebalance_guard.elapsed() >= config.max_rebalance_interval
    }

    async fn check_volatility_rebalance(
        market_conditions: &Arc<RwLock<MarketConditions>>,
        _config: &RebalancingConfig,
    ) -> bool {
        let conditions_guard = market_conditions.read().await;
        matches!(
            conditions_guard.volatility_regime,
            VolatilityRegime::High | VolatilityRegime::Extreme
        )
    }

    async fn check_momentum_rebalance(
        market_conditions: &Arc<RwLock<MarketConditions>>,
        _config: &RebalancingConfig,
    ) -> bool {
        let conditions_guard = market_conditions.read().await;
        conditions_guard.momentum_score.abs() > 0.7 // Strong momentum
    }

    async fn check_cost_optimized_rebalance(
        target_allocations: &Arc<RwLock<HashMap<String, f64>>>,
        current_positions: &Arc<RwLock<HashMap<String, f64>>>,
        config: &RebalancingConfig,
    ) -> bool {
        let expected_benefit =
            Self::calculate_rebalance_benefit(target_allocations, current_positions).await;
        expected_benefit > config.transaction_cost_threshold
    }

    async fn check_hybrid_rebalance(
        target_allocations: &Arc<RwLock<HashMap<String, f64>>>,
        current_positions: &Arc<RwLock<HashMap<String, f64>>>,
        market_conditions: &Arc<RwLock<MarketConditions>>,
        last_rebalance: &Arc<Mutex<Instant>>,
        config: &RebalancingConfig,
    ) -> bool {
        let threshold_trigger =
            Self::check_threshold_rebalance(target_allocations, current_positions, config).await;
        let volatility_trigger = Self::check_volatility_rebalance(market_conditions, config).await;
        let cost_trigger =
            Self::check_cost_optimized_rebalance(target_allocations, current_positions, config)
                .await;
        let calendar_trigger = Self::check_calendar_rebalance(last_rebalance, config).await;

        // Weighted decision
        let score = (threshold_trigger as u8 as f64 * 0.4)
            + (volatility_trigger as u8 as f64 * 0.2)
            + (cost_trigger as u8 as f64 * 0.3)
            + (calendar_trigger as u8 as f64 * 0.1);

        score > 0.5
    }

    async fn execute_rebalance(
        target_allocations: &Arc<RwLock<HashMap<String, f64>>>,
        current_positions: &Arc<RwLock<HashMap<String, f64>>>,
        market_conditions: &Arc<RwLock<MarketConditions>>,
        transaction_costs: &Arc<RwLock<HashMap<String, f64>>>,
        liquidity_scores: &Arc<RwLock<HashMap<String, f64>>>,
        config: &RebalancingConfig,
    ) -> Result<RebalanceExecution> {
        let target_guard = target_allocations.read().await;
        let current_guard = current_positions.read().await;
        let _conditions_guard = market_conditions.read().await;
        let costs_guard = transaction_costs.read().await;
        let liquidity_guard = liquidity_scores.read().await;

        // Calculate required trades
        let mut orders = Vec::new();
        let mut total_cost = 0.0;

        for (symbol, &target_weight) in target_guard.iter() {
            let current_weight = current_guard.get(symbol).copied().unwrap_or(0.0);
            let deviation = target_weight - current_weight;

            if deviation.abs() > config.threshold_percentage {
                let liquidity_score = liquidity_guard.get(symbol).copied().unwrap_or(0.5);

                if liquidity_score >= config.liquidity_requirement {
                    let transaction_cost = costs_guard.get(symbol).copied().unwrap_or(0.001);
                    let trade_size = deviation.abs().min(config.max_trade_size);

                    let order = RebalanceOrder {
                        symbol: symbol.clone(),
                        action: if deviation > 0.0 {
                            OrderAction::Buy
                        } else {
                            OrderAction::Sell
                        },
                        quantity: trade_size,
                        estimated_cost: trade_size * transaction_cost,
                        expected_slippage: Self::estimate_slippage(trade_size, liquidity_score),
                        urgency: deviation.abs() / config.threshold_percentage,
                        reasoning: format!(
                            "Rebalance {} from {:.2}% to {:.2}% (deviation: {:.2}%)",
                            symbol,
                            current_weight * 100.0,
                            target_weight * 100.0,
                            deviation.abs() * 100.0
                        ),
                    };

                    total_cost += order.estimated_cost;
                    orders.push(order);
                }
            }
        }

        // Sort orders by urgency
        orders.sort_by(|a, b| b.urgency.partial_cmp(&a.urgency).unwrap());

        // Calculate risk metrics
        let risk_metrics =
            Self::calculate_rebalance_risk_metrics(&target_guard, &current_guard).await;

        // Calculate expected improvement
        let expected_improvement =
            Self::calculate_rebalance_benefit(target_allocations, current_positions).await;

        Ok(RebalanceExecution {
            orders,
            total_cost,
            expected_improvement,
            execution_time: SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs(),
            strategy_used: config.strategy.clone(),
            risk_metrics,
        })
    }

    async fn assess_market_conditions() -> MarketConditions {
        // Simplified market conditions assessment
        // In a real implementation, this would analyze market data

        MarketConditions {
            volatility_regime: VolatilityRegime::Medium,
            momentum_score: 0.3,          // Slight positive momentum
            liquidity_score: 0.8,         // Good liquidity
            market_stress_indicator: 0.2, // Low stress
            correlation_environment: 0.6, // Moderate correlation
        }
    }

    async fn calculate_rebalance_benefit(
        target_allocations: &Arc<RwLock<HashMap<String, f64>>>,
        current_positions: &Arc<RwLock<HashMap<String, f64>>>,
    ) -> f64 {
        let target_guard = target_allocations.read().await;
        let current_guard = current_positions.read().await;

        let mut total_deviation = 0.0;
        for (symbol, &target_weight) in target_guard.iter() {
            let current_weight = current_guard.get(symbol).copied().unwrap_or(0.0);
            total_deviation += (target_weight - current_weight).abs();
        }

        // Benefit is proportional to total deviation
        total_deviation * 0.1 // Simplified benefit calculation
    }

    fn estimate_slippage(trade_size: f64, liquidity_score: f64) -> f64 {
        // Simplified slippage estimation
        let base_slippage = 0.001; // 0.1% base slippage
        let size_impact = trade_size * 0.01; // 1% impact per 1% trade size
        let liquidity_adjustment = (1.0 - liquidity_score) * 0.005; // Up to 0.5% for low liquidity

        base_slippage + size_impact + liquidity_adjustment
    }

    async fn calculate_rebalance_risk_metrics(
        target_allocations: &HashMap<String, f64>,
        current_positions: &HashMap<String, f64>,
    ) -> RebalanceRiskMetrics {
        // Simplified risk metrics calculation
        let mut concentration_risk = 0.0;
        let mut tracking_error = 0.0;

        for (symbol, &target_weight) in target_allocations {
            let current_weight = current_positions.get(symbol).copied().unwrap_or(0.0);

            // Concentration risk (Herfindahl index)
            concentration_risk += target_weight * target_weight;

            // Tracking error
            tracking_error += (target_weight - current_weight).powi(2);
        }

        tracking_error = tracking_error.sqrt();

        RebalanceRiskMetrics {
            portfolio_volatility_before: 0.15, // Would be calculated from actual positions
            portfolio_volatility_after: 0.14,  // Would be calculated from target positions
            tracking_error,
            concentration_risk,
            liquidity_risk: 0.1, // Would be calculated from liquidity scores
        }
    }

    pub async fn update_target_allocations(&self, allocations: HashMap<String, f64>) -> Result<()> {
        let mut target_guard = self.target_allocations.write().await;
        *target_guard = allocations;
        info!("🎯 Target allocations updated");
        Ok(())
    }

    pub async fn update_current_positions(&self, positions: HashMap<String, f64>) -> Result<()> {
        let mut current_guard = self.current_positions.write().await;
        *current_guard = positions;
        Ok(())
    }

    pub async fn update_transaction_costs(&self, costs: HashMap<String, f64>) -> Result<()> {
        let mut costs_guard = self.transaction_costs.write().await;
        *costs_guard = costs;
        Ok(())
    }

    pub async fn update_liquidity_scores(&self, scores: HashMap<String, f64>) -> Result<()> {
        let mut liquidity_guard = self.liquidity_scores.write().await;
        *liquidity_guard = scores;
        Ok(())
    }

    pub async fn get_rebalance_history(&self) -> Vec<RebalanceExecution> {
        let history_guard = self.rebalance_history.lock().await;
        history_guard.clone()
    }

    pub async fn get_current_deviations(&self) -> HashMap<String, f64> {
        let target_guard = self.target_allocations.read().await;
        let current_guard = self.current_positions.read().await;

        let mut deviations = HashMap::new();
        for (symbol, &target_weight) in target_guard.iter() {
            let current_weight = current_guard.get(symbol).copied().unwrap_or(0.0);
            deviations.insert(symbol.clone(), (current_weight - target_weight).abs());
        }

        deviations
    }

    pub async fn force_rebalance(&self) -> Result<RebalanceExecution> {
        Self::execute_rebalance(
            &self.target_allocations,
            &self.current_positions,
            &self.market_conditions,
            &self.transaction_costs,
            &self.liquidity_scores,
            &self.config,
        )
        .await
    }

    pub async fn shutdown(&mut self) -> Result<()> {
        info!("🛑 Shutting down Portfolio Rebalancing System");
        // Cleanup tasks would be implemented here
        info!("✅ Portfolio Rebalancing System shut down successfully");
        Ok(())
    }
}
