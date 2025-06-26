"""THE OVERMIND PROTOCOL - Strategy Profiles
Defines three distinct trading personalities for adaptive behavior based on portfolio progression.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """Available trading strategies."""
    MEMECOIN_HUNTER = "memecoin_hunter"
    SOUL_METEOR = "soul_meteor"
    DEVELOPER_TRACKING = "developer_tracking"
    METEORA_DAMM = "meteora_damm"
    CROSS_DEX_ARBITRAGE = "cross_dex_arbitrage"
    LIQUIDITY_SNIPING = "liquidity_sniping"
    MARKET_MAKING = "market_making"
    LOW_RISK_ARBITRAGE = "low_risk_arbitrage"

class ProfileType(Enum):
    """Trading profile types."""
    AGGRESSIVE_GROWTH = "aggressive_growth"
    BALANCED_RISK = "balanced_risk"
    CAPITAL_PRESERVATION = "capital_preservation"

@dataclass
class SignalProcessingRules:
    """Signal processing configuration for each profile."""
    min_confidence_threshold: float
    max_signals_per_hour: int
    signal_quality_weight: float
    volume_threshold_multiplier: float
    price_change_sensitivity: float
    social_sentiment_weight: float
    technical_analysis_weight: float

@dataclass
class PositionSizingRules:
    """Position sizing configuration for each profile."""
    base_position_size: float  # Percentage of portfolio
    max_position_size: float   # Maximum position size
    risk_per_trade: float      # Risk percentage per trade
    correlation_limit: float   # Maximum correlation between positions
    volatility_adjustment: bool # Adjust size based on volatility
    kelly_criterion_enabled: bool # Use Kelly criterion for sizing

@dataclass
class RiskParameters:
    """Risk management parameters for each profile."""
    risk_multiplier: float
    max_daily_loss: float
    max_drawdown: float
    stop_loss_percentage: float
    take_profit_percentage: float
    trailing_stop_enabled: bool
    position_timeout_hours: int
    emergency_exit_threshold: float

@dataclass
class StrategyProfile:
    """Complete strategy profile definition."""
    profile_type: ProfileType
    name: str
    description: str
    goal_progress_range: tuple  # (min_percentage, max_percentage)
    enabled_strategies: List[StrategyType]
    risk_parameters: RiskParameters
    position_sizing: PositionSizingRules
    signal_processing: SignalProcessingRules
    execution_priority: str  # LOW, MEDIUM, HIGH, URGENT
    rebalance_frequency_hours: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return asdict(self)
    
    def is_applicable_for_progress(self, progress_percentage: float) -> bool:
        """Check if this profile is applicable for the given progress percentage."""
        min_progress, max_progress = self.goal_progress_range
        return min_progress <= progress_percentage < max_progress

class AggressiveGrowthProfile:
    """AGGRESSIVE_GROWTH profile for 0-25% goal progress."""
    
    @staticmethod
    def create() -> StrategyProfile:
        """Create AGGRESSIVE_GROWTH strategy profile."""
        
        risk_parameters = RiskParameters(
            risk_multiplier=1.5,
            max_daily_loss=15.0,  # 15% max daily loss
            max_drawdown=25.0,    # 25% max drawdown
            stop_loss_percentage=8.0,  # 8% stop loss
            take_profit_percentage=25.0,  # 25% take profit
            trailing_stop_enabled=True,
            position_timeout_hours=24,  # 24 hour position timeout
            emergency_exit_threshold=20.0  # 20% emergency exit
        )
        
        position_sizing = PositionSizingRules(
            base_position_size=8.0,  # 8% base position
            max_position_size=10.0,  # 10% max position
            risk_per_trade=3.0,      # 3% risk per trade
            correlation_limit=0.7,   # 70% max correlation
            volatility_adjustment=True,
            kelly_criterion_enabled=True
        )
        
        signal_processing = SignalProcessingRules(
            min_confidence_threshold=0.6,  # 60% minimum confidence
            max_signals_per_hour=20,       # High frequency
            signal_quality_weight=0.7,
            volume_threshold_multiplier=1.5,
            price_change_sensitivity=1.2,
            social_sentiment_weight=0.8,   # High social weight
            technical_analysis_weight=0.6
        )
        
        return StrategyProfile(
            profile_type=ProfileType.AGGRESSIVE_GROWTH,
            name="Aggressive Growth Hunter",
            description="High-risk, high-reward profile focused on memecoin hunting and rapid growth opportunities. Suitable for early portfolio building phase (0-25% of goal).",
            goal_progress_range=(0.0, 25.0),
            enabled_strategies=[
                StrategyType.MEMECOIN_HUNTER,
                StrategyType.SOUL_METEOR,
                StrategyType.DEVELOPER_TRACKING
            ],
            risk_parameters=risk_parameters,
            position_sizing=position_sizing,
            signal_processing=signal_processing,
            execution_priority="HIGH",
            rebalance_frequency_hours=6  # Rebalance every 6 hours
        )

class BalancedRiskProfile:
    """BALANCED_RISK profile for 25-100% goal progress."""
    
    @staticmethod
    def create() -> StrategyProfile:
        """Create BALANCED_RISK strategy profile."""
        
        risk_parameters = RiskParameters(
            risk_multiplier=1.0,
            max_daily_loss=8.0,   # 8% max daily loss
            max_drawdown=15.0,    # 15% max drawdown
            stop_loss_percentage=5.0,  # 5% stop loss
            take_profit_percentage=15.0,  # 15% take profit
            trailing_stop_enabled=True,
            position_timeout_hours=48,  # 48 hour position timeout
            emergency_exit_threshold=12.0  # 12% emergency exit
        )
        
        position_sizing = PositionSizingRules(
            base_position_size=4.0,  # 4% base position
            max_position_size=5.0,   # 5% max position
            risk_per_trade=2.0,      # 2% risk per trade
            correlation_limit=0.5,   # 50% max correlation
            volatility_adjustment=True,
            kelly_criterion_enabled=True
        )
        
        signal_processing = SignalProcessingRules(
            min_confidence_threshold=0.7,  # 70% minimum confidence
            max_signals_per_hour=10,       # Moderate frequency
            signal_quality_weight=0.8,
            volume_threshold_multiplier=1.0,
            price_change_sensitivity=1.0,
            social_sentiment_weight=0.6,
            technical_analysis_weight=0.8  # Higher technical weight
        )
        
        return StrategyProfile(
            profile_type=ProfileType.BALANCED_RISK,
            name="Balanced Growth Optimizer",
            description="Moderate risk profile balancing growth and preservation. Focuses on arbitrage and systematic opportunities. Suitable for mid-stage portfolio growth (25-100% of goal).",
            goal_progress_range=(25.0, 100.0),
            enabled_strategies=[
                StrategyType.METEORA_DAMM,
                StrategyType.CROSS_DEX_ARBITRAGE,
                StrategyType.LIQUIDITY_SNIPING
            ],
            risk_parameters=risk_parameters,
            position_sizing=position_sizing,
            signal_processing=signal_processing,
            execution_priority="MEDIUM",
            rebalance_frequency_hours=12  # Rebalance every 12 hours
        )

class CapitalPreservationProfile:
    """CAPITAL_PRESERVATION profile for 100%+ goal progress."""
    
    @staticmethod
    def create() -> StrategyProfile:
        """Create CAPITAL_PRESERVATION strategy profile."""
        
        risk_parameters = RiskParameters(
            risk_multiplier=0.5,
            max_daily_loss=3.0,   # 3% max daily loss
            max_drawdown=8.0,     # 8% max drawdown
            stop_loss_percentage=2.0,  # 2% stop loss
            take_profit_percentage=8.0,   # 8% take profit
            trailing_stop_enabled=True,
            position_timeout_hours=72,  # 72 hour position timeout
            emergency_exit_threshold=5.0  # 5% emergency exit
        )
        
        position_sizing = PositionSizingRules(
            base_position_size=1.5,  # 1.5% base position
            max_position_size=2.0,   # 2% max position
            risk_per_trade=1.0,      # 1% risk per trade
            correlation_limit=0.3,   # 30% max correlation
            volatility_adjustment=True,
            kelly_criterion_enabled=False  # Conservative sizing
        )
        
        signal_processing = SignalProcessingRules(
            min_confidence_threshold=0.85,  # 85% minimum confidence
            max_signals_per_hour=5,         # Low frequency
            signal_quality_weight=0.9,
            volume_threshold_multiplier=0.8,
            price_change_sensitivity=0.8,
            social_sentiment_weight=0.3,    # Low social weight
            technical_analysis_weight=0.9   # High technical weight
        )
        
        return StrategyProfile(
            profile_type=ProfileType.CAPITAL_PRESERVATION,
            name="Capital Guardian",
            description="Conservative profile focused on capital preservation and steady returns. Emphasizes market making and low-risk arbitrage. Suitable for goal achievement phase (100%+ of goal).",
            goal_progress_range=(100.0, float('inf')),
            enabled_strategies=[
                StrategyType.MARKET_MAKING,
                StrategyType.LOW_RISK_ARBITRAGE
            ],
            risk_parameters=risk_parameters,
            position_sizing=position_sizing,
            signal_processing=signal_processing,
            execution_priority="LOW",
            rebalance_frequency_hours=24  # Rebalance every 24 hours
        )

class StrategyProfileManager:
    """Manager for strategy profiles."""
    
    def __init__(self):
        """Initialize the strategy profile manager."""
        self.profiles = {
            ProfileType.AGGRESSIVE_GROWTH: AggressiveGrowthProfile.create(),
            ProfileType.BALANCED_RISK: BalancedRiskProfile.create(),
            ProfileType.CAPITAL_PRESERVATION: CapitalPreservationProfile.create()
        }
        
        logger.info("📋 Strategy Profile Manager initialized with 3 profiles")
    
    def get_profile(self, profile_type: ProfileType) -> StrategyProfile:
        """Get a specific strategy profile."""
        return self.profiles[profile_type]
    
    def get_profile_for_progress(self, progress_percentage: float) -> StrategyProfile:
        """Get the appropriate profile for the given progress percentage."""
        for profile in self.profiles.values():
            if profile.is_applicable_for_progress(progress_percentage):
                return profile
        
        # Fallback to capital preservation if progress > 100%
        return self.profiles[ProfileType.CAPITAL_PRESERVATION]
    
    def get_all_profiles(self) -> Dict[ProfileType, StrategyProfile]:
        """Get all available profiles."""
        return self.profiles.copy()
    
    def validate_profile(self, profile: StrategyProfile) -> bool:
        """Validate a strategy profile configuration."""
        try:
            # Check required fields
            assert profile.profile_type in ProfileType
            assert len(profile.enabled_strategies) > 0
            assert 0 <= profile.risk_parameters.risk_multiplier <= 3.0
            assert 0 <= profile.position_sizing.max_position_size <= 20.0
            assert 0 <= profile.signal_processing.min_confidence_threshold <= 1.0
            
            return True
        except (AssertionError, AttributeError) as e:
            logger.error(f"❌ Profile validation failed: {e}")
            return False

# Global instance
strategy_profile_manager = StrategyProfileManager()
