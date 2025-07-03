use anyhow::Result;
use reqwest;
use serde_json::{json, Value};
use solana_client::rpc_client::RpcClient;
use solana_sdk::{
    commitment_config::CommitmentConfig,
    pubkey::Pubkey,
    signature::{Keypair, Signer},
    transaction::Transaction,
};
use tracing::info;

/// Jupiter DEX Integration for THE OVERMIND PROTOCOL
/// Provides real token swapping capabilities through Jupiter aggregator
pub struct JupiterDex {
    client: RpcClient,
    jupiter_api_url: String,
}

impl JupiterDex {
    pub fn new(rpc_url: String) -> Self {
        Self {
            client: RpcClient::new_with_commitment(rpc_url, CommitmentConfig::confirmed()),
            jupiter_api_url: "https://quote-api.jup.ag/v6".to_string(),
        }
    }

    /// Execute real token swap through Jupiter
    pub async fn execute_swap(
        &self,
        keypair: &Keypair,
        input_mint: &str,
        output_mint: &str,
        amount: u64,
        slippage_bps: u16, // Slippage in basis points (100 = 1%)
    ) -> Result<String> {
        info!(
            "🔄 Jupiter DEX: Executing swap {} -> {}",
            input_mint, output_mint
        );
        info!(
            "💰 Amount: {} lamports, Slippage: {}bps",
            amount, slippage_bps
        );

        // Step 1: Get quote from Jupiter
        let quote = self
            .get_quote(input_mint, output_mint, amount, slippage_bps)
            .await?;
        info!("✅ Jupiter quote received: {}", quote["outAmount"]);

        // Step 2: Get swap transaction
        let swap_transaction = self.get_swap_transaction(&quote, &keypair.pubkey()).await?;
        info!("✅ Jupiter swap transaction prepared");

        // Step 3: Execute transaction
        let signature = self.execute_transaction(keypair, &swap_transaction).await?;
        info!("✅ Jupiter swap executed: {}", signature);

        Ok(signature)
    }

    /// Get quote from Jupiter API
    async fn get_quote(
        &self,
        input_mint: &str,
        output_mint: &str,
        amount: u64,
        slippage_bps: u16,
    ) -> Result<Value> {
        let url = format!(
            "{}/quote?inputMint={}&outputMint={}&amount={}&slippageBps={}",
            self.jupiter_api_url, input_mint, output_mint, amount, slippage_bps
        );

        info!("📡 Fetching Jupiter quote: {}", url);

        let response = reqwest::get(&url).await?;
        let quote: Value = response.json().await?;

        if quote.get("error").is_some() {
            return Err(anyhow::anyhow!("Jupiter quote error: {}", quote["error"]));
        }

        Ok(quote)
    }

    /// Get swap transaction from Jupiter API
    async fn get_swap_transaction(&self, quote: &Value, user_pubkey: &Pubkey) -> Result<String> {
        let url = format!("{}/swap", self.jupiter_api_url);

        let payload = json!({
            "quoteResponse": quote,
            "userPublicKey": user_pubkey.to_string(),
            "wrapAndUnwrapSol": true,
            "dynamicComputeUnitLimit": true,
            "prioritizationFeeLamports": 1000
        });

        info!("📡 Requesting Jupiter swap transaction");

        let client = reqwest::Client::new();
        let response = client
            .post(&url)
            .header("Content-Type", "application/json")
            .json(&payload)
            .send()
            .await?;

        let swap_response: Value = response.json().await?;

        if swap_response.get("error").is_some() {
            return Err(anyhow::anyhow!(
                "Jupiter swap error: {}",
                swap_response["error"]
            ));
        }

        let swap_transaction = swap_response["swapTransaction"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("No swap transaction in response"))?;

        Ok(swap_transaction.to_string())
    }

