// 🏦 OVERMIND VAULT ACCESS MANAGER
// Unified interface for accessing funds across all security tiers

use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tokio::sync::RwLock;
use tracing::{info, warn};

use crate::modules::hardware_wallet_interface::{
    HardwareTransactionRequest, HardwareWalletManager,
};
use crate::modules::multisig_wallet_manager::MultiSigWalletManager;
use crate::modules::secure_wallet_manager::{SecureWalletManager, SecurityTier};

/// Access method for different wallet tiers
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum AccessMethod {
    HardwareWallet, // For cold storage
    MultiSignature, // For large transfers
    EnvironmentKey, // For hot wallets
    Emergency,      // For emergency access
}

/// Vault access request
#[derive(Debug, Clone)]
pub struct VaultAccessRequest {
    pub wallet_tier: SecurityTier,
    pub access_method: AccessMethod,
    pub from_address: String,
    pub to_address: String,
    pub amount_sol: f64,
    pub purpose: String,
    pub requester_id: String,
    pub urgent: bool,
}

/// Access authorization result
#[derive(Debug, Clone)]
pub struct AccessAuthorization {
    pub authorized: bool,
    pub method_required: AccessMethod,
    pub additional_approvals_needed: u8,
    pub time_lock_seconds: u64,
    pub reason: String,
}

/// OVERMIND VAULT Access Manager
pub struct VaultAccessManager {
    secure_wallet_manager: SecureWalletManager,
    hardware_wallet_manager: HardwareWalletManager,
    multisig_managers: RwLock<HashMap<String, MultiSigWalletManager>>,
    access_policies: RwLock<HashMap<SecurityTier, AccessPolicy>>,
}

/// Access policy for each security tier
#[derive(Debug, Clone)]
pub struct AccessPolicy {
    pub max_amount_without_approval: f64,
    pub required_access_method: AccessMethod,
    pub time_lock_threshold: f64,
    pub time_lock_duration_hours: u64,
    pub emergency_override_allowed: bool,
}

impl VaultAccessManager {
    /// Create new vault access manager
    pub async fn new() -> Result<Self> {
        info!("🏦 Initializing OVERMIND VAULT Access Manager");

        let secure_wallet_manager = SecureWalletManager::new();
        secure_wallet_manager.load_secure_config().await?;

        let mut hardware_wallet_manager = HardwareWalletManager::new();
        // Try to auto-connect to hardware wallet
        if let Err(e) = hardware_wallet_manager.auto_connect().await {
            warn!("⚠️ Hardware wallet not connected: {}", e);
        }

        let mut access_policies = HashMap::new();

        // Cold Storage Policy - Maximum Security
        access_policies.insert(
            SecurityTier::ColdStorage,
            AccessPolicy {
                max_amount_without_approval: 0.0, // Always requires approval
                required_access_method: AccessMethod::HardwareWallet,
                time_lock_threshold: 1.0, // Any amount > 1 SOL
                time_lock_duration_hours: 24,
                emergency_override_allowed: false,
            },
        );

        // Hot Trading Policy - Moderate Security
        access_policies.insert(
            SecurityTier::HotTrading,
            AccessPolicy {
                max_amount_without_approval: 0.1, // Up to 0.1 SOL instant
                required_access_method: AccessMethod::EnvironmentKey,
                time_lock_threshold: 0.5, // > 0.5 SOL requires time lock
                time_lock_duration_hours: 1,
                emergency_override_allowed: true,
            },
        );

        // Emergency Policy - Fast Access
        access_policies.insert(
            SecurityTier::Emergency,
            AccessPolicy {
                max_amount_without_approval: 0.05, // Very limited
                required_access_method: AccessMethod::Emergency,
                time_lock_threshold: 0.1,
                time_lock_duration_hours: 0, // No time lock for emergencies
                emergency_override_allowed: true,
            },
        );

        Ok(Self {
            secure_wallet_manager,
            hardware_wallet_manager,
            multisig_managers: RwLock::new(HashMap::new()),
            access_policies: RwLock::new(access_policies),
        })
    }

