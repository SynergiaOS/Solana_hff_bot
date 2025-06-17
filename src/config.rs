// Configuration management for SNIPERCOR
// Handles environment variables and system configuration

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::env;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub trading: TradingConfig,
    pub solana: SolanaConfig,
    pub api: ApiConfig,
    pub database: DatabaseConfig,
    pub server: ServerConfig,
    pub logging: LoggingConfig,
    // THE OVERMIND PROTOCOL - HFT Engine Configuration
    pub overmind: OvermindConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradingConfig {
    pub mode: TradingMode,
    pub max_position_size: f64,
    pub max_daily_loss: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TradingMode {
    Paper,
    Live,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SolanaConfig {
    pub rpc_url: String,
    pub wallet_private_key: String,
    // Multi-wallet support
    pub multi_wallet_enabled: bool,
    pub default_wallet_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiConfig {
    pub helius_api_key: String,
    pub helius_rpc_url: String,
    pub helius_ws_url: String,
    pub quicknode_api_key: String,
    pub quicknode_ws_url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DatabaseConfig {
    pub url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub port: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LoggingConfig {
    pub level: String,
}

// THE OVERMIND PROTOCOL - HFT Engine Configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OvermindConfig {
    pub enabled: bool,
    pub tensorzero_gateway_url: String,
    pub jito_endpoint: String,
    pub max_execution_latency_ms: u64,
    pub ai_confidence_threshold: f64,
}

#[allow(dead_code)]
impl Config {
    /// Load configuration from environment variables
    pub fn from_env() -> Result<Self> {
        dotenvy::dotenv().ok(); // Load .env file if present

        let trading_mode = match env::var("SNIPER_TRADING_MODE")
            .unwrap_or_else(|_| "paper".to_string())
            .to_lowercase()
            .as_str()
        {
            "live" => TradingMode::Live,
            _ => TradingMode::Paper,
        };

        let config = Config {
            trading: TradingConfig {
                mode: trading_mode,
                max_position_size: env::var("SNIPER_MAX_POSITION_SIZE")
                    .unwrap_or_else(|_| "1000".to_string())
                    .parse()
                    .context("Invalid SNIPER_MAX_POSITION_SIZE")?,
                max_daily_loss: env::var("SNIPER_MAX_DAILY_LOSS")
                    .unwrap_or_else(|_| "500".to_string())
                    .parse()
                    .context("Invalid SNIPER_MAX_DAILY_LOSS")?,
            },
            solana: SolanaConfig {
                rpc_url: env::var("SNIPER_SOLANA_RPC_URL")
                    .context("SNIPER_SOLANA_RPC_URL is required")?,
                wallet_private_key: env::var("SNIPER_WALLET_PRIVATE_KEY")
                    .context("SNIPER_WALLET_PRIVATE_KEY is required")?,
                multi_wallet_enabled: env::var("OVERMIND_MULTI_WALLET_ENABLED")
                    .unwrap_or_else(|_| "false".to_string())
                    .parse()
                    .unwrap_or(false),
                default_wallet_id: env::var("OVERMIND_DEFAULT_WALLET").ok(),
            },
            api: ApiConfig {
                helius_api_key: env::var("SNIPER_HELIUS_API_KEY")
                    .context("SNIPER_HELIUS_API_KEY is required")?,
                helius_rpc_url: env::var("SNIPER_HELIUS_RPC_URL")
                    .context("SNIPER_HELIUS_RPC_URL is required")?,
                helius_ws_url: env::var("SNIPER_HELIUS_WS_URL")
                    .context("SNIPER_HELIUS_WS_URL is required")?,
                quicknode_api_key: env::var("SNIPER_QUICKNODE_API_KEY")
                    .context("SNIPER_QUICKNODE_API_KEY is required")?,
                quicknode_ws_url: env::var("SNIPER_QUICKNODE_WS_URL")
                    .context("SNIPER_QUICKNODE_WS_URL is required")?,
            },
            database: DatabaseConfig {
                url: env::var("SNIPER_DATABASE_URL").context("SNIPER_DATABASE_URL is required")?,
            },
            server: ServerConfig {
                port: env::var("SNIPER_SERVER_PORT")
                    .unwrap_or_else(|_| "8080".to_string())
                    .parse()
                    .context("Invalid SNIPER_SERVER_PORT")?,
            },
            logging: LoggingConfig {
                level: env::var("SNIPER_LOG_LEVEL").unwrap_or_else(|_| "info".to_string()),
            },
            // THE OVERMIND PROTOCOL - HFT Engine Configuration
            overmind: OvermindConfig {
                enabled: env::var("OVERMIND_ENABLED")
                    .unwrap_or_else(|_| "false".to_string())
                    .parse()
                    .unwrap_or(false),
                tensorzero_gateway_url: env::var("OVERMIND_TENSORZERO_URL")
                    .unwrap_or_else(|_| "http://localhost:3000".to_string()),
                jito_endpoint: env::var("OVERMIND_JITO_ENDPOINT")
                    .unwrap_or_else(|_| "https://mainnet.block-engine.jito.wtf".to_string()),
                max_execution_latency_ms: env::var("OVERMIND_MAX_LATENCY_MS")
                    .unwrap_or_else(|_| "25".to_string())
                    .parse()
                    .unwrap_or(25),
                ai_confidence_threshold: env::var("OVERMIND_AI_CONFIDENCE_THRESHOLD")
                    .unwrap_or_else(|_| "0.7".to_string())
                    .parse()
                    .unwrap_or(0.7),
            },
        };

        // Validate configuration
        config.validate()?;

        Ok(config)
    }

    /// Validate configuration values
    fn validate(&self) -> Result<()> {
        if self.trading.max_position_size <= 0.0 {
            anyhow::bail!("max_position_size must be positive");
        }

        if self.trading.max_daily_loss <= 0.0 {
            anyhow::bail!("max_daily_loss must be positive");
        }

        if self.server.port == 0 {
            anyhow::bail!("server port must be valid");
        }

        Ok(())
    }

    /// Check if running in live trading mode
    pub fn is_live_trading(&self) -> bool {
        matches!(self.trading.mode, TradingMode::Live)
    }

    /// Get trading mode as string
    pub fn trading_mode_str(&self) -> &'static str {
        match self.trading.mode {
            TradingMode::Paper => "paper",
            TradingMode::Live => "live",
        }
    }

    /// Check if THE OVERMIND PROTOCOL is enabled
    pub fn is_overmind_enabled(&self) -> bool {
        self.overmind.enabled
    }

    /// Get OVERMIND mode description
    pub fn overmind_mode_str(&self) -> &'static str {
        if self.overmind.enabled {
            "THE OVERMIND PROTOCOL (AI-Enhanced)"
        } else {
            "Standard Mode"
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    // use std::env; // Commented out to avoid unused import warning

    #[test]
    fn test_config_validation() {
        let mut config = Config {
            trading: TradingConfig {
                mode: TradingMode::Paper,
                max_position_size: 1000.0,
                max_daily_loss: 500.0,
            },
            solana: SolanaConfig {
                rpc_url: "https://api.mainnet-beta.solana.com".to_string(),
                wallet_private_key: "test_key".to_string(),
            },
            api: ApiConfig {
                helius_api_key: "test_key".to_string(),
                helius_rpc_url: "https://devnet.helius-rpc.com".to_string(),
                helius_ws_url: "wss://devnet.helius-rpc.com".to_string(),
                quicknode_api_key: "test_key".to_string(),
                quicknode_ws_url: "wss://test.quiknode.pro".to_string(),
            },
            database: DatabaseConfig {
                url: "postgresql://test".to_string(),
            },
            server: ServerConfig { port: 8080 },
            logging: LoggingConfig {
                level: "info".to_string(),
            },
            overmind: OvermindConfig {
                enabled: false,
                tensorzero_gateway_url: "http://localhost:3000".to_string(),
                jito_endpoint: "https://mainnet.block-engine.jito.wtf".to_string(),
                max_execution_latency_ms: 25,
                ai_confidence_threshold: 0.7,
            },
        };

        assert!(config.validate().is_ok());

        // Test invalid position size
        config.trading.max_position_size = -100.0;
        assert!(config.validate().is_err());
    }

    #[test]
    fn test_trading_mode() {
        let config = Config {
            trading: TradingConfig {
                mode: TradingMode::Paper,
                max_position_size: 1000.0,
                max_daily_loss: 500.0,
            },
            solana: SolanaConfig {
                rpc_url: "test".to_string(),
                wallet_private_key: "test".to_string(),
            },
            api: ApiConfig {
                helius_api_key: "test".to_string(),
                helius_rpc_url: "https://devnet.helius-rpc.com".to_string(),
                helius_ws_url: "wss://devnet.helius-rpc.com".to_string(),
                quicknode_api_key: "test".to_string(),
                quicknode_ws_url: "wss://test.quiknode.pro".to_string(),
            },
            database: DatabaseConfig {
                url: "test".to_string(),
            },
            server: ServerConfig { port: 8080 },
            logging: LoggingConfig {
                level: "info".to_string(),
            },
            overmind: OvermindConfig {
                enabled: false,
                tensorzero_gateway_url: "http://localhost:3000".to_string(),
                jito_endpoint: "https://mainnet.block-engine.jito.wtf".to_string(),
                max_execution_latency_ms: 25,
                ai_confidence_threshold: 0.7,
            },
        };

        assert!(!config.is_live_trading());
        assert_eq!(config.trading_mode_str(), "paper");
    }
}
