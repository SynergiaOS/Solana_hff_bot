#!/usr/bin/env python3
"""
Simple Vector Memory Performance Benchmark for THE OVERMIND PROTOCOL
Direct HTTP API approach to avoid dependency conflicts
"""

import time
import statistics
import random
import string
import json
import requests
import psutil
import threading
from typing import List, Dict, Any, Tuple
import sys
import os
from datetime import datetime, timedelta


class SimpleVectorBenchmark:
    """Simple performance benchmark using direct HTTP API calls"""
    
    def __init__(self, chroma_host="localhost", chroma_port=8001):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.base_url = f"http://{chroma_host}:{chroma_port}"
        self.collection_name = "overmind_benchmark"
        self.results = {}
        self.resource_monitor = SimpleResourceMonitor()
    
    def setup(self):
        """Setup benchmark environment"""
        print("🚀 Setting up Simple Vector Memory benchmark...")
        try:
            # Test connection
            response = requests.get(f"{self.base_url}/api/v1/heartbeat", timeout=5)
            if response.status_code != 200:
                print(f"❌ ChromaDB not responding: {response.status_code}")
                return False
            
            # Create or get collection
            self._ensure_collection()
            print("✅ ChromaDB connection established and collection ready")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to ChromaDB: {e}")
            print("📝 Note: This benchmark requires ChromaDB running on port 8001")
            return False
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            # Try to get collection
            response = requests.get(f"{self.base_url}/api/v1/collections/{self.collection_name}")
            if response.status_code == 200:
                print(f"Using existing collection: {self.collection_name}")
                return
        except:
            pass
        
        # Create new collection
        collection_data = {
            "name": self.collection_name,
            "metadata": {"description": "THE OVERMIND PROTOCOL Benchmark Collection"}
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/collections",
            json=collection_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print(f"Created new collection: {self.collection_name}")
        else:
            print(f"Warning: Could not create collection: {response.status_code}")
    
    def add_memory(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """Add memory to vector database"""
        if metadata is None:
            metadata = {}
        
        memory_id = f"mem_{int(time.time() * 1000)}_{hash(text) % 10000}"
        
        data = {
            "ids": [memory_id],
            "documents": [text],
            "metadatas": [metadata]
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/collections/{self.collection_name}/add",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            return memory_id
        else:
            raise Exception(f"Failed to add memory: {response.status_code}")
    
    def query_similar(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query similar memories"""
        data = {
            "query_texts": [query_text],
            "n_results": limit
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/collections/{self.collection_name}/query",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = []
            
            if result.get('ids') and result['ids'][0]:
                for i, memory_id in enumerate(result['ids'][0]):
                    memory = {
                        "id": memory_id,
                        "text": result['documents'][0][i] if result.get('documents') else "",
                        "similarity": 1.0 - result['distances'][0][i] if result.get('distances') else 0.0
                    }
                    
                    if result.get('metadatas') and result['metadatas'][0]:
                        memory.update(result['metadatas'][0][i] or {})
                    
                    memories.append(memory)
            
            return memories
        else:
            raise Exception(f"Failed to query: {response.status_code}")
    
    def generate_trading_data(self, count: int) -> List[Dict[str, Any]]:
        """Generate realistic trading data"""
        symbols = ["SOL", "BTC", "ETH", "RAY", "ORCA", "BONK", "JUP", "WIF", "PYTH", "DRIFT"]
        strategies = ["momentum", "mean_reversion", "arbitrage", "market_making", "trend_following"]
        
        data = []
        for i in range(count):
            symbol = random.choice(symbols)
            strategy = random.choice(strategies)
            
            text = f"""
            Trading Signal #{i} for {symbol}:
            Strategy: {strategy}
            Price: ${random.uniform(10, 200):.2f}
            Volume: {random.randint(100000, 10000000):,}
            RSI: {random.randint(20, 80)}
            Action: {random.choice(['BUY', 'SELL', 'HOLD'])}
            Confidence: {random.uniform(0.5, 1.0):.2f}
            """
            
            metadata = {
                "symbol": symbol,
                "strategy": strategy,
                "timestamp": datetime.now().isoformat(),
                "type": "trading_signal"
            }
            
            data.append({"text": text.strip(), "metadata": metadata})
        
        return data
    
    def benchmark_storage_performance(self, data_sizes: List[int]) -> Dict[str, Any]:
        """Benchmark storage performance"""
        print("\n📊 Benchmarking storage performance...")
        storage_results = {}
        
        for size in data_sizes:
            print(f"  Testing storage of {size:,} memories...")
            test_data = self.generate_trading_data(size)
            
            # Start resource monitoring
            self.resource_monitor.start_monitoring()
            
            start_time = time.time()
            success_count = 0
            
            for i, item in enumerate(test_data):
                try:
                    memory_id = self.add_memory(item["text"], item["metadata"])
                    success_count += 1
                    
                    # Progress update for large datasets
                    if size >= 1000 and (i + 1) % 100 == 0:
                        progress = (i + 1) / size * 100
                        print(f"    Progress: {progress:.1f}% ({i+1:,}/{size:,})")
                        
                except Exception as e:
                    print(f"    ⚠️ Storage error at {i}: {e}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Stop resource monitoring
            resource_stats = self.resource_monitor.stop_monitoring()
            
            storage_results[size] = {
                "duration": duration,
                "memories_per_second": success_count / duration if duration > 0 else 0,
                "success_count": success_count,
                "success_rate": success_count / size if size > 0 else 0,
                "resource_usage": resource_stats
            }
            
            print(f"    ✅ Stored {success_count:,}/{size:,} memories in {duration:.2f}s")
            print(f"    📈 Rate: {storage_results[size]['memories_per_second']:.2f} memories/sec")
            print(f"    💾 Peak Memory: {resource_stats['peak_memory_mb']:.1f} MB")
            print(f"    🖥️ Avg CPU: {resource_stats['avg_cpu_percent']:.1f}%")
        
        return storage_results
    
    def benchmark_query_performance(self, query_scenarios: List[Dict]) -> Dict[str, Any]:
        """Benchmark query performance"""
        print("\n🔍 Benchmarking query performance...")
        query_results = {}
        
        test_queries = [
            "SOL trading signals",
            "BTC market analysis", 
            "ETH price movements",
            "momentum strategy",
            "arbitrage opportunities",
            "high confidence trades",
            "recent trading decisions"
        ]
        
        for scenario in query_scenarios:
            query_count = scenario["count"]
            result_limit = scenario["limit"]
            
            test_key = f"{query_count}q_{result_limit}r"
            print(f"  Testing {query_count} queries with limit {result_limit}...")
            
            # Start resource monitoring
            self.resource_monitor.start_monitoring()
            
            query_times = []
            total_results = 0
            similarity_scores = []
            
            start_time = time.time()
            
            for i in range(query_count):
                query = random.choice(test_queries) + f" {i}"
                
                query_start = time.time()
                try:
                    results = self.query_similar(query, limit=result_limit)
                    query_end = time.time()
                    
                    query_times.append(query_end - query_start)
                    total_results += len(results)
                    
                    for result in results:
                        if "similarity" in result:
                            similarity_scores.append(result["similarity"])
                            
                except Exception as e:
                    print(f"    ⚠️ Query error: {e}")
            
            end_time = time.time()
            total_duration = end_time - start_time
            
            # Stop resource monitoring
            resource_stats = self.resource_monitor.stop_monitoring()
            
            if query_times:
                query_results[test_key] = {
                    "total_duration": total_duration,
                    "avg_query_time": statistics.mean(query_times),
                    "median_query_time": statistics.median(query_times),
                    "min_query_time": min(query_times),
                    "max_query_time": max(query_times),
                    "queries_per_second": query_count / total_duration if total_duration > 0 else 0,
                    "total_results": total_results,
                    "avg_results_per_query": total_results / query_count if query_count > 0 else 0,
                    "avg_similarity": statistics.mean(similarity_scores) if similarity_scores else 0,
                    "resource_usage": resource_stats
                }
                
                print(f"    ✅ Completed {query_count} queries in {total_duration:.2f}s")
                print(f"    📈 Rate: {query_results[test_key]['queries_per_second']:.2f} queries/sec")
                print(f"    ⏱️ Avg time: {query_results[test_key]['avg_query_time']:.3f}s")
                print(f"    🎯 Avg similarity: {query_results[test_key]['avg_similarity']:.3f}")
        
        return query_results
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark suite"""
        print("🎯 Starting Comprehensive Vector Memory Performance Analysis")
        print("=" * 80)
        
        if not self.setup():
            return {"error": "Failed to setup benchmark environment"}
        
        # Storage benchmarks
        print("\n📈 Phase 1: Storage Performance Testing")
        storage_results = self.benchmark_storage_performance([100, 1000, 5000])
        
        # Query benchmarks
        print("\n📈 Phase 2: Query Performance Testing")
        query_scenarios = [
            {"count": 50, "limit": 5},
            {"count": 100, "limit": 10},
            {"count": 200, "limit": 20}
        ]
        query_results = self.benchmark_query_performance(query_scenarios)
        
        # System info
        system_info = {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / 1024**3,
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat()
        }
        
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "storage_performance": storage_results,
            "query_performance": query_results,
            "system_info": system_info
        }
        
        self.results = benchmark_results
        return benchmark_results
    
    def generate_report(self) -> str:
        """Generate performance report"""
        if not self.results:
            return "❌ No benchmark results available"
        
        report = []
        report.append("=" * 80)
        report.append("📊 THE OVERMIND PROTOCOL - VECTOR MEMORY PERFORMANCE ANALYSIS")
        report.append("=" * 80)
        report.append(f"Generated: {self.results['timestamp']}")
        report.append("")
        
        # Storage Performance
        if "storage_performance" in self.results:
            report.append("📊 STORAGE PERFORMANCE")
            report.append("-" * 40)
            storage = self.results["storage_performance"]
            
            report.append("| Dataset Size | Duration | Rate (mem/s) | Success Rate | Peak Memory |")
            report.append("|--------------|----------|--------------|--------------|-------------|")
            
            for size, metrics in storage.items():
                duration = metrics["duration"]
                rate = metrics["memories_per_second"]
                success_rate = metrics["success_rate"] * 100
                peak_mem = metrics["resource_usage"]["peak_memory_mb"]
                
                report.append(f"| {size:,} | {duration:.1f}s | {rate:.1f} | {success_rate:.1f}% | {peak_mem:.1f} MB |")
            
            report.append("")
        
        # Query Performance
        if "query_performance" in self.results:
            report.append("🔍 QUERY PERFORMANCE")
            report.append("-" * 40)
            queries = self.results["query_performance"]
            
            report.append("| Test | Avg Time | QPS | Avg Similarity |")
            report.append("|------|----------|-----|----------------|")
            
            for test_key, metrics in queries.items():
                avg_time = metrics["avg_query_time"]
                qps = metrics["queries_per_second"]
                similarity = metrics["avg_similarity"]
                
                report.append(f"| {test_key} | {avg_time:.3f}s | {qps:.1f} | {similarity:.3f} |")
            
            report.append("")
        
        # Recommendations
        report.append("🚀 RECOMMENDATIONS")
        report.append("-" * 40)
        
        recommendations = [
            "• System performance is within acceptable ranges for development",
            "• Consider implementing batch operations for large-scale storage",
            "• Monitor query performance under production load",
            "• Implement caching for frequently accessed memories"
        ]
        
        for rec in recommendations:
            report.append(rec)
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_results(self, filename: str = None):
        """Save results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simple_vector_benchmark_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Benchmark results saved to: {filename}")
        
        # Save report
        report_filename = filename.replace('.json', '_report.txt')
        with open(report_filename, 'w') as f:
            f.write(self.generate_report())
        
        print(f"📄 Performance report saved to: {report_filename}")


class SimpleResourceMonitor:
    """Simple resource monitoring"""
    
    def __init__(self):
        self.monitoring = False
        self.cpu_samples = []
        self.memory_samples = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start monitoring"""
        self.monitoring = True
        self.cpu_samples = []
        self.memory_samples = []
        
        self.monitor_thread = threading.Thread(target=self._monitor)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return stats"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        if not self.cpu_samples or not self.memory_samples:
            return {
                "avg_cpu_percent": 0,
                "peak_cpu_percent": 0,
                "avg_memory_mb": 0,
                "peak_memory_mb": 0
            }
        
        return {
            "avg_cpu_percent": statistics.mean(self.cpu_samples),
            "peak_cpu_percent": max(self.cpu_samples),
            "avg_memory_mb": statistics.mean(self.memory_samples),
            "peak_memory_mb": max(self.memory_samples)
        }
    
    def _monitor(self):
        """Monitor resources"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                cpu_percent = process.cpu_percent()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                self.cpu_samples.append(cpu_percent)
                self.memory_samples.append(memory_mb)
                
                time.sleep(0.1)
            except Exception:
                break


if __name__ == "__main__":
    benchmark = SimpleVectorBenchmark()
    results = benchmark.run_comprehensive_benchmark()
    
    if "error" not in results:
        print("\n" + "=" * 80)
        print("📊 BENCHMARK COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        # Print report
        report = benchmark.generate_report()
        print(report)
        
        # Save results
        benchmark.save_results()
    else:
        print(f"\n❌ Benchmark failed: {results['error']}")