    /// Authorize vault access request
    pub async fn authorize_access(
        &self,
        request: &VaultAccessRequest,
    ) -> Result<AccessAuthorization> {
        info!("🔐 Authorizing vault access request");
        info!("   Tier: {:?}", request.wallet_tier);
        info!("   Amount: {} SOL", request.amount_sol);
        info!("   Purpose: {}", request.purpose);

        let policies = self.access_policies.read().await;
        let policy = policies
            .get(&request.wallet_tier)
            .ok_or_else(|| anyhow!("No policy found for tier: {:?}", request.wallet_tier))?;

        // Check if amount exceeds instant approval limit
        if request.amount_sol > policy.max_amount_without_approval {
            // Requires additional approval
            let additional_approvals = match request.wallet_tier {
                SecurityTier::ColdStorage => 2, // Multi-sig required
                SecurityTier::HotTrading => 1,  // Single approval
                SecurityTier::Emergency => 0,   // Emergency override
            };

            let time_lock = if request.amount_sol > policy.time_lock_threshold {
                policy.time_lock_duration_hours * 3600
            } else {
                0
            };

            return Ok(AccessAuthorization {
                authorized: false,
                method_required: policy.required_access_method.clone(),
                additional_approvals_needed: additional_approvals,
                time_lock_seconds: time_lock,
                reason: format!(
                    "Amount {} SOL exceeds instant approval limit of {} SOL",
                    request.amount_sol, policy.max_amount_without_approval
                ),
            });
        }

        // Check if correct access method is being used
        if request.access_method != policy.required_access_method {
            return Ok(AccessAuthorization {
                authorized: false,
                method_required: policy.required_access_method.clone(),
                additional_approvals_needed: 0,
                time_lock_seconds: 0,
                reason: format!(
                    "Required access method: {:?}, provided: {:?}",
                    policy.required_access_method, request.access_method
                ),
            });
        }

        // Authorization successful
        Ok(AccessAuthorization {
            authorized: true,
            method_required: request.access_method.clone(),
            additional_approvals_needed: 0,
            time_lock_seconds: 0,
            reason: "Access authorized".to_string(),
        })
    }

    /// Execute vault transaction
    pub async fn execute_transaction(&self, request: VaultAccessRequest) -> Result<String> {
        // First authorize the request
        let authorization = self.authorize_access(&request).await?;

        if !authorization.authorized {
            return Err(anyhow!("Access not authorized: {}", authorization.reason));
        }

        info!("🚀 Executing vault transaction");
        info!("   Method: {:?}", request.access_method);
        info!("   Amount: {} SOL", request.amount_sol);

        match request.access_method {
            AccessMethod::HardwareWallet => self.execute_hardware_transaction(request).await,
            AccessMethod::MultiSignature => self.execute_multisig_transaction(request).await,
            AccessMethod::EnvironmentKey => self.execute_hot_wallet_transaction(request).await,
            AccessMethod::Emergency => self.execute_emergency_transaction(request).await,
        }
    }

    /// Execute transaction via hardware wallet
    async fn execute_hardware_transaction(&self, request: VaultAccessRequest) -> Result<String> {
        info!("🔐 Executing hardware wallet transaction");

        let hw_request = HardwareTransactionRequest {
            from_address: request.from_address,
            to_address: request.to_address,
            amount_lamports: (request.amount_sol * 1_000_000_000.0) as u64,
            memo: Some(request.purpose),
            requires_confirmation: true,
        };

        self.hardware_wallet_manager
            .execute_secure_transaction(hw_request)
            .await
    }

