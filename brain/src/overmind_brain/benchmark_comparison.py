#!/usr/bin/env python3
"""
Benchmark Comparison
Compare trading strategy performance against various benchmarks
"""

import logging
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

try:
    from .performance_analytics import PerformanceAnalyzer, PerformanceMetrics
    from .backtesting_framework import BacktestResult
except ImportError:
    # Direct import for testing
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from performance_analytics import PerformanceAnalyzer, PerformanceMetrics
    from backtesting_framework import BacktestResult

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Benchmark performance result"""
    name: str
    description: str
    total_return: float
    total_return_pct: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    equity_curve: List[Tuple[datetime, float]]

@dataclass
class ComparisonResult:
    """Strategy vs benchmark comparison"""
    strategy_name: str
    benchmark_name: str
    
    # Return comparison
    strategy_return: float
    benchmark_return: float
    excess_return: float
    
    # Risk comparison
    strategy_volatility: float
    benchmark_volatility: float
    strategy_sharpe: float
    benchmark_sharpe: float
    
    # Risk-adjusted comparison
    information_ratio: float
    tracking_error: float
    beta: float
    alpha: float
    
    # Win metrics
    outperformance_ratio: float  # % of periods strategy outperformed
    upside_capture: float
    downside_capture: float

class BenchmarkGenerator:
    """Generate benchmark performance data"""
    
    def __init__(self):
        pass
    
    def generate_buy_and_hold_sol(self, 
                                 start_date: datetime, 
                                 end_date: datetime, 
                                 initial_balance: float = 10000.0) -> BenchmarkResult:
        """Generate buy-and-hold SOL benchmark"""
        
        # Generate SOL price series (simplified)
        days = (end_date - start_date).days
        equity_curve = []
        
        # SOL parameters
        sol_annual_return = 0.15  # 15% annual return assumption
        sol_volatility = 0.60  # 60% annual volatility
        
        # Generate daily returns
        np.random.seed(42)  # Reproducible results
        daily_returns = np.random.normal(
            sol_annual_return / 365,  # Daily mean return
            sol_volatility / np.sqrt(365),  # Daily volatility
            days
        )
        
        # Calculate equity curve
        current_value = initial_balance
        current_date = start_date
        
        equity_curve.append((current_date, current_value))
        
        for daily_return in daily_returns:
            current_value *= (1 + daily_return)
            current_date += timedelta(days=1)
            equity_curve.append((current_date, current_value))
        
        # Calculate metrics
        final_value = equity_curve[-1][1]
        total_return = final_value - initial_balance
        total_return_pct = (total_return / initial_balance) * 100
        annualized_return = ((final_value / initial_balance) ** (365 / days)) - 1
        volatility = statistics.stdev(daily_returns) * np.sqrt(365)
        
        # Calculate max drawdown
        max_drawdown = 0
        peak = initial_balance
        for _, value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Sharpe ratio (assuming 2% risk-free rate)
        excess_return = annualized_return - 0.02
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        return BenchmarkResult(
            name="SOL_Buy_Hold",
            description="Buy and Hold SOL Strategy",
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            equity_curve=equity_curve
        )
    
    def generate_market_benchmark(self, 
                                start_date: datetime, 
                                end_date: datetime, 
                                initial_balance: float = 10000.0) -> BenchmarkResult:
        """Generate crypto market benchmark (simplified)"""
        
        days = (end_date - start_date).days
        equity_curve = []
        
        # Market parameters (conservative crypto market)
        market_annual_return = 0.08  # 8% annual return
        market_volatility = 0.40  # 40% annual volatility
        
        # Generate daily returns
        np.random.seed(123)  # Different seed for market
        daily_returns = np.random.normal(
            market_annual_return / 365,
            market_volatility / np.sqrt(365),
            days
        )
        
        # Calculate equity curve
        current_value = initial_balance
        current_date = start_date
        
        equity_curve.append((current_date, current_value))
        
        for daily_return in daily_returns:
            current_value *= (1 + daily_return)
            current_date += timedelta(days=1)
            equity_curve.append((current_date, current_value))
        
        # Calculate metrics
        final_value = equity_curve[-1][1]
        total_return = final_value - initial_balance
        total_return_pct = (total_return / initial_balance) * 100
        annualized_return = ((final_value / initial_balance) ** (365 / days)) - 1
        volatility = statistics.stdev(daily_returns) * np.sqrt(365)
        
        # Calculate max drawdown
        max_drawdown = 0
        peak = initial_balance
        for _, value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Sharpe ratio
        excess_return = annualized_return - 0.02
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        return BenchmarkResult(
            name="Crypto_Market",
            description="Crypto Market Index",
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            equity_curve=equity_curve
        )
    
    def generate_risk_free_benchmark(self, 
                                   start_date: datetime, 
                                   end_date: datetime, 
                                   initial_balance: float = 10000.0,
                                   annual_rate: float = 0.02) -> BenchmarkResult:
        """Generate risk-free rate benchmark"""
        
        days = (end_date - start_date).days
        daily_rate = annual_rate / 365
        
        # Calculate compound growth
        final_value = initial_balance * ((1 + daily_rate) ** days)
        
        # Create equity curve
        equity_curve = []
        current_value = initial_balance
        current_date = start_date
        
        for day in range(days + 1):
            equity_curve.append((current_date, current_value))
            current_value *= (1 + daily_rate)
            current_date += timedelta(days=1)
        
        total_return = final_value - initial_balance
        total_return_pct = (total_return / initial_balance) * 100
        
        return BenchmarkResult(
            name="Risk_Free",
            description=f"Risk-Free Rate ({annual_rate*100:.1f}%)",
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annual_rate,
            volatility=0.0,
            sharpe_ratio=0.0,  # By definition
            max_drawdown=0.0,
            equity_curve=equity_curve
        )

class BenchmarkComparator:
    """Compare strategy performance against benchmarks"""
    
    def __init__(self):
        self.benchmark_generator = BenchmarkGenerator()
        self.performance_analyzer = PerformanceAnalyzer()
    
    def compare_with_benchmarks(self, 
                              strategy_result: BacktestResult,
                              benchmarks: List[str] = None) -> Dict[str, ComparisonResult]:
        """Compare strategy with multiple benchmarks"""
        
        if benchmarks is None:
            benchmarks = ["buy_hold_sol", "crypto_market", "risk_free"]
        
        comparisons = {}
        
        for benchmark_name in benchmarks:
            # Generate benchmark
            if benchmark_name == "buy_hold_sol":
                benchmark = self.benchmark_generator.generate_buy_and_hold_sol(
                    strategy_result.start_date, 
                    strategy_result.end_date, 
                    strategy_result.initial_balance
                )
            elif benchmark_name == "crypto_market":
                benchmark = self.benchmark_generator.generate_market_benchmark(
                    strategy_result.start_date, 
                    strategy_result.end_date, 
                    strategy_result.initial_balance
                )
            elif benchmark_name == "risk_free":
                benchmark = self.benchmark_generator.generate_risk_free_benchmark(
                    strategy_result.start_date, 
                    strategy_result.end_date, 
                    strategy_result.initial_balance
                )
            else:
                continue
            
            # Compare strategy vs benchmark
            comparison = self._compare_strategy_vs_benchmark(strategy_result, benchmark)
            comparisons[benchmark_name] = comparison
        
        return comparisons
    
    def _compare_strategy_vs_benchmark(self, 
                                     strategy: BacktestResult, 
                                     benchmark: BenchmarkResult) -> ComparisonResult:
        """Compare strategy against single benchmark"""
        
        # Extract strategy returns from equity curve
        strategy_returns = []
        for i in range(1, len(strategy.equity_curve)):
            prev_val = strategy.equity_curve[i-1][1]
            curr_val = strategy.equity_curve[i][1]
            if prev_val > 0:
                strategy_returns.append((curr_val - prev_val) / prev_val)
        
        # Extract benchmark returns
        benchmark_returns = []
        for i in range(1, len(benchmark.equity_curve)):
            prev_val = benchmark.equity_curve[i-1][1]
            curr_val = benchmark.equity_curve[i][1]
            if prev_val > 0:
                benchmark_returns.append((curr_val - prev_val) / prev_val)
        
        # Align lengths
        min_length = min(len(strategy_returns), len(benchmark_returns))
        strategy_returns = strategy_returns[:min_length]
        benchmark_returns = benchmark_returns[:min_length]
        
        # Calculate comparison metrics
        excess_returns = [s - b for s, b in zip(strategy_returns, benchmark_returns)]
        
        # Tracking error
        tracking_error = statistics.stdev(excess_returns) if len(excess_returns) > 1 else 0
        
        # Information ratio
        avg_excess_return = statistics.mean(excess_returns) if excess_returns else 0
        information_ratio = avg_excess_return / tracking_error if tracking_error > 0 else 0
        
        # Beta and Alpha
        if len(strategy_returns) > 1 and len(benchmark_returns) > 1:
            covariance = np.cov(strategy_returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            
            # Alpha = Strategy Return - (Risk Free + Beta * (Benchmark Return - Risk Free))
            risk_free_rate = 0.02  # 2% annual
            alpha = strategy.annualized_return - (risk_free_rate + beta * (benchmark.annualized_return - risk_free_rate))
        else:
            beta = 0
            alpha = 0
        
        # Outperformance ratio
        outperformance_periods = sum(1 for s, b in zip(strategy_returns, benchmark_returns) if s > b)
        outperformance_ratio = (outperformance_periods / len(strategy_returns)) * 100 if strategy_returns else 0
        
        # Upside/Downside capture
        up_periods = [(s, b) for s, b in zip(strategy_returns, benchmark_returns) if b > 0]
        down_periods = [(s, b) for s, b in zip(strategy_returns, benchmark_returns) if b < 0]
        
        if up_periods:
            upside_capture = (statistics.mean([s for s, b in up_periods]) / 
                            statistics.mean([b for s, b in up_periods])) * 100
        else:
            upside_capture = 0
        
        if down_periods:
            downside_capture = (statistics.mean([s for s, b in down_periods]) / 
                              statistics.mean([b for s, b in down_periods])) * 100
        else:
            downside_capture = 0
        
        return ComparisonResult(
            strategy_name=strategy.strategy_name,
            benchmark_name=benchmark.name,
            strategy_return=strategy.total_return_pct,
            benchmark_return=benchmark.total_return_pct,
            excess_return=strategy.total_return_pct - benchmark.total_return_pct,
            strategy_volatility=strategy.volatility,
            benchmark_volatility=benchmark.volatility,
            strategy_sharpe=strategy.sharpe_ratio,
            benchmark_sharpe=benchmark.sharpe_ratio,
            information_ratio=information_ratio,
            tracking_error=tracking_error * 100,  # Convert to percentage
            beta=beta,
            alpha=alpha * 100,  # Convert to percentage
            outperformance_ratio=outperformance_ratio,
            upside_capture=upside_capture,
            downside_capture=downside_capture
        )
    
    def generate_comparison_report(self, comparisons: Dict[str, ComparisonResult]) -> str:
        """Generate comprehensive comparison report"""
        
        report = f"""
