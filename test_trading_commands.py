#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Test Trading Commands
Symuluje kilka transakcji w paper trading mode
"""

import json
import redis
import time
import uuid
from datetime import datetime, timezone

# Connect to DragonflyDB
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def create_test_trading_command(action, symbol, quantity, strategy="memecoin_hunter"):
    """Create a test trading command compatible with THE OVERMIND PROTOCOL"""
    return {
        "command_id": str(uuid.uuid4()),
        "action": action,  # "BUY" or "SELL"
        "symbol": symbol,  # Trading symbol (e.g., "SOL/USDT", "BONK/SOL")
        "quantity": quantity,  # Quantity to trade
        "confidence": 0.85,
        "strategy": strategy,
        "timestamp": time.time(),  # Unix timestamp
        "paper_trading": True,
        "max_slippage": 0.02,
        "priority": "high",
        "source": "test_session"
    }

def send_trading_command(command):
    """Send trading command to THE OVERMIND PROTOCOL"""
    command_json = json.dumps(command)
    print(f"📤 Sending command: {command['action']} {command['quantity']} {command['symbol']}")
    print(f"   Strategy: {command['strategy']}")
    print(f"   Confidence: {command['confidence']}")

    # Send to overmind:commands queue
    r.lpush("overmind:commands", command_json)
    print("✅ Command sent to overmind:commands")
    return command

def check_execution_results():
    """Check for execution results"""
    print("\n🔍 Checking execution results...")
    
    # Check execution:results queue
    results = r.lrange("execution:results", 0, -1)
    
    if results:
        print(f"📊 Found {len(results)} execution results:")
        for i, result_json in enumerate(results):
            try:
                result = json.loads(result_json)
                print(f"\n   Result {i+1}:")
                print(f"   Status: {result.get('status', 'UNKNOWN')}")
                print(f"   TX ID: {result.get('tx_id', 'N/A')}")
                print(f"   Price: {result.get('actual_price', 'N/A')}")
                print(f"   Amount: {result.get('actual_amount', 'N/A')} SOL")
                print(f"   Execution Time: {result.get('execution_time_ms', 'N/A')} ms")
                if result.get('error_message'):
                    print(f"   Error: {result['error_message']}")
            except json.JSONDecodeError:
                print(f"   Invalid JSON in result {i+1}")
    else:
        print("   No execution results found")

def run_test_trading_session():
    """Run a test trading session with multiple commands"""
    
    print("🚀 THE OVERMIND PROTOCOL - Test Trading Session")
    print("=" * 60)
    print("Mode: Paper Trading")
    print("Target: Test 5 transactions")
    print("=" * 60)
    
    # Test trading pairs (popular on Solana)
    test_symbols = [
        "SOL/USDT",   # SOL to USDT
        "BONK/SOL",   # Bonk to SOL
        "ETH/SOL",    # Ethereum to SOL
        "MSOL/SOL",   # Marinade SOL to SOL
        "USDC/SOL",   # USDC to SOL
    ]
    
    commands = []
    
    # Test 1: Small BUY order
    print("\n📈 Test 1: Small BUY order (Memecoin Hunter)")
    cmd1 = create_test_trading_command(
        action="BUY",
        symbol=test_symbols[1],  # BONK/SOL
        quantity=0.01,  # Small test amount
        strategy="memecoin_hunter"
    )
    commands.append(send_trading_command(cmd1))
    time.sleep(2)

    # Test 2: Medium BUY order
    print("\n📈 Test 2: Medium BUY order (Soul Meteor)")
    cmd2 = create_test_trading_command(
        action="BUY",
        symbol=test_symbols[2],  # ETH/SOL
        quantity=0.05,
        strategy="soul_meteor"
    )
    commands.append(send_trading_command(cmd2))
    time.sleep(2)

    # Test 3: SELL order
    print("\n📉 Test 3: SELL order (Developer Tracking)")
    cmd3 = create_test_trading_command(
        action="SELL",
        symbol=test_symbols[1],  # BONK/SOL
        quantity=0.008,
        strategy="developer_tracking"
    )
    commands.append(send_trading_command(cmd3))
    time.sleep(2)

    # Test 4: Large BUY order (test position sizing)
    print("\n📈 Test 4: Large BUY order (SOL Momentum)")
    cmd4 = create_test_trading_command(
        action="BUY",
        symbol=test_symbols[3],  # MSOL/SOL
        quantity=0.08,  # Larger amount
        strategy="sol_momentum"
    )
    commands.append(send_trading_command(cmd4))
    time.sleep(2)

    # Test 5: Quick arbitrage
    print("\n⚡ Test 5: Quick arbitrage (Meteora DAMM)")
    cmd5 = create_test_trading_command(
        action="BUY",
        symbol=test_symbols[4],  # USDC/SOL
        quantity=0.02,
        strategy="meteora_damm_v2"
    )
    commands.append(send_trading_command(cmd5))
    
    print(f"\n✅ Sent {len(commands)} test trading commands")
    print("⏳ Waiting for execution results...")
    
    # Wait for execution
    time.sleep(5)
    
    # Check results
    check_execution_results()
    
    # Check system metrics
    print("\n📊 System Metrics After Testing:")
    try:
        import requests
        response = requests.get("http://localhost:8082/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print(f"   Total Trades: {metrics.get('total_trades', 0)}")
            print(f"   Successful: {metrics.get('successful_trades', 0)}")
            print(f"   Failed: {metrics.get('failed_trades', 0)}")
            print(f"   AI Decisions: {metrics.get('ai_decisions', 0)}")
            print(f"   System Latency: {metrics.get('system_latency_ms', 0)} ms")
        else:
            print("   Could not fetch metrics")
    except Exception as e:
        print(f"   Error fetching metrics: {e}")
    
    print("\n🎯 Test Trading Session Complete!")
    print("Check logs for detailed execution information")

if __name__ == "__main__":
    try:
        run_test_trading_session()
    except KeyboardInterrupt:
        print("\n⏹️ Test session interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during test session: {e}")
