// Module declarations for SNIPERCOR
// Each module handles a specific aspect of the HFT trading system

pub mod data_ingestor;
pub mod strategy;
pub mod risk;
pub mod executor;
pub mod persistence;

// Re-export main types for easier access
pub use data_ingestor::DataIngestor;
pub use strategy::StrategyEngine;
pub use risk::RiskManager;
pub use executor::Executor;
pub use persistence::PersistenceManager;
