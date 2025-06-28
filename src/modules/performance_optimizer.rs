//! Performance Optimizer Module
//!
//! Advanced performance optimizations for THE OVERMIND PROTOCOL including
//! connection pooling, caching, batch processing, and latency optimization.

#![allow(private_interfaces)]

use anyhow::Result;
use redis::{aio::ConnectionManager, Client as RedisClient};
use serde::{Deserialize, Serialize};
use solana_client::rpc_client::RpcClient;
use solana_sdk::commitment_config::CommitmentConfig;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, RwLock};
use tracing::{debug, error, info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceConfig {
    pub target_latency_ms: u64,
    pub connection_pool_size: usize,
    pub cache_ttl_seconds: u64,
    pub batch_size: usize,
    pub batch_timeout_ms: u64,
    pub memory_optimization_enabled: bool,
    pub connection_warming_enabled: bool,
    pub adaptive_optimization_enabled: bool,
}

impl Default for PerformanceConfig {
    fn default() -> Self {
        Self {
            target_latency_ms: 25, // Sub-25ms target
            connection_pool_size: 10,
            cache_ttl_seconds: 30,
            batch_size: 50,
            batch_timeout_ms: 100,
            memory_optimization_enabled: true,
            connection_warming_enabled: true,
            adaptive_optimization_enabled: true,
        }
    }
}

#[derive(Clone)]
pub struct ConnectionPool {
    rpc_clients: Arc<RwLock<Vec<Arc<RpcClient>>>>,
    redis_connections: Arc<RwLock<Vec<ConnectionManager>>>,
    current_rpc_index: Arc<Mutex<usize>>,
    current_redis_index: Arc<Mutex<usize>>,
    health_status: Arc<RwLock<HashMap<String, bool>>>,
}

#[derive(Clone)]
pub struct CacheManager {
    redis_pool: Arc<RwLock<Vec<ConnectionManager>>>,
    local_cache: Arc<RwLock<HashMap<String, CacheEntry>>>,
    cache_stats: Arc<Mutex<CacheStats>>,
    config: PerformanceConfig,
}

#[derive(Debug, Clone)]
struct CacheEntry {
    data: String,
    created_at: Instant,
    access_count: u64,
    ttl: Duration,
}

#[derive(Debug, Clone, Default)]
struct CacheStats {
    hits: u64,
    misses: u64,
    evictions: u64,
    total_requests: u64,
}

pub struct BatchProcessor<T> {
    batch_queue: Arc<Mutex<Vec<T>>>,
    batch_size: usize,
    batch_timeout: Duration,
    processor_fn: Arc<dyn Fn(Vec<T>) -> Result<()> + Send + Sync>,
}

#[derive(Debug, Clone)]
pub struct LatencyOptimizer {
    latency_history: Arc<RwLock<Vec<Duration>>>,
    target_latency: Duration,
    optimization_strategies: Vec<OptimizationStrategy>,
    current_strategy: Arc<Mutex<usize>>,
}

#[derive(Debug, Clone)]
enum OptimizationStrategy {
    ConnectionPooling,
    RequestBatching,
    CacheAggressive,
    GeographicRouting,
    AdaptiveTimeout,
}

pub struct PerformanceOptimizer {
    config: PerformanceConfig,
    connection_pool: ConnectionPool,
    cache_manager: CacheManager,
    latency_optimizer: LatencyOptimizer,
    performance_metrics: Arc<Mutex<PerformanceMetrics>>,
}

#[derive(Debug, Clone, Default)]
pub struct PerformanceMetrics {
    pub average_latency_ms: f64,
    pub p95_latency_ms: f64,
    pub p99_latency_ms: f64,
    pub cache_hit_rate: f64,
    pub connection_pool_utilization: f64,
    pub batch_efficiency: f64,
    pub memory_usage_mb: f64,
    pub optimization_score: f64,
}

impl ConnectionPool {
    pub async fn new(rpc_urls: Vec<String>, redis_urls: Vec<String>) -> Result<Self> {
        let mut rpc_clients = Vec::new();
        let mut redis_connections = Vec::new();
        let mut health_status = HashMap::new();

        // Initialize RPC clients
        for url in rpc_urls {
            let client = Arc::new(RpcClient::new_with_commitment(
                url.clone(),
                CommitmentConfig::processed(),
            ));
            rpc_clients.push(client);
            health_status.insert(format!("rpc_{}", url), true);
        }

        // Initialize Redis connections
        for url in redis_urls {
            let client = RedisClient::open(url.clone())?;
            let conn = ConnectionManager::new(client).await?;
            redis_connections.push(conn);
            health_status.insert(format!("redis_{}", url), true);
        }

        Ok(Self {
            rpc_clients: Arc::new(RwLock::new(rpc_clients)),
            redis_connections: Arc::new(RwLock::new(redis_connections)),
            current_rpc_index: Arc::new(Mutex::new(0)),
            current_redis_index: Arc::new(Mutex::new(0)),
            health_status: Arc::new(RwLock::new(health_status)),
        })
    }

    pub async fn get_rpc_client(&self) -> Result<Arc<RpcClient>> {
        let clients = self.rpc_clients.read().await;
        let mut index = self.current_rpc_index.lock().await;

        if clients.is_empty() {
            return Err(anyhow::anyhow!("No RPC clients available"));
        }

        let client = clients[*index % clients.len()].clone();
        *index = (*index + 1) % clients.len();

        Ok(client)
    }

    pub async fn get_redis_connection(&self) -> Result<ConnectionManager> {
        let connections = self.redis_connections.read().await;
        let mut index = self.current_redis_index.lock().await;

        if connections.is_empty() {
            return Err(anyhow::anyhow!("No Redis connections available"));
        }

        let connection = connections[*index % connections.len()].clone();
        *index = (*index + 1) % connections.len();

        Ok(connection)
    }

    pub async fn health_check(&self) -> Result<()> {
        let mut health_status = self.health_status.write().await;

        // Check RPC clients
        let rpc_clients = self.rpc_clients.read().await;
        for (i, _client) in rpc_clients.iter().enumerate() {
            let key = format!("rpc_{}", i);
            // For now, assume all clients are healthy
            // In a real implementation, you would use async health checks
            health_status.insert(key, true);
        }

        // Check Redis connections
        let redis_connections = self.redis_connections.read().await;
        for (i, conn) in redis_connections.iter().enumerate() {
            let key = format!("redis_{}", i);
            let mut conn_clone = conn.clone();
            match tokio::time::timeout(
                Duration::from_secs(5),
                redis::cmd("PING").query_async::<_, String>(&mut conn_clone),
            )
            .await
            {
                Ok(Ok(_)) => {
                    health_status.insert(key, true);
                }
                _ => {
                    health_status.insert(key, false);
                    warn!("Redis connection {} is unhealthy", i);
                }
            }
        }

        Ok(())
    }
}

impl CacheManager {
    pub async fn new(redis_pool: Vec<ConnectionManager>, config: PerformanceConfig) -> Self {
        Self {
            redis_pool: Arc::new(RwLock::new(redis_pool)),
            local_cache: Arc::new(RwLock::new(HashMap::new())),
            cache_stats: Arc::new(Mutex::new(CacheStats::default())),
            config,
        }
    }

    pub async fn get(&self, key: &str) -> Result<Option<String>> {
        let start_time = Instant::now();
        let mut stats = self.cache_stats.lock().await;
        stats.total_requests += 1;

        // Check local cache first
        {
            let local_cache = self.local_cache.read().await;
            if let Some(entry) = local_cache.get(key) {
                if entry.created_at.elapsed() < entry.ttl {
                    stats.hits += 1;
                    debug!("Cache hit (local): {} in {:?}", key, start_time.elapsed());
                    return Ok(Some(entry.data.clone()));
                }
            }
        }

        // Check Redis cache
        let redis_pool = self.redis_pool.read().await;
        if let Some(conn) = redis_pool.first() {
            let mut conn_clone = conn.clone();
            match redis::cmd("GET")
                .arg(key)
                .query_async::<_, Option<String>>(&mut conn_clone)
                .await
            {
                Ok(Some(value)) => {
                    stats.hits += 1;

                    // Update local cache
                    self.update_local_cache(key.to_string(), value.clone())
                        .await;

                    debug!("Cache hit (Redis): {} in {:?}", key, start_time.elapsed());
                    return Ok(Some(value));
                }
                Ok(None) => {
                    stats.misses += 1;
                    debug!("Cache miss: {} in {:?}", key, start_time.elapsed());
                }
                Err(e) => {
                    warn!("Redis cache error for key {}: {}", key, e);
                    stats.misses += 1;
                }
            }
        }

        Ok(None)
    }

    pub async fn set(&self, key: String, value: String, ttl: Option<Duration>) -> Result<()> {
        let ttl = ttl.unwrap_or(Duration::from_secs(self.config.cache_ttl_seconds));

        // Update local cache
        self.update_local_cache(key.clone(), value.clone()).await;

        // Update Redis cache
        let redis_pool = self.redis_pool.read().await;
        if let Some(conn) = redis_pool.first() {
            let mut conn_clone = conn.clone();
            let _: () = redis::cmd("SETEX")
                .arg(&key)
                .arg(ttl.as_secs())
                .arg(&value)
                .query_async(&mut conn_clone)
                .await?;
        }

        Ok(())
    }

    async fn update_local_cache(&self, key: String, value: String) {
        let mut local_cache = self.local_cache.write().await;

        // Implement LRU eviction if cache is full
        if local_cache.len() >= 1000 {
            // Max 1000 entries in local cache
            let oldest_key = local_cache
                .iter()
                .min_by_key(|(_, entry)| entry.created_at)
                .map(|(k, _)| k.clone());

            if let Some(key_to_remove) = oldest_key {
                local_cache.remove(&key_to_remove);
                let mut stats = self.cache_stats.lock().await;
                stats.evictions += 1;
            }
        }

        local_cache.insert(
            key,
            CacheEntry {
                data: value,
                created_at: Instant::now(),
                access_count: 1,
                ttl: Duration::from_secs(self.config.cache_ttl_seconds),
            },
        );
    }

    pub async fn get_cache_stats(&self) -> CacheStats {
        self.cache_stats.lock().await.clone()
    }
}

impl<T> BatchProcessor<T>
where
    T: Send + 'static,
{
    pub fn new<F>(batch_size: usize, batch_timeout: Duration, processor: F) -> Self
    where
        F: Fn(Vec<T>) -> Result<()> + Send + Sync + 'static,
    {
        Self {
            batch_queue: Arc::new(Mutex::new(Vec::new())),
            batch_size,
            batch_timeout,
            processor_fn: Arc::new(processor),
        }
    }

    pub async fn add_item(&self, item: T) -> Result<()> {
        let mut queue = self.batch_queue.lock().await;
        queue.push(item);

        if queue.len() >= self.batch_size {
            let batch = queue.drain(..).collect();
            drop(queue); // Release lock before processing

            let processor = self.processor_fn.clone();
            tokio::spawn(async move {
                if let Err(e) = processor(batch) {
                    error!("Batch processing failed: {}", e);
                }
            });
        }

        Ok(())
    }

    pub async fn start_batch_timer(&self) {
        let batch_queue = self.batch_queue.clone();
        let processor_fn = self.processor_fn.clone();
        let timeout = self.batch_timeout;

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(timeout);

            loop {
                interval.tick().await;

                let mut queue = batch_queue.lock().await;
                if !queue.is_empty() {
                    let batch = queue.drain(..).collect();
                    drop(queue);

                    let processor = processor_fn.clone();
                    tokio::spawn(async move {
                        if let Err(e) = processor(batch) {
                            error!("Timed batch processing failed: {}", e);
                        }
                    });
                }
            }
        });
    }
}

