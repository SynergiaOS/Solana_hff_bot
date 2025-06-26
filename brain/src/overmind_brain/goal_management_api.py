"""THE OVERMIND PROTOCOL - Goal Management API
FastAPI endpoints for dynamic goal management and control.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from .goal_manager import dynamic_goal_manager, GoalType, TradingGoal, GoalChangeEvent
from .adaptive_audit_logger import adaptive_audit_logger

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class SetGoalRequest(BaseModel):
    """Request model for setting a new goal."""
    goal_type: str = Field(..., description="Type of goal: REACH_BALANCE, CAPITAL_PRESERVATION, MAXIMIZE_PROFIT")
    target_sol: float = Field(..., gt=0, le=1000, description="Target SOL amount (0.1-1000)")
    target_usd: Optional[float] = Field(None, gt=0, description="Optional target USD amount")
    reason: str = Field("API goal update", description="Reason for goal change")
    changed_by: str = Field("api_user", description="Who is making the change")
    
    @validator('goal_type')
    def validate_goal_type(cls, v):
        try:
            GoalType(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid goal_type. Must be one of: {[gt.value for gt in GoalType]}")

class GoalResponse(BaseModel):
    """Response model for goal information."""
    goal_type: str
    target_sol: float
    target_usd: Optional[float]
    is_active: bool
    created_at: str
    modified_at: str
    modified_by: str
    description: str

class GoalChangeEventResponse(BaseModel):
    """Response model for goal change events."""
    event_id: str
    old_goal: Optional[GoalResponse]
    new_goal: GoalResponse
    change_reason: str
    changed_by: str
    timestamp: str
    impact_assessment: Dict[str, Any]

class GoalStatusResponse(BaseModel):
    """Response model for goal status."""
    current_goal: Optional[GoalResponse]
    goal_manager_status: Dict[str, Any]
    last_goal_check: Optional[str]
    goal_change_listeners: int

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class GoalManagementAPI:
    """Goal Management API endpoints."""
    
    def __init__(self):
        """Initialize the Goal Management API."""
        self.app = FastAPI(
            title="THE OVERMIND PROTOCOL - Goal Management API",
            description="Dynamic goal management and control endpoints",
            version="1.0.0"
        )
        self._setup_routes()
        logger.info("🚀 Goal Management API initialized")
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.post("/api/v1/control/set-goal", response_model=APIResponse)
        async def set_goal(request: SetGoalRequest):
            """Set a new trading goal.
            
            This endpoint allows real-time modification of trading goals without
            restarting the AI Brain or interrupting trading operations.
            """
            try:
                logger.info(f"🎯 API: Setting new goal - {request.goal_type}: {request.target_sol} SOL")
                
                # Validate and convert goal type
                goal_type = GoalType(request.goal_type)
                
                # Set the goal
                success = await dynamic_goal_manager.set_goal(
                    goal_type=goal_type,
                    target_sol=request.target_sol,
                    target_usd=request.target_usd,
                    changed_by=request.changed_by,
                    change_reason=request.reason
                )
                
                if success:
                    # Get the updated goal
                    current_goal = await dynamic_goal_manager.get_current_goal()
                    
                    # Log to adaptive audit logger
                    await adaptive_audit_logger.log_event(
                        event_type="GOAL_CHANGE_API",
                        event_data={
                            "goal_type": request.goal_type,
                            "target_sol": request.target_sol,
                            "target_usd": request.target_usd,
                            "changed_by": request.changed_by,
                            "reason": request.reason,
                            "api_endpoint": "/api/v1/control/set-goal"
                        },
                        risk_level="medium",
                        confidence=1.0
                    )
                    
                    return APIResponse(
                        success=True,
                        message=f"Goal successfully updated to {request.goal_type}: {request.target_sol} SOL",
                        data={
                            "goal": GoalResponse(
                                goal_type=current_goal.goal_type.value,
                                target_sol=current_goal.target_sol,
                                target_usd=current_goal.target_usd,
                                is_active=current_goal.is_active,
                                created_at=current_goal.created_at,
                                modified_at=current_goal.modified_at,
                                modified_by=current_goal.modified_by,
                                description=current_goal.description
                            ).dict()
                        }
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to set goal - validation failed"
                    )
                    
            except ValueError as e:
                logger.error(f"❌ API: Goal validation error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid goal parameters: {e}"
                )
            except Exception as e:
                logger.error(f"❌ API: Failed to set goal: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal server error: {e}"
                )
        
        @self.app.get("/api/v1/control/current-goal", response_model=APIResponse)
        async def get_current_goal():
            """Get the current active trading goal and status."""
            try:
                logger.debug("📊 API: Getting current goal status")
                
                # Get current goal
                current_goal = await dynamic_goal_manager.get_current_goal()
                
                # Get goal manager status
                goal_status = await dynamic_goal_manager.get_status()
                
                goal_data = None
                if current_goal:
                    goal_data = GoalResponse(
                        goal_type=current_goal.goal_type.value,
                        target_sol=current_goal.target_sol,
                        target_usd=current_goal.target_usd,
                        is_active=current_goal.is_active,
                        created_at=current_goal.created_at,
                        modified_at=current_goal.modified_at,
                        modified_by=current_goal.modified_by,
                        description=current_goal.description
                    ).dict()
                
                return APIResponse(
                    success=True,
                    message="Current goal retrieved successfully",
                    data={
                        "current_goal": goal_data,
                        "goal_manager_status": goal_status,
                        "available_goal_types": [gt.value for gt in GoalType]
                    }
                )
                
            except Exception as e:
                logger.error(f"❌ API: Failed to get current goal: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve current goal: {e}"
                )
        
        @self.app.get("/api/v1/control/goal-history", response_model=APIResponse)
        async def get_goal_history(limit: int = 10):
            """Get goal change history for audit trail."""
            try:
                logger.debug(f"📜 API: Getting goal history (limit: {limit})")
                
                # Validate limit
                if limit < 1 or limit > 100:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Limit must be between 1 and 100"
                    )
                
                # Get goal history
                history = await dynamic_goal_manager.get_goal_history(limit=limit)
                
                # Convert to response format
                history_data = []
                for event in history:
                    old_goal_data = None
                    if event.old_goal:
                        old_goal_data = GoalResponse(
                            goal_type=event.old_goal.goal_type.value,
                            target_sol=event.old_goal.target_sol,
                            target_usd=event.old_goal.target_usd,
                            is_active=event.old_goal.is_active,
                            created_at=event.old_goal.created_at,
                            modified_at=event.old_goal.modified_at,
                            modified_by=event.old_goal.modified_by,
                            description=event.old_goal.description
                        ).dict()
                    
                    new_goal_data = GoalResponse(
                        goal_type=event.new_goal.goal_type.value,
                        target_sol=event.new_goal.target_sol,
                        target_usd=event.new_goal.target_usd,
                        is_active=event.new_goal.is_active,
                        created_at=event.new_goal.created_at,
                        modified_at=event.new_goal.modified_at,
                        modified_by=event.new_goal.modified_by,
                        description=event.new_goal.description
                    ).dict()
                    
                    history_data.append({
                        "event_id": event.event_id,
                        "old_goal": old_goal_data,
                        "new_goal": new_goal_data,
                        "change_reason": event.change_reason,
                        "changed_by": event.changed_by,
                        "timestamp": event.timestamp,
                        "impact_assessment": event.impact_assessment
                    })
                
                return APIResponse(
                    success=True,
                    message=f"Goal history retrieved successfully ({len(history_data)} entries)",
                    data={
                        "history": history_data,
                        "total_entries": len(history_data),
                        "limit": limit
                    }
                )
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ API: Failed to get goal history: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve goal history: {e}"
                )
        
        @self.app.get("/api/v1/control/health", response_model=APIResponse)
        async def health_check():
            """Health check endpoint for goal management system."""
            try:
                # Check goal manager status
                goal_status = await dynamic_goal_manager.get_status()
                
                # Check if we can get current goal
                current_goal = await dynamic_goal_manager.get_current_goal()
                
                health_data = {
                    "goal_manager_operational": goal_status.get("redis_connected", False),
                    "current_goal_available": current_goal is not None,
                    "goal_manager_status": goal_status,
                    "api_version": "1.0.0",
                    "endpoints_available": [
                        "/api/v1/control/set-goal",
                        "/api/v1/control/current-goal", 
                        "/api/v1/control/goal-history",
                        "/api/v1/control/health"
                    ]
                }
                
                return APIResponse(
                    success=True,
                    message="Goal Management API is healthy",
                    data=health_data
                )
                
            except Exception as e:
                logger.error(f"❌ API: Health check failed: {e}")
                return APIResponse(
                    success=False,
                    message="Goal Management API health check failed",
                    error=str(e)
                )

# Global API instance
goal_management_api = GoalManagementAPI()
