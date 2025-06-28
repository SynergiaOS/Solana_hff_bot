#!/usr/bin/env python3
"""
Performance Benchmarking System
Comprehensive performance comparison against multiple benchmarks
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
import numpy as np

try:
    from .benchmark_comparison import BenchmarkComparator, BenchmarkResult, ComparisonResult
    from .performance_analytics import PerformanceAnalyzer, PerformanceMetrics
    from .daily_pnl_tracker import DailyPnLTracker, DailyPnLRecord
except ImportError:
    # Direct import for testing
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from benchmark_comparison import BenchmarkComparator, BenchmarkResult, ComparisonResult
    from performance_analytics import PerformanceAnalyzer, PerformanceMetrics
    from daily_pnl_tracker import DailyPnLTracker, DailyPnLRecord

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkPerformance:
    """Benchmark performance data"""
    name: str
    description: str
    period_start: datetime
    period_end: datetime
    total_return: float
    total_return_pct: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    correlation_to_strategy: float

@dataclass
class PerformanceBenchmarkReport:
    """Comprehensive benchmark report"""
    strategy_name: str
    report_date: datetime
    period_days: int
    
    # Strategy performance
    strategy_performance: PerformanceMetrics
    
    # Benchmark comparisons
    benchmark_performances: Dict[str, BenchmarkPerformance]
    
    # Relative performance
    outperformance_vs_benchmarks: Dict[str, float]
    risk_adjusted_outperformance: Dict[str, float]
    
    # Rankings
    return_ranking: int  # 1 = best performer
    risk_adjusted_ranking: int
    
    # Summary metrics
    average_outperformance: float
    consistency_score: float  # How consistently we outperform
    risk_efficiency: float    # Return per unit of risk vs benchmarks

class PerformanceBenchmarkingSystem:
    """
    Performance Benchmarking System for THE OVERMIND PROTOCOL
    
    Features:
    - Multiple benchmark comparisons
    - Risk-adjusted performance analysis
    - Relative performance tracking
    - Automated benchmark reporting
    - Performance attribution analysis
    """
    
    def __init__(self):
        self.data_dir = "benchmarking_data"
        self.ensure_data_directory()
        
        # Components
        self.benchmark_comparator = BenchmarkComparator()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Benchmark definitions
        self.benchmarks = {
            "buy_hold_sol": {
                "name": "Buy & Hold SOL",
                "description": "Simple buy and hold SOL strategy",
                "risk_free": False
            },
            "crypto_market": {
                "name": "Crypto Market Index",
                "description": "Diversified crypto market portfolio",
                "risk_free": False
            },
            "risk_free": {
                "name": "Risk-Free Rate",
                "description": "2% annual risk-free rate",
                "risk_free": True
            },
            "balanced_crypto": {
                "name": "Balanced Crypto",
                "description": "60% BTC, 30% ETH, 10% SOL portfolio",
                "risk_free": False
            }
        }
        
        # Historical data
        self.benchmark_history: Dict[str, List[BenchmarkResult]] = {}
        self.performance_reports: List[PerformanceBenchmarkReport] = []
        
        logger.info("📊 Performance Benchmarking System initialized")
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    async def generate_benchmark_report(self,
                                      strategy_equity_curve: List[Tuple[datetime, float]],
                                      strategy_trades: List[Dict[str, Any]],
                                      initial_balance: float = 10000.0) -> PerformanceBenchmarkReport:
        """Generate comprehensive benchmark report"""
        
        if not strategy_equity_curve:
            raise ValueError("Strategy equity curve is required")
        
        period_start = strategy_equity_curve[0][0]
        period_end = strategy_equity_curve[-1][0]
        period_days = (period_end - period_start).days
        
        logger.info(f"📊 Generating benchmark report for period: {period_start.date()} to {period_end.date()}")
        
        # Calculate strategy performance
        strategy_performance = self.performance_analyzer.calculate_comprehensive_metrics(
            strategy_equity_curve, strategy_trades
        )
        
        # Generate benchmark performances
        benchmark_performances = {}
        outperformance_vs_benchmarks = {}
        risk_adjusted_outperformance = {}
        
        for benchmark_id, benchmark_info in self.benchmarks.items():
            try:
                # Generate benchmark data
                benchmark_result = await self._generate_benchmark_data(
                    benchmark_id, period_start, period_end, initial_balance
                )
                
                # Calculate benchmark performance
                benchmark_perf = self._calculate_benchmark_performance(
                    benchmark_result, strategy_equity_curve, strategy_performance
                )
                
                benchmark_performances[benchmark_id] = benchmark_perf
                
                # Calculate outperformance
                outperformance = strategy_performance.total_return_pct - benchmark_perf.total_return_pct
                outperformance_vs_benchmarks[benchmark_id] = outperformance
                
                # Risk-adjusted outperformance
                if benchmark_perf.volatility > 0:
                    strategy_risk_adj = strategy_performance.total_return_pct / strategy_performance.volatility
                    benchmark_risk_adj = benchmark_perf.total_return_pct / benchmark_perf.volatility
                    risk_adjusted_outperformance[benchmark_id] = strategy_risk_adj - benchmark_risk_adj
                else:
                    risk_adjusted_outperformance[benchmark_id] = strategy_performance.total_return_pct
                
            except Exception as e:
                logger.error(f"Error generating benchmark {benchmark_id}: {e}")
                continue
        
        # Calculate rankings
        all_returns = [strategy_performance.total_return_pct] + [b.total_return_pct for b in benchmark_performances.values()]
        all_sharpe = [strategy_performance.sharpe_ratio] + [b.sharpe_ratio for b in benchmark_performances.values()]
        
        return_ranking = self._calculate_ranking(strategy_performance.total_return_pct, all_returns)
        risk_adjusted_ranking = self._calculate_ranking(strategy_performance.sharpe_ratio, all_sharpe)
        
        # Summary metrics
        average_outperformance = statistics.mean(outperformance_vs_benchmarks.values()) if outperformance_vs_benchmarks else 0
        consistency_score = self._calculate_consistency_score(outperformance_vs_benchmarks)
        risk_efficiency = self._calculate_risk_efficiency(strategy_performance, benchmark_performances)
        
        report = PerformanceBenchmarkReport(
            strategy_name="SOL Momentum Strategy",
            report_date=datetime.now(),
            period_days=period_days,
            strategy_performance=strategy_performance,
            benchmark_performances=benchmark_performances,
            outperformance_vs_benchmarks=outperformance_vs_benchmarks,
            risk_adjusted_outperformance=risk_adjusted_outperformance,
            return_ranking=return_ranking,
            risk_adjusted_ranking=risk_adjusted_ranking,
            average_outperformance=average_outperformance,
            consistency_score=consistency_score,
            risk_efficiency=risk_efficiency
        )
        
        # Save report
        self.performance_reports.append(report)
        self._save_benchmark_report(report)
        
        logger.info(f"✅ Benchmark report generated - Avg outperformance: {average_outperformance:.2f}%")
        
        return report
    
    async def _generate_benchmark_data(self,
                                     benchmark_id: str,
                                     start_date: datetime,
                                     end_date: datetime,
                                     initial_balance: float) -> BenchmarkResult:
        """Generate benchmark data for comparison"""
        
        if benchmark_id == "buy_hold_sol":
            return self.benchmark_comparator.benchmark_generator.generate_buy_and_hold_sol(
                start_date, end_date, initial_balance
            )
        elif benchmark_id == "crypto_market":
            return self.benchmark_comparator.benchmark_generator.generate_market_benchmark(
                start_date, end_date, initial_balance
            )
        elif benchmark_id == "risk_free":
            return self.benchmark_comparator.benchmark_generator.generate_risk_free_benchmark(
                start_date, end_date, initial_balance
            )
        elif benchmark_id == "balanced_crypto":
            return self._generate_balanced_crypto_benchmark(start_date, end_date, initial_balance)
        else:
            raise ValueError(f"Unknown benchmark: {benchmark_id}")
    
    def _generate_balanced_crypto_benchmark(self,
                                          start_date: datetime,
                                          end_date: datetime,
                                          initial_balance: float) -> BenchmarkResult:
        """Generate balanced crypto portfolio benchmark"""
        
        days = (end_date - start_date).days
        equity_curve = []
        
        # Balanced portfolio parameters (60% BTC, 30% ETH, 10% SOL)
        btc_weight = 0.6
        eth_weight = 0.3
        sol_weight = 0.1
        
        # Simulated returns (simplified)
        np.random.seed(456)  # Different seed for balanced portfolio
        
        # Generate correlated returns for BTC, ETH, SOL
        btc_returns = np.random.normal(0.0002, 0.04 / np.sqrt(365), days)  # BTC: lower vol
        eth_returns = np.random.normal(0.0003, 0.05 / np.sqrt(365), days)  # ETH: medium vol
        sol_returns = np.random.normal(0.0004, 0.06 / np.sqrt(365), days)  # SOL: higher vol
        
        # Portfolio returns
        portfolio_returns = (btc_weight * btc_returns + 
                           eth_weight * eth_returns + 
                           sol_weight * sol_returns)
        
        # Calculate equity curve
        current_value = initial_balance
        current_date = start_date
        
        equity_curve.append((current_date, current_value))
        
        for daily_return in portfolio_returns:
            current_value *= (1 + daily_return)
            current_date += timedelta(days=1)
            equity_curve.append((current_date, current_value))
        
        # Calculate metrics
        final_value = equity_curve[-1][1]
        total_return = final_value - initial_balance
        total_return_pct = (total_return / initial_balance) * 100
        annualized_return = ((final_value / initial_balance) ** (365 / days)) - 1
        volatility = statistics.stdev(portfolio_returns) * np.sqrt(365)
        
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
            name="Balanced_Crypto",
            description="60% BTC, 30% ETH, 10% SOL Portfolio",
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            equity_curve=equity_curve
        )
    
    def _calculate_benchmark_performance(self,
                                       benchmark_result: BenchmarkResult,
                                       strategy_equity_curve: List[Tuple[datetime, float]],
                                       strategy_performance: PerformanceMetrics) -> BenchmarkPerformance:
        """Calculate benchmark performance metrics"""
        
        # Extract returns for correlation calculation
        strategy_returns = []
        for i in range(1, len(strategy_equity_curve)):
            prev_val = strategy_equity_curve[i-1][1]
            curr_val = strategy_equity_curve[i][1]
            if prev_val > 0:
                strategy_returns.append((curr_val - prev_val) / prev_val)
        
        benchmark_returns = []
        for i in range(1, len(benchmark_result.equity_curve)):
            prev_val = benchmark_result.equity_curve[i-1][1]
            curr_val = benchmark_result.equity_curve[i][1]
            if prev_val > 0:
                benchmark_returns.append((curr_val - prev_val) / prev_val)
        
        # Calculate correlation
        min_length = min(len(strategy_returns), len(benchmark_returns))
        if min_length > 1:
            strategy_returns = strategy_returns[:min_length]
            benchmark_returns = benchmark_returns[:min_length]
            correlation = np.corrcoef(strategy_returns, benchmark_returns)[0][1]
        else:
            correlation = 0.0
        
        # Calculate win rate (simplified)
        positive_returns = len([r for r in benchmark_returns if r > 0])
        win_rate = (positive_returns / len(benchmark_returns) * 100) if benchmark_returns else 0
        
        return BenchmarkPerformance(
            name=benchmark_result.name,
            description=benchmark_result.description,
            period_start=benchmark_result.equity_curve[0][0],
            period_end=benchmark_result.equity_curve[-1][0],
            total_return=benchmark_result.total_return,
            total_return_pct=benchmark_result.total_return_pct,
            annualized_return=benchmark_result.annualized_return,
            volatility=benchmark_result.volatility,
            sharpe_ratio=benchmark_result.sharpe_ratio,
            max_drawdown=benchmark_result.max_drawdown,
            win_rate=win_rate,
            correlation_to_strategy=correlation
        )
    
    def _calculate_ranking(self, value: float, all_values: List[float]) -> int:
        """Calculate ranking (1 = best)"""
        sorted_values = sorted(all_values, reverse=True)
        return sorted_values.index(value) + 1
    
    def _calculate_consistency_score(self, outperformance: Dict[str, float]) -> float:
        """Calculate consistency score (0-100)"""
        if not outperformance:
            return 0.0
        
        positive_outperformance = len([v for v in outperformance.values() if v > 0])
        return (positive_outperformance / len(outperformance)) * 100
    
    def _calculate_risk_efficiency(self,
                                 strategy_performance: PerformanceMetrics,
                                 benchmark_performances: Dict[str, BenchmarkPerformance]) -> float:
        """Calculate risk efficiency vs benchmarks"""
        if not benchmark_performances or strategy_performance.volatility == 0:
            return 0.0
        
        strategy_risk_adj = strategy_performance.total_return_pct / strategy_performance.volatility
        
        benchmark_risk_adj_values = []
        for benchmark in benchmark_performances.values():
            if benchmark.volatility > 0:
                benchmark_risk_adj_values.append(benchmark.total_return_pct / benchmark.volatility)
        
        if not benchmark_risk_adj_values:
            return strategy_risk_adj
        
        avg_benchmark_risk_adj = statistics.mean(benchmark_risk_adj_values)
        return strategy_risk_adj / avg_benchmark_risk_adj if avg_benchmark_risk_adj != 0 else 1.0
    
    def _save_benchmark_report(self, report: PerformanceBenchmarkReport):
        """Save benchmark report to file"""
        report_file = os.path.join(self.data_dir, f"benchmark_report_{report.report_date.strftime('%Y%m%d_%H%M%S')}.json")
        
        # Convert to serializable format
        report_data = {
            "strategy_name": report.strategy_name,
            "report_date": report.report_date.isoformat(),
            "period_days": report.period_days,
            "strategy_performance": asdict(report.strategy_performance),
            "benchmark_performances": {k: asdict(v) for k, v in report.benchmark_performances.items()},
            "outperformance_vs_benchmarks": report.outperformance_vs_benchmarks,
            "risk_adjusted_outperformance": report.risk_adjusted_outperformance,
            "return_ranking": report.return_ranking,
            "risk_adjusted_ranking": report.risk_adjusted_ranking,
            "average_outperformance": report.average_outperformance,
            "consistency_score": report.consistency_score,
            "risk_efficiency": report.risk_efficiency
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        logger.info(f"📋 Benchmark report saved: {report_file}")
    
    def generate_benchmark_summary(self, report: PerformanceBenchmarkReport) -> str:
        """Generate human-readable benchmark summary"""
        
        summary = f"""