📊 BENCHMARK COMPARISON REPORT
{'='*60}

"""
        
        for benchmark_name, comparison in comparisons.items():
            report += f"""
🎯 {comparison.benchmark_name.upper()}
{'-'*40}
Return Comparison:
   Strategy Return: {comparison.strategy_return:.2f}%
   Benchmark Return: {comparison.benchmark_return:.2f}%
   Excess Return: {comparison.excess_return:.2f}%

Risk Comparison:
   Strategy Volatility: {comparison.strategy_volatility*100:.2f}%
   Benchmark Volatility: {comparison.benchmark_volatility*100:.2f}%
   Strategy Sharpe: {comparison.strategy_sharpe:.2f}
   Benchmark Sharpe: {comparison.benchmark_sharpe:.2f}

Risk-Adjusted Metrics:
   Information Ratio: {comparison.information_ratio:.2f}
   Tracking Error: {comparison.tracking_error:.2f}%
   Beta: {comparison.beta:.2f}
   Alpha: {comparison.alpha:.2f}%

Performance Metrics:
   Outperformance Ratio: {comparison.outperformance_ratio:.1f}%
   Upside Capture: {comparison.upside_capture:.1f}%
   Downside Capture: {comparison.downside_capture:.1f}%

"""
        
        report += f"{'='*60}\n"
        return report

# Test function
def test_benchmark_comparison():
    """Test benchmark comparison"""
    print("🧪 Testing Benchmark Comparison")
    print("-" * 50)
    
    # Create mock strategy result
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    # Mock equity curve for strategy
    strategy_equity = []
    value = 10000
    for i in range(31):
        date = start_date + timedelta(days=i)
        # Strategy with some outperformance
        change = 0.002 + ((-1) ** i) * 0.001  # 0.2% daily + noise
        value *= (1 + change)
        strategy_equity.append((date, value))
    
    # Mock BacktestResult
    class MockBacktestResult:
        def __init__(self):
            self.strategy_name = "SOL_Momentum_Test"
            self.start_date = start_date
            self.end_date = end_date
            self.initial_balance = 10000.0
            self.final_balance = strategy_equity[-1][1]
            self.total_return = self.final_balance - self.initial_balance
            self.total_return_pct = (self.total_return / self.initial_balance) * 100
            self.annualized_return = ((self.final_balance / self.initial_balance) ** (365 / 30)) - 1
            self.volatility = 0.15  # 15% volatility
            self.sharpe_ratio = 1.2
            self.equity_curve = strategy_equity
    
    strategy_result = MockBacktestResult()
    
    # Compare with benchmarks
    comparator = BenchmarkComparator()
    comparisons = comparator.compare_with_benchmarks(strategy_result)
    
    # Generate report
    report = comparator.generate_comparison_report(comparisons)
    print(report)
    
    return True

if __name__ == "__main__":
    test_benchmark_comparison()
