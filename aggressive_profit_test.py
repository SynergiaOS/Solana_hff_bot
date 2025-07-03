#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Aggressive Profit Trading Test
Execute larger trades for maximum profit generation
"""

import redis
import json
import time
import sys

def aggressive_profit_trading():
    """Execute aggressive profit trading with larger positions"""
    
    print("🚀 THE OVERMIND PROTOCOL - AGGRESSIVE PROFIT MODE")
    print("="*60)
    print("💰 TARGETING MAXIMUM PROFIT GENERATION")
    print("⚠️  WARNING: EXECUTING REAL SOLANA TRANSACTIONS")
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
    
    # AGGRESSIVE TRADING SEQUENCE
    trades = [
        {
            "action": "BUY",
            "symbol": "BONK",
            "quantity": 0.002,  # 0.002 SOL (~$0.31)
            "strategy": "aggressive_memecoin",
            "confidence": 0.85,
            "live_trading": True,
            "paper_trading": False,
            "force_real_mode": True,
            "ai_brain_id": "profit_hunter",
            "market_regime": "bullish"
        },
        {
            "action": "BUY", 
            "symbol": "RAY",
            "quantity": 0.003,  # 0.003 SOL (~$0.47)
            "strategy": "defi_momentum",
            "confidence": 0.90,
            "live_trading": True,
            "paper_trading": False,
            "force_real_mode": True,
            "ai_brain_id": "profit_hunter",
            "market_regime": "bullish"
        },
        {
            "action": "BUY",
            "symbol": "ORCA", 
            "quantity": 0.005,  # 0.005 SOL (~$0.78)
            "strategy": "dex_alpha",
            "confidence": 0.88,
            "live_trading": True,
            "paper_trading": False,
            "force_real_mode": True,
            "ai_brain_id": "profit_hunter", 
            "market_regime": "bullish"
        }
    ]
    
    total_invested = 0
    total_profit = 0
    successful_trades = 0
    
    print(f"🎯 EXECUTING {len(trades)} AGGRESSIVE TRADES:")
    print()
    
    for i, trade in enumerate(trades, 1):
        print(f"📤 TRADE {i}/{len(trades)}: {trade['action']} {trade['symbol']}")
        print(f"   💰 Amount: {trade['quantity']} SOL (~${trade['quantity'] * 155:.2f})")
        print(f"   🎯 Strategy: {trade['strategy']}")
        print(f"   🔥 Confidence: {trade['confidence']}")
        
        # Add timestamp
        trade['timestamp'] = time.time()
        
        # Send trade
        redis_client.lpush('overmind:commands', json.dumps(trade))
        print(f"   ✅ Trade {i} sent to executor")
        
        # Wait for result
        print(f"   ⏳ Waiting for execution result...")
        
        result_received = False
        for wait_time in range(45):  # Wait up to 45 seconds
            result = redis_client.brpop('overmind:execution_results', timeout=1)
            
            if result:
                try:
                    result_data = json.loads(result[1])
                    
                    # Skip mock results
                    if result_data.get('status') == 'mock_test':
                        continue
                        
                    print(f"   🎯 TRADE {i} RESULT:")
                    print(f"      Status: {result_data.get('status')}")
                    print(f"      Mode: {result_data.get('mode')}")
                    print(f"      Price: ${result_data.get('actual_price', 0):.4f}")
                    print(f"      Profit: ${result_data.get('profit', 0):.6f}")
                    
                    if result_data.get('tx_id'):
                        print(f"      TX: {result_data.get('tx_id')}")
                        print(f"      🔗 Solscan: https://solscan.io/tx/{result_data.get('tx_id')}")
                    
                    if result_data.get('status') == 'SUCCESS' and result_data.get('mode') == 'LIVE':
                        successful_trades += 1
                        total_invested += trade['quantity'] * 155  # Approximate USD
                        total_profit += result_data.get('profit', 0)
                        print(f"   ✅ TRADE {i} SUCCESS - REAL PROFIT GENERATED!")
                    else:
                        print(f"   ❌ TRADE {i} FAILED OR PAPER MODE")
                    
                    result_received = True
                    break
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse result: {e}")
                    break
            else:
                print(f"   ⏳ Waiting... ({wait_time+1}/45)")
        
        if not result_received:
            print(f"   ❌ TRADE {i} TIMEOUT - No response")
        
        print()
        
        # Brief pause between trades
        if i < len(trades):
            print("   ⏸️  Pausing 3 seconds before next trade...")
            time.sleep(3)
    
    # FINAL RESULTS
    print("🎯 AGGRESSIVE TRADING SESSION COMPLETE")
    print("="*50)
    print(f"📊 Total Trades Executed: {successful_trades}/{len(trades)}")
    print(f"💰 Total Invested: ~${total_invested:.2f}")
    print(f"💵 Total Profit Generated: ${total_profit:.6f}")
    
    if successful_trades > 0:
        roi = (total_profit / (total_invested / 155)) * 100  # Convert back to SOL for ROI
        print(f"📈 ROI: {roi:.4f}%")
        print()
        print("🎉 AGGRESSIVE PROFIT GENERATION SUCCESSFUL!")
        print("💎 THE OVERMIND PROTOCOL GENERATING REAL PROFITS!")
        return True
    else:
        print()
        print("❌ NO SUCCESSFUL TRADES EXECUTED")
        print("🔧 Check system configuration and try again")
        return False

if __name__ == "__main__":
    print("🔥 AGGRESSIVE PROFIT MODE ACTIVATED")
    print("💰 Targeting maximum profit generation...")
    print()
    
    success = aggressive_profit_trading()
    
    if success:
        print()
        print("🚀 MISSION ACCOMPLISHED!")
        print("💰 THE OVERMIND PROTOCOL PROFIT GENERATION ACTIVE")
        print("📈 Ready for continuous autonomous trading")
    else:
        print()
        print("❌ MISSION FAILED")
        print("🔧 System requires debugging")
    
    sys.exit(0 if success else 1)
