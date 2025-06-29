"""THE OVERMIND PROTOCOL - Enhanced Planning Layer
NVIDIA-inspired planning system with reflection, reasoning, and decomposition.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class PlanningPhase(Enum):
    """Planning phases in the NVIDIA-style system"""
    PERCEPTION = "perception"
    REFLECTION = "reflection"
    REASONING = "reasoning"
    DECOMPOSITION = "decomposition"
    ACTION_PLANNING = "action_planning"
    EXECUTION = "execution"
    EVALUATION = "evaluation"

@dataclass
class PlanStep:
    """Individual step in a trading plan"""
    step_id: str
    action_type: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    expected_outcome: str
    confidence: float
    risk_level: str
    estimated_duration: float  # seconds

@dataclass
class TradingPlan:
    """Complete trading plan with multiple steps"""
    plan_id: str
    goal: str
    market_context: Dict[str, Any]
    steps: List[PlanStep]
    total_confidence: float
    risk_assessment: Dict[str, Any]
    created_at: datetime
    estimated_completion: datetime
    status: str = "created"

@dataclass
class ReflectionResult:
    """Result of reflection on past actions"""
    reflection_id: str
    original_plan: TradingPlan
    actual_outcome: Dict[str, Any]
    lessons_learned: List[str]
    success_factors: List[str]
    failure_factors: List[str]
    improvement_suggestions: List[str]
    confidence_adjustment: float

class ReflectionEngine:
    """Reflects on past decisions and outcomes to improve future planning"""
    
    def __init__(self):
        self.reflection_history = {}
        self.pattern_database = {}
        self.success_patterns = []
        self.failure_patterns = []
        
    async def reflect_on_outcome(self, plan: TradingPlan, 
                                outcome: Dict[str, Any]) -> ReflectionResult:
        """Reflect on the outcome of a trading plan"""
        try:
            reflection_id = f"refl_{uuid.uuid4().hex[:8]}"
            
            # Analyze what went right/wrong
            success_factors = self._identify_success_factors(plan, outcome)
            failure_factors = self._identify_failure_factors(plan, outcome)
            
            # Extract lessons learned
            lessons_learned = self._extract_lessons(plan, outcome, success_factors, failure_factors)
            
            # Generate improvement suggestions
            improvements = self._generate_improvements(plan, outcome, lessons_learned)
            
            # Calculate confidence adjustment
            confidence_adj = self._calculate_confidence_adjustment(plan, outcome)
            
            reflection = ReflectionResult(
                reflection_id=reflection_id,
                original_plan=plan,
                actual_outcome=outcome,
                lessons_learned=lessons_learned,
                success_factors=success_factors,
                failure_factors=failure_factors,
                improvement_suggestions=improvements,
                confidence_adjustment=confidence_adj
            )
            
            # Store reflection for future use
            self.reflection_history[reflection_id] = reflection
            self._update_pattern_database(reflection)
            
            logger.info(f"🤔 Reflection completed: {len(lessons_learned)} lessons learned")
            return reflection
            
        except Exception as e:
            logger.error(f"❌ Reflection failed: {e}")
            return None
            
    def _identify_success_factors(self, plan: TradingPlan, outcome: Dict[str, Any]) -> List[str]:
        """Identify what contributed to success"""
        factors = []
        
        # Check if outcome met expectations
        expected_profit = plan.risk_assessment.get('expected_profit', 0)
        actual_profit = outcome.get('profit_loss', 0)
        
        if actual_profit > expected_profit * 0.8:  # 80% of expected
            factors.append("Profit target achieved")
            
        # Check timing
        expected_duration = plan.estimated_completion - plan.created_at
        actual_duration = outcome.get('execution_time', 0)
        
        if actual_duration <= expected_duration.total_seconds():
            factors.append("Executed within expected timeframe")
            
        # Check risk management
        max_risk = plan.risk_assessment.get('max_loss', 0)
        actual_loss = abs(min(0, actual_profit))
        
        if actual_loss <= max_risk:
            factors.append("Risk limits respected")
            
        return factors
        
    def _identify_failure_factors(self, plan: TradingPlan, outcome: Dict[str, Any]) -> List[str]:
        """Identify what contributed to failure"""
        factors = []
        
        actual_profit = outcome.get('profit_loss', 0)
        expected_profit = plan.risk_assessment.get('expected_profit', 0)
        
        if actual_profit < expected_profit * 0.5:  # Less than 50% of expected
            factors.append("Significant underperformance")
            
        if actual_profit < 0:
            factors.append("Loss incurred")
            
        # Check if plan was executed as intended
        planned_steps = len(plan.steps)
        executed_steps = outcome.get('steps_executed', 0)
        
        if executed_steps < planned_steps:
            factors.append("Plan execution incomplete")
            
        return factors
        
    def _extract_lessons(self, plan: TradingPlan, outcome: Dict[str, Any], 
                        success_factors: List[str], failure_factors: List[str]) -> List[str]:
        """Extract actionable lessons from the experience"""
        lessons = []
        
        # Market condition lessons
        market_type = plan.market_context.get('market_type', 'unknown')
        volatility = plan.market_context.get('volatility', 'medium')
        
        if 'Profit target achieved' in success_factors:
            lessons.append(f"Strategy works well in {market_type} market with {volatility} volatility")
            
        if 'Loss incurred' in failure_factors:
            lessons.append(f"Avoid similar strategies in {market_type} market conditions")
            
        # Timing lessons
        if 'Executed within expected timeframe' in success_factors:
            lessons.append("Time estimates were accurate for this strategy type")
        elif 'Plan execution incomplete' in failure_factors:
            lessons.append("Allow more time for complex multi-step strategies")
            
        return lessons
        
    def _generate_improvements(self, plan: TradingPlan, outcome: Dict[str, Any], 
                             lessons: List[str]) -> List[str]:
        """Generate specific improvement suggestions"""
        improvements = []
        
        # Confidence adjustments
        if outcome.get('profit_loss', 0) < 0:
            improvements.append("Reduce position size for similar market conditions")
            improvements.append("Add additional confirmation signals before entry")
            
        # Risk management improvements
        max_loss = abs(min(0, outcome.get('profit_loss', 0)))
        planned_max_loss = plan.risk_assessment.get('max_loss', 0)
        
        if max_loss > planned_max_loss * 1.2:  # 20% over planned loss
            improvements.append("Implement tighter stop-loss mechanisms")
            improvements.append("Add position size limits based on volatility")
            
        return improvements
        
    def _calculate_confidence_adjustment(self, plan: TradingPlan, outcome: Dict[str, Any]) -> float:
        """Calculate how much to adjust confidence for similar future plans"""
        actual_profit = outcome.get('profit_loss', 0)
        expected_profit = plan.risk_assessment.get('expected_profit', 0)
        
        if expected_profit == 0:
            return 0.0
            
        performance_ratio = actual_profit / expected_profit
        
        # Adjust confidence based on performance
        if performance_ratio > 1.2:  # 20% better than expected
            return 0.1  # Increase confidence
        elif performance_ratio < 0.5:  # 50% worse than expected
            return -0.2  # Decrease confidence significantly
        elif performance_ratio < 0.8:  # 20% worse than expected
            return -0.1  # Decrease confidence slightly
        else:
            return 0.0  # No adjustment
            
    def _update_pattern_database(self, reflection: ReflectionResult) -> None:
        """Update pattern database with new reflection insights"""
        # Extract patterns from successful/failed strategies
        market_context = reflection.original_plan.market_context
        outcome = reflection.actual_outcome
        
        pattern_key = f"{market_context.get('market_type', 'unknown')}_{market_context.get('volatility', 'medium')}"
        
        if pattern_key not in self.pattern_database:
            self.pattern_database[pattern_key] = {
                'success_count': 0,
                'failure_count': 0,
                'lessons': [],
                'improvements': []
            }
            
        # Update pattern data
        if outcome.get('profit_loss', 0) > 0:
            self.pattern_database[pattern_key]['success_count'] += 1
            self.pattern_database[pattern_key]['lessons'].extend(reflection.lessons_learned)
        else:
            self.pattern_database[pattern_key]['failure_count'] += 1
            
        self.pattern_database[pattern_key]['improvements'].extend(reflection.improvement_suggestions)

class ReasoningEngine:
    """Advanced reasoning for trading decisions"""
    
    def __init__(self):
        self.reasoning_chains = {}
        self.logical_rules = {}
        self.market_models = {}
        
    async def reason_about_market(self, market_data: Dict[str, Any], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply reasoning to market data and context"""
        try:
            reasoning_id = f"reason_{uuid.uuid4().hex[:8]}"
            
            # Multi-step reasoning process
            reasoning_chain = []
            
            # Step 1: Analyze current market state
            market_analysis = self._analyze_market_state(market_data)
            reasoning_chain.append(("market_analysis", market_analysis))
            
            # Step 2: Apply logical rules
            rule_results = self._apply_logical_rules(market_data, context)
            reasoning_chain.append(("rule_application", rule_results))
            
            # Step 3: Consider historical patterns
            pattern_analysis = self._analyze_patterns(market_data, context)
            reasoning_chain.append(("pattern_analysis", pattern_analysis))
            
            # Step 4: Synthesize reasoning
            final_reasoning = self._synthesize_reasoning(reasoning_chain)
            
            result = {
                'reasoning_id': reasoning_id,
                'reasoning_chain': reasoning_chain,
                'final_reasoning': final_reasoning,
                'confidence': final_reasoning.get('confidence', 0.5),
                'recommendation': final_reasoning.get('recommendation', 'HOLD')
            }
            
            self.reasoning_chains[reasoning_id] = result
            return result
            
        except Exception as e:
            logger.error(f"❌ Reasoning failed: {e}")
            return {'recommendation': 'HOLD', 'confidence': 0.0}
            
    def _analyze_market_state(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current market state"""
        price = market_data.get('price', 0)
        volume = market_data.get('volume', 0)
        price_change = market_data.get('price_change_percent', 0)
        
        analysis = {
            'price_trend': 'bullish' if price_change > 2 else 'bearish' if price_change < -2 else 'neutral',
            'volume_assessment': 'high' if volume > market_data.get('avg_volume', volume) * 1.5 else 'normal',
            'momentum': 'strong' if abs(price_change) > 5 else 'weak',
            'volatility': 'high' if abs(price_change) > 10 else 'medium' if abs(price_change) > 3 else 'low'
        }
        
        return analysis
        
    def _apply_logical_rules(self, market_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply logical trading rules"""
        rules_applied = []
        
        # Rule 1: Don't buy in strong downtrend
        price_change = market_data.get('price_change_percent', 0)
        if price_change < -5:
            rules_applied.append({
                'rule': 'avoid_downtrend',
                'result': 'SELL',
                'confidence': 0.8,
                'reasoning': 'Strong downtrend detected'
            })
            
        # Rule 2: High volume + price increase = potential buy
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if price_change > 3 and volume_ratio > 1.5:
            rules_applied.append({
                'rule': 'volume_price_confirmation',
                'result': 'BUY',
                'confidence': 0.7,
                'reasoning': 'High volume confirms price movement'
            })
            
        # Rule 3: Risk management - position sizing
        current_portfolio_value = context.get('portfolio_value', 1.0)
        max_position_size = current_portfolio_value * 0.1  # 10% max
        
        rules_applied.append({
            'rule': 'position_sizing',
            'result': f'MAX_SIZE_{max_position_size}',
            'confidence': 1.0,
            'reasoning': 'Risk management position sizing'
        })
        
        return {'rules_applied': rules_applied}
        
    def _analyze_patterns(self, market_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze historical patterns"""
        # Simplified pattern analysis
        similar_episodes = context.get('similar_episodes', [])
        
        if similar_episodes:
            success_rate = sum(1 for ep in similar_episodes if ep.success_score > 0.6) / len(similar_episodes)
            avg_success_score = sum(ep.success_score for ep in similar_episodes) / len(similar_episodes)
            
            return {
                'historical_success_rate': success_rate,
                'avg_success_score': avg_success_score,
                'pattern_confidence': success_rate,
                'recommendation': 'BUY' if success_rate > 0.6 else 'HOLD' if success_rate > 0.4 else 'SELL'
            }
        else:
            return {
                'historical_success_rate': 0.5,
                'pattern_confidence': 0.3,
                'recommendation': 'HOLD'
            }
            
    def _synthesize_reasoning(self, reasoning_chain: List[Tuple[str, Dict]]) -> Dict[str, Any]:
        """Synthesize all reasoning steps into final decision"""
        recommendations = []
        confidences = []
        
        for step_name, step_result in reasoning_chain:
            if step_name == "rule_application":
                for rule in step_result.get('rules_applied', []):
                    if rule['result'] in ['BUY', 'SELL', 'HOLD']:
                        recommendations.append(rule['result'])
                        confidences.append(rule['confidence'])
                        
            elif step_name == "pattern_analysis":
                recommendations.append(step_result.get('recommendation', 'HOLD'))
                confidences.append(step_result.get('pattern_confidence', 0.5))
                
        # Synthesize final recommendation
        if not recommendations:
            return {'recommendation': 'HOLD', 'confidence': 0.5}
            
        # Count votes
        buy_votes = recommendations.count('BUY')
        sell_votes = recommendations.count('SELL')
        hold_votes = recommendations.count('HOLD')
        
        if buy_votes > sell_votes and buy_votes > hold_votes:
            final_rec = 'BUY'
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            final_rec = 'SELL'
        else:
            final_rec = 'HOLD'
            
        # Average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        return {
            'recommendation': final_rec,
            'confidence': avg_confidence,
            'vote_breakdown': {
                'BUY': buy_votes,
                'SELL': sell_votes,
                'HOLD': hold_votes
            }
        }

class DecompositionEngine:
    """Breaks down complex trading goals into manageable steps"""
    
    def __init__(self):
        self.decomposition_templates = {}
        self.step_dependencies = {}
        
    async def decompose_trading_goal(self, goal: str, market_context: Dict[str, Any], 
                                   constraints: Dict[str, Any]) -> List[PlanStep]:
        """Decompose a trading goal into executable steps"""
        try:
            steps = []
            
            # Determine goal type
            goal_type = self._classify_goal(goal)
            
            if goal_type == "buy_token":
                steps = self._decompose_buy_goal(goal, market_context, constraints)
            elif goal_type == "sell_token":
                steps = self._decompose_sell_goal(goal, market_context, constraints)
            elif goal_type == "portfolio_rebalance":
                steps = self._decompose_rebalance_goal(goal, market_context, constraints)
            else:
                # Generic decomposition
                steps = self._decompose_generic_goal(goal, market_context, constraints)
                
            logger.info(f"🔧 Goal decomposed into {len(steps)} steps")
            return steps
            
        except Exception as e:
            logger.error(f"❌ Goal decomposition failed: {e}")
            return []
            
    def _classify_goal(self, goal: str) -> str:
        """Classify the type of trading goal"""
        goal_lower = goal.lower()
        
        if "buy" in goal_lower or "purchase" in goal_lower:
            return "buy_token"
        elif "sell" in goal_lower or "exit" in goal_lower:
            return "sell_token"
        elif "rebalance" in goal_lower or "adjust" in goal_lower:
            return "portfolio_rebalance"
        else:
            return "generic"
            
    def _decompose_buy_goal(self, goal: str, market_context: Dict[str, Any], 
                           constraints: Dict[str, Any]) -> List[PlanStep]:
        """Decompose a buy goal into steps"""
        steps = []
        
        # Step 1: Market analysis
        steps.append(PlanStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            action_type="market_analysis",
            parameters={"symbol": market_context.get("symbol", "")},
            dependencies=[],
            expected_outcome="Market conditions analyzed",
            confidence=0.9,
            risk_level="LOW",
            estimated_duration=30.0
        ))
        
        # Step 2: Risk assessment
        steps.append(PlanStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            action_type="risk_assessment",
            parameters={"position_size": constraints.get("max_position_size", 0.1)},
            dependencies=[steps[0].step_id],
            expected_outcome="Risk parameters calculated",
            confidence=0.8,
            risk_level="LOW",
            estimated_duration=15.0
        ))
        
        # Step 3: Execute buy order
        steps.append(PlanStep(
            step_id=f"step_{uuid.uuid4().hex[:8]}",
            action_type="execute_buy",
            parameters={
                "symbol": market_context.get("symbol", ""),
                "amount": constraints.get("amount", 0),
                "order_type": "market"
            },
            dependencies=[steps[1].step_id],
            expected_outcome="Buy order executed",
            confidence=0.7,
            risk_level="MEDIUM",
            estimated_duration=10.0
        ))
        
        return steps
        
    def _decompose_sell_goal(self, goal: str, market_context: Dict[str, Any], 
                            constraints: Dict[str, Any]) -> List[PlanStep]:
        """Decompose a sell goal into steps"""
        # Similar structure to buy goal but for selling
        return []
        
    def _decompose_rebalance_goal(self, goal: str, market_context: Dict[str, Any], 
                                 constraints: Dict[str, Any]) -> List[PlanStep]:
        """Decompose a portfolio rebalance goal into steps"""
        # Portfolio rebalancing logic
        return []
        
    def _decompose_generic_goal(self, goal: str, market_context: Dict[str, Any], 
                               constraints: Dict[str, Any]) -> List[PlanStep]:
        """Decompose a generic goal into steps"""
        # Generic goal decomposition
        return []
