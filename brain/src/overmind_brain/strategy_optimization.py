#!/usr/bin/env python3
"""
Strategy Optimization
Optimize trading strategy parameters using backtesting results
"""

import asyncio
import logging
import itertools
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import statistics
import json

try:
    from .backtesting_framework import BacktestingEngine, HistoricalDataGenerator
    from .sol_momentum_strategy import SOLMomentumStrategy, PriceData
    from .paper_trading_engine import PaperTradingEngine, OrderSide, OrderType
    from .risk_management import RiskManager
    from .performance_analytics import PerformanceAnalyzer
except ImportError:
    # Direct import for testing
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from backtesting_framework import BacktestingEngine, HistoricalDataGenerator
    from sol_momentum_strategy import SOLMomentumStrategy, PriceData
    from paper_trading_engine import PaperTradingEngine, OrderSide, OrderType
    from risk_management import RiskManager
    from performance_analytics import PerformanceAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class OptimizationParameter:
    """Parameter to optimize"""
    name: str
    min_value: float
    max_value: float
    step: float
    current_value: float

@dataclass
class OptimizationResult:
    """Result of parameter optimization"""
    parameters: Dict[str, float]
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    score: float  # Composite optimization score

class StrategyOptimizer:
    """
    Optimize trading strategy parameters using grid search and backtesting
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.data_generator = HistoricalDataGenerator()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Optimization settings
        self.max_iterations = 50  # Limit for performance
        self.optimization_metric = "sharpe_ratio"  # Primary optimization target
        
    def define_optimization_parameters(self) -> List[OptimizationParameter]:
        """Define parameters to optimize for SOL Momentum strategy"""
        
        return [
            OptimizationParameter(
                name="short_ma_period",
                min_value=3,
                max_value=10,
                step=1,
                current_value=5
            ),
            OptimizationParameter(
                name="long_ma_period", 
                min_value=15,
                max_value=30,
                step=5,
                current_value=20
            ),
            OptimizationParameter(
                name="rsi_period",
                min_value=10,
                max_value=20,
                step=2,
                current_value=14
            ),
            OptimizationParameter(
                name="volume_threshold",
                min_value=1.2,
                max_value=2.0,
                step=0.2,
                current_value=1.5
            ),
            OptimizationParameter(
                name="confidence_threshold",
                min_value=0.5,
                max_value=0.8,
                step=0.1,
                current_value=0.6
            )
        ]
    
    def generate_parameter_combinations(self, parameters: List[OptimizationParameter]) -> List[Dict[str, float]]:
        """Generate all parameter combinations for grid search"""
        
        # Create ranges for each parameter
        param_ranges = {}
        for param in parameters:
            values = []
            current = param.min_value
            while current <= param.max_value:
                values.append(current)
                current += param.step
            param_ranges[param.name] = values
        
        # Generate all combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        combinations = []
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            # Ensure long_ma > short_ma
            if param_dict["long_ma_period"] > param_dict["short_ma_period"]:
                combinations.append(param_dict)
        
        # Limit combinations for performance
        if len(combinations) > self.max_iterations:
            # Sample evenly distributed combinations
            step = len(combinations) // self.max_iterations
            combinations = combinations[::step][:self.max_iterations]
        
        logger.info(f"🔍 Generated {len(combinations)} parameter combinations for optimization")
        return combinations
    
    async def optimize_strategy(self,
                              start_date: datetime,
                              end_date: datetime,
                              helius_api_key: str,
                              quicknode_url: Optional[str] = None) -> Tuple[Dict[str, float], List[OptimizationResult]]:
        """
        Optimize strategy parameters using backtesting
        
        Returns:
            (best_parameters, all_results)
        """
        
        logger.info(f"🚀 Starting strategy optimization")
        logger.info(f"   Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Generate historical data once (reuse for all tests)
        historical_data = self.data_generator.generate_price_series(start_date, end_date, interval_minutes=60)
        
        # Define parameters to optimize
        optimization_params = self.define_optimization_parameters()
        parameter_combinations = self.generate_parameter_combinations(optimization_params)
        
        # Test each parameter combination
        results = []
        best_score = -float('inf')
        best_parameters = None
        
        for i, params in enumerate(parameter_combinations):
            try:
                logger.info(f"🧪 Testing combination {i+1}/{len(parameter_combinations)}: {params}")
                
                # Run backtest with these parameters
                result = await self._backtest_with_parameters(
                    params, historical_data, helius_api_key, quicknode_url
                )
                
                results.append(result)
                
                # Check if this is the best result
                if result.score > best_score:
                    best_score = result.score
                    best_parameters = params
                    logger.info(f"✨ New best score: {best_score:.4f} with params: {params}")
                
            except Exception as e:
                logger.error(f"Error testing parameters {params}: {e}")
                continue
        
        logger.info(f"🎯 Optimization complete!")
        logger.info(f"   Best parameters: {best_parameters}")
        logger.info(f"   Best score: {best_score:.4f}")
        
        return best_parameters, results
    
    async def _backtest_with_parameters(self,
                                      parameters: Dict[str, float],
                                      historical_data: List[PriceData],
                                      helius_api_key: str,
                                      quicknode_url: Optional[str]) -> OptimizationResult:
        """Run backtest with specific parameters"""
        
        # Initialize components with custom parameters
        strategy = SOLMomentumStrategy(helius_api_key, quicknode_url)
        
        # Apply optimization parameters
        strategy.short_ma_period = int(parameters["short_ma_period"])
        strategy.long_ma_period = int(parameters["long_ma_period"])
        strategy.rsi_period = int(parameters["rsi_period"])
        strategy.volume_threshold = parameters["volume_threshold"]
        
        paper_engine = PaperTradingEngine(self.initial_balance)
        risk_manager = RiskManager()
        
        # Track results
        trade_history = []
        equity_curve = []
        
        # Process historical data
        current_position = None
        confidence_threshold = parameters["confidence_threshold"]
        
        for i, price_data in enumerate(historical_data):
            try:
                # Add price data to strategy
                strategy.price_history.append(price_data)
                if len(strategy.price_history) > strategy.max_history:
                    strategy.price_history = strategy.price_history[-strategy.max_history:]
                
                # Generate signal
                if len(strategy.price_history) >= strategy.short_ma_period:
                    signal = strategy.generate_signal()
                    
                    if signal and signal.confidence >= confidence_threshold:
                        
                        # Execute trades
                        if signal.signal_type.value == "BUY" and not current_position:
                            # Calculate position size
                            portfolio_value = paper_engine.get_portfolio_value()
                            quantity, _ = risk_manager.calculate_position_size(
                                symbol="SOL",
                                entry_price=signal.price,
                                portfolio_value=portfolio_value,
                                confidence=signal.confidence,
                                volatility=0.03
                            )
                            
                            try:
                                order_id = await paper_engine.place_order(
                                    symbol="SOL",
                                    side=OrderSide.BUY,
                                    quantity=quantity,
                                    order_type=OrderType.MARKET,
                                    strategy_id="optimization"
                                )
                                
                                current_position = {
                                    "entry_price": signal.price,
                                    "quantity": quantity,
                                    "entry_time": price_data.timestamp
                                }
                                
                                trade_history.append({
                                    "timestamp": price_data.timestamp,
                                    "action": "BUY",
                                    "price": signal.price,
                                    "quantity": quantity,
                                    "confidence": signal.confidence
                                })
                                
                            except Exception as e:
                                pass  # Skip failed orders
                        
                        elif signal.signal_type.value == "SELL" and current_position:
                            try:
                                order_id = await paper_engine.place_order(
                                    symbol="SOL",
                                    side=OrderSide.SELL,
                                    quantity=current_position["quantity"],
                                    order_type=OrderType.MARKET,
                                    strategy_id="optimization"
                                )
                                
                                # Calculate trade return
                                trade_return = (signal.price - current_position["entry_price"]) / current_position["entry_price"]
                                
                                trade_history.append({
                                    "timestamp": price_data.timestamp,
                                    "action": "SELL",
                                    "price": signal.price,
                                    "quantity": current_position["quantity"],
                                    "confidence": signal.confidence,
                                    "trade_return": trade_return
                                })
                                
                                current_position = None
                                
                            except Exception as e:
                                pass  # Skip failed orders
                
                # Track equity curve (every 6 hours)
                if i % 6 == 0:
                    paper_engine.update_positions()
                    current_equity = paper_engine.get_portfolio_value()
                    equity_curve.append((price_data.timestamp, current_equity))
                
            except Exception as e:
                continue
        
        # Calculate final metrics
        final_balance = paper_engine.get_portfolio_value()
        total_return = ((final_balance / self.initial_balance) - 1) * 100
        
        # Calculate performance metrics
        if len(equity_curve) > 1:
            returns = []
            for i in range(1, len(equity_curve)):
                prev_val = equity_curve[i-1][1]
                curr_val = equity_curve[i][1]
                if prev_val > 0:
                    returns.append((curr_val - prev_val) / prev_val)
            
            volatility = statistics.stdev(returns) * (252 ** 0.5) if len(returns) > 1 else 0
            avg_return = statistics.mean(returns) * 252 if returns else 0
            sharpe_ratio = (avg_return - 0.02) / volatility if volatility > 0 else 0
            
            # Max drawdown
            max_drawdown = 0
            peak = self.initial_balance
            for _, equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        else:
            sharpe_ratio = 0
            max_drawdown = 0
        
        # Trade statistics
        completed_trades = [t for t in trade_history if "trade_return" in t]
        total_trades = len(completed_trades)
        
        if total_trades > 0:
            profitable_trades = len([t for t in completed_trades if t["trade_return"] > 0])
            win_rate = (profitable_trades / total_trades) * 100
        else:
            win_rate = 0
        
        # Calculate composite score
        score = self._calculate_optimization_score(
            total_return, sharpe_ratio, max_drawdown, win_rate, total_trades
        )
        
        return OptimizationResult(
            parameters=parameters,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            total_trades=total_trades,
            score=score
        )
    
    def _calculate_optimization_score(self,
                                    total_return: float,
                                    sharpe_ratio: float,
                                    max_drawdown: float,
                                    win_rate: float,
                                    total_trades: int) -> float:
        """Calculate composite optimization score"""
        
        # Weighted scoring system
        weights = {
            "sharpe_ratio": 0.4,
            "total_return": 0.3,
            "max_drawdown": 0.2,
            "win_rate": 0.1
        }
        
        # Normalize metrics (0-1 scale)
        normalized_sharpe = max(0, min(1, (sharpe_ratio + 2) / 4))  # -2 to 2 range
        normalized_return = max(0, min(1, total_return / 100))  # 0-100% range
        normalized_drawdown = max(0, 1 - max_drawdown)  # Lower drawdown is better
        normalized_win_rate = win_rate / 100  # 0-100% to 0-1
        
        # Penalty for too few trades
        trade_penalty = 1.0 if total_trades >= 5 else total_trades / 5
        
        # Calculate weighted score
        score = (
            weights["sharpe_ratio"] * normalized_sharpe +
            weights["total_return"] * normalized_return +
            weights["max_drawdown"] * normalized_drawdown +
            weights["win_rate"] * normalized_win_rate
        ) * trade_penalty
        
        return score
    
    def generate_optimization_report(self, 
                                   best_parameters: Dict[str, float],
                                   all_results: List[OptimizationResult]) -> str:
        """Generate optimization report"""
        
        # Sort results by score
        sorted_results = sorted(all_results, key=lambda x: x.score, reverse=True)
        top_5 = sorted_results[:5]
        
        report = f"""
