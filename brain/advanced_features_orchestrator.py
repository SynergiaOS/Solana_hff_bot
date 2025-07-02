#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Advanced Features Orchestrator
Coordinates all advanced trading features
"""

import asyncio
import json
import time
import redis
import logging
import subprocess
import sys
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedFeaturesOrchestrator:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Feature configuration
        self.features = {
            'add_to_winner': {
                'enabled': True,
                'script': 'brain/add_to_winner.py',
                'process': None,
                'restart_count': 0
            },
            'drawdown_guard': {
                'enabled': True,
                'script': 'brain/drawdown_guard.py',
                'process': None,
                'restart_count': 0
            },
            'feedback_scorer': {
                'enabled': True,
                'script': 'brain/feedback_scorer.py',
                'process': None,
                'restart_count': 0
            }
        }
        
        self.max_restarts = 5
        self.restart_delay = 30
        
    async def start_feature(self, feature_name: str) -> bool:
        """Start a specific advanced feature"""
        try:
            feature = self.features.get(feature_name)
            if not feature or not feature['enabled']:
                return False
            
            if feature['process'] and feature['process'].poll() is None:
                logger.info(f"✅ {feature_name} already running")
                return True
            
            logger.info(f"🚀 Starting {feature_name}...")
            
            # Start the process
            process = subprocess.Popen(
                [sys.executable, feature['script']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            feature['process'] = process
            
            # Wait a moment to check if it started successfully
            await asyncio.sleep(2)
            
            if process.poll() is None:
                logger.info(f"✅ {feature_name} started successfully (PID: {process.pid})")
                
                # Store feature status
                feature_status = {
                    'feature': feature_name,
                    'status': 'RUNNING',
                    'pid': process.pid,
                    'start_time': time.time(),
                    'restart_count': feature['restart_count']
                }
                
                self.redis_client.hset('overmind:advanced_features', feature_name, json.dumps(feature_status))
                return True
            else:
                logger.error(f"❌ {feature_name} failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting {feature_name}: {e}")
            return False
    
    async def stop_feature(self, feature_name: str) -> bool:
        """Stop a specific advanced feature"""
        try:
            feature = self.features.get(feature_name)
            if not feature:
                return False
            
            if feature['process'] and feature['process'].poll() is None:
                logger.info(f"🛑 Stopping {feature_name}...")
                feature['process'].terminate()
                
                # Wait for graceful shutdown
                try:
                    feature['process'].wait(timeout=10)
                except subprocess.TimeoutExpired:
                    feature['process'].kill()
                
                feature['process'] = None
                
                # Update status
                feature_status = {
                    'feature': feature_name,
                    'status': 'STOPPED',
                    'stop_time': time.time()
                }
                
                self.redis_client.hset('overmind:advanced_features', feature_name, json.dumps(feature_status))
                logger.info(f"✅ {feature_name} stopped")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping {feature_name}: {e}")
            return False
    
    async def restart_feature(self, feature_name: str) -> bool:
        """Restart a specific advanced feature"""
        logger.info(f"🔄 Restarting {feature_name}...")
        
        await self.stop_feature(feature_name)
        await asyncio.sleep(self.restart_delay)
        
        feature = self.features.get(feature_name)
        if feature:
            feature['restart_count'] += 1
        
        return await self.start_feature(feature_name)
    
    async def monitor_features(self):
        """Monitor all advanced features and restart if needed"""
        while True:
            try:
                for feature_name, feature in self.features.items():
                    if not feature['enabled']:
                        continue
                    
                    # Check if process is running
                    if feature['process'] is None or feature['process'].poll() is not None:
                        if feature['restart_count'] < self.max_restarts:
                            logger.warning(f"⚠️ {feature_name} not running, restarting...")
                            await self.restart_feature(feature_name)
                        else:
                            logger.error(f"❌ {feature_name} exceeded max restarts, disabling")
                            feature['enabled'] = False
                    
                    # Update heartbeat
                    if feature['process'] and feature['process'].poll() is None:
                        heartbeat = {
                            'feature': feature_name,
                            'status': 'RUNNING',
                            'pid': feature['process'].pid,
                            'last_heartbeat': time.time()
                        }
                        
                        self.redis_client.hset('overmind:feature_heartbeats', feature_name, json.dumps(heartbeat))
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error monitoring features: {e}")
                await asyncio.sleep(30)
    
    async def start_all_features(self):
        """Start all enabled advanced features"""
        logger.info("🚀 Starting all advanced trading features...")
        
        for feature_name in self.features.keys():
            if self.features[feature_name]['enabled']:
                await self.start_feature(feature_name)
                await asyncio.sleep(5)  # Stagger startup
        
        logger.info("✅ All advanced features startup complete")
    
    async def stop_all_features(self):
        """Stop all advanced features"""
        logger.info("🛑 Stopping all advanced features...")
        
        for feature_name in self.features.keys():
            await self.stop_feature(feature_name)
        
        logger.info("✅ All advanced features stopped")
    
    async def get_features_status(self) -> Dict:
        """Get status of all advanced features"""
        status = {}
        
        for feature_name, feature in self.features.items():
            if feature['process'] and feature['process'].poll() is None:
                status[feature_name] = {
                    'status': 'RUNNING',
                    'pid': feature['process'].pid,
                    'restart_count': feature['restart_count']
                }
            else:
                status[feature_name] = {
                    'status': 'STOPPED',
                    'restart_count': feature['restart_count']
                }
        
        return status
    
    async def handle_commands(self):
        """Handle orchestrator commands from Redis"""
        while True:
            try:
                # Check for commands
                command = self.redis_client.blpop('overmind:orchestrator_commands', timeout=5)
                
                if command:
                    command_data = json.loads(command[1])
                    action = command_data.get('action')
                    feature = command_data.get('feature', 'all')
                    
                    if action == 'start':
                        if feature == 'all':
                            await self.start_all_features()
                        else:
                            await self.start_feature(feature)
                    
                    elif action == 'stop':
                        if feature == 'all':
                            await self.stop_all_features()
                        else:
                            await self.stop_feature(feature)
                    
                    elif action == 'restart':
                        if feature == 'all':
                            await self.stop_all_features()
                            await asyncio.sleep(10)
                            await self.start_all_features()
                        else:
                            await self.restart_feature(feature)
                    
                    elif action == 'status':
                        status = await self.get_features_status()
                        self.redis_client.set('overmind:features_status', json.dumps(status))
                
            except Exception as e:
                logger.error(f"❌ Error handling commands: {e}")
                await asyncio.sleep(5)
    
    async def run_orchestrator(self):
        """Main orchestrator loop"""
        logger.info("🎯 Starting Advanced Features Orchestrator")
        
        # Start all features
        await self.start_all_features()
        
        # Run monitoring and command handling concurrently
        await asyncio.gather(
            self.monitor_features(),
            self.handle_commands()
        )

async def main():
    orchestrator = AdvancedFeaturesOrchestrator()
    
    try:
        await orchestrator.run_orchestrator()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down orchestrator...")
        await orchestrator.stop_all_features()

if __name__ == "__main__":
    asyncio.run(main())
