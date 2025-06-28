//! Market data models
//!
//! Contains structures for representing market data and events.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Market event types
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum MarketEventType {
    /// Price update event
    PriceUpdate,
    /// New trade event
    Trade,
    /// Liquidity change event
    LiquidityChange,
    /// Order book update
    OrderBookUpdate,
    /// Custom event
    Custom(String),
}

/// Market event data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketEvent {
    /// Unique event ID
    pub event_id: String,

    /// Trading symbol (e.g., "SOL/USDC")
    pub symbol: String,

    /// Current price
    pub price: f64,

    /// Trading volume
    pub volume: f64,

    /// Event timestamp (ISO 8601)
    pub timestamp: String,

    /// Event type
    pub event_type: MarketEventType,

    /// Additional metadata
    pub metadata: HashMap<String, serde_json::Value>,
}
