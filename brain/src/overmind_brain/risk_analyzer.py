"""THE OVERMIND PROTOCOL - Risk Analyzer
AI-enhanced risk assessment for trading decisions with comprehensive risk metrics.
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

@dataclass
class RiskAssessment:
    """Comprehensive risk assessment result"""
    overall_risk_score: float  # 0.0 (low) to 1.0 (high)
    risk_level: str  # LOW, MEDIUM, HIGH, EXTREME
    risk_factors: List[str]
    position_size_recommendation: float
    stop_loss_recommendation: Optional[float]
    max_loss_estimate: float
    confidence_adjustment: float  # Factor to adjust decision confidence
    risk_metrics: Dict[str, float]
    warnings: List[str]
    timestamp: str

class RiskAnalyzer:
    """AI-enhanced risk analyzer for THE OVERMIND PROTOCOL"""
    
    def __init__(self, 
                 max_portfolio_risk: float = 0.02,  # 2% max portfolio risk per trade
                 max_position_size: float = 0.1,    # 10% max position size
                 volatility_threshold: float = 0.05, # 5% volatility threshold
                 correlation_threshold: float = 0.7): # 70% correlation threshold
        """
        Initialize risk analyzer
        
        Args:
            max_portfolio_risk: Maximum portfolio risk per trade (0.0-1.0)
            max_position_size: Maximum position size as fraction of portfolio
            volatility_threshold: Volatility threshold for risk assessment
            correlation_threshold: Correlation threshold for diversification
        """
        self.max_portfolio_risk = max_portfolio_risk
        self.max_position_size = max_position_size
        self.volatility_threshold = volatility_threshold
        self.correlation_threshold = correlation_threshold
        
        # Risk level thresholds
        self.risk_thresholds = {
            "LOW": 0.3,
            "MEDIUM": 0.6,
            "HIGH": 0.8,
            "EXTREME": 1.0
        }
        
        logger.info("🛡️ Risk Analyzer initialized")
    
    async def assess_risk(self, 
                         market_data: Dict[str, Any],
                         decision_data: Dict[str, Any],
                         portfolio_data: Optional[Dict[str, Any]] = None,
                         historical_data: Optional[List[Dict[str, Any]]] = None) -> RiskAssessment:
        """
        Comprehensive risk assessment for trading decision
        
        Args:
            market_data: Current market data
            decision_data: Trading decision data
            portfolio_data: Current portfolio information
            historical_data: Historical price/performance data
            
        Returns:
            Risk assessment result
        """
        try:
            # Calculate individual risk components
            market_risk = self._assess_market_risk(market_data, historical_data)
            position_risk = self._assess_position_risk(decision_data, portfolio_data)
            volatility_risk = self._assess_volatility_risk(market_data, historical_data)
            liquidity_risk = self._assess_liquidity_risk(market_data)
            correlation_risk = self._assess_correlation_risk(market_data, portfolio_data)
            
            # Combine risk scores
            risk_components = {
                "market_risk": market_risk,
                "position_risk": position_risk,
                "volatility_risk": volatility_risk,
                "liquidity_risk": liquidity_risk,
                "correlation_risk": correlation_risk
            }
            
            # Calculate overall risk score (weighted average)
            weights = {
                "market_risk": 0.25,
                "position_risk": 0.25,
                "volatility_risk": 0.20,
                "liquidity_risk": 0.15,
                "correlation_risk": 0.15
            }
            
            overall_risk = sum(risk_components[component] * weights[component] 
                             for component in risk_components)
            
            # Determine risk level
            risk_level = self._determine_risk_level(overall_risk)
            
            # Generate risk factors and warnings
            risk_factors = self._identify_risk_factors(risk_components, market_data)
            warnings = self._generate_warnings(risk_components, market_data, decision_data)
            
            # Calculate position size recommendation
            position_size = self._calculate_position_size(
                overall_risk, 
                market_data, 
                portfolio_data
            )
            
            # Calculate stop loss recommendation
            stop_loss = self._calculate_stop_loss(market_data, overall_risk)
            
            # Estimate maximum loss
            max_loss = self._estimate_max_loss(
                position_size, 
                market_data, 
                stop_loss
            )
            
            # Calculate confidence adjustment
            confidence_adjustment = self._calculate_confidence_adjustment(overall_risk)
            
            # Create risk assessment
            assessment = RiskAssessment(
                overall_risk_score=overall_risk,
                risk_level=risk_level,
                risk_factors=risk_factors,
                position_size_recommendation=position_size,
                stop_loss_recommendation=stop_loss,
                max_loss_estimate=max_loss,
                confidence_adjustment=confidence_adjustment,
                risk_metrics=risk_components,
                warnings=warnings,
                timestamp=datetime.utcnow().isoformat()
            )
            
            logger.info(f"🛡️ Risk Assessment: {risk_level} "
                       f"(Score: {overall_risk:.2f}, Position: {position_size:.1%})")
            
            return assessment
            
        except Exception as e:
            logger.error(f"❌ Risk assessment failed: {e}")
            # Return conservative default assessment
            return RiskAssessment(
                overall_risk_score=0.8,
                risk_level="HIGH",
                risk_factors=["Assessment failed"],
                position_size_recommendation=0.01,
                stop_loss_recommendation=None,
                max_loss_estimate=0.02,
                confidence_adjustment=0.5,
                risk_metrics={},
                warnings=[f"Risk assessment failed: {str(e)}"],
                timestamp=datetime.utcnow().isoformat()
            )
    
    def _assess_market_risk(self, 
                           market_data: Dict[str, Any], 
                           historical_data: Optional[List[Dict[str, Any]]]) -> float:
        """Assess general market risk"""
        risk_score = 0.0
        
        # Check for market indicators
        if market_data.get("market_trend") == "bearish":
            risk_score += 0.3
        elif market_data.get("market_trend") == "volatile":
            risk_score += 0.2
        
        # Check volume indicators
        volume = market_data.get("volume", 0)
        avg_volume = market_data.get("avg_volume", volume)
        
        if avg_volume > 0:
            volume_ratio = volume / avg_volume
            if volume_ratio < 0.5:  # Low volume
                risk_score += 0.2
            elif volume_ratio > 2.0:  # High volume
                risk_score += 0.1
        
        # Check for news/events
        if market_data.get("has_news_events", False):
            risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    def _assess_position_risk(self, 
                             decision_data: Dict[str, Any], 
                             portfolio_data: Optional[Dict[str, Any]]) -> float:
        """Assess position-specific risk"""
        risk_score = 0.0
        
        # Check position size
        requested_size = decision_data.get("quantity", 0)
        if portfolio_data:
            portfolio_value = portfolio_data.get("total_value", 1)
            position_value = requested_size * decision_data.get("price", 0)
            
            if portfolio_value > 0:
                position_ratio = position_value / portfolio_value
                if position_ratio > self.max_position_size:
                    risk_score += 0.4
                elif position_ratio > self.max_position_size * 0.5:
                    risk_score += 0.2
        
        # Check leverage
        leverage = decision_data.get("leverage", 1.0)
        if leverage > 2.0:
            risk_score += 0.3
        elif leverage > 1.5:
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _assess_volatility_risk(self, 
                               market_data: Dict[str, Any], 
                               historical_data: Optional[List[Dict[str, Any]]]) -> float:
        """Assess volatility-based risk"""
        risk_score = 0.0
        
        # Check current volatility indicators
        volatility = market_data.get("volatility", 0)
        if volatility > self.volatility_threshold * 2:
            risk_score += 0.4
        elif volatility > self.volatility_threshold:
            risk_score += 0.2
        
        # Calculate historical volatility if data available
        if historical_data and len(historical_data) > 10:
            prices = [float(d.get("price", 0)) for d in historical_data[-20:]]
            if len(prices) > 1:
                returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                          for i in range(1, len(prices))]
                hist_volatility = statistics.stdev(returns) if len(returns) > 1 else 0
                
                if hist_volatility > 0.1:  # 10% daily volatility
                    risk_score += 0.3
                elif hist_volatility > 0.05:  # 5% daily volatility
                    risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _assess_liquidity_risk(self, market_data: Dict[str, Any]) -> float:
        """Assess liquidity risk"""
        risk_score = 0.0
        
        # Check bid-ask spread
        bid = market_data.get("bid", 0)
        ask = market_data.get("ask", 0)
        
        if bid > 0 and ask > 0:
            spread = (ask - bid) / ((ask + bid) / 2)
            if spread > 0.02:  # 2% spread
                risk_score += 0.3
            elif spread > 0.01:  # 1% spread
                risk_score += 0.1
        
        # Check market depth
        market_depth = market_data.get("market_depth", 1.0)
        if market_depth < 0.5:
            risk_score += 0.2
        
        return min(risk_score, 1.0)
    
    def _assess_correlation_risk(self, 
                                market_data: Dict[str, Any], 
                                portfolio_data: Optional[Dict[str, Any]]) -> float:
        """Assess correlation and diversification risk"""
        risk_score = 0.0
        
        if not portfolio_data:
            return 0.1  # Slight risk for unknown portfolio
        
        # Check sector concentration
        current_symbol = market_data.get("symbol", "")
        current_sector = market_data.get("sector", "unknown")
        
        portfolio_positions = portfolio_data.get("positions", [])
        sector_exposure = 0.0
        
        for position in portfolio_positions:
            if position.get("sector") == current_sector:
                sector_exposure += position.get("weight", 0)
        
        if sector_exposure > 0.5:  # 50% sector concentration
            risk_score += 0.3
        elif sector_exposure > 0.3:  # 30% sector concentration
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score"""
        for level, threshold in self.risk_thresholds.items():
            if risk_score <= threshold:
                return level
        return "EXTREME"
    
    def _identify_risk_factors(self, 
                              risk_components: Dict[str, float], 
                              market_data: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors"""
        factors = []
        
        for component, score in risk_components.items():
            if score > 0.5:
                factors.append(f"High {component.replace('_', ' ')}")
        
        # Add specific market factors
        if market_data.get("volatility", 0) > self.volatility_threshold:
            factors.append("High volatility detected")
        
        if market_data.get("volume", 0) < market_data.get("avg_volume", 1) * 0.5:
            factors.append("Low trading volume")
        
        return factors
    
    def _generate_warnings(self, 
                          risk_components: Dict[str, float], 
                          market_data: Dict[str, Any], 
                          decision_data: Dict[str, Any]) -> List[str]:
        """Generate risk warnings"""
        warnings = []
        
        # High risk warnings
        if risk_components.get("volatility_risk", 0) > 0.7:
            warnings.append("⚠️ Extremely high volatility - consider reducing position size")
        
        if risk_components.get("liquidity_risk", 0) > 0.6:
            warnings.append("⚠️ Poor liquidity - may be difficult to exit position")
        
        if risk_components.get("position_risk", 0) > 0.6:
            warnings.append("⚠️ Large position size relative to portfolio")
        
        # Market condition warnings
        if market_data.get("market_trend") == "bearish":
            warnings.append("⚠️ Bearish market conditions detected")
        
        return warnings
    
    def _calculate_position_size(self, 
                                risk_score: float, 
                                market_data: Dict[str, Any], 
                                portfolio_data: Optional[Dict[str, Any]]) -> float:
        """Calculate recommended position size"""
        # Base position size (conservative)
        base_size = self.max_position_size * 0.5
        
        # Adjust based on risk score
        risk_adjustment = 1.0 - risk_score
        adjusted_size = base_size * risk_adjustment
        
        # Ensure minimum and maximum bounds
        min_size = 0.001  # 0.1% minimum
        max_size = self.max_position_size
        
        return max(min_size, min(adjusted_size, max_size))
    
    def _calculate_stop_loss(self, 
                            market_data: Dict[str, Any], 
                            risk_score: float) -> Optional[float]:
        """Calculate recommended stop loss"""
        current_price = market_data.get("price", 0)
        if current_price <= 0:
            return None
        
        # Base stop loss percentage (2-10% based on risk)
        base_stop_pct = 0.02 + (risk_score * 0.08)
        
        # Adjust for volatility
        volatility = market_data.get("volatility", 0.02)
        volatility_adjustment = min(volatility * 2, 0.05)  # Max 5% adjustment
        
        stop_loss_pct = base_stop_pct + volatility_adjustment
        
        return current_price * (1 - stop_loss_pct)
    
    def _estimate_max_loss(self, 
                          position_size: float, 
                          market_data: Dict[str, Any], 
                          stop_loss: Optional[float]) -> float:
        """Estimate maximum potential loss"""
        if not stop_loss:
            # Conservative estimate without stop loss
            return position_size * 0.1  # 10% max loss estimate
        
        current_price = market_data.get("price", 0)
        if current_price <= 0:
            return position_size * 0.05
        
        loss_per_unit = (current_price - stop_loss) / current_price
        return position_size * loss_per_unit
    
    def _calculate_confidence_adjustment(self, risk_score: float) -> float:
        """Calculate confidence adjustment factor"""
        # Higher risk = lower confidence
        return max(0.1, 1.0 - risk_score)
