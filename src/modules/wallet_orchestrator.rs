// 🎭 WALLET ORCHESTRATOR FOR OVERMIND PROTOCOL
// Intelligent wallet management and strategy routing

use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::info;

use crate::modules::dynamic_wallet_generator::{DynamicWalletGenerator, WalletGenerationConfig};
use crate::modules::strategy::StrategyType;
use crate::modules::wallet_manager::{WalletManager, WalletSelection, WalletSelectionCriteria};

/// Wallet orchestration configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrchestratorConfig {
    pub auto_generation_enabled: bool,
    pub max_wallets_total: usize,
    pub balance_rebalancing_enabled: bool,
    pub performance_monitoring_enabled: bool,
    pub rotation_strategy: RotationStrategy,
    pub load_balancing_algorithm: LoadBalancingAlgorithm,
}

/// Wallet rotation strategies
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RotationStrategy {
    TimeBasedRotation,        // Rotate based on time
    PerformanceBasedRotation, // Rotate based on performance
    BalanceBasedRotation,     // Rotate when balance limits reached
    HybridRotation,           // Combination of above
}

/// Load balancing algorithms
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LoadBalancingAlgorithm {
    RoundRobin,         // Simple round-robin
    WeightedRoundRobin, // Based on wallet performance
    LeastConnections,   // Wallet with fewest active trades
    PerformanceBased,   // Best performing wallets first
}

/// Wallet performance metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalletPerformance {
    pub wallet_id: String,
    pub strategy_type: StrategyType,
    pub total_trades: u32,
    pub successful_trades: u32,
    pub total_profit_sol: f64,
    pub average_execution_time_ms: f64,
    pub success_rate: f64,
    pub sharpe_ratio: f64,
    pub last_updated: u64,
}

/// Wallet orchestrator - intelligent wallet management
pub struct WalletOrchestrator {
    config: OrchestratorConfig,
    wallet_manager: Arc<RwLock<WalletManager>>,
    dynamic_generator: Arc<DynamicWalletGenerator>,
    performance_metrics: RwLock<HashMap<String, WalletPerformance>>,
    strategy_routing: RwLock<HashMap<StrategyType, Vec<String>>>,
    current_selections: RwLock<HashMap<StrategyType, usize>>, // For round-robin
}

impl WalletOrchestrator {
    /// Create new wallet orchestrator
    pub async fn new(
        config: OrchestratorConfig,
        wallet_manager: Arc<RwLock<WalletManager>>,
    ) -> Result<Self> {
        info!("🎭 Initializing Wallet Orchestrator");
        info!("   Auto generation: {}", config.auto_generation_enabled);
        info!("   Max wallets: {}", config.max_wallets_total);
        info!("   Load balancing: {:?}", config.load_balancing_algorithm);

        // Create dynamic generator
        let generator_config = WalletGenerationConfig {
            max_wallets_per_strategy: config.max_wallets_total / 6, // Divide among strategies
            wallet_rotation_hours: 24,
            auto_generation_enabled: config.auto_generation_enabled,
            min_balance_threshold: 0.001,
            max_balance_per_wallet: 1.0,
            security_tier: "STANDARD".to_string(),
        };

        let dynamic_generator = Arc::new(DynamicWalletGenerator::new(generator_config));

        // Initialize wallet pools
        dynamic_generator.initialize_pools().await?;

        Ok(Self {
            config,
            wallet_manager,
            dynamic_generator,
            performance_metrics: RwLock::new(HashMap::new()),
            strategy_routing: RwLock::new(HashMap::new()),
            current_selections: RwLock::new(HashMap::new()),
        })
    }

