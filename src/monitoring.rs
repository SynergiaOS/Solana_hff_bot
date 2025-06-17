// Monitoring and health check endpoints for SNIPERCOR
// Provides observability for HFT system performance

use axum::{extract::State, http::StatusCode, response::Json, routing::get, Router};
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use std::time::Instant;
use tracing::{info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthStatus {
    pub status: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub uptime_seconds: u64,
    pub version: String,
    pub components: ComponentHealth,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ComponentHealth {
    pub data_ingestor: ServiceStatus,
    pub strategy_engine: ServiceStatus,
    pub risk_manager: ServiceStatus,
    pub executor: ServiceStatus,
    pub persistence: ServiceStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceStatus {
    pub status: String,
    pub last_heartbeat: chrono::DateTime<chrono::Utc>,
    pub message_count: u64,
    pub error_count: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metrics {
    pub trading_metrics: TradingMetrics,
    pub performance_metrics: PerformanceMetrics,
    pub system_metrics: SystemMetrics,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingMetrics {
    pub total_signals: u64,
    pub approved_signals: u64,
    pub executed_trades: u64,
    pub total_volume: f64,
    pub total_pnl: f64,
    pub success_rate: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub avg_signal_latency_ms: f64,
    pub avg_execution_latency_ms: f64,
    pub max_latency_ms: f64,
    pub throughput_per_second: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    pub memory_usage_mb: f64,
    pub cpu_usage_percent: f64,
    pub active_connections: u32,
    pub queue_depths: QueueDepths,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueueDepths {
    pub market_data_queue: usize,
    pub signal_queue: usize,
    pub execution_queue: usize,
    pub persistence_queue: usize,
}

#[derive(Debug, Clone)]
pub struct MonitoringState {
    pub start_time: Instant,
    pub health: Arc<Mutex<ComponentHealth>>,
    pub metrics: Arc<Mutex<Metrics>>,
}

#[allow(dead_code)]
impl Default for MonitoringState {
    fn default() -> Self {
        Self::new()
    }
}

impl MonitoringState {
    pub fn new() -> Self {
        let now = chrono::Utc::now();

        Self {
            start_time: Instant::now(),
            health: Arc::new(Mutex::new(ComponentHealth {
                data_ingestor: ServiceStatus {
                    status: "starting".to_string(),
                    last_heartbeat: now,
                    message_count: 0,
                    error_count: 0,
                },
                strategy_engine: ServiceStatus {
                    status: "starting".to_string(),
                    last_heartbeat: now,
                    message_count: 0,
                    error_count: 0,
                },
                risk_manager: ServiceStatus {
                    status: "starting".to_string(),
                    last_heartbeat: now,
                    message_count: 0,
                    error_count: 0,
                },
                executor: ServiceStatus {
                    status: "starting".to_string(),
                    last_heartbeat: now,
                    message_count: 0,
                    error_count: 0,
                },
                persistence: ServiceStatus {
                    status: "starting".to_string(),
                    last_heartbeat: now,
                    message_count: 0,
                    error_count: 0,
                },
            })),
            metrics: Arc::new(Mutex::new(Metrics {
                trading_metrics: TradingMetrics {
                    total_signals: 0,
                    approved_signals: 0,
                    executed_trades: 0,
                    total_volume: 0.0,
                    total_pnl: 0.0,
                    success_rate: 0.0,
                },
                performance_metrics: PerformanceMetrics {
                    avg_signal_latency_ms: 0.0,
                    avg_execution_latency_ms: 0.0,
                    max_latency_ms: 0.0,
                    throughput_per_second: 0.0,
                },
                system_metrics: SystemMetrics {
                    memory_usage_mb: 0.0,
                    cpu_usage_percent: 0.0,
                    active_connections: 0,
                    queue_depths: QueueDepths {
                        market_data_queue: 0,
                        signal_queue: 0,
                        execution_queue: 0,
                        persistence_queue: 0,
                    },
                },
            })),
        }
    }

    pub fn update_component_health(
        &self,
        component: &str,
        status: &str,
        message_count: u64,
        error_count: u64,
    ) {
        if let Ok(mut health) = self.health.lock() {
            let now = chrono::Utc::now();

            match component {
                "data_ingestor" => {
                    health.data_ingestor.status = status.to_string();
                    health.data_ingestor.last_heartbeat = now;
                    health.data_ingestor.message_count = message_count;
                    health.data_ingestor.error_count = error_count;
                }
                "strategy_engine" => {
                    health.strategy_engine.status = status.to_string();
                    health.strategy_engine.last_heartbeat = now;
                    health.strategy_engine.message_count = message_count;
                    health.strategy_engine.error_count = error_count;
                }
                "risk_manager" => {
                    health.risk_manager.status = status.to_string();
                    health.risk_manager.last_heartbeat = now;
                    health.risk_manager.message_count = message_count;
                    health.risk_manager.error_count = error_count;
                }
                "executor" => {
                    health.executor.status = status.to_string();
                    health.executor.last_heartbeat = now;
                    health.executor.message_count = message_count;
                    health.executor.error_count = error_count;
                }
                "persistence" => {
                    health.persistence.status = status.to_string();
                    health.persistence.last_heartbeat = now;
                    health.persistence.message_count = message_count;
                    health.persistence.error_count = error_count;
                }
                _ => warn!("Unknown component: {}", component),
            }
        }
    }
}

// Health check endpoint
pub async fn health_check(
    State(state): State<MonitoringState>,
) -> Result<Json<HealthStatus>, StatusCode> {
    let uptime = state.start_time.elapsed().as_secs();

    let health = state
        .health
        .lock()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .clone();

    // Determine overall status
    let overall_status = if is_system_healthy(&health) {
        "healthy"
    } else {
        "unhealthy"
    };

    let health_status = HealthStatus {
        status: overall_status.to_string(),
        timestamp: chrono::Utc::now(),
        uptime_seconds: uptime,
        version: env!("CARGO_PKG_VERSION").to_string(),
        components: health,
    };

    info!("Health check requested - Status: {}", overall_status);

    Ok(Json(health_status))
}

// Readiness check endpoint
pub async fn readiness_check(
    State(state): State<MonitoringState>,
) -> Result<StatusCode, StatusCode> {
    let health = state
        .health
        .lock()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    if is_system_ready(&health) {
        Ok(StatusCode::OK)
    } else {
        Err(StatusCode::SERVICE_UNAVAILABLE)
    }
}

// Liveness check endpoint
pub async fn liveness_check() -> StatusCode {
    // Simple liveness check - if we can respond, we're alive
    StatusCode::OK
}

// Metrics endpoint
pub async fn metrics_endpoint(
    State(state): State<MonitoringState>,
) -> Result<Json<Metrics>, StatusCode> {
    let metrics = state
        .metrics
        .lock()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
        .clone();

    Ok(Json(metrics))
}

// Prometheus metrics endpoint
pub async fn prometheus_metrics(
    State(state): State<MonitoringState>,
) -> Result<String, StatusCode> {
    let metrics = state
        .metrics
        .lock()
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    let prometheus_format = format!(
        "# HELP sniper_total_signals Total number of trading signals generated\n\
         # TYPE sniper_total_signals counter\n\
         sniper_total_signals {}\n\
         \n\
         # HELP sniper_executed_trades Total number of executed trades\n\
         # TYPE sniper_executed_trades counter\n\
         sniper_executed_trades {}\n\
         \n\
         # HELP sniper_avg_latency_ms Average signal processing latency in milliseconds\n\
         # TYPE sniper_avg_latency_ms gauge\n\
         sniper_avg_latency_ms {}\n\
         \n\
         # HELP sniper_total_pnl Total profit and loss\n\
         # TYPE sniper_total_pnl gauge\n\
         sniper_total_pnl {}\n\
         \n\
         # HELP sniper_success_rate Trading success rate\n\
         # TYPE sniper_success_rate gauge\n\
         sniper_success_rate {}\n",
        metrics.trading_metrics.total_signals,
        metrics.trading_metrics.executed_trades,
        metrics.performance_metrics.avg_signal_latency_ms,
        metrics.trading_metrics.total_pnl,
        metrics.trading_metrics.success_rate
    );

    Ok(prometheus_format)
}

fn is_system_healthy(health: &ComponentHealth) -> bool {
    let now = chrono::Utc::now();
    let max_age = chrono::Duration::seconds(30); // 30 seconds max age for heartbeat

    let components = [
        &health.data_ingestor,
        &health.strategy_engine,
        &health.risk_manager,
        &health.executor,
        &health.persistence,
    ];

    for component in components {
        // Check if component is running and heartbeat is recent
        if component.status != "running"
            || (now - component.last_heartbeat) > max_age
            || component.error_count > 10
        {
            return false;
        }
    }

    true
}

fn is_system_ready(health: &ComponentHealth) -> bool {
    let components = [
        &health.data_ingestor,
        &health.strategy_engine,
        &health.risk_manager,
        &health.executor,
        &health.persistence,
    ];

    for component in components {
        if component.status == "starting" || component.status == "error" {
            return false;
        }
    }

    true
}

pub fn create_monitoring_router(state: MonitoringState) -> Router {
    Router::new()
        .route("/health", get(health_check))
        .route("/ready", get(readiness_check))
        .route("/live", get(liveness_check))
        .route("/metrics", get(metrics_endpoint))
        .route("/metrics/prometheus", get(prometheus_metrics))
        .with_state(state)
}
