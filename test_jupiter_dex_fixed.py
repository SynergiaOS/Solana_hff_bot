#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Jupiter DEX Fixed Integration Test
Test the fixed Jupiter DEX integration with enhanced monitoring
"""

import redis
import json
import time
import sys
import requests

def check_transaction_type(tx_id):
    """Check if transaction is a real DEX swap by analyzing instructions"""
    try:
        # Use Helius API to get detailed transaction info
        url = f"https://mainnet.helius-rpc.com/?api-key=edbcd361-78a0-4998-bd1e-8d4666722f82"
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransaction",
            "params": [
                tx_id,
                {
                    "encoding": "jsonParsed",
                    "maxSupportedTransactionVersion": 0
                }
            ]
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        if 'result' in data and data['result']:
            instructions = data['result']['transaction']['message']['instructions']
            program_ids = [instr.get('programId', '') for instr in instructions]
            
            # Check for Jupiter/DEX program IDs
            jupiter_programs = [
                'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4',  # Jupiter V6
                'JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB',  # Jupiter V4
                'whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc',  # Whirlpool
                '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',  # Raydium
                'DjVE6JNiYqPL2QXyCUUh8rNjHrbz9hXHNYt99MQ59qw1',  # Orca
            ]
            
            dex_interaction = any(prog in jupiter_programs for prog in program_ids)
            system_only = all(prog == '11111111111111111111111111111111' for prog in program_ids)
            
            return {
                'is_dex_swap': dex_interaction,
                'is_system_only': system_only,
                'program_count': len(set(program_ids)),
                'programs': list(set(program_ids))
            }
    except Exception as e:
        print(f"   ⚠️ Error analyzing transaction: {e}")
    
    return {'is_dex_swap': False, 'is_system_only': True, 'program_count': 1, 'programs': ['unknown']}

def test_jupiter_dex_fixed():
    """Test the fixed Jupiter DEX integration"""
    
    print("🚀 THE OVERMIND PROTOCOL - JUPITER DEX FIXED TEST")
    print("="*60)
    print("🔧 TESTING FIXED JUPITER DEX INTEGRATION")
    print("💰 REAL TOKEN SWAPS WITH ENHANCED MONITORING")
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
    
    # FIXED JUPITER DEX TESTS - Smaller amounts for testing
    dex_tests = [
        {
            "action": "BUY",
            "symbol": "BONK",  # Test 1: SOL -> BONK
            "quantity": 0.0005,  # Very small amount for testing
            "strategy": "jupiter_dex_fixed_test",
            "confidence": 0.95,
            "live_trading": True,
            "paper_trading": False,
            "force_real_mode": True,
            "ai_brain_id": "jupiter_fixed_tester",
            "market_regime": "dex_testing_fixed"
        },
        {
            "action": "BUY", 
            "symbol": "RAY",   # Test 2: SOL -> RAY
            "quantity": 0.001,  # Small amount
            "strategy": "jupiter_dex_fixed_test",
            "confidence": 0.92,
            "live_trading": True,
            "paper_trading": False,
            "force_real_mode": True,
            "ai_brain_id": "jupiter_fixed_tester",
            "market_regime": "dex_testing_fixed"
        }
    ]
    
    total_invested = 0
    successful_swaps = 0
    real_dex_swaps = 0
    system_transfers = 0
    
    print(f"🎯 EXECUTING {len(dex_tests)} FIXED JUPITER DEX TESTS:")
    print(f"💰 Total Investment: ~${sum(trade['quantity'] * 155 for trade in dex_tests):.4f}")
    print(f"🔧 Testing fixed transaction signing")
    print()
    
    for i, trade in enumerate(dex_tests, 1):
        symbol = trade['symbol']
        quantity = trade['quantity']
        
        print(f"🔧 FIXED DEX TEST {i}/{len(dex_tests)}: {trade['action']} {symbol}")
        print(f"   💰 Amount: {quantity} SOL (~${quantity * 155:.4f})")
        print(f"   🎯 Expected: Fixed Jupiter DEX swap SOL -> {symbol}")
        
        # Add timestamp
        trade['timestamp'] = time.time()
        
        # Send trade
        redis_client.lpush('overmind:commands', json.dumps(trade))
        print(f"   ✅ Fixed DEX trade {i} sent to executor")
        
        # Wait for result with enhanced monitoring
        print(f"   ⏳ Waiting for fixed Jupiter DEX result...")
        
        result_received = False
        for wait_time in range(90):  # Extended wait time for DEX operations
            result = redis_client.brpop('overmind:execution_results', timeout=1)
            
            if result:
                try:
                    result_data = json.loads(result[1])
                    
                    # Skip mock results
                    if result_data.get('status') == 'mock_test':
                        continue
                        
                    print(f"   🎯 FIXED DEX TEST {i} RESULT:")
                    print(f"      Status: {result_data.get('status')}")
                    print(f"      Mode: {result_data.get('mode')}")
                    print(f"      Symbol: {result_data.get('symbol')}")
                    print(f"      Action: {result_data.get('action')}")
                    
                    if result_data.get('tx_id'):
                        tx_id = result_data.get('tx_id')
                        print(f"      TX: {tx_id}")
                        print(f"      🔗 Solscan: https://solscan.io/tx/{tx_id}")
                        
                        # Enhanced transaction analysis
                        print(f"   🔍 ANALYZING TRANSACTION TYPE...")
                        tx_analysis = check_transaction_type(tx_id)
                        
                        print(f"      📊 Programs involved: {tx_analysis['program_count']}")
                        print(f"      🔧 Program IDs: {tx_analysis['programs']}")
                        
                        if tx_analysis['is_dex_swap']:
                            print(f"   🎉 REAL DEX SWAP DETECTED!")
                            print(f"   🚀 Jupiter/DEX programs found in transaction")
                            real_dex_swaps += 1
                        elif tx_analysis['is_system_only']:
                            print(f"   📝 System transfer only (fallback)")
                            print(f"   ⚠️ Jupiter DEX swap failed, used fallback")
                            system_transfers += 1
                        else:
                            print(f"   🤔 Mixed transaction type")
                        
                        successful_swaps += 1
                        total_invested += quantity * 155
                        print(f"   ✅ FIXED DEX TEST {i} SUCCESS")
                    else:
                        print(f"   ❌ FIXED DEX TEST {i} FAILED - No transaction ID")
                    
                    result_received = True
                    break
                    
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse result: {e}")
                    break
            else:
                if wait_time % 10 == 0:  # Progress update every 10 seconds
                    print(f"   ⏳ Still waiting... ({wait_time+1}/90)")
        
        if not result_received:
            print(f"   ❌ FIXED DEX TEST {i} TIMEOUT - No response")
        
        print()
        
        # Brief pause between tests
        if i < len(dex_tests):
            print("   ⏸️  Pausing 10 seconds before next test...")
            time.sleep(10)
    
    # FINAL RESULTS
    print("🎯 FIXED JUPITER DEX TEST COMPLETE")
    print("="*50)
    print(f"📊 Total Tests: {len(dex_tests)}")
    print(f"✅ Successful Transactions: {successful_swaps}")
    print(f"🚀 Real DEX Swaps: {real_dex_swaps}")
    print(f"📝 System Transfers (Fallback): {system_transfers}")
    print(f"💰 Total Invested: ~${total_invested:.4f}")
    
    if real_dex_swaps > 0:
        print(f"🎉 JUPITER DEX INTEGRATION FIXED AND WORKING!")
        print(f"🔄 Real token swaps successfully executed")
        print(f"📈 Success rate: {(real_dex_swaps/len(dex_tests))*100:.1f}%")
        return True
    elif successful_swaps > 0:
        print(f"📊 TRANSACTIONS SUCCESSFUL BUT STILL USING FALLBACK")
        print(f"🔧 Jupiter DEX integration needs further debugging")
        print(f"⚠️ All transactions fell back to system transfers")
        return False
    else:
        print("❌ NO SUCCESSFUL TRANSACTIONS")
        print("🔧 System requires immediate debugging")
        return False

if __name__ == "__main__":
    print("🔧 FIXED JUPITER DEX INTEGRATION TEST")
    print("🎯 Testing fixed transaction signing...")
    print("⚡ Enhanced monitoring and analysis")
    print()
    
    success = test_jupiter_dex_fixed()
    
    if success:
        print()
        print("🚀 JUPITER DEX INTEGRATION FIXED!")
        print("💰 THE OVERMIND PROTOCOL REAL DEX TRADING ACTIVE")
        print("🔄 Ready for $20 profit generation through real swaps")
    else:
        print()
        print("❌ JUPITER DEX STILL NEEDS WORK")
        print("🔧 Continue debugging transaction signing")
    
    sys.exit(0 if success else 1)
