#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Advanced Alert System
Critical notifications and monitoring
"""

import asyncio
import json
import time
import redis
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

@dataclass
class Alert:
    level: AlertLevel
    title: str
    message: str
    timestamp: float
    component: str
    data: Dict
    acknowledged: bool = False

class AlertSystem:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Alert configuration
        self.config = {
            'max_daily_loss_threshold': 0.10,      # 10% daily loss
            'high_drawdown_threshold': 0.08,       # 8% drawdown warning
            'emergency_drawdown_threshold': 0.15,  # 15% emergency
            'low_win_rate_threshold': 0.30,        # 30% win rate warning
            'system_offline_threshold': 300,       # 5 minutes offline
            'high_latency_threshold': 1000,        # 1 second latency
            'position_size_warning': 0.20,         # 20% of portfolio
            'consecutive_losses_threshold': 5,      # 5 consecutive losses
        }
        
        self.active_alerts = {}
        self.alert_history = []
        
    async def check_portfolio_alerts(self):
        """Check for portfolio-related alerts"""
        try:
            # Get latest portfolio metrics
            position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
            if not position_updates:
                return
            
            latest_update = json.loads(position_updates[0])
            portfolio_metrics = latest_update.get('portfolio_metrics', {})
            
            # Check daily loss
            daily_pnl_pct = portfolio_metrics.get('daily_pnl_percentage', 0)
            if daily_pnl_pct < -self.config['max_daily_loss_threshold']:
                await self.create_alert(
                    AlertLevel.CRITICAL,
                    "High Daily Loss",
                    f"Daily loss of {abs(daily_pnl_pct):.2%} exceeds threshold",
                    "portfolio",
                    {'daily_pnl_pct': daily_pnl_pct}
                )
            
            # Check drawdown
            total_return = portfolio_metrics.get('portfolio_return_pct', 0)
            if total_return < -self.config['emergency_drawdown_threshold']:
                await self.create_alert(
                    AlertLevel.EMERGENCY,
                    "Emergency Drawdown",
                    f"Portfolio drawdown of {abs(total_return):.2%} requires immediate attention",
                    "portfolio",
                    {'drawdown': total_return}
                )
            elif total_return < -self.config['high_drawdown_threshold']:
                await self.create_alert(
                    AlertLevel.WARNING,
                    "High Drawdown",
                    f"Portfolio drawdown of {abs(total_return):.2%} approaching danger zone",
                    "portfolio",
                    {'drawdown': total_return}
                )
            
            # Check position sizes
            positions = latest_update.get('positions', {})
            total_value = portfolio_metrics.get('total_portfolio_value', 1)
            
            for symbol, position in positions.items():
                position_value = position.get('quantity', 0) * position.get('current_price', 0)
                position_pct = position_value / total_value if total_value > 0 else 0
                
                if position_pct > self.config['position_size_warning']:
                    await self.create_alert(
                        AlertLevel.WARNING,
                        "Large Position Size",
                        f"{symbol} position ({position_pct:.2%}) exceeds recommended size",
                        "risk_management",
                        {'symbol': symbol, 'position_pct': position_pct}
                    )
            
        except Exception as e:
            logger.error(f"❌ Error checking portfolio alerts: {e}")
    
    async def check_system_alerts(self):
        """Check for system-related alerts"""
        try:
            # Check system components
            components = {
                'rust_executor': 'overmind:execution_results',
                'post_trade_intelligence': 'overmind:post_trade_intelligence',
                'add_to_winner': 'overmind:scaling_events',
                'drawdown_guard': 'overmind:drawdown_metrics'
            }
            
            current_time = time.time()
            
            for component, redis_key in components.items():
                # Check last activity
                last_activity = self.redis_client.lrange(redis_key, 0, 0)
                
                if last_activity:
                    last_data = json.loads(last_activity[0])
                    last_timestamp = last_data.get('timestamp', 0)
                    time_since_activity = current_time - last_timestamp
                    
                    if time_since_activity > self.config['system_offline_threshold']:
                        await self.create_alert(
                            AlertLevel.CRITICAL,
                            "System Component Offline",
                            f"{component} has been inactive for {time_since_activity/60:.1f} minutes",
                            "system",
                            {'component': component, 'offline_duration': time_since_activity}
                        )
                else:
                    await self.create_alert(
                        AlertLevel.WARNING,
                        "No Activity Detected",
                        f"No activity detected for {component}",
                        "system",
                        {'component': component}
                    )
            
            # Check emergency stop status
            emergency_stop = self.redis_client.get('overmind:emergency_stop')
            if emergency_stop == 'true':
                await self.create_alert(
                    AlertLevel.EMERGENCY,
                    "Emergency Stop Active",
                    "System is in emergency stop mode - all trading halted",
                    "system",
                    {'emergency_stop': True}
                )
            
        except Exception as e:
            logger.error(f"❌ Error checking system alerts: {e}")
    
    async def check_performance_alerts(self):
        """Check for performance-related alerts"""
        try:
            # Get recent execution results
            results = self.redis_client.lrange('overmind:execution_results', 0, 9)
            
            if len(results) >= 5:
                # Check consecutive losses
                recent_pnls = []
                for result_str in results[:5]:
                    result = json.loads(result_str)
                    pnl = result.get('estimated_profit', 0)
                    recent_pnls.append(pnl)
                
                consecutive_losses = 0
                for pnl in recent_pnls:
                    if pnl < 0:
                        consecutive_losses += 1
                    else:
                        break
                
                if consecutive_losses >= self.config['consecutive_losses_threshold']:
                    await self.create_alert(
                        AlertLevel.WARNING,
                        "Consecutive Losses",
                        f"{consecutive_losses} consecutive losing trades detected",
                        "performance",
                        {'consecutive_losses': consecutive_losses}
                    )
            
            # Check win rate from analytics
            analytics_results = self.redis_client.lrange('overmind:analytics_results', 0, 0)
            if analytics_results:
                analytics = json.loads(analytics_results[0])
                performance = analytics.get('performance_metrics', {})
                win_rate = performance.get('win_rate', 0)
                
                if win_rate < self.config['low_win_rate_threshold']:
                    await self.create_alert(
                        AlertLevel.WARNING,
                        "Low Win Rate",
                        f"Win rate of {win_rate:.2%} below acceptable threshold",
                        "performance",
                        {'win_rate': win_rate}
                    )
            
        except Exception as e:
            logger.error(f"❌ Error checking performance alerts: {e}")
    
    async def create_alert(self, level: AlertLevel, title: str, message: str, component: str, data: Dict):
        """Create and store a new alert"""
        try:
            alert_id = f"{component}_{title.replace(' ', '_').lower()}_{int(time.time())}"
            
            # Check if similar alert already exists (avoid spam)
            similar_alert_key = f"{component}_{title.replace(' ', '_').lower()}"
            if similar_alert_key in self.active_alerts:
                last_alert_time = self.active_alerts[similar_alert_key]
                if time.time() - last_alert_time < 300:  # 5 minutes cooldown
                    return
            
            alert = Alert(
                level=level,
                title=title,
                message=message,
                timestamp=time.time(),
                component=component,
                data=data
            )
            
            # Store alert
            alert_data = {
                'id': alert_id,
                'level': level.value,
                'title': title,
                'message': message,
                'timestamp': alert.timestamp,
                'component': component,
                'data': data,
                'acknowledged': False
            }
            
            self.redis_client.lpush('overmind:alerts', json.dumps(alert_data))
            self.redis_client.ltrim('overmind:alerts', 0, 999)  # Keep last 1000 alerts
            
            # Track active alerts
            self.active_alerts[similar_alert_key] = time.time()
            
            # Log alert
            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.CRITICAL: "🚨",
                AlertLevel.EMERGENCY: "🆘"
            }
            
            emoji = level_emoji.get(level, "📢")
            logger.warning(f"{emoji} ALERT [{level.value}] {title}: {message}")
            
            # Send to notification channels if critical/emergency
            if level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                await self.send_critical_notification(alert_data)
            
        except Exception as e:
            logger.error(f"❌ Error creating alert: {e}")
    
    async def send_critical_notification(self, alert_data: Dict):
        """Send critical notifications"""
        try:
            # Store in high-priority queue
            self.redis_client.lpush('overmind:critical_alerts', json.dumps(alert_data))
            
            # Could integrate with external notification services here
            # (Discord, Telegram, Email, SMS, etc.)
            
            logger.critical(f"🆘 CRITICAL NOTIFICATION: {alert_data['title']}")
            
        except Exception as e:
            logger.error(f"❌ Error sending critical notification: {e}")
    
    async def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        try:
            alerts = self.redis_client.lrange('overmind:alerts', 0, -1)
            
            for i, alert_str in enumerate(alerts):
                alert_data = json.loads(alert_str)
                if alert_data.get('id') == alert_id:
                    alert_data['acknowledged'] = True
                    alert_data['acknowledged_at'] = time.time()
                    
                    # Update in Redis
                    self.redis_client.lset('overmind:alerts', i, json.dumps(alert_data))
                    logger.info(f"✅ Alert acknowledged: {alert_id}")
                    break
            
        except Exception as e:
            logger.error(f"❌ Error acknowledging alert: {e}")
    
    async def get_active_alerts(self) -> List[Dict]:
        """Get all active (unacknowledged) alerts"""
        try:
            alerts = self.redis_client.lrange('overmind:alerts', 0, 49)  # Last 50 alerts
            active_alerts = []
            
            for alert_str in alerts:
                alert_data = json.loads(alert_str)
                if not alert_data.get('acknowledged', False):
                    active_alerts.append(alert_data)
            
            return sorted(active_alerts, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Error getting active alerts: {e}")
            return []
    
    async def cleanup_old_alerts(self):
        """Clean up old alerts and reset cooldowns"""
        try:
            current_time = time.time()
            
            # Clean up active alerts cooldowns (older than 1 hour)
            expired_keys = [
                key for key, timestamp in self.active_alerts.items()
                if current_time - timestamp > 3600
            ]
            
            for key in expired_keys:
                del self.active_alerts[key]
            
            logger.info(f"🧹 Cleaned up {len(expired_keys)} expired alert cooldowns")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up alerts: {e}")
    
    async def run_alert_monitoring(self):
        """Main alert monitoring loop"""
        logger.info("🚨 Starting Alert System")
        
        while True:
            try:
                # Check all alert categories
                await self.check_portfolio_alerts()
                await self.check_system_alerts()
                await self.check_performance_alerts()
                
                # Cleanup old alerts every hour
                if int(time.time()) % 3600 < 60:  # Once per hour
                    await self.cleanup_old_alerts()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Error in alert monitoring: {e}")
                await asyncio.sleep(60)

async def main():
    alert_system = AlertSystem()
    await alert_system.run_alert_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
