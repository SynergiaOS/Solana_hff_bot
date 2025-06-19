#!/usr/bin/env python3
"""
📊 THE OVERMIND PROTOCOL - Simple Throughput Test
FRONT 3: Test 3.2 - uproszczony test przepustowości systemu
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Any

# Add brain src to path
sys.path.append('brain/src')

async def test_simple_throughput():
    """Uproszczony test przepustowości"""
    print("📊 THE OVERMIND PROTOCOL - SIMPLE THROUGHPUT TEST")
    print("=" * 55)
    print("🎯 FRONT 3: Test 3.2 - sprawdzenie przepustowości")
    print()
    
    results = {
        "test_timestamp": datetime.now().isoformat(),
        "test_results": [],
        "overall_success": False
    }
    
    # Test 1: AI Decision Throughput
    print("🧠 TEST 1: AI DECISION THROUGHPUT")
    print("-" * 40)
    
    try:
        from overmind_brain.decision_engine import DecisionEngine
        
        decision_engine = DecisionEngine()
        
        # Test 10 decisions
        test_data = [
            {"symbol": "SOL/USDC", "price": 100.0 + i, "volume": 1500000}
            for i in range(10)
        ]
        
        print("🔍 Testowanie 10 decyzji AI...")
        start_time = time.perf_counter()
        
        decisions = []
        for data in test_data:
            decision = await decision_engine.analyze_market_data(data)
            decisions.append(decision)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        throughput = len(decisions) / duration
        
        ai_test = {
            "test": "AI Decision Throughput",
            "success": throughput >= 2.0,  # 2 decisions/sec minimum
            "details": {
                "decisions_count": len(decisions),
                "duration_seconds": round(duration, 2),
                "throughput_per_second": round(throughput, 2),
                "target_min": 2.0
            }
        }
        
        print(f"  Decisions: {len(decisions)}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} decisions/sec")
        print(f"  Status: {'✅ PASSED' if ai_test['success'] else '❌ FAILED'}")
        
        results["test_results"].append(ai_test)
        
    except Exception as e:
        print(f"  ❌ AI Decision Test FAILED: {e}")
        results["test_results"].append({
            "test": "AI Decision Throughput",
            "success": False,
            "error": str(e)
        })
    
    print()
    
    # Test 2: Vector Memory Throughput
    print("🧮 TEST 2: VECTOR MEMORY THROUGHPUT")
    print("-" * 40)
    
    try:
        from overmind_brain.vector_memory import VectorMemory
        
        vector_memory = VectorMemory()
        
        print("🔍 Testowanie 5 operacji storage...")
        start_time = time.perf_counter()
        
        storage_results = []
        for i in range(5):
            situation = {"market": f"test_{i}", "price": 100 + i}
            decision = {"action": "BUY", "confidence": 0.8}
            outcome = {"profit": 2.0}
            
            memory_id = await vector_memory.store_experience(situation, decision, outcome=outcome)
            storage_results.append(memory_id)
        
        end_time = time.perf_counter()
        storage_duration = end_time - start_time
        storage_throughput = len(storage_results) / storage_duration
        
        print("🔍 Testowanie 5 operacji search...")
        start_time = time.perf_counter()
        
        search_results = []
        for i in range(5):
            query = f"test market condition {i}"
            results_found = await vector_memory.similarity_search(query, top_k=3)
            search_results.append(results_found)
        
        end_time = time.perf_counter()
        search_duration = end_time - start_time
        search_throughput = len(search_results) / search_duration
        
        memory_test = {
            "test": "Vector Memory Throughput",
            "success": storage_throughput >= 1.0 and search_throughput >= 5.0,
            "details": {
                "storage": {
                    "operations": len(storage_results),
                    "duration_seconds": round(storage_duration, 2),
                    "throughput_per_second": round(storage_throughput, 2),
                    "target_min": 1.0
                },
                "search": {
                    "operations": len(search_results),
                    "duration_seconds": round(search_duration, 2),
                    "throughput_per_second": round(search_throughput, 2),
                    "target_min": 5.0
                }
            }
        }
        
        print(f"  Storage: {len(storage_results)} ops in {storage_duration:.2f}s = {storage_throughput:.2f} ops/sec")
        print(f"  Search: {len(search_results)} ops in {search_duration:.2f}s = {search_throughput:.2f} ops/sec")
        print(f"  Status: {'✅ PASSED' if memory_test['success'] else '❌ FAILED'}")
        
        results["test_results"].append(memory_test)
        
    except Exception as e:
        print(f"  ❌ Vector Memory Test FAILED: {e}")
        results["test_results"].append({
            "test": "Vector Memory Throughput",
            "success": False,
            "error": str(e)
        })
    
    print()
    
    # Test 3: End-to-End Pipeline
    print("🔗 TEST 3: END-TO-END PIPELINE THROUGHPUT")
    print("-" * 40)
    
    try:
        from overmind_brain.brain import OVERMINDBrain
        
        brain = OVERMINDBrain()
        
        print("🔍 Testowanie 3 complete pipelines...")
        start_time = time.perf_counter()
        
        pipeline_results = []
        for i in range(3):
            market_event = {
                "event_type": "price_update",
                "symbol": "SOL/USDC",
                "price": 105.0 + i,
                "volume": 1800000,
                "timestamp": datetime.now().isoformat()
            }
            
            result = await brain.process_market_event(market_event)
            pipeline_results.append(result)
        
        end_time = time.perf_counter()
        pipeline_duration = end_time - start_time
        pipeline_throughput = len(pipeline_results) / pipeline_duration
        
        e2e_test = {
            "test": "End-to-End Pipeline Throughput",
            "success": pipeline_throughput >= 0.5,  # 0.5 pipelines/sec minimum
            "details": {
                "pipelines": len(pipeline_results),
                "duration_seconds": round(pipeline_duration, 2),
                "throughput_per_second": round(pipeline_throughput, 2),
                "target_min": 0.5
            }
        }
        
        print(f"  Pipelines: {len(pipeline_results)}")
        print(f"  Duration: {pipeline_duration:.2f}s")
        print(f"  Throughput: {pipeline_throughput:.2f} pipelines/sec")
        print(f"  Status: {'✅ PASSED' if e2e_test['success'] else '❌ FAILED'}")
        
        results["test_results"].append(e2e_test)
        
    except Exception as e:
        print(f"  ❌ E2E Pipeline Test FAILED: {e}")
        results["test_results"].append({
            "test": "End-to-End Pipeline Throughput",
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
    
    # Określ poziom throughput
    if success_rate >= 0.9:
        throughput_level = "🚀 EXCELLENT"
    elif success_rate >= 0.7:
        throughput_level = "⚡ GOOD"
    elif success_rate >= 0.5:
        throughput_level = "🎯 ACCEPTABLE"
    else:
        throughput_level = "❌ NEEDS WORK"
    
    results["throughput_level"] = throughput_level
    
    print()
    print("🏆 FINALNE WYNIKI SIMPLE THROUGHPUT TEST:")
    print("=" * 50)
    print(f"  Testy zaliczone: {passed_tests}/{total_tests}")
    print(f"  Wskaźnik sukcesu: {success_rate:.1%}")
    print(f"  Poziom throughput: {throughput_level}")
    print(f"  Status: {'✅ THROUGHPUT OK!' if results['overall_success'] else '❌ NEEDS IMPROVEMENT'}")
    
    # Zapisz wyniki
    os.makedirs('docs/testing', exist_ok=True)
    with open('docs/testing/SIMPLE_THROUGHPUT_TEST.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Wyniki zapisane w: docs/testing/SIMPLE_THROUGHPUT_TEST.json")
    
    return results

async def main():
    """Główna funkcja testowa"""
    return await test_simple_throughput()

if __name__ == "__main__":
    asyncio.run(main())
