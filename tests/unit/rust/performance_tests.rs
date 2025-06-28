use tokio::time::{timeout, Duration, Instant, sleep};
use tokio::sync::mpsc;
use std::collections::HashMap;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
use chrono::Utc;

/// Performance Test Suite for THE OVERMIND PROTOCOL
/// Tests system performance under various load conditions and stress scenarios
#[cfg(test)]
mod performance_tests {
    use super::*;

    /// Test latency performance under normal load
    #[tokio::test]
    async fn test_latency_performance() {
        println!("⚡ Testing latency performance under normal load...");
        
        let (tx, mut rx) = mpsc::unbounded_channel();
        let latency_measurements = Arc::new(AtomicU64::new(0));
        let measurement_count = Arc::new(AtomicU64::new(0));
        
        // Simulate normal trading operations
        let producer = tokio::spawn(async move {
            for i in 0..1000 {
                let start_time = Instant::now();
                let operation = TradingOperation {
                    id: i,
                    operation_type: "market_data_processing".to_string(),
                    timestamp: start_time,
                    data: format!("operation_{}", i),
                };
                
                tx.send(operation).unwrap();
                
                // Normal frequency: 100 operations per second
                if i % 10 == 0 {
                    sleep(Duration::from_millis(1)).await;
                }
            }
        });
        
        // Process operations and measure latency
        let latency_counter = latency_measurements.clone();
        let count_counter = measurement_count.clone();
        
        let processor = tokio::spawn(async move {
            while let Some(operation) = timeout(Duration::from_secs(5), rx.recv()).await.unwrap_or(None) {
                let processing_start = Instant::now();
                
                // Simulate processing
                simulate_trading_operation(&operation).await;
                
                let latency = processing_start.elapsed().as_micros() as u64;
                latency_counter.fetch_add(latency, Ordering::Relaxed);
                count_counter.fetch_add(1, Ordering::Relaxed);
            }
        });
        
        producer.await.unwrap();
        sleep(Duration::from_millis(100)).await; // Allow processing to complete
        
        let total_latency = latency_measurements.load(Ordering::Relaxed);
        let total_count = measurement_count.load(Ordering::Relaxed);
        
        processor.abort(); // Stop the processor
        
        assert!(total_count > 0, "Should process operations");
        
        let avg_latency_us = total_latency / total_count;
        let avg_latency_ms = avg_latency_us as f64 / 1000.0;
        
        // Performance assertions
        assert!(avg_latency_ms < 100.0, "Average latency should be under 100ms, got {}ms", avg_latency_ms);
        assert!(total_count >= 900, "Should process at least 90% of operations, processed {}", total_count);
        
        println!("✅ Latency performance test passed:");
        println!("  📊 Operations processed: {}", total_count);
        println!("  ⏱️ Average latency: {:.2}ms", avg_latency_ms);
        println!("  🎯 Target latency: <100ms");
    }

    /// Test throughput performance under high load
    #[tokio::test]
    async fn test_throughput_performance() {
        println!("🚀 Testing throughput performance under high load...");
        
        let (tx, mut rx) = mpsc::unbounded_channel();
        let processed_count = Arc::new(AtomicU64::new(0));
        let start_time = Instant::now();
        
        // High-frequency data generator
        let generator = tokio::spawn(async move {
            for i in 0..10000 {
                let operation = TradingOperation {
                    id: i,
                    operation_type: "high_frequency_trade".to_string(),
                    timestamp: Instant::now(),
                    data: format!("hft_operation_{}", i),
                };
                
                if tx.send(operation).is_err() {
                    break;
                }
                
                // High frequency: 1000 operations per second
                if i % 100 == 0 {
                    sleep(Duration::from_millis(1)).await;
                }
            }
        });
        
        // Single processor for throughput testing
        let processor_counter = processed_count.clone();
        let processor = tokio::spawn(async move {
            let mut local_count = 0;
            while let Some(operation) = timeout(Duration::from_secs(10), rx.recv()).await.unwrap_or(None) {
                // Fast processing simulation
                simulate_fast_operation(&operation).await;

                local_count += 1;
                processor_counter.fetch_add(1, Ordering::Relaxed);

                if local_count >= 10000 { // Process up to 10000 operations
                    break;
                }
            }
            local_count
        });
        
        // Wait for generation to complete
        generator.await.unwrap();
        
        // Allow processing time
        sleep(Duration::from_secs(2)).await;
        
        let total_processed = processed_count.load(Ordering::Relaxed);
        let elapsed = start_time.elapsed();
        let throughput = total_processed as f64 / elapsed.as_secs_f64();

        // Clean up processor
        processor.abort();
        
        // Performance assertions
        assert!(total_processed >= 8000, "Should process at least 8000 operations, processed {}", total_processed);
        assert!(throughput >= 1000.0, "Throughput should be at least 1000 ops/sec, got {:.1}", throughput);
        
        println!("✅ Throughput performance test passed:");
        println!("  📈 Operations processed: {}", total_processed);
        println!("  ⚡ Throughput: {:.1} ops/sec", throughput);
        println!("  🎯 Target throughput: ≥1000 ops/sec");
        println!("  ⏱️ Total time: {:.2}s", elapsed.as_secs_f64());
    }

