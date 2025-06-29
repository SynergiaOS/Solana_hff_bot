"""THE OVERMIND PROTOCOL - Enhanced Brain Orchestrator
Main orchestrator combining human-inspired memory with NVIDIA-style planning.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from .enhanced_memory_system import EnhancedMemorySystem, TradingEpisode
from .enhanced_planning_layer import (
    ReflectionEngine, ReasoningEngine, DecompositionEngine, 
    TradingPlan, PlanStep, PlanningPhase
)

logger = logging.getLogger(__name__)

class EnhancedBrainOrchestrator:
    """Main orchestrator for THE OVERMIND PROTOCOL enhanced brain"""
    
    def __init__(self, mongodb_uri: str = None):
        # Initialize core components
        self.memory_system = EnhancedMemorySystem(mongodb_uri)
        self.reflection_engine = ReflectionEngine()
        self.reasoning_engine = ReasoningEngine()
        self.decomposition_engine = DecompositionEngine()
        
        # State tracking
        self.current_plans = {}
        self.active_phase = PlanningPhase.PERCEPTION
        self.decision_history = []
        
        # Performance metrics
        self.total_decisions = 0
        self.successful_decisions = 0
        self.total_profit_loss = 0.0
        
        logger.info("🧠 Enhanced Brain Orchestrator initialized")
        
    async def process_market_signal(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for processing market signals"""
        try:
            decision_id = f"decision_{uuid.uuid4().hex[:8]}"
            start_time = datetime.now()
            
            logger.info(f"🎯 Processing market signal for {market_data.get('symbol', 'UNKNOWN')}")
            
            # Phase 1: PERCEPTION - Process through memory system
            self.active_phase = PlanningPhase.PERCEPTION
            memory_context = await self.memory_system.process_market_perception(market_data)
            
            # Phase 2: REFLECTION - Learn from past similar situations
            self.active_phase = PlanningPhase.REFLECTION
            reflection_insights = await self._apply_reflection(market_data, memory_context)
            
            # Phase 3: REASONING - Apply logical analysis
            self.active_phase = PlanningPhase.REASONING
            reasoning_result = await self.reasoning_engine.reason_about_market(
                market_data, memory_context
            )
            
            # Phase 4: DECOMPOSITION - Break down into actionable steps
            self.active_phase = PlanningPhase.DECOMPOSITION
            trading_plan = await self._create_trading_plan(
                market_data, memory_context, reasoning_result, reflection_insights
            )
            
            # Phase 5: ACTION PLANNING - Finalize execution plan
            self.active_phase = PlanningPhase.ACTION_PLANNING
            final_decision = await self._finalize_decision(
                trading_plan, market_data, reasoning_result
            )
            
            # Store decision for future learning
            decision_record = {
                'decision_id': decision_id,
                'market_data': market_data,
                'memory_context': memory_context,
                'reasoning_result': reasoning_result,
                'trading_plan': trading_plan,
                'final_decision': final_decision,
                'timestamp': start_time,
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
            
            self.decision_history.append(decision_record)
            self.total_decisions += 1
            
            logger.info(f"✅ Decision {decision_id} completed in {decision_record['processing_time']:.2f}s")
            return final_decision
            
        except Exception as e:
            logger.error(f"❌ Market signal processing failed: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reason': f'Processing error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
            
    async def _apply_reflection(self, market_data: Dict[str, Any], 
                               memory_context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply reflection insights from past experiences"""
        try:
            # Get similar past episodes
            similar_episodes = memory_context.get('similar_episodes', [])
            
            if not similar_episodes:
                return {'insights': [], 'confidence_adjustment': 0.0}
                
            # Analyze patterns in similar episodes
            success_rate = sum(1 for ep in similar_episodes if ep.success_score > 0.6) / len(similar_episodes)
            avg_success_score = sum(ep.success_score for ep in similar_episodes) / len(similar_episodes)
            
            insights = []
            confidence_adjustment = 0.0
            
            if success_rate > 0.7:
                insights.append("Historical data shows high success rate for similar conditions")
                confidence_adjustment = 0.1
            elif success_rate < 0.3:
                insights.append("Historical data shows low success rate for similar conditions")
                confidence_adjustment = -0.2
                
            # Extract lessons from past episodes
            all_lessons = []
            for episode in similar_episodes:
                all_lessons.extend(episode.lessons_learned)
                
            # Find common lessons
            lesson_counts = {}
            for lesson in all_lessons:
                lesson_counts[lesson] = lesson_counts.get(lesson, 0) + 1
                
            common_lessons = [lesson for lesson, count in lesson_counts.items() 
                            if count >= len(similar_episodes) * 0.3]  # 30% threshold
            
            return {
                'insights': insights,
                'confidence_adjustment': confidence_adjustment,
                'success_rate': success_rate,
                'avg_success_score': avg_success_score,
                'common_lessons': common_lessons,
                'similar_episodes_count': len(similar_episodes)
            }
            
        except Exception as e:
            logger.error(f"❌ Reflection application failed: {e}")
            return {'insights': [], 'confidence_adjustment': 0.0}
            
    async def _create_trading_plan(self, market_data: Dict[str, Any], 
                                  memory_context: Dict[str, Any],
                                  reasoning_result: Dict[str, Any],
                                  reflection_insights: Dict[str, Any]) -> Optional[TradingPlan]:
        """Create a comprehensive trading plan"""
        try:
            plan_id = f"plan_{uuid.uuid4().hex[:8]}"
            
            # Determine goal based on reasoning
            recommendation = reasoning_result.get('recommendation', 'HOLD')
            confidence = reasoning_result.get('confidence', 0.5)
            
            # Apply reflection adjustments
            confidence += reflection_insights.get('confidence_adjustment', 0.0)
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            
            if recommendation == 'HOLD' or confidence < 0.3:
                return None  # No action needed
                
            # Create goal string
            symbol = market_data.get('symbol', 'UNKNOWN')
            goal = f"{recommendation} {symbol} with confidence {confidence:.2f}"
            
            # Define constraints
            constraints = {
                'max_position_size': 0.1,  # 10% of portfolio
                'max_loss': 0.05,  # 5% max loss
                'time_limit': 300,  # 5 minutes max
                'confidence_threshold': 0.3
            }
            
            # Decompose goal into steps
            steps = await self.decomposition_engine.decompose_trading_goal(
                goal, market_data, constraints
            )
            
            if not steps:
                return None
                
            # Calculate risk assessment
            risk_assessment = self._calculate_risk_assessment(
                market_data, confidence, constraints
            )
            
            # Create trading plan
            plan = TradingPlan(
                plan_id=plan_id,
                goal=goal,
                market_context=market_data,
                steps=steps,
                total_confidence=confidence,
                risk_assessment=risk_assessment,
                created_at=datetime.now(),
                estimated_completion=datetime.now() + timedelta(seconds=sum(step.estimated_duration for step in steps))
            )
            
            self.current_plans[plan_id] = plan
            logger.info(f"📋 Trading plan {plan_id} created with {len(steps)} steps")
            
            return plan
            
        except Exception as e:
            logger.error(f"❌ Trading plan creation failed: {e}")
            return None
            
    def _calculate_risk_assessment(self, market_data: Dict[str, Any], 
                                  confidence: float, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk assessment"""
        price = market_data.get('price', 0)
        volatility = abs(market_data.get('price_change_percent', 0))
        
        # Base position size on confidence and volatility
        base_position_size = constraints['max_position_size']
        volatility_adjustment = max(0.5, 1.0 - (volatility / 20.0))  # Reduce size for high volatility
        confidence_adjustment = confidence
        
        adjusted_position_size = base_position_size * volatility_adjustment * confidence_adjustment
        
        # Calculate expected profit/loss
        expected_return = confidence * 0.05  # 5% expected return at full confidence
        expected_profit = adjusted_position_size * expected_return
        max_loss = adjusted_position_size * constraints['max_loss']
        
        return {
            'position_size': adjusted_position_size,
            'expected_profit': expected_profit,
            'max_loss': max_loss,
            'risk_reward_ratio': expected_profit / max_loss if max_loss > 0 else 0,
            'volatility_score': volatility,
            'confidence_score': confidence
        }
        
    async def _finalize_decision(self, trading_plan: Optional[TradingPlan], 
                                market_data: Dict[str, Any],
                                reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the trading decision"""
        if not trading_plan:
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reason': 'No viable trading plan generated',
                'timestamp': datetime.now().isoformat()
            }
            
        # Extract key information
        recommendation = reasoning_result.get('recommendation', 'HOLD')
        confidence = trading_plan.total_confidence
        position_size = trading_plan.risk_assessment.get('position_size', 0)
        
        # Create final decision
        decision = {
            'action': recommendation,
            'confidence': confidence,
            'position_size': position_size,
            'symbol': market_data.get('symbol', 'UNKNOWN'),
            'price': market_data.get('price', 0),
            'plan_id': trading_plan.plan_id,
            'steps_count': len(trading_plan.steps),
            'estimated_duration': (trading_plan.estimated_completion - trading_plan.created_at).total_seconds(),
            'risk_assessment': trading_plan.risk_assessment,
            'reasoning_summary': reasoning_result.get('final_reasoning', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"🎯 Final decision: {recommendation} {decision['symbol']} "
                   f"(confidence: {confidence:.2f}, size: {position_size:.4f})")
        
        return decision
        
    async def record_outcome(self, decision_id: str, outcome: Dict[str, Any]) -> None:
        """Record the outcome of a trading decision for learning"""
        try:
            # Find the original decision
            decision_record = None
            for record in self.decision_history:
                if record['decision_id'] == decision_id:
                    decision_record = record
                    break
                    
            if not decision_record:
                logger.warning(f"⚠️ Decision {decision_id} not found for outcome recording")
                return
                
            # Update performance metrics
            profit_loss = outcome.get('profit_loss', 0)
            self.total_profit_loss += profit_loss
            
            if profit_loss > 0:
                self.successful_decisions += 1
                
            # Create trading episode for episodic memory
            episode = TradingEpisode(
                episode_id=f"episode_{uuid.uuid4().hex[:8]}",
                market_context=decision_record['market_data'],
                decision_made=decision_record['final_decision'],
                outcome=outcome,
                lessons_learned=outcome.get('lessons_learned', []),
                timestamp=decision_record['timestamp'],
                success_score=min(1.0, max(0.0, profit_loss / 0.05))  # Normalize to [0, 1]
            )
            
            # Store episode in memory
            await self.memory_system.add_trading_episode(episode)
            
            # Apply reflection if we have a trading plan
            trading_plan = decision_record.get('trading_plan')
            if trading_plan:
                reflection = await self.reflection_engine.reflect_on_outcome(trading_plan, outcome)
                if reflection:
                    logger.info(f"🤔 Reflection completed: {len(reflection.lessons_learned)} lessons learned")
                    
            logger.info(f"📊 Outcome recorded for decision {decision_id}: "
                       f"P&L: {profit_loss:.4f}, Success rate: {self.get_success_rate():.2f}")
                       
        except Exception as e:
            logger.error(f"❌ Outcome recording failed: {e}")
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        success_rate = self.get_success_rate()
        avg_profit = self.total_profit_loss / max(1, self.total_decisions)
        
        return {
            'total_decisions': self.total_decisions,
            'successful_decisions': self.successful_decisions,
            'success_rate': success_rate,
            'total_profit_loss': self.total_profit_loss,
            'average_profit_per_decision': avg_profit,
            'active_plans': len(self.current_plans),
            'memory_stats': self.memory_system.get_memory_stats(),
            'current_phase': self.active_phase.value
        }
        
    def get_success_rate(self) -> float:
        """Calculate current success rate"""
        if self.total_decisions == 0:
            return 0.0
        return self.successful_decisions / self.total_decisions
        
    async def query_brain_memory(self, query: str) -> Dict[str, Any]:
        """Query the brain's memory systems"""
        return await self.memory_system.query_memory(query)
        
    async def shutdown(self) -> None:
        """Gracefully shutdown the brain orchestrator"""
        try:
            # Save any pending data
            logger.info("🔄 Shutting down Enhanced Brain Orchestrator...")
            
            # Close MongoDB connections if available
            if hasattr(self.memory_system.advanced_rag, 'client') and self.memory_system.advanced_rag.client:
                self.memory_system.advanced_rag.client.close()
                
            logger.info("✅ Enhanced Brain Orchestrator shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")
