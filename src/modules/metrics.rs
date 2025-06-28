//! Metrics and Monitoring Module
//!
//! Provides comprehensive performance metrics, latency tracking,
//! and monitoring integration for THE OVERMIND PROTOCOL.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tracing::{debug, info};

/// Performance metrics for THE OVERMIND PROTOCOL
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PerformanceMetrics {
    /// Trading metrics
    pub trading: TradingMetrics,
    /// System performance metrics
    pub system: SystemMetrics,
    /// Network latency metrics
    pub network: NetworkMetrics,
    /// AI optimization metrics
    pub ai: AiMetrics,
}

/// Trading-specific metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingMetrics {
    /// Total number of trades executed
    pub total_trades: u64,
    /// Successful trades
    pub successful_trades: u64,
    /// Failed trades
    pub failed_trades: u64,
    /// Total volume traded (in USD)
    pub total_volume_usd: f64,
    /// Average trade size
    pub average_trade_size: f64,
    /// Win rate percentage
    pub win_rate: f64,
    /// Total profit/loss
    pub total_pnl: f64,
    /// Average execution time (ms)
    pub avg_execution_time_ms: f64,
    /// Best execution time (ms)
    pub best_execution_time_ms: f64,
    /// Worst execution time (ms)
    pub worst_execution_time_ms: f64,
}

/// System performance metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    /// CPU usage percentage
    pub cpu_usage: f64,
    /// Memory usage in MB
    pub memory_usage_mb: f64,
    /// System uptime in seconds
    pub uptime_seconds: u64,
    /// Number of active connections
    pub active_connections: u32,
    /// Requests per second
    pub requests_per_second: f64,
    /// Error rate percentage
    pub error_rate: f64,
}

/// Network latency metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkMetrics {
    /// RPC latency (ms)
    pub rpc_latency_ms: f64,
    /// WebSocket latency (ms)
    pub websocket_latency_ms: f64,
    /// TensorZero API latency (ms)
    pub tensorzero_latency_ms: f64,
    /// Jito bundle latency (ms)
    pub jito_latency_ms: f64,
    /// DEX API latency (ms)
    pub dex_latency_ms: f64,
}

/// AI optimization metrics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiMetrics {
    /// Number of AI optimizations performed
    pub optimizations_performed: u64,
    /// Average optimization time (ms)
    pub avg_optimization_time_ms: f64,
    /// AI confidence score average
    pub avg_confidence_score: f64,
    /// Number of successful optimizations
    pub successful_optimizations: u64,
    /// Optimization success rate
    pub optimization_success_rate: f64,
}

/// Latency tracker for measuring operation performance
#[derive(Debug)]
pub struct LatencyTracker {
    start_time: Instant,
    operation_name: String,
}

impl LatencyTracker {
    /// Start tracking latency for an operation
    pub fn start(operation_name: &str) -> Self {
        debug!("⏱️ Starting latency tracking for: {}", operation_name);
        Self {
            start_time: Instant::now(),
            operation_name: operation_name.to_string(),
        }
    }

    /// Finish tracking and return elapsed time
    pub fn finish(self) -> Duration {
        let elapsed = self.start_time.elapsed();
        info!(
            "✅ {} completed in {}ms",
            self.operation_name,
            elapsed.as_millis()
        );
        elapsed
    }

    /// Finish tracking with a custom message
    pub fn finish_with_message(self, message: &str) -> Duration {
        let elapsed = self.start_time.elapsed();
        info!(
            "✅ {} - {} ({}ms)",
            self.operation_name,
            message,
            elapsed.as_millis()
        );
        elapsed
    }
}

/// Metrics collector for THE OVERMIND PROTOCOL
pub struct MetricsCollector {
    /// Current metrics
    metrics: Arc<Mutex<PerformanceMetrics>>,
    /// Latency measurements
    latency_measurements: Arc<Mutex<HashMap<String, Vec<Duration>>>>,
    /// Start time for uptime calculation
    start_time: Instant,
}

impl MetricsCollector {
    /// Create a new metrics collector
    pub fn new() -> Self {
        Self {
            metrics: Arc::new(Mutex::new(PerformanceMetrics::default())),
            latency_measurements: Arc::new(Mutex::new(HashMap::new())),
            start_time: Instant::now(),
        }
    }

