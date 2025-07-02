#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Position Monitor
Real-time position tracking and P&L analysis for Post-Trade Intelligence
"""

import asyncio
import json
import time
import redis
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import os
import sys

# Import advanced features
try:
    from add_to_winner import AddToWinnerSystem
    ADD_TO_WINNER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Add to Winner system not available: {e}")
    ADD_TO_WINNER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PositionMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        self.positions = {}
        self.price_cache = {}
        self.performance_metrics = {
            'total_pnl': 0.0,
            'realized_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0
        }
        
        # Price APIs
        self.helius_api_key = "edbcd361-78a0-4998-bd1e-8d4666722f82"
        self.coingecko_url = "https://api.coingecko.com/api/v3"

        # Initialize Add to Winner system
        self.add_to_winner_enabled = ADD_TO_WINNER_AVAILABLE
        self.add_to_winner = None

        if self.add_to_winner_enabled:
            try:
                self.add_to_winner = AddToWinnerSystem()
                logger.info("📈 Add to Winner system initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Add to Winner: {e}")
                self.add_to_winner_enabled = False
        
    async def load_positions_from_redis(self):
        """Load open positions from Redis execution results"""
        try:
            results = self.redis_client.lrange('overmind:execution_results', 0, -1)
            
            for result_str in results:
                result = json.loads(result_str)
                
                if result.get('status') == 'MEV_PROTECTED_SUCCESS':
                    symbol = result['symbol']
                    
                    if symbol not in self.positions:
                        self.positions[symbol] = {
                            'symbol': symbol,
                            'quantity': 0.0,
                            'avg_entry_price': 0.0,
                            'total_cost': 0.0,
                            'current_price': 0.0,
                            'unrealized_pnl': 0.0,
                            'realized_pnl': 0.0,
                            'entry_time': result.get('timestamp', time.time()),
                            'last_update': time.time(),
                            'trades': []
                        }
                    
                    # Update position
                    pos = self.positions[symbol]
                    trade_quantity = result['quantity']
                    trade_price = result['execution_price']
                    
                    # Calculate new average price
                    old_total_cost = pos['avg_entry_price'] * pos['quantity']
                    new_trade_cost = trade_price * trade_quantity
                    new_total_quantity = pos['quantity'] + trade_quantity
                    
                    if new_total_quantity > 0:
                        pos['avg_entry_price'] = (old_total_cost + new_trade_cost) / new_total_quantity
                        pos['quantity'] = new_total_quantity
                        pos['total_cost'] += new_trade_cost
                    
                    pos['trades'].append({
                        'timestamp': result.get('timestamp', time.time()),
                        'action': result['action'],
                        'quantity': trade_quantity,
                        'price': trade_price,
                        'transaction_id': result['transaction_id']
                    })
                    
            logger.info(f"📊 Loaded {len(self.positions)} positions from Redis")
            
        except Exception as e:
            logger.error(f"❌ Error loading positions: {e}")
    
    async def update_current_prices(self):
        """Update current market prices for all positions"""
        try:
            # Get prices for all symbols
            symbols = list(self.positions.keys())
            
            for symbol in symbols:
                price = await self.get_current_price(symbol)
                if price:
                    self.positions[symbol]['current_price'] = price
                    self.price_cache[symbol] = {
                        'price': price,
                        'timestamp': time.time()
                    }
                    
        except Exception as e:
            logger.error(f"❌ Error updating prices: {e}")
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            # Check cache first (5 second cache)
            if symbol in self.price_cache:
                cache_age = time.time() - self.price_cache[symbol]['timestamp']
                if cache_age < 5:
                    return self.price_cache[symbol]['price']
            
            # CoinGecko mapping
            symbol_map = {
                'SOL': 'solana',
                'BONK': 'bonk',
                'RAY': 'raydium',
                'ORCA': 'orca',
                'USDC': 'usd-coin'
            }
            
            coingecko_id = symbol_map.get(symbol)
            if not coingecko_id:
                return None
                
            url = f"{self.coingecko_url}/simple/price"
            params = {
                'ids': coingecko_id,
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = data.get(coingecko_id, {}).get('usd')
                return float(price) if price else None
                
        except Exception as e:
            logger.error(f"❌ Error fetching price for {symbol}: {e}")
            
        return None
    
    def calculate_position_pnl(self, symbol: str) -> Dict:
        """Calculate P&L for a specific position"""
        if symbol not in self.positions:
            return {}
            
        pos = self.positions[symbol]
        current_price = pos['current_price']
        avg_entry_price = pos['avg_entry_price']
        quantity = pos['quantity']
        
        if current_price == 0 or avg_entry_price == 0:
            return pos
            
        # Calculate unrealized P&L
        current_value = current_price * quantity
        cost_basis = avg_entry_price * quantity
        unrealized_pnl = current_value - cost_basis
        
        # Calculate percentage return
        pnl_percentage = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0
        
        pos['unrealized_pnl'] = unrealized_pnl
        pos['pnl_percentage'] = pnl_percentage
        pos['current_value'] = current_value
        pos['cost_basis'] = cost_basis
        pos['last_update'] = time.time()
        
        return pos
    
    def calculate_portfolio_metrics(self):
        """Calculate overall portfolio performance metrics"""
        total_unrealized_pnl = 0
        total_cost_basis = 0
        total_current_value = 0
        
        for symbol, pos in self.positions.items():
            if pos['quantity'] > 0:
                total_unrealized_pnl += pos.get('unrealized_pnl', 0)
                total_cost_basis += pos.get('cost_basis', 0)
                total_current_value += pos.get('current_value', 0)
        
        self.performance_metrics.update({
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_cost_basis': total_cost_basis,
            'total_current_value': total_current_value,
            'portfolio_return_pct': (total_unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0,
            'total_trades': len([t for pos in self.positions.values() for t in pos.get('trades', [])]),
            'last_update': time.time()
        })
    
    async def publish_position_updates(self):
        """Publish position updates to Redis for other modules"""
        try:
            position_update = {
                'timestamp': time.time(),
                'positions': self.positions,
                'portfolio_metrics': self.performance_metrics,
                'update_type': 'position_monitor'
            }
            
            self.redis_client.lpush('overmind:position_updates', json.dumps(position_update))
            
            # Keep only last 100 updates
            self.redis_client.ltrim('overmind:position_updates', 0, 99)
            
        except Exception as e:
            logger.error(f"❌ Error publishing position updates: {e}")
    
    def print_position_summary(self):
        """Print current position summary"""
        print("\n🔥 THE OVERMIND PROTOCOL - POSITION MONITOR")
        print("=" * 60)
        
        if not self.positions:
            print("📊 No open positions")
            return
            
        total_pnl = 0
        
        for symbol, pos in self.positions.items():
            if pos['quantity'] > 0:
                pnl = pos.get('unrealized_pnl', 0)
                pnl_pct = pos.get('pnl_percentage', 0)
                current_price = pos.get('current_price', 0)
                
                status = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                
                print(f"{status} {symbol}: ${pnl:.6f} ({pnl_pct:+.2f}%) | "
                      f"Price: ${current_price:.6f} | Qty: {pos['quantity']:.4f}")
                
                total_pnl += pnl
        
        print("-" * 60)
        print(f"💰 TOTAL UNREALIZED P&L: ${total_pnl:.6f}")
        print(f"📊 Portfolio Return: {self.performance_metrics.get('portfolio_return_pct', 0):.2f}%")
        print(f"🔄 Last Update: {datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')}")
    
    async def monitor_positions(self):
        """Main monitoring loop"""
        logger.info("🚀 Starting Position Monitor...")
        
        # Load initial positions
        await self.load_positions_from_redis()
        
        while True:
            try:
                # Update prices
                await self.update_current_prices()
                
                # Calculate P&L for all positions
                for symbol in self.positions:
                    self.calculate_position_pnl(symbol)
                
                # Calculate portfolio metrics
                self.calculate_portfolio_metrics()

                # Check for Add to Winner opportunities
                if self.add_to_winner_enabled and self.add_to_winner:
                    await self._check_add_to_winner_opportunities()

                # Publish updates
                await self.publish_position_updates()

                # Print summary
                self.print_position_summary()
                
                # Wait 10 seconds before next update
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(5)

    async def _check_add_to_winner_opportunities(self):
        """Check for Add to Winner scaling opportunities"""
        try:
            if not self.add_to_winner:
                return

            # Analyze current positions for scaling
            performances = await self.add_to_winner.analyze_positions_for_scaling()

            if not performances:
                return

            # Check each position for scaling opportunity
            for performance in performances:
                if self.add_to_winner.should_scale_position(performance):
                    logger.info(f"📈 Add to Winner opportunity detected for {performance.symbol}")
                    logger.info(f"   P&L: {performance.pnl_percentage:.2%}, Momentum: {performance.momentum_score:.2f}")

                    # Execute scaling
                    success = await self.add_to_winner.execute_position_scaling(performance)

                    if success:
                        logger.info(f"✅ Position scaled successfully: {performance.symbol}")
                    else:
                        logger.warning(f"⚠️ Failed to scale position: {performance.symbol}")

        except Exception as e:
            logger.error(f"❌ Error checking Add to Winner opportunities: {e}")

async def main():
    monitor = PositionMonitor()
    await monitor.monitor_positions()

if __name__ == "__main__":
    asyncio.run(main())
