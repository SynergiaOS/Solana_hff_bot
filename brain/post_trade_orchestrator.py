#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Post-Trade Orchestrator
Main coordinator for Post-Trade Intelligence Layer
"""

import asyncio
import json
import time
import redis
import logging
from datetime import datetime
from typing import Dict, List, Optional
import subprocess
import sys

# Import our Post-Trade Intelligence modules
from position_monitor import PositionMonitor
from news_intelligence import NewsIntelligence
from onchain_analytics import OnChainAnalytics
from exit_strategy_manager import ExitStrategyManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostTradeOrchestrator:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Initialize all components
        self.position_monitor = PositionMonitor()
        self.news_intelligence = NewsIntelligence()
        self.onchain_analytics = OnChainAnalytics()
        self.exit_strategy_manager = ExitStrategyManager()
        
        # Orchestrator state
        self.is_running = False
        self.component_status = {
            'position_monitor': False,
            'news_intelligence': False,
            'onchain_analytics': False,
            'exit_strategy_manager': False
        }
        
        # Performance metrics
        self.metrics = {
            'total_positions_monitored': 0,
            'exit_signals_generated': 0,
            'successful_exits': 0,
            'total_profit_from_exits': 0.0,
            'start_time': time.time(),
            'last_update': time.time()
        }
    
    async def start_position_monitor(self):
        """Start position monitoring component"""
        try:
            logger.info("🚀 Starting Position Monitor...")
            
            # Load initial positions
            await self.position_monitor.load_positions_from_redis()
            
            # Start monitoring loop in background
            asyncio.create_task(self.position_monitor.monitor_positions())
            
            self.component_status['position_monitor'] = True
            logger.info("✅ Position Monitor started successfully")
            
        except Exception as e:
            logger.error(f"❌ Error starting Position Monitor: {e}")
            self.component_status['position_monitor'] = False
    
    async def start_news_intelligence(self):
        """Start news intelligence component"""
        try:
            logger.info("🚀 Starting News Intelligence...")
            
            # Start news monitoring loop in background
            asyncio.create_task(self.news_intelligence.news_monitoring_loop())
            
            self.component_status['news_intelligence'] = True
            logger.info("✅ News Intelligence started successfully")
            
        except Exception as e:
            logger.error(f"❌ Error starting News Intelligence: {e}")
            self.component_status['news_intelligence'] = False
    
    async def start_onchain_analytics(self):
        """Start on-chain analytics component"""
        try:
            logger.info("🚀 Starting On-Chain Analytics...")
            
            # Start whale monitoring loop in background
            asyncio.create_task(self.onchain_analytics.whale_monitoring_loop())
            
            self.component_status['onchain_analytics'] = True
            logger.info("✅ On-Chain Analytics started successfully")
            
        except Exception as e:
            logger.error(f"❌ Error starting On-Chain Analytics: {e}")
            self.component_status['onchain_analytics'] = False
    
    async def start_exit_strategy_manager(self):
        """Start exit strategy manager component"""
        try:
            logger.info("🚀 Starting Exit Strategy Manager...")
            
            # Start exit strategy loop in background
            asyncio.create_task(self.exit_strategy_manager.exit_strategy_loop())
            
            self.component_status['exit_strategy_manager'] = True
            logger.info("✅ Exit Strategy Manager started successfully")
            
        except Exception as e:
            logger.error(f"❌ Error starting Exit Strategy Manager: {e}")
            self.component_status['exit_strategy_manager'] = False
    
    async def monitor_system_health(self):
        """Monitor health of all components"""
        try:
            # Check Redis connectivity
            self.redis_client.ping()
            
            # Check component status
            active_components = sum(1 for status in self.component_status.values() if status)
            total_components = len(self.component_status)
            
            health_score = active_components / total_components
            
            # Update metrics
            self.metrics['last_update'] = time.time()
            self.metrics['health_score'] = health_score
            self.metrics['active_components'] = active_components
            
            # Publish health status
            health_status = {
                'timestamp': time.time(),
                'component_status': self.component_status,
                'health_score': health_score,
                'metrics': self.metrics,
                'update_type': 'system_health'
            }
            
            self.redis_client.lpush('overmind:system_health', json.dumps(health_status))
            self.redis_client.ltrim('overmind:system_health', 0, 99)
            
            return health_score
            
        except Exception as e:
            logger.error(f"❌ Error monitoring system health: {e}")
            return 0.0
    
    async def collect_intelligence_summary(self) -> Dict:
        """Collect summary from all intelligence sources"""
        try:
            summary = {
                'timestamp': time.time(),
                'positions': {},
                'news_intelligence': {},
                'whale_analytics': {},
                'exit_signals': {},
                'overall_status': 'OPERATIONAL'
            }
            
            # Get position data
            try:
                position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
                if position_updates:
                    pos_data = json.loads(position_updates[0])
                    summary['positions'] = pos_data.get('positions', {})
                    summary['portfolio_metrics'] = pos_data.get('portfolio_metrics', {})
            except Exception as e:
                logger.error(f"❌ Error collecting position data: {e}")
            
            # Get news intelligence
            try:
                news_updates = self.redis_client.lrange('overmind:news_intelligence', 0, 0)
                if news_updates:
                    news_data = json.loads(news_updates[0])
                    summary['news_intelligence'] = news_data.get('news_intelligence', {})
            except Exception as e:
                logger.error(f"❌ Error collecting news data: {e}")
            
            # Get whale analytics
            try:
                whale_updates = self.redis_client.lrange('overmind:whale_analytics', 0, 0)
                if whale_updates:
                    whale_data = json.loads(whale_updates[0])
                    summary['whale_analytics'] = whale_data.get('whale_analytics', {})
            except Exception as e:
                logger.error(f"❌ Error collecting whale data: {e}")
            
            # Get exit signals
            try:
                exit_updates = self.redis_client.lrange('overmind:exit_signals', 0, 0)
                if exit_updates:
                    exit_data = json.loads(exit_updates[0])
                    summary['exit_signals'] = exit_data.get('exit_signals', {})
            except Exception as e:
                logger.error(f"❌ Error collecting exit signals: {e}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error collecting intelligence summary: {e}")
            return {'timestamp': time.time(), 'error': str(e)}
    
    def print_orchestrator_status(self, intelligence_summary: Dict):
        """Print comprehensive status of Post-Trade Intelligence"""
        print("\n🧠 THE OVERMIND PROTOCOL - POST-TRADE INTELLIGENCE")
        print("=" * 70)
        
        # Component Status
        print("🔧 COMPONENT STATUS:")
        for component, status in self.component_status.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {component.replace('_', ' ').title()}")
        
        # Portfolio Summary
        positions = intelligence_summary.get('positions', {})
        portfolio_metrics = intelligence_summary.get('portfolio_metrics', {})
        
        if positions:
            print(f"\n💰 PORTFOLIO SUMMARY:")
            total_pnl = portfolio_metrics.get('total_unrealized_pnl', 0)
            portfolio_return = portfolio_metrics.get('portfolio_return_pct', 0)
            print(f"   Total P&L: ${total_pnl:.6f} ({portfolio_return:+.2f}%)")
            print(f"   Open Positions: {len([p for p in positions.values() if p.get('quantity', 0) > 0])}")
        
        # Intelligence Summary
        news_intel = intelligence_summary.get('news_intelligence', {})
        whale_analytics = intelligence_summary.get('whale_analytics', {})
        exit_signals = intelligence_summary.get('exit_signals', {})
        
        if news_intel:
            print(f"\n📰 NEWS INTELLIGENCE:")
            for symbol, data in list(news_intel.items())[:3]:
                sentiment = data.get('avg_sentiment', 0.5)
                news_count = data.get('news_count', 0)
                sentiment_icon = "🟢" if sentiment > 0.6 else "🔴" if sentiment < 0.4 else "⚪"
                print(f"   {sentiment_icon} {symbol}: {sentiment:.2f} sentiment ({news_count} news)")
        
        if whale_analytics:
            print(f"\n🐋 WHALE ACTIVITY:")
            for symbol, data in list(whale_analytics.items())[:3]:
                whale_count = data.get('whale_count', 0)
                buy_pressure = data.get('buy_pressure', 0.5)
                pressure_icon = "🟢" if buy_pressure > 0.6 else "🔴" if buy_pressure < 0.4 else "⚪"
                print(f"   {pressure_icon} {symbol}: {whale_count} whales (Buy: {buy_pressure:.1%})")
        
        if exit_signals:
            print(f"\n🎯 EXIT SIGNALS:")
            for symbol, analysis in list(exit_signals.items())[:3]:
                ai_rec = analysis.get('ai_recommendation', {})
                action = ai_rec.get('action', 'HOLD')
                confidence = ai_rec.get('confidence', 0.5)
                action_icon = "🔴" if action.startswith('EXIT') else "🟢" if action == 'ACCUMULATE' else "⚪"
                print(f"   {action_icon} {symbol}: {action} (Conf: {confidence:.2f})")
        
        # System Metrics
        uptime = time.time() - self.metrics['start_time']
        print(f"\n📊 SYSTEM METRICS:")
        print(f"   Uptime: {uptime/3600:.1f} hours")
        print(f"   Health Score: {self.metrics.get('health_score', 0):.1%}")
        print(f"   Last Update: {datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')}")
    
    async def orchestrator_main_loop(self):
        """Main orchestrator loop"""
        logger.info("🚀 Starting Post-Trade Intelligence Orchestrator...")
        
        # Start all components
        await self.start_position_monitor()
        await asyncio.sleep(2)
        
        await self.start_news_intelligence()
        await asyncio.sleep(2)
        
        await self.start_onchain_analytics()
        await asyncio.sleep(2)
        
        await self.start_exit_strategy_manager()
        await asyncio.sleep(5)
        
        self.is_running = True
        logger.info("✅ All Post-Trade Intelligence components started")
        
        # Main monitoring loop
        while self.is_running:
            try:
                # Monitor system health
                health_score = await self.monitor_system_health()
                
                # Collect intelligence summary
                intelligence_summary = await self.collect_intelligence_summary()
                
                # Print status
                self.print_orchestrator_status(intelligence_summary)
                
                # Publish comprehensive intelligence update
                intelligence_update = {
                    'timestamp': time.time(),
                    'intelligence_summary': intelligence_summary,
                    'system_health': health_score,
                    'component_status': self.component_status,
                    'update_type': 'post_trade_intelligence'
                }
                
                self.redis_client.lpush('overmind:post_trade_intelligence', json.dumps(intelligence_update))
                self.redis_client.ltrim('overmind:post_trade_intelligence', 0, 49)
                
                # Wait 30 seconds before next update
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ Error in orchestrator main loop: {e}")
                await asyncio.sleep(10)
    
    async def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("🛑 Shutting down Post-Trade Intelligence Orchestrator...")
        self.is_running = False
        
        # Update component status
        for component in self.component_status:
            self.component_status[component] = False
        
        logger.info("✅ Post-Trade Intelligence Orchestrator shutdown complete")

async def main():
    orchestrator = PostTradeOrchestrator()
    
    try:
        await orchestrator.orchestrator_main_loop()
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal...")
        await orchestrator.shutdown()
    except Exception as e:
        logger.error(f"❌ Fatal error in orchestrator: {e}")
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
