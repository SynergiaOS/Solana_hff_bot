#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Drawdown Protection System
Advanced risk management and capital protection
"""

import asyncio
import json
import time
import redis
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DrawdownMetrics:
    current_portfolio_value: float
    daily_high: float
    daily_low: float
    max_drawdown: float
    current_drawdown: float
    daily_pnl: float
    daily_pnl_percentage: float
    risk_level: str

class DrawdownGuard:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Drawdown Protection Configuration
        self.config = {
            'max_daily_drawdown': 0.10,      # 10% maximum daily drawdown
            'emergency_stop_drawdown': 0.15,  # 15% emergency stop
            'warning_drawdown': 0.05,         # 5% warning level
            'position_reduction_threshold': 0.08,  # 8% reduce positions
            'recovery_threshold': 0.03,       # 3% recovery before resuming
            'max_position_size_during_drawdown': 0.02,  # 2% max position during drawdown
            'monitoring_interval': 30,        # 30 seconds monitoring
        }
        
        self.daily_high = 0.0
        self.emergency_stop_triggered = False
        self.drawdown_mode = False
        
    async def get_current_portfolio_metrics(self) -> Optional[DrawdownMetrics]:
        """Get current portfolio metrics for drawdown analysis"""
        try:
            # Get latest position update
            position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
            if not position_updates:
                return None
            
            latest_update = json.loads(position_updates[0])
            portfolio_metrics = latest_update.get('portfolio_metrics', {})
            
            current_value = portfolio_metrics.get('total_portfolio_value', 0)
            daily_pnl = portfolio_metrics.get('daily_pnl', 0)
            daily_pnl_pct = portfolio_metrics.get('daily_pnl_percentage', 0)
            
            # Update daily high
            if current_value > self.daily_high:
                self.daily_high = current_value
                # Store new daily high
                self.redis_client.set('overmind:daily_high', self.daily_high)
            else:
                # Load daily high from Redis if not set
                stored_high = self.redis_client.get('overmind:daily_high')
                if stored_high and self.daily_high == 0:
                    self.daily_high = float(stored_high)
            
            # Calculate drawdown
            if self.daily_high > 0:
                current_drawdown = (self.daily_high - current_value) / self.daily_high
                max_drawdown = current_drawdown  # Simplified for now
            else:
                current_drawdown = 0
                max_drawdown = 0
            
            # Determine risk level
            if current_drawdown >= self.config['emergency_stop_drawdown']:
                risk_level = "EMERGENCY"
            elif current_drawdown >= self.config['position_reduction_threshold']:
                risk_level = "HIGH"
            elif current_drawdown >= self.config['warning_drawdown']:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return DrawdownMetrics(
                current_portfolio_value=current_value,
                daily_high=self.daily_high,
                daily_low=min(current_value, portfolio_metrics.get('daily_low', current_value)),
                max_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                daily_pnl=daily_pnl,
                daily_pnl_percentage=daily_pnl_pct,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting portfolio metrics: {e}")
            return None
    
    async def trigger_emergency_stop(self, metrics: DrawdownMetrics):
        """Trigger emergency stop procedures"""
        if self.emergency_stop_triggered:
            return
        
        logger.critical("🚨 EMERGENCY STOP TRIGGERED!")
        logger.critical(f"   Drawdown: {metrics.current_drawdown:.2%}")
        logger.critical(f"   Portfolio Value: ${metrics.current_portfolio_value:.2f}")
        
        # Set emergency stop flag
        self.emergency_stop_triggered = True
        self.redis_client.set('overmind:emergency_stop', 'true')
        
        # Close all positions
        await self.close_all_positions("EMERGENCY_STOP")
        
        # Store emergency event
        emergency_event = {
            'timestamp': time.time(),
            'event': 'EMERGENCY_STOP',
            'trigger': 'DRAWDOWN_PROTECTION',
            'drawdown': metrics.current_drawdown,
            'portfolio_value': metrics.current_portfolio_value,
            'daily_pnl': metrics.daily_pnl
        }
        
        self.redis_client.lpush('overmind:emergency_events', json.dumps(emergency_event))
        
        logger.critical("🛑 ALL POSITIONS CLOSED - EMERGENCY STOP ACTIVE")
    
    async def reduce_position_sizes(self, metrics: DrawdownMetrics):
        """Reduce position sizes during high drawdown"""
        logger.warning("⚠️ REDUCING POSITION SIZES - HIGH DRAWDOWN DETECTED")
        logger.warning(f"   Current Drawdown: {metrics.current_drawdown:.2%}")
        
        # Set drawdown mode
        self.drawdown_mode = True
        self.redis_client.set('overmind:drawdown_mode', 'true')
        self.redis_client.set('overmind:max_position_size', self.config['max_position_size_during_drawdown'])
        
        # Get current positions and reduce them
        position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
        if position_updates:
            latest_update = json.loads(position_updates[0])
            positions = latest_update.get('positions', {})
            
            for symbol, position_data in positions.items():
                quantity = position_data.get('quantity', 0)
                if quantity > 0:
                    # Reduce position by 50%
                    reduction_amount = quantity * 0.5
                    
                    reduction_signal = {
                        'action': 'SELL',
                        'symbol': symbol,
                        'quantity': reduction_amount,
                        'confidence': 0.9,
                        'strategy': 'DRAWDOWN_PROTECTION',
                        'reason': f'Reducing position due to {metrics.current_drawdown:.2%} drawdown',
                        'live_trading': True,
                        'paper_trading': False,
                        'force_real_mode': True,
                        'timestamp': time.time(),
                        'signal_id': f'drawdown_reduce_{symbol}_{int(time.time())}'
                    }
                    
                    self.redis_client.lpush('overmind:commands', json.dumps(reduction_signal))
                    logger.warning(f"📉 Reducing {symbol} position by {reduction_amount:.6f}")
        
        # Store drawdown event
        drawdown_event = {
            'timestamp': time.time(),
            'event': 'POSITION_REDUCTION',
            'trigger': 'DRAWDOWN_PROTECTION',
            'drawdown': metrics.current_drawdown,
            'action': 'REDUCE_POSITIONS_50_PERCENT'
        }
        
        self.redis_client.lpush('overmind:drawdown_events', json.dumps(drawdown_event))
    
    async def close_all_positions(self, reason: str):
        """Close all open positions"""
        try:
            position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
            if not position_updates:
                return
            
            latest_update = json.loads(position_updates[0])
            positions = latest_update.get('positions', {})
            
            for symbol, position_data in positions.items():
                quantity = position_data.get('quantity', 0)
                if quantity > 0:
                    close_signal = {
                        'action': 'SELL',
                        'symbol': symbol,
                        'quantity': quantity,
                        'confidence': 0.95,
                        'strategy': 'EMERGENCY_CLOSE',
                        'reason': reason,
                        'live_trading': True,
                        'paper_trading': False,
                        'force_real_mode': True,
                        'timestamp': time.time(),
                        'signal_id': f'emergency_close_{symbol}_{int(time.time())}'
                    }
                    
                    self.redis_client.lpush('overmind:commands', json.dumps(close_signal))
                    logger.critical(f"🚨 EMERGENCY CLOSE: {symbol} - {quantity:.6f}")
            
        except Exception as e:
            logger.error(f"❌ Error closing positions: {e}")
    
    async def check_recovery_conditions(self, metrics: DrawdownMetrics):
        """Check if system can recover from drawdown mode"""
        if not self.drawdown_mode:
            return
        
        if metrics.current_drawdown <= self.config['recovery_threshold']:
            logger.info("✅ RECOVERY DETECTED - Exiting drawdown mode")
            
            self.drawdown_mode = False
            self.redis_client.delete('overmind:drawdown_mode')
            self.redis_client.delete('overmind:max_position_size')
            
            # Store recovery event
            recovery_event = {
                'timestamp': time.time(),
                'event': 'DRAWDOWN_RECOVERY',
                'drawdown': metrics.current_drawdown,
                'portfolio_value': metrics.current_portfolio_value
            }
            
            self.redis_client.lpush('overmind:drawdown_events', json.dumps(recovery_event))
    
    async def run_drawdown_protection(self):
        """Main drawdown protection monitoring loop"""
        logger.info("🛡️ Starting Drawdown Protection System")
        
        while True:
            try:
                # Get current metrics
                metrics = await self.get_current_portfolio_metrics()
                
                if not metrics:
                    await asyncio.sleep(self.config['monitoring_interval'])
                    continue
                
                # Log current status
                logger.info(f"📊 Portfolio: ${metrics.current_portfolio_value:.2f} | "
                           f"Drawdown: {metrics.current_drawdown:.2%} | "
                           f"Risk: {metrics.risk_level}")
                
                # Check emergency stop condition
                if (metrics.current_drawdown >= self.config['emergency_stop_drawdown'] 
                    and not self.emergency_stop_triggered):
                    await self.trigger_emergency_stop(metrics)
                
                # Check position reduction condition
                elif (metrics.current_drawdown >= self.config['position_reduction_threshold'] 
                      and not self.drawdown_mode):
                    await self.reduce_position_sizes(metrics)
                
                # Check recovery conditions
                await self.check_recovery_conditions(metrics)
                
                # Store metrics
                metrics_data = {
                    'timestamp': time.time(),
                    'portfolio_value': metrics.current_portfolio_value,
                    'drawdown': metrics.current_drawdown,
                    'daily_pnl': metrics.daily_pnl,
                    'risk_level': metrics.risk_level
                }
                
                self.redis_client.lpush('overmind:drawdown_metrics', json.dumps(metrics_data))
                self.redis_client.ltrim('overmind:drawdown_metrics', 0, 999)  # Keep last 1000
                
                await asyncio.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                logger.error(f"❌ Error in drawdown protection: {e}")
                await asyncio.sleep(30)

async def main():
    guard = DrawdownGuard()
    await guard.run_drawdown_protection()

if __name__ == "__main__":
    asyncio.run(main())
