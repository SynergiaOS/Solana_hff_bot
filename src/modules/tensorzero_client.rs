//! TensorZero Client Module
//!
//! Provides real TensorZero API integration for AI-optimized transaction execution
//! in THE OVERMIND PROTOCOL.

use anyhow::{Context, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};
use tokio::time::timeout;
use tracing::{debug, error, info, warn};

/// Configuration for TensorZero client
#[derive(Debug, Clone)]
pub struct TensorZeroConfig {
    /// TensorZero Gateway URL
    pub gateway_url: String,
    /// API key for authentication
    pub api_key: String,
    /// Maximum latency allowed for optimization requests
    pub max_latency_ms: u64,
    /// Optimization level (conservative, moderate, aggressive)
    pub optimization_level: String,
    /// Whether to enable caching
    pub cache_enabled: bool,
    /// Batch size for optimization requests
    pub batch_size: usize,
    /// Request timeout in seconds
    pub request_timeout_secs: u64,
}

impl Default for TensorZeroConfig {
    fn default() -> Self {
        Self {
            gateway_url: "http://localhost:3001".to_string(),
            api_key: "".to_string(),
            max_latency_ms: 50,
            optimization_level: "aggressive".to_string(),
            cache_enabled: true,
            batch_size: 10,
            request_timeout_secs: 5,
        }
    }
}

/// Trading signal for TensorZero optimization
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingSignal {
    pub symbol: String,
    pub action: String,
    pub quantity: f64,
    pub price: Option<f64>,
    pub confidence: f64,
    pub reasoning: String,
    pub timestamp: u64,
}

/// TensorZero optimization request
#[derive(Debug, Serialize)]
struct OptimizationRequest {
    signal: TradingSignal,
    optimization_level: String,
    max_latency_ms: u64,
    cache_enabled: bool,
    context: OptimizationContext,
}

/// Context for optimization
#[derive(Debug, Serialize)]
struct OptimizationContext {
    market_conditions: String,
    volatility: f64,
    liquidity: f64,
    gas_price: u64,
    network_congestion: f64,
}

/// TensorZero optimization response
#[derive(Debug, Deserialize)]
pub struct OptimizationResponse {
    pub optimized_params: OptimizedParams,
    pub confidence_score: f64,
    pub execution_strategy: String,
    pub estimated_latency_ms: u64,
    pub risk_assessment: RiskAssessment,
}

/// Optimized transaction parameters
#[derive(Debug, Deserialize)]
pub struct OptimizedParams {
    pub slippage_tolerance: f64,
    pub priority_fee_lamports: u64,
    pub compute_unit_limit: u32,
    pub execution_timing: String,
    pub route_optimization: RouteOptimization,
}

/// Route optimization details
#[derive(Debug, Deserialize)]
pub struct RouteOptimization {
    pub dex_selection: Vec<String>,
    pub split_trades: bool,
    pub optimal_splits: Vec<f64>,
}

/// Risk assessment from TensorZero
#[derive(Debug, Deserialize)]
pub struct RiskAssessment {
    pub mev_risk: f64,
    pub slippage_risk: f64,
    pub execution_risk: f64,
    pub overall_risk: f64,
}

/// TensorZero client for AI optimization
pub struct TensorZeroClient {
    config: TensorZeroConfig,
    http_client: Client,
}

impl TensorZeroClient {
    /// Create a new TensorZero client
    pub fn new(config: TensorZeroConfig) -> Result<Self> {
        let http_client = Client::builder()
            .timeout(Duration::from_secs(config.request_timeout_secs))
            .build()
            .context("Failed to create HTTP client")?;

        Ok(Self {
            config,
            http_client,
        })
    }

