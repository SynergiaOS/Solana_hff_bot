//! THE OVERMIND PROTOCOL - Core Library
//!
//! High-frequency trading system for Solana blockchain

#![allow(clippy::all)]
#![allow(unused_parens)]
#![allow(unused_mut)]
#![allow(private_interfaces)]
#![allow(dead_code)]
#![allow(unused_variables)]

pub mod config;
pub mod models;
pub mod modules;

// Re-export commonly used items
pub use config::Config;
pub use modules::ai_connector::AIConnector;
pub use modules::hft_engine::HftEngine;
pub use modules::vault_integration::{VaultClient, VaultMultiWalletManager, WalletSecret};
