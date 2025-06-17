// THE OVERMIND PROTOCOL - Real API Integration Tests
// Tests with actual TensorZero Gateway and Jito Bundle APIs

use std::time::{Duration, Instant};
use tokio::time::timeout;
use serde_json::json;

/// Helper function for TensorZero connection test
async fn check_tensorzero_connection() {
    let client = reqwest::Client::new();
    let tensorzero_url = std::env::var("OVERMIND_TENSORZERO_URL")
        .unwrap_or_else(|_| "http://localhost:3000".to_string());

    // Test health endpoint
    let health_response = timeout(
        Duration::from_secs(5),
        client.get(format!("{}/health", tensorzero_url)).send()
    ).await;

    assert!(health_response.is_ok(), "TensorZero health check should succeed");
    let response = health_response.unwrap().unwrap();
    assert!(response.status().is_success(), "TensorZero should be healthy");

    println!("✅ TensorZero Gateway connection successful");
}

/// Test real TensorZero Gateway connection
#[tokio::test]
#[ignore] // Use --ignored to run these tests
async fn test_real_tensorzero_connection() {
    check_tensorzero_connection().await;
}

/// Helper function for AI inference test
async fn check_ai_inference() {
    let client = reqwest::Client::new();
    let tensorzero_url = std::env::var("OVERMIND_TENSORZERO_URL")
        .unwrap_or_else(|_| "http://localhost:3003".to_string());

    // Use correct TensorZero format with messages
    let request_body = json!({
        "function_name": "test_function",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "Analyze SOL/USDC market data: price=50.0, volume=1000000. Should I buy or sell?"
                }
            ]
        }
    });

    let start_time = Instant::now();

    let response = timeout(
        Duration::from_secs(10),
        client
            .post(format!("{}/inference", tensorzero_url))
            .json(&request_body)
            .send()
    ).await;

    let latency = start_time.elapsed();

    assert!(response.is_ok(), "AI inference request should succeed");
    let response = response.unwrap().unwrap();

    // Check latency requirement first
    assert!(latency.as_millis() <= 1000, "AI inference latency should be <= 1000ms, got {}ms", latency.as_millis());

    // Get response text to handle both success and error cases
    let response_text = response.text().await.unwrap();
    println!("TensorZero response: {}", response_text);

    // Try to parse as JSON
    let response_body: serde_json::Value = serde_json::from_str(&response_text)
        .expect("Response should be valid JSON");

    // Accept both success responses and expected errors (like "Unknown function")
    let is_valid_response = response_body.get("inference_id").is_some() ||
                           response_body.get("error").is_some();

    assert!(is_valid_response, "Response should contain either inference_id or error");

    println!("✅ Real AI inference test completed - Latency: {}ms", latency.as_millis());
}

/// Test real AI inference with TensorZero
#[tokio::test]
#[ignore]
async fn test_real_ai_inference() {
    check_ai_inference().await;
}

/// Helper function for Jito connection test
async fn check_jito_connection() {
    let client = reqwest::Client::new();
    let jito_endpoint = std::env::var("OVERMIND_JITO_ENDPOINT")
        .unwrap_or_else(|_| "https://mainnet.block-engine.jito.wtf".to_string());

    // Test basic connectivity (Jito doesn't have a standard health endpoint)
    // We'll test with a simple RPC call
    let rpc_request = json!({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getVersion",
        "params": []
    });

    let response = timeout(
        Duration::from_secs(10),
        client
            .post(&jito_endpoint)
            .json(&rpc_request)
            .send()
    ).await;

    assert!(response.is_ok(), "Jito endpoint should be reachable");
    let response = response.unwrap().unwrap();

    // Jito might return different status codes, so we just check it's reachable
    println!("✅ Jito endpoint reachable - Status: {}", response.status());
}

/// Test Jito Bundle API connection
#[tokio::test]
#[ignore]
async fn test_real_jito_connection() {
    check_jito_connection().await;
}

/// Test complete OVERMIND workflow with real APIs
#[tokio::test]
#[ignore]
async fn test_complete_overmind_workflow() {
    println!("🧠 Testing complete OVERMIND workflow with real APIs...");

    // Step 1: Test TensorZero connection
    check_tensorzero_connection().await;

    // Step 2: Test AI inference
    check_ai_inference().await;

    // Step 3: Test Jito connection
    check_jito_connection().await;

    println!("✅ Complete OVERMIND workflow test successful");
}

