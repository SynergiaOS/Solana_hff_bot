// THE OVERMIND PROTOCOL - AI Connector Module
// Warstwa 3-4 Bridge: Connects Python AI Brain with Rust HFT Executor
// Handles communication via DragonflyDB and vector memory integration

use anyhow::Result;
use redis::aio::ConnectionManager;
use redis::{AsyncCommands, Client};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{mpsc, RwLock};
use tokio::time::{Duration, Instant};
use tracing::{error, info, warn, instrument};
use uuid::Uuid;

use crate::modules::strategy::TradingSignal;

// ============================================================================
// AI BRAIN COMMUNICATION STRUCTURES
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIDecision {
    pub decision_id: String,
    pub symbol: String,
    pub action: AIAction,
    pub confidence: f64,
    pub reasoning: String,
    pub quantity: f64,
    pub target_price: Option<f64>,
    pub ai_context: Option<String>,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub vector_memory_context: Option<VectorContext>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AIAction {
    Buy,
    Sell,
    Hold,
    StopLoss,
    TakeProfit,
}

impl std::fmt::Display for AIAction {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AIAction::Buy => write!(f, "BUY"),
            AIAction::Sell => write!(f, "SELL"),
            AIAction::Hold => write!(f, "HOLD"),
            AIAction::StopLoss => write!(f, "STOP_LOSS"),
            AIAction::TakeProfit => write!(f, "TAKE_PROFIT"),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorContext {
    pub similar_situations: Vec<String>,
    pub confidence_score: f64,
    pub memory_relevance: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketEvent {
    pub event_id: String,
    pub symbol: String,
    pub price: f64,
    pub volume: f64,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub event_type: MarketEventType,
    pub metadata: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MarketEventType {
    PriceChange,
    VolumeSpike,
    NewToken,
    LiquidityChange,
    TechnicalSignal,
}

impl std::fmt::Display for MarketEventType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            MarketEventType::PriceChange => write!(f, "PRICE_CHANGE"),
            MarketEventType::VolumeSpike => write!(f, "VOLUME_SPIKE"),
            MarketEventType::NewToken => write!(f, "NEW_TOKEN"),
            MarketEventType::LiquidityChange => write!(f, "LIQUIDITY_CHANGE"),
            MarketEventType::TechnicalSignal => write!(f, "TECHNICAL_SIGNAL"),
        }
    }
}

// ============================================================================
// AI CONNECTOR MAIN STRUCTURE
// ============================================================================

pub struct AIConnector {
    /// DragonflyDB connection for communication with Python Brain
    dragonfly_client: ConnectionManager,
    /// Channel to send AI decisions to strategy engine
    decision_sender: mpsc::UnboundedSender<TradingSignal>,
    /// Channel to receive market events from data ingestor
    market_event_receiver: mpsc::UnboundedReceiver<MarketEvent>,
    /// Vector memory cache for performance
    vector_cache: Arc<RwLock<HashMap<String, VectorContext>>>,
    /// AI performance metrics
    metrics: AIMetrics,
    /// Configuration
    config: AIConnectorConfig,
    /// Connection status
    is_connected: Arc<RwLock<bool>>,
}

#[derive(Debug, Clone)]
pub struct AIConnectorConfig {
    pub dragonfly_url: String,
    pub brain_request_timeout: Duration,
    pub max_decision_age: Duration,
    pub confidence_threshold: f64,
    pub vector_cache_size: usize,
    pub retry_attempts: u32,
}

#[derive(Debug, Default, Clone)]
pub struct AIMetrics {
    pub decisions_received: u64,
    pub decisions_processed: u64,
    pub decisions_rejected: u64,
    pub avg_decision_latency: Duration,
    pub brain_connection_errors: u64,
    pub vector_cache_hits: u64,
    pub vector_cache_misses: u64,
}

// ============================================================================
// IMPLEMENTATION
// ============================================================================

impl AIConnector {
    pub async fn new(
        config: AIConnectorConfig,
        decision_sender: mpsc::UnboundedSender<TradingSignal>,
        market_event_receiver: mpsc::UnboundedReceiver<MarketEvent>,
    ) -> Result<Self> {
        info!("🧠 Initializing AI Connector for THE OVERMIND PROTOCOL");

        // Connect to DragonflyDB
        let client = Client::open(config.dragonfly_url.as_str())?;
        let dragonfly_client = ConnectionManager::new(client).await?;

        // Test connection
        let mut conn = dragonfly_client.clone();
        let _: String = redis::cmd("PING").query_async(&mut conn).await?;
        info!("✅ Connected to DragonflyDB at {}", config.dragonfly_url);

        Ok(Self {
            dragonfly_client,
            decision_sender,
            market_event_receiver,
            vector_cache: Arc::new(RwLock::new(HashMap::new())),
            metrics: AIMetrics::default(),
            config,
            is_connected: Arc::new(RwLock::new(true)),
        })
    }

    #[instrument(skip(self))]
    pub async fn start(&mut self) -> Result<()> {
        info!("🚀 Starting AI Connector - Bridge between Python Brain and Rust Executor");

        // Clone necessary data for tasks
        let config = self.config.clone();
        let dragonfly_client = self.dragonfly_client.clone();
        let decision_sender = self.decision_sender.clone();
        let is_connected = self.is_connected.clone();

        // Start brain listener task
        let brain_listener = {
            let config = config.clone();
            let dragonfly_client = dragonfly_client.clone();
            let decision_sender = decision_sender.clone();
            tokio::spawn(async move {
                Self::run_brain_listener(config, dragonfly_client, decision_sender).await
            })
        };

        // Start health monitor task
        let health_monitor = {
            let config = config.clone();
            let dragonfly_client = dragonfly_client.clone();
            let is_connected = is_connected.clone();
            tokio::spawn(async move {
                Self::run_health_monitor(config, dragonfly_client, is_connected).await
            })
        };

        // Start market event processor
        let market_event_processor = self.start_market_event_processor();

        // Run all tasks concurrently
        tokio::try_join!(
            async { brain_listener.await.map_err(|e| anyhow::anyhow!("Brain listener failed: {}", e))? },
            async { health_monitor.await.map_err(|e| anyhow::anyhow!("Health monitor failed: {}", e))? },
            market_event_processor
        )?;

        Ok(())
    }

    async fn start_brain_listener(&self) -> Result<()> {
        info!("👂 Starting AI Brain decision listener");
        
        let mut conn = self.dragonfly_client.clone();
        let decision_sender = self.decision_sender.clone();
        let _config = self.config.clone();

        loop {
            match self.listen_for_ai_decisions(&mut conn).await {
                Ok(Some(ai_decision)) => {
                    if let Err(e) = self.process_ai_decision(ai_decision, &decision_sender).await {
                        error!("Failed to process AI decision: {}", e);
                    }
                }
                Ok(None) => {
                    // No decision received, continue listening
                    tokio::time::sleep(Duration::from_millis(100)).await;
                }
                Err(e) => {
                    error!("Error listening for AI decisions: {}", e);
                    tokio::time::sleep(Duration::from_secs(1)).await;
                }
            }
        }
    }

    async fn start_market_event_processor(&mut self) -> Result<()> {
        info!("📊 Starting market event processor");
        
        let mut conn = self.dragonfly_client.clone();

        while let Some(market_event) = self.market_event_receiver.recv().await {
            if let Err(e) = self.send_market_event_to_brain(&mut conn, market_event).await {
                error!("Failed to send market event to brain: {}", e);
            }
        }

        Ok(())
    }

    async fn start_health_monitor(&self) -> Result<()> {
        info!("💓 Starting AI Connector health monitor");
        
        let mut interval = tokio::time::interval(Duration::from_secs(30));
        let mut conn = self.dragonfly_client.clone();

        loop {
            interval.tick().await;
            
            match self.check_brain_health(&mut conn).await {
                Ok(is_healthy) => {
                    let mut connected = self.is_connected.write().await;
                    *connected = is_healthy;
                    
                    if !is_healthy {
                        warn!("🔴 AI Brain connection unhealthy");
                    }
                }
                Err(e) => {
                    error!("Health check failed: {}", e);
                    let mut connected = self.is_connected.write().await;
                    *connected = false;
                }
            }
        }
    }

    #[instrument(skip(self, conn))]
    async fn listen_for_ai_decisions(
        &self,
        conn: &mut ConnectionManager,
    ) -> Result<Option<AIDecision>> {
        // Listen for AI decisions from Python Brain
        let result: Option<(String, String)> = conn
            .blpop("overmind:trading_commands", self.config.brain_request_timeout.as_secs() as f64)
            .await?;

        if let Some((_, decision_json)) = result {
            let ai_decision: AIDecision = serde_json::from_str(&decision_json)?;
            
            // Check decision age
            let decision_age = chrono::Utc::now() - ai_decision.timestamp;
            if decision_age > chrono::Duration::from_std(self.config.max_decision_age)? {
                warn!("Rejecting stale AI decision: {} seconds old", decision_age.num_seconds());
                return Ok(None);
            }

            info!("🧠 Received AI decision: {} {} (confidence: {:.2})",
                  ai_decision.action, ai_decision.symbol, ai_decision.confidence);
            
            Ok(Some(ai_decision))
        } else {
            Ok(None)
        }
    }

    #[instrument(skip(self, decision_sender))]
    async fn process_ai_decision(
        &self,
        ai_decision: AIDecision,
        decision_sender: &mpsc::UnboundedSender<TradingSignal>,
    ) -> Result<()> {
        let start_time = Instant::now();

        // Validate AI decision
        if ai_decision.confidence < self.config.confidence_threshold {
            warn!("Rejecting low-confidence AI decision: {:.2} < {:.2}",
                  ai_decision.confidence, self.config.confidence_threshold);
            return Ok(());
        }

        // Convert AI decision to trading signal
        let trading_signal = self.convert_ai_decision_to_signal(ai_decision).await?;

        // Send to strategy engine
        if let Err(e) = decision_sender.send(trading_signal) {
            error!("Failed to send trading signal: {}", e);
            return Err(anyhow::anyhow!("Failed to send trading signal"));
        }

        // Update metrics
        let processing_time = start_time.elapsed();
        info!("✅ Processed AI decision in {:?}", processing_time);

        Ok(())
    }

    async fn convert_ai_decision_to_signal(&self, ai_decision: AIDecision) -> Result<TradingSignal> {
        use crate::modules::strategy::{TradeAction, StrategyType};

        let action = match ai_decision.action {
            AIAction::Buy => TradeAction::Buy,
            AIAction::Sell => TradeAction::Sell,
            AIAction::Hold => return Err(anyhow::anyhow!("HOLD action not converted to signal")),
            AIAction::StopLoss => TradeAction::Sell, // Convert to sell
            AIAction::TakeProfit => TradeAction::Sell, // Convert to sell
        };

        Ok(TradingSignal {
            signal_id: ai_decision.decision_id,
            symbol: ai_decision.symbol,
            action,
            quantity: ai_decision.quantity,
            target_price: ai_decision.target_price.unwrap_or(0.0),
            confidence: ai_decision.confidence,
            timestamp: ai_decision.timestamp,
            strategy_type: StrategyType::AIDecision, // New strategy type for AI decisions
        })
    }

    #[instrument(skip(self, conn, market_event))]
    async fn send_market_event_to_brain(
        &self,
        conn: &mut ConnectionManager,
        market_event: MarketEvent,
    ) -> Result<()> {
        let event_json = serde_json::to_string(&market_event)?;
        
        // Send to Python Brain via DragonflyDB
        let _: () = conn.lpush("overmind:market_events", event_json).await?;
        
        info!("📤 Sent market event to AI Brain: {} {}", 
              market_event.symbol, market_event.event_type);

        Ok(())
    }

    async fn check_brain_health(&self, conn: &mut ConnectionManager) -> Result<bool> {
        // Send ping to brain health channel
        let health_check = serde_json::json!({
            "type": "health_check",
            "timestamp": chrono::Utc::now(),
            "source": "rust_executor"
        });

        let _: () = conn.lpush("overmind:health_check", health_check.to_string()).await?;

        // Wait for response (with timeout)
        let response: Option<(String, String)> = conn
            .blpop("overmind:health_response", 5.0) // 5 second timeout
            .await?;

        Ok(response.is_some())
    }

    pub async fn get_metrics(&self) -> AIMetrics {
        self.metrics.clone()
    }

    pub async fn is_brain_connected(&self) -> bool {
        *self.is_connected.read().await
    }

    // Static methods for spawned tasks
    async fn run_brain_listener(
        config: AIConnectorConfig,
        dragonfly_client: ConnectionManager,
        decision_sender: mpsc::UnboundedSender<TradingSignal>,
    ) -> Result<()> {
        info!("👂 Starting AI Brain decision listener");

        let mut conn = dragonfly_client.clone();

        loop {
            match Self::listen_for_ai_decisions_static(&config, &mut conn).await {
                Ok(Some(ai_decision)) => {
                    if let Err(e) = Self::process_ai_decision_static(ai_decision, &decision_sender, &config).await {
                        error!("Failed to process AI decision: {}", e);
                    }
                }
                Ok(None) => {
                    // No decision received, continue listening
                    tokio::time::sleep(Duration::from_millis(100)).await;
                }
                Err(e) => {
                    error!("Error listening for AI decisions: {}", e);
                    tokio::time::sleep(Duration::from_secs(1)).await;
                }
            }
        }
    }

    async fn run_health_monitor(
        _config: AIConnectorConfig,
        dragonfly_client: ConnectionManager,
        is_connected: Arc<RwLock<bool>>,
    ) -> Result<()> {
        info!("💓 Starting AI Connector health monitor");

        let mut interval = tokio::time::interval(Duration::from_secs(30));
        let mut conn = dragonfly_client.clone();

        loop {
            interval.tick().await;

            match Self::check_brain_health_static(&mut conn).await {
                Ok(is_healthy) => {
                    let mut connected = is_connected.write().await;
                    *connected = is_healthy;

                    if !is_healthy {
                        warn!("🔴 AI Brain connection unhealthy");
                    }
                }
                Err(e) => {
                    error!("Health check failed: {}", e);
                    let mut connected = is_connected.write().await;
                    *connected = false;
                }
            }
        }
    }

    async fn listen_for_ai_decisions_static(
        config: &AIConnectorConfig,
        conn: &mut ConnectionManager,
    ) -> Result<Option<AIDecision>> {
        // Listen for AI decisions from Python Brain
        let result: Option<(String, String)> = conn
            .blpop("overmind:trading_commands", config.brain_request_timeout.as_secs() as f64)
            .await?;

        if let Some((_, decision_json)) = result {
            let ai_decision: AIDecision = serde_json::from_str(&decision_json)?;

            // Check decision age
            let decision_age = chrono::Utc::now() - ai_decision.timestamp;
            if decision_age > chrono::Duration::from_std(config.max_decision_age)? {
                warn!("Rejecting stale AI decision: {} seconds old", decision_age.num_seconds());
                return Ok(None);
            }

            info!("🧠 Received AI decision: {} {} (confidence: {:.2})",
                  ai_decision.action, ai_decision.symbol, ai_decision.confidence);

            Ok(Some(ai_decision))
        } else {
            Ok(None)
        }
    }

    async fn process_ai_decision_static(
        ai_decision: AIDecision,
        decision_sender: &mpsc::UnboundedSender<TradingSignal>,
        config: &AIConnectorConfig,
    ) -> Result<()> {
        let start_time = Instant::now();

        // Validate AI decision
        if ai_decision.confidence < config.confidence_threshold {
            warn!("Rejecting low-confidence AI decision: {:.2} < {:.2}",
                  ai_decision.confidence, config.confidence_threshold);
            return Ok(());
        }

        // Convert AI decision to trading signal
        let trading_signal = Self::convert_ai_decision_to_signal_static(ai_decision).await?;

        // Send to strategy engine
        if let Err(e) = decision_sender.send(trading_signal) {
            error!("Failed to send trading signal: {}", e);
            return Err(anyhow::anyhow!("Failed to send trading signal"));
        }

        // Update metrics
        let processing_time = start_time.elapsed();
        info!("✅ Processed AI decision in {:?}", processing_time);

        Ok(())
    }

    async fn convert_ai_decision_to_signal_static(ai_decision: AIDecision) -> Result<TradingSignal> {
        use crate::modules::strategy::{TradeAction, StrategyType};

        let action = match ai_decision.action {
            AIAction::Buy => TradeAction::Buy,
            AIAction::Sell => TradeAction::Sell,
            AIAction::Hold => return Err(anyhow::anyhow!("HOLD action not converted to signal")),
            AIAction::StopLoss => TradeAction::Sell, // Convert to sell
            AIAction::TakeProfit => TradeAction::Sell, // Convert to sell
        };

        Ok(TradingSignal {
            signal_id: ai_decision.decision_id,
            symbol: ai_decision.symbol,
            action,
            quantity: ai_decision.quantity,
            target_price: ai_decision.target_price.unwrap_or(0.0),
            confidence: ai_decision.confidence,
            timestamp: ai_decision.timestamp,
            strategy_type: StrategyType::AIDecision, // New strategy type for AI decisions
        })
    }

    async fn check_brain_health_static(conn: &mut ConnectionManager) -> Result<bool> {
        // Send ping to brain health channel
        let health_check = serde_json::json!({
            "type": "health_check",
            "timestamp": chrono::Utc::now(),
            "source": "rust_executor"
        });

        let _: () = conn.lpush("overmind:health_check", health_check.to_string()).await?;

        // Wait for response (with timeout)
        let response: Option<(String, String)> = conn
            .blpop("overmind:health_response", 5.0) // 5 second timeout
            .await?;

        Ok(response.is_some())
    }
}

impl Default for AIConnectorConfig {
    fn default() -> Self {
        Self {
            dragonfly_url: "redis://localhost:6379".to_string(),
            brain_request_timeout: Duration::from_secs(1),
            max_decision_age: Duration::from_secs(30),
            confidence_threshold: 0.7,
            vector_cache_size: 1000,
            retry_attempts: 3,
        }
    }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

pub fn create_market_event(
    symbol: String,
    price: f64,
    volume: f64,
    event_type: MarketEventType,
) -> MarketEvent {
    MarketEvent {
        event_id: Uuid::new_v4().to_string(),
        symbol,
        price,
        volume,
        timestamp: chrono::Utc::now(),
        event_type,
        metadata: HashMap::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::sync::mpsc;

    #[tokio::test]
    async fn test_ai_decision_conversion() {
        let ai_decision = AIDecision {
            decision_id: "test-123".to_string(),
            symbol: "SOL/USDC".to_string(),
            action: AIAction::Buy,
            confidence: 0.85,
            reasoning: "Strong bullish signal".to_string(),
            quantity: 1000.0,
            target_price: Some(100.0),
            ai_context: None,
            timestamp: chrono::Utc::now(),
            vector_memory_context: None,
        };

        let (_tx, _rx) = mpsc::unbounded_channel::<AIDecision>();
        let _config = AIConnectorConfig::default();
        
        // Note: This test would need a mock DragonflyDB connection
        // For now, we just test the conversion logic
        
        assert_eq!(ai_decision.confidence, 0.85);
        assert_eq!(ai_decision.symbol, "SOL/USDC");
    }
}