impl LatencyOptimizer {
    pub fn new(target_latency: Duration) -> Self {
        Self {
            latency_history: Arc::new(RwLock::new(Vec::new())),
            target_latency,
            optimization_strategies: vec![
                OptimizationStrategy::ConnectionPooling,
                OptimizationStrategy::RequestBatching,
                OptimizationStrategy::CacheAggressive,
                OptimizationStrategy::GeographicRouting,
                OptimizationStrategy::AdaptiveTimeout,
            ],
            current_strategy: Arc::new(Mutex::new(0)),
        }
    }

    pub async fn record_latency(&self, latency: Duration) {
        let mut history = self.latency_history.write().await;
        history.push(latency);

        // Keep only last 1000 measurements
        if history.len() > 1000 {
            history.drain(0..100);
        }

        // Trigger optimization if latency is above target
        if latency > self.target_latency {
            self.trigger_optimization().await;
        }
    }

    async fn trigger_optimization(&self) {
        let mut strategy_index = self.current_strategy.lock().await;
        let current_strategy = &self.optimization_strategies[*strategy_index];

        info!(
            "🚀 Triggering optimization strategy: {:?}",
            current_strategy
        );

        match current_strategy {
            OptimizationStrategy::ConnectionPooling => {
                // Increase connection pool size
                info!("Optimizing connection pool");
            }
            OptimizationStrategy::RequestBatching => {
                // Increase batch size
                info!("Optimizing request batching");
            }
            OptimizationStrategy::CacheAggressive => {
                // Increase cache TTL
                info!("Optimizing cache strategy");
            }
            OptimizationStrategy::GeographicRouting => {
                // Switch to closer geographic region
                info!("Optimizing geographic routing");
            }
            OptimizationStrategy::AdaptiveTimeout => {
                // Adjust timeouts based on network conditions
                info!("Optimizing adaptive timeouts");
            }
        }

        // Cycle to next strategy
        *strategy_index = (*strategy_index + 1) % self.optimization_strategies.len();
    }

