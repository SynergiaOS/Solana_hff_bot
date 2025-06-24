"""THE OVERMIND PROTOCOL - Risk Analysis Agent
Specialized agent for comprehensive risk assessment using MinionAgent framework.
"""

import logging
from typing import Dict, Any, Optional, List

# Try to import MinionAgent, fall back to mock if not available
try:
    from minion_agent import AgentConfig, MinionAgent
except ImportError:
    from ..mock_minion_agent import AgentConfig, MinionAgent

from ..risk_analyzer import RiskAnalyzer, RiskAssessment

logger = logging.getLogger(__name__)

class RiskAnalysisAgent:
    """Specialized agent for risk analysis operations using MinionAgent framework."""
    
    def __init__(self):
        """Initialize the RiskAnalysisAgent with proper configuration."""
        self.config = AgentConfig(
            name="risk_analysis_agent",
            description="Agent specialized in comprehensive risk assessment for trading decisions, portfolio management, and risk mitigation strategies",
            model_id="deepseek/deepseek-reasoner",
            agent_type="CodeAgent",
            tools=[
                "assess_trading_risk",
                "calculate_position_sizing",
                "evaluate_portfolio_risk",
                "generate_risk_warnings"
            ]
        )
        
        # Initialize the MinionAgent with our config
        self.agent = MinionAgent(self.config)
        
        # Initialize the risk analyzer
        self.risk_analyzer = RiskAnalyzer()
        
        # Register our tools with the agent
        self._register_tools()
    
    def _register_tools(self):
        """Register risk analysis tools with the MinionAgent."""
        self.agent.register_tool("assess_trading_risk", self._assess_trading_risk)
        self.agent.register_tool("calculate_position_sizing", self._calculate_position_sizing)
        self.agent.register_tool("evaluate_portfolio_risk", self._evaluate_portfolio_risk)
        self.agent.register_tool("generate_risk_warnings", self._generate_risk_warnings)
    
    async def _assess_trading_risk(self, 
                                  market_data: Dict[str, Any],
                                  decision_data: Dict[str, Any],
                                  portfolio_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Assess trading risk for a specific decision.
        
        Args:
            market_data: Current market data
            decision_data: Trading decision data
            portfolio_data: Optional portfolio information
            
        Returns:
            Dict containing risk assessment results
        """
        logger.info(f"🛡️ Assessing trading risk for {decision_data.get('symbol', 'unknown')}")
        
        try:
            assessment = await self.risk_analyzer.assess_risk(
                market_data=market_data,
                decision_data=decision_data,
                portfolio_data=portfolio_data
            )
            
            return {
                "risk_score": assessment.overall_risk_score,
                "risk_level": assessment.risk_level,
                "risk_factors": assessment.risk_factors,
                "position_size_recommendation": assessment.position_size_recommendation,
                "stop_loss_recommendation": assessment.stop_loss_recommendation,
                "max_loss_estimate": assessment.max_loss_estimate,
                "confidence_adjustment": assessment.confidence_adjustment,
                "warnings": assessment.warnings,
                "risk_metrics": assessment.risk_metrics,
                "timestamp": assessment.timestamp
            }
        except Exception as e:
            logger.error(f"❌ Error assessing trading risk: {e}")
            return {
                "error": str(e),
                "risk_score": 0.8,
                "risk_level": "HIGH",
                "warnings": ["Risk assessment failed - proceeding with caution"]
            }
    
    async def _calculate_position_sizing(self, 
                                       market_data: Dict[str, Any],
                                       portfolio_data: Dict[str, Any],
                                       risk_tolerance: float = 0.02) -> Dict[str, Any]:
        """Calculate optimal position sizing based on risk parameters.
        
        Args:
            market_data: Current market data
            portfolio_data: Portfolio information
            risk_tolerance: Risk tolerance as fraction of portfolio
            
        Returns:
            Dict containing position sizing recommendations
        """
        logger.info("📊 Calculating optimal position sizing")
        
        try:
            # Create decision data for position sizing
            decision_data = {
                "symbol": market_data.get("symbol", ""),
                "price": market_data.get("price", 0),
                "quantity": 0,  # Will be calculated
                "leverage": 1.0
            }
            
            assessment = await self.risk_analyzer.assess_risk(
                market_data=market_data,
                decision_data=decision_data,
                portfolio_data=portfolio_data
            )
            
            # Calculate position sizes for different risk levels
            portfolio_value = portfolio_data.get("total_value", 0)
            current_price = market_data.get("price", 0)
            
            if portfolio_value > 0 and current_price > 0:
                conservative_size = (portfolio_value * risk_tolerance * 0.5) / current_price
                moderate_size = (portfolio_value * risk_tolerance) / current_price
                aggressive_size = (portfolio_value * risk_tolerance * 1.5) / current_price
            else:
                conservative_size = moderate_size = aggressive_size = 0
            
            return {
                "recommended_size": assessment.position_size_recommendation,
                "conservative_size": conservative_size,
                "moderate_size": moderate_size,
                "aggressive_size": aggressive_size,
                "max_portfolio_risk": assessment.max_loss_estimate,
                "stop_loss_price": assessment.stop_loss_recommendation,
                "risk_level": assessment.risk_level,
                "confidence": assessment.confidence_adjustment
            }
        except Exception as e:
            logger.error(f"❌ Error calculating position sizing: {e}")
            return {
                "error": str(e),
                "recommended_size": 0.001,
                "risk_level": "HIGH"
            }
    
    async def _evaluate_portfolio_risk(self, 
                                     portfolio_data: Dict[str, Any],
                                     market_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate overall portfolio risk.
        
        Args:
            portfolio_data: Current portfolio data
            market_conditions: Current market conditions
            
        Returns:
            Dict containing portfolio risk evaluation
        """
        logger.info("🏦 Evaluating portfolio risk")
        
        try:
            positions = portfolio_data.get("positions", [])
            total_value = portfolio_data.get("total_value", 0)
            
            # Calculate portfolio metrics
            portfolio_risk_score = 0.0
            sector_concentrations = {}
            risk_factors = []
            
            for position in positions:
                weight = position.get("weight", 0)
                sector = position.get("sector", "unknown")
                
                # Track sector concentration
                sector_concentrations[sector] = sector_concentrations.get(sector, 0) + weight
                
                # Assess individual position risk
                if weight > 0.2:  # 20% concentration
                    risk_factors.append(f"High concentration in {position.get('symbol', 'unknown')}")
                    portfolio_risk_score += 0.2
            
            # Check sector concentration
            max_sector_concentration = max(sector_concentrations.values()) if sector_concentrations else 0
            if max_sector_concentration > 0.5:
                risk_factors.append(f"High sector concentration: {max_sector_concentration:.1%}")
                portfolio_risk_score += 0.3
            
            # Factor in market conditions
            if market_conditions.get("volatility", 0) > 0.05:
                risk_factors.append("High market volatility")
                portfolio_risk_score += 0.2
            
            if market_conditions.get("trend", "neutral") == "bearish":
                risk_factors.append("Bearish market conditions")
                portfolio_risk_score += 0.3
            
            # Determine overall portfolio risk level
            if portfolio_risk_score <= 0.3:
                risk_level = "LOW"
            elif portfolio_risk_score <= 0.6:
                risk_level = "MEDIUM"
            elif portfolio_risk_score <= 0.8:
                risk_level = "HIGH"
            else:
                risk_level = "EXTREME"
            
            return {
                "portfolio_risk_score": min(portfolio_risk_score, 1.0),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "sector_concentrations": sector_concentrations,
                "max_sector_concentration": max_sector_concentration,
                "diversification_score": 1.0 - max_sector_concentration,
                "recommendations": self._generate_portfolio_recommendations(
                    portfolio_risk_score, risk_factors
                )
            }
        except Exception as e:
            logger.error(f"❌ Error evaluating portfolio risk: {e}")
            return {
                "error": str(e),
                "portfolio_risk_score": 0.8,
                "risk_level": "HIGH"
            }
    
    async def _generate_risk_warnings(self, 
                                    risk_assessment: Dict[str, Any],
                                    market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific risk warnings and recommendations.
        
        Args:
            risk_assessment: Risk assessment results
            market_data: Current market data
            
        Returns:
            Dict containing warnings and recommendations
        """
        logger.info("⚠️ Generating risk warnings")
        
        warnings = []
        recommendations = []
        
        risk_score = risk_assessment.get("risk_score", 0)
        risk_level = risk_assessment.get("risk_level", "MEDIUM")
        
        # Generate warnings based on risk level
        if risk_level == "EXTREME":
            warnings.append("🚨 EXTREME RISK: Consider avoiding this trade")
            recommendations.append("Wait for better market conditions")
        elif risk_level == "HIGH":
            warnings.append("⚠️ HIGH RISK: Proceed with extreme caution")
            recommendations.append("Reduce position size significantly")
        elif risk_level == "MEDIUM":
            warnings.append("⚠️ MEDIUM RISK: Monitor position closely")
            recommendations.append("Use appropriate stop losses")
        
        # Specific risk factor warnings
        risk_factors = risk_assessment.get("risk_factors", [])
        for factor in risk_factors:
            if "volatility" in factor.lower():
                warnings.append("⚠️ High volatility detected - expect price swings")
                recommendations.append("Consider smaller position size")
            elif "liquidity" in factor.lower():
                warnings.append("⚠️ Liquidity concerns - may be difficult to exit")
                recommendations.append("Plan exit strategy carefully")
        
        # Market condition warnings
        if market_data.get("volume", 0) < market_data.get("avg_volume", 1) * 0.5:
            warnings.append("⚠️ Low trading volume detected")
            recommendations.append("Wait for higher volume confirmation")
        
        return {
            "warnings": warnings,
            "recommendations": recommendations,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "action_required": len(warnings) > 0
        }
    
    def _generate_portfolio_recommendations(self, 
                                          risk_score: float, 
                                          risk_factors: List[str]) -> List[str]:
        """Generate portfolio-specific recommendations."""
        recommendations = []
        
        if risk_score > 0.7:
            recommendations.append("Consider reducing overall position sizes")
            recommendations.append("Increase diversification across sectors")
        
        if any("concentration" in factor.lower() for factor in risk_factors):
            recommendations.append("Reduce concentrated positions")
            recommendations.append("Spread investments across more assets")
        
        if any("volatility" in factor.lower() for factor in risk_factors):
            recommendations.append("Consider hedging strategies")
            recommendations.append("Increase cash reserves")
        
        return recommendations
    
    async def comprehensive_risk_analysis(self, 
                                        market_data: Dict[str, Any],
                                        decision_data: Dict[str, Any],
                                        portfolio_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform comprehensive risk analysis for trading decision.
        
        Args:
            market_data: Current market data
            decision_data: Trading decision data
            portfolio_data: Optional portfolio data
            
        Returns:
            Dict containing comprehensive risk analysis
        """
        prompt = f"""
        Perform comprehensive risk analysis for trading decision. Please:
        1. Assess trading risk using assess_trading_risk
        2. Calculate optimal position sizing using calculate_position_sizing
        3. Evaluate portfolio risk if portfolio data available
        4. Generate specific warnings and recommendations
        5. Provide final risk verdict and action plan
        
        Market Data: {market_data}
        Decision Data: {decision_data}
        Portfolio Data: {portfolio_data or 'Not available'}
        
        Return comprehensive analysis in JSON format with clear risk assessment and actionable recommendations.
        """
        
        try:
            result = await self.agent.execute(prompt)
            logger.info(f"🛡️ Comprehensive risk analysis completed")
            return result
        except Exception as e:
            logger.error(f"❌ Error in comprehensive risk analysis: {e}")
            return {
                "error": str(e),
                "risk_verdict": "HIGH_RISK",
                "recommendation": "AVOID_TRADE"
            }

# Factory function for easy instantiation
def create_risk_analysis_agent() -> RiskAnalysisAgent:
    """Create and return a configured RiskAnalysisAgent instance."""
    return RiskAnalysisAgent()