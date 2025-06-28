//! Liquidity Sniping Strategy Module
//!
//! Advanced strategy for detecting and capitalizing on liquidity events
//! such as new pool creation, large liquidity additions, and LP removals.

use crate::modules::strategy::{StrategyType, TradeAction, TradingSignal};
use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tokio::sync::mpsc;
use tracing::{debug, info};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquidityEvent {
    pub event_id: String,
    pub event_type: LiquidityEventType,
    pub token_mint: String,
    pub pool_address: String,
    pub dex: String,
    pub liquidity_change: f64,
    pub price_impact: f64,
    pub volume_spike: f64,
    pub timestamp: DateTime<Utc>,
    pub block_height: u64,
    pub transaction_signature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LiquidityEventType {
    PoolCreation {
        initial_liquidity_sol: f64,
        initial_token_supply: f64,
        creator_address: String,
    },
    LiquidityAddition {
        added_liquidity_sol: f64,
        provider_address: String,
        percentage_increase: f64,
    },
    LiquidityRemoval {
        removed_liquidity_sol: f64,
        provider_address: String,
        percentage_decrease: f64,
    },
    LargeSwap {
        swap_amount_sol: f64,
        direction: SwapDirection,
        trader_address: String,
        price_impact_percentage: f64,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SwapDirection {
    SolToToken,
    TokenToSol,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquiditySnipeOpportunity {
    pub opportunity_id: String,
    pub trigger_event: LiquidityEvent,
    pub snipe_type: SnipeType,
    pub recommended_action: TradeAction,
    pub optimal_entry_price: f64,
    pub max_position_size: f64,
    pub expected_profit_percentage: f64,
    pub risk_score: f64,
    pub confidence_score: f64,
    pub time_window_seconds: u64,
    pub execution_priority: ExecutionPriority,
    pub discovery_time: DateTime<Utc>,
    pub expiry_time: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SnipeType {
    NewPoolSnipe,        // Snipe new pool creation
    LiquidityDrainSnipe, // Capitalize on liquidity removal
    VolumeSpike,         // Follow large volume increases
    WhaleFollow,         // Follow large wallet movements
    ArbitrageSnipe,      // Quick arbitrage after liquidity changes
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExecutionPriority {
    Critical, // Execute immediately
    High,     // Execute within 5 seconds
    Medium,   // Execute within 30 seconds
    Low,      // Execute within 2 minutes
}

pub struct LiquiditySnipingStrategy {
    liquidity_events: Vec<LiquidityEvent>,
    opportunity_sender: mpsc::UnboundedSender<LiquiditySnipeOpportunity>,
    signal_sender: mpsc::UnboundedSender<TradingSignal>,
    config: LiquiditySnipeConfig,
    active_opportunities: Vec<LiquiditySnipeOpportunity>,
    whale_wallets: HashMap<String, WalletProfile>,
    pool_analytics: HashMap<String, PoolAnalytics>,
}

#[derive(Debug, Clone)]
pub struct LiquiditySnipeConfig {
    pub min_liquidity_sol: f64,
    pub max_position_size_sol: f64,
    pub min_profit_percentage: f64,
    pub max_risk_score: f64,
    pub whale_threshold_sol: f64,
    pub new_pool_snipe_enabled: bool,
    pub liquidity_drain_snipe_enabled: bool,
    pub volume_spike_threshold: f64,
    pub max_pool_age_minutes: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalletProfile {
    pub address: String,
    pub total_volume_sol: f64,
    pub success_rate: f64,
    pub average_hold_time_minutes: u32,
    pub preferred_tokens: Vec<String>,
    pub risk_level: WalletRiskLevel,
    pub last_activity: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WalletRiskLevel {
    Conservative,
    Moderate,
    Aggressive,
    Whale,
    Suspicious,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PoolAnalytics {
    pub pool_address: String,
    pub creation_time: DateTime<Utc>,
    pub total_volume_sol: f64,
    pub liquidity_history: Vec<LiquiditySnapshot>,
    pub price_volatility: f64,
    pub holder_count: u32,
    pub top_holders: Vec<String>,
    pub risk_flags: Vec<RiskFlag>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquiditySnapshot {
    pub timestamp: DateTime<Utc>,
    pub liquidity_sol: f64,
    pub token_price: f64,
    pub volume_24h: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum RiskFlag {
    HighConcentration,  // Few holders control most tokens
    SuspiciousActivity, // Unusual trading patterns
    NewToken,           // Token created recently
    LowLiquidity,       // Insufficient liquidity
    HighVolatility,     // Extreme price swings
    RugPullRisk,        // Indicators of potential rug pull
}

impl Default for LiquiditySnipeConfig {
    fn default() -> Self {
        Self {
            min_liquidity_sol: 10.0,
            max_position_size_sol: 25.0,
            min_profit_percentage: 2.0,
            max_risk_score: 0.7,
            whale_threshold_sol: 100.0,
            new_pool_snipe_enabled: true,
            liquidity_drain_snipe_enabled: true,
            volume_spike_threshold: 5.0, // 5x normal volume
            max_pool_age_minutes: 60,    // Only snipe pools younger than 1 hour
        }
    }
}

impl LiquiditySnipingStrategy {
    pub fn new(
        opportunity_sender: mpsc::UnboundedSender<LiquiditySnipeOpportunity>,
        signal_sender: mpsc::UnboundedSender<TradingSignal>,
        config: Option<LiquiditySnipeConfig>,
    ) -> Self {
        Self {
            liquidity_events: Vec::new(),
            opportunity_sender,
            signal_sender,
            config: config.unwrap_or_default(),
            active_opportunities: Vec::new(),
            whale_wallets: HashMap::new(),
            pool_analytics: HashMap::new(),
        }
    }

    /// Process new liquidity event
    pub async fn process_liquidity_event(&mut self, event: LiquidityEvent) -> Result<()> {
        info!(
            "🌊 Processing liquidity event: {:?} for {}",
            event.event_type, event.token_mint
        );

        // Store event for analysis
        self.liquidity_events.push(event.clone());

        // Update pool analytics
        self.update_pool_analytics(&event).await?;

        // Analyze for sniping opportunities
        self.analyze_snipe_opportunity(&event).await?;

        // Clean old events (keep last 1000)
        if self.liquidity_events.len() > 1000 {
            self.liquidity_events.drain(0..100);
        }

        Ok(())
    }

    /// Update pool analytics with new event
    async fn update_pool_analytics(&mut self, event: &LiquidityEvent) -> Result<()> {
        // Calculate current liquidity first
        let current_liquidity = self.calculate_current_liquidity(&event.pool_address).await;

        let analytics = self
            .pool_analytics
            .entry(event.pool_address.clone())
            .or_insert_with(|| PoolAnalytics {
                pool_address: event.pool_address.clone(),
                creation_time: event.timestamp,
                total_volume_sol: 0.0,
                liquidity_history: Vec::new(),
                price_volatility: 0.0,
                holder_count: 0,
                top_holders: Vec::new(),
                risk_flags: Vec::new(),
            });

        // Update volume
        if let LiquidityEventType::LargeSwap {
            swap_amount_sol, ..
        } = &event.event_type
        {
            analytics.total_volume_sol += swap_amount_sol;
        }

        // Add liquidity snapshot
        analytics.liquidity_history.push(LiquiditySnapshot {
            timestamp: event.timestamp,
            liquidity_sol: current_liquidity,
            token_price: 0.0, // Would be fetched from price oracle
            volume_24h: analytics.total_volume_sol,
        });

        // Update risk flags - clone event to avoid borrow issues
        let event_clone = event.clone();
        self.update_risk_flags_for_pool(&event.pool_address, &event_clone)
            .await;

        Ok(())
    }

    /// Calculate current liquidity for a pool
    async fn calculate_current_liquidity(&self, _pool_address: &str) -> f64 {
        // In real implementation, this would query the pool's current liquidity
        // For now, return a placeholder value
        1000.0
    }

    /// Update risk flags based on event
    async fn update_risk_flags_for_pool(&mut self, pool_address: &str, event: &LiquidityEvent) {
        if let Some(analytics) = self.pool_analytics.get_mut(pool_address) {
            // Check for new token
            let pool_age = (Utc::now() - analytics.creation_time).num_minutes();
            if pool_age < 60 {
                if !analytics.risk_flags.contains(&RiskFlag::NewToken) {
                    analytics.risk_flags.push(RiskFlag::NewToken);
                }
            }

            // Check for low liquidity
            let current_liquidity = analytics
                .liquidity_history
                .last()
                .map(|s| s.liquidity_sol)
                .unwrap_or(0.0);

            if current_liquidity < self.config.min_liquidity_sol {
                if !analytics.risk_flags.contains(&RiskFlag::LowLiquidity) {
                    analytics.risk_flags.push(RiskFlag::LowLiquidity);
                }
            }

            // Check for suspicious activity
            if let LiquidityEventType::LiquidityRemoval {
                percentage_decrease,
                ..
            } = &event.event_type
            {
                if *percentage_decrease > 50.0 {
                    if !analytics.risk_flags.contains(&RiskFlag::SuspiciousActivity) {
                        analytics.risk_flags.push(RiskFlag::SuspiciousActivity);
                    }
                }
            }
        }
    }

    /// Analyze event for sniping opportunities
    async fn analyze_snipe_opportunity(&mut self, event: &LiquidityEvent) -> Result<()> {
        let opportunity = match &event.event_type {
            LiquidityEventType::PoolCreation {
                initial_liquidity_sol,
                ..
            } => {
                if self.config.new_pool_snipe_enabled
                    && *initial_liquidity_sol >= self.config.min_liquidity_sol
                {
                    self.create_new_pool_snipe_opportunity(event).await?
                } else {
                    return Ok(());
                }
            }
            LiquidityEventType::LiquidityRemoval {
                percentage_decrease,
                ..
            } => {
                if self.config.liquidity_drain_snipe_enabled && *percentage_decrease > 20.0 {
                    self.create_liquidity_drain_opportunity(event).await?
                } else {
                    return Ok(());
                }
            }
            LiquidityEventType::LargeSwap {
                swap_amount_sol, ..
            } => {
                if *swap_amount_sol >= self.config.whale_threshold_sol {
                    self.create_whale_follow_opportunity(event).await?
                } else {
                    return Ok(());
                }
            }
            _ => return Ok(()),
        };

        // Check if opportunity meets criteria
        if opportunity.confidence_score >= 0.6
            && opportunity.risk_score <= self.config.max_risk_score
        {
            info!(
                "🎯 Liquidity Snipe Opportunity: {:?} on {} ({}% profit expected)",
                opportunity.snipe_type, event.token_mint, opportunity.expected_profit_percentage
            );

            // Send opportunity
            self.opportunity_sender
                .send(opportunity.clone())
                .context("Failed to send liquidity snipe opportunity")?;

            // Generate trading signal
            let signal = self.create_trading_signal(&opportunity).await?;
            self.signal_sender
                .send(signal)
                .context("Failed to send trading signal")?;

            self.active_opportunities.push(opportunity);
        }

        Ok(())
    }

    /// Create new pool snipe opportunity
    async fn create_new_pool_snipe_opportunity(
        &self,
        event: &LiquidityEvent,
    ) -> Result<LiquiditySnipeOpportunity> {
        let risk_score = self.calculate_new_pool_risk_score(event);
        let confidence_score = self.calculate_new_pool_confidence(event);

        Ok(LiquiditySnipeOpportunity {
            opportunity_id: uuid::Uuid::new_v4().to_string(),
            trigger_event: event.clone(),
            snipe_type: SnipeType::NewPoolSnipe,
            recommended_action: TradeAction::Buy,
            optimal_entry_price: 0.0, // Would be calculated from pool data
            max_position_size: self.config.max_position_size_sol,
            expected_profit_percentage: 10.0, // Estimated based on historical data
            risk_score,
            confidence_score,
            time_window_seconds: 300, // 5 minutes for new pool snipe
            execution_priority: ExecutionPriority::High,
            discovery_time: Utc::now(),
            expiry_time: Utc::now() + chrono::Duration::minutes(5),
        })
    }

    /// Create liquidity drain opportunity
    async fn create_liquidity_drain_opportunity(
        &self,
        event: &LiquidityEvent,
    ) -> Result<LiquiditySnipeOpportunity> {
        let risk_score = self.calculate_drain_risk_score(event);
        let confidence_score = self.calculate_drain_confidence(event);

        Ok(LiquiditySnipeOpportunity {
            opportunity_id: uuid::Uuid::new_v4().to_string(),
            trigger_event: event.clone(),
            snipe_type: SnipeType::LiquidityDrainSnipe,
            recommended_action: TradeAction::Sell, // Sell before further drain
            optimal_entry_price: 0.0,
            max_position_size: self.config.max_position_size_sol * 0.5, // Smaller position for drain
            expected_profit_percentage: 5.0,
            risk_score,
            confidence_score,
            time_window_seconds: 60, // 1 minute for quick exit
            execution_priority: ExecutionPriority::Critical,
            discovery_time: Utc::now(),
            expiry_time: Utc::now() + chrono::Duration::minutes(1),
        })
    }

    /// Create whale follow opportunity
    async fn create_whale_follow_opportunity(
        &self,
        event: &LiquidityEvent,
    ) -> Result<LiquiditySnipeOpportunity> {
        let risk_score = self.calculate_whale_follow_risk_score(event);
        let confidence_score = self.calculate_whale_follow_confidence(event);

        let recommended_action = match &event.event_type {
            LiquidityEventType::LargeSwap { direction, .. } => {
                match direction {
                    SwapDirection::SolToToken => TradeAction::Buy, // Follow whale buy
                    SwapDirection::TokenToSol => TradeAction::Sell, // Follow whale sell
                }
            }
            _ => TradeAction::Hold,
        };

        Ok(LiquiditySnipeOpportunity {
            opportunity_id: uuid::Uuid::new_v4().to_string(),
            trigger_event: event.clone(),
            snipe_type: SnipeType::WhaleFollow,
            recommended_action,
            optimal_entry_price: 0.0,
            max_position_size: self.config.max_position_size_sol * 0.3, // Conservative whale follow
            expected_profit_percentage: 3.0,
            risk_score,
            confidence_score,
            time_window_seconds: 120, // 2 minutes to follow whale
            execution_priority: ExecutionPriority::Medium,
            discovery_time: Utc::now(),
            expiry_time: Utc::now() + chrono::Duration::minutes(2),
        })
    }

    /// Calculate risk score for new pool
    fn calculate_new_pool_risk_score(&self, event: &LiquidityEvent) -> f64 {
        let mut risk = 0.3; // Base risk for new pools

        if let LiquidityEventType::PoolCreation {
            initial_liquidity_sol,
            ..
        } = &event.event_type
        {
            // Lower liquidity = higher risk
            if *initial_liquidity_sol < 50.0 {
                risk += 0.3;
            } else if *initial_liquidity_sol < 100.0 {
                risk += 0.1;
            }
        }

        // Check pool analytics for additional risk factors
        if let Some(analytics) = self.pool_analytics.get(&event.pool_address) {
            risk += analytics.risk_flags.len() as f64 * 0.1;
        }

        risk.min(1.0)
    }

    /// Calculate confidence for new pool
    fn calculate_new_pool_confidence(&self, event: &LiquidityEvent) -> f64 {
        let mut confidence = 0.5; // Base confidence

        if let LiquidityEventType::PoolCreation {
            initial_liquidity_sol,
            ..
        } = &event.event_type
        {
            // Higher liquidity = higher confidence
            confidence += (*initial_liquidity_sol / 1000.0).min(0.3);
        }

        // Data freshness
        let age_seconds = (Utc::now() - event.timestamp).num_seconds();
        if age_seconds < 10 {
            confidence += 0.2;
        }

        confidence.min(1.0)
    }

    /// Calculate risk score for liquidity drain
    fn calculate_drain_risk_score(&self, _event: &LiquidityEvent) -> f64 {
        0.8 // High risk for drain scenarios
    }

    /// Calculate confidence for liquidity drain
    fn calculate_drain_confidence(&self, event: &LiquidityEvent) -> f64 {
        if let LiquidityEventType::LiquidityRemoval {
            percentage_decrease,
            ..
        } = &event.event_type
        {
            // Higher percentage decrease = higher confidence in drain
            (*percentage_decrease / 100.0).min(0.9)
        } else {
            0.5
        }
    }

    /// Calculate risk score for whale follow
    fn calculate_whale_follow_risk_score(&self, _event: &LiquidityEvent) -> f64 {
        0.4 // Moderate risk for whale following
    }

    /// Calculate confidence for whale follow
    fn calculate_whale_follow_confidence(&self, event: &LiquidityEvent) -> f64 {
        if let LiquidityEventType::LargeSwap {
            swap_amount_sol, ..
        } = &event.event_type
        {
            // Larger swaps = higher confidence
            (*swap_amount_sol / 1000.0).min(0.8)
        } else {
            0.5
        }
    }

    /// Create trading signal from opportunity
    async fn create_trading_signal(
        &self,
        opportunity: &LiquiditySnipeOpportunity,
    ) -> Result<TradingSignal> {
        Ok(TradingSignal {
            signal_id: uuid::Uuid::new_v4().to_string(),
            symbol: opportunity.trigger_event.token_mint.clone(),
            action: opportunity.recommended_action.clone(),
            quantity: opportunity.max_position_size,
            target_price: opportunity.optimal_entry_price,
            confidence: opportunity.confidence_score,
            timestamp: Utc::now(),
            strategy_type: StrategyType::LiquiditySniping,
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
                "Cleaned up {} expired liquidity snipe opportunities",
                removed_count
            );
        }
    }
}
