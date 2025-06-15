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
        };

        assert!(!config.is_live_trading());
        assert_eq!(config.trading_mode_str(), "paper");
    }
}
