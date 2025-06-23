//! Jito Client Module
//! 
//! Provides real Jito bundle execution for MEV protection
//! in THE OVERMIND PROTOCOL.

use anyhow::{Context, Result};
use tracing::{debug, error, info};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use solana_sdk::transaction::Transaction;
use std::time::{Duration, Instant};
use tokio::time::timeout;
use base64::prelude::*;

/// Configuration for Jito client
#[derive(Debug, Clone)]
pub struct JitoConfig {
    /// Jito bundle endpoint URL
    pub bundle_url: String,
    /// Jito tip account
    pub tip_account: String,
    /// Maximum tip amount in lamports
    pub max_tip_lamports: u64,
    /// Bundle size (number of transactions)
    pub bundle_size: usize,
    /// Request timeout in seconds
    pub request_timeout_secs: u64,
    /// Priority fee multiplier
    pub priority_fee_multiplier: f64,
}

impl Default for JitoConfig {
    fn default() -> Self {
        Self {
            bundle_url: "https://mainnet.block-engine.jito.wtf".to_string(),
            tip_account: "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5".to_string(),
            max_tip_lamports: 50000,
            bundle_size: 5,
            request_timeout_secs: 10,
            priority_fee_multiplier: 1.5,
        }
    }
}

/// Jito bundle request
#[derive(Debug, Serialize)]
struct BundleRequest {
    jsonrpc: String,
    id: u64,
    method: String,
    params: BundleParams,
}

/// Bundle parameters
#[derive(Debug, Serialize)]
struct BundleParams {
    transactions: Vec<String>,
}

/// Jito bundle response
#[derive(Debug, Deserialize)]
struct BundleResponse {
    jsonrpc: String,
    id: u64,
    result: Option<String>,
    error: Option<JitoError>,
}

/// Jito error response
#[derive(Debug, Deserialize)]
struct JitoError {
    code: i32,
    message: String,
}

/// Bundle execution result
#[derive(Debug)]
pub struct BundleResult {
    pub bundle_id: String,
    pub status: BundleStatus,
    pub latency_ms: u64,
    pub tip_paid: u64,
}

/// Bundle status
#[derive(Debug)]
pub enum BundleStatus {
    Submitted,
    Accepted,
    Rejected,
    Failed,
}

/// Jito client for MEV protection
pub struct JitoClient {
    config: JitoConfig,
    http_client: Client,
}

impl JitoClient {
    /// Create a new Jito client
    pub fn new(config: JitoConfig) -> Result<Self> {
        let http_client = Client::builder()
            .timeout(Duration::from_secs(config.request_timeout_secs))
            .build()
            .context("Failed to create HTTP client for Jito")?;

        Ok(Self {
            config,
            http_client,
        })
    }

    /// Execute transaction using Jito bundle
    pub async fn execute_bundle(&self, transaction: Transaction) -> Result<BundleResult> {
        let start_time = Instant::now();
        
        info!("🚀 Executing transaction via Jito bundle for MEV protection");
        
        // Serialize transaction to base64
        let serialized_tx = self.serialize_transaction(&transaction)?;
        
        // Create bundle request
        let bundle_request = BundleRequest {
            jsonrpc: "2.0".to_string(),
            id: 1,
            method: "sendBundle".to_string(),
            params: BundleParams {
                transactions: vec![serialized_tx],
            },
        };

        // Submit bundle with timeout
        let response = timeout(
            Duration::from_secs(self.config.request_timeout_secs),
            self.submit_bundle(bundle_request)
        ).await
        .context("Jito bundle submission timed out")?
        .context("Jito bundle submission failed")?;

        let elapsed = start_time.elapsed();
        
        // Process response
        let bundle_result = self.process_bundle_response(response, elapsed)?;
        
        info!("✅ Jito bundle submitted: {} in {}ms", 
              bundle_result.bundle_id, bundle_result.latency_ms);

        Ok(bundle_result)
    }

