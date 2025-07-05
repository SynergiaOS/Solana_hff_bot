// THE OVERMIND PROTOCOL - Vault Integration Module
// Secure multi-wallet management with HashiCorp Vault

use anyhow::{anyhow, Result};
use base64::prelude::*;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VaultConfig {
    pub vault_url: String,
    pub vault_token: String,
    pub mount_path: String,
    pub role_id: Option<String>,
    pub secret_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WalletSecret {
    pub name: String,
    pub private_key: String,
    pub address: String,
    pub balance_sol: f64,
    pub security_level: String,
    pub created_at: String,
    pub last_accessed: String,
}

#[derive(Debug, Clone)]
pub struct VaultClient {
    client: Client,
    config: VaultConfig,
    token: Option<String>,
}

impl VaultClient {
    pub fn new(config: VaultConfig) -> Self {
        Self {
            client: Client::new(),
            config,
            token: None,
        }
    }

    // Authenticate with Vault using AppRole
    pub async fn authenticate(&mut self) -> Result<()> {
        if let (Some(role_id), Some(secret_id)) = (&self.config.role_id, &self.config.secret_id) {
            let auth_url = format!("{}/v1/auth/approle/login", self.config.vault_url);

            let auth_payload = serde_json::json!({
                "role_id": role_id,
                "secret_id": secret_id
            });

            let response = self
                .client
                .post(&auth_url)
                .json(&auth_payload)
                .send()
                .await?;

            if response.status().is_success() {
                let auth_response: serde_json::Value = response.json().await?;
                if let Some(token) = auth_response["auth"]["client_token"].as_str() {
                    self.token = Some(token.to_string());
                    info!("🔐 Vault authentication successful");
                    return Ok(());
                }
            }
        }

        // Fallback to direct token
        self.token = Some(self.config.vault_token.clone());
        Ok(())
    }

    // Store wallet secret in Vault
    pub async fn store_wallet(
        &self,
        wallet_name: &str,
        wallet_secret: &WalletSecret,
    ) -> Result<()> {
        let token = self
            .token
            .as_ref()
            .ok_or_else(|| anyhow!("Not authenticated"))?;

        let secret_path = format!("{}/data/wallets/{}", self.config.mount_path, wallet_name);
        let vault_url = format!("{}/v1/{}", self.config.vault_url, secret_path);

        let secret_data = serde_json::json!({
            "data": {
                "private_key": wallet_secret.private_key,
                "address": wallet_secret.address,
                "balance_sol": wallet_secret.balance_sol,
                "security_level": wallet_secret.security_level,
                "created_at": wallet_secret.created_at,
                "last_accessed": chrono::Utc::now().to_rfc3339()
            }
        });

        let response = self
            .client
            .post(&vault_url)
            .header("X-Vault-Token", token)
            .json(&secret_data)
            .send()
            .await?;

        if response.status().is_success() {
            info!("🔐 Wallet '{}' stored in Vault successfully", wallet_name);
            Ok(())
        } else {
            let error_text = response.text().await?;
            Err(anyhow!("Failed to store wallet in Vault: {}", error_text))
        }
    }

    // Retrieve wallet secret from Vault
    pub async fn get_wallet(&self, wallet_name: &str) -> Result<WalletSecret> {
        let token = self
            .token
            .as_ref()
            .ok_or_else(|| anyhow!("Not authenticated"))?;

        let secret_path = format!("{}/data/wallets/{}", self.config.mount_path, wallet_name);
        let vault_url = format!("{}/v1/{}", self.config.vault_url, secret_path);

        let response = self
            .client
            .get(&vault_url)
            .header("X-Vault-Token", token)
            .send()
            .await?;

        if response.status().is_success() {
            let vault_response: serde_json::Value = response.json().await?;

            if let Some(data) = vault_response["data"]["data"].as_object() {
                let wallet_secret = WalletSecret {
                    name: wallet_name.to_string(),
                    private_key: data["private_key"].as_str().unwrap_or("").to_string(),
                    address: data["address"].as_str().unwrap_or("").to_string(),
                    balance_sol: data["balance_sol"].as_f64().unwrap_or(0.0),
                    security_level: data["security_level"]
                        .as_str()
                        .unwrap_or("medium")
                        .to_string(),
                    created_at: data["created_at"].as_str().unwrap_or("").to_string(),
                    last_accessed: chrono::Utc::now().to_rfc3339(),
                };

                info!("🔐 Wallet '{}' retrieved from Vault", wallet_name);
                return Ok(wallet_secret);
            }
        }

        Err(anyhow!(
            "Failed to retrieve wallet '{}' from Vault",
            wallet_name
        ))
    }

    // List all available wallets
    pub async fn list_wallets(&self) -> Result<Vec<String>> {
        let token = self
            .token
            .as_ref()
            .ok_or_else(|| anyhow!("Not authenticated"))?;

        let list_path = format!("{}/metadata/wallets", self.config.mount_path);
        let vault_url = format!("{}/v1/{}?list=true", self.config.vault_url, list_path);

        let response = self
            .client
            .get(&vault_url)
            .header("X-Vault-Token", token)
            .send()
            .await?;

        if response.status().is_success() {
            let vault_response: serde_json::Value = response.json().await?;

            if let Some(keys) = vault_response["data"]["keys"].as_array() {
                let wallet_names: Vec<String> = keys
                    .iter()
                    .filter_map(|k| k.as_str().map(|s| s.to_string()))
                    .collect();

                info!("🔐 Found {} wallets in Vault", wallet_names.len());
                return Ok(wallet_names);
            }
        }

        Ok(vec![])
    }

    // Encrypt sensitive data using Vault Transit engine
    pub async fn encrypt_data(&self, plaintext: &str, key_name: &str) -> Result<String> {
        let token = self
            .token
            .as_ref()
            .ok_or_else(|| anyhow!("Not authenticated"))?;

        let encrypt_url = format!("{}/v1/transit/encrypt/{}", self.config.vault_url, key_name);

        let encrypt_payload = serde_json::json!({
            "plaintext": base64::prelude::BASE64_STANDARD.encode(plaintext.as_bytes())
        });

        let response = self
            .client
            .post(&encrypt_url)
            .header("X-Vault-Token", token)
            .json(&encrypt_payload)
            .send()
            .await?;

        if response.status().is_success() {
            let encrypt_response: serde_json::Value = response.json().await?;
            if let Some(ciphertext) = encrypt_response["data"]["ciphertext"].as_str() {
                return Ok(ciphertext.to_string());
            }
        }

        Err(anyhow!("Failed to encrypt data"))
    }

    // Health check for Vault connection
    pub async fn health_check(&self) -> Result<bool> {
        let health_url = format!("{}/v1/sys/health", self.config.vault_url);

        let response = self.client.get(&health_url).send().await?;

        Ok(response.status().is_success())
    }
}

// Multi-wallet manager with Vault integration
#[derive(Debug)]
pub struct VaultMultiWalletManager {
    vault_client: VaultClient,
    active_wallets: HashMap<String, WalletSecret>,
}

impl VaultMultiWalletManager {
    pub fn new(vault_config: VaultConfig) -> Self {
        Self {
            vault_client: VaultClient::new(vault_config),
            active_wallets: HashMap::new(),
        }
    }

    pub async fn initialize(&mut self) -> Result<()> {
        self.vault_client.authenticate().await?;

        // Load all wallets from Vault
        let wallet_names = self.vault_client.list_wallets().await?;

        for wallet_name in wallet_names {
            if let Ok(wallet) = self.vault_client.get_wallet(&wallet_name).await {
                self.active_wallets.insert(wallet_name, wallet);
            }
        }

        info!(
            "🔐 VaultMultiWalletManager initialized with {} wallets",
            self.active_wallets.len()
        );
        Ok(())
    }

    pub async fn get_wallet_for_trading(&self, strategy: &str) -> Result<&WalletSecret> {
        // Select appropriate wallet based on strategy
        let wallet_name = match strategy {
            "conservative" => "conservative-wallet",
            "arbitrage" => "arbitrage-wallet",
            "experimental" => "experimental-wallet",
            "main" => "main-trading-28sol",
            _ => "main-trading-28sol", // Default to main wallet
        };

        self.active_wallets
            .get(wallet_name)
            .ok_or_else(|| anyhow!("Wallet '{}' not found", wallet_name))
    }

    pub async fn migrate_existing_wallets(&mut self) -> Result<()> {
        // Migrate existing JSON wallets to Vault
        let wallet_files = std::fs::read_dir("wallets/")?;

        for entry in wallet_files {
            let entry = entry?;
            let path = entry.path();

            if path.extension().and_then(|s| s.to_str()) == Some("json") {
                if let Some(wallet_name) = path.file_stem().and_then(|s| s.to_str()) {
                    // Read existing wallet file
                    let wallet_content = std::fs::read_to_string(&path)?;
                    let wallet_data: serde_json::Value = serde_json::from_str(&wallet_content)?;

                    let wallet_secret = WalletSecret {
                        name: wallet_name.to_string(),
                        private_key: wallet_data["private_key"]
                            .as_str()
                            .unwrap_or("")
                            .to_string(),
                        address: wallet_data["address"].as_str().unwrap_or("").to_string(),
                        balance_sol: wallet_data["balance_sol"].as_f64().unwrap_or(0.0),
                        security_level: wallet_data["security_level"]
                            .as_str()
                            .unwrap_or("medium")
                            .to_string(),
                        created_at: wallet_data["created"].as_str().unwrap_or("").to_string(),
                        last_accessed: chrono::Utc::now().to_rfc3339(),
                    };

                    // Store in Vault
                    self.vault_client
                        .store_wallet(wallet_name, &wallet_secret)
                        .await?;
                    info!("🔐 Migrated wallet '{}' to Vault", wallet_name);
                }
            }
        }

        Ok(())
    }
}