    /// Optimize trading signal using TensorZero AI
    pub async fn optimize_signal(&self, signal: TradingSignal) -> Result<OptimizationResponse> {
        let start_time = Instant::now();

        info!(
            "🧠 Optimizing signal with TensorZero: {} {}",
            signal.action, signal.symbol
        );

        // Prepare optimization request
        let request = OptimizationRequest {
            signal: signal.clone(),
            optimization_level: self.config.optimization_level.clone(),
            max_latency_ms: self.config.max_latency_ms,
            cache_enabled: self.config.cache_enabled,
            context: self.build_optimization_context(&signal).await?,
        };

        // Make API request with timeout
        let response = timeout(
            Duration::from_millis(self.config.max_latency_ms),
            self.make_optimization_request(request),
        )
        .await
        .context("TensorZero optimization request timed out")?
        .context("TensorZero optimization request failed")?;

        let elapsed = start_time.elapsed();

        info!(
            "✅ TensorZero optimization completed in {}ms, confidence: {:.2}",
            elapsed.as_millis(),
            response.confidence_score
        );

        // Validate response
        self.validate_optimization_response(&response)?;

        Ok(response)
    }

    /// Make the actual HTTP request to TensorZero
    async fn make_optimization_request(
        &self,
        request: OptimizationRequest,
    ) -> Result<OptimizationResponse> {
        let url = format!("{}/optimize", self.config.gateway_url);

        debug!("Making TensorZero request to: {}", url);

        let response = self
            .http_client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.config.api_key))
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await
            .context("Failed to send request to TensorZero")?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            return Err(anyhow::anyhow!(
                "TensorZero API error {}: {}",
                status,
                error_text
            ));
        }

        let optimization_response: OptimizationResponse = response
            .json()
            .await
            .context("Failed to parse TensorZero response")?;

        Ok(optimization_response)
    }

    /// Build optimization context from current market conditions
    async fn build_optimization_context(
        &self,
        signal: &TradingSignal,
    ) -> Result<OptimizationContext> {
        // In production, this would gather real market data
        // For now, we'll use reasonable defaults based on the signal

        let volatility = match signal.confidence {
            c if c > 0.8 => 0.1, // Low volatility for high confidence
            c if c > 0.6 => 0.2, // Medium volatility
            _ => 0.3,            // High volatility for low confidence
        };

        Ok(OptimizationContext {
            market_conditions: "normal".to_string(),
            volatility,
            liquidity: 0.8,          // Assume good liquidity
            gas_price: 5000,         // Default priority fee
            network_congestion: 0.3, // Moderate congestion
        })
    }

    /// Validate the optimization response
    fn validate_optimization_response(&self, response: &OptimizationResponse) -> Result<()> {
        // Check confidence score
        if response.confidence_score < 0.5 {
            warn!(
                "Low confidence score from TensorZero: {:.2}",
                response.confidence_score
            );
        }

        // Check estimated latency
        if response.estimated_latency_ms > self.config.max_latency_ms {
            return Err(anyhow::anyhow!(
                "Estimated latency {}ms exceeds maximum {}ms",
                response.estimated_latency_ms,
                self.config.max_latency_ms
            ));
        }

        // Check risk assessment
        if response.risk_assessment.overall_risk > 0.8 {
            warn!(
                "High risk assessment from TensorZero: {:.2}",
                response.risk_assessment.overall_risk
            );
        }

        Ok(())
    }

    /// Health check for TensorZero service
    pub async fn health_check(&self) -> Result<bool> {
        let url = format!("{}/health", self.config.gateway_url);

        match timeout(Duration::from_secs(5), self.http_client.get(&url).send()).await {
            Ok(Ok(response)) => Ok(response.status().is_success()),
            Ok(Err(e)) => {
                error!("TensorZero health check failed: {}", e);
                Ok(false)
            }
            Err(_) => {
                error!("TensorZero health check timed out");
                Ok(false)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_tensorzero_client_creation() {
        let config = TensorZeroConfig::default();
        let client = TensorZeroClient::new(config);
        assert!(client.is_ok());
    }

    #[tokio::test]
    async fn test_optimization_context_building() {
        let config = TensorZeroConfig::default();
        let client = TensorZeroClient::new(config).unwrap();

        let signal = TradingSignal {
            symbol: "SOL/USDC".to_string(),
            action: "BUY".to_string(),
            quantity: 1.0,
            price: Some(100.0),
            confidence: 0.85,
            reasoning: "Test signal".to_string(),
            timestamp: 1234567890,
        };

        let context = client.build_optimization_context(&signal).await;
        assert!(context.is_ok());
    }
}
