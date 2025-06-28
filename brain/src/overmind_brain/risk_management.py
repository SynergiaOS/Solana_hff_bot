#!/usr/bin/env python3
"""
Risk Management System
Advanced risk management for THE OVERMIND PROTOCOL
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

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
    CORRELATION = "correlation"

@dataclass
class RiskAlert:
    """Risk management alert"""
    alert_type: AlertType
    risk_level: RiskLevel
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    action_required: bool

@dataclass
class PositionRisk:
    """Risk assessment for a position"""
    symbol: str
    position_size: float
    position_value: float
    portfolio_percentage: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    var_1d: float  # 1-day Value at Risk
    max_loss_pct: float

@dataclass
class PortfolioRisk:
    """Overall portfolio risk assessment"""
    total_value: float
    cash_percentage: float
    max_position_percentage: float
    daily_var: float
    max_drawdown: float
    sharpe_ratio: float
    volatility: float
    correlation_risk: float
    risk_score: float
    risk_level: RiskLevel

class RiskManager:
    """
    Advanced Risk Management System
    
    Features:
    - Position sizing based on volatility
    - Dynamic stop-loss and take-profit
    - Portfolio-level risk monitoring
    - Real-time risk alerts
    - Correlation analysis
    - Value at Risk (VaR) calculation
    """
    
    def __init__(self):
        # Risk parameters
        self.max_position_size = 0.15  # 15% max per position
        self.max_portfolio_risk = 0.02  # 2% max portfolio risk per trade
        self.max_daily_loss = 0.05  # 5% max daily loss
        self.max_drawdown = 0.10  # 10% max drawdown
        
        # Stop-loss parameters
        self.default_stop_loss = 0.05  # 5% stop-loss
        self.volatility_multiplier = 2.0  # Stop-loss = volatility * multiplier
        self.min_stop_loss = 0.02  # 2% minimum stop-loss
        self.max_stop_loss = 0.10  # 10% maximum stop-loss
        
        # Take-profit parameters
        self.default_risk_reward = 2.0  # 2:1 risk-reward ratio
        self.min_take_profit = 0.03  # 3% minimum take-profit
        
        # Tracking
        self.price_history: Dict[str, List[float]] = {}
        self.alerts: List[RiskAlert] = []
        self.daily_start_value: Optional[float] = None
        
        logger.info("🛡️ Risk Management System initialized")
    
    def calculate_position_size(self, 
                               symbol: str,
                               entry_price: float,
                               portfolio_value: float,
                               confidence: float = 1.0,
                               volatility: Optional[float] = None) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate optimal position size based on risk parameters
        
        Returns:
            (position_size, risk_details)
        """
        try:
            # Method 1: Fixed percentage of portfolio
            fixed_size = portfolio_value * self.max_position_size
            
            # Method 2: Risk-based sizing (Kelly Criterion simplified)
            if volatility:
                # Adjust position size based on volatility
                volatility_adjusted_size = fixed_size * (0.1 / max(volatility, 0.01))
            else:
                volatility_adjusted_size = fixed_size
            
            # Method 3: Confidence-based sizing
            confidence_adjusted_size = volatility_adjusted_size * confidence
            
            # Method 4: Portfolio risk-based sizing
            stop_loss_pct = self.calculate_stop_loss_percentage(symbol, entry_price, volatility)
            max_risk_amount = portfolio_value * self.max_portfolio_risk
            risk_based_size = max_risk_amount / stop_loss_pct
            
            # Take the minimum of all methods
            final_size = min(
                fixed_size,
                volatility_adjusted_size,
                confidence_adjusted_size,
                risk_based_size
            )
            
            # Convert to quantity
            quantity = final_size / entry_price
            
            risk_details = {
                "fixed_size": fixed_size,
                "volatility_adjusted": volatility_adjusted_size,
                "confidence_adjusted": confidence_adjusted_size,
                "risk_based_size": risk_based_size,
                "final_size": final_size,
                "quantity": quantity,
                "stop_loss_pct": stop_loss_pct,
                "portfolio_pct": (final_size / portfolio_value) * 100
            }
            
            logger.info(f"📏 Position size calculated: {quantity:.4f} {symbol} "
                       f"(${final_size:.2f}, {risk_details['portfolio_pct']:.1f}% of portfolio)")
            
            return quantity, risk_details
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            # Fallback to conservative size
            conservative_size = portfolio_value * 0.05  # 5%
            return conservative_size / entry_price, {"error": str(e)}
    
    def calculate_stop_loss_percentage(self, 
                                     symbol: str,
                                     current_price: float,
                                     volatility: Optional[float] = None) -> float:
        """Calculate dynamic stop-loss percentage"""
        try:
            if volatility:
                # Volatility-based stop-loss
                volatility_stop = volatility * self.volatility_multiplier
                stop_loss_pct = max(self.min_stop_loss, min(volatility_stop, self.max_stop_loss))
            else:
                # Default stop-loss
                stop_loss_pct = self.default_stop_loss
            
            logger.debug(f"Stop-loss calculated: {stop_loss_pct*100:.1f}% for {symbol}")
            return stop_loss_pct
            
        except Exception as e:
            logger.error(f"Error calculating stop-loss: {e}")
            return self.default_stop_loss
    
    def calculate_stop_loss_price(self, 
                                symbol: str,
                                entry_price: float,
                                side: str,
                                volatility: Optional[float] = None) -> float:
        """Calculate stop-loss price"""
        stop_loss_pct = self.calculate_stop_loss_percentage(symbol, entry_price, volatility)
        
        if side.upper() == "BUY":
            # For long positions, stop-loss is below entry price
            stop_price = entry_price * (1 - stop_loss_pct)
        else:
            # For short positions, stop-loss is above entry price
            stop_price = entry_price * (1 + stop_loss_pct)
        
        return stop_price
    
    def calculate_take_profit_price(self,
                                  entry_price: float,
                                  stop_loss_price: float,
                                  side: str,
                                  risk_reward_ratio: float = None) -> float:
        """Calculate take-profit price based on risk-reward ratio"""
        if risk_reward_ratio is None:
            risk_reward_ratio = self.default_risk_reward
        
        risk_amount = abs(entry_price - stop_loss_price)
        reward_amount = risk_amount * risk_reward_ratio
        
        if side.upper() == "BUY":
            # For long positions, take-profit is above entry price
            take_profit_price = entry_price + reward_amount
        else:
            # For short positions, take-profit is below entry price
            take_profit_price = entry_price - reward_amount
        
        return take_profit_price
    
    def assess_position_risk(self,
                           symbol: str,
                           quantity: float,
                           entry_price: float,
                           current_price: float,
                           side: str,
                           portfolio_value: float,
                           volatility: Optional[float] = None) -> PositionRisk:
        """Assess risk for a specific position"""
        
        position_value = quantity * current_price
        portfolio_percentage = (position_value / portfolio_value) * 100
        
        # Calculate stop-loss and take-profit
        stop_loss_price = self.calculate_stop_loss_price(symbol, entry_price, side, volatility)
        take_profit_price = self.calculate_take_profit_price(entry_price, stop_loss_price, side)
        
        # Calculate risk and reward amounts
        risk_amount = abs(quantity * (entry_price - stop_loss_price))
        reward_amount = abs(quantity * (take_profit_price - entry_price))
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
        
        # Calculate 1-day VaR (simplified)
        if volatility:
            var_1d = position_value * volatility * 1.65  # 95% confidence
        else:
            var_1d = position_value * 0.02  # 2% default
        
        # Maximum loss percentage
        max_loss_pct = (risk_amount / portfolio_value) * 100
        
        return PositionRisk(
            symbol=symbol,
            position_size=quantity,
            position_value=position_value,
            portfolio_percentage=portfolio_percentage,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio=risk_reward_ratio,
            var_1d=var_1d,
            max_loss_pct=max_loss_pct
        )
    
    def check_risk_limits(self, portfolio_value: float, daily_pnl: float, positions: Dict[str, Any]) -> List[RiskAlert]:
        """Check all risk limits and generate alerts"""
        alerts = []
        
        # Check daily loss limit
        if self.daily_start_value:
            daily_loss_pct = abs(daily_pnl / self.daily_start_value)
            if daily_loss_pct > self.max_daily_loss:
                alerts.append(RiskAlert(
                    alert_type=AlertType.DAILY_LOSS,
                    risk_level=RiskLevel.CRITICAL,
                    message=f"Daily loss limit exceeded: {daily_loss_pct*100:.1f}% > {self.max_daily_loss*100:.1f}%",
                    current_value=daily_loss_pct,
                    threshold=self.max_daily_loss,
                    timestamp=datetime.now(),
                    action_required=True
                ))
        
        # Check position size limits
        for symbol, position in positions.items():
            position_pct = (position.get('value', 0) / portfolio_value)
            if position_pct > self.max_position_size:
                alerts.append(RiskAlert(
                    alert_type=AlertType.POSITION_SIZE,
                    risk_level=RiskLevel.HIGH,
                    message=f"{symbol} position too large: {position_pct*100:.1f}% > {self.max_position_size*100:.1f}%",
                    current_value=position_pct,
                    threshold=self.max_position_size,
                    timestamp=datetime.now(),
                    action_required=True
                ))
        
        return alerts
    
    def calculate_portfolio_volatility(self, returns: List[float]) -> float:
        """Calculate portfolio volatility"""
        if len(returns) < 2:
            return 0.02  # Default 2% volatility
        
        return statistics.stdev(returns)
    
    def get_risk_summary(self, portfolio_value: float, positions: Dict[str, Any], returns: List[float]) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        
        # Calculate metrics
        volatility = self.calculate_portfolio_volatility(returns)
        max_position_pct = max([pos.get('portfolio_pct', 0) for pos in positions.values()]) if positions else 0
        cash_pct = 100 - sum([pos.get('portfolio_pct', 0) for pos in positions.values()])
        
        # Risk score (0-100, lower is better)
        risk_score = (
            (max_position_pct / self.max_position_size) * 30 +  # Position concentration
            (volatility / 0.05) * 30 +  # Volatility
            (len(positions) / 10) * 20 +  # Number of positions
            ((100 - cash_pct) / 100) * 20  # Cash allocation
        )
        
        # Determine risk level
        if risk_score < 25:
            risk_level = RiskLevel.LOW
        elif risk_score < 50:
            risk_level = RiskLevel.MEDIUM
        elif risk_score < 75:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
        
        return {
            "portfolio_value": portfolio_value,
            "volatility": volatility,
            "max_position_pct": max_position_pct,
            "cash_pct": cash_pct,
            "num_positions": len(positions),
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "alerts_count": len(self.alerts)
        }