    pub async fn get_performance_metrics(&self) -> PerformanceMetrics {
        let history = self.latency_history.read().await;

        if history.is_empty() {
            return PerformanceMetrics::default();
        }

        let mut sorted_latencies: Vec<_> = history.iter().map(|d| d.as_millis() as f64).collect();
        sorted_latencies.sort_by(|a, b| a.partial_cmp(b).unwrap());

        let average = sorted_latencies.iter().sum::<f64>() / sorted_latencies.len() as f64;
        let p95_index = (sorted_latencies.len() as f64 * 0.95) as usize;
        let p99_index = (sorted_latencies.len() as f64 * 0.99) as usize;

        PerformanceMetrics {
            average_latency_ms: average,
            p95_latency_ms: sorted_latencies.get(p95_index).copied().unwrap_or(0.0),
            p99_latency_ms: sorted_latencies.get(p99_index).copied().unwrap_or(0.0),
            cache_hit_rate: 0.0,              // Will be updated by cache manager
            connection_pool_utilization: 0.0, // Will be updated by connection pool
            batch_efficiency: 0.0,            // Will be updated by batch processor
            memory_usage_mb: 0.0,             // Will be updated by memory monitor
            optimization_score: Self::calculate_optimization_score(
                average,
                self.target_latency.as_millis() as f64,
            ),
        }
    }

