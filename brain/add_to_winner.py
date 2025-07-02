#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Add to Winner System
Scales winning positions based on momentum and performance
"""

import asyncio
import json
import time
import redis
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PositionPerformance:
    symbol: str
    entry_price: float
    current_price: float
    quantity: float
    unrealized_pnl: float
    pnl_percentage: float
    momentum_score: float
    time_held: float
    confidence_score: float

class AddToWinnerSystem:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Add to Winner Configuration
        self.config = {
            'min_profit_threshold': 0.05,  # 5% minimum profit to scale
            'momentum_threshold': 0.7,     # Momentum score threshold
            'max_scale_factor': 2.0,       # Maximum 2x original position
            'scale_increment': 0.25,       # Scale by 25% each time
            'min_time_held': 300,          # 5 minutes minimum hold time
            'max_positions_to_scale': 3,   # Maximum 3 positions scaled simultaneously
            'confidence_threshold': 0.8,   # Minimum confidence for scaling
        }
        
        self.scaled_positions = {}  # Track scaled positions
        
    async def analyze_positions_for_scaling(self) -> List[PositionPerformance]:
        """Analyze current positions for scaling opportunities"""
        try:
            # Get current positions
            position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
            if not position_updates:
                return []
            
            latest_update = json.loads(position_updates[0])
            positions = latest_update.get('positions', {})
            
            performance_list = []
            
            for symbol, position_data in positions.items():
                if position_data.get('quantity', 0) <= 0:
                    continue
                
                # Calculate performance metrics
                entry_price = position_data.get('entry_price', 0)
                current_price = position_data.get('current_price', 0)
                quantity = position_data.get('quantity', 0)
                
                if entry_price <= 0 or current_price <= 0:
                    continue
                
                unrealized_pnl = (current_price - entry_price) * quantity
                pnl_percentage = (current_price - entry_price) / entry_price
                
                # Calculate momentum score
                momentum_score = await self.calculate_momentum_score(symbol, position_data)
                
                # Calculate time held
                entry_time = position_data.get('entry_time', time.time())
                time_held = time.time() - entry_time
                
                # Get confidence score
                confidence_score = position_data.get('confidence', 0.5)
                
                performance = PositionPerformance(
                    symbol=symbol,
                    entry_price=entry_price,
                    current_price=current_price,
                    quantity=quantity,
                    unrealized_pnl=unrealized_pnl,
                    pnl_percentage=pnl_percentage,
                    momentum_score=momentum_score,
                    time_held=time_held,
                    confidence_score=confidence_score
                )
                
                performance_list.append(performance)
            
            return performance_list
            
        except Exception as e:
            logger.error(f"❌ Error analyzing positions: {e}")
            return []
    
    async def calculate_momentum_score(self, symbol: str, position_data: dict) -> float:
        """Calculate momentum score for a position"""
        try:
            # Get recent price data
            price_history = position_data.get('price_history', [])
            if len(price_history) < 3:
                return 0.5  # Neutral momentum
            
            # Calculate price momentum
            recent_prices = price_history[-5:]  # Last 5 price points
            if len(recent_prices) < 2:
                return 0.5
            
            # Simple momentum: (current - average) / average
            current_price = recent_prices[-1]
            avg_price = sum(recent_prices[:-1]) / len(recent_prices[:-1])
            
            momentum = (current_price - avg_price) / avg_price
            
            # Normalize to 0-1 scale
            momentum_score = max(0, min(1, 0.5 + momentum * 2))
            
            return momentum_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating momentum for {symbol}: {e}")
            return 0.5
    
    def should_scale_position(self, performance: PositionPerformance) -> bool:
        """Determine if a position should be scaled up"""
        
        # Check profit threshold
        if performance.pnl_percentage < self.config['min_profit_threshold']:
            return False
        
        # Check momentum threshold
        if performance.momentum_score < self.config['momentum_threshold']:
            return False
        
        # Check minimum time held
        if performance.time_held < self.config['min_time_held']:
            return False
        
        # Check confidence threshold
        if performance.confidence_score < self.config['confidence_threshold']:
            return False
        
        # Check if already scaled to maximum
        current_scale = self.scaled_positions.get(performance.symbol, 1.0)
        if current_scale >= self.config['max_scale_factor']:
            return False
        
        return True
    
    async def execute_position_scaling(self, performance: PositionPerformance) -> bool:
        """Execute scaling of a winning position"""
        try:
            # Calculate scale amount
            current_scale = self.scaled_positions.get(performance.symbol, 1.0)
            new_scale = min(
                current_scale + self.config['scale_increment'],
                self.config['max_scale_factor']
            )
            
            scale_amount = (new_scale - current_scale) * performance.quantity
            
            logger.info(f"🚀 SCALING WINNER: {performance.symbol}")
            logger.info(f"   Current P&L: {performance.pnl_percentage:.2%}")
            logger.info(f"   Momentum: {performance.momentum_score:.2f}")
            logger.info(f"   Scale Amount: {scale_amount:.6f}")
            
            # Create scaling signal
            scaling_signal = {
                'action': 'BUY',
                'symbol': performance.symbol,
                'quantity': scale_amount,
                'confidence': performance.confidence_score,
                'strategy': 'ADD_TO_WINNER',
                'reason': f'Scaling winner: {performance.pnl_percentage:.2%} profit, {performance.momentum_score:.2f} momentum',
                'live_trading': True,
                'paper_trading': False,
                'force_real_mode': True,
                'timestamp': time.time(),
                'signal_id': f'scale_{performance.symbol}_{int(time.time())}',
                'original_position': True,
                'scale_factor': new_scale
            }
            
            # Send scaling signal
            self.redis_client.lpush('overmind:commands', json.dumps(scaling_signal))
            
            # Update scaled positions tracking
            self.scaled_positions[performance.symbol] = new_scale
            
            # Store scaling event
            scaling_event = {
                'timestamp': time.time(),
                'symbol': performance.symbol,
                'action': 'SCALE_UP',
                'scale_factor': new_scale,
                'pnl_percentage': performance.pnl_percentage,
                'momentum_score': performance.momentum_score,
                'scale_amount': scale_amount
            }
            
            self.redis_client.lpush('overmind:scaling_events', json.dumps(scaling_event))
            
            logger.info(f"✅ Scaling signal sent for {performance.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error scaling position {performance.symbol}: {e}")
            return False
    
    async def run_add_to_winner_cycle(self):
        """Main cycle for add to winner system"""
        logger.info("🚀 Starting Add to Winner System")
        
        while True:
            try:
                # Analyze positions for scaling opportunities
                performances = await self.analyze_positions_for_scaling()
                
                if not performances:
                    await asyncio.sleep(30)
                    continue
                
                # Filter positions that should be scaled
                scalable_positions = [p for p in performances if self.should_scale_position(p)]
                
                if scalable_positions:
                    logger.info(f"🎯 Found {len(scalable_positions)} positions ready for scaling")
                    
                    # Sort by performance (best first)
                    scalable_positions.sort(key=lambda x: x.pnl_percentage, reverse=True)
                    
                    # Scale top positions (limited by max_positions_to_scale)
                    positions_to_scale = scalable_positions[:self.config['max_positions_to_scale']]
                    
                    for position in positions_to_scale:
                        await self.execute_position_scaling(position)
                        await asyncio.sleep(2)  # Small delay between scaling operations
                
                # Wait before next cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Error in add to winner cycle: {e}")
                await asyncio.sleep(30)

async def main():
    system = AddToWinnerSystem()
    await system.run_add_to_winner_cycle()

if __name__ == "__main__":
    asyncio.run(main())