# Test function
def test_risk_management():
    """Test risk management system"""
    print("🧪 Testing Risk Management System")
    print("-" * 40)
    
    # Initialize risk manager
    risk_manager = RiskManager()
    
    # Test position sizing
    portfolio_value = 1000.0
    entry_price = 100.0
    confidence = 0.8
    volatility = 0.03  # 3% volatility
    
    quantity, risk_details = risk_manager.calculate_position_size(
        symbol="SOL",
        entry_price=entry_price,
        portfolio_value=portfolio_value,
        confidence=confidence,
        volatility=volatility
    )
    
    print(f"✅ Position Size Calculation:")
    print(f"   Quantity: {quantity:.4f} SOL")
    print(f"   Position Value: ${risk_details['final_size']:.2f}")
    print(f"   Portfolio %: {risk_details['portfolio_pct']:.1f}%")
    print(f"   Stop Loss %: {risk_details['stop_loss_pct']*100:.1f}%")
    
    # Test stop-loss and take-profit
    stop_loss_price = risk_manager.calculate_stop_loss_price("SOL", entry_price, "BUY", volatility)
    take_profit_price = risk_manager.calculate_take_profit_price(entry_price, stop_loss_price, "BUY")
    
    print(f"\n✅ Risk Management Prices:")
    print(f"   Entry Price: ${entry_price:.2f}")
    print(f"   Stop Loss: ${stop_loss_price:.2f}")
    print(f"   Take Profit: ${take_profit_price:.2f}")
    print(f"   Risk/Reward: {(take_profit_price - entry_price) / (entry_price - stop_loss_price):.1f}:1")
    
    # Test position risk assessment
    current_price = 102.0
    position_risk = risk_manager.assess_position_risk(
        symbol="SOL",
        quantity=quantity,
        entry_price=entry_price,
        current_price=current_price,
        side="BUY",
        portfolio_value=portfolio_value,
        volatility=volatility
    )
    
    print(f"\n✅ Position Risk Assessment:")
    print(f"   Position Value: ${position_risk.position_value:.2f}")
    print(f"   Portfolio %: {position_risk.portfolio_percentage:.1f}%")
    print(f"   Max Loss: ${position_risk.risk_amount:.2f} ({position_risk.max_loss_pct:.1f}%)")
    print(f"   1-Day VaR: ${position_risk.var_1d:.2f}")
    
    return True

if __name__ == "__main__":
    test_risk_management()
