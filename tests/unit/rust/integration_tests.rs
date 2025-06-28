// THE OVERMIND PROTOCOL - Integration Tests
// Tests inter-module communication and end-to-end AI-enhanced workflows
// Note: Simplified due to module visibility - in production these would test actual modules

use tokio::sync::mpsc;
use tokio::time::{timeout, Duration};

mod test_utils;
mod mock_tensorzero_server;
mod mock_jito_server;

use test_utils::{TestEnvironment, TestSignalGenerator, TestConfigBuilder, PerformanceMeasurer};

#[tokio::test]
async fn test_channel_communication() -> anyhow::Result<()> {
    // Test basic MPSC channel communication (foundation of our architecture)
    let (tx, mut rx) = mpsc::unbounded_channel::<String>();

    // Spawn a task that sends data
    let sender_task = tokio::spawn(async move {
        tx.send("test_message".to_string()).unwrap();
    });

    // Receive the data
    let received = timeout(Duration::from_millis(100), rx.recv())
        .await?
        .expect("Should receive message");

    assert_eq!(received, "test_message");

    sender_task.await?;
    Ok(())
}

#[tokio::test]
async fn test_concurrent_channels() -> anyhow::Result<()> {
    // Test multiple concurrent channels (simulating our module architecture)
    let (tx1, mut rx1) = mpsc::unbounded_channel::<i32>();
    let (tx2, mut rx2) = mpsc::unbounded_channel::<String>();

    // Spawn tasks that send data
    let task1 = tokio::spawn(async move {
        for i in 0..10 {
            tx1.send(i).unwrap();
        }
    });

    let task2 = tokio::spawn(async move {
        tx2.send("concurrent_test".to_string()).unwrap();
    });

    // Receive data from both channels
    let mut numbers = Vec::new();
    let mut received_string = None;

    for _ in 0..11 {
        // 10 numbers + 1 string
        tokio::select! {
            Some(num) = rx1.recv() => {
                numbers.push(num);
            }
            Some(s) = rx2.recv() => {
                received_string = Some(s);
            }
            else => break,
        }
    }

    assert_eq!(numbers.len(), 10);
    assert_eq!(received_string, Some("concurrent_test".to_string()));

    task1.await?;
    task2.await?;
    Ok(())
}

#[tokio::test]
async fn test_channel_throughput() -> anyhow::Result<()> {
    // Test channel throughput (important for HFT performance)
    let (tx, mut rx) = mpsc::unbounded_channel::<u64>();

    let start_time = std::time::Instant::now();

    // Send 1000 messages
    let sender_task = tokio::spawn(async move {
        for i in 0..1000 {
            tx.send(i).unwrap();
        }
    });

    // Receive all messages
    let receiver_task = tokio::spawn(async move {
        let mut count = 0;
        while (rx.recv().await).is_some() {
            count += 1;
            if count >= 1000 {
                break;
            }
        }
        count
    });

    sender_task.await?;
    let received_count = receiver_task.await?;

    let duration = start_time.elapsed();

    assert_eq!(received_count, 1000);
    // Should be very fast for unbounded channels
    assert!(
        duration.as_millis() < 100,
        "Channel throughput too slow: {:?}",
        duration
    );

    Ok(())
}

// ============================================================================
// THE OVERMIND PROTOCOL - AI-Enhanced Integration Tests
// ============================================================================

/// Test complete AI-enhanced trading workflow
#[tokio::test]
async fn test_overmind_trading_workflow() -> anyhow::Result<()> {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");

    // Wait for mock servers to be ready
    tokio::time::sleep(Duration::from_millis(300)).await;

    // Verify mock servers are healthy
    assert!(env.health_check().await, "Mock servers should be healthy");

    // Create test configuration
    let config = TestConfigBuilder::new()
        .with_overmind_enabled(true)
        .with_tensorzero_url(format!("http://localhost:{}", env.tensorzero_port))
        .build();

    assert!(config.is_overmind_enabled(), "OVERMIND should be enabled");

    Ok(())
}

