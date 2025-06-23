"""THE OVERMIND PROTOCOL - Simple Brain Implementation
Simple trend follower strategy for testing the neural communication system.
"""

import asyncio
import json
import logging
import os
import time
from typing import Optional

# Try to import redis, fall back to basic implementation if not available
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis not available, using mock implementation")

from .tools.market_data_tool import get_sol_price

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleBrain:
    """Simple AI Brain implementing trend follower strategy"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_client = None
        self.previous_price: float = 0.0
        self.running = False
        
        # Strategy parameters
        self.price_check_interval = 10  # seconds
        self.min_price_change = 0.01  # minimum 1% change to trigger action
        
        logger.info(f"🧠 SimpleBrain initialized - Redis: {redis_host}:{redis_port}")
    
    async def connect_to_dragonfly(self) -> bool:
        """Connect to DragonflyDB (Redis-compatible)"""
        if not REDIS_AVAILABLE:
            logger.warning("⚠️ Redis not available, using mock mode")
            return True
        
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Connected to DragonflyDB")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to DragonflyDB: {e}")
            return False
    
    async def send_command_to_executor(self, action: str, price: float, confidence: float = 0.8) -> bool:
        """Send trading command to the Rust executor"""
        command = {
            "timestamp": time.time(),
            "action": action,
            "symbol": "SOL/USDC",
            "price": price,
            "confidence": confidence,
            "strategy": "trend_follower",
            "source": "simple_brain"
        }
        
        command_json = json.dumps(command)
        
        try:
            if REDIS_AVAILABLE and self.redis_client:
                # Send to DragonflyDB
                await self.redis_client.lpush("overmind:commands", command_json)
                logger.info(f"📤 Command sent to executor: {action} SOL at ${price:.4f}")
            else:
                # Mock mode - just log
                logger.info(f"🔄 [MOCK] Command would be sent: {action} SOL at ${price:.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send command: {e}")
            return False
    
    def analyze_price_trend(self, current_price: float, previous_price: float) -> str:
        """Analyze price trend and determine action"""
        if previous_price == 0.0:
            return "HOLD"  # First price reading
        
        price_change_percent = ((current_price - previous_price) / previous_price) * 100
        
        if abs(price_change_percent) < self.min_price_change:
            return "HOLD"  # Not enough change
        elif price_change_percent > 0:
            return "BUY"   # Price going up
        else:
            return "SELL"  # Price going down
    
    async def run_trend_follower_strategy(self):
        """Main strategy loop - trend follower"""
        logger.info("🚀 Starting trend follower strategy...")
        
        # Connect to DragonflyDB
        connected = await self.connect_to_dragonfly()
        if not connected and REDIS_AVAILABLE:
            logger.error("❌ Cannot connect to DragonflyDB, exiting")
            return
        
        self.running = True
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                logger.info(f"🔄 Strategy iteration #{iteration}")
                
                # Step 1: Get current SOL price
                current_price = await get_sol_price()
                
                if current_price is None:
                    logger.error("❌ Failed to get SOL price, skipping iteration")
                    await asyncio.sleep(self.price_check_interval)
                    continue
                
                # Step 2: Analyze trend
                action = self.analyze_price_trend(current_price, self.previous_price)
                
                # Step 3: Log decision
                if self.previous_price > 0:
                    price_change = current_price - self.previous_price
                    price_change_percent = (price_change / self.previous_price) * 100
                    
                    logger.info(f"📊 Price Analysis:")
                    logger.info(f"   Previous: ${self.previous_price:.4f}")
                    logger.info(f"   Current:  ${current_price:.4f}")
                    logger.info(f"   Change:   ${price_change:+.4f} ({price_change_percent:+.2f}%)")
                    logger.info(f"   Decision: {action}")
                else:
                    logger.info(f"📊 Initial price reading: ${current_price:.4f}")
                    logger.info(f"   Decision: {action} (first reading)")
                
                # Step 4: Send command if action is BUY or SELL
                if action in ["BUY", "SELL"]:
                    confidence = min(0.9, 0.5 + abs((current_price - self.previous_price) / self.previous_price))
                    success = await self.send_command_to_executor(action, current_price, confidence)
                    
                    if success:
                        logger.info(f"✅ {action} command sent successfully")
                    else:
                        logger.error(f"❌ Failed to send {action} command")
                elif action == "HOLD":
                    logger.info("⏸️ Holding position - no significant price change")
                
                # Step 5: Update previous price
                self.previous_price = current_price
                
                # Step 6: Wait for next iteration
                logger.info(f"⏰ Waiting {self.price_check_interval} seconds for next check...")
                await asyncio.sleep(self.price_check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"❌ Strategy execution failed: {e}")
        finally:
            self.running = False
            if self.redis_client:
                await self.redis_client.close()
            logger.info("🏁 Trend follower strategy stopped")
    
    async def stop(self):
        """Stop the brain"""
        logger.info("🛑 Stopping SimpleBrain...")
        self.running = False

# Main execution function
async def main():
    """Main entry point for simple brain"""
    logger.info("🧠 THE OVERMIND PROTOCOL - Simple Brain Starting...")
    
    # Get configuration from environment
    redis_host = os.getenv("DRAGONFLY_HOST", "localhost")
    redis_port = int(os.getenv("DRAGONFLY_PORT", "6379"))
    
    # Create and run brain
    brain = SimpleBrain(redis_host=redis_host, redis_port=redis_port)
    
    try:
        await brain.run_trend_follower_strategy()
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Brain execution failed: {e}")
    finally:
        await brain.stop()

if __name__ == "__main__":
    asyncio.run(main())