    /// Get optimal wallet for strategy execution
    pub async fn get_optimal_wallet(&self, strategy_type: StrategyType) -> Result<WalletSelection> {
        info!(
            "🎯 Selecting optimal wallet for strategy: {:?}",
            strategy_type
        );

        // Check if we have wallets for this strategy
        let available_wallets = self.get_available_wallets(&strategy_type).await?;

        if available_wallets.is_empty() {
            // Generate new wallet if auto-generation is enabled
            if self.config.auto_generation_enabled {
                info!(
                    "🔧 No wallets available, generating new wallet for {:?}",
                    strategy_type
                );
                let generated_wallet = self
                    .dynamic_generator
                    .generate_wallet(strategy_type.clone())
                    .await?;

                // Convert to WalletConfig and add to manager
                let wallet_config = self.dynamic_generator.to_wallet_config(&generated_wallet)?;
                self.wallet_manager
                    .write()
                    .await
                    .add_wallet(wallet_config)
                    .await?;

                // Return selection for new wallet
                return Ok(WalletSelection {
                    wallet_id: generated_wallet.wallet_id.clone(),
                    wallet_config: self.dynamic_generator.to_wallet_config(&generated_wallet)?,
                    available_balance: 0.0,
                    risk_capacity: 1.0,
                    selection_reason: "Newly generated wallet".to_string(),
                });
            } else {
                return Err(anyhow!(
                    "No wallets available for strategy: {:?}",
                    strategy_type
                ));
            }
        }

        // Select wallet based on load balancing algorithm
        let selected_wallet_id = match self.config.load_balancing_algorithm {
            LoadBalancingAlgorithm::RoundRobin => {
                self.select_round_robin(&strategy_type, &available_wallets)
                    .await
            }
            LoadBalancingAlgorithm::PerformanceBased => {
                self.select_performance_based(&available_wallets).await
            }
            LoadBalancingAlgorithm::LeastConnections => {
                self.select_least_connections(&available_wallets).await
            }
            LoadBalancingAlgorithm::WeightedRoundRobin => {
                self.select_weighted_round_robin(&available_wallets).await
            }
        }?;

        // Create selection criteria for wallet manager
        let criteria = WalletSelectionCriteria {
            strategy_type: strategy_type.clone(),
            required_balance: 0.001, // Minimum balance
            risk_tolerance: 0.8,
            preferred_wallet_type: None,
            exclude_wallets: vec![],
        };

        // Get detailed selection from wallet manager
        let selection = self
            .wallet_manager
            .read()
            .await
            .select_wallet(criteria)
            .await?;

        info!(
            "✅ Selected wallet: {} for {:?}",
            selected_wallet_id, strategy_type
        );
        Ok(selection)
    }

    /// Get available wallets for strategy
    async fn get_available_wallets(&self, strategy_type: &StrategyType) -> Result<Vec<String>> {
        let routing = self.strategy_routing.read().await;
        Ok(routing.get(strategy_type).cloned().unwrap_or_default())
    }

    /// Round-robin wallet selection
    async fn select_round_robin(
        &self,
        strategy_type: &StrategyType,
        wallets: &[String],
    ) -> Result<String> {
        let mut selections = self.current_selections.write().await;
        let current_index = selections.get(strategy_type).cloned().unwrap_or(0);
        let next_index = (current_index + 1) % wallets.len();

        selections.insert(strategy_type.clone(), next_index);
        Ok(wallets[current_index].clone())
    }

    /// Performance-based wallet selection
    async fn select_performance_based(&self, wallets: &[String]) -> Result<String> {
        let metrics = self.performance_metrics.read().await;

        let mut best_wallet = wallets[0].clone();
        let mut best_score = 0.0;

        for wallet_id in wallets {
            if let Some(performance) = metrics.get(wallet_id) {
                // Calculate composite score
                let score = performance.success_rate * 0.4
                    + performance.sharpe_ratio * 0.3
                    + (1.0 / performance.average_execution_time_ms) * 1000.0 * 0.3;

                if score > best_score {
                    best_score = score;
                    best_wallet = wallet_id.clone();
                }
            }
        }

        Ok(best_wallet)
    }

    /// Least connections wallet selection
    async fn select_least_connections(&self, wallets: &[String]) -> Result<String> {
        // For now, use round-robin as placeholder
        // In real implementation, would track active connections per wallet
        Ok(wallets[0].clone())
    }