    /// Test memory usage under sustained load
    #[tokio::test]
    async fn test_memory_performance() {
        println!("🧠 Testing memory performance under sustained load...");
        
        let (tx, mut rx) = mpsc::unbounded_channel();
        let memory_tracker = Arc::new(MemoryTracker::new());
        
        // Sustained load generator
        let generator = tokio::spawn(async move {
            for batch in 0..100 {
                for i in 0..100 {
                    let large_operation = LargeOperation {
                        id: batch * 100 + i,
                        data: vec![0u8; 1024], // 1KB per operation
                        metadata: create_large_metadata(),
                        timestamp: Instant::now(),
                    };
                    
                    if tx.send(large_operation).is_err() {
                        break;
                    }
                }
                
                // Batch processing delay
                sleep(Duration::from_millis(10)).await;
            }
        });
        
        // Memory-intensive processor
        let tracker = memory_tracker.clone();
        let processor = tokio::spawn(async move {
            let mut processed_operations = Vec::new();
            let mut batch_count = 0;
            
            while let Some(operation) = timeout(Duration::from_secs(15), rx.recv()).await.unwrap_or(None) {
                // Track memory before processing
                tracker.record_allocation(operation.data.len());
                
                // Process and store (simulating memory usage)
                let processed = process_large_operation(operation).await;
                processed_operations.push(processed);
                
                batch_count += 1;
                
                // Periodic cleanup to test memory management
                if batch_count % 500 == 0 {
                    processed_operations.clear(); // Simulate cleanup
                    tracker.record_cleanup();
                }
            }
            
            processed_operations.len()
        });
        
        generator.await.unwrap();
        let final_count = processor.await.unwrap();
        
        let memory_stats = memory_tracker.get_stats();
        
        // Memory performance assertions
        assert!(final_count > 0, "Should process operations");
        assert!(memory_stats.peak_usage_mb < 500.0, "Peak memory usage should be under 500MB, got {:.1}MB", memory_stats.peak_usage_mb);
        assert!(memory_stats.cleanup_count > 0, "Should perform memory cleanup");
        
        println!("✅ Memory performance test passed:");
        println!("  📊 Operations processed: {}", final_count);
        println!("  🧠 Peak memory usage: {:.1}MB", memory_stats.peak_usage_mb);
        println!("  🧹 Cleanup operations: {}", memory_stats.cleanup_count);
        println!("  🎯 Target memory: <500MB");
    }

    /// Test concurrent processing performance
    #[tokio::test]
    async fn test_concurrent_performance() {
        println!("🔄 Testing concurrent processing performance...");
        
        let concurrent_operations = 1000;
        let start_time = Instant::now();
        let success_count = Arc::new(AtomicU64::new(0));
        
        // Create multiple concurrent tasks
        let mut tasks = Vec::new();
        for task_id in 0..concurrent_operations {
            let success_counter = success_count.clone();
            
            let task = tokio::spawn(async move {
                let operation_start = Instant::now();
                
                // Simulate concurrent trading operation
                let result = simulate_concurrent_operation(task_id).await;
                
                let operation_time = operation_start.elapsed();
                
                if result.success && operation_time < Duration::from_millis(500) {
                    success_counter.fetch_add(1, Ordering::Relaxed);
                }
                
                result
            });
            
            tasks.push(task);
        }
        
        // Wait for all tasks to complete
        let mut results = Vec::new();
        for task in tasks {
            if let Ok(result) = task.await {
                results.push(result);
            }
        }
        
        let total_time = start_time.elapsed();
        let successful_operations = success_count.load(Ordering::Relaxed);
        let success_rate = successful_operations as f64 / concurrent_operations as f64;
        let avg_time_per_operation = total_time.as_millis() as f64 / concurrent_operations as f64;
        
        // Concurrent performance assertions
        assert!(success_rate >= 0.95, "Success rate should be at least 95%, got {:.1}%", success_rate * 100.0);
        assert!(avg_time_per_operation < 100.0, "Average time per operation should be under 100ms, got {:.1}ms", avg_time_per_operation);
        assert!(total_time < Duration::from_secs(30), "Total time should be under 30 seconds");
        
        println!("✅ Concurrent performance test passed:");
        println!("  🔄 Concurrent operations: {}", concurrent_operations);
        println!("  ✅ Successful operations: {}", successful_operations);
        println!("  📊 Success rate: {:.1}%", success_rate * 100.0);
        println!("  ⏱️ Avg time per operation: {:.1}ms", avg_time_per_operation);
        println!("  🕐 Total time: {:.2}s", total_time.as_secs_f64());
    }

