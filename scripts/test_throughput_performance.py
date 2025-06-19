#!/usr/bin/env python3
"""
📊 THE OVERMIND PROTOCOL - Throughput Performance Test
FRONT 3: Test 3.2 - sprawdzenie przepustowości systemu pod obciążeniem
"""

import asyncio
import json
import sys
import os
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading

# Add brain src to path
sys.path.append('brain/src')

class ThroughputPerformanceTester:
    """Tester przepustowości systemu"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    async def measure_throughput(self, func, data_list: List, concurrent: int = 1) -> Dict[str, Any]:
        """Zmierz przepustowość funkcji"""
        start_time = time.perf_counter()
        successful_operations = 0
        failed_operations = 0
        results = []
        
        if concurrent == 1:
            # Sequential processing
            for data in data_list:
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(data)
                    else:
                        result = func(data)
                    results.append(result)
                    successful_operations += 1
                except Exception as e:
                    failed_operations += 1
                    results.append({"error": str(e)})
        else:
            # Concurrent processing
            semaphore = asyncio.Semaphore(concurrent)
            
            async def process_item(data):
                async with semaphore:
                    try:
                        if asyncio.iscoroutinefunction(func):
                            result = await func(data)
                        else:
                            result = func(data)
                        return result, True
                    except Exception as e:
                        return {"error": str(e)}, False
            
            tasks = [process_item(data) for data in data_list]
            task_results = await asyncio.gather(*tasks)
            
            for result, success in task_results:
                results.append(result)
                if success:
                    successful_operations += 1
                else:
                    failed_operations += 1
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        return {
            "duration_seconds": duration,
            "total_operations": len(data_list),
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "success_rate": successful_operations / len(data_list) if data_list else 0,
            "throughput_per_second": successful_operations / duration if duration > 0 else 0,
            "results": results
        }
    
    async def test_market_data_throughput(self) -> Dict[str, Any]:
        """Test 3.2.1: Market Data Throughput"""
        print("\n📊 TEST 3.2.1: MARKET DATA THROUGHPUT")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Price Updates Processing
        print("🔍 Testowanie price updates processing...")
        try:
            from overmind_brain.decision_engine import DecisionEngine
            
            decision_engine = DecisionEngine()
            
            # Generate 100 price updates
            price_updates = [
                {
                    "symbol": "SOL/USDC",
                    "price": 100.0 + (i * 0.1),
                    "volume": 1500000 + (i * 1000),
                    "timestamp": time.time() + i
                }
                for i in range(100)
            ]
            
            # Test sequential processing
            print("  📈 Sequential processing...")
            sequential_result = await self.measure_throughput(
                decision_engine.analyze_market_data, 
                price_updates, 
                concurrent=1
            )
            
            # Test concurrent processing
            print("  📈 Concurrent processing (5 workers)...")
            concurrent_result = await self.measure_throughput(
                decision_engine.analyze_market_data, 
                price_updates, 
                concurrent=5
            )
            
            price_updates_test = {
                "test": "Price Updates Processing",
                "success": (sequential_result["throughput_per_second"] >= 10 and 
                           concurrent_result["throughput_per_second"] >= 20),
                "details": {
                    "sequential": {
                        "throughput_per_second": round(sequential_result["throughput_per_second"], 2),
                        "duration_seconds": round(sequential_result["duration_seconds"], 2),
                        "success_rate": round(sequential_result["success_rate"], 3)
                    },
                    "concurrent": {
                        "throughput_per_second": round(concurrent_result["throughput_per_second"], 2),
                        "duration_seconds": round(concurrent_result["duration_seconds"], 2),
                        "success_rate": round(concurrent_result["success_rate"], 3),
                        "workers": 5
                    },
                    "targets": {
                        "sequential_min": 10,
                        "concurrent_min": 20
                    }
                }
            }
            
            print(f"    Sequential: {sequential_result['throughput_per_second']:.2f} ops/sec")
            print(f"    Concurrent: {concurrent_result['throughput_per_second']:.2f} ops/sec")
            print(f"  Status: {'✅ PASSED' if price_updates_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            price_updates_test = {
                "test": "Price Updates Processing",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Price Updates: ❌ FAILED - {str(e)}")
        
        tests.append(price_updates_test)
        
        # Test 2: Multi-Symbol Processing
        print("🔍 Testowanie multi-symbol processing...")
        try:
            # Generate data for 10 different symbols
            symbols = ["SOL/USDC", "ETH/USDC", "BTC/USDC", "AVAX/USDC", "MATIC/USDC",
                      "ADA/USDC", "DOT/USDC", "LINK/USDC", "UNI/USDC", "AAVE/USDC"]
            
            multi_symbol_data = []
            for symbol in symbols:
                for i in range(20):  # 20 updates per symbol
                    multi_symbol_data.append({
                        "symbol": symbol,
                        "price": 100.0 + (i * 0.5),
                        "volume": 1000000 + (i * 5000)
                    })
            
            # Test concurrent multi-symbol processing
            multi_symbol_result = await self.measure_throughput(
                decision_engine.analyze_market_data,
                multi_symbol_data,
                concurrent=10
            )
            
            multi_symbol_test = {
                "test": "Multi-Symbol Processing",
                "success": multi_symbol_result["throughput_per_second"] >= 15,
                "details": {
                    "symbols_count": len(symbols),
                    "total_updates": len(multi_symbol_data),
                    "throughput_per_second": round(multi_symbol_result["throughput_per_second"], 2),
                    "duration_seconds": round(multi_symbol_result["duration_seconds"], 2),
                    "success_rate": round(multi_symbol_result["success_rate"], 3),
                    "target_min": 15
                }
            }
            
            print(f"    Multi-Symbol: {multi_symbol_result['throughput_per_second']:.2f} ops/sec")
            print(f"    Symbols: {len(symbols)}, Updates: {len(multi_symbol_data)}")
            print(f"  Status: {'✅ PASSED' if multi_symbol_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            multi_symbol_test = {
                "test": "Multi-Symbol Processing",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Multi-Symbol: ❌ FAILED - {str(e)}")
        
        tests.append(multi_symbol_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 Market Data Throughput Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "Market Data Throughput",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_ai_decision_throughput(self) -> Dict[str, Any]:
        """Test 3.2.2: AI Decision Throughput"""
        print("\n🧠 TEST 3.2.2: AI DECISION THROUGHPUT")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Decision Rate
        print("🔍 Testowanie decision rate...")
        try:
            from overmind_brain.decision_engine import DecisionEngine
            
            decision_engine = DecisionEngine()
            
            # Generate decision scenarios
            decision_scenarios = [
                {
                    "symbol": f"TOKEN{i}/USDC",
                    "price": 50.0 + (i * 2),
                    "volume": 800000 + (i * 10000),
                    "trend": "bullish" if i % 2 == 0 else "bearish"
                }
                for i in range(60)  # 60 decisions for 1-minute test
            ]
            
            # Measure decision throughput
            decision_result = await self.measure_throughput(
                decision_engine.analyze_market_data,
                decision_scenarios,
                concurrent=3
            )
            
            decisions_per_minute = decision_result["throughput_per_second"] * 60
            
            decision_rate_test = {
                "test": "AI Decision Rate",
                "success": decisions_per_minute >= 100,  # 100 decisions/min target
                "details": {
                    "decisions_per_second": round(decision_result["throughput_per_second"], 2),
                    "decisions_per_minute": round(decisions_per_minute, 2),
                    "duration_seconds": round(decision_result["duration_seconds"], 2),
                    "success_rate": round(decision_result["success_rate"], 3),
                    "target_per_minute": 100
                }
            }
            
            print(f"    Decisions/sec: {decision_result['throughput_per_second']:.2f}")
            print(f"    Decisions/min: {decisions_per_minute:.2f} (target: ≥100)")
            print(f"  Status: {'✅ PASSED' if decision_rate_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            decision_rate_test = {
                "test": "AI Decision Rate",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Decision Rate: ❌ FAILED - {str(e)}")
        
        tests.append(decision_rate_test)
        
        # Test 2: Parallel Analysis
        print("🔍 Testowanie parallel analysis...")
        try:
            # Test parallel decision making
            parallel_scenarios = [
                {
                    "symbol": "SOL/USDC",
                    "price": 105.0 + i,
                    "volume": 1500000,
                    "complexity": "high" if i % 3 == 0 else "normal"
                }
                for i in range(25)  # 25 parallel decisions
            ]
            
            parallel_result = await self.measure_throughput(
                decision_engine.analyze_market_data,
                parallel_scenarios,
                concurrent=5
            )
            
            parallel_test = {
                "test": "Parallel Analysis",
                "success": parallel_result["throughput_per_second"] >= 5,
                "details": {
                    "parallel_workers": 5,
                    "throughput_per_second": round(parallel_result["throughput_per_second"], 2),
                    "duration_seconds": round(parallel_result["duration_seconds"], 2),
                    "success_rate": round(parallel_result["success_rate"], 3),
                    "target_min": 5
                }
            }
            
            print(f"    Parallel: {parallel_result['throughput_per_second']:.2f} ops/sec")
            print(f"    Workers: 5, Success Rate: {parallel_result['success_rate']:.1%}")
            print(f"  Status: {'✅ PASSED' if parallel_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            parallel_test = {
                "test": "Parallel Analysis",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Parallel Analysis: ❌ FAILED - {str(e)}")
        
        tests.append(parallel_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 AI Decision Throughput Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "AI Decision Throughput",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_vector_memory_throughput(self) -> Dict[str, Any]:
        """Test 3.2.3: Vector Memory Throughput"""
        print("\n🧮 TEST 3.2.3: VECTOR MEMORY THROUGHPUT")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Storage Rate
        print("🔍 Testowanie storage rate...")
        try:
            from overmind_brain.vector_memory import VectorMemory
            
            vector_memory = VectorMemory()
            
            # Generate experiences for storage
            experiences = []
            for i in range(50):  # 50 experiences
                experiences.append({
                    "situation": {
                        "market": f"test_market_{i}",
                        "price": 100 + i,
                        "volume": 1000000 + (i * 10000)
                    },
                    "decision": {
                        "action": "BUY" if i % 2 == 0 else "SELL",
                        "confidence": 0.7 + (i % 3) * 0.1
                    },
                    "outcome": {
                        "profit": (i % 5) * 0.5,
                        "duration": i + 10
                    }
                })
            
            # Test storage throughput
            async def store_experience(exp_data):
                return await vector_memory.store_experience(
                    exp_data["situation"],
                    exp_data["decision"],
                    outcome=exp_data["outcome"]
                )
            
            storage_result = await self.measure_throughput(
                store_experience,
                experiences,
                concurrent=5
            )
            
            storage_per_minute = storage_result["throughput_per_second"] * 60
            
            storage_test = {
                "test": "Vector Memory Storage Rate",
                "success": storage_per_minute >= 500,  # 500 operations/min target
                "details": {
                    "storage_per_second": round(storage_result["throughput_per_second"], 2),
                    "storage_per_minute": round(storage_per_minute, 2),
                    "duration_seconds": round(storage_result["duration_seconds"], 2),
                    "success_rate": round(storage_result["success_rate"], 3),
                    "target_per_minute": 500
                }
            }
            
            print(f"    Storage/sec: {storage_result['throughput_per_second']:.2f}")
            print(f"    Storage/min: {storage_per_minute:.2f} (target: ≥500)")
            print(f"  Status: {'✅ PASSED' if storage_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            storage_test = {
                "test": "Vector Memory Storage Rate",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Storage Rate: ❌ FAILED - {str(e)}")
        
        tests.append(storage_test)
        
        # Test 2: Search Rate
        print("🔍 Testowanie search rate...")
        try:
            # Generate search queries
            search_queries = [
                f"market condition {i % 10}",
                f"trading scenario {i % 8}",
                f"profit pattern {i % 6}",
                f"risk situation {i % 4}"
            ]
            
            # Expand to 100 queries
            expanded_queries = []
            for i in range(100):
                expanded_queries.append(search_queries[i % len(search_queries)] + f" variant {i}")
            
            # Test search throughput
            async def search_memory(query):
                return await vector_memory.similarity_search(query, top_k=3)
            
            search_result = await self.measure_throughput(
                search_memory,
                expanded_queries,
                concurrent=10
            )
            
            search_per_minute = search_result["throughput_per_second"] * 60
            
            search_test = {
                "test": "Vector Memory Search Rate",
                "success": search_per_minute >= 1000,  # 1000 queries/min target
                "details": {
                    "search_per_second": round(search_result["throughput_per_second"], 2),
                    "search_per_minute": round(search_per_minute, 2),
                    "duration_seconds": round(search_result["duration_seconds"], 2),
                    "success_rate": round(search_result["success_rate"], 3),
                    "target_per_minute": 1000
                }
            }
            
            print(f"    Search/sec: {search_result['throughput_per_second']:.2f}")
            print(f"    Search/min: {search_per_minute:.2f} (target: ≥1000)")
            print(f"  Status: {'✅ PASSED' if search_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            search_test = {
                "test": "Vector Memory Search Rate",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Search Rate: ❌ FAILED - {str(e)}")
        
        tests.append(search_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 Vector Memory Throughput Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "Vector Memory Throughput",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_system_throughput(self) -> Dict[str, Any]:
        """Test 3.2.4: System Throughput"""
        print("\n🔗 TEST 3.2.4: SYSTEM THROUGHPUT")
        print("-" * 50)
        
        tests = []
        
        # Test 1: End-to-End Pipeline Throughput
        print("🔍 Testowanie end-to-end pipeline throughput...")
        try:
            from overmind_brain.brain import OVERMINDBrain
            
            brain = OVERMINDBrain()
            
            # Generate market events
            market_events = [
                {
                    "event_type": "price_update",
                    "symbol": f"TOKEN{i % 5}/USDC",
                    "price": 100.0 + (i * 0.2),
                    "volume": 1500000 + (i * 1000),
                    "timestamp": datetime.now().isoformat()
                }
                for i in range(30)  # 30 complete pipelines
            ]
            
            # Test E2E throughput
            e2e_result = await self.measure_throughput(
                brain.process_market_event,
                market_events,
                concurrent=3
            )
            
            e2e_per_minute = e2e_result["throughput_per_second"] * 60
            
            e2e_test = {
                "test": "End-to-End Pipeline Throughput",
                "success": e2e_per_minute >= 50,  # 50 complete pipelines/min target
                "details": {
                    "e2e_per_second": round(e2e_result["throughput_per_second"], 2),
                    "e2e_per_minute": round(e2e_per_minute, 2),
                    "duration_seconds": round(e2e_result["duration_seconds"], 2),
                    "success_rate": round(e2e_result["success_rate"], 3),
                    "target_per_minute": 50
                }
            }
            
            print(f"    E2E/sec: {e2e_result['throughput_per_second']:.2f}")
            print(f"    E2E/min: {e2e_per_minute:.2f} (target: ≥50)")
            print(f"  Status: {'✅ PASSED' if e2e_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            e2e_test = {
                "test": "End-to-End Pipeline Throughput",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  E2E Pipeline: ❌ FAILED - {str(e)}")
        
        tests.append(e2e_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 System Throughput Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "System Throughput",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_throughput_tests(self) -> Dict[str, Any]:
        """Uruchom wszystkie testy throughput"""
        print("📊 THE OVERMIND PROTOCOL - THROUGHPUT PERFORMANCE TEST")
        print("=" * 65)
        print("🎯 FRONT 3: Test 3.2 - sprawdzenie przepustowości systemu")
        print()
        
        # Uruchom wszystkie testy
        test_results = []
        
        # Test 3.2.1: Market Data Throughput
        market_data_result = await self.test_market_data_throughput()
        test_results.append(market_data_result)
        
        # Test 3.2.2: AI Decision Throughput
        ai_decision_result = await self.test_ai_decision_throughput()
        test_results.append(ai_decision_result)
        
        # Test 3.2.3: Vector Memory Throughput
        vector_memory_result = await self.test_vector_memory_throughput()
        test_results.append(vector_memory_result)
        
        # Test 3.2.4: System Throughput
        system_result = await self.test_system_throughput()
        test_results.append(system_result)
        
        # Oblicz ogólny wynik
        overall_success = all(result["success"] for result in test_results)
        passed_tests = sum(1 for result in test_results if result["success"])
        
        # Określ poziom przepustowości
        success_rate = passed_tests / len(test_results)
        if success_rate >= 0.95:
            throughput_level = "🚀 EXCELLENT"
        elif success_rate >= 0.85:
            throughput_level = "⚡ GOOD"
        elif success_rate >= 0.70:
            throughput_level = "🎯 ACCEPTABLE"
        elif success_rate >= 0.50:
            throughput_level = "⚠️ NEEDS OPTIMIZATION"
        else:
            throughput_level = "❌ POOR"
        
        print(f"\n🏆 FINALNE WYNIKI THROUGHPUT PERFORMANCE:")
        print("=" * 55)
        print(f"  Testy zaliczone: {passed_tests}/{len(test_results)}")
        print(f"  Wskaźnik sukcesu: {success_rate:.1%}")
        print(f"  Poziom przepustowości: {throughput_level}")
        print(f"  Status: {'✅ THROUGHPUT TARGETS MET!' if overall_success else '❌ NEEDS OPTIMIZATION'}")
        
        return {
            "test_timestamp": self.start_time.isoformat(),
            "test_duration": str(datetime.now() - self.start_time),
            "overall_success": overall_success,
            "throughput_level": throughput_level,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": len(test_results),
            "test_results": test_results,
            "status": "THROUGHPUT_TARGETS_MET" if overall_success else "NEEDS_OPTIMIZATION"
        }

async def main():
    """Główna funkcja testowa"""
    tester = ThroughputPerformanceTester()
    results = await tester.run_throughput_tests()
    
    # Zapisz wyniki
    os.makedirs('docs/testing', exist_ok=True)
    with open('docs/testing/THROUGHPUT_PERFORMANCE_TEST.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Wyniki zapisane w: docs/testing/THROUGHPUT_PERFORMANCE_TEST.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
