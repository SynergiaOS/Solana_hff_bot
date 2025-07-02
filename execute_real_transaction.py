#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - REAL MONEY TRANSACTION EXECUTION
Execute ONE real Solana transaction with actual wallet
"""

import redis
import json
import time

def main():
    r = redis.Redis(host='localhost', port=6380, decode_responses=True)
    
    print("🔥 THE OVERMIND PROTOCOL - REAL MONEY TRANSACTION")
    print("=" * 60)
    print("⚠️  WARNING: EXECUTING REAL SOLANA TRANSACTION")
    print("💰 Wallet: HCzptyDxBeUDphr2Tty7GCrpvREwv1JFK6X5yLWXSmTZ")
    print("🛡️  Real Solana Network: MAINNET")
    print()
    
    # ONE REAL TRANSACTION - VERY SMALL AMOUNT
    real_transaction = {
        'action': 'BUY',
        'symbol': 'SOL',
        'quantity': 0.001,  # VERY SMALL: 0.001 SOL (~$0.15)
        'confidence': 0.99,
        'strategy': 'REAL_MONEY_TEST',
        'live_trading': True,
        'paper_trading': False,  # EXPLICIT: Real transaction
        'timestamp': time.time(),
        'signal_id': f'real_money_test_{int(time.time())}',
        'execution_mode': 'REAL_SOLANA_TRANSACTION'
    }
    
    print(f"📤 SENDING REAL TRANSACTION:")
    print(f"   Action: {real_transaction['action']}")
    print(f"   Symbol: {real_transaction['symbol']}")
    print(f"   Amount: {real_transaction['quantity']} SOL (~${real_transaction['quantity'] * 150:.2f})")
    print(f"   Mode: REAL MONEY")
    print()
    
    # Send to executor
    r.lpush('overmind:commands', json.dumps(real_transaction))
    print("✅ REAL TRANSACTION SIGNAL SENT TO EXECUTOR")
    print()
    
    print("🔍 MONITORING EXECUTION...")
    start_time = time.time()
    
    # Monitor for 60 seconds
    while time.time() - start_time < 60:
        # Check execution results
        results = r.lrange('overmind:execution_results', 0, 2)
        
        for result_str in results:
            result = json.loads(result_str)
            if result.get('timestamp', 0) > start_time:
                print("🎯 EXECUTION DETECTED:")
                print(f"   Symbol: {result.get('symbol', 'N/A')}")
                print(f"   Status: {result.get('status', 'N/A')}")
                print(f"   TX ID: {result.get('transaction_id', 'N/A')}")
                print(f"   Mode: {result.get('mode', 'N/A')}")
                
                # Check if it's a real Solana transaction hash
                tx_id = result.get('transaction_id', '')
                if len(tx_id) == 88:  # Solana transaction hash length
                    print(f"✅ REAL SOLANA TRANSACTION CONFIRMED!")
                    print(f"🔗 View on Solscan: https://solscan.io/tx/{tx_id}")
                    return
                else:
                    print(f"⚠️  Still simulation: {tx_id}")
        
        time.sleep(5)
    
    print("⏰ Monitoring timeout - check logs manually")

if __name__ == "__main__":
    main()
