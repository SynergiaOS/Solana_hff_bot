"""
THE OVERMIND PROTOCOL - Strategy Manager
Intelligent strategy selection and validation based on market signals
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from .strategy_config import (
    StrategyConfigManager, StrategyType, StrategyParameters,
    SoulMeteorParams, MeteoraDammV2Params, DeveloperTrackingParams, MemecoinHunterParams
)

logger = logging.getLogger(__name__)

@dataclass
class MarketSignal:
    """Standardized market signal structure"""
    signal_id: str
    signal_type: str
    symbol: str
    token_address: Optional[str] = None
    price: Optional[float] = None
    volume_24h: Optional[float] = None
    liquidity: Optional[float] = None
    market_cap: Optional[float] = None
    holder_count: Optional[int] = None
    pool_age_hours: Optional[float] = None
    developer_score: Optional[float] = None
    social_score: Optional[float] = None
    confidence: float = 0.5
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class StrategyMatch:
    """Result of strategy matching process"""
    strategy_type: StrategyType
    strategy_params: StrategyParameters
    match_score: float
    validation_results: Dict[str, bool]
    reasoning: str

class StrategyManager:
    """Manages strategy selection and validation for trading signals"""
    
    def __init__(self):
        self.config_manager = StrategyConfigManager()
        logger.info("🎯 Strategy Manager initialized with configuration")
    
    def select_and_validate_strategies(self, signal_data: Dict[str, Any]) -> List[StrategyMatch]:
        """
        Main entry point: Select and validate strategies for a given signal
        
        Args:
            signal_data: Raw signal data from market
            
        Returns:
            List of validated strategy matches
        """
        # Convert raw signal to structured format
        signal = self._parse_signal(signal_data)
        
        logger.info(f"🔍 Analyzing signal {signal.signal_id} for strategy matching")
        logger.info(f"📊 Signal: {signal.symbol} | Type: {signal.signal_type} | Vol: {signal.volume_24h}")
        
        # Get enabled strategies
        enabled_strategies = self.config_manager.get_enabled_strategies()
        
        if not enabled_strategies:
            logger.warning("⚠️ No strategies enabled - returning empty list")
            return []
        
        # Validate each strategy against the signal
        strategy_matches = []
        
        for strategy_type in enabled_strategies:
            strategy_params = self.config_manager.get_strategy_params(strategy_type)
            if not strategy_params:
                continue
            
            # Validate strategy compatibility with signal
            match = self._validate_strategy_for_signal(strategy_type, strategy_params, signal)
            
            if match:
                strategy_matches.append(match)
                logger.info(f"✅ Strategy {strategy_type.value} qualified with score {match.match_score:.2f}")
            else:
                logger.info(f"❌ Strategy {strategy_type.value} disqualified")
        
        # Sort by match score (highest first)
        strategy_matches.sort(key=lambda x: x.match_score, reverse=True)
        
        logger.info(f"🎯 Strategy selection complete: {len(strategy_matches)}/{len(enabled_strategies)} strategies qualified")
        
        return strategy_matches
    
    def _parse_signal(self, signal_data: Dict[str, Any]) -> MarketSignal:
        """Parse raw signal data into structured MarketSignal"""
        
        # Extract market data if available
        market_data = signal_data.get("market_data", {})
        
        return MarketSignal(
            signal_id=signal_data.get("signal_id", f"signal_{datetime.now().timestamp()}"),
            signal_type=signal_data.get("signal_type", "unknown"),
            symbol=signal_data.get("symbol", ""),
            token_address=signal_data.get("token_address"),
            price=market_data.get("price") or signal_data.get("price"),
            volume_24h=market_data.get("volume_24h") or signal_data.get("volume"),
            liquidity=market_data.get("liquidity") or signal_data.get("liquidity"),
            market_cap=market_data.get("market_cap") or signal_data.get("market_cap"),
            holder_count=market_data.get("holders") or signal_data.get("holders"),
            pool_age_hours=signal_data.get("pool_age_hours"),
            developer_score=signal_data.get("developer_score"),
            social_score=signal_data.get("social_score"),
            confidence=signal_data.get("confidence", 0.5),
            timestamp=datetime.now(),
            metadata=signal_data.get("metadata", {})
        )
    
    def _validate_strategy_for_signal(
        self, 
        strategy_type: StrategyType, 
        strategy_params: StrategyParameters, 
        signal: MarketSignal
    ) -> Optional[StrategyMatch]:
        """Validate if a strategy is applicable to a signal"""
        
        if strategy_type == StrategyType.SOUL_METEOR:
            return self._validate_soul_meteor(strategy_params, signal)
        elif strategy_type == StrategyType.METEORA_DAMM_V2:
            return self._validate_meteora_damm_v2(strategy_params, signal)
        elif strategy_type == StrategyType.DEVELOPER_TRACKING:
            return self._validate_developer_tracking(strategy_params, signal)
        elif strategy_type == StrategyType.MEMECOIN_HUNTER:
            return self._validate_memecoin_hunter(strategy_params, signal)
        
        return None
    
    def _validate_soul_meteor(self, params: SoulMeteorParams, signal: MarketSignal) -> Optional[StrategyMatch]:
        """Validate Soul Meteor strategy against signal"""
        validation_results = {}
        reasoning_parts = []
        match_score = 0.0
        
        # Volume validation
        if signal.volume_24h is not None:
            volume_passed = signal.volume_24h >= params.min_volume
            validation_results["volume_check"] = volume_passed
            if volume_passed:
                match_score += 0.3
                reasoning_parts.append(f"Volume ${signal.volume_24h:,.0f} ≥ ${params.min_volume:,.0f} ✅")
            else:
                reasoning_parts.append(f"Volume ${signal.volume_24h:,.0f} < ${params.min_volume:,.0f} ❌")
                return None  # Hard requirement
        else:
            reasoning_parts.append("Volume data unavailable ⚠️")
        
        # Liquidity validation
        if signal.liquidity is not None:
            liquidity_passed = signal.liquidity >= params.min_liquidity
            validation_results["liquidity_check"] = liquidity_passed
            if liquidity_passed:
                match_score += 0.3
                reasoning_parts.append(f"Liquidity ${signal.liquidity:,.0f} ≥ ${params.min_liquidity:,.0f} ✅")
            else:
                reasoning_parts.append(f"Liquidity ${signal.liquidity:,.0f} < ${params.min_liquidity:,.0f} ❌")
                return None  # Hard requirement
        else:
            reasoning_parts.append("Liquidity data unavailable ⚠️")
        
        # Signal type compatibility
        compatible_types = ["new_pool_detected", "volume_spike", "price_momentum"]
        if signal.signal_type in compatible_types:
            validation_results["signal_type_check"] = True
            match_score += 0.2
            reasoning_parts.append(f"Signal type '{signal.signal_type}' compatible ✅")
        else:
            validation_results["signal_type_check"] = False
            reasoning_parts.append(f"Signal type '{signal.signal_type}' not optimal for Soul Meteor ⚠️")
        
        # Confidence check
        if signal.confidence >= params.confidence_threshold:
            validation_results["confidence_check"] = True
            match_score += 0.2
            reasoning_parts.append(f"Confidence {signal.confidence:.2f} ≥ {params.confidence_threshold:.2f} ✅")
        else:
            reasoning_parts.append(f"Confidence {signal.confidence:.2f} < {params.confidence_threshold:.2f} ❌")
            return None  # Hard requirement
        
        # Only return match if basic requirements are met
        if match_score >= 0.5:
            return StrategyMatch(
                strategy_type=StrategyType.SOUL_METEOR,
                strategy_params=params,
                match_score=match_score,
                validation_results=validation_results,
                reasoning=" | ".join(reasoning_parts)
            )
        
        return None
    
    def _validate_meteora_damm_v2(self, params: MeteoraDammV2Params, signal: MarketSignal) -> Optional[StrategyMatch]:
        """Validate Meteora DAMM V2 strategy against signal"""
        validation_results = {}
        reasoning_parts = []
        match_score = 0.0
        
        # Liquidity validation
        if signal.liquidity is not None:
            liquidity_passed = signal.liquidity >= params.min_liquidity
            validation_results["liquidity_check"] = liquidity_passed
            if liquidity_passed:
                match_score += 0.4
                reasoning_parts.append(f"Liquidity ${signal.liquidity:,.0f} ≥ ${params.min_liquidity:,.0f} ✅")
            else:
                reasoning_parts.append(f"Liquidity ${signal.liquidity:,.0f} < ${params.min_liquidity:,.0f} ❌")
                return None
        
        # Pool age validation
        if signal.pool_age_hours is not None:
            age_passed = signal.pool_age_hours >= params.min_pool_age_hours
            validation_results["pool_age_check"] = age_passed
            if age_passed:
                match_score += 0.3
                reasoning_parts.append(f"Pool age {signal.pool_age_hours:.1f}h ≥ {params.min_pool_age_hours}h ✅")
            else:
                reasoning_parts.append(f"Pool age {signal.pool_age_hours:.1f}h < {params.min_pool_age_hours}h ❌")
                return None
        
        # Signal type compatibility (Meteora prefers established pools)
        compatible_types = ["liquidity_change", "established_pool", "stable_trading"]
        if signal.signal_type in compatible_types:
            validation_results["signal_type_check"] = True
            match_score += 0.3
            reasoning_parts.append(f"Signal type '{signal.signal_type}' optimal for Meteora ✅")
        
        if match_score >= 0.5:
            return StrategyMatch(
                strategy_type=StrategyType.METEORA_DAMM_V2,
                strategy_params=params,
                match_score=match_score,
                validation_results=validation_results,
                reasoning=" | ".join(reasoning_parts)
            )
        
        return None
    
    def _validate_developer_tracking(self, params: DeveloperTrackingParams, signal: MarketSignal) -> Optional[StrategyMatch]:
        """Validate Developer Tracking strategy against signal"""
        validation_results = {}
        reasoning_parts = []
        match_score = 0.0
        
        # Developer score validation
        if signal.developer_score is not None:
            score_passed = signal.developer_score >= params.min_score
            validation_results["developer_score_check"] = score_passed
            if score_passed:
                match_score += 0.5
                reasoning_parts.append(f"Developer score {signal.developer_score:.1f} ≥ {params.min_score:.1f} ✅")
            else:
                reasoning_parts.append(f"Developer score {signal.developer_score:.1f} < {params.min_score:.1f} ❌")
                return None
        else:
            reasoning_parts.append("Developer score unavailable ❌")
            return None  # Hard requirement for this strategy
        
        # Signal type compatibility
        compatible_types = ["developer_launch", "team_token", "verified_project"]
        if signal.signal_type in compatible_types:
            validation_results["signal_type_check"] = True
            match_score += 0.3
            reasoning_parts.append(f"Signal type '{signal.signal_type}' perfect for Developer Tracking ✅")
        
        # Confidence check
        if signal.confidence >= params.confidence_threshold:
            validation_results["confidence_check"] = True
            match_score += 0.2
            reasoning_parts.append(f"Confidence {signal.confidence:.2f} ≥ {params.confidence_threshold:.2f} ✅")
        
        if match_score >= 0.5:
            return StrategyMatch(
                strategy_type=StrategyType.DEVELOPER_TRACKING,
                strategy_params=params,
                match_score=match_score,
                validation_results=validation_results,
                reasoning=" | ".join(reasoning_parts)
            )
        
        return None
    
    def _validate_memecoin_hunter(self, params: MemecoinHunterParams, signal: MarketSignal) -> Optional[StrategyMatch]:
        """Validate Memecoin Hunter strategy against signal"""
        validation_results = {}
        reasoning_parts = []
        match_score = 0.0
        
        # Market cap validation
        if signal.market_cap is not None:
            mcap_passed = signal.market_cap <= params.max_market_cap
            validation_results["market_cap_check"] = mcap_passed
            if mcap_passed:
                match_score += 0.3
                reasoning_parts.append(f"Market cap ${signal.market_cap:,.0f} ≤ ${params.max_market_cap:,.0f} ✅")
            else:
                reasoning_parts.append(f"Market cap ${signal.market_cap:,.0f} > ${params.max_market_cap:,.0f} ❌")
                return None
        
        # Social score validation
        if signal.social_score is not None:
            social_passed = signal.social_score >= params.min_social_score
            validation_results["social_score_check"] = social_passed
            if social_passed:
                match_score += 0.3
                reasoning_parts.append(f"Social score {signal.social_score:.1f} ≥ {params.min_social_score:.1f} ✅")
            else:
                reasoning_parts.append(f"Social score {signal.social_score:.1f} < {params.min_social_score:.1f} ❌")
        
        # Holder count validation
        if signal.holder_count is not None:
            holders_passed = signal.holder_count >= params.min_holders
            validation_results["holders_check"] = holders_passed
            if holders_passed:
                match_score += 0.2
                reasoning_parts.append(f"Holders {signal.holder_count} ≥ {params.min_holders} ✅")
            else:
                reasoning_parts.append(f"Holders {signal.holder_count} < {params.min_holders} ❌")
        
        # Signal type compatibility
        compatible_types = ["new_token", "viral_potential", "community_growth", "social_momentum"]
        if signal.signal_type in compatible_types:
            validation_results["signal_type_check"] = True
            match_score += 0.2
            reasoning_parts.append(f"Signal type '{signal.signal_type}' ideal for Memecoin Hunter ✅")
        
        if match_score >= 0.4:  # Lower threshold for memecoins (higher risk tolerance)
            return StrategyMatch(
                strategy_type=StrategyType.MEMECOIN_HUNTER,
                strategy_params=params,
                match_score=match_score,
                validation_results=validation_results,
                reasoning=" | ".join(reasoning_parts)
            )
        
        return None
    
    def generate_strategy_context_for_ai(self, strategy_matches: List[StrategyMatch], signal: MarketSignal) -> str:
        """Generate context prompt for AI decision making based on qualified strategies"""
        
        if not strategy_matches:
            return "No trading strategies qualified for this signal. Recommend HOLD action."
        
        context_parts = [
            f"🎯 STRATEGY ANALYSIS for {signal.symbol} ({signal.signal_type})",
            f"📊 Signal Data: Price=${signal.price or 'N/A'}, Volume=${signal.volume_24h or 'N/A'}, Liquidity=${signal.liquidity or 'N/A'}",
            "",
            f"✅ QUALIFIED STRATEGIES ({len(strategy_matches)}):"
        ]
        
        for i, match in enumerate(strategy_matches, 1):
            context_parts.extend([
                f"{i}. {match.strategy_type.value.upper()} (Score: {match.match_score:.2f})",
                f"   📋 {match.reasoning}",
                f"   🎯 Confidence Threshold: {match.strategy_params.confidence_threshold:.2f}",
                ""
            ])
        
        context_parts.extend([
            "🤖 AI DECISION REQUIREMENTS:",
            "- Choose the most appropriate strategy based on match scores and signal characteristics",
            "- Consider risk management parameters for the selected strategy",
            "- Provide BUY/SELL/HOLD recommendation with confidence score",
            "- Justify decision based on strategy-specific criteria",
            "",
            f"📈 Current Signal Confidence: {signal.confidence:.2f}"
        ])
        
        return "\n".join(context_parts)
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get summary of current strategy configuration"""
        return self.config_manager.get_configuration_summary()

# Global strategy manager instance
strategy_manager = StrategyManager()