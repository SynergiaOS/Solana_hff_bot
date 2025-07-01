#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Intelligent Trading Manager
Integrates Capital Allocator with trading signal processing
"""

import json
import redis
import time
import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from capital_allocator import create_capital_allocator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('IntelligentTradingManager')

class IntelligentTradingManager:
    """
    Intelligent Trading Manager with Dynamic Capital Allocation
    
    Processes trading signals and calculates optimal position sizes
    using the Capital Allocator before sending commands to Rust Executor
    """
    
    def __init__(self):
        """Initialize Intelligent Trading Manager"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.capital_allocator = create_capital_allocator()
        
        # Signal processing stats
        self.signal_stats = {
            'total_signals': 0,
            'processed_signals': 0,
            'rejected_signals': 0,
            'total_allocated_capital': 0.0
        }
        
        # Running flag
        self.running = False
        
        logger.info("🧠 Intelligent Trading Manager initialized")
        logger.info("💰 Dynamic Capital Allocation enabled")
        logger.info("🎯 Ready to process trading signals with optimal position sizing")
    
    async def start_signal_processing(self):
        """Start processing trading signals with intelligent allocation"""
        logger.info("🎯 Starting Intelligent Signal Processing...")
        self.running = True
        
        while self.running:
            try:
                # Listen for strategy signals
                result = self.redis_client.blpop("overmind:strategy_signals", timeout=5)
                
                if result:
                    _, signal_data = result
                    signal = json.loads(signal_data)
                    
                    await self.process_trading_signal(signal)
                
                # Also listen for manual trading commands (pass-through)
                result = self.redis_client.blpop("overmind:manual_commands", timeout=1)
                
                if result:
                    _, command_data = result
                    command = json.loads(command_data)
                    
                    # Pass manual commands directly to executor
                    self.redis_client.lpush("overmind:commands", json.dumps(command))
                    logger.info(f"📤 Manual command passed through: {command.get('action')} {command.get('symbol')}")
                
            except Exception as e:
                logger.error(f"❌ Error in signal processing: {e}")
                await asyncio.sleep(5)
    
    async def process_trading_signal(self, signal: Dict[str, Any]):
        """Process trading signal with intelligent capital allocation"""
        try:
            self.signal_stats['total_signals'] += 1
            
            logger.info(f"📊 Processing trading signal: {signal.get('signal_type', 'unknown')}")
            logger.info(f"   Token: {signal.get('token', 'UNKNOWN')}")
            logger.info(f"   Strategy: {signal.get('strategy', 'unknown')}")
            
            # Extract signal parameters
            signal_confidence = self.extract_signal_confidence(signal)
            strategy = signal.get('strategy', 'unknown')
            market_data = self.extract_market_data(signal)
            
            # Calculate optimal position size using Capital Allocator
            position_size, allocation_details = self.capital_allocator.calculate_position_size(
                signal_confidence=signal_confidence,
                strategy=strategy,
                market_data=market_data
            )
            
            # Check if position size is sufficient to trade
            if position_size <= 0:
                logger.info(f"🚫 Signal rejected: {allocation_details.get('reason', 'insufficient allocation')}")
                self.signal_stats['rejected_signals'] += 1
                return
            
            # Create optimized trading command
            trading_command = self.create_trading_command(signal, position_size, allocation_details)
            
            # Send to Rust Executor
            self.redis_client.lpush("overmind:commands", json.dumps(trading_command))
            
            # Update stats
            self.signal_stats['processed_signals'] += 1
            self.signal_stats['total_allocated_capital'] += position_size
            
            # Update capital allocator exposure
            self.capital_allocator.update_portfolio_exposure(position_size)
            
            logger.info(f"🚀 INTELLIGENT TRADING COMMAND SENT!")
            logger.info(f"   Action: {trading_command['action']}")
            logger.info(f"   Symbol: {trading_command['symbol']}")
            logger.info(f"   Position Size: {position_size:.1%}")
            logger.info(f"   Allocation Reasoning: {allocation_details.get('allocation_reasoning', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Error processing trading signal: {e}")
    
    def extract_signal_confidence(self, signal: Dict[str, Any]) -> float:
        """Extract confidence score from trading signal"""
        # Try different confidence field names
        confidence_fields = [
            'confidence', 'confidence_score', 'sentiment_score', 
            'impact_score', 'signal_strength', 'probability'
        ]
        
        for field in confidence_fields:
            if field in signal:
                confidence = signal[field]
                if isinstance(confidence, (int, float)):
                    return max(0.0, min(1.0, float(confidence)))
        
        # Default confidence based on signal type
        signal_type = signal.get('signal_type', '').lower()
        if 'governance' in signal_type:
            return 0.8  # High confidence for governance signals
        elif 'memecoin' in signal_type:
            return 0.6  # Medium confidence for memecoin signals
        else:
            return 0.5  # Default confidence
    
    def extract_market_data(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract market data from signal for regime detection"""
        market_data = {}
        
        # Extract price change
        if 'price_change_24h' in signal:
            market_data['price_change_24h'] = signal['price_change_24h']
        
        # Extract volatility
        if 'volatility' in signal:
            market_data['volatility'] = signal['volatility']
        
        # Extract volume data
        if 'volume_24h' in signal:
            market_data['volume_24h'] = signal['volume_24h']
        
        return market_data if market_data else None
    
    def create_trading_command(self, 
                             signal: Dict[str, Any], 
                             position_size: float, 
                             allocation_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create optimized trading command"""
        
        # Determine action (default to BUY for most signals)
        action = signal.get('action', 'BUY')
        if signal.get('signal_type') == 'sell_signal':
            action = 'SELL'
        
        # Create command
        command = {
            "command_id": f"intelligent_{signal.get('strategy', 'unknown')}_{int(time.time())}",
            "action": action,
            "symbol": f"{signal.get('token', 'UNKNOWN')}/SOL",
            "quantity": position_size,
            "confidence": allocation_details.get('composite_score', 0.5),
            "strategy": signal.get('strategy', 'intelligent_trading'),
            "timestamp": time.time(),
            "paper_trading": False,  # Live trading
            "max_slippage": 0.02,
            "priority": "HIGH" if position_size > 0.1 else "MEDIUM",
            "source": "intelligent_trading_manager",
            
            # Capital allocation metadata
            "allocation_details": allocation_details,
            "original_signal": signal,
            "position_size_percentage": position_size,
            "market_regime": allocation_details.get('market_regime', 'unknown'),
            "strategy_performance": allocation_details.get('strategy_multiplier', 1.0)
        }
        
        return command
    
    def process_execution_feedback(self, execution_result: Dict[str, Any]):
        """Process execution feedback to update Capital Allocator"""
        try:
            strategy = execution_result.get('strategy', 'unknown')
            success = execution_result.get('status') == 'SUCCESS'
            profit = execution_result.get('profit', 0.0)
            
            # Update strategy performance in Capital Allocator
            self.capital_allocator.update_strategy_performance(strategy, success, profit)
            
            # Update portfolio exposure (reduce if position closed)
            if execution_result.get('action') == 'SELL':
                position_size = execution_result.get('quantity', 0.0)
                self.capital_allocator.current_exposure = max(
                    0.0, 
                    self.capital_allocator.current_exposure - position_size
                )
            
            logger.info(f"📊 Capital Allocator updated with execution feedback")
            logger.info(f"   Strategy: {strategy}")
            logger.info(f"   Success: {success}")
            logger.info(f"   Profit: ${profit:.6f}")
            
        except Exception as e:
            logger.error(f"❌ Error processing execution feedback: {e}")
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """Get intelligent trading statistics"""
        allocator_stats = self.capital_allocator.get_allocation_stats()
        
        return {
            "signal_processing": self.signal_stats,
            "capital_allocation": allocator_stats,
            "system_status": {
                "running": self.running,
                "total_signals_processed": self.signal_stats['processed_signals'],
                "rejection_rate": self.signal_stats['rejected_signals'] / max(self.signal_stats['total_signals'], 1),
                "average_allocation": self.signal_stats['total_allocated_capital'] / max(self.signal_stats['processed_signals'], 1)
            }
        }
    
    def stop(self):
        """Stop the intelligent trading manager"""
        self.running = False
        logger.info("⏹️ Intelligent Trading Manager stopped")

# Factory function
def create_intelligent_trading_manager() -> IntelligentTradingManager:
    """Create intelligent trading manager instance"""
    return IntelligentTradingManager()

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_intelligent_trading():
        """Test intelligent trading manager"""
        manager = create_intelligent_trading_manager()
        
        # Test signal processing
        test_signal = {
            "signal_type": "governance_alpha",
            "token": "JTO",
            "strategy": "governance_alpha_hunter",
            "confidence_score": 0.85,
            "sentiment_score": 0.88,
            "impact_score": 0.82,
            "price_change_24h": 8.5,
            "volatility": 0.4,
            "dao": "jito",
            "proposal_type": "buyback"
        }
        
        await manager.process_trading_signal(test_signal)
        
        # Test stats
        stats = manager.get_trading_stats()
        print("=== INTELLIGENT TRADING STATS ===")
        for category, data in stats.items():
            print(f"\n{category.upper()}:")
            for key, value in data.items():
                print(f"  {key}: {value}")
    
    asyncio.run(test_intelligent_trading())
