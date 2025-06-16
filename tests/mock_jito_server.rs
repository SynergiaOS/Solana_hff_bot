// THE OVERMIND PROTOCOL - Mock Jito Bundle Server for Testing
// Simulates Jito Bundle API for comprehensive MEV protection testing

use axum::{
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;
use uuid::Uuid;

/// Mock Jito Bundle server for testing MEV protection
pub struct MockJitoServer {
    port: u16,
    metrics: Arc<Mutex<JitoMetrics>>,
    config: JitoServerConfig,
    bundles: Arc<Mutex<HashMap<String, BundleStatus>>>,
}

#[derive(Debug, Clone)]
pub struct JitoServerConfig {
    pub bundle_processing_delay_ms: u64,
    pub bundle_success_rate: f64, // 0.0 to 1.0
    pub simulate_network_congestion: bool,
    pub max_bundle_size: usize,
}

#[derive(Debug, Default)]
struct JitoMetrics {
    bundles_received: u64,
    bundles_processed: u64,
    bundles_failed: u64,
    avg_processing_time_ms: f64,
}

#[derive(Debug, Clone)]
enum BundleStatus {
    Pending,
    Processing,
    Confirmed,
    Failed(String),
}

#[derive(Debug, Deserialize)]
struct SendBundleRequest {
    transactions: Vec<String>, // Base64 encoded transactions
}

#[derive(Debug, Serialize)]
struct SendBundleResponse {
    result: String, // Bundle ID
}

#[derive(Debug, Serialize)]
struct BundleStatusResponse {
    bundle_id: String,
    status: String,
    confirmation_time_ms: Option<u64>,
    error: Option<String>,
}

impl Default for JitoServerConfig {
    fn default() -> Self {
        Self {
            bundle_processing_delay_ms: 100, // Realistic bundle processing time
            bundle_success_rate: 0.95,
            simulate_network_congestion: false,
            max_bundle_size: 5,
        }
    }
}

impl MockJitoServer {
    /// Create new mock Jito server
    pub fn new(port: u16, config: JitoServerConfig) -> Self {
        Self {
            port,
            metrics: Arc::new(Mutex::new(JitoMetrics::default())),
            config,
            bundles: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    /// Start the mock server
    pub async fn start(self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let port = self.port;
        let app = self.create_router();
        let addr = format!("0.0.0.0:{}", port);
        let listener = tokio::net::TcpListener::bind(&addr).await?;

        println!("⚡ Mock Jito Bundle Server listening on http://{}", addr);
        println!("📊 Health: http://{}/health", addr);
        println!("📦 Send Bundle: http://{}/api/v1/bundles", addr);

        axum::serve(listener, app).await?;
        Ok(())
    }

    /// Create router with all endpoints
    fn create_router(self) -> Router {
        let state = Arc::new(self);

        Router::new()
            .route("/health", get(jito_health_check))
            .route("/api/v1/bundles", post(send_bundle_endpoint))
            .route("/api/v1/bundles/:bundle_id", get(bundle_status_endpoint))
            .route("/metrics", get(jito_metrics_endpoint))
            .with_state(state)
    }

    /// Process bundle asynchronously
    async fn process_bundle(&self, bundle_id: String) {
        let processing_delay = if self.config.simulate_network_congestion {
            Duration::from_millis(self.config.bundle_processing_delay_ms * 3)
        } else {
            Duration::from_millis(self.config.bundle_processing_delay_ms)
        };
        
        // Set to processing
        {
            let mut bundles = self.bundles.lock().await;
            bundles.insert(bundle_id.clone(), BundleStatus::Processing);
        }
        
        tokio::time::sleep(processing_delay).await;
        
        // Determine final status
        use rand::Rng;
        let success = rand::thread_rng().gen::<f64>() < self.config.bundle_success_rate;
        
        let final_status = if success {
            BundleStatus::Confirmed
        } else {
            BundleStatus::Failed("Network congestion".to_string())
        };
        
        // Update status
        {
            let mut bundles = self.bundles.lock().await;
            bundles.insert(bundle_id, final_status);
        }
        
        // Update metrics
        {
            let mut metrics = self.metrics.lock().await;
            metrics.bundles_processed += 1;
            if !success {
                metrics.bundles_failed += 1;
            }
        }
    }
}

/// Health check endpoint
async fn jito_health_check() -> Json<Value> {
    Json(json!({
        "status": "healthy",
        "service": "mock-jito-bundle-api",
        "version": "1.0.0",
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "network": "devnet"
    }))
}

/// Send bundle endpoint
async fn send_bundle_endpoint(
    axum::extract::State(server): axum::extract::State<Arc<MockJitoServer>>,
    Json(request): Json<SendBundleRequest>,
) -> Result<Json<SendBundleResponse>, StatusCode> {
    let _start_time = Instant::now();
    
    // Validate bundle size
    if request.transactions.len() > server.config.max_bundle_size {
        return Err(StatusCode::BAD_REQUEST);
    }
    
    // Update metrics
    {
        let mut metrics = server.metrics.lock().await;
        metrics.bundles_received += 1;
    }
    
    // Generate bundle ID
    let bundle_id = format!("bundle_{}", Uuid::new_v4());
    
    // Add to pending bundles
    {
        let mut bundles = server.bundles.lock().await;
        bundles.insert(bundle_id.clone(), BundleStatus::Pending);
    }
    
    // Start async processing
    let server_clone = server.clone();
    let bundle_id_clone = bundle_id.clone();
    tokio::spawn(async move {
        server_clone.process_bundle(bundle_id_clone).await;
    });
    
    Ok(Json(SendBundleResponse {
        result: bundle_id,
    }))
}

/// Bundle status endpoint
async fn bundle_status_endpoint(
    axum::extract::State(server): axum::extract::State<Arc<MockJitoServer>>,
    axum::extract::Path(bundle_id): axum::extract::Path<String>,
) -> Result<Json<BundleStatusResponse>, StatusCode> {
    let bundles = server.bundles.lock().await;
    
    match bundles.get(&bundle_id) {
        Some(status) => {
            let (status_str, error) = match status {
                BundleStatus::Pending => ("pending", None),
                BundleStatus::Processing => ("processing", None),
                BundleStatus::Confirmed => ("confirmed", None),
                BundleStatus::Failed(err) => ("failed", Some(err.clone())),
            };
            
            Ok(Json(BundleStatusResponse {
                bundle_id,
                status: status_str.to_string(),
                confirmation_time_ms: if matches!(status, BundleStatus::Confirmed) {
                    Some(server.config.bundle_processing_delay_ms)
                } else {
                    None
                },
                error,
            }))
        }
        None => Err(StatusCode::NOT_FOUND),
    }
}

/// Metrics endpoint
async fn jito_metrics_endpoint(
    axum::extract::State(server): axum::extract::State<Arc<MockJitoServer>>,
) -> Json<Value> {
    let metrics = server.metrics.lock().await;
    let bundles = server.bundles.lock().await;
    
    let pending_count = bundles.values().filter(|s| matches!(s, BundleStatus::Pending)).count();
    let processing_count = bundles.values().filter(|s| matches!(s, BundleStatus::Processing)).count();
    let confirmed_count = bundles.values().filter(|s| matches!(s, BundleStatus::Confirmed)).count();
    let failed_count = bundles.values().filter(|s| matches!(s, BundleStatus::Failed(_))).count();
    
    Json(json!({
        "bundles_received": metrics.bundles_received,
        "bundles_processed": metrics.bundles_processed,
        "bundles_failed": metrics.bundles_failed,
        "success_rate": if metrics.bundles_processed > 0 {
            (metrics.bundles_processed - metrics.bundles_failed) as f64 / metrics.bundles_processed as f64
        } else {
            0.0
        },
        "bundle_status_counts": {
            "pending": pending_count,
            "processing": processing_count,
            "confirmed": confirmed_count,
            "failed": failed_count
        },
        "config": {
            "bundle_processing_delay_ms": server.config.bundle_processing_delay_ms,
            "bundle_success_rate": server.config.bundle_success_rate,
            "simulate_network_congestion": server.config.simulate_network_congestion,
            "max_bundle_size": server.config.max_bundle_size
        }
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mock_jito_server_creation() {
        let config = JitoServerConfig::default();
        let server = MockJitoServer::new(3002, config);
        assert_eq!(server.port, 3002);
    }

    #[tokio::test]
    async fn test_bundle_processing() {
        let config = JitoServerConfig {
            bundle_processing_delay_ms: 10,
            bundle_success_rate: 1.0,
            simulate_network_congestion: false,
            max_bundle_size: 5,
        };
        let server = MockJitoServer::new(3002, config);
        
        let bundle_id = "test_bundle".to_string();
        server.process_bundle(bundle_id.clone()).await;
        
        let bundles = server.bundles.lock().await;
        assert!(matches!(bundles.get(&bundle_id), Some(BundleStatus::Confirmed)));
    }

    #[tokio::test]
    async fn test_health_check() {
        let response = jito_health_check().await;
        assert_eq!(response.0["status"], "healthy");
        assert_eq!(response.0["service"], "mock-jito-bundle-api");
    }
}
