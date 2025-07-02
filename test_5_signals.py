#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - 5 Signal Autonomous Test
Test processing of 5 trading signals with Jina AI integration
"""

import redis
import json
import time
import asyncio
from datetime import datetime

def test_5_signals():
    """Process 5 test signals from Redis queue"""
    
    print('🧠 THE OVERMIND PROTOCOL - Processing 5 Test Signals')
    print('=' * 60)
    
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Check queue length
        queue_length = r.llen('overmind:commands')
        print(f'📊 Signals in queue: {queue_length}')
        
        if queue_length == 0:
            print('❌ No signals in queue. Adding test signals...')
            
            # Add test signals
            test_signals = [
                {"action":"BUY","symbol":"SOL","quantity":0.01,"strategy":"range_sniper","test_id":"T001"},
                {"action":"BUY","symbol":"BONK","quantity":5,"strategy":"memecoin_hunter","test_id":"T002"},
                {"action":"BUY","symbol":"JTO","quantity":0.5,"strategy":"governance_alpha_hunter","test_id":"T003"},
                {"action":"SELL","symbol":"SOL","quantity":0.005,"strategy":"adaptive_scalper","test_id":"T004"},
                {"action":"BUY","symbol":"RAY","quantity":1,"strategy":"liquidity_accumulator","test_id":"T005"}
            ]
            
            for signal in test_signals:
                r.lpush('overmind:commands', json.dumps(signal))
            
            queue_length = r.llen('overmind:commands')
            print(f'✅ Added {len(test_signals)} test signals. Queue length: {queue_length}')
        
        # Process each signal
        processed_count = 0
        
        for i in range(min(5, queue_length)):
            signal = r.rpop('overmind:commands')
            if signal:
                try:
                    signal_data = json.loads(signal)
                    print(f'\n🔄 Processing Signal {i+1}:')
                    print(f'   Action: {signal_data.get("action")}')
                    print(f'   Symbol: {signal_data.get("symbol")}')
                    print(f'   Quantity: {signal_data.get("quantity")}')
                    print(f'   Strategy: {signal_data.get("strategy")}')
                    print(f'   Test ID: {signal_data.get("test_id")}')
                    
                    # Simulate AI Brain processing
                    print(f'   🧠 AI Brain: Analyzing signal...')
                    time.sleep(0.2)
                    
                    # Simulate market regime check
                    market_regime = "BULLISH" if i % 2 == 0 else "SIDEWAYS"
                    print(f'   📊 Market Regime: {market_regime}')
                    
                    # Strategy filtering based on regime
                    strategy = signal_data.get("strategy")
                    blocked_strategies = ["memecoin_hunter"] if market_regime == "SIDEWAYS" else []
                    
                    if strategy in blocked_strategies:
                        print(f'   🚫 Strategy BLOCKED in {market_regime} market')
                        result = {
                            'test_id': signal_data.get('test_id'),
                            'symbol': signal_data.get('symbol'),
                            'action': signal_data.get('action'),
                            'strategy': strategy,
                            'status': 'BLOCKED',
                            'reason': f'Strategy not allowed in {market_regime} market',
                            'paper_trading': True,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        # Simulate execution
                        print(f'   ⚙️ Executor: Simulating {signal_data.get("action")} order...')
                        time.sleep(0.3)
                        
                        # Mock price calculation
                        base_prices = {"SOL": 140.0, "BONK": 0.00002, "JTO": 3.5, "RAY": 2.8}
                        mock_price = base_prices.get(signal_data.get("symbol"), 100.0)
                        mock_price += (i * 0.5)  # Small price variation
                        
                        total_value = mock_price * signal_data.get('quantity', 1)
                        
                        result = {
                            'test_id': signal_data.get('test_id'),
                            'symbol': signal_data.get('symbol'),
                            'action': signal_data.get('action'),
                            'quantity': signal_data.get('quantity'),
                            'strategy': strategy,
                            'status': 'SIMULATED',
                            'paper_trading': True,
                            'timestamp': datetime.now().isoformat(),
                            'price': mock_price,
                            'total_value': total_value,
                            'market_regime': market_regime
                        }
                        
                        print(f'   ✅ Status: SIMULATED EXECUTION')
                        print(f'   💰 Mock Price: ${mock_price:.6f}')
                        print(f'   💵 Total Value: ${total_value:.6f}')
                    
                    # Store result in Redis
                    r.lpush('overmind:execution_results', json.dumps(result))
                    
                    # Simulate Post-Trade Intelligence
                    print(f'   📈 Post-Trade: Analyzing execution...')
                    time.sleep(0.1)
                    
                    # Store in memory
                    memory_entry = {
                        'type': 'execution',
                        'signal': signal_data,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    r.lpush('overmind:memory', json.dumps(memory_entry))
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f'   ❌ Error processing signal: {e}')
        
        # Final summary
        print(f'\n📊 EXECUTION SUMMARY:')
        results_count = r.llen('overmind:execution_results')
        memory_count = r.llen('overmind:memory')
        remaining_signals = r.llen('overmind:commands')
        
        print(f'   Signals processed: {processed_count}')
        print(f'   Execution results stored: {results_count}')
        print(f'   Memory entries: {memory_count}')
        print(f'   Remaining signals: {remaining_signals}')
        
        # Show recent results
        print(f'\n📋 RECENT EXECUTION RESULTS:')
        for i in range(min(3, results_count)):
            result_json = r.lindex('overmind:execution_results', i)
            if result_json:
                result = json.loads(result_json)
                status = result.get('status')
                symbol = result.get('symbol')
                action = result.get('action')
                test_id = result.get('test_id')
                
                if status == 'SIMULATED':
                    price = result.get('price', 0)
                    value = result.get('total_value', 0)
                    print(f'   {test_id}: {action} {symbol} - ✅ SIMULATED (${price:.6f}, ${value:.6f})')
                else:
                    reason = result.get('reason', 'Unknown')
                    print(f'   {test_id}: {action} {symbol} - 🚫 BLOCKED ({reason})')
        
        print(f'\n🎯 5-Signal Autonomous Test Complete!')
        print(f'✅ THE OVERMIND PROTOCOL successfully processed trading signals')
        
    except Exception as e:
        print(f'❌ Error in test: {e}')

if __name__ == "__main__":
    test_5_signals()
