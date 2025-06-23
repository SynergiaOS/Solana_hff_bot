#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Continuous Trading Test
Simulates continuous trading activity to test the system under load
"""

import asyncio
import json
import time
import random
import subprocess
from datetime import datetime

# Trading parameters
SYMBOLS = ["SOL", "USDC", "ORCA", "RAY"]
ACTIONS = ["BUY", "SELL"]
MIN_QUANTITY = 0.01
MAX_QUANTITY = 0.5
MIN_PRICE = 50.0
MAX_PRICE = 200.0
MIN_CONFIDENCE = 0.5
MAX_CONFIDENCE = 0.95

class ContinuousTradingTest:
    def __init__(self, trades_per_minute=6, duration_minutes=5):
        self.trades_per_minute = trades_per_minute
        self.duration_minutes = duration_minutes
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        
    def generate_trading_signal(self):
        """Generate a random trading signal"""
        return {
            "action": random.choice(ACTIONS),
            "symbol": random.choice(SYMBOLS),
            "quantity": round(random.uniform(MIN_QUANTITY, MAX_QUANTITY), 3),
            "price": round(random.uniform(MIN_PRICE, MAX_PRICE), 2),
            "confidence": round(random.uniform(MIN_CONFIDENCE, MAX_CONFIDENCE), 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "continuous_trading_test"
        }
    
    def send_command_to_redis(self, command):
        """Send command to Redis using redis-cli"""
        try:
            command_json = json.dumps(command)
            result = subprocess.run([
                "redis-cli", "LPUSH", "overmind:commands", command_json
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                self.successful_trades += 1
                return True
            else:
                print(f"❌ Redis error: {result.stderr}")
                self.failed_trades += 1
                return False
        except Exception as e:
            print(f"❌ Failed to send command: {e}")
            self.failed_trades += 1
            return False
    
    def run_continuous_trading(self):
        """Run continuous trading simulation"""
        print("🚀 THE OVERMIND PROTOCOL - Continuous Trading Test")
        print("=" * 60)
        print(f"📊 Configuration:")
        print(f"   • Trades per minute: {self.trades_per_minute}")
        print(f"   • Duration: {self.duration_minutes} minutes")
        print(f"   • Total trades planned: {self.trades_per_minute * self.duration_minutes}")
        print(f"   • Interval: {60 / self.trades_per_minute:.1f} seconds")
        print()
        
        interval = 60.0 / self.trades_per_minute
        start_time = time.time()
        end_time = start_time + (self.duration_minutes * 60)
        
        print("🎯 Starting continuous trading...")
        print("-" * 40)
        
        try:
            while time.time() < end_time:
                # Generate and send trading signal
                signal = self.generate_trading_signal()
                self.total_trades += 1
                
                print(f"📤 Trade #{self.total_trades}: {signal['action']} {signal['quantity']} {signal['symbol']} @ ${signal['price']} (conf: {signal['confidence']})")
                
                success = self.send_command_to_redis(signal)
                if success:
                    print(f"   ✅ Sent successfully")
                else:
                    print(f"   ❌ Failed to send")
                
                # Wait for next trade
                time.sleep(interval)
                
                # Show progress every 10 trades
                if self.total_trades % 10 == 0:
                    elapsed = time.time() - start_time
                    remaining = end_time - time.time()
                    print(f"\n📊 Progress: {self.total_trades} trades sent, {elapsed:.1f}s elapsed, {remaining:.1f}s remaining")
                    print(f"   Success rate: {self.successful_trades}/{self.total_trades} ({100*self.successful_trades/self.total_trades:.1f}%)")
                    print("-" * 40)
        
        except KeyboardInterrupt:
            print("\n⚠️ Trading test interrupted by user")
        
        # Final statistics
        elapsed_total = time.time() - start_time
        print(f"\n🎉 Continuous Trading Test Completed!")
        print("=" * 60)
        print(f"📊 Final Statistics:")
        print(f"   • Total trades sent: {self.total_trades}")
        print(f"   • Successful: {self.successful_trades}")
        print(f"   • Failed: {self.failed_trades}")
        print(f"   • Success rate: {100*self.successful_trades/self.total_trades:.1f}%")
        print(f"   • Duration: {elapsed_total:.1f} seconds")
        print(f"   • Average rate: {self.total_trades/elapsed_total*60:.1f} trades/minute")
        print()
        
        # Check system status
        print("🔍 Checking system status...")
        try:
            result = subprocess.run([
                "curl", "-s", "http://localhost:8082/health"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("✅ System is still healthy")
            else:
                print("❌ System health check failed")
        except Exception as e:
            print(f"❌ Could not check system health: {e}")

def main():
    print("🧠 THE OVERMIND PROTOCOL - Continuous Trading Test")
    print("🎯 Testing system under continuous load")
    print("⚠️  PAPER TRADING MODE - No real money at risk")
    print()
    
    # Configuration
    trades_per_minute = 6  # 1 trade every 10 seconds
    duration_minutes = 3   # Run for 3 minutes
    
    test = ContinuousTradingTest(trades_per_minute, duration_minutes)
    test.run_continuous_trading()

if __name__ == "__main__":
    main()