📊 PERFORMANCE BENCHMARK REPORT
{'='*60}

🎯 STRATEGY: {report.strategy_name}
   Report Date: {report.report_date.strftime('%Y-%m-%d %H:%M:%S')}
   Analysis Period: {report.period_days} days

💰 STRATEGY PERFORMANCE
   Total Return: {report.strategy_performance.total_return_pct:.2f}%
   Annualized Return: {report.strategy_performance.annualized_return*100:.2f}%
   Volatility: {report.strategy_performance.volatility*100:.2f}%
   Sharpe Ratio: {report.strategy_performance.sharpe_ratio:.2f}
   Max Drawdown: {report.strategy_performance.max_drawdown*100:.2f}%

📈 BENCHMARK COMPARISONS
"""
        
        for benchmark_id, benchmark in report.benchmark_performances.items():
            outperformance = report.outperformance_vs_benchmarks.get(benchmark_id, 0)
            risk_adj_outperf = report.risk_adjusted_outperformance.get(benchmark_id, 0)
            
            summary += f"""
   {benchmark.name}:
     Return: {benchmark.total_return_pct:.2f}%
     Volatility: {benchmark.volatility*100:.2f}%
     Sharpe: {benchmark.sharpe_ratio:.2f}
     Outperformance: {outperformance:+.2f}%
     Risk-Adj Outperformance: {risk_adj_outperf:+.2f}
     Correlation: {benchmark.correlation_to_strategy:.2f}
