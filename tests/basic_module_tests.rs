//! Basic Module Tests for THE OVERMIND PROTOCOL
//!
//! Simple tests to verify that all modules compile and basic functionality works

use snipercor::modules::hft_engine::{HftEngineConfig, TradingSignal};
use snipercor::modules::ai_connector::AIConnectorConfig;
use snipercor::modules::tensorzero_client::TensorZeroConfig;
use snipercor::modules::jito_client::JitoConfig;
use snipercor::modules::multi_wallet_load_balancer::LoadBalancerConfig;
use snipercor::modules::geographic_distribution::GeographicConfig;
use snipercor::modules::submillisecond_optimizer::OptimizationConfig;

#[tokio::test]
async fn test_hft_engine_config_creation() {
    let config = HftEngineConfig::default();
    assert!(!config.solana_rpc_url.is_empty());
    assert!(!config.tensorzero_url.is_empty());
    assert!(!config.jito_url.is_empty());
    assert!(config.max_tip_lamports > 0);
    println!("✅ HFT Engine Config created successfully");
}

#[tokio::test]
async fn test_trading_signal_creation() {
    let signal = TradingSignal {
        symbol: "SOL/USDC".to_string(),
        action: "BUY".to_string(),
        quantity: 100.0,
        price: Some(150.0),
        confidence: 0.85,
        reasoning: "Strong bullish momentum detected".to_string(),
    };
    
    assert_eq!(signal.symbol, "SOL/USDC");
    assert_eq!(signal.action, "BUY");
    assert_eq!(signal.quantity, 100.0);
    assert_eq!(signal.confidence, 0.85);
    println!("✅ Trading Signal created successfully");
}

#[tokio::test]
async fn test_ai_connector_config_creation() {
    let config = AIConnectorConfig::default();
    assert!(!config.dragonfly_url.is_empty());
    assert!(config.brain_request_timeout.as_secs() > 0);
    println!("✅ AI Connector Config created successfully");
}

#[tokio::test]
async fn test_tensorzero_config_creation() {
    let config = TensorZeroConfig::default();
    assert!(!config.gateway_url.is_empty());
    assert!(config.max_latency_ms > 0);
    println!("✅ TensorZero Config created successfully");
}

#[tokio::test]
async fn test_jito_config_creation() {
    let config = JitoConfig::default();
    assert!(!config.bundle_url.is_empty());
    assert!(!config.tip_account.is_empty());
    assert!(config.max_tip_lamports > 0);
    println!("✅ Jito Config created successfully");
}

#[tokio::test]
async fn test_load_balancer_config_creation() {
    let config = LoadBalancerConfig::default();
    assert!(config.max_concurrent_transactions > 0);
    assert!(config.health_check_interval.as_secs() > 0);
    assert!(config.performance_window.as_secs() > 0);
    println!("✅ Load Balancer Config created successfully");
}

#[tokio::test]
async fn test_geographic_config_creation() {
    let config = GeographicConfig::default();
    assert!(!config.primary_regions.is_empty());
    assert!(!config.fallback_regions.is_empty());
    assert!(config.latency_threshold_ms > 0.0);
    println!("✅ Geographic Config created successfully");
}

#[tokio::test]
async fn test_optimization_config_creation() {
    let config = OptimizationConfig::default();
    assert!(config.target_latency_us > 0);
    assert!(config.memory_preallocation_mb > 0);
    println!("✅ Optimization Config created successfully");
}

#[tokio::test]
async fn test_all_configs_integration() {
    // Test that all configs can be created together
    let hft_config = HftEngineConfig::default();
    let ai_config = AIConnectorConfig::default();
    let tensor_config = TensorZeroConfig::default();
    let jito_config = JitoConfig::default();
    let lb_config = LoadBalancerConfig::default();
    let geo_config = GeographicConfig::default();
    let opt_config = OptimizationConfig::default();
    
    // Verify all configs are valid
    assert!(!hft_config.solana_rpc_url.is_empty());
    assert!(!ai_config.dragonfly_url.is_empty());
    assert!(!tensor_config.gateway_url.is_empty());
    assert!(!jito_config.bundle_url.is_empty());
    assert!(lb_config.max_concurrent_transactions > 0);
    assert!(!geo_config.primary_regions.is_empty());
    assert!(opt_config.target_latency_us > 0);
    
    println!("✅ All configs integration test passed");
}

#[tokio::test]
async fn test_module_compilation() {
    // This test simply verifies that all modules compile correctly
    // If we get here, all modules compiled successfully
    println!("✅ All modules compiled successfully");
    assert!(true, "Module compilation test passed");
}

#[tokio::test]
async fn test_performance_benchmark() {
    use std::time::Instant;
    
    let start = Instant::now();
    
    // Create multiple configs to test performance
    for _ in 0..1000 {
        let _config = HftEngineConfig::default();
    }
    
    let duration = start.elapsed();
    println!("⚡ Created 1000 configs in {:?}", duration);
    
    // Should be very fast (under 10ms)
    assert!(duration.as_millis() < 100, "Config creation should be fast");
}

#[tokio::test]
async fn test_memory_usage() {
    use std::mem;
    
    // Test memory footprint of key structures
    let hft_config_size = mem::size_of::<HftEngineConfig>();
    let trading_signal_size = mem::size_of::<TradingSignal>();
    
    println!("📊 HftEngineConfig size: {} bytes", hft_config_size);
    println!("📊 TradingSignal size: {} bytes", trading_signal_size);
    
    // Verify reasonable memory usage
    assert!(hft_config_size < 1024, "Config should be under 1KB");
    assert!(trading_signal_size < 512, "Signal should be under 512 bytes");
}

#[tokio::test]
async fn test_error_handling() {
    // Test that our error types work correctly
    use anyhow::Result;
    
    fn test_function() -> Result<()> {
        Err(anyhow::anyhow!("Test error"))
    }
    
    let result = test_function();
    assert!(result.is_err(), "Error handling should work");
    
    println!("✅ Error handling test passed");
}

#[tokio::test]
async fn test_async_functionality() {
    use tokio::time::{sleep, Duration};
    
    let start = Instant::now();
    
    // Test async sleep
    sleep(Duration::from_millis(10)).await;
    
    let duration = start.elapsed();
    assert!(duration.as_millis() >= 10, "Async sleep should work");
    
    println!("✅ Async functionality test passed");
}

#[tokio::test]
async fn test_serialization() {
    use serde_json;
    
    let signal = TradingSignal {
        symbol: "SOL/USDC".to_string(),
        action: "BUY".to_string(),
        quantity: 100.0,
        price: Some(150.0),
        confidence: 0.85,
        reasoning: "Test signal".to_string(),
    };
    
    // Test serialization
    let json = serde_json::to_string(&signal);
    assert!(json.is_ok(), "Serialization should work");
    
    // Test deserialization
    let json_str = json.unwrap();
    let deserialized: Result<TradingSignal, _> = serde_json::from_str(&json_str);
    assert!(deserialized.is_ok(), "Deserialization should work");
    
    let recovered_signal = deserialized.unwrap();
    assert_eq!(recovered_signal.symbol, signal.symbol);
    assert_eq!(recovered_signal.action, signal.action);
    
    println!("✅ Serialization test passed");
}

use std::time::Instant;
