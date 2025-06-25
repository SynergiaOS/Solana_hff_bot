//! Latency-focused benchmarks for THE OVERMIND PROTOCOL
//! 
//! Ultra-low latency performance testing with microsecond precision
//! targeting sub-millisecond execution times for HFT operations

use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use std::time::{Duration, Instant};
use tokio::runtime::Runtime;
use std::sync::{Arc, Mutex};
use std::collections::VecDeque;

/// Benchmark ultra-low latency operations
fn benchmark_ultra_low_latency(c: &mut Criterion) {
    let mut group = c.benchmark_group("ultra_low_latency");
    
    // Set measurement time to get more precise results for very fast operations
    group.measurement_time(Duration::from_secs(10));
    group.sample_size(1000);
    
    // Test atomic operations
    group.bench_function("atomic_increment", |b| {
        use std::sync::atomic::{AtomicU64, Ordering};
        let counter = AtomicU64::new(0);
        b.iter(|| {
            black_box(counter.fetch_add(1, Ordering::Relaxed))
        })
    });
    
    // Test mutex lock/unlock overhead
    group.bench_function("mutex_lock_unlock", |b| {
        let mutex = Arc::new(Mutex::new(0u64));
        b.iter(|| {
            let mut guard = mutex.lock().unwrap();
            *guard += 1;
            black_box(*guard)
        })
    });
    
    // Test channel send/receive latency
    group.bench_function("mpsc_channel_latency", |b| {
        let (tx, rx) = std::sync::mpsc::channel();
        b.iter(|| {
            tx.send(42).unwrap();
            black_box(rx.recv().unwrap())
        })
    });
    
    // Test memory allocation latency
    group.bench_function("vec_allocation_small", |b| {
        b.iter(|| {
            let vec: Vec<u64> = Vec::with_capacity(10);
            black_box(vec)
        })
    });
    
    group.bench_function("vec_allocation_medium", |b| {
        b.iter(|| {
            let vec: Vec<u64> = Vec::with_capacity(1000);
            black_box(vec)
        })
    });
    
    group.finish();
}

/// Benchmark network-related latency operations
fn benchmark_network_latency_simulation(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let mut group = c.benchmark_group("network_latency_simulation");
    
    // Simulate different network latencies
    for latency_us in [1, 10, 100, 1000].iter() {
        group.bench_with_input(
            BenchmarkId::new("simulated_network_call", latency_us),
            latency_us,
            |b, &latency_us| {
                b.iter(|| {
                    rt.block_on(async {
                        tokio::time::sleep(Duration::from_micros(latency_us)).await;
                        black_box(42)
                    })
                })
            },
        );
    }
    
    // Test concurrent network calls
    group.bench_function("concurrent_network_calls_10", |b| {
        b.iter(|| {
            rt.block_on(async {
                let handles: Vec<_> = (0..10)
                    .map(|_| {
                        tokio::spawn(async {
                            tokio::time::sleep(Duration::from_micros(100)).await;
                            42
                        })
                    })
                    .collect();

                let results: Vec<_> = futures::future::join_all(handles).await;
                black_box(results)
            })
        })
    });
    
    group.finish();
}

/// Benchmark data structure access patterns for HFT
fn benchmark_hft_data_structures(c: &mut Criterion) {
    let mut group = c.benchmark_group("hft_data_structures");
    
    // Test order book operations
    let mut order_book: VecDeque<(f64, f64)> = VecDeque::new();
    for i in 0..1000 {
        order_book.push_back((100.0 + i as f64 * 0.01, 10.0));
    }
    
    group.bench_function("order_book_top_access", |b| {
        b.iter(|| {
            black_box(order_book.front())
        })
    });
    
    group.bench_function("order_book_insert_front", |b| {
        let mut book = order_book.clone();
        b.iter(|| {
            book.push_front((99.99, 5.0));
            black_box(book.pop_front())
        })
    });
    
    // Test price level updates
    let price_levels: Vec<(f64, f64)> = (0..100)
        .map(|i| (100.0 + i as f64 * 0.01, 10.0))
        .collect();
    
    group.bench_function("price_level_update", |b| {
        b.iter(|| {
            let mut levels = price_levels.clone();
            if let Some(level) = levels.get_mut(50) {
                level.1 += 1.0;
                black_box(level);
            }
            black_box(levels)
        })
    });
    
    // Test binary search for price insertion
    group.bench_function("binary_search_price_insertion", |b| {
        b.iter(|| {
            let target_price = 100.50;
            let result = price_levels.binary_search_by(|&(price, _)| {
                price.partial_cmp(&target_price).unwrap()
            });
            black_box(result)
        })
    });
    
    group.finish();
}

