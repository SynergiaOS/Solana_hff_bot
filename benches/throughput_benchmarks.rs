//! Throughput benchmarks for THE OVERMIND PROTOCOL
//!
//! High-throughput performance testing measuring transactions per second,
//! data processing rates, and system scalability under load

#![allow(dead_code)]

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use snipercor::modules::hft_engine::TradingSignal;
use std::collections::HashMap;
use std::time::Duration;
use tokio::runtime::Runtime;

/// Benchmark transaction processing throughput
fn benchmark_transaction_throughput(c: &mut Criterion) {
    let mut group = c.benchmark_group("transaction_throughput");

    // Test different batch sizes for transaction processing
    for batch_size in [100, 1000, 10000, 100000].iter() {
        group.throughput(Throughput::Elements(*batch_size as u64));
        group.bench_with_input(
            BenchmarkId::new("process_transactions", batch_size),
            batch_size,
            |b, &size| {
                let transactions: Vec<TradingSignal> = (0..size)
                    .map(|i| TradingSignal {
                        symbol: format!("TOKEN{}/USDC", i % 100), // Limit symbols for realism
                        action: if i % 2 == 0 {
                            "BUY".to_string()
                        } else {
                            "SELL".to_string()
                        },
                        quantity: 100.0 + (i as f64) % 1000.0,
                        price: Some(150.0 + (i as f64) % 100.0),
                        confidence: 0.7 + ((i as f64) % 30.0) / 100.0,
                        reasoning: format!("Transaction {} reasoning", i),
                    })
                    .collect();

                b.iter(|| {
                    let mut processed = 0;
                    for transaction in &transactions {
                        // Simulate transaction processing
                        if transaction.confidence > 0.8 {
                            processed += 1;
                        }
                        black_box(transaction);
                    }
                    black_box(processed)
                })
            },
        );
    }

    group.finish();
}

/// Benchmark market data processing throughput
fn benchmark_market_data_throughput(c: &mut Criterion) {
    let mut group = c.benchmark_group("market_data_throughput");

    // Simulate market data updates
    #[derive(Clone)]
    struct MarketUpdate {
        symbol: String,
        price: f64,
        volume: f64,
        timestamp: u64,
    }

    for updates_per_second in [1000, 10000, 100000, 1000000].iter() {
        group.throughput(Throughput::Elements(*updates_per_second as u64));
        group.bench_with_input(
            BenchmarkId::new("process_market_updates", updates_per_second),
            updates_per_second,
            |b, &rate| {
                let updates: Vec<MarketUpdate> = (0..rate)
                    .map(|i| MarketUpdate {
                        symbol: format!("TOKEN{}", i % 100),
                        price: 100.0 + (i as f64) % 50.0,
                        volume: 1000.0 + (i as f64) % 5000.0,
                        timestamp: i as u64,
                    })
                    .collect();

                b.iter(|| {
                    let mut price_map: HashMap<String, f64> = HashMap::new();
                    let mut volume_sum = 0.0;

                    for update in &updates {
                        price_map.insert(update.symbol.clone(), update.price);
                        volume_sum += update.volume;
                        black_box(&update);
                    }

                    black_box((price_map.len(), volume_sum))
                })
            },
        );
    }

    group.finish();
}

/// Benchmark concurrent processing throughput
fn benchmark_concurrent_throughput(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let mut group = c.benchmark_group("concurrent_throughput");

    // Test different levels of concurrency
    for concurrency in [1, 4, 8, 16, 32].iter() {
        group.bench_with_input(
            BenchmarkId::new("concurrent_tasks", concurrency),
            concurrency,
            |b, &concurrency| {
                b.iter(|| {
                    rt.block_on(async {
                        let handles: Vec<_> = (0..concurrency)
                            .map(|i| {
                                tokio::spawn(async move {
                                    // Simulate CPU-intensive work
                                    let mut sum = 0u64;
                                    for j in 0..1000 {
                                        sum += (i * 1000 + j) as u64;
                                    }
                                    sum
                                })
                            })
                            .collect();

                        let results: Vec<_> = futures::future::join_all(handles).await;
                        let total: u64 = results.into_iter().map(|r| r.unwrap()).sum();
                        black_box(total)
                    })
                })
            },
        );
    }

    group.finish();
}

/// Benchmark memory throughput operations
fn benchmark_memory_throughput(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_throughput");

    // Test memory copy throughput
    for size_mb in [1, 10, 100].iter() {
        let size_bytes = size_mb * 1024 * 1024;
        group.throughput(Throughput::Bytes(size_bytes as u64));
        group.bench_with_input(
            BenchmarkId::new("memory_copy", size_mb),
            &size_bytes,
            |b, &size| {
                let source: Vec<u8> = vec![42; size];
                b.iter(|| {
                    let destination = source.clone();
                    black_box(destination)
                })
            },
        );
    }

    // Test memory allocation throughput
    for alloc_count in [1000, 10000, 100000].iter() {
        group.throughput(Throughput::Elements(*alloc_count as u64));
        group.bench_with_input(
            BenchmarkId::new("memory_allocations", alloc_count),
            alloc_count,
            |b, &count| {
                b.iter(|| {
                    let mut allocations = Vec::new();
                    for i in 0..count {
                        let vec: Vec<u64> = vec![i as u64; 100];
                        allocations.push(vec);
                    }
                    black_box(allocations)
                })
            },
        );
    }

    group.finish();
}

