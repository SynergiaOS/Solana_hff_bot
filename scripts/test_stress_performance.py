#!/usr/bin/env python3
"""
🔥 THE OVERMIND PROTOCOL - Stress Performance Test
FRONT 3: Test 3.3 - sprawdzenie zachowania systemu pod ekstremalnym obciążeniem
"""

import asyncio
import json
import sys
import os
import time
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading

# Add brain src to path
sys.path.append('brain/src')

class StressPerformanceTester:
    """Tester stress performance systemu"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.initial_memory = psutil.virtual_memory().used
        
    def get_system_metrics(self) -> Dict[str, Any]:
        """Pobierz metryki systemowe"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "memory_used_mb": round(memory.used / 1024 / 1024, 2),
            "memory_percent": memory.percent,
            "memory_available_mb": round(memory.available / 1024 / 1024, 2),
            "cpu_percent": cpu_percent,
            "timestamp": datetime.now().isoformat()
        }
    
    async def stress_test_memory_usage(self) -> Dict[str, Any]:
        """Test 3.3.1: Memory Stress Test"""
        print("\n🧠 TEST 3.3.1: MEMORY STRESS TEST")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Vector Memory Stress
        print("🔍 Testowanie Vector Memory pod obciążeniem...")
        try:
            from overmind_brain.vector_memory import VectorMemory
            
            vector_memory = VectorMemory()
            
            # Metryki początkowe
            initial_metrics = self.get_system_metrics()
            print(f"  Initial Memory: {initial_metrics['memory_used_mb']:.1f} MB")
            print(f"  Initial CPU: {initial_metrics['cpu_percent']:.1f}%")
            
            # Stress test: 100 experiences storage
            print("  📊 Storing 100 experiences...")
            start_time = time.perf_counter()
            
            stored_experiences = []
            for i in range(100):
                situation = {
                    "market": f"stress_test_{i}",
                    "price": 100 + (i * 0.1),
                    "volume": 1000000 + (i * 10000),
                    "volatility": 0.1 + (i % 10) * 0.01,
                    "indicators": {
                        "rsi": 50 + (i % 20),
                        "macd": (i % 5) * 0.1,
                        "bollinger": f"band_{i % 3}"
                    }
                }
                decision = {
                    "action": "BUY" if i % 2 == 0 else "SELL",
                    "confidence": 0.5 + (i % 5) * 0.1,
                    "position_size": 0.1 + (i % 10) * 0.05
                }
                outcome = {
                    "profit_pct": (i % 10) * 0.5 - 2.0,
                    "duration_minutes": 10 + (i % 60),
                    "max_drawdown": (i % 5) * 0.2
                }
                
                memory_id = await vector_memory.store_experience(situation, decision, outcome=outcome)
                stored_experiences.append(memory_id)
                
                # Monitor memory every 20 operations
                if i % 20 == 0 and i > 0:
                    current_metrics = self.get_system_metrics()
                    print(f"    Progress: {i}/100, Memory: {current_metrics['memory_used_mb']:.1f} MB")
            
            storage_end_time = time.perf_counter()
            storage_duration = storage_end_time - start_time
            
            # Metryki po storage
            post_storage_metrics = self.get_system_metrics()
            memory_increase = post_storage_metrics['memory_used_mb'] - initial_metrics['memory_used_mb']
            
            print(f"  📊 Storage completed: {len(stored_experiences)} experiences")
            print(f"  Memory increase: {memory_increase:.1f} MB")
            
            # Stress test: 200 searches
            print("  🔍 Performing 200 searches...")
            search_start_time = time.perf_counter()
            
            search_queries = [
                f"stress test market condition {i % 20}",
                f"trading scenario {i % 15} with volatility",
                f"profit pattern {i % 10} analysis",
                f"risk situation {i % 8} management"
            ]
            
            search_results = []
            for i in range(200):
                query = search_queries[i % len(search_queries)] + f" variant {i}"
                results = await vector_memory.similarity_search(query, top_k=5)
                search_results.append(len(results))
                
                # Monitor every 50 searches
                if i % 50 == 0 and i > 0:
                    current_metrics = self.get_system_metrics()
                    print(f"    Search progress: {i}/200, CPU: {current_metrics['cpu_percent']:.1f}%")
            
            search_end_time = time.perf_counter()
            search_duration = search_end_time - search_start_time
            
            # Metryki finalne
            final_metrics = self.get_system_metrics()
            total_memory_increase = final_metrics['memory_used_mb'] - initial_metrics['memory_used_mb']
            
            # Force garbage collection
            gc.collect()
            post_gc_metrics = self.get_system_metrics()
            
            memory_stress_test = {
                "test": "Vector Memory Stress Test",
                "success": total_memory_increase < 500,  # Less than 500MB increase
                "details": {
                    "experiences_stored": len(stored_experiences),
                    "searches_performed": len(search_results),
                    "storage_duration": round(storage_duration, 2),
                    "search_duration": round(search_duration, 2),
                    "memory_metrics": {
                        "initial_mb": initial_metrics['memory_used_mb'],
                        "final_mb": final_metrics['memory_used_mb'],
                        "increase_mb": round(total_memory_increase, 2),
                        "post_gc_mb": post_gc_metrics['memory_used_mb']
                    },
                    "cpu_metrics": {
                        "initial_percent": initial_metrics['cpu_percent'],
                        "final_percent": final_metrics['cpu_percent']
                    },
                    "target_memory_limit_mb": 500
                }
            }
            
            print(f"  Final Memory: {final_metrics['memory_used_mb']:.1f} MB")
            print(f"  Total increase: {total_memory_increase:.1f} MB")
            print(f"  After GC: {post_gc_metrics['memory_used_mb']:.1f} MB")
            print(f"  Status: {'✅ PASSED' if memory_stress_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            memory_stress_test = {
                "test": "Vector Memory Stress Test",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Memory Stress: ❌ FAILED - {str(e)}")
        
        tests.append(memory_stress_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 Memory Stress Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "Memory Stress Test",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def stress_test_cpu_usage(self) -> Dict[str, Any]:
        """Test 3.3.2: CPU Stress Test"""
        print("\n⚡ TEST 3.3.2: CPU STRESS TEST")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Concurrent AI Decisions
        print("🔍 Testowanie concurrent AI decisions...")
        try:
            from overmind_brain.decision_engine import DecisionEngine
            
            decision_engine = DecisionEngine()
            
            # Metryki początkowe
            initial_metrics = self.get_system_metrics()
            print(f"  Initial CPU: {initial_metrics['cpu_percent']:.1f}%")
            
            # Generate heavy workload
            heavy_scenarios = []
            for i in range(50):  # 50 complex scenarios
                heavy_scenarios.append({
                    "symbol": f"STRESS{i}/USDC",
                    "price": 100 + (i * 2),
                    "volume": 1000000 + (i * 50000),
                    "complexity": "maximum",
                    "indicators": {
                        "rsi": 30 + (i % 40),
                        "macd": (i % 10) * 0.2 - 1.0,
                        "bollinger_upper": 105 + i,
                        "bollinger_lower": 95 + i,
                        "volume_sma": 1200000 + (i * 10000)
                    },
                    "market_data": {
                        "bid": 100 + (i * 2) - 0.1,
                        "ask": 100 + (i * 2) + 0.1,
                        "spread": 0.2,
                        "depth": {"bids": list(range(10)), "asks": list(range(10))}
                    }
                })
            
            # Test concurrent processing
            print(f"  📊 Processing {len(heavy_scenarios)} complex scenarios concurrently...")
            start_time = time.perf_counter()
            
            # Use semaphore to limit concurrency
            semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
            
            async def process_scenario(scenario):
                async with semaphore:
                    return await decision_engine.analyze_market_data(scenario)
            
            # Monitor CPU during processing
            cpu_samples = []
            
            async def monitor_cpu():
                for _ in range(20):  # Monitor for ~20 seconds
                    await asyncio.sleep(1)
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    cpu_samples.append(cpu_percent)
                    if len(cpu_samples) % 5 == 0:
                        print(f"    CPU usage: {cpu_percent:.1f}%")
            
            # Run processing and monitoring concurrently
            monitor_task = asyncio.create_task(monitor_cpu())
            
            tasks = [process_scenario(scenario) for scenario in heavy_scenarios]
            decisions = await asyncio.gather(*tasks)
            
            monitor_task.cancel()
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Metryki finalne
            final_metrics = self.get_system_metrics()
            avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
            max_cpu = max(cpu_samples) if cpu_samples else 0
            
            cpu_stress_test = {
                "test": "Concurrent AI Decisions CPU Stress",
                "success": max_cpu < 90 and len(decisions) == len(heavy_scenarios),  # CPU < 90%
                "details": {
                    "scenarios_processed": len(decisions),
                    "duration_seconds": round(duration, 2),
                    "decisions_per_second": round(len(decisions) / duration, 2),
                    "cpu_metrics": {
                        "initial_percent": initial_metrics['cpu_percent'],
                        "average_percent": round(avg_cpu, 2),
                        "max_percent": round(max_cpu, 2),
                        "final_percent": final_metrics['cpu_percent']
                    },
                    "concurrency_level": 10,
                    "target_cpu_limit": 90
                }
            }
            
            print(f"  Decisions processed: {len(decisions)}")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Average CPU: {avg_cpu:.1f}%")
            print(f"  Max CPU: {max_cpu:.1f}%")
            print(f"  Status: {'✅ PASSED' if cpu_stress_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            cpu_stress_test = {
                "test": "Concurrent AI Decisions CPU Stress",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  CPU Stress: ❌ FAILED - {str(e)}")
        
        tests.append(cpu_stress_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 CPU Stress Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "CPU Stress Test",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def stress_test_error_handling(self) -> Dict[str, Any]:
        """Test 3.3.4: Error Handling Under Stress"""
        print("\n🛡️ TEST 3.3.4: ERROR HANDLING UNDER STRESS")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Error Recovery
        print("🔍 Testowanie error recovery under stress...")
        try:
            from overmind_brain.decision_engine import DecisionEngine
            from overmind_brain.vector_memory import VectorMemory
            
            decision_engine = DecisionEngine()
            vector_memory = VectorMemory()
            
            # Generate scenarios with intentional errors
            error_scenarios = []
            valid_scenarios = []
            
            for i in range(30):
                if i % 5 == 0:  # Every 5th scenario has errors
                    error_scenarios.append({
                        "symbol": None,  # Invalid data
                        "price": "invalid_price",
                        "volume": -1000  # Negative volume
                    })
                else:
                    valid_scenarios.append({
                        "symbol": f"VALID{i}/USDC",
                        "price": 100 + i,
                        "volume": 1000000 + (i * 1000)
                    })
            
            all_scenarios = error_scenarios + valid_scenarios
            
            print(f"  📊 Testing {len(all_scenarios)} scenarios ({len(error_scenarios)} with errors)")
            
            successful_decisions = 0
            failed_decisions = 0
            error_types = {}
            
            start_time = time.perf_counter()
            
            for scenario in all_scenarios:
                try:
                    decision = await decision_engine.analyze_market_data(scenario)
                    successful_decisions += 1
                except Exception as e:
                    failed_decisions += 1
                    error_type = type(e).__name__
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Test system recovery
            print("  🔄 Testing system recovery...")
            recovery_start = time.perf_counter()
            
            # Process valid scenarios after errors
            recovery_decisions = []
            for scenario in valid_scenarios[:10]:  # Test 10 recovery scenarios
                try:
                    decision = await decision_engine.analyze_market_data(scenario)
                    recovery_decisions.append(decision)
                except Exception as e:
                    print(f"    Recovery failed: {e}")
            
            recovery_end = time.perf_counter()
            recovery_duration = recovery_end - recovery_start
            
            error_handling_test = {
                "test": "Error Handling Under Stress",
                "success": (successful_decisions >= len(valid_scenarios) and 
                           len(recovery_decisions) >= 8),  # 80% recovery rate
                "details": {
                    "total_scenarios": len(all_scenarios),
                    "successful_decisions": successful_decisions,
                    "failed_decisions": failed_decisions,
                    "error_types": error_types,
                    "processing_duration": round(duration, 2),
                    "recovery_scenarios": len(recovery_decisions),
                    "recovery_duration": round(recovery_duration, 2),
                    "recovery_rate": round(len(recovery_decisions) / 10, 2),
                    "target_recovery_rate": 0.8
                }
            }
            
            print(f"  Successful: {successful_decisions}")
            print(f"  Failed: {failed_decisions}")
            print(f"  Recovery: {len(recovery_decisions)}/10")
            print(f"  Error types: {error_types}")
            print(f"  Status: {'✅ PASSED' if error_handling_test['success'] else '❌ FAILED'}")
            
        except Exception as e:
            error_handling_test = {
                "test": "Error Handling Under Stress",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Error Handling: ❌ FAILED - {str(e)}")
        
        tests.append(error_handling_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 Error Handling Stress Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "Error Handling Stress Test",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_stress_tests(self) -> Dict[str, Any]:
        """Uruchom wszystkie testy stress"""
        print("🔥 THE OVERMIND PROTOCOL - STRESS PERFORMANCE TEST")
        print("=" * 65)
        print("🎯 FRONT 3: Test 3.3 - sprawdzenie zachowania pod obciążeniem")
        print()
        
        # Uruchom wszystkie testy
        test_results = []
        
        # Test 3.3.1: Memory Stress
        memory_result = await self.stress_test_memory_usage()
        test_results.append(memory_result)
        
        # Test 3.3.2: CPU Stress
        cpu_result = await self.stress_test_cpu_usage()
        test_results.append(cpu_result)
        
        # Test 3.3.4: Error Handling
        error_result = await self.stress_test_error_handling()
        test_results.append(error_result)
        
        # Oblicz ogólny wynik
        overall_success = all(result["success"] for result in test_results)
        passed_tests = sum(1 for result in test_results if result["success"])
        
        # Określ poziom stress resistance
        success_rate = passed_tests / len(test_results)
        if success_rate >= 0.95:
            stress_level = "🔥 EXCELLENT"
        elif success_rate >= 0.85:
            stress_level = "💪 GOOD"
        elif success_rate >= 0.70:
            stress_level = "🎯 ACCEPTABLE"
        elif success_rate >= 0.50:
            stress_level = "⚠️ NEEDS OPTIMIZATION"
        else:
            stress_level = "❌ POOR"
        
        print(f"\n🏆 FINALNE WYNIKI STRESS PERFORMANCE:")
        print("=" * 55)
        print(f"  Testy zaliczone: {passed_tests}/{len(test_results)}")
        print(f"  Wskaźnik sukcesu: {success_rate:.1%}")
        print(f"  Poziom stress resistance: {stress_level}")
        print(f"  Status: {'✅ STRESS RESISTANCE CONFIRMED!' if overall_success else '❌ NEEDS OPTIMIZATION'}")
        
        return {
            "test_timestamp": self.start_time.isoformat(),
            "test_duration": str(datetime.now() - self.start_time),
            "overall_success": overall_success,
            "stress_level": stress_level,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": len(test_results),
            "test_results": test_results,
            "status": "STRESS_RESISTANCE_CONFIRMED" if overall_success else "NEEDS_OPTIMIZATION"
        }

async def main():
    """Główna funkcja testowa"""
    tester = StressPerformanceTester()
    results = await tester.run_stress_tests()
    
    # Zapisz wyniki
    os.makedirs('docs/testing', exist_ok=True)
    with open('docs/testing/STRESS_PERFORMANCE_TEST.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Wyniki zapisane w: docs/testing/STRESS_PERFORMANCE_TEST.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
