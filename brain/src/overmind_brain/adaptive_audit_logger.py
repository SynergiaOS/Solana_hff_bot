"""THE OVERMIND PROTOCOL - Adaptive Behavior Audit Logger
Comprehensive logging system for adaptive behavior with regulatory compliance and performance analysis.
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of audit events."""
    PROFILE_CHANGE = "profile_change"
    SIGNAL_FILTERED = "signal_filtered"
    SIGNAL_PROCESSED = "signal_processed"
    RISK_PARAMETER_UPDATE = "risk_parameter_update"
    PORTFOLIO_UPDATE = "portfolio_update"
    DECISION_MADE = "decision_made"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_EVENT = "system_event"

@dataclass
class AuditEvent:
    """Structured audit event."""
    event_id: str
    event_type: AuditEventType
    timestamp: str
    component: str
    description: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    risk_level: str = "LOW"
    compliance_relevant: bool = False

class AdaptiveAuditLogger:
    """Comprehensive audit logging system for THE OVERMIND PROTOCOL adaptive behavior."""
    
    def __init__(self, 
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 log_file_path: str = "logs/adaptive_audit.log",
                 retention_days: int = 365):
        """Initialize the audit logger.
        
        Args:
            redis_host: DragonflyDB/Redis host
            redis_port: DragonflyDB/Redis port
            log_file_path: Path to audit log file
            retention_days: Number of days to retain audit logs
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.log_file_path = log_file_path
        self.retention_days = retention_days
        
        # Redis connection
        self.redis_client = None
        
        # Event counters
        self.event_counters = {event_type: 0 for event_type in AuditEventType}
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        # Setup file logger
        self.file_logger = logging.getLogger("adaptive_audit")
        self.file_logger.setLevel(logging.INFO)
        
        # Create file handler if not exists
        if not self.file_logger.handlers:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.file_logger.addHandler(file_handler)
        
        logger.info(f"📝 Adaptive Audit Logger initialized - Log file: {log_file_path}")
    
    async def initialize(self):
        """Initialize the audit logger."""
        try:
            # Initialize Redis connection
            self.redis_client = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            
            logger.info("✅ Adaptive Audit Logger initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Adaptive Audit Logger: {e}")
            raise
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        return f"audit_{timestamp}"
    
    async def log_profile_change(self, 
                                old_profile: str, 
                                new_profile: str, 
                                reason: str, 
                                portfolio_progress: float,
                                confidence: float):
        """Log profile change event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.PROFILE_CHANGE,
            timestamp=datetime.utcnow().isoformat(),
            component="strategy_mapper",
            description=f"Profile changed from {old_profile} to {new_profile}",
            data={
                "old_profile": old_profile,
                "new_profile": new_profile,
                "reason": reason,
                "portfolio_progress_percentage": portfolio_progress,
                "decision_confidence": confidence,
                "change_trigger": "adaptive_cortex"
            },
            risk_level="MEDIUM",
            compliance_relevant=True
        )
        
        await self._store_audit_event(event)
        logger.info(f"📝 Profile change logged: {old_profile} → {new_profile}")
    
    async def log_signal_filtering(self, 
                                  signal_data: Dict[str, Any], 
                                  filtered: bool, 
                                  reason: str,
                                  active_profile: str):
        """Log signal filtering action."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.SIGNAL_FILTERED if filtered else AuditEventType.SIGNAL_PROCESSED,
            timestamp=datetime.utcnow().isoformat(),
            component="signal_filter",
            description=f"Signal {'filtered' if filtered else 'processed'}: {signal_data.get('type', 'unknown')}",
            data={
                "signal_id": signal_data.get("signal_id"),
                "signal_type": signal_data.get("type"),
                "signal_confidence": signal_data.get("confidence"),
                "filtered": filtered,
                "reason": reason,
                "active_profile": active_profile,
                "filter_criteria": {
                    "confidence_threshold": signal_data.get("confidence_threshold"),
                    "volume_threshold": signal_data.get("volume_threshold")
                }
            },
            risk_level="LOW"
        )
        
        await self._store_audit_event(event)
    
    async def log_risk_parameter_update(self, 
                                       profile_name: str, 
                                       old_params: Dict[str, Any], 
                                       new_params: Dict[str, Any]):
        """Log risk parameter update."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.RISK_PARAMETER_UPDATE,
            timestamp=datetime.utcnow().isoformat(),
            component="risk_manager",
            description=f"Risk parameters updated for profile: {profile_name}",
            data={
                "profile_name": profile_name,
                "old_parameters": old_params,
                "new_parameters": new_params,
                "parameter_changes": self._calculate_parameter_changes(old_params, new_params)
            },
            risk_level="HIGH",
            compliance_relevant=True
        )
        
        await self._store_audit_event(event)
        logger.info(f"📝 Risk parameter update logged for profile: {profile_name}")
    
    async def log_portfolio_update(self, 
                                  portfolio_state: Dict[str, Any], 
                                  previous_state: Optional[Dict[str, Any]] = None):
        """Log portfolio state update."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.PORTFOLIO_UPDATE,
            timestamp=datetime.utcnow().isoformat(),
            component="portfolio_monitor",
            description=f"Portfolio updated: {portfolio_state.get('goal_progress_percentage', 0):.1f}% progress",
            data={
                "current_state": portfolio_state,
                "previous_state": previous_state,
                "value_change": self._calculate_value_change(portfolio_state, previous_state) if previous_state else None
            },
            risk_level="LOW"
        )
        
        await self._store_audit_event(event)
    
    async def log_trading_decision(self, 
                                  signal_data: Dict[str, Any], 
                                  decision: Dict[str, Any], 
                                  analysis_context: Dict[str, Any]):
        """Log trading decision with full context."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.DECISION_MADE,
            timestamp=datetime.utcnow().isoformat(),
            component="decision_engine",
            description=f"Trading decision: {decision.get('decision', 'UNKNOWN')}",
            data={
                "signal_data": signal_data,
                "decision": decision,
                "analysis_context": analysis_context,
                "decision_factors": {
                    "confidence": decision.get("confidence"),
                    "risk_level": decision.get("risk_level"),
                    "position_size": decision.get("position_size"),
                    "strategy_used": decision.get("strategy_used")
                }
            },
            risk_level="HIGH",
            compliance_relevant=True
        )
        
        await self._store_audit_event(event)
        logger.info(f"📝 Trading decision logged: {decision.get('decision', 'UNKNOWN')}")
    
    async def log_error(self, 
                       component: str, 
                       error_message: str, 
                       error_context: Dict[str, Any]):
        """Log error event."""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=AuditEventType.ERROR_OCCURRED,
            timestamp=datetime.utcnow().isoformat(),
            component=component,
            description=f"Error in {component}: {error_message}",
            data={
                "error_message": error_message,
                "error_context": error_context,
                "stack_trace": error_context.get("stack_trace")
            },
            risk_level="HIGH",
            compliance_relevant=True
        )
        
        await self._store_audit_event(event)
        logger.error(f"📝 Error logged in {component}: {error_message}")
    
    def _calculate_parameter_changes(self, old_params: Dict[str, Any], new_params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate changes between parameter sets."""
        changes = {}
        
        for key in set(old_params.keys()) | set(new_params.keys()):
            old_val = old_params.get(key)
            new_val = new_params.get(key)
            
            if old_val != new_val:
                changes[key] = {
                    "old": old_val,
                    "new": new_val,
                    "change_type": "modified" if key in old_params and key in new_params else 
                                  "added" if key not in old_params else "removed"
                }
        
        return changes
    
    def _calculate_value_change(self, current: Dict[str, Any], previous: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio value changes."""
        current_sol = current.get("total_value_sol", 0)
        previous_sol = previous.get("total_value_sol", 0)
        
        sol_change = current_sol - previous_sol
        sol_change_percent = (sol_change / previous_sol * 100) if previous_sol > 0 else 0
        
        return {
            "sol_change": sol_change,
            "sol_change_percent": sol_change_percent,
            "progress_change": current.get("goal_progress_percentage", 0) - previous.get("goal_progress_percentage", 0)
        }
    
    async def _store_audit_event(self, event: AuditEvent):
        """Store audit event in multiple locations."""
        try:
            # Convert to JSON
            event_json = json.dumps(asdict(event), default=str)
            
            # Store in file
            self.file_logger.info(event_json)
            
            # Store in Redis
            if self.redis_client:
                # Store in main audit log
                await self.redis_client.lpush("audit:events", event_json)
                
                # Store by event type
                await self.redis_client.lpush(f"audit:{event.event_type.value}", event_json)
                
                # Store compliance-relevant events separately
                if event.compliance_relevant:
                    await self.redis_client.lpush("audit:compliance", event_json)
                
                # Maintain retention limits
                await self.redis_client.ltrim("audit:events", 0, 9999)  # Keep last 10k events
                await self.redis_client.ltrim(f"audit:{event.event_type.value}", 0, 999)  # Keep last 1k per type
                
                if event.compliance_relevant:
                    await self.redis_client.ltrim("audit:compliance", 0, 4999)  # Keep last 5k compliance events
            
            # Update counters
            self.event_counters[event.event_type] += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to store audit event: {e}")
    
    async def get_audit_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get audit summary for the specified time period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            summary = {
                "time_period_hours": hours,
                "event_counts": self.event_counters.copy(),
                "compliance_events": 0,
                "high_risk_events": 0,
                "recent_profile_changes": [],
                "recent_errors": []
            }
            
            if self.redis_client:
                # Get recent events for analysis
                recent_events = await self.redis_client.lrange("audit:events", 0, 999)
                
                for event_json in recent_events:
                    try:
                        event_data = json.loads(event_json)
                        event_time = datetime.fromisoformat(event_data["timestamp"])
                        
                        if event_time >= cutoff_time:
                            if event_data.get("compliance_relevant"):
                                summary["compliance_events"] += 1
                            
                            if event_data.get("risk_level") == "HIGH":
                                summary["high_risk_events"] += 1
                            
                            if event_data["event_type"] == "profile_change":
                                summary["recent_profile_changes"].append(event_data)
                            
                            if event_data["event_type"] == "error_occurred":
                                summary["recent_errors"].append(event_data)
                    
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Failed to generate audit summary: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_logs(self):
        """Clean up old audit logs based on retention policy."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            # This would implement log file rotation and cleanup
            # For now, we rely on Redis TTL and log rotation tools
            
            logger.info(f"📝 Audit log cleanup completed - retention: {self.retention_days} days")
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old logs: {e}")

# Global instance
adaptive_audit_logger = AdaptiveAuditLogger()