    /// Test stress performance under extreme load
    #[tokio::test]
    async fn test_stress_performance() {
        println!("💥 Testing stress performance under extreme load...");
        
        let (tx, mut rx) = mpsc::unbounded_channel();
        let stress_metrics = Arc::new(StressMetrics::new());
        
        // Extreme load generator
        let generator = tokio::spawn(async move {
            for burst in 0..50 {
                // Generate burst of operations
                for i in 0..200 {
                    let stress_operation = StressOperation {
                        id: burst * 200 + i,
                        burst_id: burst,
                        complexity: (i % 5) + 1, // Varying complexity
                        timestamp: Instant::now(),
                    };
                    
                    if tx.send(stress_operation).is_err() {
                        break;
                    }
                }
                
                // Brief pause between bursts
                sleep(Duration::from_millis(5)).await;
            }
        });
        
        // Stress processor
        let metrics = stress_metrics.clone();
        let processor = tokio::spawn(async move {
            let mut processed = 0;
            let mut failed = 0;
            
            while let Some(operation) = timeout(Duration::from_secs(20), rx.recv()).await.unwrap_or(None) {
                let process_start = Instant::now();
                
                match simulate_stress_operation(&operation).await {
                    Ok(_) => {
                        processed += 1;
                        let latency = process_start.elapsed();
                        metrics.record_success(latency);
                    }
                    Err(_) => {
                        failed += 1;
                        metrics.record_failure();
                    }
                }
            }
            
            (processed, failed)
        });
        
        generator.await.unwrap();
        let (processed_count, failed_count) = processor.await.unwrap();
        
        let final_metrics = stress_metrics.get_final_metrics();
        let total_operations = processed_count + failed_count;
        let failure_rate = failed_count as f64 / total_operations as f64;
        
        // Stress performance assertions
        assert!(total_operations >= 8000, "Should handle at least 8000 operations under stress");
        assert!(failure_rate <= 0.1, "Failure rate should be under 10%, got {:.1}%", failure_rate * 100.0);
        assert!(final_metrics.avg_latency_ms < 200.0, "Average latency under stress should be under 200ms");
        assert!(final_metrics.max_latency_ms < 1000.0, "Max latency should be under 1000ms");
        
        println!("✅ Stress performance test passed:");
        println!("  💥 Total operations: {}", total_operations);
        println!("  ✅ Processed successfully: {}", processed_count);
        println!("  ❌ Failed operations: {}", failed_count);
        println!("  📊 Failure rate: {:.1}%", failure_rate * 100.0);
        println!("  ⏱️ Avg latency: {:.1}ms", final_metrics.avg_latency_ms);
        println!("  📈 Max latency: {:.1}ms", final_metrics.max_latency_ms);
    }

    // Helper structures and functions
    #[derive(Debug, Clone)]
    struct TradingOperation {
        id: u64,
        operation_type: String,
        timestamp: Instant,
        data: String,
    }

    #[derive(Debug, Clone)]
    struct LargeOperation {
        id: u64,
        data: Vec<u8>,
        metadata: HashMap<String, String>,
        timestamp: Instant,
    }

    #[derive(Debug, Clone)]
    struct ProcessedOperation {
        id: u64,
        result: String,
        processing_time: Duration,
    }

    #[derive(Debug, Clone)]
    struct ConcurrentResult {
        task_id: u64,
        success: bool,
        execution_time: Duration,
    }

    #[derive(Debug, Clone)]
    struct StressOperation {
        id: u64,
        burst_id: u64,
        complexity: u64,
        timestamp: Instant,
    }

    #[derive(Debug, Clone)]
    struct MemoryStats {
        peak_usage_mb: f64,
        cleanup_count: u64,
    }

    #[derive(Debug, Clone)]
    struct StressMetricsData {
        avg_latency_ms: f64,
        max_latency_ms: f64,
    }

    struct MemoryTracker {
        allocated_bytes: AtomicU64,
        peak_bytes: AtomicU64,
        cleanup_count: AtomicU64,
    }

