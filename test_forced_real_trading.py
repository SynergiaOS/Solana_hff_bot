#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - FORCED REAL TRADING TEST
Test the fixed routing logic with force_real_mode flag
"""

import redis
import json
import time

def main():
    r = redis.Redis(host='localhost', port=6380, decode_responses=True)
    
    print("🔥 THE OVERMIND PROTOCOL - FORCED REAL TRADING TEST")
    print("=" * 60)
    print("🚀 Testing fixed routing logic with force_real_mode")
    print()
    
    # FORCED REAL TRADING SIGNAL WITH ALL FLAGS
    forced_real_signal = {
        'action': 'BUY',
        'symbol': 'SOL',
        'quantity': 0.001,  # Very small: 0.001 SOL
        'confidence': 0.95,
        'strategy': 'FORCED_REAL_TEST',
        'live_trading': True,
        'paper_trading': False,
        'force_real_mode': True,  # EXPLICIT FORCE FLAG
        'timestamp': time.time(),
        'signal_id': f'forced_real_{int(time.time())}'
    }
    
    print("📤 SENDING FORCED REAL TRADING SIGNAL:")
    print(f"   Action: {forced_real_signal['action']}")
    print(f"   Symbol: {forced_real_signal['symbol']}")
    print(f"   Quantity: {forced_real_signal['quantity']} SOL")
    print(f"   live_trading: {forced_real_signal['live_trading']}")
    print(f"   paper_trading: {forced_real_signal['paper_trading']}")
    print(f"   force_real_mode: {forced_real_signal['force_real_mode']}")
    print()
    
    # Send signal
    r.lpush('overmind:commands', json.dumps(forced_real_signal))
    print("✅ FORCED REAL SIGNAL SENT TO EXECUTOR!")
    print()
    
    print("🔍 MONITORING EXECUTION (30 seconds)...")
    start_time = time.time()
    
    # Monitor for 30 seconds
    while time.time() - start_time < 30:
        # Check queue status
        queue_length = r.llen('overmind:commands')
        results_count = r.llen('overmind:execution_results')
        
        print(f"⏱️  {int(time.time() - start_time)}s: Queue={queue_length}, Results={results_count}")
        
        # Check for new results
        results = r.lrange('overmind:execution_results', 0, 1)
        for result_str in results:
            result = json.loads(result_str)
            if result.get('timestamp', 0) > start_time:
                print("\n🎯 NEW EXECUTION RESULT DETECTED:")
                print(f"   TX ID: {result.get('transaction_id', 'N/A')}")
                print(f"   Status: {result.get('status', 'N/A')}")
                print(f"   Mode: {result.get('mode', 'N/A')}")
                
                # Check if real Solana transaction
                tx_id = result.get('transaction_id', '')
                if len(tx_id) >= 80:
                    print("🎉 REAL SOLANA TRANSACTION CONFIRMED!")
                    print(f"🔗 Solscan: https://solscan.io/tx/{tx_id}")
                    return
                else:
                    print(f"⚠️  Still simulation: {tx_id}")
        
        time.sleep(3)
    
    print("\n⏰ Monitoring complete")
    print(f"Final queue length: {r.llen('overmind:commands')}")

if __name__ == "__main__":
    main()
