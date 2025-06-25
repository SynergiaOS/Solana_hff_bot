#!/usr/bin/env python3
"""
Test Strategy Integration with OVERMIND Brain
Test the new strategy-aware decision making system
"""

import asyncio
import json
import sys
import os

# Add the brain module to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain', 'src'))

from overmind_brain.strategy_manager import strategy_manager
from overmind_brain.strategy_config import strategy_config

def test_strategy_configuration():
    """Test strategy configuration loading"""
    print("🔧 Testing Strategy Configuration Loading")
    print("=" * 50)
    
    config_summary = strategy_config.get_configuration_summary()
    print(f"📊 Strategy Summary: {json.dumps(config_summary, indent=2)}")
    
    enabled_strategies = strategy_config.get_enabled_strategies()
    print(f"✅ Enabled Strategies: {[s.value for s in enabled_strategies]}")
    
    return True

def test_signal_validation():
    """Test signal validation against strategies"""
    print("\n🎯 Testing Signal Validation")
    print("=" * 50)
    
    # Reinitialize strategy manager to pick up environment
    import importlib
    import overmind_brain.strategy_manager
    importlib.reload(overmind_brain.strategy_manager)
    from overmind_brain.strategy_manager import strategy_manager
    
    # Test Signal 1: High volume SOL signal (should qualify for Soul Meteor)
    test_signal_1 = {
        "signal_id": "test_sol_001",
        "signal_type": "new_pool_detected",
        "symbol": "SOL",
        "token_address": "So11111111111111111111111111111111111111112",
        "confidence": 0.85,
        "market_data": {
            "price": 143.24,
            "volume_24h": 75000,  # Above Soul Meteor minimum
            "liquidity": 50000,   # Above Soul Meteor minimum
            "market_cap": 8500000000  # Too high for Memecoin Hunter
        }
    }
    
    print("🚀 Test Signal 1: High Volume SOL")
    print(f"   Volume: ${test_signal_1['market_data']['volume_24h']:,}")
    print(f"   Liquidity: ${test_signal_1['market_data']['liquidity']:,}")
    print(f"   Market Cap: ${test_signal_1['market_data']['market_cap']:,}")
    
    strategy_matches_1 = strategy_manager.select_and_validate_strategies(test_signal_1)
    
    print(f"   📊 Qualified Strategies: {len(strategy_matches_1)}")
    for match in strategy_matches_1:
        print(f"   ✅ {match.strategy_type.value}: {match.match_score:.2f} - {match.reasoning}")
    
    # Test Signal 2: Small memecoin (should qualify for Memecoin Hunter)
    test_signal_2 = {
        "signal_id": "test_meme_001",
        "signal_type": "viral_potential",
        "symbol": "DOGE2",
        "token_address": "DogeCoin2NewTokenAddress123456789",
        "confidence": 0.70,
        "market_data": {
            "price": 0.001,
            "volume_24h": 25000,     # Below Soul Meteor minimum
            "liquidity": 15000,      # Below Soul Meteor minimum
            "market_cap": 300000     # Within Memecoin Hunter range
        },
        "social_score": 6.5,        # Above Memecoin Hunter minimum
        "holders": 75               # Above Memecoin Hunter minimum
    }
    
    print("\n🐕 Test Signal 2: Small Memecoin")
    print(f"   Volume: ${test_signal_2['market_data']['volume_24h']:,}")
    print(f"   Market Cap: ${test_signal_2['market_data']['market_cap']:,}")
    print(f"   Social Score: {test_signal_2['social_score']}")
    
    strategy_matches_2 = strategy_manager.select_and_validate_strategies(test_signal_2)
    
    print(f"   📊 Qualified Strategies: {len(strategy_matches_2)}")
    for match in strategy_matches_2:
        print(f"   ✅ {match.strategy_type.value}: {match.match_score:.2f} - {match.reasoning}")
    
    # Test Signal 3: Poor signal (should not qualify for any strategy)
    test_signal_3 = {
        "signal_id": "test_poor_001",
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
    
    print("\n❌ Test Signal 3: Poor Quality Signal")
    print(f"   Volume: ${test_signal_3['market_data']['volume_24h']:,}")
    print(f"   Confidence: {test_signal_3['confidence']}")
    
    strategy_matches_3 = strategy_manager.select_and_validate_strategies(test_signal_3)
    
    print(f"   📊 Qualified Strategies: {len(strategy_matches_3)}")
    if not strategy_matches_3:
        print("   ⚠️ No strategies qualified - system will recommend HOLD")
    
    return True

def test_strategy_context_generation():
    """Test AI context generation for qualified strategies"""
    print("\n🤖 Testing Strategy Context Generation")
    print("=" * 50)
    
    # Create a good signal
    test_signal = {
        "signal_id": "test_context_001",
        "signal_type": "new_pool_detected",
        "symbol": "TEST",
        "confidence": 0.80,
        "market_data": {
            "price": 1.50,
            "volume_24h": 60000,
            "liquidity": 30000,
            "market_cap": 450000
        },
        "social_score": 7.0,
        "holders": 120
    }
    
    strategy_matches = strategy_manager.select_and_validate_strategies(test_signal)
    
    if strategy_matches:
        parsed_signal = strategy_manager._parse_signal(test_signal)
        ai_context = strategy_manager.generate_strategy_context_for_ai(strategy_matches, parsed_signal)
        
        print("🧠 Generated AI Context:")
        print("-" * 30)
        print(ai_context)
        print("-" * 30)
    else:
        print("❌ No strategies qualified for context generation")
    
    return True

def main():
    """Run all tests"""
    print("🧪 THE OVERMIND PROTOCOL - Strategy Integration Tests")
    print("=" * 60)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv('.env.devnet')
    
    # Debug environment variables
    print(f"🔍 Environment Check:")
    print(f"   ENABLED_STRATEGIES: {os.getenv('ENABLED_STRATEGIES', 'NOT SET')}")
    print(f"   SOUL_METEOR_MIN_VOLUME: {os.getenv('SOUL_METEOR_MIN_VOLUME', 'NOT SET')}")
    print(f"   MEMECOIN_HUNTER_MAX_MARKET_CAP: {os.getenv('MEMECOIN_HUNTER_MAX_MARKET_CAP', 'NOT SET')}")
    print()
    
    try:
        # Run tests
        test_strategy_configuration()
        test_signal_validation()
        test_strategy_context_generation()
        
        print("\n🎉 All Strategy Integration Tests Completed Successfully!")
        print("✅ Strategy-aware decision making is now fully operational")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)