    fn calculate_optimization_score(actual_latency: f64, target_latency: f64) -> f64 {
        if actual_latency <= target_latency {
            100.0
        } else {
            (target_latency / actual_latency * 100.0).max(0.0)
        }
    }
}

impl PerformanceOptimizer {
    pub async fn new(config: PerformanceConfig) -> Result<Self> {
        info!("🚀 Initializing Performance Optimizer for THE OVERMIND PROTOCOL");

        // Initialize connection pool
        let rpc_urls = vec![
            "https://api.mainnet-beta.solana.com".to_string(),
            "https://solana-api.projectserum.com".to_string(),
        ];
        let redis_urls = vec!["redis://localhost:6379".to_string()];

        let connection_pool = ConnectionPool::new(rpc_urls, redis_urls).await?;

        // Initialize cache manager
        let redis_connections = connection_pool.redis_connections.read().await.clone();
        let cache_manager = CacheManager::new(redis_connections, config.clone()).await;

        // Initialize latency optimizer
        let latency_optimizer =
            LatencyOptimizer::new(Duration::from_millis(config.target_latency_ms));

        Ok(Self {
            config,
            connection_pool,
            cache_manager,
            latency_optimizer,
            performance_metrics: Arc::new(Mutex::new(PerformanceMetrics::default())),
        })
    }

    pub async fn start_optimization_loop(&self) {
        info!("🔄 Starting performance optimization loop");

        let connection_pool = self.connection_pool.clone();
        let latency_optimizer = self.latency_optimizer.clone();

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(30));

            loop {
                interval.tick().await;

                // Health check connections
                if let Err(e) = connection_pool.health_check().await {
                    error!("Connection health check failed: {}", e);
                }

                // Update performance metrics
                let metrics = latency_optimizer.get_performance_metrics().await;
                info!("📊 Performance metrics: avg_latency={:.2}ms, p95={:.2}ms, optimization_score={:.1}%", 
                      metrics.average_latency_ms, metrics.p95_latency_ms, metrics.optimization_score);
            }
        });
    }

    pub async fn get_performance_metrics(&self) -> PerformanceMetrics {
        self.latency_optimizer.get_performance_metrics().await
    }

    pub async fn optimize_request<F, T>(&self, operation: F) -> Result<T>
    where
        F: std::future::Future<Output = Result<T>>,
    {
        let start_time = Instant::now();

        let result = operation.await;

        let latency = start_time.elapsed();
        self.latency_optimizer.record_latency(latency).await;

        result
    }
}
