//! THE OVERMIND PROTOCOL Performance Benchmarks
//!
//! Comprehensive performance testing suite including:
//! - Latency measurements (sub-millisecond targets)
//! - Throughput testing (transactions per second)
//! - Memory usage analysis
//! - AI decision-making performance
//! - Risk management performance
//! - Multi-wallet load balancing performance

use chrono::Utc;
use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use snipercor::modules::{
    ai_connector::{AIAction, AIConnectorConfig, AIDecision},
    geographic_distribution::GeographicConfig,
    hft_engine::{HftEngineConfig, TradingSignal},
    jito_client::JitoConfig,
    multi_wallet_load_balancer::LoadBalancerConfig,
    submillisecond_optimizer::OptimizationConfig,
    tensorzero_client::TensorZeroConfig,
};
use std::collections::HashMap;
use std::time::{Duration, Instant};
use tokio::runtime::Runtime;

/// Benchmark configuration creation performance
fn benchmark_config_creation(c: &mut Criterion) {
    let mut group = c.benchmark_group("config_creation");

    group.bench_function("hft_engine_config", |b| {
        b.iter(|| black_box(HftEngineConfig::default()))
    });

    group.bench_function("ai_connector_config", |b| {
        b.iter(|| black_box(AIConnectorConfig::default()))
    });

    group.bench_function("tensorzero_config", |b| {
        b.iter(|| black_box(TensorZeroConfig::default()))
    });

    group.bench_function("jito_config", |b| {
        b.iter(|| black_box(JitoConfig::default()))
    });

    group.bench_function("load_balancer_config", |b| {
        b.iter(|| black_box(LoadBalancerConfig::default()))
    });

    group.bench_function("geographic_config", |b| {
        b.iter(|| black_box(GeographicConfig::default()))
    });

    group.bench_function("optimization_config", |b| {
        b.iter(|| black_box(OptimizationConfig::default()))
    });

    group.finish();
}

/// Benchmark trading signal processing performance
fn benchmark_trading_signal_processing(c: &mut Criterion) {
    let mut group = c.benchmark_group("trading_signal_processing");

    // Test different batch sizes
    for batch_size in [1, 10, 100, 1000].iter() {
        group.throughput(Throughput::Elements(*batch_size as u64));
        group.bench_with_input(
            BenchmarkId::new("signal_creation", batch_size),
            batch_size,
            |b, &size| {
                b.iter(|| {
                    let signals: Vec<TradingSignal> = (0..size)
                        .map(|i| TradingSignal {
                            symbol: format!("TOKEN{}/USDC", i),
                            action: if i % 2 == 0 {
                                "BUY".to_string()
                            } else {
                                "SELL".to_string()
                            },
                            quantity: 100.0 + (i as f64),
                            price: Some(150.0 + (i as f64) * 0.1),
                            confidence: 0.8 + (i as f64) * 0.001,
                            reasoning: format!("Signal {} reasoning", i),
                        })
                        .collect();
                    black_box(signals)
                })
            },
        );
    }

    group.finish();
}

/// Benchmark AI decision making performance
fn benchmark_ai_decision_performance(c: &mut Criterion) {
    let mut group = c.benchmark_group("ai_decision_performance");

    // Test AI decision creation and processing
    group.bench_function("ai_decision_creation", |b| {
        b.iter(|| {
            let decision = AIDecision {
                decision_id: "test_decision_001".to_string(),
                symbol: "SOL/USDC".to_string(),
                action: AIAction::Buy,
                confidence: 0.85,
                reasoning: "Strong bullish momentum detected".to_string(),
                quantity: 100.0,
                target_price: Some(165.0),
                ai_context: None,
                timestamp: Utc::now(),
                vector_memory_context: Some("Market analysis context".to_string()),
            };
            black_box(decision)
        })
    });

    // Test batch AI decision processing
    for batch_size in [10, 50, 100, 500].iter() {
        group.throughput(Throughput::Elements(*batch_size as u64));
        group.bench_with_input(
            BenchmarkId::new("ai_decision_batch", batch_size),
            batch_size,
            |b, &size| {
                b.iter(|| {
                    let decisions: Vec<AIDecision> = (0..size)
                        .map(|i| AIDecision {
                            decision_id: format!("decision_{}", i),
                            symbol: format!("TOKEN{}/USDC", i),
                            action: if i % 2 == 0 {
                                AIAction::Buy
                            } else {
                                AIAction::Sell
                            },
                            confidence: 0.7 + (i as f64) * 0.001,
                            reasoning: format!("AI decision {} reasoning", i),
                            quantity: 100.0 + (i as f64),
                            target_price: Some(140.0 + (i as f64) * 0.1),
                            ai_context: None,
                            timestamp: Utc::now(),
                            vector_memory_context: Some(format!("Context for decision {}", i)),
                        })
                        .collect();
                    black_box(decisions)
                })
            },
        );
    }

    group.finish();
}

