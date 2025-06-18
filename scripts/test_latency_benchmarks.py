#!/usr/bin/env python3
"""
⚡ THE OVERMIND PROTOCOL - Latency Benchmarks Test
FRONT 3: Test wydajności - sprawdzenie czasów odpowiedzi wszystkich komponentów
"""

import asyncio
import json
import sys
import os
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add brain src to path
sys.path.append('brain/src')

class LatencyBenchmarkTester:
    """Tester benchmarków latency"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    async def measure_latency(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """Zmierz latency funkcji"""
        start_time = time.perf_counter()
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            return result, latency
        except Exception as e:
            end_time = time.perf_counter()
            latency = (end_time - start_time) * 1000
            return {"error": str(e)}, latency
    
    async def test_ai_brain_latency(self) -> Dict[str, Any]:
        """Test 3.1.1: AI Brain Latency"""
        print("\n🧠 TEST 3.1.1: AI BRAIN LATENCY")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Single Decision Latency
        print("🔍 Testowanie single decision latency...")
        try:
            from overmind_brain.decision_engine import DecisionEngine
            
            decision_engine = DecisionEngine()
            
            # Przygotuj test data
            market_data = {
                "symbol": "SOL/USDC",
                "price": 100.0,
                "volume": 1500000,
                "trend": "bullish"
            }
            
            # Wykonaj 10 pomiarów dla statystyk
            latencies = []
            decisions = []
            
            for i in range(10):
                decision, latency = await self.measure_latency(
                    decision_engine.analyze_market_data, market_data
                )
                latencies.append(latency)
                decisions.append(decision)
            
            # Oblicz statystyki
            avg_latency = statistics.mean(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
            p99_latency = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
            
            single_decision_test = {
                "test": "Single Decision Latency",
                "success": avg_latency < 5000,  # 5s target
                "details": {
                    "measurements": 10,
                    "avg_latency_ms": round(avg_latency, 2),
                    "p95_latency_ms": round(p95_latency, 2),
                    "p99_latency_ms": round(p99_latency, 2),
                    "min_latency_ms": round(min(latencies), 2),
                    "max_latency_ms": round(max(latencies), 2),
                    "target_ms": 5000,
                    "target_met": avg_latency < 5000
                }
            }
            
            print(f"  Single Decision: {'✅ PASSED' if single_decision_test['success'] else '❌ FAILED'}")
            print(f"    Avg Latency: {avg_latency:.2f}ms (target: <5000ms)")
            print(f"    P95 Latency: {p95_latency:.2f}ms")
            print(f"    P99 Latency: {p99_latency:.2f}ms")
            
        except Exception as e:
            single_decision_test = {
                "test": "Single Decision Latency",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Single Decision: ❌ FAILED - {str(e)}")
        
        tests.append(single_decision_test)
        
        # Test 2: Batch Decisions Latency
        print("🔍 Testowanie batch decisions latency...")
        try:
            # Przygotuj batch data
            batch_data = [
                {"symbol": "SOL/USDC", "price": 100.0 + i, "volume": 1500000}
                for i in range(10)
            ]
            
            # Zmierz batch processing
            batch_start = time.perf_counter()
            batch_decisions = []
            
            for data in batch_data:
                decision, _ = await self.measure_latency(
                    decision_engine.analyze_market_data, data
                )
                batch_decisions.append(decision)
            
            batch_end = time.perf_counter()
            batch_latency = (batch_end - batch_start) * 1000
            
            batch_test = {
                "test": "Batch Decisions Latency",
                "success": batch_latency < 10000,  # 10s target for 10 decisions
                "details": {
                    "batch_size": 10,
                    "total_latency_ms": round(batch_latency, 2),
                    "avg_per_decision_ms": round(batch_latency / 10, 2),
                    "target_ms": 10000,
                    "target_met": batch_latency < 10000
                }
            }
            
            print(f"  Batch Decisions: {'✅ PASSED' if batch_test['success'] else '❌ FAILED'}")
            print(f"    Total Latency: {batch_latency:.2f}ms (target: <10000ms)")
            print(f"    Avg per Decision: {batch_latency/10:.2f}ms")
            
        except Exception as e:
            batch_test = {
                "test": "Batch Decisions Latency",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Batch Decisions: ❌ FAILED - {str(e)}")
        
        tests.append(batch_test)
        
        # Test 3: Complex Analysis Latency
        print("🔍 Testowanie complex analysis latency...")
        try:
            from overmind_brain.market_analyzer import MarketAnalyzer
            from overmind_brain.risk_analyzer import RiskAnalyzer
            
            market_analyzer = MarketAnalyzer()
            risk_analyzer = RiskAnalyzer()
            
            # Complex analysis pipeline
            complex_data = {
                "symbol": "SOL/USDC",
                "price": 105.0,
                "volume": 1800000
            }
            historical_data = [
                {"price": 95 + i, "volume": 1000000 + i*100000}
                for i in range(20)  # More historical data
            ]
            
            # Zmierz full pipeline
            pipeline_start = time.perf_counter()
            
            # Market analysis
            market_analysis, _ = await self.measure_latency(
                market_analyzer.analyze_market, complex_data, historical_data
            )
            
            # Decision making
            decision, _ = await self.measure_latency(
                decision_engine.analyze_market_data, complex_data
            )
            
            # Risk assessment
            risk_assessment, _ = await self.measure_latency(
                risk_analyzer.assess_risk,
                complex_data,
                {"action": "BUY", "position_size": 1.0},
                {"positions": {"SOL": 1.0, "USDC": 500}}
            )
            
            pipeline_end = time.perf_counter()
            pipeline_latency = (pipeline_end - pipeline_start) * 1000
            
            complex_test = {
                "test": "Complex Analysis Latency",
                "success": pipeline_latency < 15000,  # 15s target for full pipeline
                "details": {
                    "pipeline_latency_ms": round(pipeline_latency, 2),
                    "components": ["MarketAnalyzer", "DecisionEngine", "RiskAnalyzer"],
                    "target_ms": 15000,
                    "target_met": pipeline_latency < 15000
                }
            }
            
            print(f"  Complex Analysis: {'✅ PASSED' if complex_test['success'] else '❌ FAILED'}")
            print(f"    Pipeline Latency: {pipeline_latency:.2f}ms (target: <15000ms)")
            
        except Exception as e:
            complex_test = {
                "test": "Complex Analysis Latency",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Complex Analysis: ❌ FAILED - {str(e)}")
        
        tests.append(complex_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 AI Brain Latency Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "AI Brain Latency",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_vector_memory_latency(self) -> Dict[str, Any]:
        """Test 3.1.3: Vector Memory Latency"""
        print("\n🧮 TEST 3.1.3: VECTOR MEMORY LATENCY")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Experience Storage Latency
        print("🔍 Testowanie experience storage latency...")
        try:
            from overmind_brain.vector_memory import VectorMemory
            
            vector_memory = VectorMemory()
            
            # Przygotuj test experiences
            test_experiences = [
                {
                    "situation": {"market": f"test_{i}", "price": 100 + i},
                    "decision": {"action": "BUY", "confidence": 0.8},
                    "outcome": {"profit": 2.5}
                }
                for i in range(10)
            ]
            
            # Zmierz storage latency
            storage_latencies = []
            
            for exp in test_experiences:
                _, latency = await self.measure_latency(
                    vector_memory.store_experience,
                    exp["situation"],
                    exp["decision"],
                    outcome=exp["outcome"]
                )
                storage_latencies.append(latency)
            
            avg_storage_latency = statistics.mean(storage_latencies)
            p95_storage_latency = statistics.quantiles(storage_latencies, n=20)[18]
            
            storage_test = {
                "test": "Experience Storage Latency",
                "success": avg_storage_latency < 100,  # 100ms target
                "details": {
                    "measurements": len(storage_latencies),
                    "avg_latency_ms": round(avg_storage_latency, 2),
                    "p95_latency_ms": round(p95_storage_latency, 2),
                    "target_ms": 100,
                    "target_met": avg_storage_latency < 100
                }
            }
            
            print(f"  Storage Latency: {'✅ PASSED' if storage_test['success'] else '❌ FAILED'}")
            print(f"    Avg Latency: {avg_storage_latency:.2f}ms (target: <100ms)")
            print(f"    P95 Latency: {p95_storage_latency:.2f}ms")
            
        except Exception as e:
            storage_test = {
                "test": "Experience Storage Latency",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Storage Latency: ❌ FAILED - {str(e)}")
        
        tests.append(storage_test)
        
        # Test 2: Similarity Search Latency
        print("🔍 Testowanie similarity search latency...")
        try:
            # Wykonaj wiele wyszukiwań
            search_queries = [
                "bullish market condition",
                "high volatility trading",
                "profitable buy signal",
                "risk management scenario",
                "trend reversal pattern"
            ]
            
            search_latencies = []
            
            for query in search_queries:
                _, latency = await self.measure_latency(
                    vector_memory.similarity_search, query, top_k=5
                )
                search_latencies.append(latency)
            
            avg_search_latency = statistics.mean(search_latencies)
            p95_search_latency = statistics.quantiles(search_latencies, n=20)[18]
            
            search_test = {
                "test": "Similarity Search Latency",
                "success": avg_search_latency < 200,  # 200ms target
                "details": {
                    "measurements": len(search_latencies),
                    "avg_latency_ms": round(avg_search_latency, 2),
                    "p95_latency_ms": round(p95_search_latency, 2),
                    "target_ms": 200,
                    "target_met": avg_search_latency < 200
                }
            }
            
            print(f"  Search Latency: {'✅ PASSED' if search_test['success'] else '❌ FAILED'}")
            print(f"    Avg Latency: {avg_search_latency:.2f}ms (target: <200ms)")
            print(f"    P95 Latency: {p95_search_latency:.2f}ms")
            
        except Exception as e:
            search_test = {
                "test": "Similarity Search Latency",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  Search Latency: ❌ FAILED - {str(e)}")
        
        tests.append(search_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 Vector Memory Latency Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "Vector Memory Latency",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_end_to_end_latency(self) -> Dict[str, Any]:
        """Test 3.1.4: End-to-End Latency"""
        print("\n🔗 TEST 3.1.4: END-TO-END LATENCY")
        print("-" * 50)
        
        tests = []
        
        # Test 1: Market Event → Decision Pipeline
        print("🔍 Testowanie market event → decision pipeline...")
        try:
            from overmind_brain.brain import OVERMINDBrain
            
            brain = OVERMINDBrain()
            
            # Symulacja market event
            market_event = {
                "event_type": "price_update",
                "symbol": "SOL/USDC",
                "price": 105.0,
                "volume": 1800000,
                "timestamp": datetime.now().isoformat()
            }
            
            # Zmierz end-to-end pipeline
            e2e_latencies = []
            
            for i in range(5):  # 5 pomiarów
                _, latency = await self.measure_latency(
                    brain.process_market_event, market_event
                )
                e2e_latencies.append(latency)
            
            avg_e2e_latency = statistics.mean(e2e_latencies)
            p95_e2e_latency = statistics.quantiles(e2e_latencies, n=20)[18]
            
            e2e_test = {
                "test": "Market Event → Decision Pipeline",
                "success": avg_e2e_latency < 10000,  # 10s target
                "details": {
                    "measurements": len(e2e_latencies),
                    "avg_latency_ms": round(avg_e2e_latency, 2),
                    "p95_latency_ms": round(p95_e2e_latency, 2),
                    "target_ms": 10000,
                    "target_met": avg_e2e_latency < 10000
                }
            }
            
            print(f"  E2E Pipeline: {'✅ PASSED' if e2e_test['success'] else '❌ FAILED'}")
            print(f"    Avg Latency: {avg_e2e_latency:.2f}ms (target: <10000ms)")
            print(f"    P95 Latency: {p95_e2e_latency:.2f}ms")
            
        except Exception as e:
            e2e_test = {
                "test": "Market Event → Decision Pipeline",
                "success": False,
                "details": {"error": str(e)}
            }
            print(f"  E2E Pipeline: ❌ FAILED - {str(e)}")
        
        tests.append(e2e_test)
        
        overall_success = all(t["success"] for t in tests)
        print(f"\n📊 End-to-End Latency Test: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        return {
            "test_name": "End-to-End Latency",
            "success": overall_success,
            "tests": tests,
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_latency_benchmarks(self) -> Dict[str, Any]:
        """Uruchom wszystkie testy latency"""
        print("⚡ THE OVERMIND PROTOCOL - LATENCY BENCHMARKS TEST")
        print("=" * 65)
        print("🎯 FRONT 3: Test wydajności - sprawdzenie czasów odpowiedzi")
        print()
        
        # Uruchom wszystkie testy
        test_results = []
        
        # Test 3.1.1: AI Brain Latency
        ai_brain_result = await self.test_ai_brain_latency()
        test_results.append(ai_brain_result)
        
        # Test 3.1.3: Vector Memory Latency
        vector_memory_result = await self.test_vector_memory_latency()
        test_results.append(vector_memory_result)
        
        # Test 3.1.4: End-to-End Latency
        e2e_result = await self.test_end_to_end_latency()
        test_results.append(e2e_result)
        
        # Oblicz ogólny wynik
        overall_success = all(result["success"] for result in test_results)
        passed_tests = sum(1 for result in test_results if result["success"])
        
        # Określ poziom wydajności
        success_rate = passed_tests / len(test_results)
        if success_rate >= 0.95:
            performance_level = "🚀 EXCELLENT"
        elif success_rate >= 0.85:
            performance_level = "⚡ GOOD"
        elif success_rate >= 0.70:
            performance_level = "🎯 ACCEPTABLE"
        elif success_rate >= 0.50:
            performance_level = "⚠️ NEEDS OPTIMIZATION"
        else:
            performance_level = "❌ POOR"
        
        print(f"\n🏆 FINALNE WYNIKI LATENCY BENCHMARKS:")
        print("=" * 55)
        print(f"  Testy zaliczone: {passed_tests}/{len(test_results)}")
        print(f"  Wskaźnik sukcesu: {success_rate:.1%}")
        print(f"  Poziom wydajności: {performance_level}")
        print(f"  Status: {'✅ LATENCY TARGETS MET!' if overall_success else '❌ NEEDS OPTIMIZATION'}")
        
        return {
            "test_timestamp": self.start_time.isoformat(),
            "test_duration": str(datetime.now() - self.start_time),
            "overall_success": overall_success,
            "performance_level": performance_level,
            "success_rate": success_rate,
            "passed_tests": passed_tests,
            "total_tests": len(test_results),
            "test_results": test_results,
            "status": "LATENCY_TARGETS_MET" if overall_success else "NEEDS_OPTIMIZATION"
        }

async def main():
    """Główna funkcja testowa"""
    tester = LatencyBenchmarkTester()
    results = await tester.run_latency_benchmarks()
    
    # Zapisz wyniki
    os.makedirs('docs/testing', exist_ok=True)
    with open('docs/testing/LATENCY_BENCHMARKS_TEST.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Wyniki zapisane w: docs/testing/LATENCY_BENCHMARKS_TEST.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
