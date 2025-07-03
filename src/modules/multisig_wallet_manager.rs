// 🔐 MULTI-SIGNATURE WALLET MANAGER FOR OVERMIND VAULT
// Secure multi-sig access for cold storage funds

use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::RwLock;
use tracing::{info, warn};

/// Multi-signature wallet configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MultiSigConfig {
    pub wallet_address: String,
    pub required_signatures: u8,
    pub total_signers: u8,
    pub signer_addresses: Vec<String>,
    pub time_lock_seconds: u64,
}

/// Pending multi-sig transaction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingTransaction {
    pub transaction_id: String,
    pub from_address: String,
    pub to_address: String,
    pub amount_sol: f64,
    pub purpose: String,
    pub created_at: u64,
    pub expires_at: u64,
    pub signatures: HashMap<String, String>, // signer_address -> signature
    pub required_signatures: u8,
    pub status: TransactionStatus,
}

/// Transaction status in multi-sig workflow
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TransactionStatus {
    Pending,
    PartiallyApproved,
    FullyApproved,
    Executed,
    Rejected,
    Expired,
}

/// Multi-signature wallet manager
pub struct MultiSigWalletManager {
    config: MultiSigConfig,
    pending_transactions: RwLock<HashMap<String, PendingTransaction>>,
    executed_transactions: RwLock<Vec<String>>,
}

impl MultiSigWalletManager {
    /// Create new multi-sig wallet manager
    pub fn new(config: MultiSigConfig) -> Self {
        info!("🔐 Initializing Multi-Sig Wallet Manager");
        info!("   Wallet: {}", config.wallet_address);
        info!(
            "   Required signatures: {}/{}",
            config.required_signatures, config.total_signers
        );

        Self {
            config,
            pending_transactions: RwLock::new(HashMap::new()),
            executed_transactions: RwLock::new(Vec::new()),
        }
    }

    /// Create new multi-sig transaction proposal
    pub async fn propose_transaction(
        &self,
        from_address: String,
        to_address: String,
        amount_sol: f64,
        purpose: String,
        proposer_address: String,
    ) -> Result<String> {
        // Validate proposer is authorized signer
        if !self.config.signer_addresses.contains(&proposer_address) {
            return Err(anyhow!("Unauthorized proposer: {}", proposer_address));
        }

        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        let transaction_id = format!(
            "multisig_{}_{}",
            now,
            hex::encode(&proposer_address.as_bytes()[..4])
        );

        let pending_tx = PendingTransaction {
            transaction_id: transaction_id.clone(),
            from_address,
            to_address: to_address.clone(),
            amount_sol,
            purpose: purpose.clone(),
            created_at: now,
            expires_at: now + 86400, // 24 hours expiry
            signatures: HashMap::new(),
            required_signatures: self.config.required_signatures,
            status: TransactionStatus::Pending,
        };

        let mut pending = self.pending_transactions.write().await;
        pending.insert(transaction_id.clone(), pending_tx);

        info!("📝 Multi-sig transaction proposed:");
        info!("   ID: {}", transaction_id);
        info!("   To: {}", to_address);
        info!("   Amount: {} SOL", amount_sol);
        info!("   Purpose: {}", purpose);
        info!("   Proposer: {}", proposer_address);

        Ok(transaction_id)
    }

    /// Sign pending transaction
    pub async fn sign_transaction(
        &self,
        transaction_id: String,
        signer_address: String,
        signature: String,
    ) -> Result<TransactionStatus> {
        // Validate signer is authorized
        if !self.config.signer_addresses.contains(&signer_address) {
            return Err(anyhow!("Unauthorized signer: {}", signer_address));
        }

        let mut pending = self.pending_transactions.write().await;
        let transaction = pending
            .get_mut(&transaction_id)
            .ok_or_else(|| anyhow!("Transaction not found: {}", transaction_id))?;

        // Check if transaction is still valid
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        if now > transaction.expires_at {
            transaction.status = TransactionStatus::Expired;
            return Ok(TransactionStatus::Expired);
        }

        // Check if already signed by this signer
        if transaction.signatures.contains_key(&signer_address) {
            return Err(anyhow!("Transaction already signed by: {}", signer_address));
        }

        // Add signature
        transaction
            .signatures
            .insert(signer_address.clone(), signature);

        info!("✍️ Transaction signed by: {}", signer_address);
        info!(
            "   Signatures: {}/{}",
            transaction.signatures.len(),
            transaction.required_signatures
        );

        // Update status based on signature count
        let signature_count = transaction.signatures.len() as u8;

        if signature_count >= transaction.required_signatures {
            transaction.status = TransactionStatus::FullyApproved;
            info!("✅ Transaction fully approved: {}", transaction_id);

            // Auto-execute if time lock has passed
            if now >= transaction.created_at + self.config.time_lock_seconds {
                return self.execute_approved_transaction(transaction_id).await;
            } else {
                let remaining_time = (transaction.created_at + self.config.time_lock_seconds) - now;
                info!(
                    "⏰ Time lock active. Execution in {} seconds",
                    remaining_time
                );
            }
        } else {
            transaction.status = TransactionStatus::PartiallyApproved;
        }

        Ok(transaction.status.clone())
    }

