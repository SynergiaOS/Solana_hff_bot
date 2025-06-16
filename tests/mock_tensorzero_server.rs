// THE OVERMIND PROTOCOL - Mock TensorZero Gateway Server for Testing
// Provides realistic TensorZero API responses for comprehensive testing

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

/// Mock TensorZero server for testing THE OVERMIND PROTOCOL
pub struct MockTensorZeroServer {
    port: u16,
    metrics: Arc<Mutex<ServerMetrics>>,
    config: MockServerConfig,
}

#[derive(Debug, Clone)]
pub struct MockServerConfig {
    pub response_delay_ms: u64,
    pub error_rate: f64, // 0.0 to 1.0
    pub ai_confidence_range: (f64, f64),
    pub simulate_high_latency: bool,
}

#[derive(Debug, Default)]
struct ServerMetrics {
    requests_received: u64,
    responses_sent: u64,
    errors_generated: u64,
    avg_response_time_ms: f64,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct InferenceRequest {
    model_name: String,
    input: InferenceInput,
    stream: bool,
    tags: HashMap<String, String>,
}

#[derive(Debug, Deserialize)]
struct InferenceInput {
    messages: Vec<Message>,
}

#[derive(Debug, Deserialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Debug, Serialize)]
struct InferenceResponse {
    inference_id: Uuid,
    episode_id: Uuid,
    variant_name: String,
    content: Vec<ContentBlock>,
    usage: Option<Usage>,
}

#[derive(Debug, Serialize)]
struct ContentBlock {
    #[serde(rename = "type")]
    content_type: String,
    text: String,
}

#[derive(Debug, Serialize)]
struct Usage {
    input_tokens: u32,
    output_tokens: u32,
}

impl Default for MockServerConfig {
    fn default() -> Self {
        Self {
            response_delay_ms: 50, // Realistic AI response time
            error_rate: 0.0,
            ai_confidence_range: (0.6, 0.95),
            simulate_high_latency: false,
        }
    }
}

impl MockTensorZeroServer {
    /// Create new mock TensorZero server
    pub fn new(port: u16, config: MockServerConfig) -> Self {
        Self {
            port,
            metrics: Arc::new(Mutex::new(ServerMetrics::default())),
            config,
        }
    }

    /// Start the mock server
    pub async fn start(self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        let port = self.port;
        let app = self.create_router();
        let addr = format!("0.0.0.0:{}", port);
        let listener = tokio::net::TcpListener::bind(&addr).await?;

        println!("🤖 Mock TensorZero Server listening on http://{}", addr);
        println!("📊 Health: http://{}/health", addr);
        println!("🧠 Inference: http://{}/inference", addr);

        axum::serve(listener, app).await?;
        Ok(())
    }

    /// Create router with all endpoints
    fn create_router(self) -> Router {
        let state = Arc::new(self);

        Router::new()
            .route("/health", get(health_check))
            .route("/inference", post(inference_endpoint))
            .route("/metrics", get(metrics_endpoint))
            .with_state(state)
    }

