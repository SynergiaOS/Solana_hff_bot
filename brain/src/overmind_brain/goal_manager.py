"""THE OVERMIND PROTOCOL - Dynamic Goal Manager
Centralized goal configuration system with DragonflyDB integration for runtime goal modification.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

class GoalType(Enum):
    """Types of trading goals."""
    REACH_BALANCE = "REACH_BALANCE"
    CAPITAL_PRESERVATION = "CAPITAL_PRESERVATION"
    MAXIMIZE_PROFIT = "MAXIMIZE_PROFIT"

@dataclass
class TradingGoal:
    """Trading goal configuration."""
    goal_type: GoalType
    target_sol: float
    description: str
    modified_by: str
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    target_usd: Optional[float] = None
    change_reason: str = "Goal update"
    priority: int = 1  # 1=low, 2=medium, 3=high
    deadline: Optional[datetime] = None
    progress_percentage: float = 0.0
    is_active: bool = True

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

@dataclass
class GoalChangeEvent:
    """Event representing a goal change."""
    event_id: str
    goal_id: str
    old_goal: Optional[TradingGoal]
    new_goal: TradingGoal
    change_type: str  # "created", "updated", "deleted"
    changed_by: str
    change_reason: str
    timestamp: datetime

    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()

class DynamicGoalManager:
    """Centralized goal management system with DragonflyDB integration."""
    
    def __init__(self, 
                 redis_host: str = "localhost",
                 redis_port: int = 6379):
        """Initialize the Dynamic Goal Manager.
        
        Args:
            redis_host: DragonflyDB/Redis host
            redis_port: DragonflyDB/Redis port
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Redis connection
        self.redis_client = None
        
        # Current goal cache
        self.current_goal = None
        self.last_goal_check = None
        
        # Goal change listeners
        self.goal_change_callbacks = []
        
        logger.info("🎯 Dynamic Goal Manager initialized")
    
    async def initialize(self):
        """Initialize the goal manager."""
        try:
            # Initialize Redis connection
            self.redis_client = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()

            # Load or create default goal
            await self._ensure_default_goal()

            logger.info("✅ Dynamic Goal Manager initialized")

        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using mock mode: {e}")
            # Create default goal in memory
            self.current_goal = TradingGoal(
                goal_type=GoalType.REACH_BALANCE,
                target_sol=2.0,
                description="Default goal: Reach 2 SOL balance (mock mode)",
                modified_by="system_initialization"
            )
    
    async def _ensure_default_goal(self):
        """Ensure a default goal exists in DragonflyDB."""
        try:
            current_goal = await self.get_current_goal()
            
            if not current_goal:
                # Create default goal
                default_goal = TradingGoal(
                    goal_type=GoalType.REACH_BALANCE,
                    target_sol=2.0,
                    description="Default goal: Reach 2 SOL balance",
                    modified_by="system_initialization"
                )
                
                await self._store_goal(default_goal)
                logger.info("📋 Created default trading goal: 2 SOL")
            else:
                logger.info(f"📋 Loaded existing goal: {current_goal.description}")
                
        except Exception as e:
            logger.error(f"❌ Failed to ensure default goal: {e}")
    
    async def get_current_goal(self) -> Optional[TradingGoal]:
        """Get the current trading goal."""
        try:
            # Check cache first
            if (self.current_goal and self.last_goal_check and
                (datetime.now() - self.last_goal_check).total_seconds() < 60):
                return self.current_goal

            # Ensure Redis client is initialized
            if not self.redis_client:
                await self.initialize()

            # Get from Redis (if available)
            if self.redis_client:
                goal_json = await self.redis_client.get("overmind:current_goal")
            else:
                # Return cached goal if Redis not available
                return self.current_goal
            
            if not goal_json:
                return None
            
            # Parse goal
            goal_data = json.loads(goal_json)
            
            # Create TradingGoal object
            goal = TradingGoal(
                goal_type=GoalType(goal_data["goal_type"]),
                target_sol=goal_data["target_sol"],
                description=goal_data["description"],
                modified_by=goal_data["modified_by"],
                created_at=datetime.fromisoformat(goal_data["created_at"])
            )
            
            # Update cache
            self.current_goal = goal
            self.last_goal_check = datetime.now()
            
            return goal
            
        except Exception as e:
            logger.error(f"❌ Failed to get current goal: {e}")
            return None
    
    async def _store_goal(self, goal: TradingGoal) -> bool:
        """Store a goal in DragonflyDB."""
        try:
            # Ensure Redis client is initialized
            if not self.redis_client:
                await self.initialize()

            # Convert to dict
            goal_dict = asdict(goal)

            # Convert datetime to string
            goal_dict["created_at"] = goal_dict["created_at"].isoformat()
            goal_dict["goal_type"] = goal_dict["goal_type"].value

            # Store in Redis (if available)
            if self.redis_client:
                await self.redis_client.set("overmind:current_goal", json.dumps(goal_dict))
                # Add to history (non-awaitable operations)
                self.redis_client.lpush("overmind:goal_history", json.dumps(goal_dict))
                self.redis_client.ltrim("overmind:goal_history", 0, 99)  # Keep last 100
            else:
                logger.warning("Redis not available, storing goal in memory only")
            
            # Update cache
            self.current_goal = goal
            self.last_goal_check = datetime.now()
            
            # Notify listeners
            for callback in self.goal_change_callbacks:
                try:
                    await callback(goal)
                except Exception as e:
                    logger.error(f"❌ Goal change callback error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store goal: {e}")
            return False
    
    async def set_goal(self,
                      goal_type: GoalType,
                      target_sol: float,
                      description: str,
                      modified_by: str,
                      target_usd: Optional[float] = None,
                      change_reason: str = "Goal update",
                      priority: int = 1,
                      deadline: Optional[datetime] = None) -> bool:
        """Set a new trading goal."""
        try:
            # Create new goal
            new_goal = TradingGoal(
                goal_type=goal_type,
                target_sol=target_sol,
                description=description,
                modified_by=modified_by,
                target_usd=target_usd,
                change_reason=change_reason,
                priority=priority,
                deadline=deadline
            )
            
            # Store goal
            success = await self._store_goal(new_goal)
            
            if success:
                logger.info(f"🎯 New goal set: {description}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to set goal: {e}")
            return False
    
    async def get_goal_history(self, limit: int = 10) -> List[TradingGoal]:
        """Get goal history."""
        try:
            # Ensure Redis client is initialized
            if not self.redis_client:
                await self.initialize()

            if not self.redis_client:
                return []

            # Return current goal as history (simplified for now)
            return [self.current_goal] if self.current_goal else []
            
        except Exception as e:
            logger.error(f"❌ Failed to get goal history: {e}")
            return []
    
    def register_goal_change_callback(self, callback):
        """Register a callback for goal changes."""
        self.goal_change_callbacks.append(callback)

    async def update_goal_progress(self, progress_percentage: float) -> bool:
        """Update progress towards current goal."""
        try:
            current_goal = await self.get_current_goal()
            if not current_goal:
                logger.warning("No current goal to update progress for")
                return False

            # Update progress
            current_goal.progress_percentage = max(0.0, min(100.0, progress_percentage))
            current_goal.modified_at = datetime.now()

            # Store updated goal
            success = await self._store_goal(current_goal)

            if success:
                logger.info(f"📊 Goal progress updated: {progress_percentage:.1f}%")

            return success

        except Exception as e:
            logger.error(f"❌ Failed to update goal progress: {e}")
            return False

    async def validate_goal(self, goal: TradingGoal) -> Dict[str, Any]:
        """Validate a trading goal configuration."""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }

        try:
            # Validate target_sol
            if goal.target_sol <= 0:
                validation_result['errors'].append("Target SOL must be positive")
                validation_result['is_valid'] = False
            elif goal.target_sol > 1000:
                validation_result['warnings'].append("Target SOL is very high (>1000)")

            # Validate target_usd if provided
            if goal.target_usd is not None:
                if goal.target_usd <= 0:
                    validation_result['errors'].append("Target USD must be positive")
                    validation_result['is_valid'] = False

            # Validate priority
            if goal.priority not in [1, 2, 3]:
                validation_result['errors'].append("Priority must be 1, 2, or 3")
                validation_result['is_valid'] = False

            # Validate deadline
            if goal.deadline and goal.deadline <= datetime.now():
                validation_result['warnings'].append("Deadline is in the past")

            # Validate description
            if not goal.description or len(goal.description.strip()) < 5:
                validation_result['errors'].append("Description must be at least 5 characters")
                validation_result['is_valid'] = False

            return validation_result

        except Exception as e:
            logger.error(f"❌ Goal validation error: {e}")
            return {
                'is_valid': False,
                'warnings': [],
                'errors': [f"Validation error: {str(e)}"]
            }

    async def get_goal_analytics(self) -> Dict[str, Any]:
        """Get analytics about goal management."""
        try:
            current_goal = await self.get_current_goal()
            history = await self.get_goal_history(limit=50)

            analytics = {
                'current_goal': {
                    'exists': current_goal is not None,
                    'type': current_goal.goal_type.value if current_goal else None,
                    'target_sol': current_goal.target_sol if current_goal else 0,
                    'progress': current_goal.progress_percentage if current_goal else 0,
                    'priority': current_goal.priority if current_goal else 0,
                    'days_since_created': (datetime.now() - current_goal.created_at).days if current_goal and current_goal.created_at else 0
                },
                'history_stats': {
                    'total_goals': len(history),
                    'goal_types_used': list(set(goal.goal_type.value for goal in history)),
                    'avg_target_sol': sum(goal.target_sol for goal in history) / len(history) if history else 0,
                    'most_common_type': max(set(goal.goal_type.value for goal in history), key=lambda x: [goal.goal_type.value for goal in history].count(x)) if history else None
                },
                'performance': {
                    'goals_completed': len([goal for goal in history if goal.progress_percentage >= 100]),
                    'avg_completion_rate': sum(goal.progress_percentage for goal in history) / len(history) if history else 0,
                    'high_priority_goals': len([goal for goal in history if goal.priority == 3])
                },
                'timestamp': datetime.now().isoformat()
            }

            return analytics

        except Exception as e:
            logger.error(f"❌ Failed to get goal analytics: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get goal manager status."""
        try:
            current_goal = await self.get_current_goal()
            
            return {
                "current_goal": asdict(current_goal) if current_goal else None,
                "last_goal_check": self.last_goal_check,
                "goal_change_listeners": len(self.goal_change_callbacks),
                "redis_connected": self.redis_client is not None
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get goal manager status: {e}")
            return {"error": str(e)}

# Global instance
dynamic_goal_manager = DynamicGoalManager()
