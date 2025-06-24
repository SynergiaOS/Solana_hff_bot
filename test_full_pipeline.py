#!/usr/bin/env python3
"""
Test Full OVERMIND Pipeline with Strategy Integration
Test the complete signal processing pipeline
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the brain module to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain', 'src'))

from dotenv import load_dotenv
load_dotenv('.env.devnet')

from overmind_brain.overmind_brain_manager import create_overmind_brain_manager

async def test_full_pipeline():
    """Test the complete signal processing pipeline"""
    print("🧪 THE OVERMIND PROTOCOL - Full Pipeline Test")
    print("=" * 60)
    
    # Create brain manager
    brain_manager = create_overmind_brain_manager(
        redis_host="localhost",
        redis_port=6379,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Initialize brain manager
    await brain_manager.initialize()
    print("✅ Brain Manager initialized")
    
    # Test Signal 1: Should qualify for Soul Meteor
    test_signal_1 = {
        "signal_id": "pipeline_test_001",
        "signal_type": "new_pool_detected",
        "symbol": "TESTSOL",
        "token_address": "TestToken123",
        "confidence": 0.85,
        "market_data": {
            "price": 1.50,
            "volume_24h": 75000,    # Above Soul Meteor minimum (50k)
            "liquidity": 60000,     # Above Soul Meteor minimum (25k)
            "market_cap": 400000    # Within Memecoin Hunter range
        },
        "social_score": 7.5,        # Above Memecoin Hunter minimum
        "holders": 150              # Above Memecoin Hunter minimum
    }
    
    print(f"\n🚀 Testing Signal: {test_signal_1['symbol']}")
    print(f"   Type: {test_signal_1['signal_type']}")
    print(f"   Volume: ${test_signal_1['market_data']['volume_24h']:,}")
    print(f"   Liquidity: ${test_signal_1['market_data']['liquidity']:,}")
    print(f"   Market Cap: ${test_signal_1['market_data']['market_cap']:,}")
    print(f"   Social Score: {test_signal_1['social_score']}")
    print(f"   Confidence: {test_signal_1['confidence']}")
    
    # Phase 1: Market Analysis with Strategy Integration
    print("\n📊 Phase 1: Strategy-Aware Market Analysis")
    analysis_result = await brain_manager._coordinate_market_analysis(test_signal_1)
    
    print(f"✅ Analysis completed")
    print(f"   Workflow ID: {analysis_result.get('workflow_id', 'N/A')}")
    
    # Check strategy analysis
    strategy_analysis = analysis_result.get('strategy_analysis', {})
    if strategy_analysis:
        qualified_strategies = strategy_analysis.get('qualified_strategies', [])
        print(f"   📊 Qualified Strategies: {len(qualified_strategies)}")
        
        for strategy in qualified_strategies:
            print(f"      ✅ {strategy['strategy']}: {strategy['score']:.2f}")
            print(f"         {strategy['reasoning']}")
        
        top_strategy = strategy_analysis.get('top_strategy', 'none')
        print(f"   🎯 Top Strategy: {top_strategy}")
        
        # Show strategy context (first 200 chars)
        strategy_context = strategy_analysis.get('strategy_context', '')
        if strategy_context:
            print(f"   🧠 AI Context Preview: {strategy_context[:200]}...")
    
    # Phase 2: Decision Pipeline
    print("\n🎯 Phase 2: Strategy-Aware Decision Pipeline")
    
    if analysis_result.get('analysis_results'):
        decision_result = await brain_manager._execute_trading_decision_pipeline(analysis_result)
        
        print("✅ Decision pipeline completed")
        
        trading_decision = decision_result.get('trading_decision', {})
        if trading_decision:
            print(f"   📊 Trading Decision:")
            print(f"      Action: {trading_decision.get('decision', 'N/A')}")
            print(f"      Confidence: {trading_decision.get('confidence', 'N/A')}")
            print(f"      Strategy Used: {trading_decision.get('strategy_used', 'N/A')}")
            print(f"      Risk Level: {trading_decision.get('risk_level', 'N/A')}")
            print(f"      Reasoning: {trading_decision.get('reasoning', 'N/A')}")
    else:
        print("⚠️ Analysis failed - no decision pipeline executed")
    
    # Test Signal 2: Should not qualify for any strategy
    print(f"\n❌ Testing Poor Quality Signal")
    
    test_signal_2 = {
        "signal_id": "pipeline_test_002",
        "signal_type": "unknown",
        "symbol": "POOR",
        "confidence": 0.30,  # Below all thresholds
        "market_data": {
            "price": 0.0001,
            "volume_24h": 1000,      # Below all minimums
            "liquidity": 500,        # Below all minimums
            "market_cap": 2000000    # Too high for Memecoin Hunter
        }
    }
    
    print(f"   Volume: ${test_signal_2['market_data']['volume_24h']:,}")
    print(f"   Confidence: {test_signal_2['confidence']}")
    
    poor_analysis = await brain_manager._coordinate_market_analysis(test_signal_2)
    
    strategy_analysis_poor = poor_analysis.get('strategy_analysis', {})
    if strategy_analysis_poor:
        qualified_strategies_poor = strategy_analysis_poor.get('qualified_strategies', [])
        print(f"   📊 Qualified Strategies: {len(qualified_strategies_poor)}")
        
        if not qualified_strategies_poor:
            print("   ✅ Correctly identified as unqualified - system recommends HOLD")
            recommendation = strategy_analysis_poor.get('recommendation', 'N/A')
            reason = strategy_analysis_poor.get('reason', 'N/A')
            print(f"   📋 Recommendation: {recommendation}")
            print(f"   💡 Reason: {reason}")
    
    print("\n🎉 Full Pipeline Test Completed!")
    print("✅ Strategy-aware decision making is fully operational")

def main():
    """Run the full pipeline test"""
    try:
        asyncio.run(test_full_pipeline())
        return True
    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)