#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Real-time Regime Monitor
Continuous monitoring of market regimes with change alerts
"""

import asyncio
import json
import redis
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from market_regime_detector import create_market_regime_detector, MarketRegime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('RegimeMonitor')

class RegimeMonitor:
    """
    Real-time Market Regime Monitor
    
    Continuously monitors market conditions and detects regime changes
    Sends alerts when significant regime shifts occur
    """
    
    def __init__(self, monitoring_interval: int = 60):
        """Initialize Regime Monitor"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.regime_detector = create_market_regime_detector()
        
        # Monitoring configuration
        self.monitoring_interval = monitoring_interval  # seconds
        self.symbols_to_monitor = ['SOL', 'BTC', 'ETH']  # Can be expanded
        
        # Regime change detection
        self.previous_regimes = {}
        self.regime_change_threshold = 0.3  # Minimum confidence change to trigger alert
        
        # Alert configuration
        self.alert_cooldown = 300  # 5 minutes between similar alerts
        self.last_alerts = {}
        
        # Statistics
        self.monitoring_stats = {
            'total_checks': 0,
            'regime_changes_detected': 0,
            'alerts_sent': 0,
            'start_time': time.time()
        }
        
        # Running flag
        self.running = False
        
        logger.info("📊 Real-time Regime Monitor initialized")
        logger.info(f"⏰ Monitoring interval: {monitoring_interval} seconds")
        logger.info(f"🎯 Symbols: {', '.join(self.symbols_to_monitor)}")
    
    async def start_monitoring(self):
        """Start continuous regime monitoring"""
        logger.info("🎯 Starting Real-time Regime Monitoring...")
        self.running = True
        
        while self.running:
            try:
                # Monitor all symbols
                for symbol in self.symbols_to_monitor:
                    await self.monitor_symbol_regime(symbol)
                
                # Update monitoring stats
                self.monitoring_stats['total_checks'] += 1
                
                # Send periodic status update
                if self.monitoring_stats['total_checks'] % 10 == 0:
                    await self.send_status_update()
                
                # Wait before next check
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(30)  # Shorter wait on error
    
    async def monitor_symbol_regime(self, symbol: str):
        """Monitor regime for a specific symbol"""
        try:
            logger.info(f"🔍 Monitoring regime for {symbol}...")
            
            # Detect current regime
            current_analysis = await self.regime_detector.detect_current_regime(symbol)
            
            # Check for regime change
            regime_changed = await self.check_regime_change(symbol, current_analysis)
            
            if regime_changed:
                await self.handle_regime_change(symbol, current_analysis)
            
            # Store current regime for next comparison
            self.previous_regimes[symbol] = {
                'regime': current_analysis.regime,
                'confidence': current_analysis.confidence,
                'timestamp': current_analysis.timestamp
            }
            
            logger.info(f"✅ {symbol} regime monitoring complete: {current_analysis.regime.value}")
            
        except Exception as e:
            logger.error(f"❌ Error monitoring {symbol}: {e}")
    
    async def check_regime_change(self, symbol: str, current_analysis) -> bool:
        """Check if regime has changed significantly"""
        try:
            previous = self.previous_regimes.get(symbol)
            
            if not previous:
                # First time monitoring this symbol
                return True
            
            # Check for regime type change
            regime_changed = previous['regime'] != current_analysis.regime
            
            # Check for significant confidence change
            confidence_change = abs(previous['confidence'] - current_analysis.confidence)
            significant_confidence_change = confidence_change > self.regime_change_threshold
            
            # Consider it a change if regime changed OR confidence changed significantly
            return regime_changed or significant_confidence_change
            
        except Exception as e:
            logger.error(f"❌ Error checking regime change: {e}")
            return False
    
    async def handle_regime_change(self, symbol: str, current_analysis):
        """Handle detected regime change"""
        try:
            previous = self.previous_regimes.get(symbol, {})
            previous_regime = previous.get('regime', 'unknown')
            
            logger.info(f"🚨 REGIME CHANGE DETECTED for {symbol}!")
            logger.info(f"   Previous: {previous_regime}")
            logger.info(f"   Current: {current_analysis.regime.value}")
            logger.info(f"   Confidence: {current_analysis.confidence:.2f}")
            
            # Update stats
            self.monitoring_stats['regime_changes_detected'] += 1
            
            # Send regime change alert
            await self.send_regime_change_alert(symbol, previous_regime, current_analysis)
            
            # Notify Capital Allocator of regime change
            await self.notify_capital_allocator(symbol, current_analysis)
            
        except Exception as e:
            logger.error(f"❌ Error handling regime change: {e}")
    
    async def send_regime_change_alert(self, symbol: str, previous_regime: str, current_analysis):
        """Send regime change alert"""
        try:
            # Check alert cooldown
            alert_key = f"{symbol}_{current_analysis.regime.value}"
            last_alert_time = self.last_alerts.get(alert_key, 0)
            
            if time.time() - last_alert_time < self.alert_cooldown:
                logger.info(f"⏰ Alert cooldown active for {alert_key}")
                return
            
            # Create alert
            alert = {
                "type": "regime_change",
                "symbol": symbol,
                "previous_regime": previous_regime,
                "current_regime": current_analysis.regime.value,
                "confidence": current_analysis.confidence,
                "allocation_multiplier": current_analysis.allocation_multiplier,
                "risk_level": current_analysis.risk_level,
                "reasoning": current_analysis.reasoning,
                "timestamp": time.time(),
                "priority": self.get_alert_priority(current_analysis.regime)
            }
            
            # Send to alerts queue
            self.redis_client.lpush("overmind:alerts", json.dumps(alert))
            
            # Update alert tracking
            self.last_alerts[alert_key] = time.time()
            self.monitoring_stats['alerts_sent'] += 1
            
            logger.info(f"🚨 Regime change alert sent: {symbol} → {current_analysis.regime.value}")
            
        except Exception as e:
            logger.error(f"❌ Error sending alert: {e}")
    
    async def notify_capital_allocator(self, symbol: str, current_analysis):
        """Notify Capital Allocator of regime change"""
        try:
            # Send regime update notification
            notification = {
                "type": "regime_update",
                "symbol": symbol,
                "regime": current_analysis.regime.value,
                "allocation_multiplier": current_analysis.allocation_multiplier,
                "confidence": current_analysis.confidence,
                "timestamp": time.time()
            }
            
            # Send to capital allocator notifications
            self.redis_client.lpush("overmind:regime_updates", json.dumps(notification))
            
            logger.info(f"📊 Capital Allocator notified of regime change: {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Error notifying Capital Allocator: {e}")
    
    def get_alert_priority(self, regime: MarketRegime) -> str:
        """Determine alert priority based on regime"""
        high_priority_regimes = [MarketRegime.CRASH, MarketRegime.BEAR_STRONG, MarketRegime.HIGH_VOLATILITY]
        medium_priority_regimes = [MarketRegime.BULL_STRONG, MarketRegime.BEAR_WEAK]
        
        if regime in high_priority_regimes:
            return "HIGH"
        elif regime in medium_priority_regimes:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def send_status_update(self):
        """Send periodic status update"""
        try:
            uptime = time.time() - self.monitoring_stats['start_time']
            
            status = {
                "type": "regime_monitor_status",
                "uptime_seconds": uptime,
                "total_checks": self.monitoring_stats['total_checks'],
                "regime_changes_detected": self.monitoring_stats['regime_changes_detected'],
                "alerts_sent": self.monitoring_stats['alerts_sent'],
                "symbols_monitored": len(self.symbols_to_monitor),
                "current_regimes": {
                    symbol: data.get('regime', 'unknown').value if hasattr(data.get('regime', 'unknown'), 'value') else str(data.get('regime', 'unknown'))
                    for symbol, data in self.previous_regimes.items()
                },
                "timestamp": time.time()
            }
            
            # Send status update
            self.redis_client.setex("overmind:regime_monitor_status", 300, json.dumps(status))
            
            logger.info(f"📊 Status update: {self.monitoring_stats['total_checks']} checks, "
                       f"{self.monitoring_stats['regime_changes_detected']} changes, "
                       f"{self.monitoring_stats['alerts_sent']} alerts")
            
        except Exception as e:
            logger.error(f"❌ Error sending status update: {e}")
    
    async def get_regime_history(self, symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get regime history for a symbol"""
        try:
            # Get regime history from Redis
            history_key = f"overmind:regime_history:{symbol}"
            history_data = self.redis_client.lrange(history_key, 0, hours * 60 // self.monitoring_interval)
            
            history = []
            for data in history_data:
                try:
                    regime_entry = json.loads(data)
                    history.append(regime_entry)
                except:
                    continue
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Error getting regime history: {e}")
            return []
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        uptime = time.time() - self.monitoring_stats['start_time']
        
        return {
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "total_checks": self.monitoring_stats['total_checks'],
            "regime_changes_detected": self.monitoring_stats['regime_changes_detected'],
            "alerts_sent": self.monitoring_stats['alerts_sent'],
            "symbols_monitored": self.symbols_to_monitor,
            "monitoring_interval": self.monitoring_interval,
            "current_regimes": self.previous_regimes,
            "change_detection_rate": self.monitoring_stats['regime_changes_detected'] / max(self.monitoring_stats['total_checks'], 1)
        }
    
    def stop_monitoring(self):
        """Stop regime monitoring"""
        self.running = False
        logger.info("⏹️ Regime monitoring stopped")

# Factory function
def create_regime_monitor(monitoring_interval: int = 60) -> RegimeMonitor:
    """Create regime monitor instance"""
    return RegimeMonitor(monitoring_interval)

# Example usage
if __name__ == "__main__":
    async def test_regime_monitoring():
        """Test regime monitoring"""
        monitor = create_regime_monitor(monitoring_interval=30)  # 30 seconds for testing
        
        try:
            # Run monitoring for a short time
            monitoring_task = asyncio.create_task(monitor.start_monitoring())
            
            # Let it run for 2 minutes
            await asyncio.sleep(120)
            
            # Stop monitoring
            monitor.stop_monitoring()
            monitoring_task.cancel()
            
            # Show stats
            stats = monitor.get_monitoring_stats()
            print("=== REGIME MONITORING STATS ===")
            for key, value in stats.items():
                print(f"{key}: {value}")
                
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("Monitoring stopped by user")
    
    asyncio.run(test_regime_monitoring())
