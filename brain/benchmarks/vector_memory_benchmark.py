#!/usr/bin/env python3
"""
VectorMemory Performance Benchmark for THE OVERMIND PROTOCOL
Comprehensive performance testing and benchmarking
"""

import time
import statistics
import random
import string
import json
from typing import List, Dict, Any
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from overmind_brain.vector_memory import VectorMemory


class VectorMemoryBenchmark:
    """Performance benchmark suite for VectorMemory"""
    
    def __init__(self):
        self.results = {}
        self.vector_memory = None
    
    def setup(self):
        """Setup benchmark environment"""
        print("🚀 Setting up VectorMemory benchmark...")
        try:
            self.vector_memory = VectorMemory("benchmark_collection")
            print("✅ VectorMemory initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize VectorMemory: {e}")
            print("📝 Note: This benchmark requires a running Qdrant instance")
            return False
        return True
    
    def generate_test_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate test data for benchmarking"""
        test_data = []
        categories = ["trading", "market_analysis", "risk_assessment", "portfolio", "news"]
        
        for i in range(count):
            text_length = random.randint(50, 500)
            text = f"Test memory {i}: " + ''.join(random.choices(string.ascii_letters + ' ', k=text_length))
            
            metadata = {
                "id": i,
                "category": random.choice(categories),
                "priority": random.randint(1, 5),
                "timestamp": f"2025-06-23T{random.randint(10, 23):02d}:{random.randint(0, 59):02d}:00Z",
                "symbol": random.choice(["SOL", "BTC", "ETH", "RAY", "ORCA"]),
                "confidence": round(random.uniform(0.1, 1.0), 2)
            }
            
            test_data.append({"text": text, "metadata": metadata})
        
        return test_data
    
    def benchmark_storage(self, data_sizes: List[int]) -> Dict[str, Any]:
        """Benchmark memory storage performance"""
        print("\n📊 Benchmarking storage performance...")
        storage_results = {}
        
        for size in data_sizes:
            print(f"  Testing storage of {size} memories...")
            test_data = self.generate_test_data(size)
            
            start_time = time.time()
            memory_ids = []
            
            for item in test_data:
                try:
                    memory_id = self.vector_memory.add_memory(item["text"], item["metadata"])
                    memory_ids.append(memory_id)
                except Exception as e:
                    print(f"    ⚠️ Storage error: {e}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            storage_results[size] = {
                "duration": duration,
                "memories_per_second": size / duration if duration > 0 else 0,
                "avg_time_per_memory": duration / size if size > 0 else 0,
                "success_count": len(memory_ids),
                "success_rate": len(memory_ids) / size if size > 0 else 0
            }
            
            print(f"    ✅ Stored {len(memory_ids)}/{size} memories in {duration:.2f}s")
            print(f"    📈 Rate: {storage_results[size]['memories_per_second']:.2f} memories/sec")
        
        return storage_results
    
    def benchmark_queries(self, query_counts: List[int], result_limits: List[int]) -> Dict[str, Any]:
        """Benchmark query performance"""
        print("\n🔍 Benchmarking query performance...")
        query_results = {}
        
        # Generate test queries
        test_queries = [
            "trading strategy for SOL",
            "market analysis Bitcoin",
            "risk assessment portfolio",
            "high confidence signals",
            "recent trading decisions",
            "profitable trades",
            "market volatility analysis",
            "technical indicators",
            "price movement patterns",
            "volume analysis"
        ]
        
        for query_count in query_counts:
            for limit in result_limits:
                test_key = f"{query_count}_queries_{limit}_limit"
                print(f"  Testing {query_count} queries with limit {limit}...")
                
                query_times = []
                total_results = 0
                
                start_time = time.time()
                
                for i in range(query_count):
                    query = random.choice(test_queries) + f" {i}"
                    
                    query_start = time.time()
                    try:
                        results = self.vector_memory.find_similar(query, limit=limit)
                        query_end = time.time()
                        
                        query_times.append(query_end - query_start)
                        total_results += len(results)
                    except Exception as e:
                        print(f"    ⚠️ Query error: {e}")
                
                end_time = time.time()
                total_duration = end_time - start_time
                
                if query_times:
                    query_results[test_key] = {
                        "total_duration": total_duration,
                        "avg_query_time": statistics.mean(query_times),
                        "median_query_time": statistics.median(query_times),
                        "min_query_time": min(query_times),
                        "max_query_time": max(query_times),
                        "queries_per_second": query_count / total_duration if total_duration > 0 else 0,
                        "total_results": total_results,
                        "avg_results_per_query": total_results / query_count if query_count > 0 else 0
                    }
                    
                    print(f"    ✅ Completed {query_count} queries in {total_duration:.2f}s")
                    print(f"    📈 Rate: {query_results[test_key]['queries_per_second']:.2f} queries/sec")
                    print(f"    ⏱️ Avg time: {query_results[test_key]['avg_query_time']:.3f}s")
        
        return query_results
    
    def benchmark_concurrent_operations(self, thread_counts: List[int]) -> Dict[str, Any]:
        """Benchmark concurrent operations"""
        print("\n🔄 Benchmarking concurrent operations...")
        import threading
        import queue
        
        concurrent_results = {}
        
        for thread_count in thread_counts:
            print(f"  Testing with {thread_count} concurrent threads...")
            
            results_queue = queue.Queue()
            
            def worker(worker_id, operations_per_worker=10):
                worker_times = []
                
                for i in range(operations_per_worker):
                    # Mix of storage and query operations
                    if i % 2 == 0:
                        # Storage operation
                        start = time.time()
                        text = f"Concurrent worker {worker_id} memory {i}"
                        try:
                            self.vector_memory.add_memory(text, {"worker": worker_id, "op": i})
                            worker_times.append(time.time() - start)
                        except Exception as e:
                            print(f"    ⚠️ Storage error in worker {worker_id}: {e}")
                    else:
                        # Query operation
                        start = time.time()
                        try:
                            results = self.vector_memory.find_similar(f"worker {worker_id} query {i}", limit=5)
                            worker_times.append(time.time() - start)
                        except Exception as e:
                            print(f"    ⚠️ Query error in worker {worker_id}: {e}")
                
                results_queue.put({
                    "worker_id": worker_id,
                    "operation_times": worker_times,
                    "avg_time": statistics.mean(worker_times) if worker_times else 0
                })
            
            # Start concurrent workers
            start_time = time.time()
            threads = []
            
            for i in range(thread_count):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Collect results
            worker_results = []
            while not results_queue.empty():
                worker_results.append(results_queue.get())
            
            if worker_results:
                all_times = []
                for result in worker_results:
                    all_times.extend(result["operation_times"])
                
                concurrent_results[thread_count] = {
                    "total_duration": total_duration,
                    "workers_completed": len(worker_results),
                    "total_operations": len(all_times),
                    "avg_operation_time": statistics.mean(all_times) if all_times else 0,
                    "operations_per_second": len(all_times) / total_duration if total_duration > 0 else 0,
                    "worker_avg_times": [r["avg_time"] for r in worker_results]
                }
                
                print(f"    ✅ {len(worker_results)} workers completed {len(all_times)} operations in {total_duration:.2f}s")
                print(f"    📈 Rate: {concurrent_results[thread_count]['operations_per_second']:.2f} ops/sec")
        
        return concurrent_results
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        print("🎯 Starting VectorMemory Performance Benchmark")
        print("=" * 60)
        
        if not self.setup():
            return {"error": "Failed to setup benchmark environment"}
        
        # Storage benchmarks
        storage_results = self.benchmark_storage([10, 50, 100, 500])
        
        # Query benchmarks
        query_results = self.benchmark_queries([10, 50, 100], [5, 10, 20])
        
        # Concurrent operation benchmarks
        concurrent_results = self.benchmark_concurrent_operations([2, 5, 10])
        
        # Get final metrics
        final_metrics = self.vector_memory.get_metrics()
        
        benchmark_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "storage_performance": storage_results,
            "query_performance": query_results,
            "concurrent_performance": concurrent_results,
            "final_metrics": final_metrics
        }
        
        self.results = benchmark_results
        return benchmark_results
    
    def save_results(self, filename: str = None):
        """Save benchmark results to file"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"vector_memory_benchmark_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Benchmark results saved to: {filename}")
    
    def print_summary(self):
        """Print benchmark summary"""
        if not self.results:
            print("❌ No benchmark results available")
            return
        
        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)
        
        # Storage summary
        if "storage_performance" in self.results:
            print("\n🗄️ Storage Performance:")
            for size, metrics in self.results["storage_performance"].items():
                print(f"  {size} memories: {metrics['memories_per_second']:.2f} mem/sec")
        
        # Query summary
        if "query_performance" in self.results:
            print("\n🔍 Query Performance:")
            for test, metrics in self.results["query_performance"].items():
                print(f"  {test}: {metrics['queries_per_second']:.2f} queries/sec")
        
        # Concurrent summary
        if "concurrent_performance" in self.results:
            print("\n🔄 Concurrent Performance:")
            for threads, metrics in self.results["concurrent_performance"].items():
                print(f"  {threads} threads: {metrics['operations_per_second']:.2f} ops/sec")
        
        # Final metrics
        if "final_metrics" in self.results:
            metrics = self.results["final_metrics"]
            print(f"\n📈 Final Metrics:")
            print(f"  Total queries: {metrics.get('queries_total', 0)}")
            print(f"  Success rate: {metrics.get('queries_success', 0) / max(metrics.get('queries_total', 1), 1) * 100:.1f}%")
            print(f"  Avg query time: {metrics.get('avg_query_time', 0):.3f}s")


if __name__ == "__main__":
    benchmark = VectorMemoryBenchmark()
    results = benchmark.run_full_benchmark()
    benchmark.print_summary()
    benchmark.save_results()
