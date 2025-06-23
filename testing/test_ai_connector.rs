use anyhow::Result;
use redis::Client;
use serde_json::json;
use tokio::sync::mpsc;

use crate::modules::ai_connector::{AIConnector, AIConnectorConfig};
use crate::modules::strategy::TradingSignal;

#[tokio::test]
async fn test_ai_connector_communication() -> Result<()> {
    // Setup DragonflyDB client for test
    let client = Client::open("redis://localhost:6379")?;
    let mut conn = client.get_async_connection().await?;
    
    // Create channels
    let (tx, _rx) = mpsc::unbounded_channel::<TradingSignal>();
    let (market_tx, market_rx) = mpsc::unbounded_channel();
    
    // Create AI connector
    let config = AIConnectorConfig {
        dragonfly_url: "redis://localhost:6379".to_string(),
        brain_request_timeout: std::time::Duration::from_secs(1),
        max_decision_age: std::time::Duration::from_secs(30),
        confidence_threshold: 0.5,
        vector_cache_size: 100,
        retry_attempts: 3,
    };
    
    let mut ai_connector = AIConnector::new(config, tx, market_rx).await?;
    
    // Send test message to DragonflyDB
    let test_decision = json!({
        "decision_id": "test-123",
        "symbol": "SOL/USDC",
        "action": "BUY",
        "confidence": 0.85,
        "reasoning": "Test decision",
        "quantity": 100.0,
        "target_price": 100.0,
        "timestamp": chrono::Utc::now()
    });
    
    redis::cmd("LPUSH")
        .arg("overmind:trading_commands")
        .arg(test_decision.to_string())
        .execute_async(&mut conn)
        .await?;
    
    // Start AI connector in background
    let handle = tokio::spawn(async move {
        ai_connector.start().await
    });
    
    // Wait briefly
    tokio::time::sleep(std::time::Duration::from_secs(2)).await;
    
    // Verify connection is healthy
    let is_connected = ai_connector.is_brain_connected().await;
    assert!(is_connected, "AI Brain connection should be healthy");
    
    // Clean up
    handle.abort();
    
    Ok(())
}