    /// Execute the swap transaction
    async fn execute_transaction(
        &self,
        keypair: &Keypair,
        transaction_data: &str,
    ) -> Result<String> {
        info!("🔧 Decoding Jupiter transaction data...");

        // Decode base64 transaction with error handling
        use base64::{engine::general_purpose, Engine as _};
        let transaction_bytes = match general_purpose::STANDARD.decode(transaction_data) {
            Ok(bytes) => {
                info!("✅ Base64 decode successful: {} bytes", bytes.len());
                bytes
            }
            Err(e) => {
                return Err(anyhow::anyhow!("Base64 decode failed: {}", e));
            }
        };

        // Deserialize transaction with enhanced error handling
        let mut transaction: Transaction =
            match bincode::deserialize::<Transaction>(&transaction_bytes) {
                Ok(tx) => {
                    info!("✅ Transaction deserialization successful");
                    info!(
                        "📊 Transaction has {} instructions",
                        tx.message.instructions.len()
                    );
                    tx
                }
                Err(e) => {
                    return Err(anyhow::anyhow!("Transaction deserialization failed: {}", e));
                }
            };

        // Get fresh blockhash and update transaction
        info!("🔄 Getting fresh blockhash...");
        let recent_blockhash = self.client.get_latest_blockhash()?;
        transaction.message.recent_blockhash = recent_blockhash;

        info!("🔐 Signing transaction...");
        // Try different signing approaches
        match transaction.try_sign(&[keypair], recent_blockhash) {
            Ok(_) => {
                info!("✅ Transaction signed successfully");
            }
            Err(e) => {
                info!("⚠️ try_sign failed: {}, attempting partial_sign", e);
                // Fallback to partial_sign
                transaction.partial_sign(&[keypair], recent_blockhash);
                info!("✅ Transaction partially signed");
            }
        }

        // Send transaction with retry logic
        info!("📤 Sending transaction to network...");
        let signature = match self.client.send_and_confirm_transaction(&transaction) {
            Ok(sig) => {
                info!("✅ Transaction confirmed: {}", sig);
                sig
            }
            Err(e) => {
                info!("⚠️ send_and_confirm failed: {}, trying send_transaction", e);
                // Fallback to just send without confirmation
                match self.client.send_transaction(&transaction) {
                    Ok(sig) => {
                        info!("✅ Transaction sent: {}", sig);
                        sig
                    }
                    Err(e2) => {
                        return Err(anyhow::anyhow!("Transaction send failed: {}", e2));
                    }
                }
            }
        };

        Ok(signature.to_string())
    }

    /// Get token mint addresses for common tokens
    pub fn get_token_mint(symbol: &str) -> Result<String> {
        let mint = match symbol.to_uppercase().as_str() {
            "SOL" => "So11111111111111111111111111111111111111112", // Wrapped SOL
            "USDC" => "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT" => "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "RAY" => "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
            "ORCA" => "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
            "BONK" => "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "JTO" => "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
            "WIF" => "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
            "PEPE" => "BzUodNXyUKKFEKioUMLfbKdoNuyCQk3RjKzjVEoNbXKy",
            _ => return Err(anyhow::anyhow!("Unknown token symbol: {}", symbol)),
        };

        Ok(mint.to_string())
    }
}

/// Helper function to execute real DEX swap
pub async fn execute_real_dex_swap(
    keypair: &Keypair,
    action: &str,
    symbol: &str,
    quantity: f64,
    rpc_url: &str,
) -> Result<String> {
    let jupiter = JupiterDex::new(rpc_url.to_string());

    let (input_mint, output_mint, amount) = match action.to_uppercase().as_str() {
        "BUY" => {
            // BUY token with SOL
            let sol_mint = JupiterDex::get_token_mint("SOL")?;
            let token_mint = JupiterDex::get_token_mint(symbol)?;
            let sol_amount = (quantity * 1_000_000_000.0) as u64; // Convert SOL to lamports
            (sol_mint, token_mint, sol_amount)
        }
        "SELL" => {
            // SELL token for SOL
            let token_mint = JupiterDex::get_token_mint(symbol)?;
            let sol_mint = JupiterDex::get_token_mint("SOL")?;
            // For SELL, quantity should be in token units, not SOL
            let token_amount = (quantity * 1_000_000.0) as u64; // Assuming 6 decimals for most tokens
            (token_mint, sol_mint, token_amount)
        }
        _ => return Err(anyhow::anyhow!("Invalid action: {}", action)),
    };

    info!("🔄 Executing {} {} via Jupiter DEX", action, symbol);
    info!(
        "📊 Input: {}, Output: {}, Amount: {}",
        input_mint, output_mint, amount
    );

    // Execute swap with 1% slippage
    let signature = jupiter
        .execute_swap(keypair, &input_mint, &output_mint, amount, 100)
        .await?;

    info!("✅ Real DEX swap completed: {}", signature);
    Ok(signature)
}
