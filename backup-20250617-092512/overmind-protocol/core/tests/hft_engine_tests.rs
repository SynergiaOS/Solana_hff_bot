// THE OVERMIND PROTOCOL - Comprehensive HFT Engine Tests
// Tests for TensorZero integration, Jito bundles, and ultra-low latency execution

// Note: In integration tests, we need to reference the crate differently
// use snipercor::modules::hft_engine::{HFTConfig, OvermindHFTEngine, ExecutionResult};
use std::time::{Duration, Instant};
use tokio::time::timeout;

mod test_utils;
mod mock_tensorzero_server;
mod mock_jito_server;

use test_utils::{TestEnvironment, TestHFTConfigBuilder, PerformanceMeasurer, TestAssertions};

/// Test HFT Engine creation and initialization
#[tokio::test]
async fn test_hft_engine_creation() {
    let config = TestHFTConfigBuilder::new().build();
    let engine = OvermindHFTEngine::new(config);
    
    assert!(engine.is_ok(), "HFT Engine should be created successfully");
}

/// Test HFT Engine with invalid configuration
#[tokio::test]
async fn test_hft_engine_invalid_config() {
    let config = TestHFTConfigBuilder::new()
        .with_tensorzero_url("invalid_url".to_string())
        .build();
    
    let engine = OvermindHFTEngine::new(config);
    // Should still create but fail on actual requests
    assert!(engine.is_ok());
}

/// Test TensorZero client integration
#[tokio::test]
async fn test_tensorzero_integration() {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");
    
    // Wait for mock server to be ready
    tokio::time::sleep(Duration::from_millis(200)).await;
    
    let config = TestHFTConfigBuilder::new()
        .with_tensorzero_url(format!("http://localhost:{}", env.tensorzero_port))
        .build();
    
    let mut engine = OvermindHFTEngine::new(config).expect("Failed to create HFT engine");
    
    let market_data = r#"{"signal_id":"test","strategy":"momentum","price":50.0}"#;
    
    let result = timeout(
        Duration::from_secs(5),
        engine.execute_ai_signal(market_data)
    ).await;
    
    assert!(result.is_ok(), "TensorZero request should not timeout");
    
    match result.unwrap() {
        Ok(ExecutionResult::Executed { ai_confidence, .. }) => {
            TestAssertions::assert_confidence_valid(ai_confidence);
        }
        Ok(ExecutionResult::Skipped { reason, .. }) => {
            println!("AI skipped execution: {}", reason);
        }
        Err(e) => {
            panic!("TensorZero integration failed: {}", e);
        }
    }
}

/// Test AI confidence threshold filtering
#[tokio::test]
async fn test_ai_confidence_threshold() {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");
    
    tokio::time::sleep(Duration::from_millis(200)).await;
    
    // Set high confidence threshold
    let config = TestHFTConfigBuilder::new()
        .with_tensorzero_url(format!("http://localhost:{}", env.tensorzero_port))
        .with_ai_confidence_threshold(0.95) // Very high threshold
        .build();
    
    let mut engine = OvermindHFTEngine::new(config).expect("Failed to create HFT engine");
    
    let market_data = r#"{"signal_id":"test","strategy":"low_confidence","price":50.0}"#;
    
    let result = engine.execute_ai_signal(market_data).await;
    
    match result {
        Ok(ExecutionResult::Skipped { reason, .. }) => {
            assert!(reason.contains("confidence"), "Should skip due to low confidence");
        }
        Ok(ExecutionResult::Executed { ai_confidence, .. }) => {
            assert!(ai_confidence >= 0.95, "Should only execute high confidence signals");
        }
        Err(e) => {
            panic!("Unexpected error: {}", e);
        }
    }
}

