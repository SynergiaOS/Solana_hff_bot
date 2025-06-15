// Module declarations for SNIPERCOR
// Each module handles a specific aspect of the HFT trading system

pub mod data_ingestor;
pub mod executor;
pub mod persistence;
pub mod risk;
pub mod strategy;

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
