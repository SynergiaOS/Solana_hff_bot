#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Advanced Analytics Engine
Deep performance analysis and insights
"""

import asyncio
import json
import time
import redis
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    total_trades: int
    profitable_trades: int
    losing_trades: int

@dataclass
class StrategyAnalysis:
    strategy_name: str
    total_trades: int
    win_rate: float
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    best_trade: float
    worst_trade: float

class AnalyticsEngine:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
    async def get_all_trades(self) -> List[Dict]:
        """Get all historical trades"""
        try:
            results = self.redis_client.lrange('overmind:execution_results', 0, -1)
            trades = []
            
            for result_str in results:
                result = json.loads(result_str)
                if result.get('status') == 'SUCCESS':
                    trades.append({
                        'timestamp': result.get('timestamp', time.time()),
                        'symbol': result.get('symbol', ''),
                        'action': result.get('action', ''),
                        'quantity': result.get('quantity', 0),
                        'price': result.get('execution_price', 0),
                        'pnl': result.get('estimated_profit', 0),
                        'strategy': result.get('strategy', 'UNKNOWN'),
                        'confidence': result.get('confidence', 0.5)
                    })
            
            return sorted(trades, key=lambda x: x['timestamp'])
            
        except Exception as e:
            logger.error(f"❌ Error getting trades: {e}")
            return []
    
    async def calculate_performance_metrics(self, trades: List[Dict]) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # Extract P&L values
        pnl_values = [trade['pnl'] for trade in trades]
        
        # Basic metrics
        total_trades = len(trades)
        profitable_trades = len([pnl for pnl in pnl_values if pnl > 0])
        losing_trades = len([pnl for pnl in pnl_values if pnl < 0])
        
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        # Return metrics
        total_return = sum(pnl_values)
        avg_win = np.mean([pnl for pnl in pnl_values if pnl > 0]) if profitable_trades > 0 else 0
        avg_loss = np.mean([pnl for pnl in pnl_values if pnl < 0]) if losing_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum([pnl for pnl in pnl_values if pnl > 0])
        gross_loss = abs(sum([pnl for pnl in pnl_values if pnl < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        if len(pnl_values) > 1:
            returns_std = np.std(pnl_values)
            avg_return = np.mean(pnl_values)
            sharpe_ratio = avg_return / returns_std if returns_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown calculation
        cumulative_pnl = np.cumsum(pnl_values)
        running_max = np.maximum.accumulate(cumulative_pnl)
        drawdown = (cumulative_pnl - running_max) / running_max
        max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        
        return PerformanceMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            losing_trades=losing_trades
        )
    
    async def analyze_strategies(self, trades: List[Dict]) -> List[StrategyAnalysis]:
        """Analyze performance by strategy"""
        strategy_groups = {}
        
        # Group trades by strategy
        for trade in trades:
            strategy = trade['strategy']
            if strategy not in strategy_groups:
                strategy_groups[strategy] = []
            strategy_groups[strategy].append(trade)
        
        analyses = []
        
        for strategy_name, strategy_trades in strategy_groups.items():
            if len(strategy_trades) == 0:
                continue
            
            pnl_values = [trade['pnl'] for trade in strategy_trades]
            
            total_trades = len(strategy_trades)
            profitable_trades = len([pnl for pnl in pnl_values if pnl > 0])
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            
            avg_return = np.mean(pnl_values)
            
            # Sharpe ratio
            if len(pnl_values) > 1:
                returns_std = np.std(pnl_values)
                sharpe_ratio = avg_return / returns_std if returns_std > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Max drawdown
            cumulative_pnl = np.cumsum(pnl_values)
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdown = (cumulative_pnl - running_max) / running_max
            max_drawdown = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
            
            # Profit factor
            gross_profit = sum([pnl for pnl in pnl_values if pnl > 0])
            gross_loss = abs(sum([pnl for pnl in pnl_values if pnl < 0]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            best_trade = max(pnl_values) if pnl_values else 0
            worst_trade = min(pnl_values) if pnl_values else 0
            
            analysis = StrategyAnalysis(
                strategy_name=strategy_name,
                total_trades=total_trades,
                win_rate=win_rate,
                avg_return=avg_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                profit_factor=profit_factor,
                best_trade=best_trade,
                worst_trade=worst_trade
            )
            
            analyses.append(analysis)
        
        return sorted(analyses, key=lambda x: x.sharpe_ratio, reverse=True)
    
    async def get_hourly_performance(self, trades: List[Dict]) -> Dict:
        """Analyze performance by hour of day"""
        hourly_pnl = {hour: [] for hour in range(24)}
        
        for trade in trades:
            hour = datetime.fromtimestamp(trade['timestamp']).hour
            hourly_pnl[hour].append(trade['pnl'])
        
        hourly_stats = {}
        for hour, pnl_list in hourly_pnl.items():
            if pnl_list:
                hourly_stats[hour] = {
                    'avg_pnl': np.mean(pnl_list),
                    'total_pnl': sum(pnl_list),
                    'trade_count': len(pnl_list),
                    'win_rate': len([pnl for pnl in pnl_list if pnl > 0]) / len(pnl_list)
                }
            else:
                hourly_stats[hour] = {
                    'avg_pnl': 0,
                    'total_pnl': 0,
                    'trade_count': 0,
                    'win_rate': 0
                }
        
        return hourly_stats
    
    async def get_symbol_performance(self, trades: List[Dict]) -> Dict:
        """Analyze performance by trading symbol"""
        symbol_groups = {}
        
        for trade in trades:
            symbol = trade['symbol']
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(trade)
        
        symbol_stats = {}
        for symbol, symbol_trades in symbol_groups.items():
            pnl_values = [trade['pnl'] for trade in symbol_trades]
            
            symbol_stats[symbol] = {
                'total_trades': len(symbol_trades),
                'total_pnl': sum(pnl_values),
                'avg_pnl': np.mean(pnl_values),
                'win_rate': len([pnl for pnl in pnl_values if pnl > 0]) / len(pnl_values),
                'best_trade': max(pnl_values),
                'worst_trade': min(pnl_values)
            }
        
        return symbol_stats
    
    async def generate_insights(self, metrics: PerformanceMetrics, strategies: List[StrategyAnalysis]) -> List[str]:
        """Generate actionable insights from analysis"""
        insights = []
        
        # Overall performance insights
        if metrics.sharpe_ratio > 2.0:
            insights.append("🎯 Excellent risk-adjusted returns - consider increasing position sizes")
        elif metrics.sharpe_ratio < 0.5:
            insights.append("⚠️ Poor risk-adjusted returns - review strategy parameters")
        
        if metrics.win_rate > 0.6:
            insights.append("✅ High win rate indicates good entry timing")
        elif metrics.win_rate < 0.4:
            insights.append("❌ Low win rate - consider tighter entry criteria")
        
        if metrics.max_drawdown > 0.15:
            insights.append("🛡️ High drawdown detected - strengthen risk management")
        
        # Strategy-specific insights
        if strategies:
            best_strategy = strategies[0]
            worst_strategy = strategies[-1]
            
            insights.append(f"🏆 Best performing strategy: {best_strategy.strategy_name} (Sharpe: {best_strategy.sharpe_ratio:.2f})")
            
            if len(strategies) > 1:
                insights.append(f"📉 Underperforming strategy: {worst_strategy.strategy_name} - consider optimization")
        
        # Profit factor insights
        if metrics.profit_factor > 2.0:
            insights.append("💰 Strong profit factor - winners significantly outweigh losers")
        elif metrics.profit_factor < 1.0:
            insights.append("💸 Negative profit factor - losses exceed gains")
        
        return insights
    
    async def store_analytics_results(self, metrics: PerformanceMetrics, strategies: List[StrategyAnalysis], insights: List[str]):
        """Store analytics results in Redis"""
        try:
            analytics_data = {
                'timestamp': time.time(),
                'performance_metrics': {
                    'total_return': metrics.total_return,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'max_drawdown': metrics.max_drawdown,
                    'win_rate': metrics.win_rate,
                    'profit_factor': metrics.profit_factor,
                    'total_trades': metrics.total_trades
                },
                'strategy_analysis': [
                    {
                        'name': s.strategy_name,
                        'trades': s.total_trades,
                        'win_rate': s.win_rate,
                        'sharpe_ratio': s.sharpe_ratio,
                        'avg_return': s.avg_return
                    } for s in strategies
                ],
                'insights': insights
            }
            
            self.redis_client.lpush('overmind:analytics_results', json.dumps(analytics_data))
            self.redis_client.ltrim('overmind:analytics_results', 0, 99)  # Keep last 100
            
            logger.info("📊 Analytics results stored")
            
        except Exception as e:
            logger.error(f"❌ Error storing analytics: {e}")
    
    async def run_analytics_cycle(self):
        """Main analytics cycle"""
        logger.info("📊 Starting Analytics Engine")
        
        while True:
            try:
                # Get all trades
                trades = await self.get_all_trades()
                
                if len(trades) < 5:  # Need minimum trades for meaningful analysis
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                # Calculate performance metrics
                metrics = await self.calculate_performance_metrics(trades)
                
                # Analyze strategies
                strategies = await self.analyze_strategies(trades)
                
                # Generate insights
                insights = await self.generate_insights(metrics, strategies)
                
                # Store results
                await self.store_analytics_results(metrics, strategies, insights)
                
                # Log summary
                logger.info(f"📈 Analytics Update:")
                logger.info(f"   Total Return: ${metrics.total_return:.6f}")
                logger.info(f"   Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
                logger.info(f"   Win Rate: {metrics.win_rate:.2%}")
                logger.info(f"   Total Trades: {metrics.total_trades}")
                
                for insight in insights[:3]:  # Log top 3 insights
                    logger.info(f"   💡 {insight}")
                
                await asyncio.sleep(600)  # Run every 10 minutes
                
            except Exception as e:
                logger.error(f"❌ Error in analytics cycle: {e}")
                await asyncio.sleep(300)

async def main():
    engine = AnalyticsEngine()
    await engine.run_analytics_cycle()

if __name__ == "__main__":
    asyncio.run(main())
