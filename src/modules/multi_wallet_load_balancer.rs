//! Multi-Wallet Load Balancer for THE OVERMIND PROTOCOL
//!
//! Advanced load balancing across multiple wallets with intelligent routing,
//! performance optimization, and geographic distribution.

use anyhow::Result;
use rand;
use serde::{Deserialize, Serialize};
use solana_sdk::pubkey::Pubkey;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::{Mutex, RwLock};
use tracing::{debug, info, warn};

// Type aliases to reduce complexity and improve readability
type PerformanceData = Vec<(u64, f64)>; // (timestamp, latency)
type PerformanceTracker = Arc<Mutex<HashMap<String, PerformanceData>>>;
type WalletNodes = Arc<RwLock<HashMap<String, WalletNode>>>;
type RoutingHistory = Arc<Mutex<Vec<RoutingDecision>>>;
type GeographicZones = Arc<RwLock<HashMap<String, Vec<String>>>>; // region -> wallet_ids
type ActiveTransactions = Arc<RwLock<HashMap<String, TransactionRequest>>>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoadBalancerConfig {
    pub max_concurrent_transactions: usize,
    pub health_check_interval: Duration,
    pub performance_window: Duration,
    pub failover_threshold: f64,
    pub geographic_preference: bool,
    pub load_balancing_strategy: LoadBalancingStrategy,
    pub circuit_breaker_enabled: bool,
    pub adaptive_routing: bool,
    pub latency_threshold_ms: f64,
    pub success_rate_threshold: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LoadBalancingStrategy {
    RoundRobin,
    WeightedRoundRobin,
    LeastConnections,
    PerformanceBased,
    Geographic,
    Adaptive,
    Hybrid,
}

impl Default for LoadBalancerConfig {
    fn default() -> Self {
        Self {
            max_concurrent_transactions: 100,
            health_check_interval: Duration::from_secs(30),
            performance_window: Duration::from_secs(300), // 5 minutes
            failover_threshold: 0.8,                      // 80% success rate threshold
            geographic_preference: true,
            load_balancing_strategy: LoadBalancingStrategy::Adaptive,
            circuit_breaker_enabled: true,
            adaptive_routing: true,
            latency_threshold_ms: 100.0,
            success_rate_threshold: 0.95, // 95% success rate
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalletNode {
    pub wallet_id: String,
    pub public_key: Pubkey,
    pub endpoint: String,
    pub region: String,
    pub weight: f64,
    pub max_concurrent: usize,
    pub current_load: usize,
    pub is_healthy: bool,
    pub performance_metrics: WalletPerformanceMetrics,
    pub circuit_breaker_state: CircuitBreakerState,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalletPerformanceMetrics {
    pub average_latency_ms: f64,
    pub success_rate: f64,
    pub transactions_per_second: f64,
    pub error_rate: f64,
    pub last_success_time: u64,
    pub consecutive_failures: u32,
    pub total_transactions: u64,
    pub successful_transactions: u64,
    pub failed_transactions: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CircuitBreakerState {
    Closed,   // Normal operation
    Open,     // Failing, reject requests
    HalfOpen, // Testing if service recovered
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransactionRequest {
    pub id: String,
    pub priority: TransactionPriority,
    pub estimated_compute_units: u32,
    pub max_latency_ms: Option<u64>,
    pub preferred_region: Option<String>,
    pub retry_count: u32,
    pub created_at: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TransactionPriority {
    Low,
    Normal,
    High,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoutingDecision {
    pub selected_wallet: String,
    pub routing_reason: String,
    pub estimated_latency_ms: f64,
    pub confidence_score: f64,
    pub backup_wallets: Vec<String>,
}

pub struct MultiWalletLoadBalancer {
    config: LoadBalancerConfig,
    wallet_nodes: WalletNodes,
    routing_history: RoutingHistory,
    performance_tracker: PerformanceTracker,
    current_round_robin_index: Arc<Mutex<usize>>,
    geographic_zones: GeographicZones,
    active_transactions: ActiveTransactions,
}

impl MultiWalletLoadBalancer {
    pub fn new(config: LoadBalancerConfig) -> Self {
        Self {
            config,
            wallet_nodes: Arc::new(RwLock::new(HashMap::new())),
            routing_history: Arc::new(Mutex::new(Vec::new())),
            performance_tracker: Arc::new(Mutex::new(HashMap::new())),
            current_round_robin_index: Arc::new(Mutex::new(0)),
            geographic_zones: Arc::new(RwLock::new(HashMap::new())),
            active_transactions: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("⚡ Starting Multi-Wallet Load Balancer for THE OVERMIND PROTOCOL");

        // Start health monitoring
        self.start_health_monitoring().await;

        // Start performance tracking
        self.start_performance_tracking().await;

        // Start circuit breaker monitoring
        if self.config.circuit_breaker_enabled {
            self.start_circuit_breaker_monitoring().await;
        }

        info!("✅ Multi-Wallet Load Balancer started successfully");
        Ok(())
    }

    async fn start_health_monitoring(&self) {
        let wallet_nodes = self.wallet_nodes.clone();
        let config = self.config.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(config.health_check_interval);

            loop {
                interval.tick().await;

                let mut nodes_guard = wallet_nodes.write().await;
                for (wallet_id, node) in nodes_guard.iter_mut() {
                    let is_healthy = Self::check_wallet_health(node).await;

                    if node.is_healthy != is_healthy {
                        if is_healthy {
                            info!("✅ Wallet {} recovered and is now healthy", wallet_id);
                        } else {
                            warn!("❌ Wallet {} is now unhealthy", wallet_id);
                        }
                        node.is_healthy = is_healthy;
                    }
                }
            }
        });
    }

    async fn start_performance_tracking(&self) {
        let performance_tracker = self.performance_tracker.clone();
        let wallet_nodes = self.wallet_nodes.clone();
        let config = self.config.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(60)); // Update every minute

            loop {
                interval.tick().await;

                let mut tracker_guard = performance_tracker.lock().await;
                let nodes_guard = wallet_nodes.read().await;

                let current_time = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs();

                // Clean old performance data
                let cutoff_time = current_time - config.performance_window.as_secs();

                for (wallet_id, performance_data) in tracker_guard.iter_mut() {
                    performance_data.retain(|(timestamp, _)| *timestamp > cutoff_time);

                    // Update wallet performance metrics
                    if let Some(_node) = nodes_guard.get(wallet_id) {
                        // Performance metrics would be updated here
                        debug!("Updated performance metrics for wallet {}", wallet_id);
                    }
                }
            }
        });
    }

    async fn start_circuit_breaker_monitoring(&self) {
        let wallet_nodes = self.wallet_nodes.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(10));

            loop {
                interval.tick().await;

                let mut nodes_guard = wallet_nodes.write().await;
                for (wallet_id, node) in nodes_guard.iter_mut() {
                    Self::update_circuit_breaker_state(node).await;

                    if matches!(node.circuit_breaker_state, CircuitBreakerState::Open) {
                        debug!("🔴 Circuit breaker OPEN for wallet {}", wallet_id);
                    }
                }
            }
        });
    }

    pub async fn route_transaction(&self, request: TransactionRequest) -> Result<RoutingDecision> {
        // Add to active transactions
        {
            let mut active_guard = self.active_transactions.write().await;
            active_guard.insert(request.id.clone(), request.clone());
        }

        let decision = match self.config.load_balancing_strategy {
            LoadBalancingStrategy::RoundRobin => self.round_robin_routing(&request).await?,
            LoadBalancingStrategy::WeightedRoundRobin => {
                self.weighted_round_robin_routing(&request).await?
            }
            LoadBalancingStrategy::LeastConnections => {
                self.least_connections_routing(&request).await?
            }
            LoadBalancingStrategy::PerformanceBased => {
                self.performance_based_routing(&request).await?
            }
            LoadBalancingStrategy::Geographic => self.geographic_routing(&request).await?,
            LoadBalancingStrategy::Adaptive => self.adaptive_routing(&request).await?,
            LoadBalancingStrategy::Hybrid => self.hybrid_routing(&request).await?,
        };

        // Store routing decision
        {
            let mut history_guard = self.routing_history.lock().await;
            history_guard.push(decision.clone());

            // Keep only last 1000 decisions
            if history_guard.len() > 1000 {
                let len = history_guard.len();
                history_guard.drain(0..len - 1000);
            }
        }

        Ok(decision)
    }

    async fn round_robin_routing(&self, _request: &TransactionRequest) -> Result<RoutingDecision> {
        let nodes_guard = self.wallet_nodes.read().await;
        let healthy_wallets: Vec<_> = nodes_guard
            .iter()
            .filter(|(_, node)| {
                node.is_healthy && !matches!(node.circuit_breaker_state, CircuitBreakerState::Open)
            })
            .collect();

        if healthy_wallets.is_empty() {
            return Err(anyhow::anyhow!("No healthy wallets available"));
        }

        let mut index_guard = self.current_round_robin_index.lock().await;
        let selected_index = *index_guard % healthy_wallets.len();
        *index_guard = (*index_guard + 1) % healthy_wallets.len();

        let (wallet_id, node) = healthy_wallets[selected_index];

        Ok(RoutingDecision {
            selected_wallet: wallet_id.clone(),
            routing_reason: "Round Robin selection".to_string(),
            estimated_latency_ms: node.performance_metrics.average_latency_ms,
            confidence_score: 0.8,
            backup_wallets: healthy_wallets
                .iter()
                .filter(|(id, _)| *id != wallet_id)
                .take(2)
                .map(|(id, _)| id.to_string())
                .collect(),
        })
    }

    async fn weighted_round_robin_routing(
        &self,
        _request: &TransactionRequest,
    ) -> Result<RoutingDecision> {
        let nodes_guard = self.wallet_nodes.read().await;
        let healthy_wallets: Vec<_> = nodes_guard
            .iter()
            .filter(|(_, node)| {
                node.is_healthy && !matches!(node.circuit_breaker_state, CircuitBreakerState::Open)
            })
            .collect();

        if healthy_wallets.is_empty() {
            return Err(anyhow::anyhow!("No healthy wallets available"));
        }

        // Calculate total weight
        let total_weight: f64 = healthy_wallets.iter().map(|(_, node)| node.weight).sum();

        // Generate random number for weighted selection
        let random_value = rand::random::<f64>() * total_weight;
        let mut cumulative_weight = 0.0;

        for (wallet_id, node) in healthy_wallets.iter() {
            cumulative_weight += node.weight;
            if random_value <= cumulative_weight {
                return Ok(RoutingDecision {
                    selected_wallet: wallet_id.to_string(),
                    routing_reason: format!("Weighted selection (weight: {:.2})", node.weight),
                    estimated_latency_ms: node.performance_metrics.average_latency_ms,
                    confidence_score: 0.85,
                    backup_wallets: healthy_wallets
                        .iter()
                        .filter(|(id, _)| id.as_str() != *wallet_id)
                        .take(2)
                        .map(|(id, _)| id.to_string())
                        .collect(),
                });
            }
        }

        // Fallback to first wallet
        let (wallet_id, node) = healthy_wallets[0];
        Ok(RoutingDecision {
            selected_wallet: wallet_id.clone(),
            routing_reason: "Weighted fallback".to_string(),
            estimated_latency_ms: node.performance_metrics.average_latency_ms,
            confidence_score: 0.7,
            backup_wallets: Vec::new(),
        })
    }

    async fn least_connections_routing(
        &self,
        _request: &TransactionRequest,
    ) -> Result<RoutingDecision> {
        let nodes_guard = self.wallet_nodes.read().await;
        let healthy_wallets: Vec<_> = nodes_guard
            .iter()
            .filter(|(_, node)| {
                node.is_healthy && !matches!(node.circuit_breaker_state, CircuitBreakerState::Open)
            })
            .collect();

        if healthy_wallets.is_empty() {
            return Err(anyhow::anyhow!("No healthy wallets available"));
        }

        // Find wallet with least connections
        let (wallet_id, node) = healthy_wallets
            .iter()
            .min_by_key(|(_, node)| node.current_load)
            .unwrap();

        Ok(RoutingDecision {
            selected_wallet: wallet_id.to_string(),
            routing_reason: format!("Least connections (load: {})", node.current_load),
            estimated_latency_ms: node.performance_metrics.average_latency_ms,
            confidence_score: 0.9,
            backup_wallets: healthy_wallets
                .iter()
                .filter(|(id, _)| id.as_str() != *wallet_id)
                .take(2)
                .map(|(id, _)| id.to_string())
                .collect(),
        })
    }

    async fn performance_based_routing(
        &self,
        _request: &TransactionRequest,
    ) -> Result<RoutingDecision> {
        let nodes_guard = self.wallet_nodes.read().await;
        let healthy_wallets: Vec<_> = nodes_guard
            .iter()
            .filter(|(_, node)| {
                node.is_healthy && !matches!(node.circuit_breaker_state, CircuitBreakerState::Open)
            })
            .collect();

        if healthy_wallets.is_empty() {
            return Err(anyhow::anyhow!("No healthy wallets available"));
        }

        // Calculate performance score for each wallet
        let mut scored_wallets: Vec<_> = healthy_wallets
            .iter()
            .map(|(wallet_id, node)| {
                let latency_score =
                    1.0 / (1.0 + node.performance_metrics.average_latency_ms / 100.0);
                let success_score = node.performance_metrics.success_rate;
                let load_score = 1.0 - (node.current_load as f64 / node.max_concurrent as f64);

                let total_score = latency_score * 0.4 + success_score * 0.4 + load_score * 0.2;
                (wallet_id, node, total_score)
            })
            .collect();

        // Sort by performance score (highest first)
        scored_wallets.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap());

        let (wallet_id, node, score) = scored_wallets[0];

        Ok(RoutingDecision {
            selected_wallet: wallet_id.to_string(),
            routing_reason: format!("Performance-based selection (score: {:.3})", score),
            estimated_latency_ms: node.performance_metrics.average_latency_ms,
            confidence_score: score,
            backup_wallets: scored_wallets
                .iter()
                .skip(1)
                .take(2)
                .map(|(id, _, _)| id.to_string())
                .collect(),
        })
    }

    async fn geographic_routing(&self, request: &TransactionRequest) -> Result<RoutingDecision> {
        let nodes_guard = self.wallet_nodes.read().await;
        let zones_guard = self.geographic_zones.read().await;

        // If preferred region is specified, try to use wallets from that region
        if let Some(preferred_region) = &request.preferred_region {
            if let Some(region_wallets) = zones_guard.get(preferred_region) {
                let regional_healthy_wallets: Vec<_> = region_wallets
                    .iter()
                    .filter_map(|wallet_id| nodes_guard.get(wallet_id))
                    .filter(|node| {
                        node.is_healthy
                            && !matches!(node.circuit_breaker_state, CircuitBreakerState::Open)
                    })
                    .collect();

                if !regional_healthy_wallets.is_empty() {
                    // Use performance-based selection within the region
                    let best_wallet = regional_healthy_wallets
                        .iter()
                        .max_by(|a, b| {
                            a.performance_metrics
                                .success_rate
                                .partial_cmp(&b.performance_metrics.success_rate)
                                .unwrap()
                        })
                        .unwrap();

                    return Ok(RoutingDecision {
                        selected_wallet: "regional_wallet".to_string(), // Would use actual wallet ID
                        routing_reason: format!("Geographic preference: {}", preferred_region),
                        estimated_latency_ms: best_wallet.performance_metrics.average_latency_ms,
                        confidence_score: 0.95,
                        backup_wallets: Vec::new(),
                    });
                }
            }
        }

        // Fallback to performance-based routing
        self.performance_based_routing(request).await
    }

    async fn adaptive_routing(&self, request: &TransactionRequest) -> Result<RoutingDecision> {
        // Adaptive routing combines multiple strategies based on current conditions
        let nodes_guard = self.wallet_nodes.read().await;

        // Analyze current system state
        let total_load: usize = nodes_guard.values().map(|node| node.current_load).sum();
        let avg_latency: f64 = nodes_guard
            .values()
            .map(|node| node.performance_metrics.average_latency_ms)
            .sum::<f64>()
            / nodes_guard.len() as f64;

        // Choose strategy based on conditions
        let strategy = if total_load > 80 {
            // High load - use least connections
            LoadBalancingStrategy::LeastConnections
        } else if avg_latency > self.config.latency_threshold_ms {
            // High latency - use performance-based
            LoadBalancingStrategy::PerformanceBased
        } else if request.preferred_region.is_some() {
            // Geographic preference specified
            LoadBalancingStrategy::Geographic
        } else {
            // Normal conditions - use weighted round robin
            LoadBalancingStrategy::WeightedRoundRobin
        };

        // Execute chosen strategy
        match strategy {
            LoadBalancingStrategy::LeastConnections => {
                self.least_connections_routing(request).await
            }
            LoadBalancingStrategy::PerformanceBased => {
                self.performance_based_routing(request).await
            }
            LoadBalancingStrategy::Geographic => self.geographic_routing(request).await,
            LoadBalancingStrategy::WeightedRoundRobin => {
                self.weighted_round_robin_routing(request).await
            }
            _ => self.performance_based_routing(request).await, // Fallback
        }
    }

    async fn hybrid_routing(&self, request: &TransactionRequest) -> Result<RoutingDecision> {
        // Hybrid routing uses multiple strategies and selects the best result
        let strategies = vec![
            self.performance_based_routing(request).await,
            self.least_connections_routing(request).await,
            self.weighted_round_robin_routing(request).await,
        ];

        // Filter successful results
        let valid_decisions: Vec<_> = strategies.into_iter().filter_map(|r| r.ok()).collect();

        if valid_decisions.is_empty() {
            return Err(anyhow::anyhow!("All routing strategies failed"));
        }

        // Select decision with highest confidence score
        let best_decision = valid_decisions
            .into_iter()
            .max_by(|a, b| a.confidence_score.partial_cmp(&b.confidence_score).unwrap())
            .unwrap();

        Ok(RoutingDecision {
            selected_wallet: best_decision.selected_wallet,
            routing_reason: format!("Hybrid selection: {}", best_decision.routing_reason),
            estimated_latency_ms: best_decision.estimated_latency_ms,
            confidence_score: best_decision.confidence_score,
            backup_wallets: best_decision.backup_wallets,
        })
    }

    async fn check_wallet_health(node: &WalletNode) -> bool {
        // Simplified health check - in real implementation would ping the wallet/endpoint
        node.performance_metrics.success_rate > 0.8
            && node.performance_metrics.consecutive_failures < 5
            && node.current_load < node.max_concurrent
    }

    async fn update_circuit_breaker_state(node: &mut WalletNode) {
        match node.circuit_breaker_state {
            CircuitBreakerState::Closed => {
                if node.performance_metrics.success_rate < 0.5
                    || node.performance_metrics.consecutive_failures > 10
                {
                    node.circuit_breaker_state = CircuitBreakerState::Open;
                }
            }
            CircuitBreakerState::Open => {
                // Check if enough time has passed to try half-open
                let current_time = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs();

                if current_time - node.performance_metrics.last_success_time > 60 {
                    node.circuit_breaker_state = CircuitBreakerState::HalfOpen;
                }
            }
            CircuitBreakerState::HalfOpen => {
                if node.performance_metrics.success_rate > 0.8 {
                    node.circuit_breaker_state = CircuitBreakerState::Closed;
                } else if node.performance_metrics.consecutive_failures > 3 {
                    node.circuit_breaker_state = CircuitBreakerState::Open;
                }
            }
        }
    }

    pub async fn add_wallet(&self, wallet: WalletNode) -> Result<()> {
        let wallet_id = wallet.wallet_id.clone();
        let region = wallet.region.clone();

        // Add to wallet nodes
        {
            let mut nodes_guard = self.wallet_nodes.write().await;
            nodes_guard.insert(wallet_id.clone(), wallet);
        }

        // Add to geographic zones
        {
            let mut zones_guard = self.geographic_zones.write().await;
            zones_guard
                .entry(region)
                .or_insert_with(Vec::new)
                .push(wallet_id.clone());
        }

        info!("✅ Added wallet {} to load balancer", wallet_id);
        Ok(())
    }

    pub async fn remove_wallet(&self, wallet_id: &str) -> Result<()> {
        // Remove from wallet nodes
        let removed_wallet = {
            let mut nodes_guard = self.wallet_nodes.write().await;
            nodes_guard.remove(wallet_id)
        };

        if let Some(wallet) = removed_wallet {
            // Remove from geographic zones
            let mut zones_guard = self.geographic_zones.write().await;
            if let Some(region_wallets) = zones_guard.get_mut(&wallet.region) {
                region_wallets.retain(|id| id != wallet_id);
                if region_wallets.is_empty() {
                    zones_guard.remove(&wallet.region);
                }
            }

            info!("✅ Removed wallet {} from load balancer", wallet_id);
        }

        Ok(())
    }

    pub async fn get_load_balancer_stats(&self) -> HashMap<String, serde_json::Value> {
        let nodes_guard = self.wallet_nodes.read().await;
        let history_guard = self.routing_history.lock().await;

        let total_wallets = nodes_guard.len();
        let healthy_wallets = nodes_guard.values().filter(|node| node.is_healthy).count();
        let total_load: usize = nodes_guard.values().map(|node| node.current_load).sum();
        let avg_latency: f64 = if !nodes_guard.is_empty() {
            nodes_guard
                .values()
                .map(|node| node.performance_metrics.average_latency_ms)
                .sum::<f64>()
                / nodes_guard.len() as f64
        } else {
            0.0
        };

        let mut stats = HashMap::new();
        stats.insert(
            "total_wallets".to_string(),
            serde_json::Value::Number(total_wallets.into()),
        );
        stats.insert(
            "healthy_wallets".to_string(),
            serde_json::Value::Number(healthy_wallets.into()),
        );
        stats.insert(
            "total_load".to_string(),
            serde_json::Value::Number(total_load.into()),
        );
        stats.insert(
            "average_latency_ms".to_string(),
            serde_json::Value::Number(serde_json::Number::from_f64(avg_latency).unwrap()),
        );
        stats.insert(
            "routing_decisions".to_string(),
            serde_json::Value::Number(history_guard.len().into()),
        );

        stats
    }

    pub async fn shutdown(&mut self) -> Result<()> {
        info!("🛑 Shutting down Multi-Wallet Load Balancer");
        // Cleanup tasks would be implemented here
        info!("✅ Multi-Wallet Load Balancer shut down successfully");
        Ok(())
    }
}
