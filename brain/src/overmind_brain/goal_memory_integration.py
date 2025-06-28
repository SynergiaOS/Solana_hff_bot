"""
THE OVERMIND PROTOCOL - Goal Memory Integration
Enhanced integration between goal management and vector memory for intelligent goal tracking
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import asdict

from .goal_manager import dynamic_goal_manager, TradingGoal, GoalType
from .chroma_vector_memory import ChromaVectorMemory

logger = logging.getLogger(__name__)

class GoalMemoryIntegration:
    """
    Integration layer between goal management and vector memory
    Stores goal-related experiences and provides intelligent goal recommendations
    """
    
    def __init__(self):
        self.goal_manager = dynamic_goal_manager
        self.vector_memory = ChromaVectorMemory(collection_name="goal_memories")
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the goal memory integration"""
        try:
            # Initialize goal manager
            await self.goal_manager.initialize()
            
            # Register goal change callback
            self.goal_manager.register_goal_change_callback(self._on_goal_change)
            
            self.initialized = True
            logger.info("Goal Memory Integration initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Goal Memory Integration: {e}")
            return False
    
    async def _on_goal_change(self, new_goal: TradingGoal):
        """Callback for when goals change - store in vector memory"""
        try:
            # Create memory text for the goal change
            goal_memory_text = f"""
            Goal Change Event:
            Type: {new_goal.goal_type.value}
            Target SOL: {new_goal.target_sol}
            Target USD: {new_goal.target_usd or 'Not specified'}
            Description: {new_goal.description}
            Priority: {new_goal.priority}
            Changed by: {new_goal.modified_by}
            Reason: {new_goal.change_reason}
            Deadline: {new_goal.deadline.isoformat() if new_goal.deadline else 'No deadline'}
            """
            
            # Store in vector memory
            metadata = {
                'type': 'goal_change',
                'goal_type': new_goal.goal_type.value,
                'target_sol': new_goal.target_sol,
                'priority': new_goal.priority,
                'modified_by': new_goal.modified_by,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            memory_id = self.vector_memory.add_memory(goal_memory_text, metadata)
            logger.info(f"📝 Stored goal change in vector memory: {memory_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store goal change in memory: {e}")
    
    async def store_goal_achievement(self, goal: TradingGoal, achievement_data: Dict[str, Any]):
        """Store goal achievement in vector memory"""
        try:
            achievement_text = f"""
            Goal Achievement:
            Goal Type: {goal.goal_type.value}
            Target: {goal.target_sol} SOL
            Achieved: {achievement_data.get('achieved_amount', 0)} SOL
            Success Rate: {achievement_data.get('success_rate', 0):.2f}%
            Time Taken: {achievement_data.get('days_to_complete', 0)} days
            Strategy Used: {achievement_data.get('strategy', 'Unknown')}
            Market Conditions: {achievement_data.get('market_conditions', 'Unknown')}
            Key Factors: {achievement_data.get('key_factors', [])}
            """
            
            metadata = {
                'type': 'goal_achievement',
                'goal_type': goal.goal_type.value,
                'target_sol': goal.target_sol,
                'achieved_amount': achievement_data.get('achieved_amount', 0),
                'success_rate': achievement_data.get('success_rate', 0),
                'days_to_complete': achievement_data.get('days_to_complete', 0),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            memory_id = self.vector_memory.add_memory(achievement_text, metadata)
            logger.info(f"🏆 Stored goal achievement in vector memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store goal achievement: {e}")
            return None
    
    async def store_goal_failure(self, goal: TradingGoal, failure_data: Dict[str, Any]):
        """Store goal failure analysis in vector memory"""
        try:
            failure_text = f"""
            Goal Failure Analysis:
            Goal Type: {goal.goal_type.value}
            Target: {goal.target_sol} SOL
            Achieved: {failure_data.get('achieved_amount', 0)} SOL
            Failure Reason: {failure_data.get('failure_reason', 'Unknown')}
            Market Conditions: {failure_data.get('market_conditions', 'Unknown')}
            Lessons Learned: {failure_data.get('lessons_learned', [])}
            Recommended Changes: {failure_data.get('recommended_changes', [])}
            """
            
            metadata = {
                'type': 'goal_failure',
                'goal_type': goal.goal_type.value,
                'target_sol': goal.target_sol,
                'achieved_amount': failure_data.get('achieved_amount', 0),
                'failure_reason': failure_data.get('failure_reason', 'Unknown'),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            memory_id = self.vector_memory.add_memory(failure_text, metadata)
            logger.info(f"📉 Stored goal failure analysis in vector memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store goal failure: {e}")
            return None
    
    async def get_goal_recommendations(self, current_portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get intelligent goal recommendations based on past experiences"""
        try:
            current_sol = current_portfolio.get('total_value_sol', 0)
            current_usd = current_portfolio.get('total_value_usd', 0)
            
            # Query for similar portfolio situations
            query_text = f"""
            Portfolio situation: {current_sol} SOL, ${current_usd} USD
            Looking for goal recommendations based on similar past experiences
            """
            
            # Find relevant memories
            relevant_memories = self.vector_memory.find_similar(query_text, limit=10)
            
            # Analyze memories to generate recommendations
            recommendations = []
            
            # Analyze successful goal achievements
            successful_goals = [
                memory for memory in relevant_memories 
                if memory.get('type') == 'goal_achievement'
            ]
            
            if successful_goals:
                # Recommend based on successful patterns
                for success in successful_goals[:3]:
                    target_sol = success.get('target_sol', current_sol * 1.5)
                    success_rate = success.get('success_rate', 0)
                    
                    if success_rate > 70:  # High success rate
                        recommendations.append({
                            'goal_type': success.get('goal_type', 'REACH_BALANCE'),
                            'target_sol': target_sol,
                            'confidence': success_rate / 100,
                            'reasoning': f"Similar portfolio achieved {target_sol} SOL with {success_rate}% success rate",
                            'priority': 2,
                            'estimated_days': success.get('days_to_complete', 30)
                        })
            
            # Add conservative recommendation
            if current_sol > 0:
                recommendations.append({
                    'goal_type': 'CAPITAL_PRESERVATION',
                    'target_sol': current_sol * 1.1,  # 10% increase
                    'confidence': 0.8,
                    'reasoning': "Conservative growth based on current portfolio",
                    'priority': 1,
                    'estimated_days': 14
                })
            
            # Add aggressive recommendation
            recommendations.append({
                'goal_type': 'MAXIMIZE_PROFIT',
                'target_sol': current_sol * 2.0,  # Double portfolio
                'confidence': 0.6,
                'reasoning': "Aggressive growth opportunity",
                'priority': 3,
                'estimated_days': 60
            })
            
            # Sort by confidence
            recommendations.sort(key=lambda x: x['confidence'], reverse=True)
            
            return recommendations[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"❌ Failed to get goal recommendations: {e}")
            return []
    
    async def analyze_goal_performance(self, goal_type: GoalType, days: int = 30) -> Dict[str, Any]:
        """Analyze performance of specific goal type over time"""
        try:
            # Query for goal achievements and failures of this type
            query_text = f"Goal type: {goal_type.value} achievements and failures"
            
            relevant_memories = self.vector_memory.find_similar(query_text, limit=50)
            
            # Filter for this goal type
            goal_memories = [
                memory for memory in relevant_memories
                if memory.get('goal_type') == goal_type.value and
                memory.get('type') in ['goal_achievement', 'goal_failure']
            ]
            
            if not goal_memories:
                return {
                    'goal_type': goal_type.value,
                    'analysis': 'No historical data available',
                    'recommendations': []
                }
            
            # Analyze performance
            achievements = [m for m in goal_memories if m.get('type') == 'goal_achievement']
            failures = [m for m in goal_memories if m.get('type') == 'goal_failure']
            
            total_attempts = len(achievements) + len(failures)
            success_rate = len(achievements) / total_attempts * 100 if total_attempts > 0 else 0
            
            avg_target = sum(m.get('target_sol', 0) for m in goal_memories) / len(goal_memories)
            avg_achieved = sum(m.get('achieved_amount', 0) for m in achievements) / len(achievements) if achievements else 0
            avg_completion_time = sum(m.get('days_to_complete', 0) for m in achievements) / len(achievements) if achievements else 0
            
            analysis = {
                'goal_type': goal_type.value,
                'total_attempts': total_attempts,
                'successes': len(achievements),
                'failures': len(failures),
                'success_rate': success_rate,
                'avg_target_sol': avg_target,
                'avg_achieved_sol': avg_achieved,
                'avg_completion_days': avg_completion_time,
                'performance_rating': 'HIGH' if success_rate > 70 else 'MEDIUM' if success_rate > 40 else 'LOW',
                'recommendations': []
            }
            
            # Generate recommendations based on analysis
            if success_rate > 70:
                analysis['recommendations'].append("This goal type has high success rate - recommended")
            elif success_rate < 40:
                analysis['recommendations'].append("This goal type has low success rate - consider alternatives")
            
            if avg_completion_time > 60:
                analysis['recommendations'].append("Goals of this type take long time - set realistic deadlines")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze goal performance: {e}")
            return {
                'goal_type': goal_type.value,
                'error': str(e)
            }
    
    async def get_goal_insights(self) -> Dict[str, Any]:
        """Get comprehensive insights about goal management"""
        try:
            # Get current goal
            current_goal = await self.goal_manager.get_current_goal()
            
            # Get goal analytics
            analytics = await self.goal_manager.get_goal_analytics()
            
            # Get memory statistics
            memory_stats = self.vector_memory.get_stats()
            
            # Analyze each goal type
            goal_type_analysis = {}
            for goal_type in GoalType:
                analysis = await self.analyze_goal_performance(goal_type)
                goal_type_analysis[goal_type.value] = analysis
            
            insights = {
                'current_goal_status': {
                    'has_goal': current_goal is not None,
                    'goal_type': current_goal.goal_type.value if current_goal else None,
                    'progress': current_goal.progress_percentage if current_goal else 0,
                    'priority': current_goal.priority if current_goal else 0
                },
                'historical_performance': analytics,
                'memory_integration': {
                    'total_memories': memory_stats.get('memories_stored', 0),
                    'goal_related_memories': len([
                        m for m in self.vector_memory.find_similar("goal", limit=100)
                        if m.get('type', '').startswith('goal_')
                    ])
                },
                'goal_type_analysis': goal_type_analysis,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Failed to get goal insights: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

# Global instance
goal_memory_integration = GoalMemoryIntegration()
