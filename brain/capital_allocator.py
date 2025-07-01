#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Dynamic Capital Allocator
Intelligent position sizing based on signal quality and market conditions
"""

import math
import logging
import json
import redis
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CapitalAllocator')

@dataclass
class AllocationParams:
    """Parameters for capital allocation calculation"""
    base_allocation: float = 0.02  # 2% base allocation
    max_allocation: float = 0.25   # 25% maximum allocation
    min_allocation: float = 0.005  # 0.5% minimum allocation
    confidence_threshold: float = 0.5  # Minimum confidence to trade
    risk_multiplier: float = 1.0   # Risk adjustment multiplier
    portfolio_heat: float = 0.0    # Current portfolio exposure

@dataclass
class SignalQuality:
    """Signal quality assessment"""
    confidence_score: float
    strategy_performance: float
    market_regime_score: float
    volatility_adjustment: float
    time_decay_factor: float
    composite_score: float

class CapitalAllocator:
    """
    Dynamic Capital Allocator - The Brain's Risk Management System
    
    Calculates optimal position sizes based on:
    - Signal quality and confidence
    - Strategy historical performance
    - Current market regime
    - Portfolio heat and exposure
    - Risk management parameters
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize Capital Allocator"""
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Default allocation parameters
        self.params = AllocationParams()
        
        # Strategy performance tracking
        self.strategy_performance = {
            'memecoin_hunter': 0.75,
            'governance_alpha_hunter': 0.85,
            'high_vol_sniper': 0.65,
            'sol_momentum_trader': 0.70
        }
        
        # Market regime detection (enhanced with 7 regimes)
        self.market_regimes = {
            'bull_strong': 1.5,      # Strong bull - increase allocation significantly
            'bull_weak': 1.2,        # Weak bull - moderate increase
            'bear_strong': 0.3,      # Strong bear - drastically reduce
            'bear_weak': 0.6,        # Weak bear - reduce allocation
            'sideways': 0.8,         # Sideways - conservative
            'high_volatility': 0.4,  # High vol - very conservative
            'crash': 0.1,            # Crash - minimal allocation
            'bull_market': 1.2,      # Legacy compatibility
            'bear_market': 0.6,      # Legacy compatibility
            'unknown': 1.0           # Default multiplier
        }
        
        # Portfolio tracking
        self.current_exposure = 0.0
        self.max_portfolio_heat = 0.6  # Maximum 60% portfolio exposure
        
        logger.info("🧠 Dynamic Capital Allocator initialized")
        logger.info(f"📊 Max allocation: {self.params.max_allocation:.1%}")
        logger.info(f"🎯 Confidence threshold: {self.params.confidence_threshold:.2f}")
    
    def calculate_position_size(self, 
                              signal_confidence: float,
                              strategy: str,
                              market_data: Optional[Dict[str, Any]] = None) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate optimal position size based on signal quality
        
        Args:
            signal_confidence: Signal confidence score (0.0 to 1.0)
            strategy: Trading strategy name
            market_data: Optional market context data
            
        Returns:
            Tuple of (position_size_percentage, allocation_details)
        """
        try:
            # Step 1: Assess signal quality
            signal_quality = self.assess_signal_quality(signal_confidence, strategy, market_data)
            
            # Step 2: Check if signal meets minimum threshold
            if signal_quality.composite_score < self.params.confidence_threshold:
                logger.info(f"🚫 Signal below threshold: {signal_quality.composite_score:.2f} < {self.params.confidence_threshold:.2f}")
                return 0.0, {"reason": "below_threshold", "composite_score": signal_quality.composite_score}
            
            # Step 3: Calculate base allocation using logarithmic curve
            base_allocation = self.calculate_base_allocation(signal_quality.composite_score)
            
            # Step 4: Apply strategy performance multiplier
            strategy_multiplier = self.strategy_performance.get(strategy, 0.5)
            strategy_adjusted = base_allocation * strategy_multiplier
            
            # Step 5: Apply market regime adjustment
            market_regime = self.detect_market_regime(market_data)
            regime_multiplier = self.market_regimes.get(market_regime, 1.0)
            regime_adjusted = strategy_adjusted * regime_multiplier
            
            # Step 6: Apply portfolio heat check
            portfolio_adjusted = self.apply_portfolio_heat_limit(regime_adjusted)
            
            # Step 7: Apply final bounds
            final_allocation = max(
                self.params.min_allocation,
                min(portfolio_adjusted, self.params.max_allocation)
            )
            
            # Create allocation details
            allocation_details = {
                "signal_confidence": signal_confidence,
                "composite_score": signal_quality.composite_score,
                "base_allocation": base_allocation,
                "strategy": strategy,
                "strategy_multiplier": strategy_multiplier,
                "market_regime": market_regime,
                "regime_multiplier": regime_multiplier,
                "portfolio_heat": self.current_exposure,
                "final_allocation": final_allocation,
                "allocation_reasoning": self.get_allocation_reasoning(signal_quality, final_allocation)
            }
            
            logger.info(f"💰 Position size calculated: {final_allocation:.1%}")
            logger.info(f"   Strategy: {strategy}")
            logger.info(f"   Confidence: {signal_confidence:.2f}")
            logger.info(f"   Composite Score: {signal_quality.composite_score:.2f}")
            logger.info(f"   Market Regime: {market_regime}")
            
            return final_allocation, allocation_details
            
        except Exception as e:
            logger.error(f"❌ Error calculating position size: {e}")
            return self.params.min_allocation, {"error": str(e)}
    
    def assess_signal_quality(self, 
                            confidence: float, 
                            strategy: str, 
                            market_data: Optional[Dict[str, Any]]) -> SignalQuality:
        """Assess overall signal quality"""
        
        # Base confidence score
        confidence_score = confidence
        
        # Strategy performance factor
        strategy_performance = self.strategy_performance.get(strategy, 0.5)
        
        # Market regime score (simplified for now)
        market_regime_score = 0.8  # Default neutral
        
        # Volatility adjustment (reduce allocation in high volatility)
        volatility_adjustment = 0.9  # Default slight reduction
        
        # Time decay factor (signals get weaker over time)
        time_decay_factor = 1.0  # No decay for immediate signals
        
        # Calculate composite score using weighted average
        composite_score = (
            confidence_score * 0.4 +           # 40% signal confidence
            strategy_performance * 0.3 +       # 30% strategy track record
            market_regime_score * 0.2 +        # 20% market conditions
            volatility_adjustment * 0.1        # 10% volatility adjustment
        ) * time_decay_factor
        
        return SignalQuality(
            confidence_score=confidence_score,
            strategy_performance=strategy_performance,
            market_regime_score=market_regime_score,
            volatility_adjustment=volatility_adjustment,
            time_decay_factor=time_decay_factor,
            composite_score=composite_score
        )
    
    def calculate_base_allocation(self, composite_score: float) -> float:
        """Calculate base allocation using logarithmic curve"""

        # Logarithmic allocation curve for better risk management
        # Maps 0.5-1.0 confidence to allocation percentages

        if composite_score < 0.5:
            return 0.0
        elif composite_score < 0.6:
            return 0.01  # 1%
        elif composite_score < 0.7:
            return 0.02  # 2%
        elif composite_score < 0.8:
            return 0.05  # 5%
        elif composite_score < 0.9:
            return 0.10  # 10%
        elif composite_score < 0.95:
            return 0.18  # 18%
        else:
            return 0.25  # 25% for highest confidence signals
    
    def detect_market_regime(self, market_data: Optional[Dict[str, Any]]) -> str:
        """Detect current market regime using advanced detector"""

        try:
            # Try to get regime from Redis (from Market Regime Detector)
            regime_data = self.redis_client.get("overmind:current_regime")

            if regime_data and isinstance(regime_data, str):
                regime_info = json.loads(regime_data)
                regime = regime_info.get('regime', 'unknown')
                confidence = regime_info.get('confidence', 0.0)

                # Use advanced regime if confidence is high
                if confidence > 0.6:
                    logger.info(f"📊 Using advanced regime detection: {regime} (confidence: {confidence:.2f})")
                    return regime

            # Fallback to simple detection if advanced detector unavailable
            if not market_data:
                return 'unknown'

            # Simple regime detection as fallback
            try:
                # Check for high volatility
                volatility = market_data.get('volatility', 0.0)
                if volatility > 0.8:
                    return 'high_volatility'

                # Check price trend
                price_change_24h = market_data.get('price_change_24h', 0.0)
                if price_change_24h > 10:
                    return 'bull_strong'
                elif price_change_24h > 2:
                    return 'bull_weak'
                elif price_change_24h < -10:
                    return 'bear_strong'
                elif price_change_24h < -2:
                    return 'bear_weak'
                else:
                    return 'sideways'

            except Exception as e:
                logger.warning(f"⚠️ Error in fallback regime detection: {e}")
                return 'unknown'

        except Exception as e:
            logger.warning(f"⚠️ Error detecting market regime: {e}")
            return 'unknown'
    
    def apply_portfolio_heat_limit(self, allocation: float) -> float:
        """Apply portfolio heat limits to prevent overexposure"""

        # Check current portfolio exposure
        remaining_capacity = self.max_portfolio_heat - self.current_exposure

        if remaining_capacity <= 0:
            logger.warning("🔥 Portfolio heat limit reached - no new positions")
            return 0.0

        # Limit allocation to remaining capacity
        limited_allocation = min(allocation, remaining_capacity)

        if limited_allocation < allocation:
            logger.info(f"🔥 Portfolio heat limit applied: {allocation:.1%} → {limited_allocation:.1%}")

        # Ensure we don't go below minimum allocation unless we're at heat limit
        if limited_allocation > 0 and limited_allocation < self.params.min_allocation:
            if remaining_capacity >= self.params.min_allocation:
                limited_allocation = self.params.min_allocation
            else:
                limited_allocation = 0.0

        return limited_allocation
    
    def get_allocation_reasoning(self, signal_quality: SignalQuality, final_allocation: float) -> str:
        """Generate human-readable allocation reasoning"""
        
        if final_allocation == 0.0:
            return "No allocation - signal below confidence threshold"
        
        confidence_level = "HIGH" if signal_quality.confidence_score > 0.8 else "MEDIUM" if signal_quality.confidence_score > 0.6 else "LOW"
        allocation_level = "LARGE" if final_allocation > 0.1 else "MEDIUM" if final_allocation > 0.03 else "SMALL"
        
        return f"{allocation_level} allocation ({final_allocation:.1%}) based on {confidence_level} confidence signal with composite score {signal_quality.composite_score:.2f}"
    
    def update_portfolio_exposure(self, new_position_size: float):
        """Update current portfolio exposure tracking"""
        self.current_exposure += new_position_size
        self.current_exposure = max(0.0, min(self.current_exposure, 1.0))  # Clamp to 0-100%
        
        logger.info(f"📊 Portfolio exposure updated: {self.current_exposure:.1%}")
    
    def update_strategy_performance(self, strategy: str, success: bool, profit: float):
        """Update strategy performance tracking"""
        
        # Simple performance update (in production, use more sophisticated tracking)
        current_performance = self.strategy_performance.get(strategy, 0.5)
        
        if success and profit > 0:
            # Increase performance score
            new_performance = min(1.0, current_performance + 0.05)
        else:
            # Decrease performance score
            new_performance = max(0.1, current_performance - 0.03)
        
        self.strategy_performance[strategy] = new_performance
        
        logger.info(f"📈 Strategy performance updated: {strategy} → {new_performance:.2f}")
    
    def get_allocation_stats(self) -> Dict[str, Any]:
        """Get current allocation statistics"""
        return {
            "current_exposure": self.current_exposure,
            "max_portfolio_heat": self.max_portfolio_heat,
            "remaining_capacity": self.max_portfolio_heat - self.current_exposure,
            "strategy_performance": self.strategy_performance,
            "allocation_params": {
                "max_allocation": self.params.max_allocation,
                "min_allocation": self.params.min_allocation,
                "confidence_threshold": self.params.confidence_threshold
            }
        }

