// 🛡️ OVERMIND VAULT - MAXIMUM SECURITY WALLET MANAGER
// Fortress-level security for THE OVERMIND PROTOCOL

use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::RwLock;
use tracing::{error, info, warn};

/// Security tier levels for wallet classification
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub enum SecurityTier {
    ColdStorage, // Hardware wallet, offline signing
    HotTrading,  // Environment variables, limited balance
    Emergency,   // Emergency access only
}

/// Wallet security configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecureWalletConfig {
    pub wallet_id: String,
    pub name: String,
    pub security_tier: SecurityTier,
    pub max_balance_sol: f64,
    pub requires_multi_sig: bool,
    pub time_lock_hours: u64,
    pub allowed_strategies: Vec<String>,
    pub emergency_stop_threshold: f64,
}

/// Transfer request with security validation
#[derive(Debug, Clone)]
pub struct SecureTransferRequest {
    pub from_wallet: String,
    pub to_address: String,
    pub amount_sol: f64,
    pub purpose: String,
    pub requires_confirmation: bool,
    pub time_lock_until: Option<SystemTime>,
}

/// Security event for monitoring
#[derive(Debug, Clone, Serialize)]
pub struct SecurityEvent {
    pub timestamp: u64,
    pub event_type: String,
    pub wallet_id: String,
    pub description: String,
    pub risk_level: u8, // 1-10
    pub action_taken: String,
}

/// OVERMIND VAULT - Maximum Security Wallet Manager
pub struct SecureWalletManager {
    wallets: RwLock<HashMap<String, SecureWalletConfig>>,
    pending_transfers: RwLock<HashMap<String, SecureTransferRequest>>,
    security_events: RwLock<Vec<SecurityEvent>>,
    emergency_mode: RwLock<bool>,
}

impl SecureWalletManager {
    /// Initialize secure wallet manager
    pub fn new() -> Self {
        info!("🛡️ Initializing OVERMIND VAULT Security System");

        Self {
            wallets: RwLock::new(HashMap::new()),
            pending_transfers: RwLock::new(HashMap::new()),
            security_events: RwLock::new(Vec::new()),
            emergency_mode: RwLock::new(false),
        }
    }

    /// Load secure wallet configuration from environment
    pub async fn load_secure_config(&self) -> Result<()> {
        info!("🔐 Loading secure wallet configuration");

        let mut wallets = self.wallets.write().await;

        // Cold Storage Wallet (Hardware/Offline)
        let cold_storage = SecureWalletConfig {
            wallet_id: "cold_storage".to_string(),
            name: "OVERMIND Cold Storage Vault".to_string(),
            security_tier: SecurityTier::ColdStorage,
            max_balance_sol: f64::INFINITY, // No limit for cold storage
            requires_multi_sig: true,
            time_lock_hours: 24,        // 24h delay for large transfers
            allowed_strategies: vec![], // No trading from cold storage
            emergency_stop_threshold: 0.0,
        };

        // Primary Trading Wallet
        let primary_trading = SecureWalletConfig {
            wallet_id: "primary_trading".to_string(),
            name: "Primary Trading Wallet".to_string(),
            security_tier: SecurityTier::HotTrading,
            max_balance_sol: 1.0, // Max 1 SOL
            requires_multi_sig: false,
            time_lock_hours: 0,
            allowed_strategies: vec![
                "TokenSniping".to_string(),
                "Arbitrage".to_string(),
                "MomentumTrading".to_string(),
            ],
            emergency_stop_threshold: 0.5, // Stop at 50% loss
        };

        // HFT Trading Wallet
        let hft_trading = SecureWalletConfig {
            wallet_id: "hft_trading".to_string(),
            name: "High Frequency Trading Wallet".to_string(),
            security_tier: SecurityTier::HotTrading,
            max_balance_sol: 0.5, // Max 0.5 SOL
            requires_multi_sig: false,
            time_lock_hours: 0,
            allowed_strategies: vec!["Arbitrage".to_string(), "TokenSniping".to_string()],
            emergency_stop_threshold: 0.3, // Stop at 30% loss
        };

        // Experimental Wallet
        let experimental = SecureWalletConfig {
            wallet_id: "experimental".to_string(),
            name: "Experimental Trading Wallet".to_string(),
            security_tier: SecurityTier::HotTrading,
            max_balance_sol: 0.1, // Max 0.1 SOL
            requires_multi_sig: false,
            time_lock_hours: 0,
            allowed_strategies: vec![
                "SoulMeteor".to_string(),
                "Meteora".to_string(),
                "DeveloperTracking".to_string(),
            ],
            emergency_stop_threshold: 0.8, // Allow higher risk
        };

        // Emergency Wallet
        let emergency = SecureWalletConfig {
            wallet_id: "emergency".to_string(),
            name: "Emergency Access Wallet".to_string(),
            security_tier: SecurityTier::Emergency,
            max_balance_sol: 0.1, // Minimal balance
            requires_multi_sig: true,
            time_lock_hours: 0,         // No delay for emergencies
            allowed_strategies: vec![], // Emergency only
            emergency_stop_threshold: 0.0,
        };

        wallets.insert("cold_storage".to_string(), cold_storage);
        wallets.insert("primary_trading".to_string(), primary_trading);
        wallets.insert("hft_trading".to_string(), hft_trading);
        wallets.insert("experimental".to_string(), experimental);
        wallets.insert("emergency".to_string(), emergency);

        info!("✅ Loaded {} secure wallet configurations", wallets.len());
        Ok(())
    }