    /// Record a successful trade
    pub fn record_successful_trade(&self, volume_usd: f64, execution_time: Duration) {
        if let Ok(mut metrics) = self.metrics.lock() {
            metrics.trading.total_trades += 1;
            metrics.trading.successful_trades += 1;
            metrics.trading.total_volume_usd += volume_usd;

            // Update execution time metrics
            let execution_ms = execution_time.as_millis() as f64;
            metrics.trading.avg_execution_time_ms = (metrics.trading.avg_execution_time_ms
                * (metrics.trading.total_trades - 1) as f64
                + execution_ms)
                / metrics.trading.total_trades as f64;

            if metrics.trading.best_execution_time_ms == 0.0
                || execution_ms < metrics.trading.best_execution_time_ms
            {
                metrics.trading.best_execution_time_ms = execution_ms;
            }

            if execution_ms > metrics.trading.worst_execution_time_ms {
                metrics.trading.worst_execution_time_ms = execution_ms;
            }

            // Update win rate
            metrics.trading.win_rate = (metrics.trading.successful_trades as f64
                / metrics.trading.total_trades as f64)
                * 100.0;
        }
    }

    /// Record a failed trade
    pub fn record_failed_trade(&self) {
        if let Ok(mut metrics) = self.metrics.lock() {
            metrics.trading.total_trades += 1;
            metrics.trading.failed_trades += 1;

            // Update win rate
            metrics.trading.win_rate = (metrics.trading.successful_trades as f64
                / metrics.trading.total_trades as f64)
                * 100.0;
        }
    }

    /// Record latency measurement
    pub fn record_latency(&self, operation: &str, latency: Duration) {
        if let Ok(mut measurements) = self.latency_measurements.lock() {
            measurements
                .entry(operation.to_string())
                .or_insert_with(Vec::new)
                .push(latency);
        }

        // Update specific latency metrics
        if let Ok(mut metrics) = self.metrics.lock() {
            let latency_ms = latency.as_millis() as f64;

            match operation {
                "rpc_call" => metrics.network.rpc_latency_ms = latency_ms,
                "websocket" => metrics.network.websocket_latency_ms = latency_ms,
                "tensorzero" => metrics.network.tensorzero_latency_ms = latency_ms,
                "jito_bundle" => metrics.network.jito_latency_ms = latency_ms,
                "dex_api" => metrics.network.dex_latency_ms = latency_ms,
                _ => {}
            }
        }
    }

    /// Record AI optimization
    pub fn record_ai_optimization(&self, success: bool, confidence: f64, duration: Duration) {
        if let Ok(mut metrics) = self.metrics.lock() {
            metrics.ai.optimizations_performed += 1;

            if success {
                metrics.ai.successful_optimizations += 1;
            }

            // Update average optimization time
            let duration_ms = duration.as_millis() as f64;
            metrics.ai.avg_optimization_time_ms = (metrics.ai.avg_optimization_time_ms
                * (metrics.ai.optimizations_performed - 1) as f64
                + duration_ms)
                / metrics.ai.optimizations_performed as f64;

            // Update average confidence score
            metrics.ai.avg_confidence_score = (metrics.ai.avg_confidence_score
                * (metrics.ai.optimizations_performed - 1) as f64
                + confidence)
                / metrics.ai.optimizations_performed as f64;

            // Update success rate
            metrics.ai.optimization_success_rate = (metrics.ai.successful_optimizations as f64
                / metrics.ai.optimizations_performed as f64)
                * 100.0;
        }
    }

    /// Update system metrics
    pub fn update_system_metrics(
        &self,
        cpu_usage: f64,
        memory_usage_mb: f64,
        active_connections: u32,
    ) {
        if let Ok(mut metrics) = self.metrics.lock() {
            metrics.system.cpu_usage = cpu_usage;
            metrics.system.memory_usage_mb = memory_usage_mb;
            metrics.system.active_connections = active_connections;
            metrics.system.uptime_seconds = self.start_time.elapsed().as_secs();
        }
    }

    /// Get current metrics snapshot
    pub fn get_metrics(&self) -> PerformanceMetrics {
        self.metrics.lock().unwrap().clone()
    }

    /// Get average latency for an operation
    pub fn get_average_latency(&self, operation: &str) -> Option<Duration> {
        if let Ok(measurements) = self.latency_measurements.lock() {
            if let Some(latencies) = measurements.get(operation) {
                if !latencies.is_empty() {
                    let total: Duration = latencies.iter().sum();
                    return Some(total / latencies.len() as u32);
                }
            }
        }
        None
    }

