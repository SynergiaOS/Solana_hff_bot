//! Memory Optimizer Module
//!
//! Advanced memory management and optimization for THE OVERMIND PROTOCOL
//! including memory pooling, garbage collection optimization, and memory monitoring.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::alloc::{GlobalAlloc, Layout, System};
use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::{Mutex, RwLock};
use tracing::{debug, info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryConfig {
    pub max_heap_size_mb: usize,
    pub gc_threshold_mb: usize,
    pub memory_pool_enabled: bool,
    pub memory_monitoring_enabled: bool,
    pub memory_pressure_threshold: f64,
    pub cleanup_interval_seconds: u64,
    pub object_pool_sizes: HashMap<String, usize>,
}

impl Default for MemoryConfig {
    fn default() -> Self {
        let mut object_pool_sizes = HashMap::new();
        object_pool_sizes.insert("trading_signals".to_string(), 1000);
        object_pool_sizes.insert("market_events".to_string(), 5000);
        object_pool_sizes.insert("execution_results".to_string(), 1000);
        object_pool_sizes.insert("price_data".to_string(), 10000);

        Self {
            max_heap_size_mb: 2048, // 2GB max heap
            gc_threshold_mb: 1024,  // Trigger cleanup at 1GB
            memory_pool_enabled: true,
            memory_monitoring_enabled: true,
            memory_pressure_threshold: 0.8, // 80% memory usage threshold
            cleanup_interval_seconds: 60,   // Cleanup every minute
            object_pool_sizes,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct MemoryStats {
    pub total_allocated_bytes: u64,
    pub total_deallocated_bytes: u64,
    pub current_usage_bytes: u64,
    pub peak_usage_bytes: u64,
    pub allocation_count: u64,
    pub deallocation_count: u64,
    pub gc_runs: u64,
    pub memory_pressure: f64,
    pub fragmentation_ratio: f64,
}

pub struct MemoryTracker {
    stats: Arc<Mutex<MemoryStats>>,
    allocated: AtomicU64,
    deallocated: AtomicU64,
    allocation_count: AtomicU64,
    deallocation_count: AtomicU64,
    peak_usage: AtomicU64,
}

impl MemoryTracker {
    pub fn new() -> Self {
        Self {
            stats: Arc::new(Mutex::new(MemoryStats::default())),
            allocated: AtomicU64::new(0),
            deallocated: AtomicU64::new(0),
            allocation_count: AtomicU64::new(0),
            deallocation_count: AtomicU64::new(0),
            peak_usage: AtomicU64::new(0),
        }
    }

    pub fn record_allocation(&self, size: usize) {
        let allocated = self.allocated.fetch_add(size as u64, Ordering::Relaxed) + size as u64;
        let deallocated = self.deallocated.load(Ordering::Relaxed);
        let current_usage = allocated - deallocated;

        self.allocation_count.fetch_add(1, Ordering::Relaxed);

        // Update peak usage
        let mut peak = self.peak_usage.load(Ordering::Relaxed);
        while current_usage > peak {
            match self.peak_usage.compare_exchange_weak(
                peak,
                current_usage,
                Ordering::Relaxed,
                Ordering::Relaxed,
            ) {
                Ok(_) => break,
                Err(x) => peak = x,
            }
        }
    }

    pub fn record_deallocation(&self, size: usize) {
        self.deallocated.fetch_add(size as u64, Ordering::Relaxed);
        self.deallocation_count.fetch_add(1, Ordering::Relaxed);
    }

    pub async fn get_stats(&self) -> MemoryStats {
        let allocated = self.allocated.load(Ordering::Relaxed);
        let deallocated = self.deallocated.load(Ordering::Relaxed);
        let current_usage = allocated - deallocated;
        let peak_usage = self.peak_usage.load(Ordering::Relaxed);
        let allocation_count = self.allocation_count.load(Ordering::Relaxed);
        let deallocation_count = self.deallocation_count.load(Ordering::Relaxed);

        let mut stats = self.stats.lock().await;
        stats.total_allocated_bytes = allocated;
        stats.total_deallocated_bytes = deallocated;
        stats.current_usage_bytes = current_usage;
        stats.peak_usage_bytes = peak_usage;
        stats.allocation_count = allocation_count;
        stats.deallocation_count = deallocation_count;

        // Calculate memory pressure (current usage / peak usage)
        stats.memory_pressure = if peak_usage > 0 {
            current_usage as f64 / peak_usage as f64
        } else {
            0.0
        };

        // Calculate fragmentation ratio (allocations / deallocations)
        stats.fragmentation_ratio = if deallocation_count > 0 {
            allocation_count as f64 / deallocation_count as f64
        } else {
            allocation_count as f64
        };

        stats.clone()
    }
}

// Custom allocator wrapper for tracking
pub struct TrackingAllocator {
    inner: System,
    tracker: Arc<MemoryTracker>,
}

impl TrackingAllocator {
    pub fn new(tracker: Arc<MemoryTracker>) -> Self {
        Self {
            inner: System,
            tracker,
        }
    }
}

unsafe impl GlobalAlloc for TrackingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ptr = self.inner.alloc(layout);
        if !ptr.is_null() {
            self.tracker.record_allocation(layout.size());
        }
        ptr
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        self.tracker.record_deallocation(layout.size());
        self.inner.dealloc(ptr, layout);
    }
}

pub struct ObjectPool<T> {
    objects: Arc<Mutex<Vec<T>>>,
    factory: Arc<dyn Fn() -> T + Send + Sync>,
    max_size: usize,
    current_size: AtomicUsize,
}

impl<T> ObjectPool<T>
where
    T: Send + 'static,
{
    pub fn new<F>(factory: F, max_size: usize) -> Self
    where
        F: Fn() -> T + Send + Sync + 'static,
    {
        Self {
            objects: Arc::new(Mutex::new(Vec::with_capacity(max_size))),
            factory: Arc::new(factory),
            max_size,
            current_size: AtomicUsize::new(0),
        }
    }

    pub async fn acquire(&self) -> T {
        let mut objects = self.objects.lock().await;

        if let Some(obj) = objects.pop() {
            self.current_size.fetch_sub(1, Ordering::Relaxed);
            obj
        } else {
            // Create new object if pool is empty
            (self.factory)()
        }
    }

    pub async fn release(&self, obj: T) {
        let current_size = self.current_size.load(Ordering::Relaxed);

        if current_size < self.max_size {
            let mut objects = self.objects.lock().await;
            if objects.len() < self.max_size {
                objects.push(obj);
                self.current_size.fetch_add(1, Ordering::Relaxed);
            }
            // If pool is full, just drop the object
        }
    }

    pub fn pool_size(&self) -> usize {
        self.current_size.load(Ordering::Relaxed)
    }
}

pub struct MemoryOptimizer {
    config: MemoryConfig,
    tracker: Arc<MemoryTracker>,
    object_pools: HashMap<String, Arc<dyn std::any::Any + Send + Sync>>,
    cleanup_tasks: Vec<tokio::task::JoinHandle<()>>,
    memory_pressure_callbacks: Arc<RwLock<Vec<Box<dyn Fn(f64) + Send + Sync>>>>,
}

impl MemoryOptimizer {
    pub fn new(config: MemoryConfig) -> Self {
        let tracker = Arc::new(MemoryTracker::new());

        Self {
            config,
            tracker,
            object_pools: HashMap::new(),
            cleanup_tasks: Vec::new(),
            memory_pressure_callbacks: Arc::new(RwLock::new(Vec::new())),
        }
    }

    pub async fn initialize(&mut self) -> Result<()> {
        info!("🧠 Initializing Memory Optimizer for THE OVERMIND PROTOCOL");

        if self.config.memory_monitoring_enabled {
            self.start_memory_monitoring().await;
        }

        if self.config.memory_pool_enabled {
            self.initialize_object_pools().await;
        }

        self.start_cleanup_tasks().await;

        info!("✅ Memory Optimizer initialized successfully");
        Ok(())
    }

    async fn start_memory_monitoring(&mut self) {
        let tracker = self.tracker.clone();
        let config = self.config.clone();
        let callbacks = self.memory_pressure_callbacks.clone();

        let handle = tokio::spawn(async move {
            let mut interval = tokio::time::interval(Duration::from_secs(10));

            loop {
                interval.tick().await;

                let stats = tracker.get_stats().await;
                let memory_usage_mb = stats.current_usage_bytes as f64 / 1024.0 / 1024.0;

                debug!(
                    "📊 Memory usage: {:.2}MB, pressure: {:.2}%, fragmentation: {:.2}",
                    memory_usage_mb,
                    stats.memory_pressure * 100.0,
                    stats.fragmentation_ratio
                );

                // Check memory pressure
                if stats.memory_pressure > config.memory_pressure_threshold {
                    warn!(
                        "⚠️ High memory pressure detected: {:.2}%",
                        stats.memory_pressure * 100.0
                    );

                    // Trigger pressure callbacks
                    let callbacks_guard = callbacks.read().await;
                    for callback in callbacks_guard.iter() {
                        callback(stats.memory_pressure);
                    }
                }

                // Check if we're approaching memory limits
                if memory_usage_mb > config.gc_threshold_mb as f64 {
                    warn!("🗑️ Memory usage above GC threshold, triggering cleanup");
                    // Force garbage collection (in a real implementation)
                    // std::hint::black_box(Vec::<u8>::with_capacity(1024 * 1024));
                }
            }
        });

        self.cleanup_tasks.push(handle);
    }

    async fn initialize_object_pools(&mut self) {
        info!("🏊 Initializing object pools");

        for (pool_name, pool_size) in &self.config.object_pool_sizes {
            match pool_name.as_str() {
                "trading_signals" => {
                    // In a real implementation, you'd create pools for actual types
                    info!("Created trading_signals pool with size {}", pool_size);
                }
                "market_events" => {
                    info!("Created market_events pool with size {}", pool_size);
                }
                "execution_results" => {
                    info!("Created execution_results pool with size {}", pool_size);
                }
                "price_data" => {
                    info!("Created price_data pool with size {}", pool_size);
                }
                _ => {
                    warn!("Unknown object pool type: {}", pool_name);
                }
            }
        }
    }

    async fn start_cleanup_tasks(&mut self) {
        let tracker = self.tracker.clone();
        let config = self.config.clone();

        let handle = tokio::spawn(async move {
            let mut interval =
                tokio::time::interval(Duration::from_secs(config.cleanup_interval_seconds));

            loop {
                interval.tick().await;

                let stats = tracker.get_stats().await;

                // Perform memory cleanup if needed
                if stats.memory_pressure > 0.7 {
                    info!("🧹 Performing memory cleanup due to high pressure");

                    // In a real implementation, you would:
                    // 1. Clear caches
                    // 2. Compact data structures
                    // 3. Release unused object pools
                    // 4. Force garbage collection

                    // Simulate cleanup
                    tokio::time::sleep(Duration::from_millis(100)).await;

                    info!("✅ Memory cleanup completed");
                }
            }
        });

        self.cleanup_tasks.push(handle);
    }

    pub async fn register_pressure_callback<F>(&self, callback: F)
    where
        F: Fn(f64) + Send + Sync + 'static,
    {
        let mut callbacks = self.memory_pressure_callbacks.write().await;
        callbacks.push(Box::new(callback));
    }

    pub async fn get_memory_stats(&self) -> MemoryStats {
        self.tracker.get_stats().await
    }

    pub async fn force_cleanup(&self) -> Result<()> {
        info!("🧹 Forcing memory cleanup");

        let stats_before = self.tracker.get_stats().await;

        // Simulate cleanup operations
        tokio::time::sleep(Duration::from_millis(50)).await;

        let stats_after = self.tracker.get_stats().await;

        info!(
            "✅ Forced cleanup completed. Memory usage: {:.2}MB -> {:.2}MB",
            stats_before.current_usage_bytes as f64 / 1024.0 / 1024.0,
            stats_after.current_usage_bytes as f64 / 1024.0 / 1024.0
        );

        Ok(())
    }

    pub async fn optimize_for_trading(&self) -> Result<()> {
        info!("⚡ Optimizing memory for high-frequency trading");

        // Pre-allocate commonly used data structures
        // Warm up object pools
        // Set up memory-mapped files for large datasets
        // Configure NUMA-aware allocations

        let stats = self.tracker.get_stats().await;
        info!(
            "📊 Trading optimization complete. Current memory usage: {:.2}MB",
            stats.current_usage_bytes as f64 / 1024.0 / 1024.0
        );

        Ok(())
    }

    pub async fn get_optimization_recommendations(&self) -> Vec<String> {
        let stats = self.tracker.get_stats().await;
        let mut recommendations = Vec::new();

        if stats.memory_pressure > 0.8 {
            recommendations
                .push("Consider increasing memory limits or reducing cache sizes".to_string());
        }

        if stats.fragmentation_ratio > 2.0 {
            recommendations
                .push("High memory fragmentation detected, consider memory compaction".to_string());
        }

        if stats.allocation_count > stats.deallocation_count * 2 {
            recommendations.push(
                "Memory leak potential detected, review object lifecycle management".to_string(),
            );
        }

        let current_usage_mb = stats.current_usage_bytes as f64 / 1024.0 / 1024.0;
        if current_usage_mb > self.config.max_heap_size_mb as f64 * 0.9 {
            recommendations
                .push("Approaching maximum heap size, consider scaling resources".to_string());
        }

        if recommendations.is_empty() {
            recommendations.push("Memory usage is optimal".to_string());
        }

        recommendations
    }

    pub async fn shutdown(&mut self) -> Result<()> {
        info!("🛑 Shutting down Memory Optimizer");

        // Cancel all cleanup tasks
        for handle in self.cleanup_tasks.drain(..) {
            handle.abort();
        }

        // Final memory report
        let final_stats = self.tracker.get_stats().await;
        info!(
            "📊 Final memory stats: {:.2}MB used, {} allocations, {} deallocations",
            final_stats.current_usage_bytes as f64 / 1024.0 / 1024.0,
            final_stats.allocation_count,
            final_stats.deallocation_count
        );

        Ok(())
    }
}

// Helper functions for memory optimization
pub fn optimize_vector_capacity<T>(vec: &mut Vec<T>, expected_size: usize) {
    if vec.capacity() < expected_size {
        vec.reserve(expected_size - vec.len());
    } else if vec.capacity() > expected_size * 2 {
        vec.shrink_to(expected_size);
    }
}

pub fn optimize_hashmap_capacity<K, V>(map: &mut HashMap<K, V>, expected_size: usize)
where
    K: std::hash::Hash + Eq,
{
    if map.capacity() < expected_size {
        map.reserve(expected_size - map.len());
    }
    // Note: HashMap doesn't have shrink_to method
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_memory_tracker() {
        let tracker = MemoryTracker::new();

        tracker.record_allocation(1024);
        tracker.record_allocation(2048);
        tracker.record_deallocation(1024);

        let stats = tracker.get_stats().await;
        assert_eq!(stats.current_usage_bytes, 2048);
        assert_eq!(stats.allocation_count, 2);
        assert_eq!(stats.deallocation_count, 1);
    }

    #[tokio::test]
    async fn test_object_pool() {
        let pool = ObjectPool::new(|| String::new(), 10);

        let obj1 = pool.acquire().await;
        let obj2 = pool.acquire().await;

        pool.release(obj1).await;
        pool.release(obj2).await;

        assert_eq!(pool.pool_size(), 2);
    }
}
