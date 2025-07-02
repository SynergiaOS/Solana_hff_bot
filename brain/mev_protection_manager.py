#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - MEV Protection Manager
Integrated MEV protection system for live trading
"""

import asyncio
import json
import redis
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from mev_risk_analyzer import create_mev_risk_analyzer, MEVRiskLevel
from transaction_timing_optimizer import create_transaction_timing_optimizer
from anti_sandwich_protection import create_anti_sandwich_protection

# Import vector memory for MEV incident storage
try:
    import sys
    import os
    # Add the correct path to vector memory
    brain_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join(brain_path, 'src', 'overmind_brain'))
    from vector_memory import VectorMemory
    VECTOR_MEMORY_AVAILABLE = True
except ImportError:
    VECTOR_MEMORY_AVAILABLE = False
    print("⚠️ Vector Memory not available - MEV incidents will only be stored in Redis")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MEVProtectionManager')

class MEVProtectionManager:
    """
    Integrated MEV Protection Manager
    
    Coordinates all MEV protection systems:
    - Risk assessment
    - Timing optimization
    - Anti-sandwich protection
    - Integration with Rust Executor
    """
    
    def __init__(self):
        """Initialize MEV Protection Manager"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Initialize protection components
        self.risk_analyzer = create_mev_risk_analyzer()
        self.timing_optimizer = create_transaction_timing_optimizer()
        self.sandwich_protection = create_anti_sandwich_protection()

        # Initialize vector memory for MEV incident storage
        self.vector_memory = None
        if VECTOR_MEMORY_AVAILABLE:
            try:
                self.vector_memory = VectorMemory()
                logger.info("🧠 Vector Memory initialized for MEV incident storage")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Vector Memory: {e}")
                self.vector_memory = None
        
        # Protection statistics
        self.protection_stats = {
            'total_transactions': 0,
            'protected_transactions': 0,
            'mev_attacks_prevented': 0,
            'estimated_savings': 0.0,
            'protection_effectiveness': 0.0
        }
        
        # Running flag
        self.running = False
        
        logger.info("🛡️ MEV Protection Manager initialized")
        logger.info("⚡ Integrated protection systems ready")
        logger.info("🎯 Live trading protection enabled")
    
    async def protect_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply comprehensive MEV protection to a transaction
        """
        try:
            logger.info(f"🛡️ Applying MEV protection to transaction...")
            
            # Step 1: MEV Risk Assessment
            risk_assessment = await self.risk_analyzer.assess_mev_risk(
                transaction_data.get('token_address', 'unknown'),
                transaction_data.get('amount', 0.0),
                transaction_data.get('transaction_type', 'swap')
            )
            
            # Step 2: Timing Optimization
            timing_recommendation = await self.timing_optimizer.optimize_transaction_timing(
                transaction_data.get('token_address', 'unknown'),
                transaction_data.get('amount', 0.0),
                transaction_data.get('urgency', 'normal')
            )
            
            # Step 3: Anti-Sandwich Protection
            sandwich_analysis = await self.sandwich_protection.comprehensive_protection_analysis(
                transaction_data
            )
            
            # Step 4: Integrate all protections
            protected_transaction = await self.integrate_protections(
                transaction_data, risk_assessment, timing_recommendation, sandwich_analysis
            )
            
            # Step 5: Generate protection report
            protection_report = self.generate_protection_report(
                risk_assessment, timing_recommendation, sandwich_analysis
            )
            
            # Update statistics
            self.update_protection_stats(protection_report)
            
            # Store protection data
            await self.store_protection_data(protected_transaction, protection_report)

            # Store MEV incident in vector memory for learning
            await self.store_mev_incident_in_vector_memory(
                transaction_data, risk_assessment, timing_recommendation, protection_report
            )
            
            logger.info(f"✅ MEV protection applied successfully")
            logger.info(f"   Risk Level: {risk_assessment.risk_level.value}")
            logger.info(f"   Timing Strategy: {timing_recommendation.strategy.value}")
            logger.info(f"   Protection Effectiveness: {protection_report['overall_effectiveness']:.1%}")
            
            return {
                'protected_transaction': protected_transaction,
                'protection_report': protection_report,
                'original_transaction': transaction_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error applying MEV protection: {e}")
            return {
                'protected_transaction': transaction_data,
                'protection_report': {'error': str(e)},
                'original_transaction': transaction_data
            }
    
    async def integrate_protections(self, 
                                  transaction_data: Dict[str, Any],
                                  risk_assessment,
                                  timing_recommendation,
                                  sandwich_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate all protection mechanisms"""
        try:
            # Start with original transaction
            protected_tx = transaction_data.copy()
            
            # Apply MEV risk-based protections
            if risk_assessment.use_jito_bundle:
                protected_tx['use_jito_bundle'] = True
                protected_tx['jito_tip'] = risk_assessment.recommended_priority_fee
            
            # Apply timing optimizations
            protected_tx['timing_delay'] = timing_recommendation.delay_seconds
            protected_tx['priority_fee_multiplier'] = timing_recommendation.priority_fee_multiplier
            protected_tx['optimal_execution_time'] = timing_recommendation.optimal_execution_time
            
            # Apply sandwich protections
            if 'protected_transaction' in sandwich_analysis:
                sandwich_protected = sandwich_analysis['protected_transaction']
                
                # Merge sandwich protections
                for key, value in sandwich_protected.items():
                    if key.startswith('protection_') or key in ['slippage', 'split_transaction', 'use_private_mempool']:
                        protected_tx[key] = value
            
            # Apply combined slippage (take maximum for safety)
            base_slippage = transaction_data.get('slippage', 0.01)
            risk_slippage = risk_assessment.recommended_slippage
            sandwich_slippage = sandwich_analysis.get('protected_transaction', {}).get('slippage', base_slippage)
            
            protected_tx['slippage'] = max(base_slippage, risk_slippage, sandwich_slippage)
            
            # Apply emergency protections
            if (risk_assessment.risk_level == MEVRiskLevel.EXTREME or 
                sandwich_analysis.get('protection_strategy', {}).emergency_abort):
                protected_tx['emergency_abort'] = True
                protected_tx['abort_reason'] = "Extreme MEV risk detected"
            
            # Add protection metadata
            protected_tx['mev_protection_applied'] = True
            protected_tx['protection_timestamp'] = time.time()
            protected_tx['risk_score'] = risk_assessment.risk_score
            protected_tx['timing_strategy'] = timing_recommendation.strategy.value
            
            return protected_tx
            
        except Exception as e:
            logger.error(f"❌ Error integrating protections: {e}")
            return transaction_data
    
    def generate_protection_report(self, risk_assessment, timing_recommendation, sandwich_analysis) -> Dict[str, Any]:
        """Generate comprehensive protection report"""
        try:
            # Calculate overall effectiveness
            risk_effectiveness = 1.0 - risk_assessment.risk_score
            timing_effectiveness = timing_recommendation.confidence
            sandwich_effectiveness = sandwich_analysis.get('protection_strategy', {}).estimated_effectiveness or 0.5
            
            overall_effectiveness = (risk_effectiveness + timing_effectiveness + sandwich_effectiveness) / 3.0
            
            # Determine protection level
            if overall_effectiveness > 0.8:
                protection_level = "MAXIMUM"
            elif overall_effectiveness > 0.6:
                protection_level = "HIGH"
            elif overall_effectiveness > 0.4:
                protection_level = "MEDIUM"
            else:
                protection_level = "LOW"
            
            # Calculate estimated savings
            threat_level = sandwich_analysis.get('threat_assessment', {}).threat_level or 0.0
            estimated_loss_prevented = sandwich_analysis.get('threat_assessment', {}).estimated_loss or 0.0
            
            report = {
                'overall_effectiveness': overall_effectiveness,
                'protection_level': protection_level,
                'risk_assessment': {
                    'risk_score': risk_assessment.risk_score,
                    'risk_level': risk_assessment.risk_level.value,
                    'recommended_slippage': risk_assessment.recommended_slippage,
                    'use_jito_bundle': risk_assessment.use_jito_bundle
                },
                'timing_optimization': {
                    'strategy': timing_recommendation.strategy.value,
                    'delay_seconds': timing_recommendation.delay_seconds,
                    'confidence': timing_recommendation.confidence
                },
                'sandwich_protection': {
                    'threat_level': threat_level,
                    'protection_level': sandwich_analysis.get('protection_strategy', {}).protection_level.value if sandwich_analysis.get('protection_strategy') else 'minimal',
                    'estimated_loss_prevented': estimated_loss_prevented
                },
                'protections_applied': {
                    'jito_bundle': risk_assessment.use_jito_bundle,
                    'timing_delay': timing_recommendation.delay_seconds > 0,
                    'slippage_increase': risk_assessment.recommended_slippage > 0.01,
                    'private_mempool': sandwich_analysis.get('protection_strategy', {}).use_private_mempool or False
                },
                'estimated_savings': estimated_loss_prevented,
                'timestamp': time.time()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating protection report: {e}")
            return {'error': str(e), 'overall_effectiveness': 0.5}
    
    def update_protection_stats(self, protection_report: Dict[str, Any]):
        """Update protection statistics"""
        try:
            self.protection_stats['total_transactions'] += 1
            
            if protection_report.get('overall_effectiveness', 0.0) > 0.5:
                self.protection_stats['protected_transactions'] += 1
            
            # Estimate MEV attacks prevented
            if protection_report.get('sandwich_protection', {}).get('threat_level', 0.0) > 0.5:
                self.protection_stats['mev_attacks_prevented'] += 1
            
            # Add estimated savings
            savings = protection_report.get('estimated_savings', 0.0)
            self.protection_stats['estimated_savings'] += savings
            
            # Update average effectiveness
            total_protected = self.protection_stats['protected_transactions']
            if total_protected > 0:
                current_avg = self.protection_stats['protection_effectiveness']
                new_effectiveness = protection_report.get('overall_effectiveness', 0.0)
                self.protection_stats['protection_effectiveness'] = (
                    (current_avg * (total_protected - 1) + new_effectiveness) / total_protected
                )
            
        except Exception as e:
            logger.error(f"❌ Error updating protection stats: {e}")
    
    async def store_protection_data(self, protected_transaction: Dict[str, Any], 
                                  protection_report: Dict[str, Any]):
        """Store protection data in Redis"""
        try:
            # Store current protection status
            protection_data = {
                'protected_transaction': protected_transaction,
                'protection_report': protection_report,
                'timestamp': time.time()
            }
            
            self.redis_client.setex("overmind:mev_protection", 300, json.dumps(protection_data))
            
            # Add to protection history
            self.redis_client.lpush("overmind:mev_protection_history", json.dumps(protection_data))
            self.redis_client.ltrim("overmind:mev_protection_history", 0, 99)  # Keep last 100
            
            # Store statistics
            self.redis_client.setex("overmind:mev_protection_stats", 3600, json.dumps(self.protection_stats))
            
            logger.info("📊 MEV protection data stored")
            
        except Exception as e:
            logger.error(f"❌ Error storing protection data: {e}")

    async def store_mev_incident_in_vector_memory(self,
                                                transaction_data: Dict[str, Any],
                                                risk_assessment,
                                                timing_recommendation,
                                                protection_report: Dict[str, Any]):
        """Store MEV incident in vector memory for learning and pattern recognition"""
        try:
            if not self.vector_memory:
                logger.debug("🧠 Vector Memory not available - skipping MEV incident storage")
                return

            # Create MEV incident record for vector memory
            mev_incident = {
                "incident_type": "mev_protection_applied",
                "timestamp": datetime.now().isoformat(),
                "token_address": transaction_data.get('token_address', 'unknown'),
                "transaction_amount": transaction_data.get('amount', 0.0),
                "transaction_type": transaction_data.get('transaction_type', 'swap'),

                # Risk assessment data
                "risk_score": risk_assessment.risk_score,
                "risk_level": risk_assessment.risk_level.value,
                "congestion_score": risk_assessment.congestion_score,
                "bot_activity_score": risk_assessment.bot_activity_score,
                "sandwich_risk": risk_assessment.sandwich_risk,
                "frontrun_risk": risk_assessment.frontrun_risk,

                # Protection measures applied
                "protection_applied": {
                    "use_jito_bundle": risk_assessment.use_jito_bundle,
                    "timing_delay": timing_recommendation.delay_seconds,
                    "slippage_adjustment": risk_assessment.recommended_slippage,
                    "priority_fee_multiplier": timing_recommendation.priority_fee_multiplier,
                    "timing_strategy": timing_recommendation.strategy.value
                },

                # Effectiveness metrics
                "protection_effectiveness": protection_report['overall_effectiveness'],
                "protection_level": protection_report['protection_level'],
                "estimated_savings": protection_report.get('estimated_savings', 0.0),

                # Learning data
                "market_conditions": {
                    "network_congestion": risk_assessment.congestion_score,
                    "bot_activity": risk_assessment.bot_activity_score,
                    "time_of_day": datetime.now().hour
                },

                "outcome": "protection_applied",  # Will be updated with actual results
                "lessons_learned": f"Applied {protection_report['protection_level']} protection with {protection_report['overall_effectiveness']:.1%} effectiveness"
            }

            # Store in vector memory with MEV-specific metadata
            metadata = {
                "category": "mev_incident",
                "risk_level": risk_assessment.risk_level.value,
                "protection_level": protection_report['protection_level'],
                "token": transaction_data.get('token_address', 'unknown'),
                "timestamp": time.time(),
                "effectiveness": protection_report['overall_effectiveness']
            }

            # Create searchable content for vector memory
            content = f"""
            MEV Protection Incident Report:
            Token: {transaction_data.get('token_address', 'unknown')}
            Amount: {transaction_data.get('amount', 0.0)} SOL
            Risk Level: {risk_assessment.risk_level.value}
            Risk Score: {risk_assessment.risk_score:.2f}

            Protection Measures:
            - Jito Bundle: {risk_assessment.use_jito_bundle}
            - Timing Delay: {timing_recommendation.delay_seconds}s
            - Slippage: {risk_assessment.recommended_slippage:.1%}
            - Strategy: {timing_recommendation.strategy.value}

            Effectiveness: {protection_report['overall_effectiveness']:.1%}
            Protection Level: {protection_report['protection_level']}

            Market Conditions:
            - Network Congestion: {risk_assessment.congestion_score:.2f}
            - Bot Activity: {risk_assessment.bot_activity_score:.2f}
            - Sandwich Risk: {risk_assessment.sandwich_risk:.2f}
            - Frontrun Risk: {risk_assessment.frontrun_risk:.2f}

            Reasoning: {risk_assessment.reasoning}
            """

            # Store in vector memory
            self.vector_memory.store_memory(
                content=content.strip(),
                metadata=metadata,
                memory_type="mev_incident"
            )

            logger.info(f"🧠 MEV incident stored in vector memory: {risk_assessment.risk_level.value} risk")

        except Exception as e:
            logger.error(f"❌ Error storing MEV incident in vector memory: {e}")

    async def process_trading_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process trading command with MEV protection"""
        try:
            logger.info(f"🛡️ Processing trading command with MEV protection...")
            
            # Apply MEV protection
            protection_result = await self.protect_transaction(command)
            
            # Get protected transaction
            protected_command = protection_result['protected_transaction']
            protection_report = protection_result['protection_report']
            
            # Check for emergency abort
            if protected_command.get('emergency_abort', False):
                logger.warning(f"🚨 EMERGENCY ABORT: {protected_command.get('abort_reason', 'Unknown')}")
                return {
                    'status': 'ABORTED',
                    'reason': protected_command.get('abort_reason', 'Emergency abort due to MEV risk'),
                    'original_command': command,
                    'protection_report': protection_report
                }
            
            # Apply timing delay if needed
            delay = protected_command.get('timing_delay', 0)
            if delay > 0:
                logger.info(f"⏰ Applying timing delay: {delay} seconds")
                await asyncio.sleep(delay)
            
            # Send protected command to Rust Executor
            await self.send_to_executor(protected_command)
            
            return {
                'status': 'PROTECTED_AND_SENT',
                'protected_command': protected_command,
                'protection_report': protection_report,
                'original_command': command
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing trading command: {e}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'original_command': command
            }
    
    async def send_to_executor(self, protected_command: Dict[str, Any]):
        """Send protected command to Rust Executor"""
        try:
            # Add MEV protection flags for Rust Executor
            executor_command = protected_command.copy()
            
            # Set Jito bundle parameters
            if protected_command.get('use_jito_bundle', False):
                executor_command['execution_method'] = 'jito_bundle'
                executor_command['jito_tip'] = protected_command.get('jito_tip', 0.00001)
            
            # Set priority fee
            if 'priority_fee_multiplier' in protected_command:
                base_fee = 0.000005  # 5000 lamports
                executor_command['priority_fee'] = base_fee * protected_command['priority_fee_multiplier']
            
            # Send to Rust Executor via Redis
            self.redis_client.lpush("overmind:commands", json.dumps(executor_command))
            
            logger.info(f"📤 Protected command sent to Rust Executor")
            logger.info(f"   Use Jito Bundle: {executor_command.get('use_jito_bundle', False)}")
            logger.info(f"   Priority Fee: {executor_command.get('priority_fee', 'default')}")
            
        except Exception as e:
            logger.error(f"❌ Error sending to executor: {e}")
    
    async def start_protection_service(self):
        """Start MEV protection service"""
        logger.info("🛡️ Starting MEV Protection Service...")
        self.running = True
        
        while self.running:
            try:
                # Listen for trading commands
                result = self.redis_client.blpop("overmind:mev_commands", timeout=5)
                
                if result:
                    _, command_data = result
                    command = json.loads(command_data)
                    
                    # Process command with MEV protection
                    await self.process_trading_command(command)
                
            except Exception as e:
                logger.error(f"❌ Error in protection service: {e}")
                await asyncio.sleep(5)
    
    def get_protection_statistics(self) -> Dict[str, Any]:
        """Get MEV protection statistics"""
        return {
            'protection_stats': self.protection_stats,
            'uptime': time.time() - (self.protection_stats.get('start_time', time.time())),
            'protection_rate': (
                self.protection_stats['protected_transactions'] / 
                max(self.protection_stats['total_transactions'], 1)
            ),
            'average_effectiveness': self.protection_stats['protection_effectiveness'],
            'estimated_total_savings': self.protection_stats['estimated_savings']
        }
    
    def stop_protection_service(self):
        """Stop MEV protection service"""
        self.running = False
        logger.info("⏹️ MEV Protection Service stopped")

# Factory function
def create_mev_protection_manager() -> MEVProtectionManager:
    """Create MEV protection manager instance"""
    return MEVProtectionManager()

# Example usage
if __name__ == "__main__":
    async def test_mev_protection_manager():
        """Test MEV protection manager"""
        manager = create_mev_protection_manager()
        
        # Test transaction
        test_transaction = {
            'command_id': 'test_mev_protection_001',
            'action': 'BUY',
            'symbol': 'JTO/SOL',
            'token_address': 'JTO',
            'amount': 100.0,
            'slippage': 0.01,
            'urgency': 'normal',
            'transaction_type': 'swap'
        }
        
        # Apply MEV protection
        result = await manager.protect_transaction(test_transaction)
        
        print("=== MEV PROTECTION MANAGER TEST ===")
        
        protection_report = result['protection_report']
        print(f"Overall Effectiveness: {protection_report['overall_effectiveness']:.1%}")
        print(f"Protection Level: {protection_report['protection_level']}")
        
        print(f"\nRisk Assessment:")
        risk = protection_report['risk_assessment']
        print(f"  Risk Score: {risk['risk_score']:.2f}")
        print(f"  Risk Level: {risk['risk_level']}")
        print(f"  Use Jito Bundle: {risk['use_jito_bundle']}")
        
        print(f"\nTiming Optimization:")
        timing = protection_report['timing_optimization']
        print(f"  Strategy: {timing['strategy']}")
        print(f"  Delay: {timing['delay_seconds']}s")
        print(f"  Confidence: {timing['confidence']:.1%}")
        
        print(f"\nSandwich Protection:")
        sandwich = protection_report['sandwich_protection']
        print(f"  Threat Level: {sandwich['threat_level']:.1%}")
        print(f"  Protection Level: {sandwich['protection_level']}")
        print(f"  Estimated Savings: ${sandwich['estimated_loss_prevented']:.6f}")
        
        protected_tx = result['protected_transaction']
        print(f"\nProtected Transaction Changes:")
        for key, value in protected_tx.items():
            if key not in test_transaction or protected_tx[key] != test_transaction[key]:
                print(f"  {key}: {value}")
        
        # Test statistics
        stats = manager.get_protection_statistics()
        print(f"\nProtection Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    asyncio.run(test_mev_protection_manager())