# Factory function
def create_capital_allocator() -> CapitalAllocator:
    """Create capital allocator instance"""
    return CapitalAllocator()

# Example usage and testing
if __name__ == "__main__":
    def test_capital_allocator():
        """Test capital allocator functionality"""
        allocator = create_capital_allocator()
        
        # Test different signal qualities
        test_cases = [
            (0.4, "memecoin_hunter", "Below threshold"),
            (0.6, "memecoin_hunter", "Medium confidence"),
            (0.8, "governance_alpha_hunter", "High confidence"),
            (0.95, "governance_alpha_hunter", "Very high confidence"),
            (0.7, "high_vol_sniper", "Medium confidence different strategy")
        ]
        
        print("=== CAPITAL ALLOCATOR TEST ===")
        
        for confidence, strategy, description in test_cases:
            allocation, details = allocator.calculate_position_size(
                signal_confidence=confidence,
                strategy=strategy,
                market_data={"price_change_24h": 5.0, "volatility": 0.3}
            )
            
            print(f"\n{description}:")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Strategy: {strategy}")
            print(f"  Allocation: {allocation:.1%}")
            print(f"  Reasoning: {details.get('allocation_reasoning', 'N/A')}")
        
        # Test stats
        print("\n=== ALLOCATION STATS ===")
        stats = allocator.get_allocation_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
    
    test_capital_allocator()
