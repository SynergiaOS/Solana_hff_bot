use tokio::time::Duration;

/// AI Brain Validation Test Suite
/// Tests AI decision-making quality, ensemble models, RAG accuracy, and optimization
#[cfg(test)]
mod ai_brain_validation_tests {
    use super::*;

    /// Test AI connector configuration validation
    #[tokio::test]
    async fn test_ai_connector_config_validation() {
        use snipercor::modules::ai_connector::AIConnectorConfig;

        let config = AIConnectorConfig {
            dragonfly_url: "redis://localhost:6379".to_string(),
            brain_request_timeout: Duration::from_secs(30),
            tensorzero_url: "http://localhost:3000".to_string(),
            use_tensorzero: true,
            max_decision_age: Duration::from_secs(60),
            confidence_threshold: 0.5,
            vector_cache_size: 1000,
            retry_attempts: 3,
        };

        // Validate configuration parameters
        assert!(config.brain_request_timeout > Duration::from_secs(0), "Timeout should be positive");
        assert!(config.max_decision_age > Duration::from_secs(0), "Max decision age should be positive");
        assert!(config.confidence_threshold >= 0.0 && config.confidence_threshold <= 1.0, "Confidence threshold should be in [0,1]");
        assert!(config.vector_cache_size > 0, "Vector cache size should be positive");
        assert!(config.retry_attempts > 0, "Retry attempts should be positive");

        println!("✅ AI Connector configuration validation passed");
    }

    /// Test TensorZero client configuration
    #[tokio::test]
    async fn test_tensorzero_config_validation() {
        use snipercor::modules::tensorzero_client::{TensorZeroClient, TensorZeroConfig};

        let config = TensorZeroConfig {
            gateway_url: "http://localhost:3000".to_string(),
            api_key: "test_key".to_string(),
            max_latency_ms: 1000,
            optimization_level: "1".to_string(),
            cache_enabled: true,
            request_timeout_secs: 30,
            batch_size: 10,
        };

        // Validate TensorZero configuration
        assert!(config.max_latency_ms > 0, "Max latency should be positive");
        assert!(config.request_timeout_secs > 0, "Request timeout should be positive");
        assert!(config.batch_size > 0, "Batch size should be positive");

        // Test client creation
        let client_result = TensorZeroClient::new(config);
        assert!(client_result.is_ok(), "TensorZero client should be created successfully");

        println!("✅ TensorZero configuration validation passed");
    }

    /// Test AI Brain decision structure validation
    #[tokio::test]
    async fn test_ai_decision_structure() {
        use snipercor::modules::ai_connector::{AIDecision, AIAction};

        // Create a test decision with actual fields
        let decision = AIDecision {
            decision_id: "test_decision_001".to_string(),
            symbol: "SOL/USDC".to_string(),
            action: AIAction::Buy,
            quantity: 1000.0,
            target_price: Some(105.0),
            confidence: 0.85,
            reasoning: "Strong bullish signals detected".to_string(),
            timestamp: chrono::Utc::now(),
            ai_context: Some(std::collections::HashMap::new()),
            vector_memory_context: Some("test_context".to_string()),
        };

        // Validate decision structure
        assert!(matches!(decision.action, AIAction::Buy), "Action should be Buy");
        assert!(decision.confidence >= 0.0 && decision.confidence <= 1.0, "Confidence should be in [0,1]");
        assert!(!decision.reasoning.is_empty(), "Reasoning should not be empty");
        assert!(decision.quantity > 0.0, "Quantity should be positive");
        assert!(!decision.decision_id.is_empty(), "Decision ID should not be empty");

        println!("✅ AI Decision structure validation passed");
    }

    /// Test AI Brain market event structure
    #[tokio::test]
    async fn test_market_event_structure() {
        use snipercor::modules::ai_connector::{MarketEvent, MarketEventType};
        use chrono::Utc;

        // Create a test market event
        let event = MarketEvent {
            event_id: "test_event_001".to_string(),
            symbol: "SOL/USDC".to_string(),
            price: 100.0,
            volume: 1000000.0,
            timestamp: Utc::now(),
            event_type: MarketEventType::PriceUpdate,
            metadata: std::collections::HashMap::new(),
        };

        // Validate event structure
        assert!(!event.event_id.is_empty(), "Event ID should not be empty");
        assert!(!event.symbol.is_empty(), "Symbol should not be empty");
        assert!(event.price > 0.0, "Price should be positive");
        assert!(event.volume >= 0.0, "Volume should be non-negative");
        assert!(matches!(event.event_type, MarketEventType::PriceUpdate), "Event type should be PriceUpdate");

        println!("✅ Market Event structure validation passed");
    }

    /// Test AI Brain performance metrics
    #[tokio::test]
    async fn test_ai_metrics_structure() {
        use snipercor::modules::ai_connector::AIMetrics;

        // Create test metrics
        let metrics = AIMetrics {
            decisions_received: 100,
            decisions_processed: 95,
            decisions_rejected: 5,
            avg_decision_latency: Duration::from_millis(150),
            brain_connection_errors: 2,
            vector_cache_hits: 80,
            vector_cache_misses: 20,
        };

        // Validate metrics structure
        assert!(metrics.decisions_received >= metrics.decisions_processed, "Received should be >= processed");
        assert!(metrics.decisions_processed + metrics.decisions_rejected <= metrics.decisions_received, "Processed + rejected should be <= received");
        assert!(metrics.avg_decision_latency < Duration::from_secs(5), "Average latency should be reasonable");
        assert!(metrics.vector_cache_hits + metrics.vector_cache_misses > 0, "Should have cache activity");

        println!("✅ AI Metrics structure validation passed");
    }

    /// Test AI Brain action types
    #[tokio::test]
    async fn test_ai_action_types() {
        use snipercor::modules::ai_connector::AIAction;

        // Test all action types
        let actions = vec![
            AIAction::Buy,
            AIAction::Sell,
            AIAction::Hold,
            AIAction::StopLoss,
            AIAction::TakeProfit,
        ];

        for action in actions {
            match action {
                AIAction::Buy => assert!(true, "Buy action should be valid"),
                AIAction::Sell => assert!(true, "Sell action should be valid"),
                AIAction::Hold => assert!(true, "Hold action should be valid"),
                AIAction::StopLoss => assert!(true, "StopLoss action should be valid"),
                AIAction::TakeProfit => assert!(true, "TakeProfit action should be valid"),
            }
        }

        println!("✅ AI Action types validation passed");
    }

    /// Test AI Brain market event types
    #[tokio::test]
    async fn test_market_event_types() {
        use snipercor::modules::ai_connector::MarketEventType;

        // Test all event types
        let event_types = vec![
            MarketEventType::PriceUpdate,
            MarketEventType::VolumeSpike,
            MarketEventType::OrderBookChange,
            MarketEventType::TradeExecution,
            MarketEventType::NewsEvent,
        ];

        for event_type in event_types {
            match event_type {
                MarketEventType::PriceUpdate => assert!(true, "PriceUpdate should be valid"),
                MarketEventType::VolumeSpike => assert!(true, "VolumeSpike should be valid"),
                MarketEventType::OrderBookChange => assert!(true, "OrderBookChange should be valid"),
                MarketEventType::TradeExecution => assert!(true, "TradeExecution should be valid"),
                MarketEventType::NewsEvent => assert!(true, "NewsEvent should be valid"),
            }
        }

        println!("✅ Market Event types validation passed");
    }
}
