// THE OVERMIND PROTOCOL - Multi-Wallet Configuration System
// Production-grade configuration management for multiple Solana wallets

use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use std::path::Path;
use tracing::info;

use crate::modules::strategy::StrategyType;
use crate::modules::wallet_manager::{
    WalletConfig, WalletConfigBuilder, WalletRiskLimits, WalletType,
};

/// Multi-wallet configuration for THE OVERMIND PROTOCOL
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiWalletConfig {
    pub default_wallet_id: String,
    pub wallets: HashMap<String, WalletConfig>,
    pub global_settings: GlobalWalletSettings,
    pub strategy_routing: HashMap<StrategyType, Vec<String>>,
}

/// Global settings that apply to all wallets
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlobalWalletSettings {
    pub max_concurrent_wallets: u32,
    pub wallet_selection_timeout_ms: u64,
    pub balance_check_interval_sec: u64,
    pub emergency_stop_threshold: f64,
    pub auto_rebalance_enabled: bool,
    pub risk_aggregation_enabled: bool,
}

/// Wallet configuration from environment variables
#[derive(Debug, Clone)]
pub struct EnvWalletConfig {
    pub wallet_id: String,
    pub name: String,
    pub private_key_path: String,
    pub wallet_type: WalletType,
    pub risk_profile: String,
    pub max_allocation: f64,
}

impl MultiWalletConfig {
    /// Load multi-wallet configuration from environment variables
    pub fn from_env() -> Result<Self> {
        info!("🏦 Loading multi-wallet configuration from environment");

        // Parse managed wallets from environment
        let managed_wallets = env::var("OVERMIND_MANAGED_WALLETS")
            .context("OVERMIND_MANAGED_WALLETS environment variable not set")?;

        let wallet_configs = Self::parse_managed_wallets(&managed_wallets)?;
        
        // Set default wallet
        let default_wallet_id = env::var("OVERMIND_DEFAULT_WALLET")
            .unwrap_or_else(|_| {
                wallet_configs.first()
                    .map(|w| w.wallet_id.clone())
                    .unwrap_or_else(|| "primary".to_string())
            });

        // Build wallet configurations
        let mut wallets = HashMap::new();
        let mut strategy_routing = HashMap::new();

        for env_config in wallet_configs {
            let wallet_config = Self::build_wallet_config(env_config)?;
            
            // Add to strategy routing
            for allocation in &wallet_config.strategy_allocation {
                if allocation.enabled {
                    strategy_routing
                        .entry(allocation.strategy_type.clone())
                        .or_insert_with(Vec::new)
                        .push(wallet_config.wallet_id.clone());
                }
            }
            
            wallets.insert(wallet_config.wallet_id.clone(), wallet_config);
        }

        let global_settings = GlobalWalletSettings::from_env()?;

        Ok(Self {
            default_wallet_id,
            wallets,
            global_settings,
            strategy_routing,
        })
    }

    /// Parse managed wallets string from environment
    /// Format: "wallet_id:path:type:risk:allocation,wallet_id2:path2:type2:risk2:allocation2"
    fn parse_managed_wallets(managed_wallets: &str) -> Result<Vec<EnvWalletConfig>> {
        let mut configs = Vec::new();

        for wallet_def in managed_wallets.split(',') {
            let parts: Vec<&str> = wallet_def.split(':').collect();
            
            if parts.len() != 5 {
                return Err(anyhow!(
                    "Invalid wallet definition format. Expected 'id:path:type:risk:allocation', got: {}",
                    wallet_def
                ));
            }

            let wallet_type = match parts[2].to_lowercase().as_str() {
                "primary" => WalletType::Primary,
                "secondary" => WalletType::Secondary,
                "hft" => WalletType::HFT,
                "conservative" => WalletType::Conservative,
                "experimental" => WalletType::Experimental,
                "arbitrage" => WalletType::Arbitrage,
                "mev" | "mevprotection" => WalletType::MEVProtection,
                "emergency" => WalletType::Emergency,
                _ => return Err(anyhow!("Invalid wallet type: {}", parts[2])),
            };

            let max_allocation: f64 = parts[4].parse()
                .context("Invalid allocation percentage")?;

            if max_allocation < 0.0 || max_allocation > 1.0 {
                return Err(anyhow!("Allocation must be between 0.0 and 1.0, got: {}", max_allocation));
            }

            configs.push(EnvWalletConfig {
                wallet_id: parts[0].to_string(),
                name: parts[0].replace('_', " ").to_title_case(),
                private_key_path: parts[1].to_string(),
                wallet_type,
                risk_profile: parts[3].to_string(),
                max_allocation,
            });
        }

        if configs.is_empty() {
            return Err(anyhow!("No wallet configurations found"));
        }

        info!("📋 Parsed {} wallet configurations", configs.len());
        Ok(configs)
    }

