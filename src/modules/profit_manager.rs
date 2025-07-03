use anyhow::Result;
use solana_client::rpc_client::RpcClient;
use solana_sdk::{
    commitment_config::CommitmentConfig,
    native_token::LAMPORTS_PER_SOL,
    pubkey::Pubkey,
    signature::{Keypair, Signer},
    system_instruction,
    transaction::Transaction,
};
use std::str::FromStr;
use tracing::{info, warn, error};

/// Profit Manager for THE OVERMIND PROTOCOL
/// Automatically transfers profits to secure wallet
pub struct ProfitManager {
    rpc_client: RpcClient,
    trading_keypair: Keypair,
    profit_wallet: Pubkey,
    transfer_threshold: f64,
    transfer_percentage: f64,
    enabled: bool,
}

impl ProfitManager {
    pub fn new(
        rpc_url: String,
        trading_keypair: Keypair,
        profit_wallet_address: String,
        transfer_threshold: f64,
        transfer_percentage: f64,
        enabled: bool,
    ) -> Result<Self> {
        let profit_wallet = Pubkey::from_str(&profit_wallet_address)?;
        
        Ok(Self {
            rpc_client: RpcClient::new_with_commitment(rpc_url, CommitmentConfig::confirmed()),
            trading_keypair,
            profit_wallet,
            transfer_threshold,
            transfer_percentage,
            enabled,
        })
    }

    /// Check if profit transfer should be executed
    pub async fn check_and_transfer_profits(&self, initial_balance: f64) -> Result<bool> {
        if !self.enabled {
            return Ok(false);
        }

        // Get current balance
        let current_balance = self.get_trading_wallet_balance().await?;
        
        // Calculate profit
        let profit = current_balance - initial_balance;
        
        if profit >= self.transfer_threshold {
            info!("💰 Profit detected: {:.6} SOL (threshold: {:.6})", profit, self.transfer_threshold);
            
            // Calculate transfer amount
            let transfer_amount = profit * (self.transfer_percentage / 100.0);
            
            if transfer_amount > 0.001 { // Minimum transfer to cover fees
                return self.transfer_profit(transfer_amount).await;
            }
        }

        Ok(false)
    }

    /// Transfer profit to secure wallet
    async fn transfer_profit(&self, amount: f64) -> Result<bool> {
        let lamports = (amount * LAMPORTS_PER_SOL as f64) as u64;
        
        info!("🔄 Transferring {:.6} SOL to profit wallet: {}", amount, self.profit_wallet);

        // Create transfer instruction
        let instruction = system_instruction::transfer(
            &self.trading_keypair.pubkey(),
            &self.profit_wallet,
            lamports,
        );

        // Get recent blockhash
        let recent_blockhash = self.rpc_client.get_latest_blockhash()?;

        // Create transaction
        let transaction = Transaction::new_signed_with_payer(
            &[instruction],
            Some(&self.trading_keypair.pubkey()),
            &[&self.trading_keypair],
            recent_blockhash,
        );

        // Send transaction
        match self.rpc_client.send_and_confirm_transaction(&transaction) {
            Ok(signature) => {
                info!("✅ Profit transfer successful: {}", signature);
                info!("💰 Transferred {:.6} SOL to profit wallet", amount);
                Ok(true)
            }
            Err(e) => {
                error!("❌ Profit transfer failed: {}", e);
                Ok(false)
            }
        }
    }

    /// Get trading wallet balance
    async fn get_trading_wallet_balance(&self) -> Result<f64> {
        let balance = self.rpc_client.get_balance(&self.trading_keypair.pubkey())?;
        Ok(balance as f64 / LAMPORTS_PER_SOL as f64)
    }

    /// Get profit wallet balance
    pub async fn get_profit_wallet_balance(&self) -> Result<f64> {
        let balance = self.rpc_client.get_balance(&self.profit_wallet)?;
        Ok(balance as f64 / LAMPORTS_PER_SOL as f64)
    }

    /// Get profit statistics
    pub async fn get_profit_stats(&self, initial_balance: f64) -> Result<ProfitStats> {
        let trading_balance = self.get_trading_wallet_balance().await?;
        let profit_balance = self.get_profit_wallet_balance().await?;
        
        Ok(ProfitStats {
            initial_trading_balance: initial_balance,
            current_trading_balance: trading_balance,
            profit_wallet_balance: profit_balance,
            total_profit: (trading_balance - initial_balance) + (profit_balance - 27.6), // Assuming 27.6 was initial
            profit_percentage: ((trading_balance - initial_balance) / initial_balance) * 100.0,
        })
    }
}

#[derive(Debug)]
pub struct ProfitStats {
    pub initial_trading_balance: f64,
    pub current_trading_balance: f64,
    pub profit_wallet_balance: f64,
    pub total_profit: f64,
    pub profit_percentage: f64,
}

impl ProfitStats {
    pub fn display(&self) {
        info!("📊 PROFIT STATISTICS:");
        info!("   Trading Wallet: {:.6} SOL (started: {:.6})", 
              self.current_trading_balance, self.initial_trading_balance);
        info!("   Profit Wallet: {:.6} SOL", self.profit_wallet_balance);
        info!("   Total Profit: {:.6} SOL ({:.2}%)", 
              self.total_profit, self.profit_percentage);
    }
}
