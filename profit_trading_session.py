#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Profit Trading Session
5 strategicznych transakcji z minimalnym zyskiem
"""

import json
import redis
import time
import uuid
import requests
from datetime import datetime, timezone

# Connect to DragonflyDB
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_real_market_prices():
    """Pobierz rzeczywiste ceny z Helius API"""
    try:
        # Sprawdź aktualne ceny przez system
        response = requests.get("http://localhost:8082/metrics")
        if response.status_code == 200:
            print("📊 System metrics available")
        
        # Pobierz ceny z CoinGecko jako backup
        coingecko_url = "https://api.coingecko.com/api/v3/simple/price?ids=solana,bonk,raydium&vs_currencies=usd"
        response = requests.get(coingecko_url)
        
        if response.status_code == 200:
            data = response.json()
            prices = {
                'SOL': data.get('solana', {}).get('usd', 150.0),
                'BONK': data.get('bonk', {}).get('usd', 0.000025),
                'RAY': data.get('raydium', {}).get('usd', 2.1)
            }
            print(f"📊 Real market prices fetched:")
            for symbol, price in prices.items():
                print(f"   💰 {symbol}: ${price}")
            return prices
        else:
            print("⚠️ Using fallback prices")
            return {'SOL': 150.0, 'BONK': 0.000025, 'RAY': 2.1}
    except Exception as e:
        print(f"❌ Error fetching prices: {e}")
        return {'SOL': 150.0, 'BONK': 0.000025, 'RAY': 2.1}

def create_profit_trading_command(action, symbol, quantity, strategy, target_profit_pct=2.0):
    """Stwórz komendę trading z target profit"""
    return {
        "command_id": str(uuid.uuid4()),
        "action": action,
        "symbol": symbol,
        "quantity": quantity,
        "confidence": 0.85,
        "strategy": strategy,
        "timestamp": time.time(),
        "paper_trading": False,  # LIVE TRADING dla zysku!
        "max_slippage": 0.01,  # 1% max slippage
        "priority": "HIGH",
        "target_profit_pct": target_profit_pct,
        "source": "profit_session"
    }

def send_trading_command(command):
    """Wyślij komendę trading"""
    command_json = json.dumps(command)
    print(f"📤 {command['action']} {command['quantity']} {command['symbol']}")
    print(f"   Strategy: {command['strategy']}")
    print(f"   Target Profit: {command.get('target_profit_pct', 0)}%")
    print(f"   Live Trading: {not command.get('paper_trading', True)}")
    
    r.lpush("overmind:commands", command_json)
    print("✅ Command sent!")
    return command

def wait_for_execution_and_check_profit(command_id, expected_action):
    """Czekaj na wykonanie i sprawdź zysk"""
    print(f"⏳ Waiting for {expected_action} execution...")
    
    for i in range(30):  # Wait up to 30 seconds
        time.sleep(1)
        
        # Check execution results
        results = r.lrange("overmind:execution_results", 0, -1)
        
        for result_json in results:
            try:
                result = json.loads(result_json)
                if result.get('command_id') == command_id:
                    print(f"✅ {expected_action} executed!")
                    print(f"   Status: {result.get('status', 'UNKNOWN')}")
                    print(f"   Price: ${result.get('actual_price', 'N/A')}")
                    print(f"   Amount: {result.get('actual_amount', 'N/A')}")
                    print(f"   TX ID: {result.get('tx_id', 'N/A')}")
                    
                    if result.get('profit'):
                        print(f"   💰 Profit: ${result['profit']:.6f}")
                    
                    return result
            except json.JSONDecodeError:
                continue
        
        if i % 5 == 0:
            print(f"   Still waiting... ({i}s)")
    
    print(f"⚠️ Timeout waiting for {expected_action} execution")
    return None

def execute_profit_trading_session():
    """Wykonaj sesję 5 transakcji z zyskiem"""
    
    print("🔥 THE OVERMIND PROTOCOL - PROFIT TRADING SESSION")
    print("=" * 60)
    print("🎯 Goal: 5 transactions with minimal profit")
    print("💰 Starting balance: 0.343 SOL ($51.47)")
    print("📈 Target: Small but consistent gains")
    print("⚡ Mode: LIVE TRADING")
    print("=" * 60)
    
    # Get current market prices
    prices = get_real_market_prices()
    
    total_profit = 0.0
    successful_trades = 0
    
    # Transaction 1: Quick BONK scalp (high volume, small profit)
    print(f"\n💎 Transaction 1: BONK Quick Scalp")
    print(f"   Current BONK price: ${prices['BONK']}")
    print(f"   Strategy: Buy low, sell 2% higher")
    
    # BUY BONK
    buy_cmd_1 = create_profit_trading_command(
        action="BUY",
        symbol="BONK/SOL", 
        quantity=0.02,  # 2% of portfolio
        strategy="quick_scalp_bonk",
        target_profit_pct=2.0
    )
    send_trading_command(buy_cmd_1)
    
    buy_result_1 = wait_for_execution_and_check_profit(buy_cmd_1['command_id'], "BUY")
    
    if buy_result_1 and buy_result_1.get('status') == 'SUCCESS':
        time.sleep(2)  # Wait for price movement
        
        # SELL BONK with 2% profit target
        sell_cmd_1 = create_profit_trading_command(
            action="SELL",
            symbol="BONK/SOL",
            quantity=0.02,
            strategy="quick_scalp_bonk_exit",
            target_profit_pct=2.0
        )
        send_trading_command(sell_cmd_1)
        
        sell_result_1 = wait_for_execution_and_check_profit(sell_cmd_1['command_id'], "SELL")
        
        if sell_result_1 and sell_result_1.get('profit', 0) > 0:
            profit_1 = float(sell_result_1.get('profit', 0))
            total_profit += profit_1
            successful_trades += 1
            print(f"✅ Transaction 1 PROFIT: ${profit_1:.6f}")
        else:
            print("❌ Transaction 1 failed or no profit")
    
    time.sleep(3)
    
    # Transaction 2: RAY momentum trade
    print(f"\n🚀 Transaction 2: RAY Momentum Trade")
    print(f"   Current RAY price: ${prices['RAY']}")
    print(f"   Strategy: Momentum following")
    
    buy_cmd_2 = create_profit_trading_command(
        action="BUY",
        symbol="RAY/SOL",
        quantity=0.03,  # 3% of portfolio
        strategy="momentum_ray",
        target_profit_pct=1.5
    )
    send_trading_command(buy_cmd_2)
    
    buy_result_2 = wait_for_execution_and_check_profit(buy_cmd_2['command_id'], "BUY")
    
    if buy_result_2 and buy_result_2.get('status') == 'SUCCESS':
        time.sleep(3)
        
        sell_cmd_2 = create_profit_trading_command(
            action="SELL",
            symbol="RAY/SOL",
            quantity=0.03,
            strategy="momentum_ray_exit",
            target_profit_pct=1.5
        )
        send_trading_command(sell_cmd_2)
        
        sell_result_2 = wait_for_execution_and_check_profit(sell_cmd_2['command_id'], "SELL")
        
        if sell_result_2 and sell_result_2.get('profit', 0) > 0:
            profit_2 = float(sell_result_2.get('profit', 0))
            total_profit += profit_2
            successful_trades += 1
            print(f"✅ Transaction 2 PROFIT: ${profit_2:.6f}")
        else:
            print("❌ Transaction 2 failed or no profit")
    
    time.sleep(3)
    
    # Transaction 3: SOL/USDC arbitrage
    print(f"\n⚡ Transaction 3: SOL/USDC Arbitrage")
    print(f"   Current SOL price: ${prices['SOL']}")
    print(f"   Strategy: Quick arbitrage")
    
    buy_cmd_3 = create_profit_trading_command(
        action="BUY",
        symbol="SOL/USDT",
        quantity=0.01,  # 1% of portfolio
        strategy="sol_arbitrage",
        target_profit_pct=0.5
    )
    send_trading_command(buy_cmd_3)
    
    buy_result_3 = wait_for_execution_and_check_profit(buy_cmd_3['command_id'], "BUY")
    
    if buy_result_3 and buy_result_3.get('status') == 'SUCCESS':
        time.sleep(1)
        
        sell_cmd_3 = create_profit_trading_command(
            action="SELL",
            symbol="SOL/USDT",
            quantity=0.01,
            strategy="sol_arbitrage_exit",
            target_profit_pct=0.5
        )
        send_trading_command(sell_cmd_3)
        
        sell_result_3 = wait_for_execution_and_check_profit(sell_cmd_3['command_id'], "SELL")
        
        if sell_result_3 and sell_result_3.get('profit', 0) > 0:
            profit_3 = float(sell_result_3.get('profit', 0))
            total_profit += profit_3
            successful_trades += 1
            print(f"✅ Transaction 3 PROFIT: ${profit_3:.6f}")
        else:
            print("❌ Transaction 3 failed or no profit")
    
    time.sleep(3)
    
    # Transaction 4: BONK volume play
    print(f"\n📊 Transaction 4: BONK Volume Play")
    
    buy_cmd_4 = create_profit_trading_command(
        action="BUY",
        symbol="BONK/SOL",
        quantity=0.015,
        strategy="bonk_volume_play",
        target_profit_pct=3.0
    )
    send_trading_command(buy_cmd_4)
    
    buy_result_4 = wait_for_execution_and_check_profit(buy_cmd_4['command_id'], "BUY")
    
    if buy_result_4 and buy_result_4.get('status') == 'SUCCESS':
        time.sleep(4)
        
        sell_cmd_4 = create_profit_trading_command(
            action="SELL",
            symbol="BONK/SOL",
            quantity=0.015,
            strategy="bonk_volume_exit",
            target_profit_pct=3.0
        )
        send_trading_command(sell_cmd_4)
        
        sell_result_4 = wait_for_execution_and_check_profit(sell_cmd_4['command_id'], "SELL")
        
        if sell_result_4 and sell_result_4.get('profit', 0) > 0:
            profit_4 = float(sell_result_4.get('profit', 0))
            total_profit += profit_4
            successful_trades += 1
            print(f"✅ Transaction 4 PROFIT: ${profit_4:.6f}")
        else:
            print("❌ Transaction 4 failed or no profit")
    
    time.sleep(3)
    
    # Transaction 5: Final profit lock
    print(f"\n🔒 Transaction 5: Final Profit Lock")
    
    buy_cmd_5 = create_profit_trading_command(
        action="BUY",
        symbol="RAY/SOL",
        quantity=0.025,
        strategy="final_profit_lock",
        target_profit_pct=1.0
    )
    send_trading_command(buy_cmd_5)
    
    buy_result_5 = wait_for_execution_and_check_profit(buy_cmd_5['command_id'], "BUY")
    
    if buy_result_5 and buy_result_5.get('status') == 'SUCCESS':
        time.sleep(2)
        
        sell_cmd_5 = create_profit_trading_command(
            action="SELL",
            symbol="RAY/SOL",
            quantity=0.025,
            strategy="final_profit_exit",
            target_profit_pct=1.0
        )
        send_trading_command(sell_cmd_5)
        
        sell_result_5 = wait_for_execution_and_check_profit(sell_cmd_5['command_id'], "SELL")
        
        if sell_result_5 and sell_result_5.get('profit', 0) > 0:
            profit_5 = float(sell_result_5.get('profit', 0))
            total_profit += profit_5
            successful_trades += 1
            print(f"✅ Transaction 5 PROFIT: ${profit_5:.6f}")
        else:
            print("❌ Transaction 5 failed or no profit")
    
    # Final summary
    print(f"\n🎯 PROFIT TRADING SESSION COMPLETE!")
    print("=" * 60)
    print(f"📊 Total Transactions: 5")
    print(f"✅ Successful Trades: {successful_trades}/5")
    print(f"💰 Total Profit: ${total_profit:.6f}")
    print(f"📈 Success Rate: {(successful_trades/5)*100:.1f}%")
    
    if total_profit > 0:
        starting_balance_usd = 0.343 * prices['SOL']
        profit_percentage = (total_profit / starting_balance_usd) * 100
        print(f"🚀 Profit Percentage: {profit_percentage:.3f}%")
        print(f"💎 New Balance: ~{0.343 + (total_profit/prices['SOL']):.6f} SOL")
    
    if successful_trades >= 3:
        print("🎉 SESSION SUCCESS! Minimum profit achieved!")
    else:
        print("⚠️ Session needs improvement. Analyze and retry.")
    
    return total_profit, successful_trades

if __name__ == "__main__":
    try:
        print("🔥 Starting PROFIT TRADING SESSION...")
        print("⚡ THE OVERMIND PROTOCOL - Live Trading Mode")
        print("🎯 Target: 5 transactions with minimal profit")
        print()
        
        total_profit, successful_trades = execute_profit_trading_session()
        
        print(f"\n🎯 FINAL RESULT:")
        print(f"💰 Total Profit: ${total_profit:.6f}")
        print(f"✅ Successful Trades: {successful_trades}/5")
        
        if total_profit > 0:
            print("🎉 PROFIT ACHIEVED! THE OVERMIND PROTOCOL WORKS!")
        else:
            print("📊 Learning session completed. Optimize and retry.")
            
    except KeyboardInterrupt:
        print("\n⏹️ Trading session interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during trading session: {e}")
