//! Real-time Performance Monitor Module
//!
//! Advanced real-time monitoring and alerting system for THE OVERMIND PROTOCOL
//! with sub-millisecond precision and adaptive thresholds.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::sync::{broadcast, Mutex, RwLock};
use tracing::{debug, error, info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MonitoringConfig {
    pub latency_threshold_ms: f64,
    pub throughput_threshold_tps: f64,
    pub error_rate_threshold: f64,
    pub memory_threshold_mb: f64,
    pub cpu_threshold_percent: f64,
    pub alert_cooldown_seconds: u64,
    pub metrics_retention_minutes: u32,
    pub sampling_interval_ms: u64,
    pub adaptive_thresholds_enabled: bool,
}

impl Default for MonitoringConfig {
    fn default() -> Self {
        Self {
            latency_threshold_ms: 25.0,      // Sub-25ms target
            throughput_threshold_tps: 100.0, // 100 TPS minimum
            error_rate_threshold: 0.01,      // 1% error rate
            memory_threshold_mb: 1024.0,     // 1GB memory threshold
            cpu_threshold_percent: 80.0,     // 80% CPU threshold
            alert_cooldown_seconds: 300,     // 5 minutes between alerts
            metrics_retention_minutes: 60,   // Keep 1 hour of metrics
            sampling_interval_ms: 100,       // Sample every 100ms
            adaptive_thresholds_enabled: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetric {
    pub timestamp: u64,
    pub metric_type: MetricType,
    pub value: f64,
    pub tags: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum MetricType {
    Latency,
    Throughput,
    ErrorRate,
    MemoryUsage,
    CpuUsage,
    NetworkLatency,
    DiskIo,
    CacheHitRate,
    ConnectionPoolUtilization,
    TradingSignalLatency,
    ExecutionLatency,
    AIDecisionLatency,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alert {
    pub id: String,
    pub timestamp: u64,
    pub severity: AlertSeverity,
    pub metric_type: MetricType,
    pub message: String,
    pub current_value: f64,
    pub threshold: f64,
    pub tags: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AlertSeverity {
    Info,
    Warning,
    Critical,
    Emergency,
}

#[derive(Debug, Clone)]
pub struct MetricWindow {
    values: VecDeque<(u64, f64)>, // (timestamp, value)
    window_duration: Duration,
}

impl MetricWindow {
    pub fn new(window_duration: Duration) -> Self {
        Self {
            values: VecDeque::new(),
            window_duration,
        }
    }

    pub fn add_value(&mut self, timestamp: u64, value: f64) {
        self.values.push_back((timestamp, value));

        // Remove old values outside the window
        let cutoff = timestamp.saturating_sub(self.window_duration.as_millis() as u64);
        while let Some(&(ts, _)) = self.values.front() {
            if ts < cutoff {
                self.values.pop_front();
            } else {
                break;
            }
        }
    }

    pub fn get_average(&self) -> f64 {
        if self.values.is_empty() {
            return 0.0;
        }

        let sum: f64 = self.values.iter().map(|(_, v)| v).sum();
        sum / self.values.len() as f64
    }

    pub fn get_percentile(&self, percentile: f64) -> f64 {
        if self.values.is_empty() {
            return 0.0;
        }

        let mut sorted_values: Vec<f64> = self.values.iter().map(|(_, v)| *v).collect();
        sorted_values.sort_by(|a, b| a.partial_cmp(b).unwrap());

        let index = (sorted_values.len() as f64 * percentile / 100.0) as usize;
        sorted_values
            .get(index.min(sorted_values.len() - 1))
            .copied()
            .unwrap_or(0.0)
    }

    pub fn get_max(&self) -> f64 {
        self.values.iter().map(|(_, v)| *v).fold(0.0, f64::max)
    }

    pub fn get_min(&self) -> f64 {
        self.values
            .iter()
            .map(|(_, v)| *v)
            .fold(f64::INFINITY, f64::min)
    }

    pub fn get_count(&self) -> usize {
        self.values.len()
    }
}

#[derive(Debug, Clone)]
pub struct AdaptiveThreshold {
    baseline: f64,
    multiplier: f64,
    min_threshold: f64,
    max_threshold: f64,
    adaptation_rate: f64,
}

impl AdaptiveThreshold {
    pub fn new(initial_threshold: f64, multiplier: f64) -> Self {
        Self {
            baseline: initial_threshold,
            multiplier,
            min_threshold: initial_threshold * 0.5,
            max_threshold: initial_threshold * 3.0,
            adaptation_rate: 0.1,
        }
    }

    pub fn update(&mut self, current_average: f64) {
        // Exponential moving average for baseline
        self.baseline =
            self.baseline * (1.0 - self.adaptation_rate) + current_average * self.adaptation_rate;
    }

    pub fn get_threshold(&self) -> f64 {
        (self.baseline * self.multiplier)
            .max(self.min_threshold)
            .min(self.max_threshold)
    }
}

pub struct RealtimeMonitor {
    config: MonitoringConfig,
    metrics: Arc<RwLock<HashMap<MetricType, MetricWindow>>>,
    adaptive_thresholds: Arc<RwLock<HashMap<MetricType, AdaptiveThreshold>>>,
    alert_sender: broadcast::Sender<Alert>,
    last_alert_times: Arc<Mutex<HashMap<String, Instant>>>,
    monitoring_tasks: Vec<tokio::task::JoinHandle<()>>,
}

impl RealtimeMonitor {
    pub fn new(config: MonitoringConfig) -> Self {
        let (alert_sender, _) = broadcast::channel(1000);
        let window_duration = Duration::from_secs(config.metrics_retention_minutes as u64 * 60);

        let mut metrics = HashMap::new();
        let mut adaptive_thresholds = HashMap::new();

        // Initialize metric windows and adaptive thresholds
        for metric_type in [
            MetricType::Latency,
            MetricType::Throughput,
            MetricType::ErrorRate,
            MetricType::MemoryUsage,
            MetricType::CpuUsage,
            MetricType::TradingSignalLatency,
            MetricType::ExecutionLatency,
            MetricType::AIDecisionLatency,
        ] {
            metrics.insert(metric_type.clone(), MetricWindow::new(window_duration));

            let threshold = match metric_type {
                MetricType::Latency
                | MetricType::TradingSignalLatency
                | MetricType::ExecutionLatency
                | MetricType::AIDecisionLatency => config.latency_threshold_ms,
                MetricType::Throughput => config.throughput_threshold_tps,
                MetricType::ErrorRate => config.error_rate_threshold,
                MetricType::MemoryUsage => config.memory_threshold_mb,
                MetricType::CpuUsage => config.cpu_threshold_percent,
                _ => 100.0,
            };

            adaptive_thresholds.insert(metric_type, AdaptiveThreshold::new(threshold, 1.5));
        }

        Self {
            config,
            metrics: Arc::new(RwLock::new(metrics)),
            adaptive_thresholds: Arc::new(RwLock::new(adaptive_thresholds)),
            alert_sender,
            last_alert_times: Arc::new(Mutex::new(HashMap::new())),
            monitoring_tasks: Vec::new(),
        }
    }

    pub async fn start(&mut self) -> Result<()> {
        info!("📊 Starting Real-time Performance Monitor for THE OVERMIND PROTOCOL");

        // Start system metrics collection
        self.start_system_metrics_collection().await;

        // Start adaptive threshold updates
        if self.config.adaptive_thresholds_enabled {
            self.start_adaptive_threshold_updates().await;
        }

        // Start alert processing
        self.start_alert_processing().await;

        info!("✅ Real-time Performance Monitor started successfully");
        Ok(())
    }

    async fn start_system_metrics_collection(&mut self) {
        let metrics = self.metrics.clone();
        let config = self.config.clone();

        let handle = tokio::spawn(async move {
            let mut interval =
                tokio::time::interval(Duration::from_millis(config.sampling_interval_ms));

            loop {
                interval.tick().await;
                let timestamp = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_millis() as u64;

                // Collect system metrics
                let cpu_usage = Self::get_cpu_usage().await;
                let memory_usage = Self::get_memory_usage().await;
                let network_latency = Self::get_network_latency().await;

                // Update metrics
                let mut metrics_guard = metrics.write().await;

                if let Some(window) = metrics_guard.get_mut(&MetricType::CpuUsage) {
                    window.add_value(timestamp, cpu_usage);
                }

                if let Some(window) = metrics_guard.get_mut(&MetricType::MemoryUsage) {
                    window.add_value(timestamp, memory_usage);
                }

                if let Some(window) = metrics_guard.get_mut(&MetricType::NetworkLatency) {
                    window.add_value(timestamp, network_latency);
                }
            }
        });

        self.monitoring_tasks.push(handle);
    }

    async fn start_adaptive_threshold_updates(&mut self) {
        let metrics = self.metrics.clone();
        let adaptive_thresholds = self.adaptive_thresholds.clone();

        let handle = tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(60)); // Update every minute

            loop {
                interval.tick().await;

                let metrics_guard = metrics.read().await;
                let mut thresholds_guard = adaptive_thresholds.write().await;

                for (metric_type, window) in metrics_guard.iter() {
                    if let Some(threshold) = thresholds_guard.get_mut(metric_type) {
                        let current_average = window.get_average();
                        threshold.update(current_average);

                        debug!(
                            "Updated adaptive threshold for {:?}: {:.2}",
                            metric_type,
                            threshold.get_threshold()
                        );
                    }
                }
            }
        });

        self.monitoring_tasks.push(handle);
    }

    async fn start_alert_processing(&mut self) {
        let metrics = self.metrics.clone();
        let adaptive_thresholds = self.adaptive_thresholds.clone();
        let alert_sender = self.alert_sender.clone();
        let last_alert_times = self.last_alert_times.clone();
        let config = self.config.clone();

        let handle = tokio::spawn(async move {
            let mut interval =
                tokio::time::interval(Duration::from_millis(config.sampling_interval_ms));

            loop {
                interval.tick().await;

                let metrics_guard = metrics.read().await;
                let thresholds_guard = adaptive_thresholds.read().await;
                let mut alert_times_guard = last_alert_times.lock().await;

                for (metric_type, window) in metrics_guard.iter() {
                    if let Some(threshold_config) = thresholds_guard.get(metric_type) {
                        let current_value = window.get_average();
                        let threshold = if config.adaptive_thresholds_enabled {
                            threshold_config.get_threshold()
                        } else {
                            match metric_type {
                                MetricType::Latency
                                | MetricType::TradingSignalLatency
                                | MetricType::ExecutionLatency
                                | MetricType::AIDecisionLatency => config.latency_threshold_ms,
                                MetricType::Throughput => config.throughput_threshold_tps,
                                MetricType::ErrorRate => config.error_rate_threshold,
                                MetricType::MemoryUsage => config.memory_threshold_mb,
                                MetricType::CpuUsage => config.cpu_threshold_percent,
                                _ => 100.0,
                            }
                        };

                        // Check if threshold is exceeded
                        let should_alert = match metric_type {
                            MetricType::Throughput => current_value < threshold, // Lower is worse for throughput
                            _ => current_value > threshold, // Higher is worse for others
                        };

                        if should_alert {
                            let alert_key = format!("{:?}", metric_type);
                            let now = Instant::now();

                            // Check cooldown
                            let should_send_alert =
                                if let Some(last_alert) = alert_times_guard.get(&alert_key) {
                                    now.duration_since(*last_alert).as_secs()
                                        >= config.alert_cooldown_seconds
                                } else {
                                    true
                                };

                            if should_send_alert {
                                let severity = Self::determine_alert_severity(
                                    current_value,
                                    threshold,
                                    metric_type,
                                );
                                let alert = Alert {
                                    id: uuid::Uuid::new_v4().to_string(),
                                    timestamp: SystemTime::now()
                                        .duration_since(UNIX_EPOCH)
                                        .unwrap()
                                        .as_millis()
                                        as u64,
                                    severity,
                                    metric_type: metric_type.clone(),
                                    message: Self::generate_alert_message(
                                        metric_type,
                                        current_value,
                                        threshold,
                                    ),
                                    current_value,
                                    threshold,
                                    tags: HashMap::new(),
                                };

                                if let Err(e) = alert_sender.send(alert) {
                                    error!("Failed to send alert: {}", e);
                                } else {
                                    alert_times_guard.insert(alert_key, now);
                                }
                            }
                        }
                    }
                }
            }
        });

        self.monitoring_tasks.push(handle);
    }

    pub async fn record_metric(
        &self,
        metric_type: MetricType,
        value: f64,
        _tags: Option<HashMap<String, String>>,
    ) {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        let mut metrics_guard = self.metrics.write().await;
        if let Some(window) = metrics_guard.get_mut(&metric_type) {
            window.add_value(timestamp, value);
        }

        // Log high-priority metrics
        match metric_type {
            MetricType::TradingSignalLatency
            | MetricType::ExecutionLatency
            | MetricType::AIDecisionLatency => {
                if value > self.config.latency_threshold_ms {
                    warn!(
                        "High latency detected for {:?}: {:.2}ms",
                        metric_type, value
                    );
                }
            }
            _ => {}
        }
    }

    pub async fn get_metric_summary(&self, metric_type: &MetricType) -> Option<MetricSummary> {
        let metrics_guard = self.metrics.read().await;
        if let Some(window) = metrics_guard.get(metric_type) {
            Some(MetricSummary {
                average: window.get_average(),
                p50: window.get_percentile(50.0),
                p95: window.get_percentile(95.0),
                p99: window.get_percentile(99.0),
                max: window.get_max(),
                min: window.get_min(),
                count: window.get_count(),
            })
        } else {
            None
        }
    }

    pub fn subscribe_to_alerts(&self) -> broadcast::Receiver<Alert> {
        self.alert_sender.subscribe()
    }

    async fn get_cpu_usage() -> f64 {
        // In a real implementation, this would use system APIs
        // For now, return a simulated value
        rand::random::<f64>() * 100.0
    }

    async fn get_memory_usage() -> f64 {
        // In a real implementation, this would use system APIs
        // For now, return a simulated value
        500.0 + rand::random::<f64>() * 500.0
    }

    async fn get_network_latency() -> f64 {
        // In a real implementation, this would ping network endpoints
        // For now, return a simulated value
        10.0 + rand::random::<f64>() * 20.0
    }

    fn determine_alert_severity(
        current_value: f64,
        threshold: f64,
        metric_type: &MetricType,
    ) -> AlertSeverity {
        let ratio = current_value / threshold;

        match metric_type {
            MetricType::Latency
            | MetricType::TradingSignalLatency
            | MetricType::ExecutionLatency
            | MetricType::AIDecisionLatency => {
                if ratio > 3.0 {
                    AlertSeverity::Emergency
                } else if ratio > 2.0 {
                    AlertSeverity::Critical
                } else if ratio > 1.5 {
                    AlertSeverity::Warning
                } else {
                    AlertSeverity::Info
                }
            }
            _ => {
                if ratio > 2.0 {
                    AlertSeverity::Critical
                } else if ratio > 1.5 {
                    AlertSeverity::Warning
                } else {
                    AlertSeverity::Info
                }
            }
        }
    }

    fn generate_alert_message(
        metric_type: &MetricType,
        current_value: f64,
        threshold: f64,
    ) -> String {
        match metric_type {
            MetricType::Latency => format!(
                "High latency detected: {:.2}ms (threshold: {:.2}ms)",
                current_value, threshold
            ),
            MetricType::TradingSignalLatency => format!(
                "Trading signal latency exceeded: {:.2}ms (threshold: {:.2}ms)",
                current_value, threshold
            ),
            MetricType::ExecutionLatency => format!(
                "Execution latency exceeded: {:.2}ms (threshold: {:.2}ms)",
                current_value, threshold
            ),
            MetricType::AIDecisionLatency => format!(
                "AI decision latency exceeded: {:.2}ms (threshold: {:.2}ms)",
                current_value, threshold
            ),
            MetricType::Throughput => format!(
                "Low throughput detected: {:.2} TPS (threshold: {:.2} TPS)",
                current_value, threshold
            ),
            MetricType::ErrorRate => format!(
                "High error rate detected: {:.2}% (threshold: {:.2}%)",
                current_value * 100.0,
                threshold * 100.0
            ),
            MetricType::MemoryUsage => format!(
                "High memory usage detected: {:.2}MB (threshold: {:.2}MB)",
                current_value, threshold
            ),
            MetricType::CpuUsage => format!(
                "High CPU usage detected: {:.2}% (threshold: {:.2}%)",
                current_value, threshold
            ),
            _ => format!(
                "Threshold exceeded for {:?}: {:.2} (threshold: {:.2})",
                metric_type, current_value, threshold
            ),
        }
    }

    pub async fn shutdown(&mut self) -> Result<()> {
        info!("🛑 Shutting down Real-time Performance Monitor");

        // Cancel all monitoring tasks
        for handle in self.monitoring_tasks.drain(..) {
            handle.abort();
        }

        info!("✅ Real-time Performance Monitor shut down successfully");
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetricSummary {
    pub average: f64,
    pub p50: f64,
    pub p95: f64,
    pub p99: f64,
    pub max: f64,
    pub min: f64,
    pub count: usize,
}