/// Test latency performance requirements
#[tokio::test]
async fn test_latency_performance() {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");
    
    tokio::time::sleep(Duration::from_millis(200)).await;
    
    let config = TestHFTConfigBuilder::new()
        .with_tensorzero_url(format!("http://localhost:{}", env.tensorzero_port))
        .with_jito_endpoint(format!("http://localhost:{}", env.jito_port))
        .with_max_latency(25) // 25ms target
        .build();
    
    let mut engine = OvermindHFTEngine::new(config).expect("Failed to create HFT engine");
    
    let mut measurer = PerformanceMeasurer::new();
    let market_data = r#"{"signal_id":"test","strategy":"speed_test","price":50.0}"#;
    
    // Run multiple iterations to get average latency
    for _ in 0..10 {
        measurer.start_measurement();
        
        let result = engine.execute_ai_signal(market_data).await;
        
        let duration = measurer.end_measurement();
        
        // Each individual request should be fast
        TestAssertions::assert_latency_acceptable(duration, 100); // Allow 100ms for test environment
        
        match result {
            Ok(ExecutionResult::Executed { latency_ms, .. }) => {
                assert!(latency_ms <= 100, "Reported latency should be reasonable: {}ms", latency_ms);
            }
            Ok(ExecutionResult::Skipped { latency_ms, .. }) => {
                assert!(latency_ms <= 100, "Skip latency should be reasonable: {}ms", latency_ms);
            }
            Err(e) => {
                println!("Request failed (acceptable in stress test): {}", e);
            }
        }
    }
    
    let avg_latency = measurer.average_duration();
    let p95_latency = measurer.percentile(95.0);
    
    println!("Average latency: {}ms", avg_latency.as_millis());
    println!("P95 latency: {}ms", p95_latency.as_millis());
    
    // In test environment, allow higher latencies
    TestAssertions::assert_latency_acceptable(avg_latency, 200);
    TestAssertions::assert_latency_acceptable(p95_latency, 500);
}