/// Benchmark memory access patterns
fn benchmark_memory_access_patterns(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_access_patterns");
    
    // Test sequential vs random access
    let data: Vec<u64> = (0..10000).collect();
    
    group.bench_function("sequential_access", |b| {
        b.iter(|| {
            let mut sum = 0u64;
            for i in 0..1000 {
                sum += data[i];
            }
            black_box(sum)
        })
    });
    
    group.bench_function("random_access", |b| {
        use rand::Rng;
        let mut rng = rand::thread_rng();
        let indices: Vec<usize> = (0..1000).map(|_| rng.gen_range(0..data.len())).collect();
        
        b.iter(|| {
            let mut sum = 0u64;
            for &idx in &indices {
                sum += data[idx];
            }
            black_box(sum)
        })
    });
    
    // Test cache-friendly vs cache-unfriendly patterns
    group.bench_function("cache_friendly_stride_1", |b| {
        b.iter(|| {
            let mut sum = 0u64;
            for i in (0..1000).step_by(1) {
                sum += data[i];
            }
            black_box(sum)
        })
    });
    
    group.bench_function("cache_unfriendly_stride_64", |b| {
        b.iter(|| {
            let mut sum = 0u64;
            for i in (0..1000).step_by(64) {
                if i < data.len() {
                    sum += data[i];
                }
            }
            black_box(sum)
        })
    });
    
    group.finish();
}

/// Benchmark floating point operations critical for trading
fn benchmark_trading_math_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("trading_math_operations");
    
    let prices: Vec<f64> = (0..1000).map(|i| 100.0 + i as f64 * 0.01).collect();
    let volumes: Vec<f64> = (0..1000).map(|i| 10.0 + i as f64 * 0.1).collect();
    
    // Test VWAP calculation
    group.bench_function("vwap_calculation", |b| {
        b.iter(|| {
            let mut total_value = 0.0;
            let mut total_volume = 0.0;
            
            for i in 0..100 {
                total_value += prices[i] * volumes[i];
                total_volume += volumes[i];
            }
            
            let vwap = if total_volume > 0.0 {
                total_value / total_volume
            } else {
                0.0
            };
            
            black_box(vwap)
        })
    });
    
    // Test moving average calculation
    group.bench_function("moving_average_calculation", |b| {
        b.iter(|| {
            let window_size = 20;
            let mut sum = 0.0;
            
            for i in 0..window_size {
                sum += prices[i];
            }
            
            let ma = sum / window_size as f64;
            black_box(ma)
        })
    });
    
    // Test volatility calculation
    group.bench_function("volatility_calculation", |b| {
        b.iter(|| {
            let window_size = 20;
            let mut sum = 0.0;
            let mut sum_sq = 0.0;
            
            for i in 0..window_size {
                let price = prices[i];
                sum += price;
                sum_sq += price * price;
            }
            
            let mean = sum / window_size as f64;
            let variance = (sum_sq / window_size as f64) - (mean * mean);
            let volatility = variance.sqrt();
            
            black_box(volatility)
        })
    });
    
    // Test percentage change calculation
    group.bench_function("percentage_change_calculation", |b| {
        b.iter(|| {
            let mut changes = Vec::with_capacity(99);
            for i in 1..100 {
                let change = (prices[i] - prices[i-1]) / prices[i-1] * 100.0;
                changes.push(change);
            }
            black_box(changes)
        })
    });
    
    group.finish();
}

/// Benchmark time-critical operations
fn benchmark_time_critical_operations(c: &mut Criterion) {
    let mut group = c.benchmark_group("time_critical_operations");
    
    // Test timestamp generation
    group.bench_function("timestamp_generation", |b| {
        b.iter(|| {
            let now = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            black_box(now)
        })
    });
    
    // Test high-precision timing
    group.bench_function("high_precision_timing", |b| {
        b.iter(|| {
            let start = Instant::now();
            // Simulate minimal work
            black_box(std::hint::black_box(42));
            let elapsed = start.elapsed();
            black_box(elapsed.as_nanos())
        })
    });
    
    // Test deadline checking
    group.bench_function("deadline_checking", |b| {
        let deadline = Instant::now() + Duration::from_millis(100);
        b.iter(|| {
            let now = Instant::now();
            let is_expired = now > deadline;
            black_box(is_expired)
        })
    });
    
    group.finish();
}

criterion_group!(
    latency_benches,
    benchmark_ultra_low_latency,
    benchmark_network_latency_simulation,
    benchmark_hft_data_structures,
    benchmark_memory_access_patterns,
    benchmark_trading_math_operations,
    benchmark_time_critical_operations
);

criterion_main!(latency_benches);
