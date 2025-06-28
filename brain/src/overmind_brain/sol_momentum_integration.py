#!/usr/bin/env python3
"""
SOL Momentum Strategy Integration
Integration layer between SOL Momentum Strategy and THE OVERMIND PROTOCOL
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from .sol_momentum_strategy import SOLMomentumStrategy, TradingSignal, SignalType
    from .strategy_manager import strategy_manager
    from .strategy_config import StrategyType
except ImportError:
    # Direct import for testing
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from sol_momentum_strategy import SOLMomentumStrategy, TradingSignal, SignalType
    from strategy_manager import strategy_manager
    from strategy_config import StrategyType

logger = logging.getLogger(__name__)

class SOLMomentumIntegration:
    """
    Integration layer for SOL Momentum Strategy with THE OVERMIND PROTOCOL
    """
    
    def __init__(self):
        # Load QuickNode URL from environment
        self._load_environment()
        
        # Initialize strategy with Helius API
        self.strategy = SOLMomentumStrategy(self.helius_api_key, self.quicknode_url)
        self.last_signal: Optional[TradingSignal] = None
        
        logger.info("🚀 SOL Momentum Integration initialized")
    
    def _load_environment(self):
        """Load environment configuration"""
        # Load .env manually
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Get Helius API key (primary for Python AI Brain)
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        if not self.helius_api_key:
            raise ValueError("Helius API key not configured")

        # Get QuickNode URL (optional, for slot reference)
        self.quicknode_url = os.getenv('QUICKNODE_MAINNET_RPC_URL')
        
        # Check if SOL Momentum is enabled
        enabled_strategies_str = os.getenv("ENABLED_STRATEGIES", "")
        enabled_strategies = [s.strip() for s in enabled_strategies_str.split(",")]
        self.enabled = "sol_momentum" in enabled_strategies

        # For testing, enable by default if not explicitly disabled
        if not enabled_strategies_str or enabled_strategies == [""]:
            self.enabled = True

        print(f"Helius API Key: {'Configured' if self.helius_api_key else 'Missing'}")
        print(f"QuickNode URL: {self.quicknode_url[:50] if self.quicknode_url else 'None'}...")
        print(f"ENABLED_STRATEGIES env: '{enabled_strategies_str}'")
        print(f"Parsed strategies: {enabled_strategies}")
        print(f"SOL Momentum enabled: {self.enabled}")
        logger.info(f"SOL Momentum enabled: {self.enabled}")
    
    async def initialize(self) -> bool:
        """Initialize the integration"""
        try:
            print(f"Initializing SOL Momentum integration...")
            print(f"Enabled: {self.enabled}")

            if not self.enabled:
                print("SOL Momentum strategy not enabled")
                logger.info("SOL Momentum strategy not enabled")
                return False

            print("Testing strategy connection...")

            # Build initial price history (need at least 5 points for short MA)
            print("Building initial price history...")
            for i in range(6):  # Get 6 data points
                success = await self.strategy.update_price_history()
                if success:
                    print(f"  Data point {i+1}/6 collected")
                else:
                    print(f"  Failed to collect data point {i+1}")
                    return False

                if i < 5:  # Don't sleep after last iteration
                    await asyncio.sleep(1)  # Wait 1 second between data points

            # Now test signal generation
            test_signal = self.strategy.generate_signal()
            print(f"Test signal result: {test_signal}")

            if test_signal:
                print("✅ SOL Momentum integration initialized successfully")
                logger.info("✅ SOL Momentum integration initialized successfully")
                return True
            else:
                print("⚠️ No signal generated (this is normal for HOLD signals)")
                print("✅ SOL Momentum integration initialized successfully")
                logger.info("✅ SOL Momentum integration initialized successfully")
                return True  # Strategy is working even if no signal

        except Exception as e:
            print(f"Error initializing SOL Momentum integration: {e}")
            logger.error(f"Error initializing SOL Momentum integration: {e}")
            return False
    
    async def generate_trading_signal(self) -> Optional[Dict[str, Any]]:
        """Generate trading signal for THE OVERMIND PROTOCOL"""
        if not self.enabled:
            return None
        
        try:
            # Run strategy cycle
            signal = await self.strategy.run_strategy_cycle()
            if not signal:
                return None
            
            self.last_signal = signal
            
            # Convert to OVERMIND format
            overmind_signal = {
                "signal_id": f"sol_momentum_{int(signal.timestamp.timestamp())}",
                "strategy_type": "sol_momentum",
                "symbol": "SOL",
                "signal_type": signal.signal_type.value.lower(),
                "action": signal.signal_type.value,
                "confidence": signal.confidence,
                "price": signal.price,
                "timestamp": signal.timestamp.isoformat(),
                "reasoning": signal.reasoning,
                "risk_level": signal.risk_level.lower(),
                "indicators": signal.indicators,
                "metadata": {
                    "strategy_name": "SOL Momentum",
                    "short_ma": signal.indicators.get("short_ma"),
                    "long_ma": signal.indicators.get("long_ma"),
                    "rsi": signal.indicators.get("rsi"),
                    "volume_ratio": signal.indicators.get("volume_ratio"),
                    "ma_diff": signal.indicators.get("ma_diff")
                }
            }
            
            logger.info(f"📊 SOL Momentum Signal: {signal.signal_type.value} "
                       f"(Confidence: {signal.confidence:.2f})")
            
            return overmind_signal
            
        except Exception as e:
            logger.error(f"Error generating SOL momentum signal: {e}")
            return None
    
    async def validate_signal_with_strategy_manager(self, signal_data: Dict[str, Any]) -> bool:
        """Validate signal with strategy manager"""
        try:
            # Check if SOL Momentum strategy is enabled in strategy manager
            try:
                enabled_strategies = strategy_manager.config_manager.get_enabled_strategies()
                if StrategyType.SOL_MOMENTUM not in enabled_strategies:
                    logger.warning("SOL Momentum not enabled in strategy manager")
                    return False
            except AttributeError:
                # Fallback - assume enabled for testing
                logger.info("Strategy manager config not available, assuming enabled")
            
            # Validate signal
            strategy_matches = strategy_manager.select_and_validate_strategies(signal_data)
            
            # Check if SOL Momentum qualified
            sol_momentum_match = None
            for match in strategy_matches:
                if match.strategy_type == StrategyType.SOL_MOMENTUM:
                    sol_momentum_match = match
                    break
            
            if sol_momentum_match:
                logger.info(f"✅ SOL Momentum validated by strategy manager "
                           f"(Score: {sol_momentum_match.match_score:.2f})")
                return True
            else:
                logger.info("❌ SOL Momentum not validated by strategy manager")
                return False
                
        except Exception as e:
            logger.error(f"Error validating with strategy manager: {e}")
            return False
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """Get current strategy status"""
        base_status = self.strategy.get_strategy_status()
        
        return {
            **base_status,
            "integration_enabled": self.enabled,
            "last_signal": {
                "type": self.last_signal.signal_type.value if self.last_signal else None,
                "confidence": self.last_signal.confidence if self.last_signal else None,
                "timestamp": self.last_signal.timestamp.isoformat() if self.last_signal else None
            } if self.last_signal else None,
            "quicknode_url_configured": bool(self.quicknode_url and 'your-mainnet-endpoint' not in self.quicknode_url)
        }
    
    async def run_continuous_monitoring(self, interval_seconds: int = 60) -> None:
        """Run continuous monitoring and signal generation"""
        if not self.enabled:
            logger.info("SOL Momentum not enabled, skipping continuous monitoring")
            return
        
        logger.info(f"🔄 Starting SOL Momentum continuous monitoring (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Generate signal
                signal = await self.generate_trading_signal()
                
                if signal and signal['action'] != 'HOLD':
                    # Validate with strategy manager
                    validated = await self.validate_signal_with_strategy_manager(signal)
                    
                    if validated:
                        logger.info(f"🎯 VALIDATED SIGNAL: {signal['action']} SOL "
                                   f"(Confidence: {signal['confidence']:.2f})")
                        # Here you would send to the main trading engine
                    else:
                        logger.info(f"⚠️ Signal not validated by strategy manager")
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(interval_seconds)

# Global instance - will be created when needed
sol_momentum_integration = None

# Test function
async def test_sol_momentum_integration():
    """Test SOL Momentum integration"""
    print("🧪 Testing SOL Momentum Integration")
    print("-" * 50)

    try:
        # Create fresh instance for testing
        integration = SOLMomentumIntegration()

        # Initialize
        try:
            success = await integration.initialize()
            if not success:
                print("❌ Integration initialization failed")
                return False
        except Exception as e:
            print(f"❌ Integration initialization error: {e}")
            return False
        
        print("✅ Integration initialized")
        
        # Generate signal
        signal = await integration.generate_trading_signal()
        if signal:
            print(f"✅ Signal generated: {signal['action']} (Confidence: {signal['confidence']:.2f})")
            print(f"   Reasoning: {signal['reasoning']}")

            # Validate with strategy manager
            validated = await integration.validate_signal_with_strategy_manager(signal)
            print(f"   Strategy Manager Validation: {'✅ PASSED' if validated else '❌ FAILED'}")
        else:
            print("⚠️ No signal generated")

        # Get status
        status = integration.get_strategy_status()
        print(f"\n📊 Integration Status:")
        print(f"   Enabled: {status['integration_enabled']}")
        print(f"   Strategy Ready: {status['strategy_ready']}")
        print(f"   Price History: {status['price_history_length']} points")
        print(f"   QuickNode Configured: {status['quicknode_url_configured']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_sol_momentum_integration())