/// Benchmark serialization throughput
fn benchmark_serialization_throughput(c: &mut Criterion) {
    let mut group = c.benchmark_group("serialization_throughput");

    // Create test data
    let signals: Vec<TradingSignal> = (0..10000)
        .map(|i| TradingSignal {
            symbol: format!("TOKEN{}/USDC", i % 100),
            action: if i % 2 == 0 {
                "BUY".to_string()
            } else {
                "SELL".to_string()
            },
            quantity: 100.0 + (i as f64),
            price: Some(150.0 + (i as f64) * 0.01),
            confidence: 0.8 + (i as f64) * 0.0001,
            reasoning: format!("Signal {} with detailed reasoning and analysis", i),
        })
        .collect();

    // Test JSON serialization throughput
    for batch_size in [100, 1000, 10000].iter() {
        group.throughput(Throughput::Elements(*batch_size as u64));
        group.bench_with_input(
            BenchmarkId::new("json_serialize", batch_size),
            batch_size,
            |b, &size| {
                let batch = &signals[0..size];
                b.iter(|| {
                    let json = serde_json::to_string(batch).unwrap();
                    black_box(json)
                })
            },
        );
    }

    // Test JSON deserialization throughput
    let json_batches: Vec<String> = [100, 1000, 10000]
        .iter()
        .map(|&size| serde_json::to_string(&signals[0..size]).unwrap())
        .collect();

    for (i, batch_size) in [100, 1000, 10000].iter().enumerate() {
        group.throughput(Throughput::Elements(*batch_size as u64));
        group.bench_with_input(
            BenchmarkId::new("json_deserialize", batch_size),
            &json_batches[i],
            |b, json_str| {
                b.iter(|| {
                    let signals: Vec<TradingSignal> = serde_json::from_str(json_str).unwrap();
                    black_box(signals)
                })
            },
        );
    }

    group.finish();
}

/// Benchmark network simulation throughput
fn benchmark_network_simulation_throughput(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let mut group = c.benchmark_group("network_simulation_throughput");

    // Simulate different network request rates
    for requests_per_batch in [10, 100, 1000].iter() {
        group.throughput(Throughput::Elements(*requests_per_batch as u64));
        group.bench_with_input(
            BenchmarkId::new("simulated_network_requests", requests_per_batch),
            requests_per_batch,
            |b, &count| {
                b.iter(|| {
                    rt.block_on(async {
                        let handles: Vec<_> = (0..count)
                            .map(|i| {
                                tokio::spawn(async move {
                                    // Simulate network request processing
                                    tokio::time::sleep(Duration::from_micros(10)).await;
                                    format!("Response {}", i)
                                })
                            })
                            .collect();

                        let responses: Vec<_> = futures::future::join_all(handles).await;
                        black_box(responses.len())
                    })
                })
            },
        );
    }

    group.finish();
}

/// Benchmark data aggregation throughput
fn benchmark_data_aggregation_throughput(c: &mut Criterion) {
    let mut group = c.benchmark_group("data_aggregation_throughput");

    // Create large dataset for aggregation
    let data: Vec<(String, f64, f64)> = (0..100000)
        .map(|i| {
            (
                format!("SYMBOL_{}", i % 100),
                100.0 + (i as f64) % 50.0,    // price
                1000.0 + (i as f64) % 5000.0, // volume
            )
        })
        .collect();

    // Test aggregation by symbol
    for chunk_size in [1000, 10000, 100000].iter() {
        group.throughput(Throughput::Elements(*chunk_size as u64));
        group.bench_with_input(
            BenchmarkId::new("aggregate_by_symbol", chunk_size),
            chunk_size,
            |b, &size| {
                let chunk = &data[0..size];
                b.iter(|| {
                    let mut aggregated: HashMap<String, (f64, f64, u32)> = HashMap::new();

                    for (symbol, price, volume) in chunk {
                        let entry = aggregated.entry(symbol.clone()).or_insert((0.0, 0.0, 0));
                        entry.0 += price;
                        entry.1 += volume;
                        entry.2 += 1;
                    }

                    // Calculate averages
                    let averages: HashMap<String, (f64, f64)> = aggregated
                        .into_iter()
                        .map(|(symbol, (price_sum, volume_sum, count))| {
                            (
                                symbol,
                                (price_sum / count as f64, volume_sum / count as f64),
                            )
                        })
                        .collect();

                    black_box(averages)
                })
            },
        );
    }

    group.finish();
}

criterion_group!(
    throughput_benches,
    benchmark_transaction_throughput,
    benchmark_market_data_throughput,
    benchmark_concurrent_throughput,
    benchmark_memory_throughput,
    benchmark_serialization_throughput,
    benchmark_network_simulation_throughput,
    benchmark_data_aggregation_throughput
);

criterion_main!(throughput_benches);