🎯 STRATEGY OPTIMIZATION REPORT
{'='*60}

🏆 BEST PARAMETERS:
{json.dumps(best_parameters, indent=2)}

📊 BEST PERFORMANCE:
   Total Return: {top_5[0].total_return:.2f}%
   Sharpe Ratio: {top_5[0].sharpe_ratio:.2f}
   Max Drawdown: {top_5[0].max_drawdown*100:.2f}%
   Win Rate: {top_5[0].win_rate:.1f}%
   Total Trades: {top_5[0].total_trades}
   Optimization Score: {top_5[0].score:.4f}

🥇 TOP 5 PARAMETER COMBINATIONS:
"""
        
        for i, result in enumerate(top_5, 1):
            report += f"""
{i}. Score: {result.score:.4f}
   Parameters: {result.parameters}
   Return: {result.total_return:.2f}%, Sharpe: {result.sharpe_ratio:.2f}
   Drawdown: {result.max_drawdown*100:.2f}%, Win Rate: {result.win_rate:.1f}%
"""
        
        report += f"\n{'='*60}\n"
        return report

# Test function
async def test_strategy_optimization():
    """Test strategy optimization"""
    print("🧪 Testing Strategy Optimization")
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
        # Initialize optimizer
        optimizer = StrategyOptimizer(initial_balance=10000.0)
        
        # Define optimization period (shorter for testing)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=15)  # 15 days for quick test
        
        # Run optimization
        best_params, all_results = await optimizer.optimize_strategy(
            start_date=start_date,
            end_date=end_date,
            helius_api_key=helius_api_key
        )
        
        # Generate report
        report = optimizer.generate_optimization_report(best_params, all_results)
        print(report)
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy optimization test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_strategy_optimization())
