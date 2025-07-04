// THE OVERMIND PROTOCOL - RPC Failover Module
// Handles multiple RPC endpoints with automatic failover and health monitoring

use crate::config::{RpcEndpoint, SolanaConfig};
use anyhow::{anyhow, Result};
use serde_json::Value;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use tracing::{debug, info, warn};

#[derive(Debug, Clone)]
pub struct RpcFailoverClient {
    endpoints: Arc<RwLock<Vec<RpcEndpoint>>>,
    config: SolanaConfig,
    http_client: reqwest::Client,
    current_endpoint_index: Arc<RwLock<usize>>,
}

#[derive(Debug, Clone)]
pub struct RpcResponse {
    pub result: Value,
    pub endpoint_used: String,
    pub latency_ms: u64,
}

impl RpcFailoverClient {
    /// Create new RPC failover client
    pub fn new(config: SolanaConfig) -> Self {
        let http_client = reqwest::Client::builder()
            .timeout(Duration::from_millis(10000)) // 10 second timeout
            .build()
            .expect("Failed to create HTTP client");

        Self {
            endpoints: Arc::new(RwLock::new(config.rpc_endpoints.clone())),
            config,
            http_client,
            current_endpoint_index: Arc::new(RwLock::new(0)),
        }
    }

    /// Execute RPC call with automatic failover
    pub async fn call(&self, method: &str, params: Value) -> Result<RpcResponse> {
        if !self.config.failover_enabled {
            // Use primary endpoint only
            return self.call_single_endpoint(0, method, params).await;
        }

        let endpoint_count = {
            let endpoints = self.endpoints.read().await;
            endpoints.len()
        };

        let mut last_error = None;

        // Try each endpoint in priority order
        for index in 0..endpoint_count {
            let is_healthy = {
                let endpoints = self.endpoints.read().await;
                endpoints.get(index).map(|e| e.is_healthy).unwrap_or(false)
            };

            if !is_healthy {
                debug!("Skipping unhealthy endpoint at index {}", index);
                continue;
            }

            match self
                .call_single_endpoint(index, method, params.clone())
                .await
            {
                Ok(response) => {
                    // Update current endpoint index for future calls
                    *self.current_endpoint_index.write().await = index;
                    return Ok(response);
                }
                Err(e) => {
                    let endpoint_name = {
                        let endpoints = self.endpoints.read().await;
                        endpoints
                            .get(index)
                            .map(|e| e.name.clone())
                            .unwrap_or_default()
                    };

                    warn!(
                        "RPC call failed on endpoint {}: {}. Trying next endpoint...",
                        endpoint_name, e
                    );
                    last_error = Some(e);

                    // Mark endpoint as unhealthy
                    self.mark_endpoint_unhealthy(index).await;
                }
            }
        }

        Err(last_error.unwrap_or_else(|| anyhow!("All RPC endpoints failed")))
    }

