// Module declarations for THE OVERMIND PROTOCOL
// Each module handles a specific aspect of the AI-enhanced HFT trading system

pub mod data_ingestor;
pub mod executor;
pub mod persistence;
pub mod risk;
pub mod strategy;
// THE OVERMIND PROTOCOL - Core Components
pub mod hft_engine;
pub mod ai_connector;
// THE OVERMIND PROTOCOL - Multi-Wallet Support
pub mod wallet_manager;
pub mod multi_wallet_config;
pub mod multi_wallet_executor;

// Advanced strategy modules based on Solana knowledge
pub mod dev_tracker;
pub mod meteora_damm;
pub mod soul_meteor;

// Re-export main types for easier access
// Note: Exports commented out to avoid unused import warnings in skeleton
// pub use data_ingestor::DataIngestor;
// pub use executor::Executor;
// pub use persistence::PersistenceManager;
// pub use risk::RiskManager;
// pub use strategy::StrategyEngine;