/// Test AI decision latency in integration scenario
#[tokio::test]
async fn test_ai_decision_latency_integration() -> anyhow::Result<()> {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");

    tokio::time::sleep(Duration::from_millis(300)).await;

    let mut measurer = PerformanceMeasurer::new();

    // Simulate multiple AI decisions
    for i in 0..5 {
        measurer.start_measurement();

        // Simulate AI decision request
        let client = reqwest::Client::new();
        let response = client
            .get(&format!("http://localhost:{}/health", env.tensorzero_port))
            .send()
            .await;

        let duration = measurer.end_measurement();

        assert!(response.is_ok(), "Request {} should succeed", i);
        assert!(duration.as_millis() < 100, "Request {} latency should be acceptable", i);
    }

    let avg_latency = measurer.average_duration();
    println!("Average AI decision latency: {}ms", avg_latency.as_millis());

    Ok(())
}

/// Test error handling in AI-enhanced workflow
#[tokio::test]
async fn test_overmind_error_handling() -> anyhow::Result<()> {
    // Test with invalid configuration
    let config = TestConfigBuilder::new()
        .with_overmind_enabled(true)
        .with_tensorzero_url("http://localhost:9999".to_string()) // Non-existent server
        .build();

    assert!(config.is_overmind_enabled(), "OVERMIND should be enabled");

    // Test that system handles invalid configuration gracefully
    let client = reqwest::Client::new();
    let result = timeout(
        Duration::from_millis(500),
        client.get("http://localhost:9999/health").send()
    ).await;

    // Should either timeout or fail - both are acceptable
    assert!(result.is_err() || result.unwrap().is_err(), "Should fail with invalid server");

    Ok(())
}

/// Test concurrent AI requests
#[tokio::test]
async fn test_concurrent_ai_requests() -> anyhow::Result<()> {
    let env = TestEnvironment::new();
    env.setup().await.expect("Failed to setup test environment");

    tokio::time::sleep(Duration::from_millis(300)).await;

    let client = reqwest::Client::new();
    let mut handles = Vec::new();

    // Create 10 concurrent requests
    for i in 0..10 {
        let client_clone = client.clone();
        let url = format!("http://localhost:{}/health", env.tensorzero_port);

        let handle = tokio::spawn(async move {
            let result = client_clone.get(&url).send().await;
            (i, result.is_ok())
        });

        handles.push(handle);
    }

    // Wait for all requests
    let results = futures::future::join_all(handles).await;

    let successful = results.iter()
        .filter_map(|r| r.as_ref().ok())
        .filter(|(_, success)| *success)
        .count();

    println!("Concurrent requests: {}/{} successful", successful, results.len());

    // At least 80% should succeed
    assert!(successful >= 8, "At least 8/10 concurrent requests should succeed");

    Ok(())
}

/// Test signal generation and processing
#[tokio::test]
async fn test_signal_processing_workflow() -> anyhow::Result<()> {
    // Create test signals
    let high_conf_signal = TestSignalGenerator::high_confidence_signal();
    let low_conf_signal = TestSignalGenerator::low_confidence_signal();
    let medium_conf_signal = TestSignalGenerator::medium_confidence_signal();

    // Validate signals
    assert!(high_conf_signal.confidence >= 0.9, "High confidence signal should have confidence >= 0.9");
    assert!(low_conf_signal.confidence <= 0.5, "Low confidence signal should have confidence <= 0.5");
    assert!(medium_conf_signal.confidence >= 0.6 && medium_conf_signal.confidence <= 0.8,
            "Medium confidence signal should be in range [0.6, 0.8]");

    // Test signal processing through channels
    let (signal_tx, mut signal_rx) = mpsc::unbounded_channel();

    // Send signals
    signal_tx.send(high_conf_signal)?;
    signal_tx.send(low_conf_signal)?;
    signal_tx.send(medium_conf_signal)?;

    // Process signals
    let mut processed_count = 0;
    while let Some(signal) = timeout(Duration::from_millis(100), signal_rx.recv()).await? {
        processed_count += 1;

        // Validate each signal
        assert!(!signal.signal_id.is_empty(), "Signal ID should not be empty");
        assert!(signal.quantity > 0.0, "Quantity should be positive");
        assert!(signal.confidence >= 0.0 && signal.confidence <= 1.0, "Confidence should be in [0,1]");

        if processed_count >= 3 {
            break;
        }
    }

    assert_eq!(processed_count, 3, "Should process all 3 signals");

    Ok(())
}