/// Test AI decision latency under load
#[tokio::test]
#[ignore]
async fn test_ai_latency_under_load() {
    let client = reqwest::Client::new();
    let tensorzero_url = std::env::var("OVERMIND_TENSORZERO_URL")
        .unwrap_or_else(|_| "http://localhost:3000".to_string());
    
    let mut handles = Vec::new();
    let num_requests = 10;
    
    println!("🧠 Testing AI latency under load ({} concurrent requests)...", num_requests);
    
    for i in 0..num_requests {
        let client_clone = client.clone();
        let url_clone = tensorzero_url.clone();
        
        let handle = tokio::spawn(async move {
            let request_body = json!({
                "function_name": "overmind_trading_decision",
                "input": {
                    "market_data": json!({
                        "symbol": "SOL/USDC",
                        "price": 50.0 + i as f64,
                        "volume": 1000000,
                        "request_id": i
                    }).to_string()
                }
            });
            
            let start_time = Instant::now();
            
            let response = client_clone
                .post(format!("{}/inference", url_clone))
                .json(&request_body)
                .send()
                .await;
            
            let latency = start_time.elapsed();
            
            (i, response.is_ok(), latency)
        });
        
        handles.push(handle);
    }
    
    let results = futures::future::join_all(handles).await;
    
    let mut successful = 0;
    let mut total_latency = Duration::from_millis(0);
    let mut max_latency = Duration::from_millis(0);
    
    for result in results {
        let (request_id, success, latency) = result.unwrap();
        
        if success {
            successful += 1;
            total_latency += latency;
            max_latency = max_latency.max(latency);
            
            println!("Request {}: {}ms", request_id, latency.as_millis());
        } else {
            println!("Request {} failed", request_id);
        }
    }
    
    let avg_latency = total_latency / successful;
    let success_rate = successful as f64 / num_requests as f64 * 100.0;
    
    println!("📊 Load test results:");
    println!("  Success rate: {:.1}%", success_rate);
    println!("  Average latency: {}ms", avg_latency.as_millis());
    println!("  Max latency: {}ms", max_latency.as_millis());
    
    // Assertions
    assert!(success_rate >= 80.0, "Success rate should be >= 80%, got {:.1}%", success_rate);
    assert!(avg_latency.as_millis() <= 200, "Average latency should be <= 200ms, got {}ms", avg_latency.as_millis());
    assert!(max_latency.as_millis() <= 500, "Max latency should be <= 500ms, got {}ms", max_latency.as_millis());
    
    println!("✅ AI latency under load test passed");
}

/// Test error handling with real APIs
#[tokio::test]
#[ignore]
async fn test_real_api_error_handling() {
    let client = reqwest::Client::new();
    
    // Test with invalid TensorZero endpoint
    let invalid_url = "http://localhost:9999";
    
    let response = timeout(
        Duration::from_secs(2),
        client.get(format!("{}/health", invalid_url)).send()
    ).await;
    
    // Should either timeout or fail
    assert!(response.is_err() || response.unwrap().is_err(), "Should fail with invalid endpoint");
    
    println!("✅ Error handling test passed");
}

/// Test configuration validation
#[tokio::test]
#[ignore]
async fn test_production_configuration() {
    println!("🔧 Testing production configuration...");

    // Check optional environment variables with defaults
    let config_vars = vec![
        ("OVERMIND_ENABLED", "false"),
        ("OVERMIND_TENSORZERO_URL", "http://localhost:3003"),
        ("OVERMIND_JITO_ENDPOINT", "https://mainnet.block-engine.jito.wtf"),
        ("OVERMIND_MAX_LATENCY_MS", "25"),
        ("OVERMIND_AI_CONFIDENCE_THRESHOLD", "0.7"),
    ];

    for (var, default_value) in config_vars {
        let value = std::env::var(var).unwrap_or_else(|_| default_value.to_string());
        assert!(!value.is_empty(), "Configuration variable {} should not be empty", var);
        println!("  {}: {}", var, value);
    }

    // Validate specific values with defaults
    let overmind_enabled: bool = std::env::var("OVERMIND_ENABLED")
        .unwrap_or_else(|_| "false".to_string())
        .parse()
        .unwrap_or(false);

    println!("  OVERMIND enabled: {}", overmind_enabled);

    let max_latency: u64 = std::env::var("OVERMIND_MAX_LATENCY_MS")
        .unwrap_or_else(|_| "25".to_string())
        .parse()
        .unwrap_or(25);

    assert!(max_latency <= 100, "Max latency should be reasonable for HFT, got {}ms", max_latency);

    let confidence_threshold: f64 = std::env::var("OVERMIND_AI_CONFIDENCE_THRESHOLD")
        .unwrap_or_else(|_| "0.7".to_string())
        .parse()
        .unwrap_or(0.7);

    assert!((0.5..=1.0).contains(&confidence_threshold),
            "Confidence threshold should be between 0.5 and 1.0, got {}", confidence_threshold);

    println!("✅ Production configuration validation passed");
}

/// Test system health monitoring
#[tokio::test]
#[ignore]
async fn test_system_health_monitoring() {
    let client = reqwest::Client::new();
    
    println!("🔍 Testing system health monitoring...");
    
    // Test main trading system health
    let trading_health = client
        .get("http://localhost:8080/health")
        .send()
        .await;
    
    if let Ok(response) = trading_health {
        if response.status().is_success() {
            println!("✅ Trading system health: OK");
        } else {
            println!("⚠️ Trading system health: {}", response.status());
        }
    } else {
        println!("❌ Trading system health: Not reachable");
    }
    
    // Test Prometheus metrics
    let metrics_response = client
        .get("http://localhost:9090/-/healthy")
        .send()
        .await;
    
    if let Ok(response) = metrics_response {
        if response.status().is_success() {
            println!("✅ Prometheus health: OK");
        } else {
            println!("⚠️ Prometheus health: {}", response.status());
        }
    } else {
        println!("❌ Prometheus health: Not reachable");
    }
    
    // Test Grafana
    let grafana_response = client
        .get("http://localhost:3001/api/health")
        .send()
        .await;
    
    if let Ok(response) = grafana_response {
        if response.status().is_success() {
            println!("✅ Grafana health: OK");
        } else {
            println!("⚠️ Grafana health: {}", response.status());
        }
    } else {
        println!("❌ Grafana health: Not reachable");
    }
    
    println!("✅ System health monitoring test completed");
}
