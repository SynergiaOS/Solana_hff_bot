#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Final Jupiter DEX Test
Ultimate test of Jupiter DEX integration with enhanced error handling
"""

import redis
import json
import time
import sys

def test_jupiter_final():
    """Final test of Jupiter DEX integration"""
    
    print("🎯 THE OVERMIND PROTOCOL - FINAL JUPITER DEX TEST")
    print("="*60)
    print("🔧 ULTIMATE JUPITER DEX INTEGRATION TEST")
    print("💰 ENHANCED ERROR HANDLING & DEBUGGING")
    print("🚀 TARGET: REAL DEX SWAPS FOR $20+ PROFITS")
    print()
    
    # Connect to Redis
    try:
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    
    # Clear old results
    redis_client.delete('overmind:execution_results')
    print("🧹 Cleared old execution results")
    
    # FINAL JUPITER DEX TEST - Single test with maximum debugging
    final_test = {
        "action": "BUY",
        "symbol": "BONK",  # Single test: SOL -> BONK
        "quantity": 0.001,  # 0.001 SOL (~$0.155)
        "strategy": "jupiter_dex_final_test",
        "confidence": 0.95,
        "live_trading": True,
        "paper_trading": False,
        "force_real_mode": True,
        "ai_brain_id": "jupiter_final_tester",
        "market_regime": "dex_testing_final"
    }
    
    print(f"🎯 EXECUTING FINAL JUPITER DEX TEST:")
    print(f"💰 Investment: {final_test['quantity']} SOL (~${final_test['quantity'] * 155:.3f})")
    print(f"🔧 Enhanced error handling and debugging active")
    print(f"🚀 Target: Real Jupiter DEX swap SOL -> {final_test['symbol']}")
    print()
    
    symbol = final_test['symbol']
    quantity = final_test['quantity']
    
    print(f"🔧 FINAL DEX TEST: {final_test['action']} {symbol}")
    print(f"   💰 Amount: {quantity} SOL (~${quantity * 155:.3f})")
    print(f"   🎯 Expected: Real Jupiter DEX swap with enhanced debugging")
    
    # Add timestamp
    final_test['timestamp'] = time.time()
    
    # Send trade
    redis_client.lpush('overmind:commands', json.dumps(final_test))
    print(f"   ✅ Final DEX test sent to executor")
    
    # Wait for result with maximum patience
    print(f"   ⏳ Waiting for final Jupiter DEX result...")
    print(f"   📊 Enhanced debugging should show detailed transaction flow")
    
    result_received = False
    for wait_time in range(120):  # Extended wait time for debugging
        result = redis_client.brpop('overmind:execution_results', timeout=1)
        
        if result:
            try:
                result_data = json.loads(result[1])
                
                # Skip mock results
                if result_data.get('status') == 'mock_test':
                    continue
                    
                print(f"   🎯 FINAL DEX TEST RESULT:")
                print(f"      Status: {result_data.get('status')}")
                print(f"      Mode: {result_data.get('mode')}")
                print(f"      Symbol: {result_data.get('symbol')}")
                print(f"      Action: {result_data.get('action')}")
                print(f"      Profit: ${result_data.get('profit', 0):.6f}")
                
                if result_data.get('tx_id'):
                    tx_id = result_data.get('tx_id')
                    print(f"      TX: {tx_id}")
                    print(f"      🔗 Solscan: https://solscan.io/tx/{tx_id}")
                    
                    print(f"   ✅ FINAL DEX TEST SUCCESS")
                    print(f"   📊 Check executor logs for detailed Jupiter DEX flow")
                    result_received = True
                else:
                    print(f"   ❌ FINAL DEX TEST FAILED - No transaction ID")
                
                break
                
            except json.JSONDecodeError as e:
                print(f"   ❌ Failed to parse result: {e}")
                break
        else:
            if wait_time % 15 == 0:  # Progress update every 15 seconds
                print(f"   ⏳ Still waiting for Jupiter DEX result... ({wait_time+1}/120)")
                print(f"   📊 Check logs: tail -f logs/executor_jupiter_enhanced.log")
    
    if not result_received:
        print(f"   ❌ FINAL DEX TEST TIMEOUT - Check logs for details")
        print(f"   📊 Logs: tail -n 50 logs/executor_jupiter_enhanced.log")
    
    print()
    
    # FINAL ANALYSIS
    print("🎯 FINAL JUPITER DEX TEST COMPLETE")
    print("="*50)
    
    if result_received:
        print(f"✅ Transaction executed successfully")
        print(f"📊 Check logs for Jupiter DEX integration details")
        print(f"🔍 Analyze transaction on Solscan to verify DEX swap")
        print()
        print("🚀 NEXT STEPS:")
        print("1. Verify transaction type on Solscan")
        print("2. Check if Jupiter/DEX programs were involved")
        print("3. If successful, scale up for $20+ profit generation")
        return True
    else:
        print(f"❌ Test failed or timed out")
        print(f"🔧 Check executor logs for debugging information")
        print(f"📊 Jupiter DEX integration needs further work")
        return False

if __name__ == "__main__":
    print("🎯 FINAL JUPITER DEX INTEGRATION TEST")
    print("🔧 Enhanced error handling and debugging...")
    print("🚀 Target: Real DEX swaps for profit generation")
    print()
    
    success = test_jupiter_final()
    
    if success:
        print()
        print("🎉 FINAL JUPITER DEX TEST COMPLETED!")
        print("💰 THE OVERMIND PROTOCOL READY FOR SCALING")
        print("🚀 Ready to generate $20+ profits through real DEX trading")
        print()
        print("🎯 NEXT MISSION: Scale up trading for $20+ target")
    else:
        print()
        print("❌ FINAL JUPITER DEX TEST NEEDS MORE WORK")
        print("🔧 Continue debugging Jupiter integration")
        print("📊 Check logs for detailed error analysis")
    
    sys.exit(0 if success else 1)