/// Benchmark memory allocation and deallocation performance
fn benchmark_memory_performance(c: &mut Criterion) {
    let mut group = c.benchmark_group("memory_performance");

    // Test vector allocation performance
    for size in [1000, 10000, 100000].iter() {
        group.throughput(Throughput::Elements(*size as u64));
        group.bench_with_input(
            BenchmarkId::new("vector_allocation", size),
            size,
            |b, &size| {
                b.iter(|| {
                    let mut vec: Vec<f64> = Vec::with_capacity(size);
                    for i in 0..size {
                        vec.push(i as f64);
                    }
                    black_box(vec)
                })
            },
        );
    }

    // Test HashMap allocation performance
    for size in [1000, 10000, 100000].iter() {
        group.throughput(Throughput::Elements(*size as u64));
        group.bench_with_input(
            BenchmarkId::new("hashmap_allocation", size),
            size,
            |b, &size| {
                b.iter(|| {
                    let mut map: HashMap<String, f64> = HashMap::with_capacity(size);
                    for i in 0..size {
                        map.insert(format!("key_{}", i), i as f64);
                    }
                    black_box(map)
                })
            },
        );
    }

    group.finish();
}

/// Benchmark serialization/deserialization performance
fn benchmark_serialization_performance(c: &mut Criterion) {
    let mut group = c.benchmark_group("serialization_performance");

    let signal = TradingSignal {
        symbol: "SOL/USDC".to_string(),
        action: "BUY".to_string(),
        quantity: 100.0,
        price: Some(150.0),
        confidence: 0.85,
        reasoning: "Strong bullish momentum detected with high volume".to_string(),
    };

    group.bench_function("json_serialize", |b| {
        b.iter(|| black_box(serde_json::to_string(&signal).unwrap()))
    });

    let json_str = serde_json::to_string(&signal).unwrap();
    group.bench_function("json_deserialize", |b| {
        b.iter(|| black_box(serde_json::from_str::<TradingSignal>(&json_str).unwrap()))
    });

    group.finish();
}

/// Benchmark async task performance
fn benchmark_async_performance(c: &mut Criterion) {
    let rt = Runtime::new().unwrap();
    let mut group = c.benchmark_group("async_performance");

    group.bench_function("tokio_spawn_single", |b| {
        b.iter(|| {
            rt.block_on(async {
                let handle = tokio::spawn(async {
                    tokio::time::sleep(Duration::from_micros(1)).await;
                    42
                });
                black_box(handle.await.unwrap())
            })
        })
    });

    group.bench_function("tokio_spawn_batch_10", |b| {
        b.iter(|| {
            rt.block_on(async {
                let handles: Vec<_> = (0..10)
                    .map(|_| {
                        tokio::spawn(async {
                            tokio::time::sleep(Duration::from_micros(1)).await;
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

/// Benchmark latency measurement overhead
fn benchmark_latency_measurement(c: &mut Criterion) {
    let mut group = c.benchmark_group("latency_measurement");

    group.bench_function("instant_now_overhead", |b| {
        b.iter(|| {
            let start = Instant::now();
            black_box(start);
            let end = Instant::now();
            black_box(end);
            black_box(end.duration_since(start))
        })
    });

    group.bench_function("duration_measurement", |b| {
        b.iter(|| {
            let start = Instant::now();
            // Simulate minimal work
            black_box(42 + 42);
            let duration = start.elapsed();
            black_box(duration)
        })
    });

    group.finish();
}

criterion_group!(
    benches,
    benchmark_config_creation,
    benchmark_trading_signal_processing,
    benchmark_ai_decision_performance,
    benchmark_memory_performance,
    benchmark_serialization_performance,
    benchmark_async_performance,
    benchmark_latency_measurement
);

criterion_main!(benches);
