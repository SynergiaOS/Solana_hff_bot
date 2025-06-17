// THE OVERMIND PROTOCOL - Library Interface
// Exposes modules for testing and external use

pub mod config;
pub mod modules;
pub mod monitoring;

// Re-export commonly used types for easier access
pub use config::{Config, TradingMode};
pub use modules::{
    ai_connector::AIConnectorConfig,
    data_ingestor::{DataIngestor, MarketData},
    executor::{ExecutionResult, Executor},
    hft_engine::{HFTConfig, OvermindHFTEngine, ExecutionResult as HFTExecutionResult},
    persistence::{PersistenceManager, PersistenceMessage},
    risk::{ApprovedSignal, RiskManager, RiskParameters},
    strategy::{StrategyEngine, TradingSignal, StrategyType, TradeAction},
};
pub use monitoring::{create_monitoring_router, MonitoringState};
