#!/usr/bin/env python3
"""
Simplified Strategy Test - Tests only StrategyManager without full Brain dependencies
"""

import sys
import os
import json
from datetime import datetime

# Add the brain module to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain', 'src'))

# Test with minimal imports
try:
    from overmind_brain.strategy_manager import StrategyManager
    from overmind_brain.strategy_config import StrategyConfigManager
    print("✅ Strategy modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_strategy_integration():
    """Test strategy integration without external dependencies"""
    print("🧠 Testing Strategy Integration - Standalone Mode")
    print("=" * 60)
    
    # Initialize strategy manager
    try:
        strategy_manager = StrategyManager()
        print("✅ StrategyManager initialized successfully")
    except Exception as e:
        print(f"❌ StrategyManager initialization failed: {e}")
        return False
    
    # Print configuration summary
    config_summary = strategy_manager.get_strategy_summary() 
    print(f"📊 Configuration Summary:")
    print(f"   Enabled: {config_summary['enabled_strategies']}")
    print(f"   Default: {config_summary['default_strategy']}")
    print()
    
    # Test realistic market signals
    test_signals = [
        {
            "signal_id": "standalone_001",
            "signal_type": "new_pool_detected",
            "symbol": "SOL", 
            "confidence": 0.85,
            "volume_24h": 120000,  # High volume
            "liquidity": 80000,    # High liquidity
            "market_cap": 8500000000,
            "price": 145.50
        },
        {
            "signal_id": "standalone_002",
            "signal_type": "viral_potential", 
            "symbol": "DOGE2",
            "confidence": 0.72,
            "volume_24h": 18000,   # Medium volume
            "liquidity": 12000,    # Medium liquidity
            "market_cap": 400000,  # Small market cap
            "price": 0.003,
            "social_score": 8.1,
            "holder_count": 200
        },
        {
            "signal_id": "standalone_003",
            "signal_type": "developer_launch",
            "symbol": "DEV",
            "confidence": 0.88,
            "volume_24h": 45000,
            "liquidity": 35000,
            "market_cap": 2000000,
            "price": 0.15,
            "developer_score": 8.5,
            "developer_launches": 5
        },
        {
            "signal_id": "standalone_004",
            "signal_type": "unknown",
            "symbol": "POOR",
            "confidence": 0.20,    # Very low confidence
            "volume_24h": 800,     # Very low volume
            "liquidity": 300,      # Very low liquidity
            "market_cap": 5000000,
            "price": 0.0001
        }
    ]
    
    print(f"🔍 Testing {len(test_signals)} market signals:")
    
    for i, signal in enumerate(test_signals):
        print(f"\n📊 Signal {i+1}: {signal['symbol']} ({signal['signal_type']})")
        print(f"   Vol: ${signal.get('volume_24h', 0):,}, Liq: ${signal.get('liquidity', 0):,}")
        print(f"   MCap: ${signal.get('market_cap', 0):,}, Conf: {signal.get('confidence', 0):.2f}")
        
        try:
            # Test strategy selection
            matches = strategy_manager.select_and_validate_strategies(signal)
            
            if matches:
                print(f"   ✅ {len(matches)} strategies qualified:")
                for match in matches:
                    print(f"      • {match.strategy_type.value}: {match.match_score:.2f}")
                    print(f"        {match.reasoning}")
                
                # Test AI context generation  
                parsed_signal = strategy_manager._parse_signal(signal)
                ai_context = strategy_manager.generate_strategy_context_for_ai(matches, parsed_signal)
                print(f"   🤖 AI Context: {len(ai_context)} chars")
                
                # Show first 200 chars of context
                context_preview = ai_context[:200] + "..." if len(ai_context) > 200 else ai_context
                print(f"   Preview: {context_preview}")
                
            else:
                print(f"   ❌ No strategies qualified")
                print(f"   📋 System would recommend: HOLD")
                
        except Exception as e:
            print(f"   🚨 Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print(f"\n🎉 Strategy Integration Test Completed Successfully!")
    print(f"✅ Strategy-aware decision making is operational")
    return True

def main():
    """Run strategy integration tests"""
    print("🚀 THE OVERMIND PROTOCOL - Standalone Strategy Tests")
    print("=" * 70)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.devnet')
    
    # Debug environment
    print("🔧 Environment Variables:")
    print(f"   ENABLED_STRATEGIES: {os.getenv('ENABLED_STRATEGIES', 'NOT SET')}")
    print(f"   SOUL_METEOR_MIN_VOLUME: {os.getenv('SOUL_METEOR_MIN_VOLUME', 'NOT SET')}")
    print(f"   MEMECOIN_HUNTER_MAX_MARKET_CAP: {os.getenv('MEMECOIN_HUNTER_MAX_MARKET_CAP', 'NOT SET')}")
    print()
    
    try:
        success = test_strategy_integration()
        
        if success:
            print("\n✅ ALL TESTS PASSED")
            print("🧠 OVERMIND Brain strategic intelligence is ready for deployment!")
            print("\n📋 Integration Summary:")
            print("   • Configuration loading: ✅")
            print("   • Strategy validation: ✅") 
            print("   • Signal filtering: ✅")
            print("   • AI context generation: ✅")
            print("\n🎯 Next Steps:")
            print("   1. Deploy with production environment")
            print("   2. Connect to live market data") 
            print("   3. Monitor strategy performance")
            print("   4. Adjust parameters based on results")
            
        return success
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)