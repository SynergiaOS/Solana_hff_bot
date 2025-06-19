#!/usr/bin/env python3
"""
🔥 THE OVERMIND PROTOCOL - Simple Stress Test
FRONT 3: Test 3.3 - uproszczony test stress bez zewnętrznych zależności
"""

import asyncio
import json
import sys
import os
import time
import gc
from datetime import datetime
from typing import Dict, List, Any

# Add brain src to path
sys.path.append('brain/src')

async def test_simple_stress():
    """Uproszczony test stress"""
    print("🔥 THE OVERMIND PROTOCOL - SIMPLE STRESS TEST")
    print("=" * 55)
    print("🎯 FRONT 3: Test 3.3 - sprawdzenie pod obciążeniem")
    print()
    
    results = {
        "test_timestamp": datetime.now().isoformat(),
        "test_results": [],
        "overall_success": False
    }
    
    # Test 1: Memory Stress - Vector Memory
    print("🧠 TEST 1: MEMORY STRESS - VECTOR MEMORY")
    print("-" * 45)
    
    try:
        from overmind_brain.vector_memory import VectorMemory
        
        vector_memory = VectorMemory()
        
        print("🔍 Storing 50 complex experiences...")
        start_time = time.perf_counter()
        
        stored_experiences = []
        for i in range(50):
            # Complex experience data
            situation = {
                "market": f"stress_test_{i}",
                "price": 100 + (i * 0.5),
                "volume": 1000000 + (i * 20000),
                "volatility": 0.1 + (i % 10) * 0.01,
                "indicators": {
                    "rsi": 30 + (i % 40),
                    "macd": (i % 10) * 0.2 - 1.0,
                    "bollinger_upper": 105 + i,
                    "bollinger_lower": 95 + i,
                    "volume_sma": 1200000 + (i * 10000),
                    "price_sma_20": 100 + (i * 0.3),
                    "price_sma_50": 100 + (i * 0.2)
                },
                "market_conditions": {
                    "trend": "bullish" if i % 2 == 0 else "bearish",
                    "strength": (i % 5) * 0.2,
                    "momentum": (i % 7) * 0.15 - 0.5
                }
            }
            decision = {
                "action": "BUY" if i % 3 == 0 else "SELL" if i % 3 == 1 else "HOLD",
                "confidence": 0.4 + (i % 6) * 0.1,
                "position_size": 0.1 + (i % 10) * 0.05,
                "reasoning": f"Complex analysis for scenario {i} with multiple indicators"
            }
            outcome = {
                "profit_pct": (i % 15) * 0.3 - 2.0,
                "duration_minutes": 15 + (i % 120),
                "max_drawdown": (i % 8) * 0.15,
                "sharpe_ratio": (i % 10) * 0.2 - 1.0
            }
            
            memory_id = await vector_memory.store_experience(situation, decision, outcome=outcome)
            stored_experiences.append(memory_id)
            
            if i % 10 == 0 and i > 0:
                print(f"  Progress: {i}/50 experiences stored")
        
        storage_end_time = time.perf_counter()
        storage_duration = storage_end_time - start_time
        
        print("🔍 Performing 100 complex searches...")
        search_start_time = time.perf_counter()
        
        search_queries = [
            "bullish market with high volume and strong momentum",
            "bearish trend with oversold RSI conditions",
            "sideways market with low volatility trading",
            "breakout pattern with increasing volume",
            "reversal signal with diverging indicators",
            "high volatility with uncertain direction",
            "strong uptrend with momentum confirmation",
            "consolidation phase with range trading"
        ]
        
        search_results = []
        for i in range(100):
            query = search_queries[i % len(search_queries)] + f" scenario {i}"
            results_found = await vector_memory.similarity_search(query, top_k=5)
            search_results.append(len(results_found))
            
            if i % 20 == 0 and i > 0:
                print(f"  Search progress: {i}/100 searches completed")
        
        search_end_time = time.perf_counter()
        search_duration = search_end_time - search_start_time
        
        # Force garbage collection
        gc.collect()
        
        memory_test = {
            "test": "Memory Stress - Vector Memory",
            "success": len(stored_experiences) == 50 and len(search_results) == 100,
            "details": {
                "experiences_stored": len(stored_experiences),
                "searches_performed": len(search_results),
                "storage_duration": round(storage_duration, 2),
                "search_duration": round(search_duration, 2),
                "storage_rate": round(len(stored_experiences) / storage_duration, 2),
                "search_rate": round(len(search_results) / search_duration, 2),
                "avg_search_results": round(sum(search_results) / len(search_results), 2)
            }
        }
        
        print(f"  Experiences stored: {len(stored_experiences)}")
        print(f"  Searches completed: {len(search_results)}")
        print(f"  Storage rate: {memory_test['details']['storage_rate']:.2f} ops/sec")
        print(f"  Search rate: {memory_test['details']['search_rate']:.2f} ops/sec")
        print(f"  Status: {'✅ PASSED' if memory_test['success'] else '❌ FAILED'}")
        
        results["test_results"].append(memory_test)
        
    except Exception as e:
        print(f"  ❌ Memory Stress Test FAILED: {e}")
        results["test_results"].append({
            "test": "Memory Stress - Vector Memory",
            "success": False,
            "error": str(e)
        })
    
    print()
    
    # Test 2: CPU Stress - Concurrent AI Decisions
    print("⚡ TEST 2: CPU STRESS - CONCURRENT AI DECISIONS")
    print("-" * 45)
    
    try:
        from overmind_brain.decision_engine import DecisionEngine
        
        decision_engine = DecisionEngine()
        
        # Generate complex scenarios
        complex_scenarios = []
        for i in range(30):
            complex_scenarios.append({
                "symbol": f"STRESS{i}/USDC",
                "price": 100 + (i * 3),
                "volume": 1000000 + (i * 100000),
                "complexity": "maximum",
                "indicators": {
                    "rsi": 20 + (i % 60),
                    "macd": (i % 20) * 0.1 - 1.0,
                    "bollinger_upper": 110 + i,
                    "bollinger_lower": 90 + i,
                    "volume_sma": 1500000 + (i * 50000),
                    "atr": (i % 10) * 0.5,
                    "stoch_k": (i % 100),
                    "stoch_d": ((i + 3) % 100)
                },
                "market_data": {
                    "bid": 100 + (i * 3) - 0.2,
                    "ask": 100 + (i * 3) + 0.2,
                    "spread": 0.4,
                    "last_trades": [100 + (i * 3) + j * 0.1 for j in range(-5, 5)]
                }
            })
        
        print(f"🔍 Processing {len(complex_scenarios)} complex scenarios concurrently...")
        start_time = time.perf_counter()
        
        # Use semaphore for controlled concurrency
        semaphore = asyncio.Semaphore(8)  # Max 8 concurrent
        
        async def process_scenario(scenario):
            async with semaphore:
                return await decision_engine.analyze_market_data(scenario)
        
        # Process all scenarios
        tasks = [process_scenario(scenario) for scenario in complex_scenarios]
        decisions = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        cpu_test = {
            "test": "CPU Stress - Concurrent AI Decisions",
            "success": len(decisions) == len(complex_scenarios) and duration < 60,  # Complete in <60s
            "details": {
                "scenarios_processed": len(decisions),
                "duration_seconds": round(duration, 2),
                "decisions_per_second": round(len(decisions) / duration, 2),
                "concurrency_level": 8,
                "target_duration": 60,
                "successful_decisions": sum(1 for d in decisions if d is not None)
            }
        }
        
        print(f"  Scenarios processed: {len(decisions)}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Rate: {cpu_test['details']['decisions_per_second']:.2f} decisions/sec")
        print(f"  Successful: {cpu_test['details']['successful_decisions']}")
        print(f"  Status: {'✅ PASSED' if cpu_test['success'] else '❌ FAILED'}")
        
        results["test_results"].append(cpu_test)
        
    except Exception as e:
        print(f"  ❌ CPU Stress Test FAILED: {e}")
        results["test_results"].append({
            "test": "CPU Stress - Concurrent AI Decisions",
            "success": False,
            "error": str(e)
        })
    
    print()
    
    # Test 3: Error Handling Under Stress
    print("🛡️ TEST 3: ERROR HANDLING UNDER STRESS")
    print("-" * 40)
    
    try:
        # Generate mixed scenarios (valid and invalid)
        mixed_scenarios = []
        
        # Add valid scenarios
        for i in range(20):
            mixed_scenarios.append({
                "symbol": f"VALID{i}/USDC",
                "price": 100 + i,
                "volume": 1000000 + (i * 10000),
                "type": "valid"
            })
        
        # Add invalid scenarios
        invalid_scenarios = [
            {"symbol": None, "price": "invalid", "volume": -1000, "type": "invalid"},
            {"symbol": "", "price": 0, "volume": None, "type": "invalid"},
            {"symbol": "TEST/USDC", "price": -50, "volume": "bad_volume", "type": "invalid"},
            {"symbol": "INVALID", "price": float('inf'), "volume": 1000000, "type": "invalid"},
            {"price": 100, "volume": 1000000, "type": "invalid"},  # Missing symbol
        ]
        
        mixed_scenarios.extend(invalid_scenarios)
        
        print(f"🔍 Testing {len(mixed_scenarios)} scenarios ({len(invalid_scenarios)} with errors)...")
        
        successful_decisions = 0
        failed_decisions = 0
        error_types = {}
        
        start_time = time.perf_counter()
        
        for scenario in mixed_scenarios:
            try:
                decision = await decision_engine.analyze_market_data(scenario)
                if decision is not None:
                    successful_decisions += 1
            except Exception as e:
                failed_decisions += 1
                error_type = type(e).__name__
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Test recovery with valid scenarios
        print("  🔄 Testing system recovery...")
        recovery_scenarios = [
            {"symbol": f"RECOVERY{i}/USDC", "price": 105 + i, "volume": 1200000}
            for i in range(5)
        ]
        
        recovery_decisions = []
        for scenario in recovery_scenarios:
            try:
                decision = await decision_engine.analyze_market_data(scenario)
                recovery_decisions.append(decision)
            except Exception as e:
                print(f"    Recovery failed: {e}")
        
        error_test = {
            "test": "Error Handling Under Stress",
            "success": (successful_decisions >= 20 and len(recovery_decisions) >= 4),
            "details": {
                "total_scenarios": len(mixed_scenarios),
                "valid_scenarios": 20,
                "invalid_scenarios": len(invalid_scenarios),
                "successful_decisions": successful_decisions,
                "failed_decisions": failed_decisions,
                "error_types": error_types,
                "processing_duration": round(duration, 2),
                "recovery_scenarios": len(recovery_decisions),
                "recovery_rate": round(len(recovery_decisions) / 5, 2)
            }
        }
        
        print(f"  Total scenarios: {len(mixed_scenarios)}")
        print(f"  Successful: {successful_decisions}")
        print(f"  Failed: {failed_decisions}")
        print(f"  Recovery: {len(recovery_decisions)}/5")
        print(f"  Error types: {error_types}")
        print(f"  Status: {'✅ PASSED' if error_test['success'] else '❌ FAILED'}")
        
        results["test_results"].append(error_test)
        
    except Exception as e:
        print(f"  ❌ Error Handling Test FAILED: {e}")
        results["test_results"].append({
            "test": "Error Handling Under Stress",
            "success": False,
            "error": str(e)
        })
    
    # Oblicz ogólny wynik
    passed_tests = sum(1 for test in results["test_results"] if test["success"])
    total_tests = len(results["test_results"])
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    results["overall_success"] = success_rate >= 0.67  # 2/3 tests must pass
    results["passed_tests"] = passed_tests
    results["total_tests"] = total_tests
    results["success_rate"] = success_rate
    
    # Określ poziom stress resistance
    if success_rate >= 0.9:
        stress_level = "🔥 EXCELLENT"
    elif success_rate >= 0.7:
        stress_level = "💪 GOOD"
    elif success_rate >= 0.5:
        stress_level = "🎯 ACCEPTABLE"
    else:
        stress_level = "❌ NEEDS WORK"
    
    results["stress_level"] = stress_level
    
    print()
    print("🏆 FINALNE WYNIKI SIMPLE STRESS TEST:")
    print("=" * 50)
    print(f"  Testy zaliczone: {passed_tests}/{total_tests}")
    print(f"  Wskaźnik sukcesu: {success_rate:.1%}")
    print(f"  Poziom stress resistance: {stress_level}")
    print(f"  Status: {'✅ STRESS RESISTANCE OK!' if results['overall_success'] else '❌ NEEDS IMPROVEMENT'}")
    
    # Zapisz wyniki
    os.makedirs('docs/testing', exist_ok=True)
    with open('docs/testing/SIMPLE_STRESS_TEST.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Wyniki zapisane w: docs/testing/SIMPLE_STRESS_TEST.json")
    
    return results

async def main():
    """Główna funkcja testowa"""
    return await test_simple_stress()

if __name__ == "__main__":
    asyncio.run(main())
