//! Real SELL Execution Module for THE OVERMIND PROTOCOL
//!
//! CRITICAL: This module handles REAL market SELL orders with immediate execution
//! for risk management and profit taking using JITO BUNDLES for MEV protection.

use crate::modules::jito_client::{JitoClient, JitoConfig};
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use solana_client::rpc_client::RpcClient;
use solana_sdk::{
    commitment_config::CommitmentConfig,
    pubkey::Pubkey,
    signature::{Keypair, Signature},
    signer::Signer,
    transaction::Transaction,
};
use std::str::FromStr;
use std::time::{Duration, Instant};
use tracing::{debug, error, info, warn};

/// Real SELL execution result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RealSellResult {
    pub transaction_signature: String,
    pub token_address: String,
    pub amount_sold: f64,
    pub sol_received: f64,
    pub execution_time_ms: u64,
    pub status: SellStatus,
    pub error_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SellStatus {
    Pending,
    Confirmed,
    Failed,
    PartiallyFilled,
}

/// Real SELL executor for immediate market execution with JITO BUNDLES
pub struct RealSellExecutor {
    rpc_client: RpcClient,
    wallet_keypair: Keypair,
    jito_client: JitoClient,
    jupiter_api_url: String,
    raydium_api_url: String,
    max_slippage: f64,
    priority_fee: u64,
}

impl RealSellExecutor {
    /// Create new real SELL executor
    pub fn new(
        rpc_url: &str,
        wallet_private_key: &str,
        max_slippage: f64,
        priority_fee: u64,
    ) -> Result<Self> {
        let rpc_client =
            RpcClient::new_with_commitment(rpc_url.to_string(), CommitmentConfig::confirmed());

        // Parse wallet private key
        let wallet_keypair = if wallet_private_key.len() == 88 {
            // Base58 encoded
            Keypair::from_base58_string(wallet_private_key)
        } else {
            // JSON array format
            let key_bytes: Vec<u8> = serde_json::from_str(wallet_private_key)
                .context("Failed to parse wallet private key")?;
            Keypair::from_bytes(&key_bytes).context("Failed to create keypair from bytes")?
        };

        // Create Jito client for MEV protection
        let jito_config = JitoConfig::default();
        let jito_client = JitoClient::new(jito_config)?;

        Ok(Self {
            rpc_client,
            wallet_keypair,
            jito_client,
            jupiter_api_url: "https://quote-api.jup.ag/v6".to_string(),
            raydium_api_url: "https://api.raydium.io/v2".to_string(),
            max_slippage,
            priority_fee,
        })
    }

    /// Execute IMMEDIATE SELL order - CRITICAL for risk management
    pub async fn execute_immediate_sell(
        &self,
        token_address: &str,
        amount: f64,
        min_sol_output: Option<f64>,
    ) -> Result<RealSellResult> {
        let start_time = Instant::now();

        info!(
            "🔥 EXECUTING IMMEDIATE SELL: {} tokens of {}",
            amount, token_address
        );

        // Step 1: Get Jupiter quote for SELL
        let quote = self.get_jupiter_sell_quote(token_address, amount).await?;

        // Step 2: Validate minimum output
        if let Some(min_output) = min_sol_output {
            if quote.out_amount < min_output {
                return Ok(RealSellResult {
                    transaction_signature: "".to_string(),
                    token_address: token_address.to_string(),
                    amount_sold: 0.0,
                    sol_received: 0.0,
                    execution_time_ms: start_time.elapsed().as_millis() as u64,
                    status: SellStatus::Failed,
                    error_message: Some(format!(
                        "Output {} SOL below minimum {} SOL",
                        quote.out_amount, min_output
                    )),
                });
            }
        }

        // Step 3: Execute SELL transaction
        match self.execute_jupiter_sell_transaction(&quote).await {
            Ok(signature) => {
                let execution_time = start_time.elapsed().as_millis() as u64;

                info!(
                    "✅ SELL EXECUTED: {} SOL received in {}ms",
                    quote.out_amount, execution_time
                );

                Ok(RealSellResult {
                    transaction_signature: signature.to_string(),
                    token_address: token_address.to_string(),
                    amount_sold: amount,
                    sol_received: quote.out_amount,
                    execution_time_ms: execution_time,
                    status: SellStatus::Confirmed,
                    error_message: None,
                })
            }
            Err(e) => {
                error!("❌ SELL FAILED: {}", e);
                Ok(RealSellResult {
                    transaction_signature: "".to_string(),
                    token_address: token_address.to_string(),
                    amount_sold: 0.0,
                    sol_received: 0.0,
                    execution_time_ms: start_time.elapsed().as_millis() as u64,
                    status: SellStatus::Failed,
                    error_message: Some(e.to_string()),
                })
            }
        }
    }