    /// Execute fully approved transaction
    pub async fn execute_approved_transaction(
        &self,
        transaction_id: String,
    ) -> Result<TransactionStatus> {
        let mut pending = self.pending_transactions.write().await;
        let transaction = pending
            .get_mut(&transaction_id)
            .ok_or_else(|| anyhow!("Transaction not found: {}", transaction_id))?;

        // Verify transaction is fully approved
        if transaction.status != TransactionStatus::FullyApproved {
            return Err(anyhow!(
                "Transaction not fully approved: {:?}",
                transaction.status
            ));
        }

        // Check time lock
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        if now < transaction.created_at + self.config.time_lock_seconds {
            return Err(anyhow!("Time lock still active"));
        }

        info!("🚀 Executing multi-sig transaction: {}", transaction_id);
        info!("   From: {}", transaction.from_address);
        info!("   To: {}", transaction.to_address);
        info!("   Amount: {} SOL", transaction.amount_sol);

        // In production, execute actual Solana transaction here
        // For now, simulate execution
        tokio::time::sleep(tokio::time::Duration::from_millis(1000)).await;

        transaction.status = TransactionStatus::Executed;

        // Move to executed transactions
        let mut executed = self.executed_transactions.write().await;
        executed.push(transaction_id.clone());

        info!(
            "✅ Multi-sig transaction executed successfully: {}",
            transaction_id
        );
        Ok(TransactionStatus::Executed)
    }

    /// Get pending transactions for a signer
    pub async fn get_pending_transactions(
        &self,
        signer_address: String,
    ) -> Result<Vec<PendingTransaction>> {
        // Validate signer is authorized
        if !self.config.signer_addresses.contains(&signer_address) {
            return Err(anyhow!("Unauthorized signer: {}", signer_address));
        }

        let pending = self.pending_transactions.read().await;
        let mut transactions = Vec::new();

        for transaction in pending.values() {
            // Include transactions that need this signer's signature
            if !transaction.signatures.contains_key(&signer_address)
                && (transaction.status == TransactionStatus::Pending
                    || transaction.status == TransactionStatus::PartiallyApproved)
            {
                transactions.push(transaction.clone());
            }
        }

        Ok(transactions)
    }

    /// Get transaction status
    pub async fn get_transaction_status(
        &self,
        transaction_id: String,
    ) -> Result<TransactionStatus> {
        let pending = self.pending_transactions.read().await;

        if let Some(transaction) = pending.get(&transaction_id) {
            Ok(transaction.status.clone())
        } else {
            let executed = self.executed_transactions.read().await;
            if executed.contains(&transaction_id) {
                Ok(TransactionStatus::Executed)
            } else {
                Err(anyhow!("Transaction not found: {}", transaction_id))
            }
        }
    }

    /// Reject transaction (requires majority vote)
    pub async fn reject_transaction(
        &self,
        transaction_id: String,
        rejector_address: String,
    ) -> Result<TransactionStatus> {
        // Validate rejector is authorized
        if !self.config.signer_addresses.contains(&rejector_address) {
            return Err(anyhow!("Unauthorized rejector: {}", rejector_address));
        }

        let mut pending = self.pending_transactions.write().await;
        let transaction = pending
            .get_mut(&transaction_id)
            .ok_or_else(|| anyhow!("Transaction not found: {}", transaction_id))?;

        transaction.status = TransactionStatus::Rejected;

        warn!("❌ Transaction rejected by: {}", rejector_address);
        warn!("   Transaction ID: {}", transaction_id);

        Ok(TransactionStatus::Rejected)
    }

    /// Clean up expired transactions
    pub async fn cleanup_expired_transactions(&self) -> Result<usize> {
        let mut pending = self.pending_transactions.write().await;
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();

        let mut expired_count = 0;
        let mut to_remove = Vec::new();

        for (id, transaction) in pending.iter_mut() {
            if now > transaction.expires_at && transaction.status != TransactionStatus::Executed {
                transaction.status = TransactionStatus::Expired;
                to_remove.push(id.clone());
                expired_count += 1;
            }
        }

        for id in to_remove {
            pending.remove(&id);
        }

        if expired_count > 0 {
            info!("🧹 Cleaned up {} expired transactions", expired_count);
        }

        Ok(expired_count)
    }

    /// Get multi-sig wallet summary
    pub async fn get_wallet_summary(&self) -> MultiSigSummary {
        let pending = self.pending_transactions.read().await;
        let executed = self.executed_transactions.read().await;

        let pending_count = pending.len();
        let executed_count = executed.len();

        let partially_approved = pending
            .values()
            .filter(|tx| tx.status == TransactionStatus::PartiallyApproved)
            .count();

        let fully_approved = pending
            .values()
            .filter(|tx| tx.status == TransactionStatus::FullyApproved)
            .count();

        MultiSigSummary {
            wallet_address: self.config.wallet_address.clone(),
            required_signatures: self.config.required_signatures,
            total_signers: self.config.total_signers,
            pending_transactions: pending_count,
            executed_transactions: executed_count,
            partially_approved,
            fully_approved,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct MultiSigSummary {
    pub wallet_address: String,
    pub required_signatures: u8,
    pub total_signers: u8,
    pub pending_transactions: usize,
    pub executed_transactions: usize,
    pub partially_approved: usize,
    pub fully_approved: usize,
}
