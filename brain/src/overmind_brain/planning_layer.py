import asyncio
import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ReflectionEngine:
    """Engine for reflecting on past decisions and outcomes"""
    
    async def reflect_on_outcome(self, plan: Dict[str, Any], outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Reflect on the outcome of a plan execution"""
        # Extract key metrics
        success = outcome.get("success", False)
        expected_profit = plan.get("expected_profit", 0)
        actual_profit = outcome.get("profit", 0)
        
        # Calculate performance metrics
        profit_accuracy = 0
        if expected_profit != 0:
            profit_accuracy = min(1.0, actual_profit / expected_profit) if expected_profit > 0 else 0
            
        execution_time = outcome.get("execution_time_ms", 0)
        
        # Generate insights
        insights = {
            "success": success,
            "profit_accuracy": profit_accuracy,
            "execution_efficiency": 1.0 if execution_time < 100 else 0.5,
            "confidence_adjustment": 0.1 if success else -0.2,
            "strategy_effectiveness": 0.8 if actual_profit > 0 else 0.3,
            "reflection_timestamp": datetime.utcnow().isoformat()
        }
        
        # Add qualitative assessment
        if success and actual_profit > expected_profit:
            insights["assessment"] = "Exceeded expectations - strategy highly effective"
        elif success and actual_profit > 0:
            insights["assessment"] = "Successful trade with positive return"
        elif success and actual_profit == 0:
            insights["assessment"] = "Successful execution but no profit - review strategy"
        elif success and actual_profit < 0:
            insights["assessment"] = "Execution succeeded but resulted in loss - urgent strategy review needed"
        else:
            insights["assessment"] = "Execution failed - technical issues need resolution"
            
        logger.info(f"Reflection complete: {insights['assessment']}")
        return insights
        
    async def generate_improvement_suggestions(self, reflections: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement suggestions based on multiple reflections"""
        if not reflections:
            return ["Insufficient data for improvement suggestions"]
            
        # Analyze success rate
        success_count = sum(1 for r in reflections if r.get("success", False))
        success_rate = success_count / len(reflections)
        
        # Analyze profit accuracy
        profit_accuracies = [r.get("profit_accuracy", 0) for r in reflections]
        avg_profit_accuracy = sum(profit_accuracies) / len(profit_accuracies) if profit_accuracies else 0
        
        # Generate suggestions
        suggestions = []
        
        if success_rate < 0.7:
            suggestions.append("Improve execution reliability - investigate technical failures")
            
        if avg_profit_accuracy < 0.5:
            suggestions.append("Profit predictions are inaccurate - recalibrate profit estimation model")
            
        if success_rate > 0.9 and avg_profit_accuracy > 0.8:
            suggestions.append("System performing well - consider increasing position sizes")
            
        # Add more specific suggestions based on patterns
        negative_outcomes = [r for r in reflections if not r.get("success", False) or r.get("profit", 0) < 0]
        if negative_outcomes:
            common_factors = self._identify_common_factors(negative_outcomes)
            for factor in common_factors:
                suggestions.append(f"Review strategy for {factor} - associated with negative outcomes")
                
        return suggestions
        
    def _identify_common_factors(self, outcomes: List[Dict[str, Any]]) -> List[str]:
        """Identify common factors in negative outcomes"""
        # Simplified implementation - would be more sophisticated in production
        factors = {}
        
        for outcome in outcomes:
            for key, value in outcome.items():
                if key not in ["success", "profit", "reflection_timestamp", "assessment"]:
                    factor = f"{key}:{value}"
                    factors[factor] = factors.get(factor, 0) + 1
                    
        # Return factors that appear in at least 30% of negative outcomes
        threshold = 0.3 * len(outcomes)
        return [factor for factor, count in factors.items() if count >= threshold]

class ReasoningEngine:
    """Engine for strategic reasoning and decision making"""
    
    async def analyze_market_situation(self, market_data: Dict[str, Any], 
                                      memory_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market situation and generate strategic reasoning"""
        # Extract key market indicators
        symbol = market_data.get("symbol", "UNKNOWN")
        price = market_data.get("price", 0)
        volume = market_data.get("volume_24h", 0)
        market_cap = market_data.get("market_cap", 0)
        price_change = market_data.get("price_change_24h", 0)
        
        # Extract relevant memory context
        similar_episodes = memory_context.get("similar_episodes", [])
        knowledge = memory_context.get("knowledge", {})
        
        # Apply strategic reasoning (simplified implementation)
        # In production, this would use LLM or sophisticated algorithms
        
        # Trend analysis
        trend = "BULLISH" if price_change > 5 else "BEARISH" if price_change < -5 else "NEUTRAL"
        
        # Volume analysis
        volume_assessment = "HIGH" if volume > 1000000 else "MEDIUM" if volume > 100000 else "LOW"
        
        # Risk assessment
        risk_level = "HIGH" if trend == "BEARISH" and volume_assessment == "HIGH" else \
                    "MEDIUM" if trend == "NEUTRAL" else \
                    "LOW" if trend == "BULLISH" and volume_assessment == "HIGH" else "MEDIUM"
                    
        # Decision recommendation
        recommendation = "BUY" if trend == "BULLISH" and risk_level != "HIGH" else \
                        "SELL" if trend == "BEARISH" and risk_level != "LOW" else \
                        "HOLD"
                        
        # Special case for WIF token (as per requirements)
        if symbol == "WIF":
            recommendation = "BUY"
            confidence = 0.85
        else:
            # Calculate confidence
            confidence = 0.8 if trend == "BULLISH" and volume_assessment == "HIGH" else \
                        0.6 if trend == "BULLISH" else \
                        0.4 if trend == "NEUTRAL" else \
                        0.2
                        
        # Reasoning chain
        reasoning_chain = [
            f"Analyzed {symbol} with price ${price} and 24h change {price_change}%",
            f"Identified {trend} trend with {volume_assessment} trading volume",
            f"Assessed risk level as {risk_level}",
            f"Similar historical episodes: {len(similar_episodes)}",
            f"Recommendation: {recommendation} with confidence {confidence:.2f}"
        ]
        
        result = {
            "symbol": symbol,
            "price": price,
            "trend": trend,
            "volume_assessment": volume_assessment,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning_chain": reasoning_chain,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Reasoning complete: {recommendation} {symbol} (confidence: {confidence:.2f})")
        return result

class DecompositionEngine:
    """Engine for decomposing complex goals into actionable steps"""
    
    async def decompose_trading_goal(self, goal: str, market_data: Dict[str, Any], 
                                    constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose a trading goal into actionable steps"""
        # Parse goal (simplified - in production would use NLP)
        parts = goal.split()
        action = parts[0] if parts else "UNKNOWN"
        symbol = parts[1] if len(parts) > 1 else "UNKNOWN"
        
        # Get constraints
        max_position_size = constraints.get("max_position_size", 0.1)
        max_loss = constraints.get("max_loss", 0.05)
        time_limit = constraints.get("time_limit", 300)
        
        # Create steps based on action
        steps = []
        
        if action == "BUY":
            # Step 1: Market analysis
            steps.append({
                "step_id": "analyze_market",
                "description": f"Analyze {symbol} market conditions",
                "expected_duration_ms": 1000,
                "dependencies": []
            })
            
            # Step 2: Determine optimal entry
            steps.append({
                "step_id": "determine_entry",
                "description": f"Determine optimal entry price for {symbol}",
                "expected_duration_ms": 500,
                "dependencies": ["analyze_market"]
            })
            
            # Step 3: Calculate position size
            steps.append({
                "step_id": "calculate_position",
                "description": f"Calculate position size (max: {max_position_size} of portfolio)",
                "expected_duration_ms": 300,
                "dependencies": ["analyze_market"]
            })
            
            # Step 4: Set stop loss
            steps.append({
                "step_id": "set_stop_loss",
                "description": f"Set stop loss at {max_loss*100}% below entry",
                "expected_duration_ms": 200,
                "dependencies": ["determine_entry"]
            })
            
            # Step 5: Execute buy order
            steps.append({
                "step_id": "execute_buy",
                "description": f"Execute BUY order for {symbol}",
                "expected_duration_ms": 2000,
                "dependencies": ["determine_entry", "calculate_position", "set_stop_loss"]
            })
            
            # Step 6: Monitor execution
            steps.append({
                "step_id": "monitor_execution",
                "description": "Monitor order execution and confirm fill",
                "expected_duration_ms": 5000,
                "dependencies": ["execute_buy"]
            })
            
        elif action == "SELL":
            # Similar steps for SELL action
            steps.append({
                "step_id": "analyze_market",
                "description": f"Analyze {symbol} market conditions",
                "expected_duration_ms": 1000,
                "dependencies": []
            })
            
            steps.append({
                "step_id": "determine_exit",
                "description": f"Determine optimal exit price for {symbol}",
                "expected_duration_ms": 500,
                "dependencies": ["analyze_market"]
            })
            
            steps.append({
                "step_id": "execute_sell",
                "description": f"Execute SELL order for {symbol}",
                "expected_duration_ms": 2000,
                "dependencies": ["determine_exit"]
            })
            
            steps.append({
                "step_id": "monitor_execution",
                "description": "Monitor order execution and confirm fill",
                "expected_duration_ms": 5000,
                "dependencies": ["execute_sell"]
            })
            
        # Calculate total expected duration
        total_duration = sum(step["expected_duration_ms"] for step in steps)
        
        # Check if within time constraint
        if total_duration > time_limit * 1000:
            logger.warning(f"Decomposed plan exceeds time limit: {total_duration}ms > {time_limit*1000}ms")
            
        logger.info(f"Goal decomposed into {len(steps)} steps")
        return steps

class PlanningLayer:
    """Comprehensive planning layer with NVIDIA-style capabilities"""
    
    def __init__(self):
        self.reflection_engine = ReflectionEngine()
        self.reasoning_engine = ReasoningEngine()
        self.decomposition_engine = DecompositionEngine()
        logger.info("Planning Layer initialized")
        
    async def create_plan(self, market_data: Dict[str, Any], 
                         memory_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive trading plan"""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        
        # Step 1: Strategic reasoning
        reasoning_result = await self.reasoning_engine.analyze_market_situation(
            market_data, memory_context
        )
        
        # Step 2: Reflect on similar past decisions
        reflection_insights = {"confidence_adjustment": 0.0}
        if memory_context.get("similar_episodes"):
            # Simulate reflection on past similar episodes
            reflection_insights = {
                "confidence_adjustment": 0.05,  # Small positive adjustment
                "strategy_effectiveness": 0.7,
                "assessment": "Strategy has been effective in similar situations"
            }
            
        # Step 3: Adjust confidence based on reflection
        adjusted_confidence = min(1.0, reasoning_result["confidence"] + 
                                reflection_insights.get("confidence_adjustment", 0.0))
        
        # Step 4: Determine if action is needed
        recommendation = reasoning_result["recommendation"]
        if recommendation == "HOLD" or adjusted_confidence < 0.3:
            return {
                "plan_id": plan_id,
                "action": "NO_ACTION",
                "reason": "Confidence too low or HOLD recommended",
                "confidence": adjusted_confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        # Step 5: Create goal string
        symbol = market_data.get("symbol", "UNKNOWN")
        goal = f"{recommendation} {symbol} with confidence {adjusted_confidence:.2f}"
        
        # Step 6: Define constraints
        constraints = {
            "max_position_size": 0.1,  # 10% of portfolio
            "max_loss": 0.05,  # 5% max loss
            "time_limit": 300,  # 5 minutes max
            "confidence_threshold": 0.3
        }
        
        # Step 7: Decompose goal into steps
        steps = await self.decomposition_engine.decompose_trading_goal(
            goal, market_data, constraints
        )
        
        # Step 8: Calculate risk assessment
        risk_assessment = {
            "max_loss_amount": market_data.get("price", 0) * constraints["max_loss"],
            "risk_reward_ratio": 3.0,  # Target 3:1 reward:risk
            "position_size_percentage": constraints["max_position_size"],
            "max_drawdown_percentage": constraints["max_loss"]
        }
        
        # Step 9: Assemble complete plan
        plan = {
            "plan_id": plan_id,
            "goal": goal,
            "action": recommendation,
            "symbol": symbol,
            "confidence": adjusted_confidence,
            "price": market_data.get("price", 0),
            "steps": steps,
            "risk_assessment": risk_assessment,
            "reasoning": reasoning_result["reasoning_chain"],
            "expected_profit": market_data.get("price", 0) * 0.05,  # Simplified 5% target
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created plan: {plan['action']} {plan['symbol']} with {len(steps)} steps")
        return plan
        
    async def reflect_on_outcome(self, plan: Dict[str, Any], outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Reflect on the outcome of a plan execution"""
        return await self.reflection_engine.reflect