    /// Build wallet configuration from environment config
    fn build_wallet_config(env_config: EnvWalletConfig) -> Result<WalletConfig> {
        // Load private key from file or environment
        let private_key = if env_config.private_key_path.starts_with("env:") {
            let env_var = &env_config.private_key_path[4..];
            env::var(env_var)
                .context(format!("Environment variable {} not found", env_var))?
        } else if Path::new(&env_config.private_key_path).exists() {
            std::fs::read_to_string(&env_config.private_key_path)
                .context("Failed to read private key file")?
                .trim()
                .to_string()
        } else {
            return Err(anyhow!("Private key path not found: {}", env_config.private_key_path));
        };

        // Create risk limits based on risk profile
        let risk_limits = Self::create_risk_limits(&env_config.risk_profile, env_config.max_allocation)?;

        // Create strategy allocations based on wallet type
        let strategy_allocations = Self::create_strategy_allocations(&env_config.wallet_type, env_config.max_allocation);

        let mut builder = WalletConfigBuilder::new(
            env_config.wallet_id.clone(),
            env_config.name,
            private_key,
        )?;

        builder = builder
            .wallet_type(env_config.wallet_type)
            .risk_limits(risk_limits)
            .description(format!("Auto-configured {} wallet", env_config.risk_profile));

        // Add strategy allocations
        for (strategy_type, allocation_pct, max_position) in strategy_allocations {
            builder = builder.add_strategy_allocation(strategy_type, allocation_pct, max_position);
        }

        Ok(builder.build())
    }

    /// Create risk limits based on risk profile
    fn create_risk_limits(risk_profile: &str, max_allocation: f64) -> Result<WalletRiskLimits> {
        let base_limits = match risk_profile.to_lowercase().as_str() {
            "low" | "conservative" => WalletRiskLimits {
                max_daily_loss: 100.0,
                max_position_size: 1000.0,
                max_concurrent_positions: 3,
                max_exposure_percentage: 20.0,
                stop_loss_threshold: 2.0,
                daily_trade_limit: 10,
            },
            "medium" | "moderate" => WalletRiskLimits {
                max_daily_loss: 500.0,
                max_position_size: 5000.0,
                max_concurrent_positions: 5,
                max_exposure_percentage: 50.0,
                stop_loss_threshold: 3.0,
                daily_trade_limit: 25,
            },
            "high" | "aggressive" => WalletRiskLimits {
                max_daily_loss: 2000.0,
                max_position_size: 20000.0,
                max_concurrent_positions: 10,
                max_exposure_percentage: 80.0,
                stop_loss_threshold: 5.0,
                daily_trade_limit: 50,
            },
            "experimental" => WalletRiskLimits {
                max_daily_loss: 50.0,
                max_position_size: 500.0,
                max_concurrent_positions: 2,
                max_exposure_percentage: 10.0,
                stop_loss_threshold: 1.0,
                daily_trade_limit: 5,
            },
            _ => return Err(anyhow!("Invalid risk profile: {}", risk_profile)),
        };

        // Scale limits by allocation
        Ok(WalletRiskLimits {
            max_daily_loss: base_limits.max_daily_loss * max_allocation,
            max_position_size: base_limits.max_position_size * max_allocation,
            max_concurrent_positions: base_limits.max_concurrent_positions,
            max_exposure_percentage: base_limits.max_exposure_percentage,
            stop_loss_threshold: base_limits.stop_loss_threshold,
            daily_trade_limit: base_limits.daily_trade_limit,
        })
    }