    /// Export metrics in Prometheus format
    pub fn export_prometheus_metrics(&self) -> String {
        let metrics = self.get_metrics();

        format!(
            "# HELP overmind_trades_total Total number of trades executed\n\
             # TYPE overmind_trades_total counter\n\
             overmind_trades_total {}\n\
             \n\
             # HELP overmind_trades_successful Number of successful trades\n\
             # TYPE overmind_trades_successful counter\n\
             overmind_trades_successful {}\n\
             \n\
             # HELP overmind_execution_time_ms Average execution time in milliseconds\n\
             # TYPE overmind_execution_time_ms gauge\n\
             overmind_execution_time_ms {}\n\
             \n\
             # HELP overmind_rpc_latency_ms RPC latency in milliseconds\n\
             # TYPE overmind_rpc_latency_ms gauge\n\
             overmind_rpc_latency_ms {}\n\
             \n\
             # HELP overmind_ai_optimizations_total Total AI optimizations performed\n\
             # TYPE overmind_ai_optimizations_total counter\n\
             overmind_ai_optimizations_total {}\n\
             \n\
             # HELP overmind_system_uptime_seconds System uptime in seconds\n\
             # TYPE overmind_system_uptime_seconds counter\n\
             overmind_system_uptime_seconds {}\n",
            metrics.trading.total_trades,
            metrics.trading.successful_trades,
            metrics.trading.avg_execution_time_ms,
            metrics.network.rpc_latency_ms,
            metrics.ai.optimizations_performed,
            metrics.system.uptime_seconds
        )
    }

    /// Log performance summary
    pub fn log_performance_summary(&self) {
        let metrics = self.get_metrics();

        info!("📊 PERFORMANCE SUMMARY:");
        info!(
            "  Trading: {} trades, {:.2}% win rate, ${:.2} volume",
            metrics.trading.total_trades,
            metrics.trading.win_rate,
            metrics.trading.total_volume_usd
        );
        info!(
            "  Execution: {:.1}ms avg, {:.1}ms best, {:.1}ms worst",
            metrics.trading.avg_execution_time_ms,
            metrics.trading.best_execution_time_ms,
            metrics.trading.worst_execution_time_ms
        );
        info!(
            "  Network: {:.1}ms RPC, {:.1}ms TensorZero, {:.1}ms Jito",
            metrics.network.rpc_latency_ms,
            metrics.network.tensorzero_latency_ms,
            metrics.network.jito_latency_ms
        );
        info!(
            "  AI: {} optimizations, {:.2}% success rate, {:.3} avg confidence",
            metrics.ai.optimizations_performed,
            metrics.ai.optimization_success_rate,
            metrics.ai.avg_confidence_score
        );
        info!(
            "  System: {:.1}% CPU, {:.1}MB RAM, {}s uptime",
            metrics.system.cpu_usage, metrics.system.memory_usage_mb, metrics.system.uptime_seconds
        );
    }
}

impl Default for TradingMetrics {
    fn default() -> Self {
        Self {
            total_trades: 0,
            successful_trades: 0,
            failed_trades: 0,
            total_volume_usd: 0.0,
            average_trade_size: 0.0,
            win_rate: 0.0,
            total_pnl: 0.0,
            avg_execution_time_ms: 0.0,
            best_execution_time_ms: 0.0,
            worst_execution_time_ms: 0.0,
        }
    }
}

impl Default for SystemMetrics {
    fn default() -> Self {
        Self {
            cpu_usage: 0.0,
            memory_usage_mb: 0.0,
            uptime_seconds: 0,
            active_connections: 0,
            requests_per_second: 0.0,
            error_rate: 0.0,
        }
    }
}

impl Default for NetworkMetrics {
    fn default() -> Self {
        Self {
            rpc_latency_ms: 0.0,
            websocket_latency_ms: 0.0,
            tensorzero_latency_ms: 0.0,
            jito_latency_ms: 0.0,
            dex_latency_ms: 0.0,
        }
    }
}

impl Default for AiMetrics {
    fn default() -> Self {
        Self {
            optimizations_performed: 0,
            avg_optimization_time_ms: 0.0,
            avg_confidence_score: 0.0,
            successful_optimizations: 0,
            optimization_success_rate: 0.0,
        }
    }
}

impl Default for MetricsCollector {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_metrics_collector_creation() {
        let collector = MetricsCollector::new();
        let metrics = collector.get_metrics();
        assert_eq!(metrics.trading.total_trades, 0);
    }

    #[test]
    fn test_latency_tracker() {
        let tracker = LatencyTracker::start("test_operation");
        std::thread::sleep(Duration::from_millis(10));
        let elapsed = tracker.finish();
        assert!(elapsed.as_millis() >= 10);
    }

    #[test]
    fn test_trade_recording() {
        let collector = MetricsCollector::new();
        collector.record_successful_trade(100.0, Duration::from_millis(50));

        let metrics = collector.get_metrics();
        assert_eq!(metrics.trading.total_trades, 1);
        assert_eq!(metrics.trading.successful_trades, 1);
        assert_eq!(metrics.trading.total_volume_usd, 100.0);
    }
}
