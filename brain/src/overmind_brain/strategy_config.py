"""
THE OVERMIND PROTOCOL - Strategy Configuration Manager
Handles loading and validation of trading strategies and their parameters
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """Available trading strategies"""
    SOUL_METEOR = "soul_meteor"
    METEORA_DAMM_V2 = "meteora_damm_v2"
    DEVELOPER_TRACKING = "developer_tracking"
    MEMECOIN_HUNTER = "memecoin_hunter"

@dataclass
class StrategyParameters:
    """Base class for strategy parameters"""
    strategy_type: StrategyType
    enabled: bool = True

@dataclass
class SoulMeteorParams(StrategyParameters):
    """Soul Meteor strategy parameters"""
    min_volume: float = 100000.0
    min_liquidity: float = 50000.0
    max_risk_per_trade: float = 0.02
    confidence_threshold: float = 0.7
    
    def __post_init__(self):
        self.strategy_type = StrategyType.SOUL_METEOR

@dataclass
class MeteoraDammV2Params(StrategyParameters):
    """Meteora DAMM V2 strategy parameters"""
    min_liquidity: float = 50000.0
    min_pool_age_hours: int = 24
    max_slippage: float = 0.01
    confidence_threshold: float = 0.75
    
    def __post_init__(self):
        self.strategy_type = StrategyType.METEORA_DAMM_V2

@dataclass
class DeveloperTrackingParams(StrategyParameters):
    """Developer tracking strategy parameters"""
    min_score: float = 7.0
    min_previous_launches: int = 3
    max_dev_risk_exposure: float = 0.15
    confidence_threshold: float = 0.8
    
    def __post_init__(self):
        self.strategy_type = StrategyType.DEVELOPER_TRACKING

@dataclass
class MemecoinHunterParams(StrategyParameters):
    """Memecoin hunter strategy parameters"""
    max_market_cap: float = 1000000.0
    min_social_score: float = 5.0
    max_age_hours: int = 72
    min_holders: int = 100
    confidence_threshold: float = 0.65
    
    def __post_init__(self):
        self.strategy_type = StrategyType.MEMECOIN_HUNTER

class StrategyConfigManager:
    """Manages loading and validation of strategy configurations"""
    
    def __init__(self):
        self.enabled_strategies: List[StrategyType] = []
        self.strategy_params: Dict[StrategyType, StrategyParameters] = {}
        self.default_strategy: Optional[StrategyType] = None
        self._load_configuration()
    
    def _load_configuration(self):
        """Load strategy configuration from environment variables"""
        logger.info("🔧 Loading strategy configuration from environment...")
        
        # Load enabled strategies
        enabled_strategies_str = os.getenv("ENABLED_STRATEGIES", "soul_meteor")
        enabled_strategy_names = [s.strip() for s in enabled_strategies_str.split(",")]
        
        self.enabled_strategies = []
        for strategy_name in enabled_strategy_names:
            try:
                strategy_type = StrategyType(strategy_name)
                self.enabled_strategies.append(strategy_type)
                logger.info(f"✅ Enabled strategy: {strategy_name}")
            except ValueError:
                logger.warning(f"⚠️ Unknown strategy: {strategy_name}")
        
        # Load default strategy
        default_strategy_str = os.getenv("DEFAULT_STRATEGY", "soul_meteor")
        try:
            self.default_strategy = StrategyType(default_strategy_str)
            logger.info(f"🎯 Default strategy: {default_strategy_str}")
        except ValueError:
            logger.warning(f"⚠️ Invalid default strategy: {default_strategy_str}")
            if self.enabled_strategies:
                self.default_strategy = self.enabled_strategies[0]
        
        # Load strategy parameters
        self._load_strategy_parameters()
        
        logger.info(f"📊 Strategy configuration loaded: {len(self.enabled_strategies)} strategies enabled")
    
    def _load_strategy_parameters(self):
        """Load parameters for each strategy"""
        
        # Soul Meteor parameters
        if StrategyType.SOUL_METEOR in self.enabled_strategies:
            soul_meteor_params = SoulMeteorParams(
                strategy_type=StrategyType.SOUL_METEOR,
                min_volume=float(os.getenv("SOUL_METEOR_MIN_VOLUME", "100000")),
                min_liquidity=float(os.getenv("SOUL_METEOR_MIN_LIQUIDITY", "50000")),
                max_risk_per_trade=float(os.getenv("SOUL_METEOR_MAX_RISK", "0.02")),
                confidence_threshold=float(os.getenv("SOUL_METEOR_CONFIDENCE", "0.7"))
            )
            self.strategy_params[StrategyType.SOUL_METEOR] = soul_meteor_params
            logger.info(f"📈 Soul Meteor params: vol≥{soul_meteor_params.min_volume}, liq≥{soul_meteor_params.min_liquidity}")
        
        # Meteora DAMM V2 parameters
        if StrategyType.METEORA_DAMM_V2 in self.enabled_strategies:
            meteora_params = MeteoraDammV2Params(
                strategy_type=StrategyType.METEORA_DAMM_V2,
                min_liquidity=float(os.getenv("METEORA_DAMM_V2_MIN_LIQUIDITY", "50000")),
                min_pool_age_hours=int(os.getenv("METEORA_DAMM_V2_MIN_AGE", "24")),
                max_slippage=float(os.getenv("METEORA_DAMM_V2_MAX_SLIPPAGE", "0.01")),
                confidence_threshold=float(os.getenv("METEORA_DAMM_V2_CONFIDENCE", "0.75"))
            )
            self.strategy_params[StrategyType.METEORA_DAMM_V2] = meteora_params
            logger.info(f"🌊 Meteora DAMM V2 params: liq≥{meteora_params.min_liquidity}, age≥{meteora_params.min_pool_age_hours}h")
        
        # Developer Tracking parameters
        if StrategyType.DEVELOPER_TRACKING in self.enabled_strategies:
            dev_tracking_params = DeveloperTrackingParams(
                strategy_type=StrategyType.DEVELOPER_TRACKING,
                min_score=float(os.getenv("DEVELOPER_TRACKING_MIN_SCORE", "7.0")),
                min_previous_launches=int(os.getenv("DEVELOPER_TRACKING_MIN_LAUNCHES", "3")),
                max_dev_risk_exposure=float(os.getenv("DEVELOPER_TRACKING_MAX_EXPOSURE", "0.15")),
                confidence_threshold=float(os.getenv("DEVELOPER_TRACKING_CONFIDENCE", "0.8"))
            )
            self.strategy_params[StrategyType.DEVELOPER_TRACKING] = dev_tracking_params
            logger.info(f"👨‍💻 Developer Tracking params: score≥{dev_tracking_params.min_score}, launches≥{dev_tracking_params.min_previous_launches}")
        
        # Memecoin Hunter parameters
        if StrategyType.MEMECOIN_HUNTER in self.enabled_strategies:
            memecoin_params = MemecoinHunterParams(
                strategy_type=StrategyType.MEMECOIN_HUNTER,
                max_market_cap=float(os.getenv("MEMECOIN_HUNTER_MAX_MARKET_CAP", "1000000")),
                min_social_score=float(os.getenv("MEMECOIN_HUNTER_MIN_SOCIAL", "5.0")),
                max_age_hours=int(os.getenv("MEMECOIN_HUNTER_MAX_AGE", "72")),
                min_holders=int(os.getenv("MEMECOIN_HUNTER_MIN_HOLDERS", "100")),
                confidence_threshold=float(os.getenv("MEMECOIN_HUNTER_CONFIDENCE", "0.65"))
            )
            self.strategy_params[StrategyType.MEMECOIN_HUNTER] = memecoin_params
            logger.info(f"🐕 Memecoin Hunter params: mcap≤{memecoin_params.max_market_cap}, social≥{memecoin_params.min_social_score}")
    
    def get_enabled_strategies(self) -> List[StrategyType]:
        """Get list of enabled strategies"""
        return self.enabled_strategies.copy()
    
    def get_strategy_params(self, strategy_type: StrategyType) -> Optional[StrategyParameters]:
        """Get parameters for specific strategy"""
        return self.strategy_params.get(strategy_type)
    
    def is_strategy_enabled(self, strategy_type: StrategyType) -> bool:
        """Check if strategy is enabled"""
        return strategy_type in self.enabled_strategies
    
    def get_default_strategy(self) -> Optional[StrategyType]:
        """Get default strategy"""
        return self.default_strategy
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            "enabled_strategies": [s.value for s in self.enabled_strategies],
            "default_strategy": self.default_strategy.value if self.default_strategy else None,
            "strategy_count": len(self.enabled_strategies),
            "parameters": {
                strategy.value: {
                    "confidence_threshold": params.confidence_threshold,
                    "strategy_specific": self._get_strategy_specific_params(params)
                }
                for strategy, params in self.strategy_params.items()
            }
        }
    
    def _get_strategy_specific_params(self, params: StrategyParameters) -> Dict[str, Any]:
        """Extract strategy-specific parameters for summary"""
        if isinstance(params, SoulMeteorParams):
            return {
                "min_volume": params.min_volume,
                "min_liquidity": params.min_liquidity,
                "max_risk_per_trade": params.max_risk_per_trade
            }
        elif isinstance(params, MeteoraDammV2Params):
            return {
                "min_liquidity": params.min_liquidity,
                "min_pool_age_hours": params.min_pool_age_hours,
                "max_slippage": params.max_slippage
            }
        elif isinstance(params, DeveloperTrackingParams):
            return {
                "min_score": params.min_score,
                "min_previous_launches": params.min_previous_launches,
                "max_dev_risk_exposure": params.max_dev_risk_exposure
            }
        elif isinstance(params, MemecoinHunterParams):
            return {
                "max_market_cap": params.max_market_cap,
                "min_social_score": params.min_social_score,
                "max_age_hours": params.max_age_hours,
                "min_holders": params.min_holders
            }
        return {}

# Global strategy configuration manager
strategy_config = StrategyConfigManager()