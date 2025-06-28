#!/usr/bin/env python3
"""
Risk Metrics Monitor
Real-time risk metrics monitoring with alerts for THE OVERMIND PROTOCOL
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import numpy as np

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    POSITION_SIZE = "position_size"
    DAILY_LOSS = "daily_loss"
    DRAWDOWN = "drawdown"
    VOLATILITY = "volatility"
    VAR_BREACH = "var_breach"
    CORRELATION = "correlation"
    LEVERAGE = "leverage"
    CONCENTRATION = "concentration"

@dataclass
class RiskAlert:
    """Risk alert data structure"""
    alert_id: str
    alert_type: AlertType
    risk_level: RiskLevel
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    action_required: bool
    strategy_affected: Optional[str] = None
    position_affected: Optional[str] = None

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    timestamp: datetime
    
    # Portfolio metrics
    portfolio_value: float
    cash_percentage: float
    positions_count: int
    largest_position_pct: float
    
    # Risk measures
    daily_var_95: float
    daily_var_99: float
    expected_shortfall: float
    max_drawdown: float
    current_drawdown: float
    
    # Volatility metrics
    portfolio_volatility: float
    rolling_volatility_30d: float
    volatility_trend: str  # "increasing", "decreasing", "stable"
    
    # Concentration metrics
    concentration_ratio: float  # Top 3 positions as % of portfolio
    correlation_risk: float
    
    # Performance metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Risk-adjusted metrics
    risk_adjusted_return: float
    information_ratio: float
    
    # Alert status
    active_alerts: int
    risk_score: float  # 0-100 composite risk score

class RiskMetricsMonitor:
    """
    Real-time Risk Metrics Monitoring System
    
    Features:
    - Continuous risk metrics calculation
    - Real-time alert generation
    - Risk threshold monitoring
    - Historical risk tracking
    - Automated risk reporting
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.data_dir = "risk_monitoring_data"
        self.ensure_data_directory()
        
        # Risk thresholds
        self.thresholds = {
            "max_position_size": 0.20,  # 20% max single position
            "max_daily_loss": 0.05,     # 5% max daily loss
            "max_drawdown": 0.15,       # 15% max drawdown
            "max_volatility": 0.30,     # 30% max annual volatility
            "max_var_95": 0.03,         # 3% max daily VaR 95%
            "max_concentration": 0.50,  # 50% max top 3 positions
            "min_sharpe": 0.5,          # Minimum Sharpe ratio
            "max_correlation": 0.80     # Max correlation between positions
        }
        
        # Historical data
        self.risk_history: List[RiskMetrics] = []
        self.active_alerts: List[RiskAlert] = []
        self.price_history: Dict[str, List[float]] = {}
        
        # Monitoring settings
        self.monitoring_interval = 60  # 60 seconds
        self.alert_cooldown = 300      # 5 minutes between same alerts
        self.last_alerts: Dict[str, datetime] = {}
        
        logger.info("🛡️ Risk Metrics Monitor initialized")
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def calculate_risk_metrics(self, 
                             portfolio_value: float,
                             positions: Dict[str, Any],
                             daily_returns: List[float],
                             cash_balance: float) -> RiskMetrics:
        """Calculate comprehensive risk metrics"""
        
        timestamp = datetime.now()
        
        # Portfolio composition
        cash_percentage = (cash_balance / portfolio_value) * 100
        positions_count = len(positions)
        
        # Position analysis
        position_values = [pos.get('value', 0) for pos in positions.values()]
        largest_position_pct = (max(position_values) / portfolio_value * 100) if position_values else 0
        
        # Concentration metrics
        sorted_positions = sorted(position_values, reverse=True)
        top_3_value = sum(sorted_positions[:3])
        concentration_ratio = (top_3_value / portfolio_value * 100) if portfolio_value > 0 else 0
        
        # Risk measures
        daily_var_95 = self._calculate_var(daily_returns, 0.95)
        daily_var_99 = self._calculate_var(daily_returns, 0.99)
        expected_shortfall = self._calculate_expected_shortfall(daily_returns, 0.95)
        
        # Drawdown calculation
        max_drawdown, current_drawdown = self._calculate_drawdowns(portfolio_value)
        
        # Volatility metrics
        portfolio_volatility = self._calculate_portfolio_volatility(daily_returns)
        rolling_vol_30d = self._calculate_rolling_volatility(daily_returns, 30)
        volatility_trend = self._determine_volatility_trend()
        
        # Performance ratios
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        calmar_ratio = self._calculate_calmar_ratio(daily_returns, max_drawdown)
        
        # Risk-adjusted metrics
        risk_adjusted_return = self._calculate_risk_adjusted_return(daily_returns, portfolio_volatility)
        information_ratio = self._calculate_information_ratio(daily_returns)
        
        # Correlation risk (simplified)
        correlation_risk = self._calculate_correlation_risk(positions)
        
        # Composite risk score
        risk_score = self._calculate_risk_score(
            largest_position_pct, max_drawdown, portfolio_volatility, 
            concentration_ratio, len(self.active_alerts)
        )
        
        return RiskMetrics(
            timestamp=timestamp,
            portfolio_value=portfolio_value,
            cash_percentage=cash_percentage,
            positions_count=positions_count,
            largest_position_pct=largest_position_pct,
            daily_var_95=daily_var_95,
            daily_var_99=daily_var_99,
            expected_shortfall=expected_shortfall,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            portfolio_volatility=portfolio_volatility,
            rolling_volatility_30d=rolling_vol_30d,
            volatility_trend=volatility_trend,
            concentration_ratio=concentration_ratio,
            correlation_risk=correlation_risk,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            risk_adjusted_return=risk_adjusted_return,
            information_ratio=information_ratio,
            active_alerts=len(self.active_alerts),
            risk_score=risk_score
        )
    
    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        """Calculate Value at Risk"""
        if len(returns) < 2:
            return 0.0
        
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return abs(sorted_returns[index]) if index < len(sorted_returns) else 0.0
    
    def _calculate_expected_shortfall(self, returns: List[float], confidence: float) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        var = self._calculate_var(returns, confidence)
        tail_losses = [r for r in returns if r <= -var]
        return abs(statistics.mean(tail_losses)) if tail_losses else 0.0
    
    def _calculate_drawdowns(self, current_value: float) -> Tuple[float, float]:
        """Calculate maximum and current drawdown"""
        if not self.risk_history:
            return 0.0, 0.0
        
        # Find peak value
        peak_value = max(r.portfolio_value for r in self.risk_history)
        peak_value = max(peak_value, current_value)
        
        # Current drawdown
        current_drawdown = (peak_value - current_value) / peak_value if peak_value > 0 else 0.0
        
        # Maximum drawdown from history
        max_drawdown = 0.0
        running_peak = self.initial_balance
        
        for record in self.risk_history:
            if record.portfolio_value > running_peak:
                running_peak = record.portfolio_value
            
            drawdown = (running_peak - record.portfolio_value) / running_peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown, current_drawdown
    
    def _calculate_portfolio_volatility(self, returns: List[float]) -> float:
        """Calculate annualized portfolio volatility"""
        if len(returns) < 2:
            return 0.0
        
        return statistics.stdev(returns) * (252 ** 0.5)  # Annualized
    
    def _calculate_rolling_volatility(self, returns: List[float], window: int) -> float:
        """Calculate rolling volatility"""
        if len(returns) < window:
            return self._calculate_portfolio_volatility(returns)
        
        recent_returns = returns[-window:]
        return statistics.stdev(recent_returns) * (252 ** 0.5)
    
    def _determine_volatility_trend(self) -> str:
        """Determine volatility trend"""
        if len(self.risk_history) < 10:
            return "stable"
        
        recent_vols = [r.portfolio_volatility for r in self.risk_history[-10:]]
        if len(recent_vols) < 2:
            return "stable"
        
        trend = np.polyfit(range(len(recent_vols)), recent_vols, 1)[0]
        
        if trend > 0.01:
            return "increasing"
        elif trend < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0.0
        
        avg_return = statistics.mean(returns) * 252  # Annualized
        volatility = statistics.stdev(returns) * (252 ** 0.5)
        risk_free_rate = 0.02  # 2% annual
        
        return (avg_return - risk_free_rate) / volatility if volatility > 0 else 0.0
    
    def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio"""
        if len(returns) < 2:
            return 0.0
        
        avg_return = statistics.mean(returns) * 252
        downside_returns = [r for r in returns if r < 0]
        
        if not downside_returns:
            return float('inf') if avg_return > 0 else 0.0
        
        downside_deviation = statistics.stdev(downside_returns) * (252 ** 0.5)
        risk_free_rate = 0.02
        
        return (avg_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0.0
    
    def _calculate_calmar_ratio(self, returns: List[float], max_drawdown: float) -> float:
        """Calculate Calmar ratio"""
        if len(returns) < 2 or max_drawdown == 0:
            return 0.0
        
        avg_return = statistics.mean(returns) * 252
        return avg_return / max_drawdown
    
    def _calculate_risk_adjusted_return(self, returns: List[float], volatility: float) -> float:
        """Calculate risk-adjusted return"""
        if len(returns) < 2 or volatility == 0:
            return 0.0
        
        avg_return = statistics.mean(returns) * 252
        return avg_return / volatility
    
    def _calculate_information_ratio(self, returns: List[float]) -> float:
        """Calculate information ratio (simplified)"""
        if len(returns) < 2:
            return 0.0
        
        # Assuming benchmark return of 0.08 (8% annual)
        benchmark_daily = 0.08 / 252
        excess_returns = [r - benchmark_daily for r in returns]
        
        if not excess_returns:
            return 0.0
        
        avg_excess = statistics.mean(excess_returns) * 252
        tracking_error = statistics.stdev(excess_returns) * (252 ** 0.5)
        
        return avg_excess / tracking_error if tracking_error > 0 else 0.0
    
    def _calculate_correlation_risk(self, positions: Dict[str, Any]) -> float:
        """Calculate correlation risk (simplified)"""
        # Simplified correlation risk based on position concentration
        if len(positions) <= 1:
            return 0.0
        
        # Higher concentration = higher correlation risk
        position_values = [pos.get('value', 0) for pos in positions.values()]
        total_value = sum(position_values)
        
        if total_value == 0:
            return 0.0
        
        # Calculate Herfindahl index as proxy for correlation risk
        herfindahl = sum((value / total_value) ** 2 for value in position_values)
        return herfindahl  # 0 = perfectly diversified, 1 = single position
    
    def _calculate_risk_score(self, position_pct: float, drawdown: float, 
                            volatility: float, concentration: float, alerts: int) -> float:
        """Calculate composite risk score (0-100)"""
        
        # Normalize each component (0-1 scale)
        position_score = min(position_pct / 50, 1.0)  # 50% = max score
        drawdown_score = min(drawdown / 0.30, 1.0)    # 30% = max score
        volatility_score = min(volatility / 0.50, 1.0) # 50% = max score
        concentration_score = min(concentration / 80, 1.0) # 80% = max score
        alert_score = min(alerts / 5, 1.0)            # 5 alerts = max score
        
        # Weighted composite score
        weights = [0.25, 0.30, 0.20, 0.15, 0.10]
        scores = [position_score, drawdown_score, volatility_score, concentration_score, alert_score]
        
        composite_score = sum(w * s for w, s in zip(weights, scores)) * 100
        return min(composite_score, 100.0)
    
    def check_risk_thresholds(self, metrics: RiskMetrics) -> List[RiskAlert]:
        """Check all risk thresholds and generate alerts"""
        alerts = []
        
        # Position size check
        if metrics.largest_position_pct > self.thresholds["max_position_size"] * 100:
            alerts.append(self._create_alert(
                AlertType.POSITION_SIZE, RiskLevel.HIGH,
                f"Position size {metrics.largest_position_pct:.1f}% exceeds limit {self.thresholds['max_position_size']*100:.1f}%",
                metrics.largest_position_pct, self.thresholds["max_position_size"] * 100
            ))
        
        # Drawdown check
        if metrics.current_drawdown > self.thresholds["max_drawdown"]:
            risk_level = RiskLevel.CRITICAL if metrics.current_drawdown > 0.20 else RiskLevel.HIGH
            alerts.append(self._create_alert(
                AlertType.DRAWDOWN, risk_level,
                f"Current drawdown {metrics.current_drawdown*100:.1f}% exceeds limit {self.thresholds['max_drawdown']*100:.1f}%",
                metrics.current_drawdown * 100, self.thresholds["max_drawdown"] * 100
            ))
        
        # Volatility check
        if metrics.portfolio_volatility > self.thresholds["max_volatility"]:
            alerts.append(self._create_alert(
                AlertType.VOLATILITY, RiskLevel.MEDIUM,
                f"Portfolio volatility {metrics.portfolio_volatility*100:.1f}% exceeds limit {self.thresholds['max_volatility']*100:.1f}%",
                metrics.portfolio_volatility * 100, self.thresholds["max_volatility"] * 100
            ))
        
        # VaR check
        if metrics.daily_var_95 > self.thresholds["max_var_95"]:
            alerts.append(self._create_alert(
                AlertType.VAR_BREACH, RiskLevel.HIGH,
                f"Daily VaR 95% {metrics.daily_var_95*100:.1f}% exceeds limit {self.thresholds['max_var_95']*100:.1f}%",
                metrics.daily_var_95 * 100, self.thresholds["max_var_95"] * 100
            ))
        
        # Concentration check
        if metrics.concentration_ratio > self.thresholds["max_concentration"] * 100:
            alerts.append(self._create_alert(
                AlertType.CONCENTRATION, RiskLevel.MEDIUM,
                f"Portfolio concentration {metrics.concentration_ratio:.1f}% exceeds limit {self.thresholds['max_concentration']*100:.1f}%",
                metrics.concentration_ratio, self.thresholds["max_concentration"] * 100
            ))
        
        return alerts
    
    def _create_alert(self, alert_type: AlertType, risk_level: RiskLevel,
                     message: str, current_value: float, threshold: float) -> RiskAlert:
        """Create risk alert"""
        alert_id = f"{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return RiskAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            risk_level=risk_level,
            message=message,
            current_value=current_value,
            threshold=threshold,
            timestamp=datetime.now(),
            action_required=risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        )
    
    def add_risk_metrics(self, metrics: RiskMetrics):
        """Add risk metrics and check for alerts"""
        self.risk_history.append(metrics)
        
        # Check thresholds
        new_alerts = self.check_risk_thresholds(metrics)
        
        # Filter alerts by cooldown
        filtered_alerts = []
        for alert in new_alerts:
            alert_key = f"{alert.alert_type.value}_{alert.risk_level.value}"
            last_alert_time = self.last_alerts.get(alert_key)
            
            if not last_alert_time or (datetime.now() - last_alert_time).seconds > self.alert_cooldown:
                filtered_alerts.append(alert)
                self.last_alerts[alert_key] = datetime.now()
        
        # Add new alerts
        self.active_alerts.extend(filtered_alerts)
        
        # Save data
        self._save_risk_data(metrics, filtered_alerts)
        
        # Log alerts
        for alert in filtered_alerts:
            logger.warning(f"🚨 RISK ALERT: {alert.message}")
    
    def _save_risk_data(self, metrics: RiskMetrics, alerts: List[RiskAlert]):
        """Save risk data to files"""
        # Save metrics
        metrics_file = os.path.join(self.data_dir, "risk_metrics.json")
        
        data = {
            "current_metrics": asdict(metrics),
            "historical_metrics": [asdict(m) for m in self.risk_history[-100:]],  # Last 100 records
            "active_alerts": [asdict(a) for a in self.active_alerts],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(metrics_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Save alerts if any
        if alerts:
            alerts_file = os.path.join(self.data_dir, f"alerts_{datetime.now().strftime('%Y%m%d')}.json")
            
            alert_data = {
                "timestamp": datetime.now().isoformat(),
                "alerts": [asdict(a) for a in alerts]
            }
            
            with open(alerts_file, 'a') as f:
                f.write(json.dumps(alert_data, default=str) + '\n')
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk summary"""
        if not self.risk_history:
            return {"status": "no_data"}
        
        latest = self.risk_history[-1]
        
        return {
            "timestamp": latest.timestamp.isoformat(),
            "risk_score": latest.risk_score,
            "risk_level": self._get_risk_level_from_score(latest.risk_score),
            "portfolio_value": latest.portfolio_value,
            "current_drawdown": latest.current_drawdown * 100,
            "volatility": latest.portfolio_volatility * 100,
            "var_95": latest.daily_var_95 * 100,
            "active_alerts": len(self.active_alerts),
            "critical_alerts": len([a for a in self.active_alerts if a.risk_level == RiskLevel.CRITICAL]),
            "positions_count": latest.positions_count,
            "concentration": latest.concentration_ratio
        }
    
    def _get_risk_level_from_score(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score < 25:
            return "LOW"
        elif score < 50:
            return "MEDIUM"
        elif score < 75:
            return "HIGH"
        else:
            return "CRITICAL"

# Test function
def test_risk_metrics_monitor():
    """Test the risk metrics monitor"""
    print("🧪 Testing Risk Metrics Monitor")
    print("-" * 40)
    
    # Initialize monitor
    monitor = RiskMetricsMonitor(initial_balance=10000.0)
    
    # Simulate portfolio data
    portfolio_value = 10500.0
    cash_balance = 2000.0
    positions = {
        "SOL": {"value": 6000.0},
        "BTC": {"value": 2000.0},
        "ETH": {"value": 500.0}
    }
    
    # Simulate daily returns
    daily_returns = [0.02, -0.01, 0.015, -0.025, 0.01, 0.005, -0.015]
    
    # Calculate risk metrics
    metrics = monitor.calculate_risk_metrics(portfolio_value, positions, daily_returns, cash_balance)
    
    print(f"📊 Risk Metrics:")
    print(f"   Portfolio Value: ${metrics.portfolio_value:,.2f}")
    print(f"   Risk Score: {metrics.risk_score:.1f}/100")
    print(f"   Largest Position: {metrics.largest_position_pct:.1f}%")
    print(f"   Current Drawdown: {metrics.current_drawdown*100:.2f}%")
    print(f"   Portfolio Volatility: {metrics.portfolio_volatility*100:.1f}%")
    print(f"   Daily VaR 95%: {metrics.daily_var_95*100:.2f}%")
    print(f"   Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    
    # Add metrics and check alerts
    monitor.add_risk_metrics(metrics)
    
    # Get summary
    summary = monitor.get_risk_summary()
    print(f"\n🛡️ Risk Summary:")
    print(f"   Risk Level: {summary['risk_level']}")
    print(f"   Active Alerts: {summary['active_alerts']}")
    print(f"   Concentration: {summary['concentration']:.1f}%")
    
    return True

if __name__ == "__main__":
    test_risk_metrics_monitor()
