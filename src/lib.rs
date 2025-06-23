//! THE OVERMIND PROTOCOL - Core Library
//!
//! High-frequency trading system for Solana blockchain

pub mod config;
pub mod models;
pub mod modules;

// Re-export commonly used items
pub use config::Config;
pub use modules::ai_connector::AIConnector;
pub use modules::hft_engine::HftEngine;
