#!/usr/bin/env python3
"""
VectorMemory Alerts System for THE OVERMIND PROTOCOL
Monitoring and alerting for vector memory operations
"""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    component: str
    metrics: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class VectorMemoryAlertsManager:
    """Alerts manager for VectorMemory monitoring"""
    
    def __init__(self, vector_memory=None):
        self.vector_memory = vector_memory
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable] = []
        self.thresholds = {
            "query_time_warning": 1.0,  # seconds
            "query_time_critical": 5.0,  # seconds
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.20,  # 20%
            "memory_usage_warning": 0.80,  # 80%
            "memory_usage_critical": 0.95,  # 95%
            "query_rate_drop_warning": 0.50,  # 50% drop
            "query_rate_drop_critical": 0.80,  # 80% drop
        }
        self.baseline_metrics = {}
        self.monitoring_active = False
        
        logger.info("VectorMemory Alerts Manager initialized")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add alert handler function"""
        self.alert_handlers.append(handler)
        logger.info(f"Added alert handler: {handler.__name__}")
    
    def create_alert(self, severity: AlertSeverity, title: str, message: str, 
                    component: str = "vector_memory", metrics: Dict[str, Any] = None) -> Alert:
        """Create new alert"""
        alert = Alert(
            id=f"alert_{int(time.time())}_{len(self.alerts)}",
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            component=component,
            metrics=metrics or {}
        )
        
        self.alerts.append(alert)
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler {handler.__name__}: {e}")
        
        logger.warning(f"Alert created: [{severity.value.upper()}] {title}")
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert by ID"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert_id}")
                return True
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active (unresolved) alerts"""
        active = [alert for alert in self.alerts if not alert.resolved]
        if severity:
            active = [alert for alert in active if alert.severity == severity]
        return active
    
    def check_query_performance(self, metrics: Dict[str, Any]):
        """Check query performance metrics for alerts"""
        if not metrics:
            return
        
        avg_query_time = metrics.get('avg_query_time', 0)
        
        # Check query time thresholds
        if avg_query_time > self.thresholds['query_time_critical']:
            self.create_alert(
                AlertSeverity.CRITICAL,
                "Critical Query Performance",
                f"Average query time is {avg_query_time:.3f}s (threshold: {self.thresholds['query_time_critical']}s)",
                metrics={"avg_query_time": avg_query_time}
            )
        elif avg_query_time > self.thresholds['query_time_warning']:
            self.create_alert(
                AlertSeverity.WARNING,
                "Slow Query Performance",
                f"Average query time is {avg_query_time:.3f}s (threshold: {self.thresholds['query_time_warning']}s)",
                metrics={"avg_query_time": avg_query_time}
            )
    
    def check_error_rates(self, metrics: Dict[str, Any]):
        """Check error rates for alerts"""
        queries_total = metrics.get('queries_total', 0)
        queries_failed = metrics.get('queries_failed', 0)
        
        if queries_total > 0:
            error_rate = queries_failed / queries_total
            
            if error_rate > self.thresholds['error_rate_critical']:
                self.create_alert(
                    AlertSeverity.CRITICAL,
                    "High Error Rate",
                    f"Query error rate is {error_rate:.2%} (threshold: {self.thresholds['error_rate_critical']:.2%})",
                    metrics={"error_rate": error_rate, "queries_failed": queries_failed, "queries_total": queries_total}
                )
            elif error_rate > self.thresholds['error_rate_warning']:
                self.create_alert(
                    AlertSeverity.WARNING,
                    "Elevated Error Rate",
                    f"Query error rate is {error_rate:.2%} (threshold: {self.thresholds['error_rate_warning']:.2%})",
                    metrics={"error_rate": error_rate, "queries_failed": queries_failed, "queries_total": queries_total}
                )
    
    def check_memory_health(self, metrics: Dict[str, Any]):
        """Check memory system health"""
        status = metrics.get('status', 'unknown')
        
        if status == 'error':
            error_msg = metrics.get('error', 'Unknown error')
            self.create_alert(
                AlertSeverity.CRITICAL,
                "VectorMemory System Error",
                f"VectorMemory system error: {error_msg}",
                metrics=metrics
            )
        elif status != 'operational':
            self.create_alert(
                AlertSeverity.WARNING,
                "VectorMemory Status Warning",
                f"VectorMemory status is '{status}' (expected: operational)",
                metrics=metrics
            )
    
    def check_query_rate_changes(self, current_metrics: Dict[str, Any]):
        """Check for significant changes in query rates"""
        if not self.baseline_metrics:
            self.baseline_metrics = current_metrics.copy()
            return
        
        current_rate = current_metrics.get('queries_total', 0)
        baseline_rate = self.baseline_metrics.get('queries_total', 0)
        
        if baseline_rate > 0:
            rate_change = (current_rate - baseline_rate) / baseline_rate
            
            if rate_change < -self.thresholds['query_rate_drop_critical']:
                self.create_alert(
                    AlertSeverity.CRITICAL,
                    "Critical Query Rate Drop",
                    f"Query rate dropped by {abs(rate_change):.2%} (threshold: {self.thresholds['query_rate_drop_critical']:.2%})",
                    metrics={"rate_change": rate_change, "current_rate": current_rate, "baseline_rate": baseline_rate}
                )
            elif rate_change < -self.thresholds['query_rate_drop_warning']:
                self.create_alert(
                    AlertSeverity.WARNING,
                    "Query Rate Drop",
                    f"Query rate dropped by {abs(rate_change):.2%} (threshold: {self.thresholds['query_rate_drop_warning']:.2%})",
                    metrics={"rate_change": rate_change, "current_rate": current_rate, "baseline_rate": baseline_rate}
                )
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        if not self.vector_memory:
            return {"status": "error", "message": "No VectorMemory instance configured"}
        
        try:
            # Get current metrics
            metrics = self.vector_memory.get_metrics()
            
            # Run all checks
            self.check_query_performance(metrics)
            self.check_error_rates(metrics)
            self.check_memory_health(metrics)
            self.check_query_rate_changes(metrics)
            
            # Update baseline
            self.baseline_metrics = metrics.copy()
            
            # Get active alerts summary
            active_alerts = self.get_active_alerts()
            critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
            warning_alerts = [a for a in active_alerts if a.severity == AlertSeverity.WARNING]
            
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "status": "critical" if critical_alerts else ("warning" if warning_alerts else "healthy"),
                "metrics": metrics,
                "alerts": {
                    "total_active": len(active_alerts),
                    "critical": len(critical_alerts),
                    "warnings": len(warning_alerts)
                }
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.create_alert(
                AlertSeverity.CRITICAL,
                "Health Check Failed",
                f"Unable to perform health check: {str(e)}",
                metrics={"error": str(e)}
            )
            return {"status": "error", "message": str(e)}
    
    async def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring"""
        self.monitoring_active = True
        logger.info(f"Starting VectorMemory monitoring (interval: {interval}s)")
        
        while self.monitoring_active:
            try:
                health_status = self.run_health_check()
                logger.debug(f"Health check completed: {health_status['status']}")
                
                # Auto-resolve old alerts if system is healthy
                if health_status['status'] == 'healthy':
                    self._auto_resolve_old_alerts()
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
            
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        logger.info("VectorMemory monitoring stopped")
    
    def _auto_resolve_old_alerts(self, max_age_hours: int = 24):
        """Auto-resolve old alerts if system is healthy"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for alert in self.alerts:
            if not alert.resolved and alert.timestamp < cutoff_time:
                if alert.severity in [AlertSeverity.WARNING, AlertSeverity.INFO]:
                    self.resolve_alert(alert.id)
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts"""
        total_alerts = len(self.alerts)
        active_alerts = len(self.get_active_alerts())
        
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([
                a for a in self.alerts if a.severity == severity
            ])
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": total_alerts - active_alerts,
            "severity_breakdown": severity_counts,
            "latest_alert": self.alerts[-1].timestamp.isoformat() if self.alerts else None
        }


# Default alert handlers
def console_alert_handler(alert: Alert):
    """Simple console alert handler"""
    timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {alert.severity.value.upper()}: {alert.title}")
    print(f"  {alert.message}")
    if alert.metrics:
        print(f"  Metrics: {alert.metrics}")


def log_alert_handler(alert: Alert):
    """Log-based alert handler"""
    if alert.severity == AlertSeverity.CRITICAL:
        logger.critical(f"{alert.title}: {alert.message}")
    elif alert.severity == AlertSeverity.ERROR:
        logger.error(f"{alert.title}: {alert.message}")
    elif alert.severity == AlertSeverity.WARNING:
        logger.warning(f"{alert.title}: {alert.message}")
    else:
        logger.info(f"{alert.title}: {alert.message}")


# Example usage
if __name__ == "__main__":
    # Create alerts manager
    alerts_manager = VectorMemoryAlertsManager()
    
    # Add handlers
    alerts_manager.add_alert_handler(console_alert_handler)
    alerts_manager.add_alert_handler(log_alert_handler)
    
    # Example alert
    alerts_manager.create_alert(
        AlertSeverity.WARNING,
        "Test Alert",
        "This is a test alert for demonstration",
        metrics={"test_metric": 42}
    )
    
    # Get summary
    summary = alerts_manager.get_alert_summary()
    print(f"Alert Summary: {summary}")