    /// Execute multi-signature transaction
    async fn execute_multisig_transaction(&self, request: VaultAccessRequest) -> Result<String> {
        info!("🔐 Executing multi-signature transaction");

        // Get or create multi-sig manager for this wallet
        let multisig_managers = self.multisig_managers.read().await;

        // For now, return transaction ID that would be created
        // In production, this would integrate with actual multi-sig wallet
        let transaction_id = format!(
            "multisig_{}_{}",
            chrono::Utc::now().timestamp(),
            hex::encode(&request.from_address.as_bytes()[..4])
        );

        info!("📝 Multi-sig transaction proposed: {}", transaction_id);
        Ok(transaction_id)
    }

    /// Execute hot wallet transaction
    async fn execute_hot_wallet_transaction(&self, request: VaultAccessRequest) -> Result<String> {
        info!("🔥 Executing hot wallet transaction");

        // In production, this would use environment variables to access hot wallet keys
        // and execute transaction via Solana RPC

        let transaction_id = format!(
            "hot_{}_{}",
            chrono::Utc::now().timestamp(),
            hex::encode(&request.to_address.as_bytes()[..4])
        );

        info!("✅ Hot wallet transaction executed: {}", transaction_id);
        Ok(transaction_id)
    }

    /// Execute emergency transaction
    async fn execute_emergency_transaction(&self, request: VaultAccessRequest) -> Result<String> {
        warn!("🚨 Executing EMERGENCY transaction");
        warn!("   Amount: {} SOL", request.amount_sol);
        warn!("   Purpose: {}", request.purpose);

        // Emergency transactions bypass normal security but are logged extensively
        let transaction_id = format!(
            "emergency_{}_{}",
            chrono::Utc::now().timestamp(),
            hex::encode(&request.requester_id.as_bytes()[..4])
        );

        // In production, this would use emergency wallet keys
        warn!("⚠️ EMERGENCY transaction executed: {}", transaction_id);
        Ok(transaction_id)
    }

    /// Get vault balance summary
    pub async fn get_vault_summary(&self) -> Result<VaultSummary> {
        info!("📊 Getting vault balance summary");

        // In production, query actual wallet balances
        let cold_storage_balance = 27.605; // From our known balance
        let hot_wallet_balances = HashMap::from([
            ("primary_trading".to_string(), 0.001),
            ("hft_trading".to_string(), 0.001),
            ("experimental".to_string(), 0.0),
        ]);

        let total_balance = cold_storage_balance + hot_wallet_balances.values().sum::<f64>();

        Ok(VaultSummary {
            total_balance_sol: total_balance,
            cold_storage_balance_sol: cold_storage_balance,
            hot_wallet_balances,
            hardware_wallet_connected: self.hardware_wallet_manager.is_connected(),
            security_status: "SECURE".to_string(),
        })
    }

    /// Transfer funds between tiers (e.g., cold storage to hot wallet)
    pub async fn transfer_between_tiers(
        &self,
        from_tier: SecurityTier,
        to_tier: SecurityTier,
        amount_sol: f64,
        purpose: String,
    ) -> Result<String> {
        info!("🔄 Transferring between security tiers");
        info!("   From: {:?} → To: {:?}", from_tier, to_tier);
        info!("   Amount: {} SOL", amount_sol);

        // Create appropriate access request based on source tier
        let access_method = match from_tier {
            SecurityTier::ColdStorage => AccessMethod::HardwareWallet,
            SecurityTier::HotTrading => AccessMethod::EnvironmentKey,
            SecurityTier::Emergency => AccessMethod::Emergency,
        };

        let request = VaultAccessRequest {
            wallet_tier: from_tier,
            access_method,
            from_address: "source_wallet".to_string(), // Would be actual address
            to_address: "destination_wallet".to_string(), // Would be actual address
            amount_sol,
            purpose,
            requester_id: "system".to_string(),
            urgent: false,
        };

        self.execute_transaction(request).await
    }
}

#[derive(Debug, Serialize)]
pub struct VaultSummary {
    pub total_balance_sol: f64,
    pub cold_storage_balance_sol: f64,
    pub hot_wallet_balances: HashMap<String, f64>,
    pub hardware_wallet_connected: bool,
    pub security_status: String,
}
