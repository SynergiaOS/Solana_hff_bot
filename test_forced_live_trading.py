#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Forced Live Trading Test
Test real transaction execution with debug logging
"""

import redis
import json
import time
import sys

def test_forced_live_trading():
    """Test forced live trading with debug output"""
    
    print("🚀 THE OVERMIND PROTOCOL - FORCED LIVE TRADING TEST")
    print("="*60)
    print("⚠️  WARNING: TESTING REAL SOLANA TRANSACTIONS")
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
    
    # Test command with force_real_mode
    test_command = {
        "action": "BUY",
        "symbol": "SOL", 
        "quantity": 0.0005,  # Very small amount: 0.0005 SOL (~$0.075)
        "strategy": "forced_live_test",
        "confidence": 0.95,
        "timestamp": time.time(),
        "live_trading": True,
        "paper_trading": False,
        "force_real_mode": True,  # FORCE real transaction
        "ai_brain_id": "debug_test",
        "market_regime": "test"
    }
    
    print("📤 Sending forced live trading command:")
    print(f"   Action: {test_command['action']}")
    print(f"   Symbol: {test_command['symbol']}")
    print(f"   Quantity: {test_command['quantity']} SOL")
    print(f"   Force Real Mode: {test_command['force_real_mode']}")
    print()
    
    # Send command
    redis_client.lpush('overmind:commands', json.dumps(test_command))
    print("✅ Command sent to overmind:commands")
    
    # Wait for response
    print("⏳ Waiting for execution result...")
    
    for i in range(30):  # Wait up to 30 seconds
        # Check for results
        result = redis_client.brpop('overmind:execution_results', timeout=1)
        
        if result:
            try:
                result_data = json.loads(result[1])
                print()
                print("🎯 EXECUTION RESULT RECEIVED:")
                print("="*40)
                
                for key, value in result_data.items():
                    print(f"   {key}: {value}")
                
                print()
                
                # Check if it was a real transaction
                if not result_data.get('paper_trading', True):
                    print("🎉 SUCCESS: REAL SOLANA TRANSACTION EXECUTED!")
                    if 'transaction_id' in result_data:
                        print(f"🔗 Transaction ID: {result_data['transaction_id']}")
                        print("🔍 Check on Solscan for details")
                    return True
                else:
                    print("📝 Note: Still executed as paper trade")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse result: {e}")
                print(f"Raw result: {result[1]}")
                return False
        else:
            print(f"⏳ Waiting... ({i+1}/30)")
    
    print()
    print("❌ TIMEOUT: No response received from executor")
    
    # Check if command is still in queue
    queue_len = redis_client.llen('overmind:commands')
    results_len = redis_client.llen('overmind:execution_results')
    
    print(f"📊 Commands in queue: {queue_len}")
    print(f"📊 Results available: {results_len}")
    
    if results_len > 0:
        print("📋 Available results:")
        results = redis_client.lrange('overmind:execution_results', 0, -1)
        for i, result in enumerate(results):
            print(f"   Result {i+1}: {result}")
    
    return False

def check_wallet_balance():
    """Check wallet balance before testing"""
    print("💰 Checking wallet balance...")
    
    # This would normally check Solana balance
    # For now, just indicate we should check manually
    print("📋 Please verify wallet has sufficient SOL for testing")
    print("   Minimum required: 0.001 SOL (for fees + test amount)")
    print()

if __name__ == "__main__":
    print("🔍 Pre-flight checks...")
    check_wallet_balance()
    
    print("🚀 Starting forced live trading test...")
    success = test_forced_live_trading()
    
    if success:
        print()
        print("🎉 LIVE TRADING TEST SUCCESSFUL!")
        print("✅ System is ready for autonomous live trading")
    else:
        print()
        print("❌ LIVE TRADING TEST FAILED")
        print("🔧 Check executor logs for debugging")
        print("📋 Verify wallet balance and configuration")
    
    sys.exit(0 if success else 1)
