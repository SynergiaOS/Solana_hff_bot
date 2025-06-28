#!/usr/bin/env python3
"""
Historical Backtesting Framework
Test trading strategies on historical data for THE OVERMIND PROTOCOL
"""

import asyncio
import logging
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
import numpy as np

try:
    from .sol_momentum_strategy import SOLMomentumStrategy, PriceData, TradingSignal
    from .paper_trading_engine import PaperTradingEngine, OrderSide, OrderType
    from .risk_management import RiskManager
except ImportError:
    # Direct import for testing
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from sol_momentum_strategy import SOLMomentumStrategy, PriceData, TradingSignal
    from paper_trading_engine import PaperTradingEngine, OrderSide, OrderType
    from risk_management import RiskManager

logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """Results from backtesting"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    profitable_trades: int
    avg_trade_return: float
    volatility: float
    calmar_ratio: float
    trade_history: List[Dict[str, Any]]
    daily_returns: List[float]
    equity_curve: List[Tuple[datetime, float]]

class HistoricalDataGenerator:
    """
    Generate realistic historical price data for backtesting
    In production, this would fetch real data from Helius/QuickNode APIs
    """
    
    def __init__(self):
        self.base_price = 100.0
        self.daily_volatility = 0.03  # 3% daily volatility
        self.trend_strength = 0.0001  # Small upward trend
        
    def generate_price_series(self, start_date: datetime, end_date: datetime, interval_minutes: int = 60) -> List[PriceData]:
        """Generate realistic price series with trends and volatility"""
        
        # Calculate number of data points
        total_minutes = int((end_date - start_date).total_seconds() / 60)
        num_points = total_minutes // interval_minutes
        
        prices = []
        current_price = self.base_price
        current_time = start_date
        
        # Generate random walk with trend
        np.random.seed(42)  # For reproducible results
        
        for i in range(num_points):
            # Random price movement
            random_change = np.random.normal(0, self.daily_volatility / 24)  # Hourly volatility
            trend_change = self.trend_strength
            
            # Add some market cycles (simplified)
            cycle_factor = np.sin(i / 100) * 0.001  # Long-term cycle
            noise_factor = np.random.normal(0, 0.0005)  # Market noise
            
            price_change = random_change + trend_change + cycle_factor + noise_factor
            current_price *= (1 + price_change)
            
            # Generate volume (correlated with volatility)
            base_volume = 50000000  # $50M base volume
            volume_multiplier = 1 + abs(price_change) * 10  # Higher volume on big moves
            volume = base_volume * volume_multiplier * (0.8 + np.random.random() * 0.4)
            
            price_data = PriceData(
                price=current_price,
                timestamp=current_time,
                volume=volume,
                slot=i
            )
            
            prices.append(price_data)
            current_time += timedelta(minutes=interval_minutes)
        
        logger.info(f"📊 Generated {len(prices)} price points from {start_date} to {end_date}")
        logger.info(f"   Price range: ${min(p.price for p in prices):.2f} - ${max(p.price for p in prices):.2f}")
        
        return prices

class BacktestingEngine:
    """
    Backtesting engine for trading strategies
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.data_generator = HistoricalDataGenerator()
        
    async def backtest_strategy(self,
                              strategy_name: str,
                              start_date: datetime,
                              end_date: datetime,
                              helius_api_key: str,
                              quicknode_url: Optional[str] = None) -> BacktestResult:
        """
        Run backtest for SOL Momentum strategy
        """
        logger.info(f"🔄 Starting backtest: {strategy_name}")
        logger.info(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"   Initial Balance: ${self.initial_balance:,.2f}")
        
        # Generate historical data
        historical_data = self.data_generator.generate_price_series(start_date, end_date, interval_minutes=60)
        
        # Initialize components
        strategy = SOLMomentumStrategy(helius_api_key, quicknode_url)
        paper_engine = PaperTradingEngine(self.initial_balance)
        risk_manager = RiskManager()
        
        # Track results
        trade_history = []
        daily_returns = []
        equity_curve = []
        
        # Process each data point
        current_position = None
        last_equity = self.initial_balance
        
        for i, price_data in enumerate(historical_data):
            try:
                # Add price data to strategy
                strategy.price_history.append(price_data)
                if len(strategy.price_history) > strategy.max_history:
                    strategy.price_history = strategy.price_history[-strategy.max_history:]
                
                # Generate signal (only if we have enough history)
                if len(strategy.price_history) >= strategy.short_ma_period:
                    signal = strategy.generate_signal()
                    
                    if signal and signal.confidence >= 0.6:  # Minimum confidence threshold
                        
                        # Execute trades based on signal
                        if signal.signal_type.value == "BUY" and not current_position:
                            # Calculate position size using risk manager
                            portfolio_value = paper_engine.get_portfolio_value()
                            quantity, risk_details = risk_manager.calculate_position_size(
                                symbol="SOL",
                                entry_price=signal.price,
                                portfolio_value=portfolio_value,
                                confidence=signal.confidence,
                                volatility=0.03
                            )
                            
                            # Place buy order
                            try:
                                order_id = await paper_engine.place_order(
                                    symbol="SOL",
                                    side=OrderSide.BUY,
                                    quantity=quantity,
                                    order_type=OrderType.MARKET,
                                    strategy_id=strategy_name
                                )
                                
                                current_position = {
                                    "entry_price": signal.price,
                                    "quantity": quantity,
                                    "entry_time": price_data.timestamp,
                                    "order_id": order_id
                                }
                                
                                trade_history.append({
                                    "timestamp": price_data.timestamp,
                                    "action": "BUY",
                                    "price": signal.price,
                                    "quantity": quantity,
                                    "confidence": signal.confidence,
                                    "portfolio_value": portfolio_value
                                })
                                
                            except Exception as e:
                                logger.debug(f"Failed to place BUY order: {e}")
                        
                        elif signal.signal_type.value == "SELL" and current_position:
                            # Place sell order
                            try:
                                order_id = await paper_engine.place_order(
                                    symbol="SOL",
                                    side=OrderSide.SELL,
                                    quantity=current_position["quantity"],
                                    order_type=OrderType.MARKET,
                                    strategy_id=strategy_name
                                )
                                
                                # Calculate trade return
                                trade_return = (signal.price - current_position["entry_price"]) / current_position["entry_price"]
                                
                                trade_history.append({
                                    "timestamp": price_data.timestamp,
                                    "action": "SELL",
                                    "price": signal.price,
                                    "quantity": current_position["quantity"],
                                    "confidence": signal.confidence,
                                    "trade_return": trade_return,
                                    "hold_time": (price_data.timestamp - current_position["entry_time"]).total_seconds() / 3600  # hours
                                })
                                
                                current_position = None
                                
                            except Exception as e:
                                logger.debug(f"Failed to place SELL order: {e}")
                
                # Update portfolio values and track equity curve
                paper_engine.update_positions()
                current_equity = paper_engine.get_portfolio_value()
                
                # Calculate daily returns (every 24 hours)
                if i > 0 and i % 24 == 0:  # Every 24 hours
                    daily_return = (current_equity - last_equity) / last_equity
                    daily_returns.append(daily_return)
                    last_equity = current_equity
                
                # Track equity curve (every 6 hours for reasonable granularity)
                if i % 6 == 0:
                    equity_curve.append((price_data.timestamp, current_equity))
                
            except Exception as e:
                logger.error(f"Error processing data point {i}: {e}")
                continue
        
        # Calculate final metrics
        final_balance = paper_engine.get_portfolio_value()
        total_return = final_balance - self.initial_balance
        total_return_pct = (total_return / self.initial_balance) * 100
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(
            daily_returns, equity_curve, trade_history, self.initial_balance, final_balance
        )
        
        result = BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.initial_balance,
            final_balance=final_balance,
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=metrics["max_drawdown"],
            sharpe_ratio=metrics["sharpe_ratio"],
            win_rate=metrics["win_rate"],
            total_trades=metrics["total_trades"],
            profitable_trades=metrics["profitable_trades"],
            avg_trade_return=metrics["avg_trade_return"],
            volatility=metrics["volatility"],
            calmar_ratio=metrics["calmar_ratio"],
            trade_history=trade_history,
            daily_returns=daily_returns,
            equity_curve=equity_curve
        )
        
        logger.info(f"✅ Backtest completed!")
        logger.info(f"   Final Balance: ${final_balance:,.2f}")
        logger.info(f"   Total Return: {total_return_pct:.2f}%")
        logger.info(f"   Total Trades: {metrics['total_trades']}")
        logger.info(f"   Win Rate: {metrics['win_rate']:.1f}%")
        logger.info(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        
        return result
    
    def _calculate_performance_metrics(self, daily_returns: List[float], equity_curve: List[Tuple[datetime, float]], 
                                     trade_history: List[Dict[str, Any]], initial_balance: float, final_balance: float) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        
        # Trade statistics
        buy_trades = [t for t in trade_history if t["action"] == "BUY"]
        sell_trades = [t for t in trade_history if t["action"] == "SELL"]
        total_trades = len(sell_trades)  # Complete round trips
        
        if total_trades > 0:
            trade_returns = [t.get("trade_return", 0) for t in sell_trades if "trade_return" in t]
            profitable_trades = len([r for r in trade_returns if r > 0])
            win_rate = (profitable_trades / total_trades) * 100
            avg_trade_return = statistics.mean(trade_returns) if trade_returns else 0
        else:
            profitable_trades = 0
            win_rate = 0
            avg_trade_return = 0
        
        # Volatility and Sharpe ratio
        if len(daily_returns) > 1:
            volatility = statistics.stdev(daily_returns) * (252 ** 0.5)  # Annualized
            avg_daily_return = statistics.mean(daily_returns)
            sharpe_ratio = (avg_daily_return * 252) / volatility if volatility > 0 else 0
        else:
            volatility = 0
            sharpe_ratio = 0
        
        # Maximum drawdown
        max_drawdown = 0
        peak = initial_balance
        for _, equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calmar ratio
        total_return_annualized = ((final_balance / initial_balance) ** (365 / len(equity_curve))) - 1 if len(equity_curve) > 0 else 0
        calmar_ratio = total_return_annualized / max_drawdown if max_drawdown > 0 else 0
        
        return {
            "total_trades": total_trades,
            "profitable_trades": profitable_trades,
            "win_rate": win_rate,
            "avg_trade_return": avg_trade_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "calmar_ratio": calmar_ratio
        }

# Test function
async def test_backtesting_framework():
    """Test the backtesting framework"""
    print("🧪 Testing Backtesting Framework")
    print("=" * 50)
    
    # Load environment
    import os
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    helius_api_key = os.getenv('HELIUS_API_KEY')
    if not helius_api_key:
        print("❌ Helius API key not configured")
        return False
    
    try:
        # Initialize backtesting engine
        engine = BacktestingEngine(initial_balance=10000.0)
        
        # Define test period (30 days for quick test)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Run backtest
        result = await engine.backtest_strategy(
            strategy_name="SOL_Momentum_Test",
            start_date=start_date,
            end_date=end_date,
            helius_api_key=helius_api_key
        )
        
        # Display results
        print(f"\n📊 Backtest Results:")
        print(f"   Strategy: {result.strategy_name}")
        print(f"   Period: {result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}")
        print(f"   Initial Balance: ${result.initial_balance:,.2f}")
        print(f"   Final Balance: ${result.final_balance:,.2f}")
        print(f"   Total Return: {result.total_return_pct:.2f}%")
        print(f"   Max Drawdown: {result.max_drawdown*100:.2f}%")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   Total Trades: {result.total_trades}")
        print(f"   Win Rate: {result.win_rate:.1f}%")
        print(f"   Volatility: {result.volatility*100:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Backtesting test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_backtesting_framework())
