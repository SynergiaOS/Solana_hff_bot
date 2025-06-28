#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Simple Trading Bot Tester
Sends trading commands to test real transactions on Solana Devnet
"""

import asyncio
import json
import time
import requests
from datetime import datetime
import redis.asyncio as redis

# Configuration
DRAGONFLY_URL = "redis://127.0.0.1:6379"
RUST_EXECUTOR_URL = "http://localhost:8082"
HELIUS_API_KEY = "edbcd361-78a0-4998-bd1e-8d4666722f82"
HELIUS_RPC_URL = f"https://devnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

class SimpleTradingBot:
    def __init__(self):
        self.redis_client = None
        self.running = False
        
    async def connect_redis(self):
        """Connect to DragonflyDB"""
        try:
            self.redis_client = redis.from_url(DRAGONFLY_URL)
            await self.redis_client.ping()
            print("✅ Connected to DragonflyDB")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to DragonflyDB: {e}")
            return False
    
    def check_rust_executor(self):
        """Check if Rust executor is running"""
        try:
            response = requests.get(f"{RUST_EXECUTOR_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Rust Executor is healthy")
                return True
            else:
                print(f"❌ Rust Executor unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach Rust Executor: {e}")
            return False
    
    def get_sol_price(self):
        """Get current SOL price from CoinGecko"""
        try:
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                price = data['solana']['usd']
                print(f"💰 Current SOL price: ${price}")
                return price
            else:
                print(f"❌ Failed to get SOL price: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting SOL price: {e}")
            return None
    
    async def send_trading_command(self, action, symbol, quantity, price, confidence=0.8):
        """Send trading command to Rust executor via DragonflyDB"""
        command = {
            "action": action,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simple_trading_bot"
        }
        
        try:
            command_json = json.dumps(command)
            await self.redis_client.lpush("overmind:commands", command_json)
            print(f"📤 Sent command: {action} {quantity} {symbol} @ ${price}")
            return True
        except Exception as e:
            print(f"❌ Failed to send command: {e}")
            return False
    
    async def monitor_responses(self):
        """Monitor responses from Rust executor"""
        print("👂 Monitoring responses from Rust executor...")
        while self.running:
            try:
                # Check for responses
                response = await self.redis_client.brpop("overmind:responses", timeout=1)
                if response:
                    _, response_data = response
                    response_json = json.loads(response_data.decode('utf-8'))
                    print(f"📥 Response: {response_json}")
            except Exception as e:
                if self.running:
                    print(f"❌ Error monitoring responses: {e}")
            await asyncio.sleep(0.1)
    
    async def run_trading_simulation(self):
        """Run a simple trading simulation"""
        print("\n🚀 Starting THE OVERMIND PROTOCOL Trading Simulation")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_rust_executor():
            return
        
        if not await self.connect_redis():
            return
        
        self.running = True
        
        # Start response monitor
        monitor_task = asyncio.create_task(self.monitor_responses())
        
        try:
            previous_price = None
            trade_count = 0
            
            for i in range(10):  # Run 10 trading cycles
                print(f"\n📊 Trading Cycle {i+1}/10")
                print("-" * 30)
                
                # Get current SOL price
                current_price = self.get_sol_price()
                if current_price is None:
                    print("⚠️ Skipping cycle due to price fetch failure")
                    await asyncio.sleep(10)
                    continue
                
                # Determine trading action
                if previous_price is None:
                    action = "HOLD"
                    print("📊 First cycle - HOLDING")
                elif current_price > previous_price:
                    action = "BUY"
                    print(f"📈 Price increased (${previous_price:.2f} → ${current_price:.2f}) - BUYING")
                elif current_price < previous_price:
                    action = "SELL"
                    print(f"📉 Price decreased (${previous_price:.2f} → ${current_price:.2f}) - SELLING")
                else:
                    action = "HOLD"
                    print("📊 Price unchanged - HOLDING")
                
                # Send trading command (only for BUY/SELL)
                if action in ["BUY", "SELL"]:
                    quantity = 0.1  # Small amount for testing
                    confidence = 0.8
                    
                    success = await self.send_trading_command(
                        action, "SOL", quantity, current_price, confidence
                    )
                    
                    if success:
                        trade_count += 1
                        print(f"✅ Trade #{trade_count} sent successfully")
                    else:
                        print("❌ Failed to send trade")
                
                previous_price = current_price
                
                # Wait before next cycle
                print("⏳ Waiting 15 seconds before next cycle...")
                await asyncio.sleep(15)
            
            print(f"\n🎉 Trading simulation completed!")
            print(f"📊 Total trades sent: {trade_count}")
            
        except KeyboardInterrupt:
            print("\n⚠️ Trading simulation interrupted by user")
        except Exception as e:
            print(f"\n❌ Trading simulation error: {e}")
        finally:
            self.running = False
            monitor_task.cancel()
            if self.redis_client:
                await self.redis_client.close()
            print("🛑 Trading simulation stopped")

async def main():
    """Main function"""
    print("🧠 THE OVERMIND PROTOCOL - Simple Trading Bot")
    print("🎯 Testing real transactions on Solana Devnet")
    print("⚠️  PAPER TRADING MODE - No real money at risk")
    print()
    
    bot = SimpleTradingBot()
    await bot.run_trading_simulation()

if __name__ == "__main__":
    asyncio.run(main())