    /// Weighted round-robin selection
    async fn select_weighted_round_robin(&self, wallets: &[String]) -> Result<String> {
        let metrics = self.performance_metrics.read().await;

        // Calculate weights based on performance
        let mut weighted_wallets = Vec::new();
        for wallet_id in wallets {
            let weight = if let Some(performance) = metrics.get(wallet_id) {
                (performance.success_rate * 10.0) as usize + 1
            } else {
                1 // Default weight for new wallets
            };

            for _ in 0..weight {
                weighted_wallets.push(wallet_id.clone());
            }
        }

        if weighted_wallets.is_empty() {
            return Ok(wallets[0].clone());
        }

        // Use round-robin on weighted list
        let mut selections = self.current_selections.write().await;
        let current_index = selections
            .get(&StrategyType::TokenSniping)
            .cloned()
            .unwrap_or(0);
        let next_index = (current_index + 1) % weighted_wallets.len();

        selections.insert(StrategyType::TokenSniping, next_index);
        Ok(weighted_wallets[current_index].clone())
    }

    /// Update wallet performance metrics
    pub async fn update_performance(&self, wallet_id: String, performance: WalletPerformance) {
        let mut metrics = self.performance_metrics.write().await;
        metrics.insert(wallet_id.clone(), performance);
        info!("📊 Updated performance metrics for wallet: {}", wallet_id);
    }

    /// Process wallet rotations
    pub async fn process_rotations(&self) -> Result<Vec<String>> {
        info!("🔄 Processing wallet rotations");
        let rotated_wallets = self.dynamic_generator.process_rotations().await?;

        if !rotated_wallets.is_empty() {
            info!("✅ Rotated {} wallets", rotated_wallets.len());
            // Update routing after rotations
            self.update_strategy_routing().await?;
        }

        Ok(rotated_wallets)
    }

    /// Update strategy routing after wallet changes
    async fn update_strategy_routing(&self) -> Result<()> {
        let pool_stats = self.dynamic_generator.get_pool_stats().await;
        let mut routing = self.strategy_routing.write().await;

        for (strategy_type, stats) in pool_stats {
            // Get active wallets for this strategy
            let active_wallets: Vec<String> = (0..stats.active_count)
                .map(|i| format!("{}_{}", strategy_type.to_string().to_lowercase(), i))
                .collect();

            routing.insert(strategy_type, active_wallets);
        }

        Ok(())
    }

    /// Get orchestrator statistics
    pub async fn get_stats(&self) -> OrchestratorStats {
        let pool_stats = self.dynamic_generator.get_pool_stats().await;
        let metrics = self.performance_metrics.read().await;
        let routing = self.strategy_routing.read().await;

        let total_wallets: usize = pool_stats.values().map(|s| s.active_count).sum();
        let total_strategies = routing.len();
        let avg_performance = if metrics.is_empty() {
            0.0
        } else {
            metrics.values().map(|m| m.success_rate).sum::<f64>() / metrics.len() as f64
        };

        OrchestratorStats {
            total_wallets,
            total_strategies,
            avg_performance,
            auto_generation_enabled: self.config.auto_generation_enabled,
            load_balancing_algorithm: self.config.load_balancing_algorithm.clone(),
        }
    }
}

/// Orchestrator statistics
#[derive(Debug, Serialize)]
pub struct OrchestratorStats {
    pub total_wallets: usize,
    pub total_strategies: usize,
    pub avg_performance: f64,
    pub auto_generation_enabled: bool,
    pub load_balancing_algorithm: LoadBalancingAlgorithm,
}

impl Default for OrchestratorConfig {
    fn default() -> Self {
        Self {
            auto_generation_enabled: true,
            max_wallets_total: 30,
            balance_rebalancing_enabled: true,
            performance_monitoring_enabled: true,
            rotation_strategy: RotationStrategy::HybridRotation,
            load_balancing_algorithm: LoadBalancingAlgorithm::PerformanceBased,
        }
    }
}