"""
        
        summary += f"""
🏆 RANKINGS
   Return Ranking: #{report.return_ranking} out of {len(report.benchmark_performances) + 1}
   Risk-Adjusted Ranking: #{report.risk_adjusted_ranking} out of {len(report.benchmark_performances) + 1}

📊 SUMMARY METRICS
   Average Outperformance: {report.average_outperformance:+.2f}%
   Consistency Score: {report.consistency_score:.1f}%
   Risk Efficiency: {report.risk_efficiency:.2f}x

{'='*60}
"""
        
        return summary

# Test function
async def test_performance_benchmarking():
    """Test the performance benchmarking system"""
    print("🧪 Testing Performance Benchmarking System")
    print("-" * 50)
    
    # Initialize system
    benchmarking = PerformanceBenchmarkingSystem()
    
    # Create mock strategy data
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    # Mock equity curve (growing with some volatility)
    equity_curve = []
    value = 10000
    current_date = start_date
    
    for i in range(30):
        # Add some random movement with slight upward trend
        change = 0.005 + ((-1) ** i) * 0.002  # 0.5% trend + noise
        value *= (1 + change)
        equity_curve.append((current_date, value))
        current_date += timedelta(days=1)
    
    # Mock trades with proper structure
    trades = [
        {"action": "BUY", "timestamp": start_date + timedelta(days=5), "price": 100},
        {"action": "SELL", "timestamp": start_date + timedelta(days=7), "trade_return": 0.05, "hold_time": 48},
        {"action": "BUY", "timestamp": start_date + timedelta(days=10), "price": 102},
        {"action": "SELL", "timestamp": start_date + timedelta(days=12), "trade_return": -0.02, "hold_time": 48},
        {"action": "BUY", "timestamp": start_date + timedelta(days=15), "price": 101},
        {"action": "SELL", "timestamp": start_date + timedelta(days=17), "trade_return": 0.03, "hold_time": 48}
    ]
    
    # Generate benchmark report
    report = await benchmarking.generate_benchmark_report(equity_curve, trades)
    
    # Generate summary
    summary = benchmarking.generate_benchmark_summary(report)
    print(summary)
    
    return True

if __name__ == "__main__":
    asyncio.run(test_performance_benchmarking())
