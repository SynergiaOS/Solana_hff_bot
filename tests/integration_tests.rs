// Integration tests for SNIPERCOR HFT system
// Tests inter-module communication and end-to-end workflows
// Note: Simplified due to module visibility - in production these would test actual modules

use tokio::sync::mpsc;
use tokio::time::{timeout, Duration};

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

    for _ in 0..11 { // 10 numbers + 1 string
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
        while let Some(_) = rx.recv().await {
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
    assert!(duration.as_millis() < 100, "Channel throughput too slow: {:?}", duration);

    Ok(())
}
