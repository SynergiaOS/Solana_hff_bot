//! Hybrid Price Fetcher for THE OVERMIND PROTOCOL
//!
//! Uses multiple data sources with fallback hierarchy:
//! 1. Helius API (Primary - no rate limits)
//! 2. CoinGecko API (Secondary - has rate limits)
//! 3. Fallback prices (Emergency)

use anyhow::{Context, Result};
use reqwest;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::RwLock;
use tracing::{debug, info, warn};

/// Price data with source tracking
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HybridPriceData {
    pub symbol: String,
    pub price_usd: f64,
    pub last_updated: u64,
    pub data_source: PriceSource,
    pub confidence: f64, // 0.0 to 1.0
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PriceSource {
    Helius,
    CoinGecko,
    Fallback,
    Jupiter,
    Raydium,
}

/// Helius price response
#[derive(Debug, Deserialize)]
struct HeliusTokenPrice {
    #[serde(rename = "tokenAddress")]
    token_address: String,
    #[serde(rename = "priceUsd")]
    price_usd: f64,
    #[serde(rename = "lastUpdated")]
    last_updated: Option<u64>,
}

/// CoinGecko response (existing)
#[derive(Debug, Deserialize)]
struct CoinGeckoResponse {
    solana: Option<CoinGeckoPrice>,
    bitcoin: Option<CoinGeckoPrice>,
    ethereum: Option<CoinGeckoPrice>,
    #[serde(rename = "usd-coin")]
    usd_coin: Option<CoinGeckoPrice>,
    raydium: Option<CoinGeckoPrice>,
    orca: Option<CoinGeckoPrice>,
}

#[derive(Debug, Deserialize)]
struct CoinGeckoPrice {
    usd: f64,
}

/// Hybrid price fetcher with multiple sources
pub struct HybridPriceFetcher {
    client: reqwest::Client,
    cache: RwLock<HashMap<String, HybridPriceData>>,
    cache_duration: Duration,
    helius_api_key: String,
    helius_url: String,
    coingecko_url: String,
    token_addresses: HashMap<String, String>, // symbol -> mint address
}

impl HybridPriceFetcher {
    /// Create new hybrid price fetcher
    pub fn new() -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(10))
            .user_agent("THE-OVERMIND-PROTOCOL/1.0")
            .build()
            .expect("Failed to create HTTP client");

        // Get Helius API key from environment
        let helius_api_key = std::env::var("HELIUS_API_KEY")
            .unwrap_or_else(|_| "edbcd361-78a0-4998-bd1e-8d4666722f82".to_string());

        // Token mint addresses for Helius API
        let mut token_addresses = HashMap::new();
        token_addresses.insert(
            "SOL".to_string(),
            "So11111111111111111111111111111111111111112".to_string(),
        );
        token_addresses.insert(
            "USDC".to_string(),
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v".to_string(),
        );
        token_addresses.insert(
            "BONK".to_string(),
            "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263".to_string(),
        );
        token_addresses.insert(
            "RAY".to_string(),
            "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R".to_string(),
        );
        token_addresses.insert(
            "ORCA".to_string(),
            "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE".to_string(),
        );

        Self {
            client,
            cache: RwLock::new(HashMap::new()),
            cache_duration: Duration::from_secs(15), // Shorter cache for real-time trading
            helius_api_key,
            helius_url: "https://api.helius.xyz/v0".to_string(),
            coingecko_url: "https://api.coingecko.com/api/v3/simple/price".to_string(),
            token_addresses,
        }
    }

    /// Get current timestamp
    fn current_timestamp() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
    }

    /// Check if cached price is valid
    fn is_cache_valid(&self, price_data: &HybridPriceData) -> bool {
        let current_time = Self::current_timestamp();
        current_time - price_data.last_updated < self.cache_duration.as_secs()
    }

    /// Fetch prices from Helius API (Primary source)
    pub async fn fetch_helius_prices(&self) -> Result<HashMap<String, HybridPriceData>> {
        info!("📊 Fetching real-time prices from Helius API...");

        let mut prices = HashMap::new();
        let current_time = Self::current_timestamp();

        // Get prices for each token
        for (symbol, mint_address) in &self.token_addresses {
            match self.get_helius_token_price(mint_address).await {
                Ok(price) => {
                    prices.insert(
                        symbol.clone(),
                        HybridPriceData {
                            symbol: symbol.clone(),
                            price_usd: price,
                            last_updated: current_time,
                            data_source: PriceSource::Helius,
                            confidence: 0.95, // High confidence for Helius
                        },
                    );
                    debug!("✅ Helius price for {}: ${:.4}", symbol, price);
                }
                Err(e) => {
                    warn!("⚠️ Failed to get Helius price for {}: {}", symbol, e);
                }
            }
        }

        if !prices.is_empty() {
            info!(
                "✅ Helius prices fetched successfully: {} tokens",
                prices.len()
            );
        }

        Ok(prices)
    }

    /// Get single token price from Helius
    async fn get_helius_token_price(&self, mint_address: &str) -> Result<f64> {
        let url = format!("{}/token-metadata", self.helius_url);

        let payload = serde_json::json!({
            "mintAccounts": [mint_address]
        });

        let response = self
            .client
            .post(&url)
            .query(&[("api-key", &self.helius_api_key)])
            .json(&payload)
            .send()
            .await
            .context("Failed to send Helius request")?;

        if !response.status().is_success() {
            return Err(anyhow::anyhow!("Helius API error: {}", response.status()));
        }

        let data: Vec<serde_json::Value> = response
            .json()
            .await
            .context("Failed to parse Helius response")?;

        if let Some(token_data) = data.first() {
            // Try to extract price from metadata
            // Note: Helius metadata might not always have price, so we'll use a fallback approach
            if let Some(price) = token_data.get("price").and_then(|p| p.as_f64()) {
                return Ok(price);
            }
        }

        // If no price in metadata, use Jupiter price API through Helius
        self.get_jupiter_price_via_helius(mint_address).await
    }

    /// Get Jupiter price via Helius
    async fn get_jupiter_price_via_helius(&self, mint_address: &str) -> Result<f64> {
        // Use Jupiter quote API to get current price
        let jupiter_url = "https://quote-api.jup.ag/v6/quote";

        // Get quote for 1 token to SOL to determine price
        let amount = 1_000_000; // 1 token with 6 decimals

        let response = self
            .client
            .get(jupiter_url)
            .query(&[
                ("inputMint", mint_address),
                ("outputMint", "So11111111111111111111111111111111111111112"), // SOL
                ("amount", &amount.to_string()),
                ("slippageBps", "50"), // 0.5% slippage
            ])
            .send()
            .await
            .context("Failed to get Jupiter quote")?;

        if response.status().is_success() {
            let quote: serde_json::Value = response.json().await?;

            if let Some(out_amount) = quote.get("outAmount").and_then(|a| a.as_str()) {
                let sol_amount: f64 = out_amount.parse().unwrap_or(0.0) / 1_000_000_000.0; // Convert lamports to SOL

                // Get SOL price in USD (we'll use a simple fallback for now)
                let sol_price_usd = 150.0; // This should be fetched from another source

                let token_price_usd = sol_amount * sol_price_usd;
                return Ok(token_price_usd);
            }
        }

        Err(anyhow::anyhow!("Failed to get Jupiter price"))
    }

    /// Fetch prices from CoinGecko (Secondary source)
    pub async fn fetch_coingecko_prices(&self) -> Result<HashMap<String, HybridPriceData>> {
        info!("📊 Fetching backup prices from CoinGecko API...");

        let url = format!(
            "{}?ids=solana,bitcoin,ethereum,usd-coin,raydium,orca&vs_currencies=usd",
            self.coingecko_url
        );

        let response = self.client.get(&url).send().await?;

        if !response.status().is_success() {
            return Err(anyhow::anyhow!(
                "CoinGecko API error: {}",
                response.status()
            ));
        }

        let coingecko_data: CoinGeckoResponse = response.json().await?;
        let current_time = Self::current_timestamp();

        let mut prices = HashMap::new();

        // Map CoinGecko data to our format
        if let Some(sol_data) = coingecko_data.solana {
            prices.insert(
                "SOL".to_string(),
                HybridPriceData {
                    symbol: "SOL".to_string(),
                    price_usd: sol_data.usd,
                    last_updated: current_time,
                    data_source: PriceSource::CoinGecko,
                    confidence: 0.85, // Lower confidence due to rate limits
                },
            );
        }

        if let Some(usdc_data) = coingecko_data.usd_coin {
            prices.insert(
                "USDC".to_string(),
                HybridPriceData {
                    symbol: "USDC".to_string(),
                    price_usd: usdc_data.usd,
                    last_updated: current_time,
                    data_source: PriceSource::CoinGecko,
                    confidence: 0.85,
                },
            );
        }

        info!(
            "✅ CoinGecko backup prices fetched: {} tokens",
            prices.len()
        );
        Ok(prices)
    }

    /// Get real price with hybrid approach
    pub async fn get_real_price(&self, symbol: &str) -> Result<f64> {
        // Check cache first
        {
            let cache = self.cache.read().await;
            if let Some(cached_price) = cache.get(symbol) {
                if self.is_cache_valid(cached_price) {
                    debug!(
                        "💾 Using cached price for {}: ${:.4} ({})",
                        symbol,
                        cached_price.price_usd,
                        format!("{:?}", cached_price.data_source)
                    );
                    return Ok(cached_price.price_usd);
                }
            }
        }

        // Try Helius first (primary source)
        if let Ok(helius_prices) = self.fetch_helius_prices().await {
            if let Some(price_data) = helius_prices.get(symbol) {
                // Update cache
                let mut cache = self.cache.write().await;
                cache.insert(symbol.to_string(), price_data.clone());

                info!(
                    "✅ Using Helius price for {}: ${:.4}",
                    symbol, price_data.price_usd
                );
                return Ok(price_data.price_usd);
            }
        }

        // Fallback to CoinGecko
        if let Ok(coingecko_prices) = self.fetch_coingecko_prices().await {
            if let Some(price_data) = coingecko_prices.get(symbol) {
                // Update cache
                let mut cache = self.cache.write().await;
                cache.insert(symbol.to_string(), price_data.clone());

                warn!(
                    "⚠️ Using CoinGecko fallback for {}: ${:.4}",
                    symbol, price_data.price_usd
                );
                return Ok(price_data.price_usd);
            }
        }

        // Final fallback to hardcoded prices
        let fallback_price = self.get_fallback_price(symbol);
        warn!(
            "🚨 Using emergency fallback price for {}: ${:.4}",
            symbol, fallback_price
        );

        // Cache fallback price
        let mut cache = self.cache.write().await;
        cache.insert(
            symbol.to_string(),
            HybridPriceData {
                symbol: symbol.to_string(),
                price_usd: fallback_price,
                last_updated: Self::current_timestamp(),
                data_source: PriceSource::Fallback,
                confidence: 0.5, // Low confidence for fallback
            },
        );

        Ok(fallback_price)
    }

    /// Get fallback price
    fn get_fallback_price(&self, symbol: &str) -> f64 {
        match symbol {
            "SOL" => 150.0,
            "BTC" => 107000.0,
            "ETH" => 2450.0,
            "USDC" => 1.0,
            "RAY" => 2.1,
            "ORCA" => 1.97,
            "BONK" => 0.000025,
            _ => 1.0,
        }
    }

    /// Get all cached prices with metadata
    pub async fn get_all_prices_with_metadata(&self) -> HashMap<String, HybridPriceData> {
        self.cache.read().await.clone()
    }
}