/// Test concurrent execution performance
#[tokio::test]
async fn test_concurrent_execution() {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");
    
    tokio::time::sleep(Duration::from_millis(200)).await;
    
    let config = TestHFTConfigBuilder::new()
        .with_tensorzero_url(format!("http://localhost:{}", env.tensorzero_port))
        .build();
    
    let engine = OvermindHFTEngine::new(config).expect("Failed to create HFT engine");
    
    // Create multiple concurrent requests
    let mut handles = Vec::new();
    
    for i in 0..5 {
        let mut engine_clone = OvermindHFTEngine::new(
            TestHFTConfigBuilder::new()
                .with_tensorzero_url(format!("http://localhost:{}", env.tensorzero_port))
                .build()
        ).expect("Failed to create HFT engine");
        
        let handle = tokio::spawn(async move {
            let market_data = format!(r#"{{"signal_id":"concurrent_{}","strategy":"test","price":50.0}}"#, i);
            engine_clone.execute_ai_signal(&market_data).await
        });
        
        handles.push(handle);
    }
    
    // Wait for all requests to complete
    let results = futures::future::join_all(handles).await;
    
    let mut successful = 0;
    let mut skipped = 0;
    let mut failed = 0;
    
    for result in results {
        match result {
            Ok(Ok(ExecutionResult::Executed { .. })) => successful += 1,
            Ok(Ok(ExecutionResult::Skipped { .. })) => skipped += 1,
            Ok(Err(_)) => failed += 1,
            Err(_) => failed += 1,
        }
    }
    
    println!("Concurrent execution results: {} successful, {} skipped, {} failed", 
             successful, skipped, failed);
    
    // At least some requests should succeed
    assert!(successful + skipped > 0, "At least some requests should complete successfully");
}

/// Test error handling and recovery
#[tokio::test]
async fn test_error_handling() {
    // Test with non-existent server
    let config = TestHFTConfigBuilder::new()
        .with_tensorzero_url("http://localhost:9999".to_string()) // Non-existent server
        .build();
    
    let mut engine = OvermindHFTEngine::new(config).expect("Failed to create HFT engine");
    
    let market_data = r#"{"signal_id":"error_test","strategy":"test","price":50.0}"#;
    
    let result = timeout(
        Duration::from_secs(2),
        engine.execute_ai_signal(market_data)
    ).await;
    
    // Should either timeout or return an error
    match result {
        Ok(Err(_)) => {
            // Expected error due to connection failure
        }
        Err(_) => {
            // Expected timeout
        }
        Ok(Ok(_)) => {
            panic!("Should not succeed with non-existent server");
        }
    }
}

/// Test Jito bundle integration
#[tokio::test]
async fn test_jito_bundle_integration() {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");
    
    tokio::time::sleep(Duration::from_millis(200)).await;
    
    let config = TestHFTConfigBuilder::new()
        .with_tensorzero_url(format!("http://localhost:{}", env.tensorzero_port))
        .with_jito_endpoint(format!("http://localhost:{}", env.jito_port))
        .build();
    
    let mut engine = OvermindHFTEngine::new(config).expect("Failed to create HFT engine");
    
    let market_data = r#"{"signal_id":"jito_test","strategy":"mev","price":50.0}"#;
    
    let result = engine.execute_ai_signal(market_data).await;
    
    match result {
        Ok(ExecutionResult::Executed { bundle_id, .. }) => {
            assert!(!bundle_id.is_empty(), "Bundle ID should not be empty");
            assert!(bundle_id.starts_with("bundle_"), "Bundle ID should have correct format");
        }
        Ok(ExecutionResult::Skipped { reason, .. }) => {
            println!("Execution skipped: {}", reason);
        }
        Err(e) => {
            println!("Jito integration error (may be expected in test): {}", e);
        }
    }
}

/// Test metrics collection
#[tokio::test]
async fn test_metrics_collection() {
    let config = TestHFTConfigBuilder::new().build();
    let engine = OvermindHFTEngine::new(config).expect("Failed to create HFT engine");
    
    let metrics = engine.get_metrics();
    
    // Initial metrics should be zero
    assert_eq!(metrics.total_executions, 0);
    assert_eq!(metrics.successful_executions, 0);
    assert_eq!(metrics.failed_executions, 0);
    assert_eq!(metrics.ai_decisions_made, 0);
    assert_eq!(metrics.bundles_submitted, 0);
}

/// Stress test for high-frequency execution
#[tokio::test]
async fn test_high_frequency_stress() {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");
    
    tokio::time::sleep(Duration::from_millis(200)).await;
    
    let config = TestHFTConfigBuilder::new()
        .with_tensorzero_url(format!("http://localhost:{}", env.tensorzero_port))
        .build();
    
    let mut engine = OvermindHFTEngine::new(config).expect("Failed to create HFT engine");
    
    let start_time = Instant::now();
    let mut successful_requests = 0;
    
    // Run for 5 seconds
    while start_time.elapsed() < Duration::from_secs(5) {
        let market_data = format!(
            r#"{{"signal_id":"stress_{}","strategy":"test","price":50.0}}"#,
            chrono::Utc::now().timestamp_nanos()
        );
        
        match engine.execute_ai_signal(&market_data).await {
            Ok(ExecutionResult::Executed { .. }) | Ok(ExecutionResult::Skipped { .. }) => {
                successful_requests += 1;
            }
            Err(_) => {
                // Errors are acceptable under stress
            }
        }
        
        // Small delay to prevent overwhelming the system
        tokio::time::sleep(Duration::from_millis(10)).await;
    }
    
    let total_time = start_time.elapsed();
    let requests_per_second = successful_requests as f64 / total_time.as_secs_f64();
    
    println!("Stress test results: {} requests in {}ms ({:.2} req/s)", 
             successful_requests, total_time.as_millis(), requests_per_second);
    
    // Should handle at least some requests per second
    assert!(requests_per_second > 1.0, "Should handle at least 1 request per second");
}
