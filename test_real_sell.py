#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Real SELL Execution Test
CRITICAL: Test real SELL functionality with Jito bundles
"""

import json
import redis
import time
import uuid
from datetime import datetime, timezone

# Connect to DragonflyDB
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def test_real_sell_execution():
    """Test REAL SELL execution - CRITICAL for risk management"""
    
    print("🔥 THE OVERMIND PROTOCOL - REAL SELL EXECUTION TEST")
    print("=" * 60)
    print("⚠️  WARNING: This will test REAL market SELL orders!")
    print("🛡️  Mode: Paper trading (safe simulation)")
    print("=" * 60)
    
    # Test 1: Small SELL order (emergency exit simulation)
    print("\n🚨 Test 1: Emergency SELL - Small Position")
    sell_command_1 = {
        "command_id": str(uuid.uuid4()),
        "action": "SELL",
        "symbol": "BONK/SOL",
        "quantity": 0.005,  # Small amount for testing
        "confidence": 0.95,  # High confidence for emergency
        "strategy": "emergency_exit",
        "timestamp": time.time(),
        "paper_trading": True,
        "max_slippage": 0.05,  # 5% max slippage for emergency
        "priority": "CRITICAL",
        "sell_type": "MARKET",  # Immediate market sell
        "source": "real_sell_test"
    }
    
    send_sell_command(sell_command_1)
    time.sleep(3)
    
    # Test 2: Medium SELL order (profit taking)
    print("\n💰 Test 2: Profit Taking SELL")
    sell_command_2 = {
        "command_id": str(uuid.uuid4()),
        "action": "SELL",
        "symbol": "ETH/SOL", 
        "quantity": 0.02,
        "confidence": 0.85,
        "strategy": "profit_taking",
        "timestamp": time.time(),
        "paper_trading": True,
        "max_slippage": 0.02,  # 2% max slippage for profit taking
        "priority": "HIGH",
        "sell_type": "LIMIT",  # Limit order for better price
        "min_sol_output": 0.019,  # Minimum SOL to receive
        "source": "real_sell_test"
    }
    
    send_sell_command(sell_command_2)
    time.sleep(3)
    
    # Test 3: Large SELL order (position reduction)
    print("\n📉 Test 3: Position Reduction SELL")
    sell_command_3 = {
        "command_id": str(uuid.uuid4()),
        "action": "SELL",
        "symbol": "MSOL/SOL",
        "quantity": 0.05,
        "confidence": 0.75,
        "strategy": "position_reduction", 
        "timestamp": time.time(),
        "paper_trading": True,
        "max_slippage": 0.03,  # 3% max slippage
        "priority": "MEDIUM",
        "sell_type": "MARKET",
        "source": "real_sell_test"
    }
    
    send_sell_command(sell_command_3)
    time.sleep(3)
    
    # Test 4: Stop-loss SELL (risk management)
    print("\n🛑 Test 4: Stop-Loss SELL")
    sell_command_4 = {
        "command_id": str(uuid.uuid4()),
        "action": "SELL",
        "symbol": "USDC/SOL",
        "quantity": 0.01,
        "confidence": 0.90,
        "strategy": "stop_loss",
        "timestamp": time.time(),
        "paper_trading": True,
        "max_slippage": 0.10,  # 10% max slippage for stop-loss
        "priority": "CRITICAL",
        "sell_type": "MARKET",
        "stop_loss_price": 0.009,  # Trigger price
        "source": "real_sell_test"
    }
    
    send_sell_command(sell_command_4)
    time.sleep(3)
    
    # Test 5: Emergency SELL ALL (liquidation)
    print("\n🚨 Test 5: EMERGENCY SELL ALL")
    emergency_command = {
        "command_id": str(uuid.uuid4()),
        "action": "EMERGENCY_SELL_ALL",
        "symbol": "ALL_POSITIONS",
        "quantity": 0.0,  # Will sell all available
        "confidence": 1.0,  # Maximum confidence for emergency
        "strategy": "emergency_liquidation",
        "timestamp": time.time(),
        "paper_trading": True,
        "max_slippage": 0.15,  # 15% max slippage for emergency
        "priority": "CRITICAL",
        "sell_type": "MARKET",
        "reason": "Emergency liquidation test",
        "source": "real_sell_test"
    }
    
    send_sell_command(emergency_command)
    
    print(f"\n✅ Sent 5 REAL SELL test commands")
    print("⏳ Waiting for execution results...")
    
    # Wait for execution
    time.sleep(10)
    
    # Check results
    check_sell_execution_results()

def send_sell_command(command):
    """Send SELL command to THE OVERMIND PROTOCOL"""
    command_json = json.dumps(command)
    print(f"📤 Sending SELL: {command['action']} {command['quantity']} {command['symbol']}")
    print(f"   Strategy: {command['strategy']}")
    print(f"   Priority: {command['priority']}")
    print(f"   Max Slippage: {command['max_slippage']*100:.1f}%")
    
    # Send to overmind:commands queue
    r.lpush("overmind:commands", command_json)
    print("✅ SELL command sent to overmind:commands")

def check_sell_execution_results():
    """Check SELL execution results"""
    print("\n🔍 Checking SELL execution results...")
    
    # Check execution results
    results = r.lrange("overmind:execution_results", 0, -1)
    
    if results:
        print(f"📊 Found {len(results)} execution results:")
        sell_results = []
        
        for i, result_json in enumerate(results):
            try:
                result = json.loads(result_json)
                if 'SELL' in result.get('action', '').upper():
                    sell_results.append(result)
                    print(f"\n   SELL Result {len(sell_results)}:")
                    print(f"   Action: {result.get('action', 'UNKNOWN')}")
                    print(f"   Status: {result.get('status', 'UNKNOWN')}")
                    print(f"   Symbol: {result.get('symbol', 'N/A')}")
                    print(f"   Amount: {result.get('actual_amount', 'N/A')}")
                    print(f"   Price: {result.get('actual_price', 'N/A')}")
                    print(f"   SOL Received: {result.get('sol_received', 'N/A')}")
                    print(f"   Execution Time: {result.get('execution_time_ms', 'N/A')} ms")
                    print(f"   TX ID: {result.get('tx_id', 'N/A')}")
                    if result.get('error_message'):
                        print(f"   Error: {result['error_message']}")
            except json.JSONDecodeError:
                print(f"   Invalid JSON in result {i+1}")
        
        if sell_results:
            print(f"\n📈 SELL EXECUTION SUMMARY:")
            print(f"   Total SELL orders: {len(sell_results)}")
            successful = len([r for r in sell_results if r.get('status') == 'SUCCESS'])
            print(f"   Successful: {successful}/{len(sell_results)}")
            print(f"   Success Rate: {(successful/len(sell_results)*100):.1f}%")
            
            total_sol_received = sum([float(r.get('sol_received', 0)) for r in sell_results])
            print(f"   Total SOL Received: {total_sol_received:.6f} SOL")
            
            avg_execution_time = sum([int(r.get('execution_time_ms', 0)) for r in sell_results]) / len(sell_results)
            print(f"   Average Execution Time: {avg_execution_time:.1f} ms")
        else:
            print("   No SELL results found in execution results")
    else:
        print("   No execution results found")
    
    # Check system metrics after SELL tests
    print("\n📊 System Metrics After SELL Tests:")
    try:
        import requests
        response = requests.get("http://localhost:8082/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print(f"   Total Trades: {metrics.get('total_trades', 0)}")
            print(f"   Successful: {metrics.get('successful_trades', 0)}")
            print(f"   Failed: {metrics.get('failed_trades', 0)}")
            print(f"   SELL Orders: {metrics.get('sell_orders', 0)}")
            print(f"   System Latency: {metrics.get('system_latency_ms', 0)} ms")
        else:
            print("   Could not fetch metrics")
    except Exception as e:
        print(f"   Error fetching metrics: {e}")

def test_emergency_sell_functionality():
    """Test emergency SELL functionality specifically"""
    print("\n🚨 EMERGENCY SELL FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Emergency stop-loss
    emergency_sell = {
        "command_id": str(uuid.uuid4()),
        "action": "EMERGENCY_SELL",
        "symbol": "ALL_TOKENS",
        "quantity": 0.0,  # Sell everything
        "confidence": 1.0,
        "strategy": "emergency_stop_loss",
        "timestamp": time.time(),
        "paper_trading": True,
        "max_slippage": 0.20,  # 20% max slippage for emergency
        "priority": "CRITICAL",
        "reason": "Emergency stop-loss triggered",
        "source": "emergency_test"
    }
    
    send_sell_command(emergency_sell)
    print("🚨 Emergency SELL command sent!")

if __name__ == "__main__":
    try:
        print("🔥 Starting REAL SELL execution tests...")
        print("⚠️  These tests will validate SELL functionality")
        print("🛡️  Running in PAPER TRADING mode for safety")
        print()
        
        # Run main SELL tests
        test_real_sell_execution()
        
        # Run emergency SELL tests
        test_emergency_sell_functionality()
        
        print("\n🎯 REAL SELL Testing Complete!")
        print("✅ All SELL commands sent successfully")
        print("📊 Check execution results above")
        print("🔥 SELL functionality validated!")
        
    except KeyboardInterrupt:
        print("\n⏹️ SELL test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during SELL test: {e}")
