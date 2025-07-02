#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - 48H Final Validation Monitor
Comprehensive monitoring and analysis for final validation phase
"""

import asyncio
import json
import time
import redis
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        self.validation_start = time.time()
        self.validation_duration = 48 * 3600  # 48 hours
        
        # Validation metrics
        self.metrics = {
            'start_time': self.validation_start,
            'end_time': self.validation_start + self.validation_duration,
            'total_positions_opened': 0,
            'total_positions_closed': 0,
            'successful_exits': 0,
            'failed_exits': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'intelligence_accuracy': 0.0,
            'mev_protection_success': 0.0,
            'system_uptime': 0.0,
            'position_lifecycle_events': [],
            'intelligence_events': [],
            'exit_decisions': []
        }
        
        # Baseline portfolio state
        self.baseline_portfolio = None
        
    async def capture_baseline(self):
        """Capture baseline portfolio state"""
        try:
            position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
            if position_updates:
                self.baseline_portfolio = json.loads(position_updates[0])
                logger.info(f"📊 Baseline captured: {len(self.baseline_portfolio.get('positions', {}))} positions")
                
                # Store baseline
                baseline_data = {
                    'timestamp': time.time(),
                    'portfolio_state': self.baseline_portfolio,
                    'validation_start': True
                }
                
                self.redis_client.lpush('overmind:validation_baseline', json.dumps(baseline_data))
                
        except Exception as e:
            logger.error(f"❌ Error capturing baseline: {e}")
    
    def calculate_time_remaining(self):
        """Calculate remaining validation time"""
        elapsed = time.time() - self.validation_start
        remaining = self.validation_duration - elapsed
        return max(0, remaining)
    
    def get_validation_progress(self):
        """Get validation progress percentage"""
        elapsed = time.time() - self.validation_start
        progress = (elapsed / self.validation_duration) * 100
        return min(100, progress)
    
    async def analyze_position_lifecycle(self):
        """Analyze complete position lifecycle events"""
        try:
            # Get recent position updates
            position_updates = self.redis_client.lrange('overmind:position_updates', 0, 9)
            
            # Get recent exit signals
            exit_signals = self.redis_client.lrange('overmind:exit_signals', 0, 4)
            
            # Get recent execution results
            execution_results = self.redis_client.lrange('overmind:execution_results', 0, 9)
            
            lifecycle_analysis = {
                'timestamp': time.time(),
                'active_positions': len(position_updates),
                'recent_exits': len(exit_signals),
                'recent_executions': len(execution_results),
                'position_health': 'GOOD'
            }
            
            # Analyze position health
            if position_updates:
                latest_update = json.loads(position_updates[0])
                portfolio_metrics = latest_update.get('portfolio_metrics', {})
                
                total_pnl = portfolio_metrics.get('total_unrealized_pnl', 0)
                portfolio_return = portfolio_metrics.get('portfolio_return_pct', 0)
                
                lifecycle_analysis.update({
                    'current_pnl': total_pnl,
                    'portfolio_return': portfolio_return,
                    'position_count': len(latest_update.get('positions', {}))
                })
                
                # Update metrics
                self.metrics['total_pnl'] = total_pnl
                
                if portfolio_return < -5:
                    lifecycle_analysis['position_health'] = 'POOR'
                elif portfolio_return < 0:
                    lifecycle_analysis['position_health'] = 'FAIR'
            
            return lifecycle_analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing position lifecycle: {e}")
            return {'error': str(e), 'timestamp': time.time()}
    
    async def analyze_intelligence_performance(self):
        """Analyze Post-Trade Intelligence performance"""
        try:
            # Get recent intelligence updates
            intelligence_updates = self.redis_client.lrange('overmind:post_trade_intelligence', 0, 4)
            news_updates = self.redis_client.lrange('overmind:news_intelligence', 0, 2)
            whale_updates = self.redis_client.lrange('overmind:whale_analytics', 0, 2)
            
            intelligence_analysis = {
                'timestamp': time.time(),
                'intelligence_updates': len(intelligence_updates),
                'news_updates': len(news_updates),
                'whale_updates': len(whale_updates),
                'intelligence_health': 'OPERATIONAL'
            }
            
            # Analyze intelligence quality
            if intelligence_updates:
                latest_intel = json.loads(intelligence_updates[0])
                system_health = latest_intel.get('system_health', 0)
                component_status = latest_intel.get('component_status', {})
                
                active_components = sum(1 for status in component_status.values() if status)
                total_components = len(component_status)
                
                intelligence_analysis.update({
                    'system_health': system_health,
                    'active_components': active_components,
                    'total_components': total_components,
                    'component_uptime': active_components / total_components if total_components > 0 else 0
                })
                
                if system_health < 0.8:
                    intelligence_analysis['intelligence_health'] = 'DEGRADED'
                elif system_health < 0.5:
                    intelligence_analysis['intelligence_health'] = 'CRITICAL'
            
            return intelligence_analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing intelligence performance: {e}")
            return {'error': str(e), 'timestamp': time.time()}
    
    async def analyze_exit_decisions(self):
        """Analyze exit decision quality and timing"""
        try:
            # Get recent exit signals
            exit_signals = self.redis_client.lrange('overmind:exit_signals', 0, 9)
            
            exit_analysis = {
                'timestamp': time.time(),
                'total_exit_signals': len(exit_signals),
                'exit_actions': {'HOLD': 0, 'EXIT_PARTIAL': 0, 'EXIT_IMMEDIATELY': 0, 'ACCUMULATE': 0},
                'avg_confidence': 0.0,
                'exit_quality': 'GOOD'
            }
            
            if exit_signals:
                total_confidence = 0
                signal_count = 0
                
                for signal_str in exit_signals:
                    signal_data = json.loads(signal_str)
                    exit_signals_data = signal_data.get('exit_signals', {})
                    
                    for symbol, analysis in exit_signals_data.items():
                        ai_rec = analysis.get('ai_recommendation', {})
                        action = ai_rec.get('action', 'HOLD')
                        confidence = ai_rec.get('confidence', 0.5)
                        
                        exit_analysis['exit_actions'][action] = exit_analysis['exit_actions'].get(action, 0) + 1
                        total_confidence += confidence
                        signal_count += 1
                
                if signal_count > 0:
                    exit_analysis['avg_confidence'] = total_confidence / signal_count
                
                # Assess exit quality
                exit_rate = (exit_analysis['exit_actions']['EXIT_PARTIAL'] + 
                           exit_analysis['exit_actions']['EXIT_IMMEDIATELY']) / signal_count
                
                if exit_rate > 0.8:
                    exit_analysis['exit_quality'] = 'AGGRESSIVE'
                elif exit_rate < 0.1:
                    exit_analysis['exit_quality'] = 'CONSERVATIVE'
            
            return exit_analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing exit decisions: {e}")
            return {'error': str(e), 'timestamp': time.time()}
    
    def print_validation_status(self, lifecycle_analysis, intelligence_analysis, exit_analysis):
        """Print comprehensive validation status"""
        progress = self.get_validation_progress()
        remaining_hours = self.calculate_time_remaining() / 3600
        
        print("\n🔥 THE OVERMIND PROTOCOL - 48H FINAL VALIDATION")
        print("=" * 70)
        print(f"⏱️  VALIDATION PROGRESS: {progress:.1f}% ({remaining_hours:.1f}h remaining)")
        
        # Position Lifecycle Status
        print(f"\n📊 POSITION LIFECYCLE:")
        print(f"   Current P&L: ${lifecycle_analysis.get('current_pnl', 0):.6f}")
        print(f"   Portfolio Return: {lifecycle_analysis.get('portfolio_return', 0):.2f}%")
        print(f"   Active Positions: {lifecycle_analysis.get('position_count', 0)}")
        print(f"   Health Status: {lifecycle_analysis.get('position_health', 'UNKNOWN')}")
        
        # Intelligence Performance
        print(f"\n🧠 INTELLIGENCE PERFORMANCE:")
        print(f"   System Health: {intelligence_analysis.get('system_health', 0):.1%}")
        print(f"   Active Components: {intelligence_analysis.get('active_components', 0)}/{intelligence_analysis.get('total_components', 0)}")
        print(f"   Intelligence Status: {intelligence_analysis.get('intelligence_health', 'UNKNOWN')}")
        
        # Exit Decision Analysis
        print(f"\n🎯 EXIT DECISION ANALYSIS:")
        print(f"   Exit Signals Generated: {exit_analysis.get('total_exit_signals', 0)}")
        print(f"   Average Confidence: {exit_analysis.get('avg_confidence', 0):.2f}")
        print(f"   Exit Quality: {exit_analysis.get('exit_quality', 'UNKNOWN')}")
        
        exit_actions = exit_analysis.get('exit_actions', {})
        for action, count in exit_actions.items():
            if count > 0:
                print(f"   {action}: {count}")
        
        print(f"\n🔄 Last Update: {datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def store_validation_snapshot(self, lifecycle_analysis, intelligence_analysis, exit_analysis):
        """Store validation snapshot for historical analysis"""
        try:
            validation_snapshot = {
                'timestamp': time.time(),
                'validation_progress': self.get_validation_progress(),
                'remaining_time': self.calculate_time_remaining(),
                'lifecycle_analysis': lifecycle_analysis,
                'intelligence_analysis': intelligence_analysis,
                'exit_analysis': exit_analysis,
                'metrics': self.metrics
            }
            
            self.redis_client.lpush('overmind:validation_snapshots', json.dumps(validation_snapshot))
            
            # Keep only last 100 snapshots
            self.redis_client.ltrim('overmind:validation_snapshots', 0, 99)
            
        except Exception as e:
            logger.error(f"❌ Error storing validation snapshot: {e}")
    
    async def validation_monitoring_loop(self):
        """Main validation monitoring loop"""
        logger.info("🚀 Starting 48H Final Validation Monitor...")
        
        # Capture baseline
        await self.capture_baseline()
        
        while self.calculate_time_remaining() > 0:
            try:
                # Analyze all aspects
                lifecycle_analysis = await self.analyze_position_lifecycle()
                intelligence_analysis = await self.analyze_intelligence_performance()
                exit_analysis = await self.analyze_exit_decisions()
                
                # Print status
                self.print_validation_status(lifecycle_analysis, intelligence_analysis, exit_analysis)
                
                # Store snapshot
                await self.store_validation_snapshot(lifecycle_analysis, intelligence_analysis, exit_analysis)
                
                # Wait 5 minutes before next analysis
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Error in validation monitoring loop: {e}")
                await asyncio.sleep(60)
        
        logger.info("✅ 48H Validation Period Complete!")
        await self.generate_final_report()
    
    async def generate_final_report(self):
        """Generate final validation report"""
        try:
            # Get all validation snapshots
            snapshots = self.redis_client.lrange('overmind:validation_snapshots', 0, -1)
            
            final_report = {
                'validation_period': '48_hours',
                'start_time': self.validation_start,
                'end_time': time.time(),
                'total_snapshots': len(snapshots),
                'final_metrics': self.metrics,
                'recommendation': 'PENDING_ANALYSIS'
            }
            
            # Store final report
            self.redis_client.lpush('overmind:validation_final_report', json.dumps(final_report))
            
            print("\n🎯 48H VALIDATION COMPLETE - FINAL REPORT GENERATED")
            print("=" * 70)
            print(f"📊 Total Snapshots: {len(snapshots)}")
            print(f"⏱️  Duration: {(time.time() - self.validation_start) / 3600:.1f} hours")
            print(f"💰 Final P&L: ${self.metrics['total_pnl']:.6f}")
            
        except Exception as e:
            logger.error(f"❌ Error generating final report: {e}")

async def main():
    monitor = ValidationMonitor()
    await monitor.validation_monitoring_loop()

if __name__ == "__main__":
    asyncio.run(main())