    /// Call specific endpoint by index
    async fn call_single_endpoint(
        &self,
        endpoint_index: usize,
        method: &str,
        params: Value,
    ) -> Result<RpcResponse> {
        let (endpoint_url, endpoint_name, timeout_ms) = {
            let endpoints = self.endpoints.read().await;
            let endpoint = endpoints
                .get(endpoint_index)
                .ok_or_else(|| anyhow!("Endpoint index {} not found", endpoint_index))?;
            (
                endpoint.url.clone(),
                endpoint.name.clone(),
                endpoint.timeout_ms,
            )
        };

        let start_time = Instant::now();

        let request_body = serde_json::json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        });

        let response = self
            .http_client
            .post(&endpoint_url)
            .timeout(Duration::from_millis(timeout_ms))
            .header("Content-Type", "application/json")
            .json(&request_body)
            .send()
            .await
            .map_err(|e| anyhow!("HTTP request failed: {}", e))?;

        let latency = start_time.elapsed().as_millis() as u64;

        if !response.status().is_success() {
            return Err(anyhow!(
                "HTTP error {}: {}",
                response.status(),
                response.text().await.unwrap_or_default()
            ));
        }

        let json_response: Value = response
            .json()
            .await
            .map_err(|e| anyhow!("Failed to parse JSON response: {}", e))?;

        // Check for JSON-RPC error
        if let Some(error) = json_response.get("error") {
            return Err(anyhow!("RPC error: {}", error));
        }

        let result = json_response
            .get("result")
            .ok_or_else(|| anyhow!("No result field in response"))?
            .clone();

        // Update endpoint latency
        self.update_endpoint_latency(endpoint_index, latency as f64)
            .await;

        debug!(
            "RPC call successful on {}: {}ms latency",
            endpoint_name, latency
        );

        Ok(RpcResponse {
            result,
            endpoint_used: endpoint_name,
            latency_ms: latency,
        })
    }

    /// Mark endpoint as unhealthy
    async fn mark_endpoint_unhealthy(&self, endpoint_index: usize) {
        let mut endpoints = self.endpoints.write().await;
        if let Some(endpoint) = endpoints.get_mut(endpoint_index) {
            endpoint.is_healthy = false;
            endpoint.last_health_check = Some(chrono::Utc::now());
            warn!("Marked endpoint {} as unhealthy", endpoint.name);
        }
    }

    /// Update endpoint latency
    async fn update_endpoint_latency(&self, endpoint_index: usize, latency_ms: f64) {
        let mut endpoints = self.endpoints.write().await;
        if let Some(endpoint) = endpoints.get_mut(endpoint_index) {
            // Exponential moving average
            endpoint.avg_latency_ms = Some(match endpoint.avg_latency_ms {
                Some(current) => current * 0.8 + latency_ms * 0.2,
                None => latency_ms,
            });
        }
    }

    /// Start health check background task
    pub async fn start_health_checks(&self) {
        if !self.config.failover_enabled {
            return;
        }

        let endpoints = self.endpoints.clone();
        let http_client = self.http_client.clone();
        let interval_ms = self.config.health_check_interval_ms;

        tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_millis(interval_ms));

            loop {
                interval.tick().await;

                let endpoints_read = endpoints.read().await;
                let endpoint_count = endpoints_read.len();
                drop(endpoints_read);

                for index in 0..endpoint_count {
                    let endpoints_clone = endpoints.clone();
                    let client_clone = http_client.clone();

                    tokio::spawn(async move {
                        Self::health_check_endpoint(endpoints_clone, client_clone, index).await;
                    });
                }
            }
        });

        info!("RPC health checks started with {}ms interval", interval_ms);
    }

    /// Perform health check on specific endpoint
    async fn health_check_endpoint(
        endpoints: Arc<RwLock<Vec<RpcEndpoint>>>,
        http_client: reqwest::Client,
        endpoint_index: usize,
    ) {
        let endpoint_url = {
            let endpoints_read = endpoints.read().await;
            if let Some(endpoint) = endpoints_read.get(endpoint_index) {
                endpoint.url.clone()
            } else {
                return;
            }
        };

        let start_time = Instant::now();

        // Simple health check: get latest blockhash
        let health_check_body = serde_json::json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": []
        });

        let result = http_client
            .post(&endpoint_url)
            .timeout(Duration::from_millis(5000))
            .header("Content-Type", "application/json")
            .json(&health_check_body)
            .send()
            .await;

        let latency = start_time.elapsed().as_millis() as f64;
        let is_healthy = result.is_ok() && result.unwrap().status().is_success();

        // Update endpoint health status
        let mut endpoints_write = endpoints.write().await;
        if let Some(endpoint) = endpoints_write.get_mut(endpoint_index) {
            let was_healthy = endpoint.is_healthy;
            endpoint.is_healthy = is_healthy;
            endpoint.last_health_check = Some(chrono::Utc::now());

            if is_healthy {
                endpoint.avg_latency_ms = Some(match endpoint.avg_latency_ms {
                    Some(current) => current * 0.9 + latency * 0.1,
                    None => latency,
                });

                if !was_healthy {
                    info!("Endpoint {} is now healthy ({}ms)", endpoint.name, latency);
                }
            } else if was_healthy {
                warn!("Endpoint {} is now unhealthy", endpoint.name);
            }
        }
    }

    /// Get current endpoint status
    pub async fn get_endpoint_status(&self) -> Vec<RpcEndpoint> {
        self.endpoints.read().await.clone()
    }

    /// Get best available endpoint
    pub async fn get_best_endpoint(&self) -> Option<RpcEndpoint> {
        let endpoints = self.endpoints.read().await;

        endpoints
            .iter()
            .filter(|e| e.is_healthy)
            .min_by(|a, b| {
                // Sort by priority first, then by latency
                a.priority.cmp(&b.priority).then_with(|| {
                    let a_latency = a.avg_latency_ms.unwrap_or(f64::MAX);
                    let b_latency = b.avg_latency_ms.unwrap_or(f64::MAX);
                    a_latency
                        .partial_cmp(&b_latency)
                        .unwrap_or(std::cmp::Ordering::Equal)
                })
            })
            .cloned()
    }
}

/// Convenience functions for common RPC calls
impl RpcFailoverClient {
    /// Get account info
    pub async fn get_account_info(&self, pubkey: &str) -> Result<RpcResponse> {
        self.call(
            "getAccountInfo",
            serde_json::json!([pubkey, {"encoding": "base64"}]),
        )
        .await
    }

    /// Get latest blockhash
    pub async fn get_latest_blockhash(&self) -> Result<RpcResponse> {
        self.call("getLatestBlockhash", serde_json::json!([])).await
    }

    /// Send transaction
    pub async fn send_transaction(&self, transaction: &str) -> Result<RpcResponse> {
        self.call(
            "sendTransaction",
            serde_json::json!([transaction, {"encoding": "base64"}]),
        )
        .await
    }

    /// Get transaction status
    pub async fn get_transaction(&self, signature: &str) -> Result<RpcResponse> {
        self.call(
            "getTransaction",
            serde_json::json!([signature, {"encoding": "base64"}]),
        )
        .await
    }
}
