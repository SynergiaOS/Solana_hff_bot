use serde::{Deserialize, Serialize};

/// AI Decision model received from the AI Brain
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIDecision {
    /// Trading symbol (e.g., "SOL/USDC")
    pub symbol: String,

    /// Trading action (e.g., "BUY", "SELL", "HOLD")
    pub action: String,

    /// Quantity to trade
    pub quantity: f64,

    /// Target price (optional)
    pub target_price: Option<f64>,

    /// AI confidence score (0.0-1.0)
    pub confidence: f64,

    /// Reasoning behind the decision
    pub reasoning: String,

    /// Timestamp of the decision
    pub timestamp: String,
}