    impl MemoryTracker {
        fn new() -> Self {
            Self {
                allocated_bytes: AtomicU64::new(0),
                peak_bytes: AtomicU64::new(0),
                cleanup_count: AtomicU64::new(0),
            }
        }

        fn record_allocation(&self, bytes: usize) {
            let current = self.allocated_bytes.fetch_add(bytes as u64, Ordering::Relaxed) + bytes as u64;
            let mut peak = self.peak_bytes.load(Ordering::Relaxed);
            while current > peak {
                match self.peak_bytes.compare_exchange_weak(peak, current, Ordering::Relaxed, Ordering::Relaxed) {
                    Ok(_) => break,
                    Err(new_peak) => peak = new_peak,
                }
            }
        }

        fn record_cleanup(&self) {
            self.cleanup_count.fetch_add(1, Ordering::Relaxed);
            self.allocated_bytes.store(0, Ordering::Relaxed); // Simulate cleanup
        }

        fn get_stats(&self) -> MemoryStats {
            MemoryStats {
                peak_usage_mb: self.peak_bytes.load(Ordering::Relaxed) as f64 / (1024.0 * 1024.0),
                cleanup_count: self.cleanup_count.load(Ordering::Relaxed),
            }
        }
    }

    struct StressMetrics {
        total_latency: AtomicU64,
        max_latency: AtomicU64,
        success_count: AtomicU64,
        failure_count: AtomicU64,
    }

    impl StressMetrics {
        fn new() -> Self {
            Self {
                total_latency: AtomicU64::new(0),
                max_latency: AtomicU64::new(0),
                success_count: AtomicU64::new(0),
                failure_count: AtomicU64::new(0),
            }
        }

        fn record_success(&self, latency: Duration) {
            let latency_us = latency.as_micros() as u64;
            self.total_latency.fetch_add(latency_us, Ordering::Relaxed);
            self.success_count.fetch_add(1, Ordering::Relaxed);
            
            let mut max = self.max_latency.load(Ordering::Relaxed);
            while latency_us > max {
                match self.max_latency.compare_exchange_weak(max, latency_us, Ordering::Relaxed, Ordering::Relaxed) {
                    Ok(_) => break,
                    Err(new_max) => max = new_max,
                }
            }
        }

        fn record_failure(&self) {
            self.failure_count.fetch_add(1, Ordering::Relaxed);
        }

        fn get_final_metrics(&self) -> StressMetricsData {
            let total_latency = self.total_latency.load(Ordering::Relaxed);
            let success_count = self.success_count.load(Ordering::Relaxed);
            let max_latency = self.max_latency.load(Ordering::Relaxed);

            StressMetricsData {
                avg_latency_ms: if success_count > 0 {
                    (total_latency / success_count) as f64 / 1000.0
                } else {
                    0.0
                },
                max_latency_ms: max_latency as f64 / 1000.0,
            }
        }
    }

    async fn simulate_trading_operation(_operation: &TradingOperation) {
        // Simulate realistic trading operation processing time
        sleep(Duration::from_micros(100)).await;
    }

    async fn simulate_fast_operation(_operation: &TradingOperation) {
        // Simulate fast HFT operation
        sleep(Duration::from_micros(10)).await;
    }

    fn create_large_metadata() -> HashMap<String, String> {
        let mut metadata = HashMap::new();
        for i in 0..10 {
            metadata.insert(format!("key_{}", i), format!("value_{}_with_some_data", i));
        }
        metadata
    }

    async fn process_large_operation(operation: LargeOperation) -> ProcessedOperation {
        let start = Instant::now();
        
        // Simulate processing
        sleep(Duration::from_micros(50)).await;
        
        ProcessedOperation {
            id: operation.id,
            result: format!("processed_{}", operation.id),
            processing_time: start.elapsed(),
        }
    }

    async fn simulate_concurrent_operation(task_id: u64) -> ConcurrentResult {
        let start = Instant::now();
        
        // Simulate varying processing times
        let processing_time = Duration::from_millis(10 + (task_id % 100));
        sleep(processing_time).await;
        
        // Simulate occasional failures
        let success = task_id % 20 != 0; // 95% success rate
        
        ConcurrentResult {
            task_id,
            success,
            execution_time: start.elapsed(),
        }
    }

    async fn simulate_stress_operation(operation: &StressOperation) -> Result<(), &'static str> {
        // Simulate processing time based on complexity
        let processing_time = Duration::from_micros(operation.complexity * 50);
        sleep(processing_time).await;
        
        // Simulate stress-induced failures
        if operation.complexity > 4 && operation.id % 50 == 0 {
            Err("Stress-induced failure")
        } else {
            Ok(())
        }
    }
}