    /// Generate realistic AI trading decision
    fn generate_ai_decision(&self, _market_data: &str) -> Value {
        use rand::Rng;
        let mut rng = rand::thread_rng();
        
        // Parse market data to make realistic decisions
        let confidence = rng.gen_range(self.config.ai_confidence_range.0..=self.config.ai_confidence_range.1);
        
        // Simulate different trading scenarios
        let scenarios = vec![
            ("arbitrage", "buy", "SOL", "USDC", 1000, 1050, "Arbitrage opportunity detected between DEXs"),
            ("momentum", "buy", "SOL", "USDC", 500, 525, "Strong upward momentum detected"),
            ("mean_reversion", "sell", "SOL", "USDC", 800, 760, "Price above moving average, expecting reversion"),
            ("mev", "buy", "SOL", "USDC", 2000, 2100, "MEV opportunity in upcoming transaction"),
            ("hold", "hold", "SOL", "USDC", 0, 0, "Market conditions unclear, holding position"),
        ];
        
        let scenario = &scenarios[rng.gen_range(0..scenarios.len())];
        
        json!({
            "signal_type": scenario.0,
            "confidence": confidence,
            "action_type": scenario.1,
            "token_in": scenario.2,
            "token_out": scenario.3,
            "amount_in": scenario.4,
            "min_amount_out": scenario.5,
            "slippage_tolerance": 0.01,
            "priority_fee": rng.gen_range(1000..5000),
            "estimated_profit": (scenario.5 - scenario.4) as f64,
            "time_window_ms": rng.gen_range(500..2000),
            "reasoning": scenario.6
        })
    }
}

/// Health check endpoint
async fn health_check() -> Json<Value> {
    Json(json!({
        "status": "healthy",
        "service": "mock-tensorzero-gateway",
        "version": "1.0.0",
        "timestamp": chrono::Utc::now().to_rfc3339()
    }))
}

/// Main inference endpoint
async fn inference_endpoint(
    axum::extract::State(server): axum::extract::State<Arc<MockTensorZeroServer>>,
    Json(request): Json<InferenceRequest>,
) -> Result<Json<InferenceResponse>, StatusCode> {
    let start_time = Instant::now();
    
    // Update metrics
    {
        let mut metrics = server.metrics.lock().await;
        metrics.requests_received += 1;
    }
    
    // Simulate processing delay
    let delay = if server.config.simulate_high_latency {
        Duration::from_millis(server.config.response_delay_ms * 3)
    } else {
        Duration::from_millis(server.config.response_delay_ms)
    };
    tokio::time::sleep(delay).await;
    
    // Simulate errors
    if server.config.error_rate > 0.0 {
        use rand::Rng;
        if rand::thread_rng().gen::<f64>() < server.config.error_rate {
            let mut metrics = server.metrics.lock().await;
            metrics.errors_generated += 1;
            return Err(StatusCode::INTERNAL_SERVER_ERROR);
        }
    }
    
    // Extract market data from request
    let market_data = request.input.messages
        .iter()
        .find(|msg| msg.role == "user")
        .map(|msg| msg.content.as_str())
        .unwrap_or("");
    
    // Generate AI decision
    let ai_decision = server.generate_ai_decision(market_data);
    
    let response = InferenceResponse {
        inference_id: Uuid::new_v4(),
        episode_id: Uuid::new_v4(),
        variant_name: "mock-variant".to_string(),
        content: vec![ContentBlock {
            content_type: "text".to_string(),
            text: ai_decision.to_string(),
        }],
        usage: Some(Usage {
            input_tokens: market_data.len() as u32 / 4, // Rough estimate
            output_tokens: ai_decision.to_string().len() as u32 / 4,
        }),
    };
    
    // Update metrics
    {
        let mut metrics = server.metrics.lock().await;
        metrics.responses_sent += 1;
        let response_time = start_time.elapsed().as_millis() as f64;
        metrics.avg_response_time_ms = 
            (metrics.avg_response_time_ms * (metrics.responses_sent - 1) as f64 + response_time) 
            / metrics.responses_sent as f64;
    }
    
    Ok(Json(response))
}

/// Metrics endpoint
async fn metrics_endpoint(
    axum::extract::State(server): axum::extract::State<Arc<MockTensorZeroServer>>,
) -> Json<Value> {
    let metrics = server.metrics.lock().await;
    
    Json(json!({
        "requests_received": metrics.requests_received,
        "responses_sent": metrics.responses_sent,
        "errors_generated": metrics.errors_generated,
        "avg_response_time_ms": metrics.avg_response_time_ms,
        "error_rate": if metrics.requests_received > 0 {
            metrics.errors_generated as f64 / metrics.requests_received as f64
        } else {
            0.0
        },
        "config": {
            "response_delay_ms": server.config.response_delay_ms,
            "error_rate": server.config.error_rate,
            "ai_confidence_range": server.config.ai_confidence_range,
            "simulate_high_latency": server.config.simulate_high_latency
        }
    }))
}

#[cfg(test)]
mod tests {
    use super::*;


    #[tokio::test]
    async fn test_mock_server_creation() {
        let config = MockServerConfig::default();
        let server = MockTensorZeroServer::new(3001, config);
        assert_eq!(server.port, 3001);
    }

    #[tokio::test]
    async fn test_ai_decision_generation() {
        let config = MockServerConfig::default();
        let server = MockTensorZeroServer::new(3001, config);
        
        let decision = server.generate_ai_decision("test market data");
        assert!(decision["confidence"].as_f64().unwrap() >= 0.6);
        assert!(decision["confidence"].as_f64().unwrap() <= 0.95);
        assert!(decision["signal_type"].as_str().is_some());
    }

    #[tokio::test]
    async fn test_health_check() {
        let response = health_check().await;
        assert_eq!(response.0["status"], "healthy");
    }
}
