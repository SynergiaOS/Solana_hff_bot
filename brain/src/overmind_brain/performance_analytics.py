#!/usr/bin/env python3
"""
Performance Analytics
Advanced performance metrics and analysis for THE OVERMIND PROTOCOL
"""

import logging
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    # Basic metrics
    total_return: float
    total_return_pct: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int  # days
    value_at_risk_95: float
    conditional_var_95: float
    calmar_ratio: float
    sortino_ratio: float
    
    # Trade metrics
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_trade_duration: float  # hours
    
    # Advanced metrics
    information_ratio: float
    treynor_ratio: float
    jensen_alpha: float
    beta: float
    correlation_to_market: float
    
    # Consistency metrics
    monthly_win_rate: float
    consecutive_wins: int
    consecutive_losses: int
    recovery_factor: float

class PerformanceAnalyzer:
    """
    Advanced performance analysis for trading strategies
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate  # 2% annual risk-free rate
        
    def calculate_comprehensive_metrics(self,
                                      equity_curve: List[Tuple[datetime, float]],
                                      trade_history: List[Dict[str, Any]],
                                      benchmark_returns: Optional[List[float]] = None) -> PerformanceMetrics:
        """Calculate all performance metrics"""
        
        if len(equity_curve) < 2:
            return self._empty_metrics()
        
        # Extract returns
        returns = self._calculate_returns(equity_curve)
        initial_balance = equity_curve[0][1]
        final_balance = equity_curve[-1][1]
        
        # Basic metrics
        total_return = final_balance - initial_balance
        total_return_pct = (total_return / initial_balance) * 100
        
        # Annualized return
        days = (equity_curve[-1][0] - equity_curve[0][0]).days
        annualized_return = ((final_balance / initial_balance) ** (365 / max(days, 1))) - 1
        
        # Volatility (annualized)
        volatility = statistics.stdev(returns) * (252 ** 0.5) if len(returns) > 1 else 0
        
        # Sharpe ratio
        excess_return = annualized_return - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # Risk metrics
        max_drawdown, max_dd_duration = self._calculate_max_drawdown(equity_curve)
        var_95 = self._calculate_var(returns, 0.95)
        cvar_95 = self._calculate_conditional_var(returns, 0.95)
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        sortino_ratio = self._calculate_sortino_ratio(returns, self.risk_free_rate)
        
        # Trade metrics
        trade_metrics = self._calculate_trade_metrics(trade_history)
        
        # Advanced metrics
        advanced_metrics = self._calculate_advanced_metrics(returns, benchmark_returns)
        
        # Consistency metrics
        consistency_metrics = self._calculate_consistency_metrics(equity_curve, trade_history)
        
        return PerformanceMetrics(
            # Basic metrics
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            
            # Risk metrics
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_dd_duration,
            value_at_risk_95=var_95,
            conditional_var_95=cvar_95,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            
            # Trade metrics
            total_trades=trade_metrics["total_trades"],
            win_rate=trade_metrics["win_rate"],
            profit_factor=trade_metrics["profit_factor"],
            avg_win=trade_metrics["avg_win"],
            avg_loss=trade_metrics["avg_loss"],
            largest_win=trade_metrics["largest_win"],
            largest_loss=trade_metrics["largest_loss"],
            avg_trade_duration=trade_metrics["avg_duration"],
            
            # Advanced metrics
            information_ratio=advanced_metrics["information_ratio"],
            treynor_ratio=advanced_metrics["treynor_ratio"],
            jensen_alpha=advanced_metrics["jensen_alpha"],
            beta=advanced_metrics["beta"],
            correlation_to_market=advanced_metrics["correlation"],
            
            # Consistency metrics
            monthly_win_rate=consistency_metrics["monthly_win_rate"],
            consecutive_wins=consistency_metrics["consecutive_wins"],
            consecutive_losses=consistency_metrics["consecutive_losses"],
            recovery_factor=consistency_metrics["recovery_factor"]
        )
    
    def _calculate_returns(self, equity_curve: List[Tuple[datetime, float]]) -> List[float]:
        """Calculate period returns from equity curve"""
        returns = []
        for i in range(1, len(equity_curve)):
            prev_value = equity_curve[i-1][1]
            curr_value = equity_curve[i][1]
            if prev_value > 0:
                returns.append((curr_value - prev_value) / prev_value)
        return returns
    
    def _calculate_max_drawdown(self, equity_curve: List[Tuple[datetime, float]]) -> Tuple[float, int]:
        """Calculate maximum drawdown and its duration"""
        max_drawdown = 0
        max_duration = 0
        peak = equity_curve[0][1]
        peak_date = equity_curve[0][0]
        
        for date, value in equity_curve:
            if value > peak:
                peak = value
                peak_date = date
            else:
                drawdown = (peak - value) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    duration = (date - peak_date).days
                    if duration > max_duration:
                        max_duration = duration
        
        return max_drawdown, max_duration
    
    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        """Calculate Value at Risk"""
        if len(returns) < 2:
            return 0
        
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return abs(sorted_returns[index]) if index < len(sorted_returns) else 0
    
    def _calculate_conditional_var(self, returns: List[float], confidence: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if len(returns) < 2:
            return 0
        
        var = self._calculate_var(returns, confidence)
        tail_losses = [r for r in returns if r <= -var]
        return abs(statistics.mean(tail_losses)) if tail_losses else 0
    
    def _calculate_sortino_ratio(self, returns: List[float], risk_free_rate: float) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if len(returns) < 2:
            return 0
        
        excess_returns = [r - risk_free_rate/252 for r in returns]  # Daily risk-free rate
        downside_returns = [r for r in excess_returns if r < 0]
        
        if not downside_returns:
            return float('inf') if statistics.mean(excess_returns) > 0 else 0
        
        downside_deviation = statistics.stdev(downside_returns) * (252 ** 0.5)
        avg_excess_return = statistics.mean(excess_returns) * 252
        
        return avg_excess_return / downside_deviation if downside_deviation > 0 else 0
    
    def _calculate_trade_metrics(self, trade_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trade-specific metrics"""
        
        # Filter completed trades (buy-sell pairs)
        completed_trades = []
        open_position = None
        
        for trade in trade_history:
            if trade["action"] == "BUY":
                open_position = trade
            elif trade["action"] == "SELL" and open_position:
                trade_return = trade.get("trade_return", 0)
                duration = trade.get("hold_time", 0)
                
                completed_trades.append({
                    "return": trade_return,
                    "duration": duration,
                    "entry_time": open_position["timestamp"],
                    "exit_time": trade["timestamp"]
                })
                open_position = None
        
        if not completed_trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "largest_win": 0,
                "largest_loss": 0,
                "avg_duration": 0
            }
        
        # Calculate metrics
        returns = [t["return"] for t in completed_trades]
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        
        total_trades = len(completed_trades)
        win_rate = (len(wins) / total_trades) * 100
        
        avg_win = statistics.mean(wins) if wins else 0
        avg_loss = statistics.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0
        
        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        durations = [t["duration"] for t in completed_trades if t["duration"] > 0]
        avg_duration = statistics.mean(durations) if durations else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_win": avg_win * 100,  # Convert to percentage
            "avg_loss": avg_loss * 100,
            "largest_win": largest_win * 100,
            "largest_loss": largest_loss * 100,
            "avg_duration": avg_duration
        }
    
    def _calculate_advanced_metrics(self, returns: List[float], benchmark_returns: Optional[List[float]]) -> Dict[str, Any]:
        """Calculate advanced performance metrics"""
        
        if not benchmark_returns or len(benchmark_returns) != len(returns):
            # Use mock benchmark (market return)
            benchmark_returns = [0.0003] * len(returns)  # 0.03% daily market return
        
        if len(returns) < 2:
            return {
                "information_ratio": 0,
                "treynor_ratio": 0,
                "jensen_alpha": 0,
                "beta": 0,
                "correlation": 0
            }
        
        # Beta calculation
        if len(benchmark_returns) == len(returns):
            covariance = np.cov(returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        else:
            beta = 0
        
        # Correlation
        correlation = np.corrcoef(returns, benchmark_returns)[0][1] if len(benchmark_returns) == len(returns) else 0
        
        # Information ratio
        excess_returns = [r - b for r, b in zip(returns, benchmark_returns)]
        tracking_error = statistics.stdev(excess_returns) if len(excess_returns) > 1 else 0
        information_ratio = statistics.mean(excess_returns) / tracking_error if tracking_error > 0 else 0
        
        # Treynor ratio
        avg_return = statistics.mean(returns) * 252  # Annualized
        treynor_ratio = (avg_return - self.risk_free_rate) / beta if beta != 0 else 0
        
        # Jensen's Alpha
        market_return = statistics.mean(benchmark_returns) * 252  # Annualized
        expected_return = self.risk_free_rate + beta * (market_return - self.risk_free_rate)
        jensen_alpha = avg_return - expected_return
        
        return {
            "information_ratio": information_ratio,
            "treynor_ratio": treynor_ratio,
            "jensen_alpha": jensen_alpha,
            "beta": beta,
            "correlation": correlation
        }
    
    def _calculate_consistency_metrics(self, equity_curve: List[Tuple[datetime, float]], trade_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consistency and reliability metrics"""
        
        # Monthly win rate (simplified)
        monthly_returns = self._group_returns_by_month(equity_curve)
        positive_months = len([r for r in monthly_returns if r > 0])
        monthly_win_rate = (positive_months / len(monthly_returns)) * 100 if monthly_returns else 0
        
        # Consecutive wins/losses
        consecutive_wins, consecutive_losses = self._calculate_consecutive_streaks(trade_history)
        
        # Recovery factor
        max_dd = self._calculate_max_drawdown(equity_curve)[0]
        total_return = (equity_curve[-1][1] / equity_curve[0][1]) - 1 if len(equity_curve) > 1 else 0
        recovery_factor = total_return / max_dd if max_dd > 0 else 0
        
        return {
            "monthly_win_rate": monthly_win_rate,
            "consecutive_wins": consecutive_wins,
            "consecutive_losses": consecutive_losses,
            "recovery_factor": recovery_factor
        }
    
    def _group_returns_by_month(self, equity_curve: List[Tuple[datetime, float]]) -> List[float]:
        """Group returns by month"""
        if len(equity_curve) < 2:
            return []
        
        monthly_returns = []
        current_month = equity_curve[0][0].month
        month_start_value = equity_curve[0][1]
        
        for date, value in equity_curve[1:]:
            if date.month != current_month:
                # Month ended, calculate return
                monthly_return = (value - month_start_value) / month_start_value
                monthly_returns.append(monthly_return)
                
                # Start new month
                current_month = date.month
                month_start_value = value
        
        return monthly_returns
    
    def _calculate_consecutive_streaks(self, trade_history: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Calculate maximum consecutive wins and losses"""
        
        # Get trade results
        results = []
        for trade in trade_history:
            if "trade_return" in trade:
                results.append(trade["trade_return"] > 0)
        
        if not results:
            return 0, 0
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for is_win in results:
            if is_win:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return max_wins, max_losses
    
    def _empty_metrics(self) -> PerformanceMetrics:
        """Return empty metrics for edge cases"""
        return PerformanceMetrics(
            total_return=0, total_return_pct=0, annualized_return=0, volatility=0, sharpe_ratio=0,
            max_drawdown=0, max_drawdown_duration=0, value_at_risk_95=0, conditional_var_95=0,
            calmar_ratio=0, sortino_ratio=0, total_trades=0, win_rate=0, profit_factor=0,
            avg_win=0, avg_loss=0, largest_win=0, largest_loss=0, avg_trade_duration=0,
            information_ratio=0, treynor_ratio=0, jensen_alpha=0, beta=0, correlation_to_market=0,
            monthly_win_rate=0, consecutive_wins=0, consecutive_losses=0, recovery_factor=0
        )
    
    def generate_performance_report(self, metrics: PerformanceMetrics) -> str:
        """Generate a comprehensive performance report"""
        
        report = f"""
📊 PERFORMANCE ANALYSIS REPORT
{'='*50}

💰 RETURN METRICS
   Total Return: {metrics.total_return_pct:.2f}%
   Annualized Return: {metrics.annualized_return*100:.2f}%
   Volatility: {metrics.volatility*100:.2f}%
   Sharpe Ratio: {metrics.sharpe_ratio:.2f}

🛡️ RISK METRICS
   Max Drawdown: {metrics.max_drawdown*100:.2f}%
   Max DD Duration: {metrics.max_drawdown_duration} days
   VaR (95%): {metrics.value_at_risk_95*100:.2f}%
   CVaR (95%): {metrics.conditional_var_95*100:.2f}%
   Calmar Ratio: {metrics.calmar_ratio:.2f}
   Sortino Ratio: {metrics.sortino_ratio:.2f}

📈 TRADE METRICS
   Total Trades: {metrics.total_trades}
   Win Rate: {metrics.win_rate:.1f}%
   Profit Factor: {metrics.profit_factor:.2f}
   Avg Win: {metrics.avg_win:.2f}%
   Avg Loss: {metrics.avg_loss:.2f}%
   Largest Win: {metrics.largest_win:.2f}%
   Largest Loss: {metrics.largest_loss:.2f}%
   Avg Trade Duration: {metrics.avg_trade_duration:.1f} hours

🎯 ADVANCED METRICS
   Information Ratio: {metrics.information_ratio:.2f}
   Treynor Ratio: {metrics.treynor_ratio:.2f}
   Jensen's Alpha: {metrics.jensen_alpha*100:.2f}%
   Beta: {metrics.beta:.2f}
   Market Correlation: {metrics.correlation_to_market:.2f}

🔄 CONSISTENCY METRICS
   Monthly Win Rate: {metrics.monthly_win_rate:.1f}%
   Max Consecutive Wins: {metrics.consecutive_wins}
   Max Consecutive Losses: {metrics.consecutive_losses}
   Recovery Factor: {metrics.recovery_factor:.2f}

{'='*50}
"""
        return report

# Test function
def test_performance_analytics():
    """Test performance analytics"""
    print("🧪 Testing Performance Analytics")
    print("-" * 40)
    
    # Create mock data
    from datetime import datetime, timedelta
    
    # Mock equity curve (growing with some volatility)
    start_date = datetime.now() - timedelta(days=30)
    equity_curve = []
    value = 10000
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        # Add some random movement
        change = (i * 0.01) + ((-1) ** i) * 0.005  # Trend + noise
        value *= (1 + change)
        equity_curve.append((date, value))
    
    # Mock trade history
    trade_history = [
        {"action": "BUY", "timestamp": start_date + timedelta(days=1), "price": 100},
        {"action": "SELL", "timestamp": start_date + timedelta(days=3), "trade_return": 0.02, "hold_time": 48},
        {"action": "BUY", "timestamp": start_date + timedelta(days=5), "price": 102},
        {"action": "SELL", "timestamp": start_date + timedelta(days=7), "trade_return": -0.01, "hold_time": 48},
        {"action": "BUY", "timestamp": start_date + timedelta(days=10), "price": 101},
        {"action": "SELL", "timestamp": start_date + timedelta(days=12), "trade_return": 0.03, "hold_time": 48},
    ]
    
    # Analyze performance
    analyzer = PerformanceAnalyzer()
    metrics = analyzer.calculate_comprehensive_metrics(equity_curve, trade_history)
    
    # Generate report
    report = analyzer.generate_performance_report(metrics)
    print(report)
    
    return True

if __name__ == "__main__":
    test_performance_analytics()