    /// Create strategy allocations based on wallet type
    fn create_strategy_allocations(wallet_type: &WalletType, max_allocation: f64) -> Vec<(StrategyType, f64, f64)> {
        let base_allocation = max_allocation * 100.0; // Convert to percentage
        
        match wallet_type {
            WalletType::Primary => vec![
                (StrategyType::TokenSniping, base_allocation * 0.4, 5000.0),
                (StrategyType::Arbitrage, base_allocation * 0.3, 3000.0),
                (StrategyType::MomentumTrading, base_allocation * 0.3, 2000.0),
            ],
            WalletType::HFT => vec![
                (StrategyType::Arbitrage, base_allocation * 0.6, 10000.0),
                (StrategyType::TokenSniping, base_allocation * 0.4, 8000.0),
            ],
            WalletType::Conservative => vec![
                (StrategyType::MomentumTrading, base_allocation * 0.7, 1000.0),
                (StrategyType::Arbitrage, base_allocation * 0.3, 500.0),
            ],
            WalletType::Experimental => vec![
                (StrategyType::SoulMeteorSniping, base_allocation * 0.5, 200.0),
                (StrategyType::MeteoraDAMM, base_allocation * 0.3, 150.0),
                (StrategyType::DeveloperTracking, base_allocation * 0.2, 100.0),
            ],
            WalletType::Arbitrage => vec![
                (StrategyType::Arbitrage, base_allocation * 1.0, 15000.0),
            ],
            WalletType::MEVProtection => vec![
                (StrategyType::TokenSniping, base_allocation * 0.6, 8000.0),
                (StrategyType::Arbitrage, base_allocation * 0.4, 5000.0),
            ],
            _ => vec![
                (StrategyType::MomentumTrading, base_allocation * 1.0, 1000.0),
            ],
        }
    }

    /// Save configuration to file
    pub async fn save_to_file(&self, path: &str) -> Result<()> {
        let content = serde_json::to_string_pretty(self)
            .context("Failed to serialize multi-wallet configuration")?;
        
        tokio::fs::write(path, content).await
            .context("Failed to write configuration file")?;
        
        info!("💾 Saved multi-wallet configuration to {}", path);
        Ok(())
    }

    /// Load configuration from file
    pub async fn load_from_file(path: &str) -> Result<Self> {
        let content = tokio::fs::read_to_string(path).await
            .context("Failed to read configuration file")?;
        
        let config: Self = serde_json::from_str(&content)
            .context("Failed to parse configuration file")?;
        
        info!("📂 Loaded multi-wallet configuration from {}", path);
        Ok(config)
    }
}

impl GlobalWalletSettings {
    fn from_env() -> Result<Self> {
        Ok(Self {
            max_concurrent_wallets: env::var("OVERMIND_MAX_CONCURRENT_WALLETS")
                .unwrap_or_else(|_| "10".to_string())
                .parse()
                .context("Invalid OVERMIND_MAX_CONCURRENT_WALLETS")?,
            
            wallet_selection_timeout_ms: env::var("OVERMIND_WALLET_SELECTION_TIMEOUT_MS")
                .unwrap_or_else(|_| "5000".to_string())
                .parse()
                .context("Invalid OVERMIND_WALLET_SELECTION_TIMEOUT_MS")?,
            
            balance_check_interval_sec: env::var("OVERMIND_BALANCE_CHECK_INTERVAL_SEC")
                .unwrap_or_else(|_| "300".to_string())
                .parse()
                .context("Invalid OVERMIND_BALANCE_CHECK_INTERVAL_SEC")?,
            
            emergency_stop_threshold: env::var("OVERMIND_EMERGENCY_STOP_THRESHOLD")
                .unwrap_or_else(|_| "0.1".to_string())
                .parse()
                .context("Invalid OVERMIND_EMERGENCY_STOP_THRESHOLD")?,
            
            auto_rebalance_enabled: env::var("OVERMIND_AUTO_REBALANCE_ENABLED")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .context("Invalid OVERMIND_AUTO_REBALANCE_ENABLED")?,
            
            risk_aggregation_enabled: env::var("OVERMIND_RISK_AGGREGATION_ENABLED")
                .unwrap_or_else(|_| "true".to_string())
                .parse()
                .context("Invalid OVERMIND_RISK_AGGREGATION_ENABLED")?,
        })
    }
}

impl Default for GlobalWalletSettings {
    fn default() -> Self {
        Self {
            max_concurrent_wallets: 10,
            wallet_selection_timeout_ms: 5000,
            balance_check_interval_sec: 300,
            emergency_stop_threshold: 0.1,
            auto_rebalance_enabled: true,
            risk_aggregation_enabled: true,
        }
    }
}

/// Helper trait for string case conversion
trait ToTitleCase {
    fn to_title_case(&self) -> String;
}

impl ToTitleCase for str {
    fn to_title_case(&self) -> String {
        self.split_whitespace()
            .map(|word| {
                let mut chars = word.chars();
                match chars.next() {
                    None => String::new(),
                    Some(first) => first.to_uppercase().collect::<String>() + &chars.as_str().to_lowercase(),
                }
            })
            .collect::<Vec<String>>()
            .join(" ")
    }
}
