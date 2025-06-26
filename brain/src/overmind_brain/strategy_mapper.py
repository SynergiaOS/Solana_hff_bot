"""THE OVERMIND PROTOCOL - Strategy Mapper
Intelligent decision engine that maps portfolio progress to appropriate strategy profiles.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import redis.asyncio as aioredis

from .strategy_profiles import StrategyProfile, ProfileType, strategy_profile_manager
from .portfolio_monitor import PortfolioState
from .goal_manager import dynamic_goal_manager

logger = logging.getLogger(__name__)

@dataclass
class ProfileSwitchDecision:
    """Decision data for profile switching."""
    current_profile: ProfileType
    recommended_profile: ProfileType
    should_switch: bool
    reason: str
    confidence: float
    hysteresis_triggered: bool
    time_since_last_switch: float
    decision_timestamp: str

@dataclass
class HysteresisState:
    """Hysteresis state for preventing rapid profile switching."""
    current_profile: ProfileType
    last_switch_time: datetime
    switch_count_24h: int
    buffer_zone_active: bool
    buffer_zone_percentage: float
    minimum_hold_time_minutes: int

class StrategyMapper:
    """Intelligent decision engine for mapping portfolio progress to strategy profiles."""
    
    def __init__(self, 
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 hysteresis_buffer: float = 2.0,
                 minimum_hold_time: int = 15):
        """Initialize the Strategy Mapper.
        
        Args:
            redis_host: DragonflyDB/Redis host
            redis_port: DragonflyDB/Redis port
            hysteresis_buffer: Buffer zone percentage to prevent rapid switching
            minimum_hold_time: Minimum hold time in minutes before allowing switch
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.hysteresis_buffer = hysteresis_buffer
        self.minimum_hold_time = minimum_hold_time
        
        # Redis connection
        self.redis_client = None
        
        # Current state
        self.current_profile = ProfileType.AGGRESSIVE_GROWTH  # Default starting profile
        self.hysteresis_state = None
        
        # Decision history
        self.decision_history = []
        self.max_history_entries = 1000

        # Goal change tracking
        self.last_goal_check = None
        self.current_goal_target = None

        logger.info(f"🎛️ Strategy Mapper initialized - Buffer: {hysteresis_buffer}%, Hold time: {minimum_hold_time}min")
    
    async def initialize(self):
        """Initialize the strategy mapper."""
        try:
            # Initialize Redis connection
            self.redis_client = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            # Load existing state
            await self._load_state()
            
            logger.info("✅ Strategy Mapper initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Strategy Mapper: {e}")
            raise
    
    async def _load_state(self):
        """Load existing hysteresis state from DragonflyDB."""
        try:
            state_data = await self.redis_client.get("state:strategy_mapper")
            
            if state_data:
                state_dict = json.loads(state_data)
                
                self.current_profile = ProfileType(state_dict["current_profile"])
                
                # Reconstruct hysteresis state
                hysteresis_data = state_dict.get("hysteresis_state", {})
                if hysteresis_data:
                    self.hysteresis_state = HysteresisState(
                        current_profile=ProfileType(hysteresis_data["current_profile"]),
                        last_switch_time=datetime.fromisoformat(hysteresis_data["last_switch_time"]),
                        switch_count_24h=hysteresis_data["switch_count_24h"],
                        buffer_zone_active=hysteresis_data["buffer_zone_active"],
                        buffer_zone_percentage=hysteresis_data["buffer_zone_percentage"],
                        minimum_hold_time_minutes=hysteresis_data["minimum_hold_time_minutes"]
                    )
                
                logger.info(f"📋 Loaded existing state - Current profile: {self.current_profile.value}")
            else:
                # Initialize default state
                await self._initialize_default_state()
                
        except Exception as e:
            logger.error(f"❌ Failed to load strategy mapper state: {e}")
            await self._initialize_default_state()
    
    async def _initialize_default_state(self):
        """Initialize default hysteresis state."""
        self.hysteresis_state = HysteresisState(
            current_profile=self.current_profile,
            last_switch_time=datetime.utcnow(),
            switch_count_24h=0,
            buffer_zone_active=False,
            buffer_zone_percentage=self.hysteresis_buffer,
            minimum_hold_time_minutes=self.minimum_hold_time
        )
        
        await self._save_state()
        logger.info("📋 Initialized default strategy mapper state")
    
    async def _save_state(self):
        """Save current state to DragonflyDB."""
        try:
            state_data = {
                "current_profile": self.current_profile.value,
                "hysteresis_state": asdict(self.hysteresis_state) if self.hysteresis_state else None,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Convert datetime to string for JSON serialization
            if self.hysteresis_state:
                state_data["hysteresis_state"]["last_switch_time"] = self.hysteresis_state.last_switch_time.isoformat()
            
            await self.redis_client.set(
                "state:strategy_mapper",
                json.dumps(state_data, default=str)
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to save strategy mapper state: {e}")

    async def _check_for_goal_changes(self) -> bool:
        """Check if trading goals have changed and trigger profile re-evaluation if needed."""
        try:
            # Check for goal changes using the goal manager
            goal_changed = await dynamic_goal_manager.check_for_goal_changes()

            if goal_changed:
                # Get the new goal
                current_goal = await dynamic_goal_manager.get_current_goal()

                if current_goal:
                    old_target = self.current_goal_target
                    self.current_goal_target = current_goal.target_sol

                    logger.info(f"🎯 Goal change detected: {old_target} SOL → {self.current_goal_target} SOL")

                    # Log goal change event
                    await self._log_goal_change_event(old_target, self.current_goal_target, current_goal.goal_type.value)

                    return True

            return False

        except Exception as e:
            logger.error(f"❌ Failed to check for goal changes: {e}")
            return False

    async def _log_goal_change_event(self, old_target: Optional[float], new_target: float, goal_type: str):
        """Log goal change event for audit trail."""
        try:
            goal_change_event = {
                "event_type": "GOAL_CHANGE_DETECTED",
                "old_target_sol": old_target,
                "new_target_sol": new_target,
                "goal_type": goal_type,
                "timestamp": datetime.utcnow().isoformat(),
                "impact": {
                    "requires_profile_reevaluation": True,
                    "percentage_change": ((new_target - old_target) / old_target * 100) if old_target else 0,
                    "hysteresis_reset": False  # We preserve hysteresis logic
                }
            }

            # Store in decision history
            await self.redis_client.lpush(
                "history:goal_changes",
                json.dumps(goal_change_event, default=str)
            )

            # Keep only last 100 goal change events
            await self.redis_client.ltrim("history:goal_changes", 0, 99)

            logger.info(f"📋 Goal change event logged: {goal_type} - {new_target} SOL")

        except Exception as e:
            logger.error(f"❌ Failed to log goal change event: {e}")

    def _calculate_base_profile_for_progress(self, progress_percentage: float) -> ProfileType:
        """Calculate base profile recommendation based on progress percentage."""
        if progress_percentage < 25.0:
            return ProfileType.AGGRESSIVE_GROWTH
        elif progress_percentage < 100.0:
            return ProfileType.BALANCED_RISK
        else:
            return ProfileType.CAPITAL_PRESERVATION
    
    def _check_hysteresis_conditions(self, 
                                   current_progress: float, 
                                   recommended_profile: ProfileType) -> Tuple[bool, str]:
        """Check hysteresis conditions to prevent rapid switching."""
        
        if not self.hysteresis_state:
            return True, "No hysteresis state - allowing switch"
        
        # Check minimum hold time
        time_since_switch = datetime.utcnow() - self.hysteresis_state.last_switch_time
        if time_since_switch.total_seconds() < (self.minimum_hold_time * 60):
            remaining_time = (self.minimum_hold_time * 60) - time_since_switch.total_seconds()
            return False, f"Minimum hold time not met - {remaining_time:.0f}s remaining"
        
        # Check if we're in a buffer zone
        if recommended_profile != self.current_profile:
            # Calculate buffer zones around transition points
            if self.current_profile == ProfileType.AGGRESSIVE_GROWTH and recommended_profile == ProfileType.BALANCED_RISK:
                # Buffer around 25% transition
                if 25.0 - self.hysteresis_buffer <= current_progress <= 25.0 + self.hysteresis_buffer:
                    return False, f"In hysteresis buffer zone around 25% transition"
            
            elif self.current_profile == ProfileType.BALANCED_RISK and recommended_profile == ProfileType.CAPITAL_PRESERVATION:
                # Buffer around 100% transition
                if 100.0 - self.hysteresis_buffer <= current_progress <= 100.0 + self.hysteresis_buffer:
                    return False, f"In hysteresis buffer zone around 100% transition"
            
            elif self.current_profile == ProfileType.BALANCED_RISK and recommended_profile == ProfileType.AGGRESSIVE_GROWTH:
                # Buffer around 25% transition (downward)
                if 25.0 - self.hysteresis_buffer <= current_progress <= 25.0 + self.hysteresis_buffer:
                    return False, f"In hysteresis buffer zone around 25% transition (downward)"
            
            elif self.current_profile == ProfileType.CAPITAL_PRESERVATION and recommended_profile == ProfileType.BALANCED_RISK:
                # Buffer around 100% transition (downward)
                if 100.0 - self.hysteresis_buffer <= current_progress <= 100.0 + self.hysteresis_buffer:
                    return False, f"In hysteresis buffer zone around 100% transition (downward)"
        
        # Check switch frequency (max 3 switches per 24 hours)
        if self.hysteresis_state.switch_count_24h >= 3:
            return False, "Maximum switches per 24 hours reached"
        
        return True, "Hysteresis conditions satisfied"
    
    async def determine_active_profile(self, portfolio_state: PortfolioState) -> ProfileSwitchDecision:
        """Determine the active profile based on portfolio state with hysteresis and dynamic goals."""

        # Check for goal changes first
        goal_changed = await self._check_for_goal_changes()

        # If goal changed, we need to recalculate progress with new target
        if goal_changed and self.current_goal_target:
            # Recalculate progress percentage with new goal
            current_sol = portfolio_state.total_value_sol
            recalculated_progress = min((current_sol / self.current_goal_target) * 100, 100.0)

            logger.info(f"🎯 Recalculated progress with new goal: {recalculated_progress:.1f}% "
                       f"(was {portfolio_state.goal_progress_percentage:.1f}%)")

            # Update portfolio state progress for this decision
            current_progress = recalculated_progress
        else:
            current_progress = portfolio_state.goal_progress_percentage
        
        # Calculate base recommendation
        recommended_profile = self._calculate_base_profile_for_progress(current_progress)
        
        # Check hysteresis conditions
        should_switch, hysteresis_reason = self._check_hysteresis_conditions(
            current_progress, recommended_profile
        )
        
        # Override should_switch if profiles are the same
        if recommended_profile == self.current_profile:
            should_switch = False
            hysteresis_reason = "Already using recommended profile"
        
        # Calculate confidence based on how far we are from transition points
        confidence = self._calculate_decision_confidence(current_progress, recommended_profile)
        
        # Create decision
        decision = ProfileSwitchDecision(
            current_profile=self.current_profile,
            recommended_profile=recommended_profile,
            should_switch=should_switch,
            reason=hysteresis_reason,
            confidence=confidence,
            hysteresis_triggered=not should_switch and recommended_profile != self.current_profile,
            time_since_last_switch=((datetime.utcnow() - self.hysteresis_state.last_switch_time).total_seconds() / 60) if self.hysteresis_state else 0,
            decision_timestamp=datetime.utcnow().isoformat()
        )
        
        # Log decision
        logger.info(f"🎯 Profile decision: {self.current_profile.value} → {recommended_profile.value} "
                   f"(switch: {should_switch}, confidence: {confidence:.2f}, progress: {current_progress:.1f}%)")
        
        # Store decision in history
        await self._store_decision(decision, portfolio_state)
        
        return decision
    
    def _calculate_decision_confidence(self, progress_percentage: float, recommended_profile: ProfileType) -> float:
        """Calculate confidence in the profile decision."""
        
        # Base confidence starts at 0.5
        confidence = 0.5
        
        # Increase confidence based on distance from transition points
        if recommended_profile == ProfileType.AGGRESSIVE_GROWTH:
            # More confident the further we are from 25%
            distance_from_transition = abs(25.0 - progress_percentage)
            confidence += min(0.4, distance_from_transition / 25.0 * 0.4)
        
        elif recommended_profile == ProfileType.BALANCED_RISK:
            # More confident the further we are from both 25% and 100%
            distance_from_25 = abs(25.0 - progress_percentage)
            distance_from_100 = abs(100.0 - progress_percentage)
            min_distance = min(distance_from_25, distance_from_100)
            confidence += min(0.4, min_distance / 37.5 * 0.4)  # 37.5 is half the range
        
        elif recommended_profile == ProfileType.CAPITAL_PRESERVATION:
            # More confident the further we are above 100%
            if progress_percentage >= 100.0:
                excess_progress = progress_percentage - 100.0
                confidence += min(0.4, excess_progress / 50.0 * 0.4)  # Cap at 150%
        
        return min(1.0, confidence)
    
    async def _store_decision(self, decision: ProfileSwitchDecision, portfolio_state: PortfolioState):
        """Store decision in history and DragonflyDB."""
        try:
            # Add to local history
            decision_record = {
                "decision": asdict(decision),
                "portfolio_state": {
                    "total_value_sol": portfolio_state.total_value_sol,
                    "goal_progress_percentage": portfolio_state.goal_progress_percentage,
                    "timestamp": portfolio_state.last_updated
                }
            }
            
            self.decision_history.append(decision_record)
            
            # Keep only last N entries
            if len(self.decision_history) > self.max_history_entries:
                self.decision_history = self.decision_history[-self.max_history_entries:]
            
            # Store in DragonflyDB
            await self.redis_client.lpush(
                "history:strategy_decisions",
                json.dumps(decision_record, default=str)
            )
            
            # Keep only last 1000 entries in Redis
            await self.redis_client.ltrim("history:strategy_decisions", 0, 999)
            
        except Exception as e:
            logger.error(f"❌ Failed to store decision: {e}")
    
    async def execute_profile_switch(self, decision: ProfileSwitchDecision) -> bool:
        """Execute a profile switch if recommended."""
        
        if not decision.should_switch:
            return False
        
        try:
            # Update current profile
            old_profile = self.current_profile
            self.current_profile = decision.recommended_profile
            
            # Update hysteresis state
            if self.hysteresis_state:
                self.hysteresis_state.current_profile = self.current_profile
                self.hysteresis_state.last_switch_time = datetime.utcnow()
                self.hysteresis_state.switch_count_24h += 1
                
                # Reset 24h counter if more than 24 hours have passed
                if (datetime.utcnow() - self.hysteresis_state.last_switch_time).total_seconds() > 86400:
                    self.hysteresis_state.switch_count_24h = 1
            
            # Save state
            await self._save_state()
            
            logger.info(f"🔄 Profile switched: {old_profile.value} → {self.current_profile.value}")
            
            # Publish profile change event
            await self._publish_profile_change_event(old_profile, self.current_profile, decision)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to execute profile switch: {e}")
            return False
    
    async def _publish_profile_change_event(self, 
                                          old_profile: ProfileType, 
                                          new_profile: ProfileType, 
                                          decision: ProfileSwitchDecision):
        """Publish profile change event to DragonflyDB."""
        try:
            event_data = {
                "event_type": "profile_change",
                "old_profile": old_profile.value,
                "new_profile": new_profile.value,
                "decision": asdict(decision),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.publish(
                "overmind:profile_changes",
                json.dumps(event_data, default=str)
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to publish profile change event: {e}")
    
    def get_current_profile(self) -> StrategyProfile:
        """Get the current active strategy profile."""
        return strategy_profile_manager.get_profile(self.current_profile)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get strategy mapper status."""
        return {
            "current_profile": self.current_profile.value,
            "hysteresis_state": asdict(self.hysteresis_state) if self.hysteresis_state else None,
            "decision_history_count": len(self.decision_history),
            "hysteresis_buffer": self.hysteresis_buffer,
            "minimum_hold_time": self.minimum_hold_time
        }
