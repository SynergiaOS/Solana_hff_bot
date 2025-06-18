#!/usr/bin/env python3
"""
🧠 THE OVERMIND PROTOCOL - Real AI Brain Test
Test rzeczywistych komponentów AI Brain
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add brain src to path
sys.path.append('brain/src')

async def test_real_ai_components():
    """Test rzeczywistych komponentów AI Brain"""
    print("🧠 THE OVERMIND PROTOCOL - TEST RZECZYWISTYCH KOMPONENTÓW AI")
    print("=" * 65)
    print()
    
    results = {
        "test_timestamp": datetime.now().isoformat(),
        "components_tested": [],
        "overall_status": "UNKNOWN"
    }
    
    # Test 1: DecisionEngine
    print("🎯 TEST 1: DECISION ENGINE")
    print("-" * 30)
    try:
        from overmind_brain.decision_engine import DecisionEngine
        
        # Inicjalizacja
        decision_engine = DecisionEngine()
        print("✅ DecisionEngine zainicjalizowany")
        
        # Test analizy
        market_data = {
            "symbol": "SOL/USDC",
            "price": 100.0,
            "price_change_24h": 5.2,
            "volume_24h": 1500000,
            "rsi": 65,
            "trend": "bullish"
        }
        
        # Wywołanie analizy (prawdziwa metoda)
        print("🔍 Testowanie analizy rynku...")
        decision = await decision_engine.analyze_market_data(market_data)
        
        print(f"  Decision: {decision.action}")
        print(f"  Confidence: {decision.confidence:.2f}")
        print(f"  Reasoning: {decision.reasoning[:50]}...")

        results["components_tested"].append({
            "component": "DecisionEngine",
            "status": "WORKING",
            "test_result": {
                "action": decision.action,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "symbol": decision.symbol
            }
        })
        
    except Exception as e:
        print(f"❌ DecisionEngine error: {e}")
        results["components_tested"].append({
            "component": "DecisionEngine", 
            "status": "ERROR",
            "error": str(e)
        })
    
    print()
    
    # Test 2: RiskAnalyzer
    print("🛡️ TEST 2: RISK ANALYZER")
    print("-" * 30)
    try:
        from overmind_brain.risk_analyzer import RiskAnalyzer
        
        risk_analyzer = RiskAnalyzer()
        print("✅ RiskAnalyzer zainicjalizowany")
        
        # Test analizy ryzyka
        market_data = {
            "symbol": "SOL/USDC",
            "price": 100.0,
            "volatility": 0.12
        }
        decision_data = {
            "action": "BUY",
            "position_size": 1.5
        }
        portfolio_data = {
            "positions": {"SOL": 1.5, "USDC": 200}
        }

        print("🔍 Testowanie analizy ryzyka...")
        risk_analysis = await risk_analyzer.assess_risk(market_data, decision_data, portfolio_data)
        
        print(f"  Risk Level: {risk_analysis.risk_level}")
        print(f"  Risk Score: {risk_analysis.overall_risk_score:.2f}")
        print(f"  Max Position: {risk_analysis.position_size_recommendation:.2f}")

        results["components_tested"].append({
            "component": "RiskAnalyzer",
            "status": "WORKING",
            "test_result": {
                "risk_level": risk_analysis.risk_level,
                "risk_score": risk_analysis.overall_risk_score,
                "position_size_recommendation": risk_analysis.position_size_recommendation,
                "risk_factors": risk_analysis.risk_factors
            }
        })
        
    except Exception as e:
        print(f"❌ RiskAnalyzer error: {e}")
        results["components_tested"].append({
            "component": "RiskAnalyzer",
            "status": "ERROR",
            "error": str(e)
        })
    
    print()
    
    # Test 3: MarketAnalyzer
    print("📊 TEST 3: MARKET ANALYZER")
    print("-" * 30)
    try:
        from overmind_brain.market_analyzer import MarketAnalyzer
        
        market_analyzer = MarketAnalyzer()
        print("✅ MarketAnalyzer zainicjalizowany")
        
        # Test analizy rynku
        current_data = {
            "symbol": "SOL/USDC",
            "price": 102.0,
            "volume": 1600000
        }
        historical_data = [
            {"price": 95, "volume": 1000000},
            {"price": 97, "volume": 1200000},
            {"price": 99, "volume": 1500000},
            {"price": 100, "volume": 1800000}
        ]

        print("🔍 Testowanie analizy technicznej...")
        analysis = await market_analyzer.analyze_market(current_data, historical_data)
        
        print(f"  Trend: {analysis.trend_direction}")
        print(f"  Strength: {analysis.trend_strength:.2f}")
        print(f"  Patterns: {len(analysis.pattern_signals)} detected")

        results["components_tested"].append({
            "component": "MarketAnalyzer",
            "status": "WORKING",
            "test_result": {
                "trend_direction": analysis.trend_direction,
                "trend_strength": analysis.trend_strength,
                "pattern_signals": analysis.pattern_signals,
                "support_levels": analysis.support_levels,
                "resistance_levels": analysis.resistance_levels,
                "market_sentiment": analysis.market_sentiment
            }
        })
        
    except Exception as e:
        print(f"❌ MarketAnalyzer error: {e}")
        results["components_tested"].append({
            "component": "MarketAnalyzer",
            "status": "ERROR", 
            "error": str(e)
        })
    
    print()
    
    # Test 4: VectorMemory
    print("🧮 TEST 4: VECTOR MEMORY")
    print("-" * 30)
    try:
        from overmind_brain.vector_memory import VectorMemory
        
        vector_memory = VectorMemory()
        print("✅ VectorMemory zainicjalizowany")
        
        # Test pamięci wektorowej
        print("🔍 Testowanie pamięci wektorowej...")
        
        # Test dodawania doświadczenia
        situation = {
            "market_condition": "bullish_trend",
            "price": 100.0,
            "volume": 1500000
        }
        decision = {
            "action": "BUY",
            "confidence": 0.8,
            "position_size": 1.0
        }
        outcome = {
            "result": "profitable",
            "profit_pct": 3.2
        }

        memory_id = await vector_memory.store_experience(situation, decision, outcome=outcome)
        print(f"  Experience stored: {memory_id is not None}")

        # Test wyszukiwania podobnych doświadczeń
        query = "bullish trend market condition"
        similar = await vector_memory.similarity_search(query, top_k=3)
        print(f"  Similar experiences found: {len(similar)}")
        
        results["components_tested"].append({
            "component": "VectorMemory",
            "status": "WORKING",
            "test_result": {
                "storage": {"memory_id": memory_id},
                "retrieval": {"count": len(similar)}
            }
        })
        
    except Exception as e:
        print(f"❌ VectorMemory error: {e}")
        results["components_tested"].append({
            "component": "VectorMemory",
            "status": "ERROR",
            "error": str(e)
        })
    
    print()
    
    # Test 5: OVERMINDBrain (Main Orchestrator)
    print("🧠 TEST 5: OVERMIND BRAIN (MAIN ORCHESTRATOR)")
    print("-" * 50)
    try:
        from overmind_brain.brain import OVERMINDBrain
        
        brain = OVERMINDBrain()
        print("✅ OVERMINDBrain zainicjalizowany")
        
        # Test głównej logiki
        print("🔍 Testowanie głównej logiki AI...")
        
        # Test pełnej analizy
        market_event_data = {
            "event_type": "price_update",
            "symbol": "SOL/USDC",
            "price": 100.0,
            "volume": 1500000,
            "timestamp": datetime.now().isoformat()
        }

        brain_decision = await brain.process_market_event(market_event_data)

        if brain_decision:
            print(f"  Final Decision: {brain_decision.action}")
            print(f"  Confidence: {brain_decision.confidence:.2f}")
            print(f"  Symbol: {brain_decision.symbol}")
        else:
            print("  No decision made (normal for some market events)")
        
        results["components_tested"].append({
            "component": "OVERMINDBrain",
            "status": "WORKING",
            "test_result": {
                "decision_made": brain_decision is not None,
                "action": brain_decision.action if brain_decision else None,
                "confidence": brain_decision.confidence if brain_decision else None,
                "symbol": brain_decision.symbol if brain_decision else None
            }
        })
        
    except Exception as e:
        print(f"❌ OVERMINDBrain error: {e}")
        results["components_tested"].append({
            "component": "OVERMINDBrain",
            "status": "ERROR",
            "error": str(e)
        })
    
    # Podsumowanie
    print()
    print("📊 PODSUMOWANIE TESTÓW RZECZYWISTYCH KOMPONENTÓW")
    print("=" * 55)
    
    working_components = [c for c in results["components_tested"] if c["status"] == "WORKING"]
    error_components = [c for c in results["components_tested"] if c["status"] == "ERROR"]
    
    print(f"✅ Działające komponenty: {len(working_components)}/5")
    print(f"❌ Komponenty z błędami: {len(error_components)}/5")
    
    for component in working_components:
        print(f"  ✅ {component['component']}")
    
    for component in error_components:
        print(f"  ❌ {component['component']}: {component.get('error', 'Unknown error')}")
    
    # Określ ogólny status
    if len(working_components) == 5:
        overall_status = "ALL_WORKING"
        status_msg = "🎉 WSZYSTKIE KOMPONENTY DZIAŁAJĄ!"
    elif len(working_components) >= 3:
        overall_status = "MOSTLY_WORKING"
        status_msg = "⚠️ WIĘKSZOŚĆ KOMPONENTÓW DZIAŁA"
    else:
        overall_status = "NEEDS_WORK"
        status_msg = "❌ WYMAGA POPRAWY"
    
    results["overall_status"] = overall_status
    results["working_components"] = len(working_components)
    results["total_components"] = 5
    
    print(f"\n🎯 STATUS OGÓLNY: {status_msg}")
    
    # Zapisz wyniki
    os.makedirs('docs/testing', exist_ok=True)
    with open('docs/testing/REAL_AI_COMPONENTS_TEST.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Wyniki zapisane w: docs/testing/REAL_AI_COMPONENTS_TEST.json")
    
    return results

async def main():
    """Główna funkcja testowa"""
    results = await test_real_ai_components()
    return results

if __name__ == "__main__":
    asyncio.run(main())
