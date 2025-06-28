#!/usr/bin/env python3
"""
Start 14-Day Live Paper Trading
Launch the complete 14-day paper trading validation for THE OVERMIND PROTOCOL
"""

import asyncio
import logging
import sys
import os
import signal
from datetime import datetime

# Add brain module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'brain', 'src'))

from overmind_brain.live_paper_trading import LivePaperTradingSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class LiveTradingLauncher:
    """Launcher for 14-day live paper trading"""
    
    def __init__(self):
        self.system = None
        self.running = False
    
    async def start_14_day_trading(self):
        """Start the complete 14-day trading session"""
        
        print("🚀 THE OVERMIND PROTOCOL - 14-Day Live Paper Trading")
        print("=" * 60)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Duration: 14 days")
        print("Mode: Paper Trading (No real money)")
        print("Strategy: SOL Momentum with Risk Management")
        print("=" * 60)
        
        try:
            # Initialize system
            self.system = LivePaperTradingSystem(
                initial_balance=10000.0,  # $10,000 starting balance
                session_duration_days=14
            )
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start trading session
            session_id = await self.system.start_live_trading_session()
            
            print(f"✅ Session started: {session_id}")
            print("📊 Monitoring will run continuously...")
            print("📋 Daily reports will be generated automatically")
            print("🛑 Press Ctrl+C to stop gracefully")
            print("-" * 60)
            
            # Run the trading loop
            self.running = True
            await self.system.run_live_trading_loop()
            
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
            await self._graceful_shutdown()
        except Exception as e:
            logger.error(f"❌ Error in live trading: {e}")
            await self._graceful_shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.system:
            asyncio.create_task(self.system.stop_trading_session())
    
    async def _graceful_shutdown(self):
        """Perform graceful shutdown"""
        if self.system:
            await self.system.stop_trading_session()
        print("✅ Shutdown complete")

async def main():
    """Main entry point"""
    
    # Load environment variables
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Check required environment variables
    required_vars = ['HELIUS_API_KEY', 'QUICKNODE_MAINNET_RPC_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease configure these in your .env file")
        return False
    
    # Check if SOL Momentum is enabled
    enabled_strategies = os.getenv('ENABLED_STRATEGIES', '').split(',')
    if 'sol_momentum' not in [s.strip() for s in enabled_strategies]:
        print("❌ SOL Momentum strategy not enabled")
        print("Please add 'sol_momentum' to ENABLED_STRATEGIES in .env")
        return False
    
    print("✅ Environment configuration validated")
    
    # Start the launcher
    launcher = LiveTradingLauncher()
    await launcher.start_14_day_trading()
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