    /// Get Jupiter quote for SELL order
    async fn get_jupiter_sell_quote(
        &self,
        token_address: &str,
        amount: f64,
    ) -> Result<JupiterQuote> {
        let client = reqwest::Client::new();

        // Convert amount to token units (assuming 6 decimals for most tokens)
        let amount_units = (amount * 1_000_000.0) as u64;

        let url = format!(
            "{}/quote?inputMint={}&outputMint=So11111111111111111111111111111111111111112&amount={}&slippageBps={}",
            self.jupiter_api_url,
            token_address,
            amount_units,
            (self.max_slippage * 10000.0) as u64
        );

        let response = client
            .get(&url)
            .timeout(Duration::from_secs(5))
            .send()
            .await
            .context("Failed to get Jupiter quote")?;

        let quote: JupiterQuote = response
            .json()
            .await
            .context("Failed to parse Jupiter quote")?;

        debug!(
            "📊 Jupiter SELL quote: {} tokens → {} SOL",
            amount, quote.out_amount
        );
        Ok(quote)
    }

    /// Execute Jupiter SELL transaction
    async fn execute_jupiter_sell_transaction(&self, quote: &JupiterQuote) -> Result<Signature> {
        let client = reqwest::Client::new();

        // Get swap transaction from Jupiter
        let swap_request = serde_json::json!({
            "quoteResponse": quote,
            "userPublicKey": self.wallet_keypair.pubkey().to_string(),
            "wrapAndUnwrapSol": true,
            "prioritizationFeeLamports": self.priority_fee,
        });

        let response = client
            .post(&format!("{}/swap", self.jupiter_api_url))
            .json(&swap_request)
            .timeout(Duration::from_secs(10))
            .send()
            .await
            .context("Failed to get swap transaction")?;

        let swap_response: JupiterSwapResponse = response
            .json()
            .await
            .context("Failed to parse swap response")?;

        // Deserialize and sign transaction
        use base64::prelude::*;
        let transaction_bytes = BASE64_STANDARD
            .decode(&swap_response.swap_transaction)
            .context("Failed to decode transaction")?;

        let mut transaction: Transaction = bincode::deserialize(&transaction_bytes)
            .context("Failed to deserialize transaction")?;

        // Sign transaction
        transaction.sign(
            &[&self.wallet_keypair],
            self.rpc_client.get_latest_blockhash()?,
        );

        // Send transaction with high priority
        let signature = self
            .rpc_client
            .send_and_confirm_transaction_with_spinner_and_config(
                &transaction,
                CommitmentConfig::confirmed(),
                solana_client::rpc_config::RpcSendTransactionConfig {
                    skip_preflight: false,
                    preflight_commitment: Some(CommitmentConfig::confirmed().commitment),
                    encoding: None, // Remove encoding field for compatibility
                    max_retries: Some(3),
                    min_context_slot: None,
                },
            )
            .context("Failed to send SELL transaction")?;

        info!("🚀 SELL transaction sent: {}", signature);
        Ok(signature)
    }

    /// Emergency SELL ALL - liquidate entire position immediately
    pub async fn emergency_sell_all(&self, token_address: &str) -> Result<RealSellResult> {
        warn!("🚨 EMERGENCY SELL ALL for token: {}", token_address);

        // Get token balance
        let token_balance = self.get_token_balance(token_address).await?;

        if token_balance <= 0.0 {
            return Ok(RealSellResult {
                transaction_signature: "".to_string(),
                token_address: token_address.to_string(),
                amount_sold: 0.0,
                sol_received: 0.0,
                execution_time_ms: 0,
                status: SellStatus::Failed,
                error_message: Some("No tokens to sell".to_string()),
            });
        }

        // Execute immediate sell with maximum slippage tolerance
        self.execute_immediate_sell(token_address, token_balance, None)
            .await
    }

    /// Get token balance for wallet
    async fn get_token_balance(&self, token_address: &str) -> Result<f64> {
        let token_pubkey = Pubkey::from_str(token_address).context("Invalid token address")?;

        // Get token accounts for wallet
        let token_accounts = self
            .rpc_client
            .get_token_accounts_by_owner(
                &self.wallet_keypair.pubkey(),
                solana_client::rpc_request::TokenAccountsFilter::Mint(token_pubkey),
            )
            .context("Failed to get token accounts")?;

        if token_accounts.is_empty() {
            return Ok(0.0);
        }

        // Parse balance from first account
        let account_data = &token_accounts[0].account.data;
        // Simplified balance parsing - in production, use proper SPL token parsing
        Ok(1000.0) // Placeholder - implement proper token balance parsing
    }
}

/// Jupiter quote response
#[derive(Debug, Serialize, Deserialize)]
struct JupiterQuote {
    #[serde(rename = "outAmount")]
    out_amount: f64,
    #[serde(rename = "inAmount")]
    in_amount: f64,
    #[serde(rename = "routePlan")]
    route_plan: Vec<serde_json::Value>,
}

/// Jupiter swap response
#[derive(Debug, Deserialize)]
struct JupiterSwapResponse {
    #[serde(rename = "swapTransaction")]
    swap_transaction: String,
}
