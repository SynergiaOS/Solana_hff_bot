"""THE OVERMIND PROTOCOL - Dynamic Goal Manager
Centralized goal configuration system with DragonflyDB integration for runtime goal modification.
"""

import asyncio
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
    target_usd: Optional[float] = None
    is_active: bool = True
    created_at: str = ""
    modified_at: str = ""
    modified_by: str = "system"
    description: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.modified_at:
            self.modified_at = datetime.utcnow().isoformat()
        if not self.description:
            self.description = f"{self.goal_type.value}: Target {self.target_sol} SOL"

@dataclass
class GoalChangeEvent:
    """Goal change event for audit trail."""
    event_id: str
    old_goal: Optional[TradingGoal]
    new_goal: TradingGoal
    change_reason: str
    changed_by: str
    timestamp: str
    impact_assessment: Dict[str, Any]

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
            logger.error(f"❌ Failed to initialize Dynamic Goal Manager: {e}")
            raise
    
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
        """Get the current active trading goal."""
        try:
            goal_data = await self.redis_client.get("config:trading_goals")
            
            if goal_data:
                goal_dict = json.loads(goal_data)
                
                # Convert goal_type string back to enum
                goal_dict["goal_type"] = GoalType(goal_dict["goal_type"])
                
                goal = TradingGoal(**goal_dict)
                self.current_goal = goal
                return goal
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get current goal: {e}")
            return None
    
    async def set_goal(self, 
                      goal_type: GoalType, 
                      target_sol: float,
                      target_usd: Optional[float] = None,
                      changed_by: str = "user",
                      change_reason: str = "Manual goal update") -> bool:
        """Set a new trading goal.
        
        Args:
            goal_type: Type of goal
            target_sol: Target SOL amount
            target_usd: Optional target USD amount
            changed_by: Who made the change
            change_reason: Reason for the change
            
        Returns:
            bool: True if goal was set successfully
        """
        try:
            # Validate goal parameters
            validation_result = await self._validate_goal(goal_type, target_sol, target_usd)
            if not validation_result["valid"]:
                logger.error(f"❌ Goal validation failed: {validation_result['reason']}")
                return False
            
            # Get current goal for change tracking
            old_goal = await self.get_current_goal()
            
            # Create new goal
            new_goal = TradingGoal(
                goal_type=goal_type,
                target_sol=target_sol,
                target_usd=target_usd,
                modified_by=changed_by,
                modified_at=datetime.utcnow().isoformat()
            )
            
            # Calculate impact assessment
            impact_assessment = await self._calculate_impact_assessment(old_goal, new_goal)
            
            # Store new goal atomically
            success = await self._store_goal(new_goal)
            
            if success:
                # Create change event
                change_event = GoalChangeEvent(
                    event_id=f"goal_change_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                    old_goal=old_goal,
                    new_goal=new_goal,
                    change_reason=change_reason,
                    changed_by=changed_by,
                    timestamp=datetime.utcnow().isoformat(),
                    impact_assessment=impact_assessment
                )
                
                # Store change event
                await self._store_goal_change_event(change_event)
                
                # Update last modified timestamp
                await self.redis_client.set(
                    "config:trading_goals:last_modified",
                    datetime.utcnow().isoformat()
                )
                
                # Notify listeners
                await self._notify_goal_change_listeners(change_event)
                
                logger.info(f"✅ Goal updated: {old_goal.description if old_goal else 'None'} → {new_goal.description}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to set goal: {e}")
            return False
    
    async def _validate_goal(self, 
                           goal_type: GoalType, 
                           target_sol: float, 
                           target_usd: Optional[float]) -> Dict[str, Any]:
        """Validate goal parameters."""
        try:
            # Basic validation
            if target_sol <= 0:
                return {"valid": False, "reason": "target_sol must be greater than 0"}
            
            if target_sol > 1000:  # Reasonable upper limit
                return {"valid": False, "reason": "target_sol cannot exceed 1000 SOL"}
            
            if target_usd is not None and target_usd <= 0:
                return {"valid": False, "reason": "target_usd must be greater than 0 if specified"}
            
            # Goal type specific validation
            if goal_type == GoalType.CAPITAL_PRESERVATION and target_sol < 0.1:
                return {"valid": False, "reason": "CAPITAL_PRESERVATION requires at least 0.1 SOL"}
            
            return {"valid": True, "reason": "Goal parameters are valid"}
            
        except Exception as e:
            return {"valid": False, "reason": f"Validation error: {e}"}
    
    async def _calculate_impact_assessment(self, 
                                         old_goal: Optional[TradingGoal], 
                                         new_goal: TradingGoal) -> Dict[str, Any]:
        """Calculate the impact of goal change on trading behavior."""
        try:
            impact = {
                "goal_type_changed": False,
                "target_increased": False,
                "target_decreased": False,
                "percentage_change": 0.0,
                "profile_change_likely": False,
                "risk_level_change": "none"
            }
            
            if old_goal:
                # Check goal type change
                impact["goal_type_changed"] = old_goal.goal_type != new_goal.goal_type
                
                # Check target change
                target_change = new_goal.target_sol - old_goal.target_sol
                impact["target_increased"] = target_change > 0
                impact["target_decreased"] = target_change < 0
                impact["percentage_change"] = (target_change / old_goal.target_sol) * 100
                
                # Assess profile change likelihood
                # This would trigger profile re-evaluation in StrategyMapper
                impact["profile_change_likely"] = abs(impact["percentage_change"]) > 10
                
                # Assess risk level change
                if new_goal.goal_type == GoalType.MAXIMIZE_PROFIT:
                    impact["risk_level_change"] = "increased"
                elif new_goal.goal_type == GoalType.CAPITAL_PRESERVATION:
                    impact["risk_level_change"] = "decreased"
                elif old_goal.goal_type != new_goal.goal_type:
                    impact["risk_level_change"] = "modified"
            
            return impact
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate impact assessment: {e}")
            return {}
    
    async def _store_goal(self, goal: TradingGoal) -> bool:
        """Store goal in DragonflyDB atomically."""
        try:
            goal_data = asdict(goal)
            # Convert enum to string for JSON serialization
            goal_data["goal_type"] = goal.goal_type.value
            
            # Store atomically
            await self.redis_client.set(
                "config:trading_goals",
                json.dumps(goal_data, default=str)
            )
            
            # Update cache
            self.current_goal = goal
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store goal: {e}")
            return False
    
    async def _store_goal_change_event(self, event: GoalChangeEvent):
        """Store goal change event for audit trail."""
        try:
            event_data = asdict(event)
            
            # Convert enums to strings
            if event.old_goal:
                event_data["old_goal"]["goal_type"] = event.old_goal.goal_type.value
            event_data["new_goal"]["goal_type"] = event.new_goal.goal_type.value
            
            # Store in goal change history
            await self.redis_client.lpush(
                "history:goal_changes",
                json.dumps(event_data, default=str)
            )
            
            # Keep only last 1000 changes
            await self.redis_client.ltrim("history:goal_changes", 0, 999)
            
        except Exception as e:
            logger.error(f"❌ Failed to store goal change event: {e}")
    
    async def get_goal_history(self, limit: int = 10) -> List[GoalChangeEvent]:
        """Get goal change history."""
        try:
            history_data = await self.redis_client.lrange("history:goal_changes", 0, limit - 1)
            
            events = []
            for event_json in history_data:
                try:
                    event_dict = json.loads(event_json)
                    
                    # Convert goal type strings back to enums
                    if event_dict.get("old_goal"):
                        event_dict["old_goal"]["goal_type"] = GoalType(event_dict["old_goal"]["goal_type"])
                        event_dict["old_goal"] = TradingGoal(**event_dict["old_goal"])
                    
                    event_dict["new_goal"]["goal_type"] = GoalType(event_dict["new_goal"]["goal_type"])
                    event_dict["new_goal"] = TradingGoal(**event_dict["new_goal"])
                    
                    events.append(GoalChangeEvent(**event_dict))
                    
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"⚠️ Failed to parse goal change event: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"❌ Failed to get goal history: {e}")
            return []
    
    def add_goal_change_listener(self, callback):
        """Add a callback to be notified of goal changes."""
        self.goal_change_callbacks.append(callback)
    
    async def _notify_goal_change_listeners(self, event: GoalChangeEvent):
        """Notify all registered listeners of goal changes."""
        for callback in self.goal_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"❌ Error in goal change listener: {e}")
    
    async def check_for_goal_changes(self) -> bool:
        """Check if goals have changed since last check."""
        try:
            last_modified = await self.redis_client.get("config:trading_goals:last_modified")
            
            if last_modified and self.last_goal_check:
                if last_modified > self.last_goal_check:
                    self.last_goal_check = last_modified
                    return True
            elif last_modified:
                self.last_goal_check = last_modified
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to check for goal changes: {e}")
            return False
    
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
