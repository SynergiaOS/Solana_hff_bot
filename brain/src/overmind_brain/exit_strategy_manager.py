"""
THE OVERMIND PROTOCOL - Exit Strategy Manager
Intelligent exit decision making and position management
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class ExitReason(Enum):
    """Types of exit triggers"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TIME_BASED = "time_based"
    RISK_MANAGEMENT = "risk_management"
    MARKET_CONDITIONS = "market_conditions"
    STRATEGY_SIGNAL = "strategy_signal"

@dataclass
class Position:
    """Active trading position"""
    symbol: str
    entry_price: float
    quantity: float
    entry_time: datetime
    entry_strategy: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_hold_time_hours: Optional[int] = None
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    
    def update_current_price(self, price: float):
        """Update current price and calculate PnL"""
        self.current_price = price
        self.unrealized_pnl = (price - self.entry_price) * self.quantity

@dataclass
class ExitDecision:
    """Exit decision result"""
    should_exit: bool
    exit_reason: ExitReason
    confidence: float
    suggested_price: Optional[float] = None
    partial_exit: bool = False
    exit_percentage: float = 1.0  # 100% by default
    reasoning: str = ""
    urgency: str = "NORMAL"  # LOW, NORMAL, HIGH, CRITICAL

class ExitStrategyManager:
    """Manages position exits and sell decisions"""
    
    def __init__(self):
        """Initialize Exit Strategy Manager"""
        self.active_positions: Dict[str, Position] = {}
        self.default_stop_loss_pct = 0.05  # 5%
        self.default_take_profit_pct = 0.15  # 15%
        self.max_position_hold_hours = 24  # 24 hours max hold
        
        logger.info("🚪 Exit Strategy Manager initialized")
    
    def add_position(self, position: Position) -> bool:
        """Add new position for monitoring"""
        try:
            self.active_positions[position.symbol] = position
            logger.info(f"📊 Added position: {position.symbol} @ ${position.entry_price:.4f}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add position {position.symbol}: {e}")
            return False
    
    def evaluate_exit_decision(self, symbol: str, market_data: Dict[str, Any]) -> Optional[ExitDecision]:
        """
        Evaluate if position should be exited based on current market conditions
        
        Args:
            symbol: Symbol to evaluate
            market_data: Current market data
            
        Returns:
            ExitDecision or None if no position exists
        """
        position = self.active_positions.get(symbol)
        if not position:
            return None
        
        current_price = market_data.get('price', 0.0)
        if current_price <= 0:
            logger.warning(f"⚠️ Invalid price for {symbol}: {current_price}")
            return None
        
        # Update position with current price
        position.update_current_price(current_price)
        
        logger.debug(f"🔍 Evaluating exit for {symbol}: ${current_price:.4f} (Entry: ${position.entry_price:.4f})")
        
        # Check all exit conditions
        exit_checks = [
            self._check_stop_loss(position),
            self._check_take_profit(position),
            self._check_time_based_exit(position),
            self._check_risk_management_exit(position, market_data),
            self._check_market_condition_exit(position, market_data),
            self._check_strategy_signal_exit(position, market_data)
        ]
        
        # Find the highest priority exit reason
        valid_exits = [exit_dec for exit_dec in exit_checks if exit_dec and exit_dec.should_exit]
        
        if valid_exits:
            # Sort by urgency and confidence
            urgency_priority = {"CRITICAL": 4, "HIGH": 3, "NORMAL": 2, "LOW": 1}
            best_exit = max(valid_exits, key=lambda x: (urgency_priority.get(x.urgency, 0), x.confidence))
            
            logger.info(f"🚪 Exit decision for {symbol}: {best_exit.exit_reason.value} "
                       f"(Confidence: {best_exit.confidence:.2f}, Urgency: {best_exit.urgency})")
            
            return best_exit
        
        return ExitDecision(
            should_exit=False,
            exit_reason=ExitReason.MARKET_CONDITIONS,
            confidence=0.0,
            reasoning="No exit conditions met - continue holding"
        )
    
    def _check_stop_loss(self, position: Position) -> Optional[ExitDecision]:
        """Check if stop loss should be triggered"""
        if not position.stop_loss or not position.current_price:
            return None
        
        if position.current_price <= position.stop_loss:
            pnl_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
            
            return ExitDecision(
                should_exit=True,
                exit_reason=ExitReason.STOP_LOSS,
                confidence=0.95,
                suggested_price=position.current_price,
                urgency="HIGH",
                reasoning=f"Stop loss triggered at ${position.current_price:.4f} "
                         f"(Target: ${position.stop_loss:.4f}, PnL: {pnl_pct:.1f}%)"
            )
        
        return None
    
    def _check_take_profit(self, position: Position) -> Optional[ExitDecision]:
        """Check if take profit should be triggered"""
        if not position.take_profit or not position.current_price:
            return None
        
        if position.current_price >= position.take_profit:
            pnl_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
            
            return ExitDecision(
                should_exit=True,
                exit_reason=ExitReason.TAKE_PROFIT,
                confidence=0.90,
                suggested_price=position.current_price,
                urgency="NORMAL",
                reasoning=f"Take profit target reached at ${position.current_price:.4f} "
                         f"(Target: ${position.take_profit:.4f}, PnL: {pnl_pct:.1f}%)"
            )
        
        return None
    
    def _check_time_based_exit(self, position: Position) -> Optional[ExitDecision]:
        """Check if position should be exited based on time"""
        if not position.max_hold_time_hours:
            position.max_hold_time_hours = self.max_position_hold_hours
        
        time_held = datetime.now() - position.entry_time
        max_hold = timedelta(hours=position.max_hold_time_hours)
        
        if time_held >= max_hold:
            return ExitDecision(
                should_exit=True,
                exit_reason=ExitReason.TIME_BASED,
                confidence=0.70,
                suggested_price=position.current_price,
                urgency="NORMAL",
                reasoning=f"Maximum hold time reached: {time_held.total_seconds()/3600:.1f}h "
                         f"(Limit: {position.max_hold_time_hours}h)"
            )
        
        # Warning when approaching time limit
        if time_held >= max_hold * 0.8:  # 80% of max time
            return ExitDecision(
                should_exit=False,
                exit_reason=ExitReason.TIME_BASED,
                confidence=0.50,
                reasoning=f"Approaching time limit: {time_held.total_seconds()/3600:.1f}h / {position.max_hold_time_hours}h"
            )
        
        return None
    
    def _check_risk_management_exit(self, position: Position, market_data: Dict[str, Any]) -> Optional[ExitDecision]:
        """Check if position should be exited for risk management"""
        if not position.current_price:
            return None
        
        # Check for extreme price drops
        price_change_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
        
        # Emergency exit on >10% loss (even without stop loss)
        if price_change_pct <= -10.0:
            return ExitDecision(
                should_exit=True,
                exit_reason=ExitReason.RISK_MANAGEMENT,
                confidence=0.85,
                suggested_price=position.current_price,
                urgency="CRITICAL",
                reasoning=f"Emergency exit: Extreme loss {price_change_pct:.1f}% "
                         f"(${position.entry_price:.4f} → ${position.current_price:.4f})"
            )
        
        # Check volatility spike
        volatility = market_data.get('volatility', 0.0)
        if volatility > 0.15:  # 15% volatility
            return ExitDecision(
                should_exit=True,
                exit_reason=ExitReason.RISK_MANAGEMENT,
                confidence=0.75,
                suggested_price=position.current_price,
                urgency="HIGH",
                reasoning=f"High volatility detected: {volatility:.1%} - risk management exit"
            )
        
        return None
    
    def _check_market_condition_exit(self, position: Position, market_data: Dict[str, Any]) -> Optional[ExitDecision]:
        """Check market conditions for exit signals"""
        # Check volume drop (liquidity concerns)
        volume_24h = market_data.get('volume_24h', 0)
        if volume_24h < 10000:  # Very low volume
            return ExitDecision(
                should_exit=True,
                exit_reason=ExitReason.MARKET_CONDITIONS,
                confidence=0.65,
                suggested_price=position.current_price,
                urgency="NORMAL",
                reasoning=f"Low trading volume: ${volume_24h:,.0f} - liquidity risk"
            )
        
        # Check liquidity drop
        liquidity = market_data.get('liquidity', 0)
        if liquidity < 5000:  # Very low liquidity
            return ExitDecision(
                should_exit=True,
                exit_reason=ExitReason.MARKET_CONDITIONS,
                confidence=0.70,
                suggested_price=position.current_price,
                urgency="HIGH",
                reasoning=f"Low liquidity: ${liquidity:,.0f} - exit risk"
            )
        
        return None
    
    def _check_strategy_signal_exit(self, position: Position, market_data: Dict[str, Any]) -> Optional[ExitDecision]:
        """Check for strategy-specific exit signals"""
        signal_type = market_data.get('signal_type', '')
        confidence = market_data.get('confidence', 0.5)
        
        # Negative signals that suggest exit
        negative_signals = [
            'sell_pressure', 'bearish_pattern', 'negative_sentiment',
            'whale_dump', 'developer_dump', 'exploit_detected'
        ]
        
        if any(neg_signal in signal_type for neg_signal in negative_signals):
            return ExitDecision(
                should_exit=True,
                exit_reason=ExitReason.STRATEGY_SIGNAL,
                confidence=confidence,
                suggested_price=position.current_price,
                urgency="HIGH",
                reasoning=f"Negative strategy signal detected: {signal_type}"
            )
        
        # Strategy-specific rules based on entry strategy
        if position.entry_strategy == "memecoin_hunter":
            # Memecoins - take profits quickly, exit on social sentiment drop
            social_score = market_data.get('social_score', 5.0)
            if social_score < 3.0:
                return ExitDecision(
                    should_exit=True,
                    exit_reason=ExitReason.STRATEGY_SIGNAL,
                    confidence=0.80,
                    suggested_price=position.current_price,
                    urgency="NORMAL",
                    reasoning=f"Memecoin social score dropped to {social_score:.1f}"
                )
        
        return None
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all active positions"""
        total_positions = len(self.active_positions)
        total_unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.active_positions.values() 
            if pos.unrealized_pnl is not None
        )
        
        positions_summary = {}
        for symbol, position in self.active_positions.items():
            pnl_pct = 0.0
            if position.current_price:
                pnl_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
            
            positions_summary[symbol] = {
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "unrealized_pnl": position.unrealized_pnl,
                "pnl_percentage": pnl_pct,
                "entry_strategy": position.entry_strategy,
                "time_held_hours": (datetime.now() - position.entry_time).total_seconds() / 3600
            }
        
        return {
            "total_positions": total_positions,
            "total_unrealized_pnl": total_unrealized_pnl,
            "positions": positions_summary,
            "timestamp": datetime.now().isoformat()
        }
    
    def remove_position(self, symbol: str) -> bool:
        """Remove position after exit"""
        if symbol in self.active_positions:
            position = self.active_positions.pop(symbol)
            logger.info(f"🚪 Removed position: {symbol} (held for {(datetime.now() - position.entry_time).total_seconds()/3600:.1f}h)")
            return True
        return False

# Global exit strategy manager instance
exit_strategy_manager = ExitStrategyManager()