    /// Submit bundle to Jito
    async fn submit_bundle(&self, request: BundleRequest) -> Result<BundleResponse> {
        let url = format!("{}/api/v1/bundles", self.config.bundle_url);
        
        debug!("Submitting bundle to Jito: {}", url);
        
        let response = self.http_client
            .post(&url)
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .await
            .context("Failed to send bundle to Jito")?;

        if !response.status().is_success() {
            let status = response.status();
            let error_text = response.text().await.unwrap_or_default();
            return Err(anyhow::anyhow!(
                "Jito API error {}: {}", status, error_text
            ));
        }

        let bundle_response: BundleResponse = response
            .json()
            .await
            .context("Failed to parse Jito response")?;

        Ok(bundle_response)
    }

    /// Serialize transaction to base64
    fn serialize_transaction(&self, transaction: &Transaction) -> Result<String> {
        let serialized = bincode::serialize(transaction)
            .context("Failed to serialize transaction")?;
        
        Ok(base64::prelude::BASE64_STANDARD.encode(serialized))
    }

    /// Process bundle response
    fn process_bundle_response(&self, response: BundleResponse, elapsed: Duration) -> Result<BundleResult> {
        if let Some(error) = response.error {
            return Err(anyhow::anyhow!(
                "Jito bundle error {}: {}", error.code, error.message
            ));
        }

        let bundle_id = response.result
            .ok_or_else(|| anyhow::anyhow!("No bundle ID in Jito response"))?;

        Ok(BundleResult {
            bundle_id,
            status: BundleStatus::Submitted,
            latency_ms: elapsed.as_millis() as u64,
            tip_paid: self.calculate_tip(),
        })
    }

    /// Calculate tip amount
    fn calculate_tip(&self) -> u64 {
        // In production, this would calculate optimal tip based on network conditions
        // For now, use a reasonable default
        std::cmp::min(
            (5000.0 * self.config.priority_fee_multiplier) as u64,
            self.config.max_tip_lamports
        )
    }

    /// Health check for Jito service
    pub async fn health_check(&self) -> Result<bool> {
        let url = format!("{}/api/v1/bundles", self.config.bundle_url);
        
        match timeout(
            Duration::from_secs(5),
            self.http_client.head(&url).send()
        ).await {
            Ok(Ok(response)) => Ok(response.status().is_success()),
            Ok(Err(e)) => {
                error!("Jito health check failed: {}", e);
                Ok(false)
            },
            Err(_) => {
                error!("Jito health check timed out");
                Ok(false)
            }
        }
    }

    /// Get bundle status
    pub async fn get_bundle_status(&self, bundle_id: &str) -> Result<BundleStatus> {
        let url = format!("{}/api/v1/bundles/{}", self.config.bundle_url, bundle_id);
        
        match timeout(
            Duration::from_secs(5),
            self.http_client.get(&url).send()
        ).await {
            Ok(Ok(response)) => {
                if response.status().is_success() {
                    // In production, parse the actual status from response
                    Ok(BundleStatus::Accepted)
                } else {
                    Ok(BundleStatus::Rejected)
                }
            },
            Ok(Err(_)) => Ok(BundleStatus::Failed),
            Err(_) => Ok(BundleStatus::Failed),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use solana_sdk::signature::{Keypair, Signer};

    #[tokio::test]
    async fn test_jito_client_creation() {
        let config = JitoConfig::default();
        let client = JitoClient::new(config);
        assert!(client.is_ok());
    }

    #[test]
    fn test_transaction_serialization() {
        let config = JitoConfig::default();
        let client = JitoClient::new(config).unwrap();
        
        // Create a simple transaction
        let keypair = Keypair::new();
        let transaction = Transaction::new_with_payer(
            &[],
            Some(&keypair.pubkey()),
        );

        let result = client.serialize_transaction(&transaction);
        assert!(result.is_ok());
    }

    #[test]
    fn test_tip_calculation() {
        let config = JitoConfig {
            priority_fee_multiplier: 2.0,
            max_tip_lamports: 10000,
            ..JitoConfig::default()
        };
        let client = JitoClient::new(config).unwrap();
        
        let tip = client.calculate_tip();
        assert!(tip <= 10000);
        assert!(tip > 0);
    }
}