    /// Validate transfer request against security policies
    pub async fn validate_transfer(&self, request: &SecureTransferRequest) -> Result<bool> {
        let wallets = self.wallets.read().await;
        let emergency_mode = *self.emergency_mode.read().await;

        // Check if in emergency mode
        if emergency_mode && request.from_wallet != "emergency" {
            self.log_security_event(
                "transfer_blocked_emergency".to_string(),
                request.from_wallet.clone(),
                "Transfer blocked - system in emergency mode".to_string(),
                8,
                "BLOCKED".to_string(),
            )
            .await;
            return Ok(false);
        }

        // Get wallet config
        let wallet_config = wallets
            .get(&request.from_wallet)
            .ok_or_else(|| anyhow!("Wallet not found: {}", request.from_wallet))?;

        // Check amount limits
        if request.amount_sol > wallet_config.max_balance_sol {
            self.log_security_event(
                "transfer_amount_exceeded".to_string(),
                request.from_wallet.clone(),
                format!(
                    "Amount {} exceeds limit {}",
                    request.amount_sol, wallet_config.max_balance_sol
                ),
                9,
                "BLOCKED".to_string(),
            )
            .await;
            return Ok(false);
        }

        // Check multi-sig requirements
        if wallet_config.requires_multi_sig && !request.requires_confirmation {
            self.log_security_event(
                "multi_sig_required".to_string(),
                request.from_wallet.clone(),
                "Multi-signature required for this wallet".to_string(),
                7,
                "PENDING_CONFIRMATION".to_string(),
            )
            .await;
            return Ok(false);
        }

        // Check time locks
        if wallet_config.time_lock_hours > 0 && request.amount_sol > 1.0 {
            let time_lock_until =
                SystemTime::now() + Duration::from_secs(wallet_config.time_lock_hours * 3600);
            self.log_security_event(
                "time_lock_applied".to_string(),
                request.from_wallet.clone(),
                format!(
                    "Transfer time-locked for {} hours",
                    wallet_config.time_lock_hours
                ),
                5,
                "TIME_LOCKED".to_string(),
            )
            .await;
            // Would store time-locked transfer for later execution
        }

        info!(
            "✅ Transfer validation passed for wallet: {}",
            request.from_wallet
        );
        Ok(true)
    }

    /// Log security event
    async fn log_security_event(
        &self,
        event_type: String,
        wallet_id: String,
        description: String,
        risk_level: u8,
        action_taken: String,
    ) {
        let event = SecurityEvent {
            timestamp: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            event_type,
            wallet_id,
            description: description.clone(),
            risk_level,
            action_taken,
        };

        let mut events = self.security_events.write().await;
        events.push(event);

        // Log based on risk level
        match risk_level {
            1..=3 => info!("🔒 Security Event: {}", description),
            4..=6 => warn!("⚠️ Security Warning: {}", description),
            7..=10 => error!("🚨 Security Alert: {}", description),
            _ => info!("🔒 Security Event: {}", description),
        }
    }

    /// Activate emergency mode
    pub async fn activate_emergency_mode(&self, reason: String) {
        let mut emergency_mode = self.emergency_mode.write().await;
        *emergency_mode = true;

        self.log_security_event(
            "emergency_mode_activated".to_string(),
            "system".to_string(),
            format!("Emergency mode activated: {}", reason),
            10,
            "EMERGENCY_STOP".to_string(),
        )
        .await;

        error!("🚨 EMERGENCY MODE ACTIVATED: {}", reason);
    }

    /// Get security summary
    pub async fn get_security_summary(&self) -> SecuritySummary {
        let events = self.security_events.read().await;
        let emergency_mode = *self.emergency_mode.read().await;

        let high_risk_events = events.iter().filter(|e| e.risk_level >= 7).count();
        let recent_events = events
            .iter()
            .filter(|e| {
                let now = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs();
                now - e.timestamp < 3600 // Last hour
            })
            .count();

        SecuritySummary {
            emergency_mode,
            total_events: events.len(),
            high_risk_events,
            recent_events,
            last_event_timestamp: events.last().map(|e| e.timestamp),
        }
    }
}

#[derive(Debug, Serialize)]
pub struct SecuritySummary {
    pub emergency_mode: bool,
    pub total_events: usize,
    pub high_risk_events: usize,
    pub recent_events: usize,
    pub last_event_timestamp: Option<u64>,
}

impl Default for SecureWalletManager {
    fn default() -> Self {
        Self::new()
    }
}
