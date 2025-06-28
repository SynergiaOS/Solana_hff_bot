// Module declarations for THE OVERMIND PROTOCOL
// Each module handles a specific aspect of the AI-enhanced HFT trading system

pub mod data_ingestor;
pub mod executor;
pub mod persistence;
pub mod risk;
pub mod strategy;
// THE OVERMIND PROTOCOL - Core Components
pub mod ai_connector;
pub mod dex_integration;
pub mod error_handling;
pub mod hft_engine;
pub mod jito_client;
pub mod metrics;
pub mod real_price_fetcher;
pub mod tensorzero_client;
// THE OVERMIND PROTOCOL - Multi-Wallet Support
pub mod multi_wallet_config;
pub mod multi_wallet_executor;
pub mod wallet_manager;

// Advanced strategy modules based on Solana knowledge
pub mod dev_tracker;
pub mod meteora_damm;
pub mod soul_meteor;
// NEW ADVANCED STRATEGIES
pub mod cross_dex_arbitrage;
pub mod liquidity_sniping;
pub mod mev_arbitrage;

// PERFORMANCE OPTIMIZATION MODULES
pub mod memory_optimizer;
pub mod performance_optimizer;
pub mod realtime_monitor;

// ADVANCED RISK MANAGEMENT MODULES
pub mod advanced_risk_management;
pub mod dynamic_position_sizing;
pub mod portfolio_rebalancer;

// MULTI-WALLET & HIGH-FREQUENCY OPTIMIZATION MODULES
pub mod geographic_distribution;
pub mod multi_wallet_load_balancer;
pub mod submillisecond_optimizer;

// Re-export main types for easier access
// Note: Exports commented out to avoid unused import warnings in skeleton
// pub use data_ingestor::DataIngestor;
// pub use executor::Executor;
// pub use persistence::PersistenceManager;
// pub use risk::RiskManager;
// pub use strategy::StrategyEngine;
