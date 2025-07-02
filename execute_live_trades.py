#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Live Trading Execution
Execute 5 real money transactions with MEV protection
"""

import redis
import json
import time
import requests

def main():
    r = redis.Redis(host='localhost', port=6380, decode_responses=True)
    
    print("🔥 THE OVERMIND PROTOCOL - LIVE TRADING ACTIVATION")
    print("=" * 60)
    print("⚠️  WARNING: EXECUTING REAL MONEY TRANSACTIONS")
    print("💰 Wallet: HCzptyDxBeUDphr2Tty7GCrpvREwv1JFK6X5yLWXSmTZ")
    print("🛡️  MEV Protection: ENABLED")
    print()
    
    # 5 AGGRESSIVE LIVE TRADING SIGNALS
    live_signals = [
        {
            'action': 'BUY',
            'symbol': 'SOL',
            'quantity': 0.05,  # Small amounts for safety
            'confidence': 0.95,
            'strategy': 'LIVE_AGGRESSIVE_MOMENTUM',
            'mev_protection': True,
            'anti_sandwich': True,
            'jito_bundle': True,
            'live_trading': True,
            'paper_trading': False,  # EXPLICIT: Force live trading
            'max_slippage': 0.01,
            'priority_fee': 0.001
        },
        {
            'action': 'BUY',
            'symbol': 'BONK',
            'quantity': 0.03,
            'confidence': 0.88,
            'strategy': 'LIVE_MEMECOIN_SCALP',
            'mev_protection': True,
            'live_trading': True,
            'paper_trading': False,  # EXPLICIT: Force live trading
            'max_slippage': 0.02,
            'priority_fee': 0.001
        },
        {
            'action': 'BUY',
            'symbol': 'RAY',
            'quantity': 0.04,
            'confidence': 0.92,
            'strategy': 'LIVE_DEX_ARBITRAGE',
            'mev_protection': True,
            'jito_bundle': True,
            'live_trading': True,
            'paper_trading': False,  # EXPLICIT: Force live trading
            'max_slippage': 0.015,
            'priority_fee': 0.0015
        },
        {
            'action': 'BUY',
            'symbol': 'ORCA',
            'quantity': 0.035,
            'confidence': 0.85,
            'strategy': 'LIVE_LIQUIDITY_SNIPE',
            'mev_protection': True,
            'live_trading': True,
            'paper_trading': False,  # EXPLICIT: Force live trading
            'max_slippage': 0.02,
            'priority_fee': 0.001
        },
        {
            'action': 'BUY',
            'symbol': 'JUP',
            'quantity': 0.025,
            'confidence': 0.90,
            'strategy': 'LIVE_ECOSYSTEM_PLAY',
            'mev_protection': True,
            'jito_bundle': True,
            'live_trading': True,
            'paper_trading': False,  # EXPLICIT: Force live trading
            'max_slippage': 0.015,
            'priority_fee': 0.002
        }
    ]
    
    print("🚀 EXECUTING 5 LIVE TRADING SIGNALS...")
    print()
    
    for i, signal in enumerate(live_signals, 1):
        print(f"📤 Signal {i}/5: {signal['action']} {signal['symbol']}")
        print(f"   Quantity: {signal['quantity']} SOL")
        print(f"   Confidence: {signal['confidence']:.2f}")
        print(f"   Strategy: {signal['strategy']}")
        print(f"   MEV Protection: {signal['mev_protection']}")
        
        # Add timestamp and unique ID
        signal['timestamp'] = time.time()
        signal['signal_id'] = f"live_{int(time.time())}_{i}"
        signal['execution_mode'] = 'LIVE_TRADING'
        
        # Send to trading queue (CORRECTED NAME)
        r.lpush('overmind:commands', json.dumps(signal))
        
        print(f"   ✅ Signal sent to executor")
        print()
        
        # Wait 3 seconds between signals
        time.sleep(3)
    
    print("✅ ALL 5 LIVE TRADING SIGNALS SENT!")
    print()
    print("🔍 MONITORING EXECUTION...")
    
    # Monitor execution for 2 minutes
    start_time = time.time()
    executed_count = 0
    
    while time.time() - start_time < 120:  # 2 minutes
        # Check for new execution results
        results = r.lrange('overmind:execution_results', 0, 4)
        
        current_executed = 0
        for result_str in results:
            result = json.loads(result_str)
            if result.get('live_trading') and result.get('timestamp', 0) > start_time:
                current_executed += 1
        
        if current_executed > executed_count:
            executed_count = current_executed
            print(f"🎯 EXECUTED: {executed_count}/5 live transactions")
        
        time.sleep(5)
    
    print()
    print("📊 FINAL EXECUTION SUMMARY:")
    
    # Get final results
    results = r.lrange('overmind:execution_results', 0, 9)
    live_results = []
    
    for result_str in results:
        result = json.loads(result_str)
        if result.get('live_trading') and result.get('timestamp', 0) > start_time:
            live_results.append(result)
    
    if live_results:
        total_spent = 0
        total_profit = 0
        
        for i, result in enumerate(live_results, 1):
            symbol = result.get('symbol', 'UNKNOWN')
            quantity = result.get('quantity', 0)
            status = result.get('status', 'UNKNOWN')
            tx_id = result.get('transaction_id', 'N/A')
            
            print(f"{i}. {symbol}: {quantity} SOL - {status}")
            print(f"   TX: {tx_id}")
            
            if 'estimated_profit' in result:
                profit = result['estimated_profit']
                total_profit += profit
                print(f"   Profit: ${profit:.6f}")
            
            if 'execution_price' in result:
                spent = quantity * result['execution_price']
                total_spent += spent
        
        print()
        print(f"💰 TOTAL SPENT: {total_spent:.6f} SOL")
        print(f"📈 TOTAL PROFIT: ${total_profit:.6f}")
        print(f"✅ SUCCESSFUL EXECUTIONS: {len(live_results)}/5")
        
    else:
        print("⚠️  No live executions detected yet")
        print("🔄 Check logs for execution status")
    
    print()
    print("🎯 LIVE TRADING EXECUTION COMPLETE!")

if __name__ == "__main__":
    main()
