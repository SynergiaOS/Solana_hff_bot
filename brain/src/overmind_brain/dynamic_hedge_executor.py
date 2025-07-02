#!/usr/bin/env python3
"""
Dynamic Hedge Executor
Automatic execution of hedging strategies and position management
"""

import asyncio
import logging
import json
import time
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class HedgeExecutionStatus(Enum):
    """Status of hedge execution"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REBALANCING = "rebalancing"

class HedgeExecutionType(Enum):
    """Type of hedge execution"""
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    CONDITIONAL = "conditional"
    SCHEDULED = "scheduled"

@dataclass
class HedgeExecution:
    """Hedge execution order"""
    execution_id: str
    hedge_id: str
    primary_symbol: str
    hedge_symbol: str
    hedge_ratio: float
    target_hedge_size: float
    current_hedge_size: float
    execution_type: HedgeExecutionType
    status: HedgeExecutionStatus
    created_time: float
    start_time: Optional[float]
    completion_time: Optional[float]
    execution_progress: float
    total_cost: float
    slippage: float
    effectiveness: float
    error_message: Optional[str]

@dataclass
class HedgeRebalanceOrder:
    """Hedge rebalancing order"""
    order_id: str
    hedge_id: str
    current_ratio: float
    target_ratio: float
    adjustment_size: float
    urgency: float
    reason: str
    timestamp: float

@dataclass
class HedgeMonitoringAlert:
    """Alert for hedge monitoring"""
    alert_id: str
    hedge_id: str
    alert_type: str
    severity: str
    message: str
    current_effectiveness: float
    target_effectiveness: float
    recommended_action: str
    timestamp: float

class DynamicHedgeExecutor:
    """
    Dynamic hedge execution system for THE OVERMIND PROTOCOL
    
    Features:
    - Automatic hedge execution
    - Real-time hedge monitoring
    - Dynamic rebalancing
    - Risk-based execution timing
    - Cost optimization
    - Effectiveness tracking
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Execution configuration
        self.max_execution_time = 300  # 5 minutes max execution time
        self.rebalance_threshold = 0.1  # 10% deviation triggers rebalance
        self.min_effectiveness_threshold = 0.6  # Minimum 60% effectiveness
        self.max_slippage_tolerance = 0.02  # 2% max slippage
        
        # Active executions tracking
        self.active_executions = {}
        self.execution_queue = []
        self.monitoring_alerts = []
        
        # Performance tracking
        self.execution_history = []
        self.success_rate = 0.0
        self.average_execution_time = 0.0
        self.average_cost = 0.0
        
        logger.info("🔄 Dynamic Hedge Executor initialized")
    
    async def start_hedge_execution_engine(self):
        """Start the hedge execution engine"""
        try:
            logger.info("🚀 Starting hedge execution engine")
            
            # Start execution tasks
            execution_task = asyncio.create_task(self.process_execution_queue())
            monitoring_task = asyncio.create_task(self.monitor_active_hedges())
            rebalancing_task = asyncio.create_task(self.check_hedge_rebalancing())
            
            # Wait for all tasks
            await asyncio.gather(execution_task, monitoring_task, rebalancing_task)
            
        except Exception as e:
            logger.error(f"❌ Error in hedge execution engine: {e}")
    
    async def execute_hedge_recommendation(self, hedge_recommendation: Dict[str, Any]) -> str:
        """Execute a hedge recommendation"""
        try:
            logger.info(f"🎯 Executing hedge recommendation for {hedge_recommendation.get('primary_symbol')}")
            
            # Create execution order
            execution = await self.create_hedge_execution(hedge_recommendation)
            
            # Add to execution queue
            self.execution_queue.append(execution)
            self.active_executions[execution.execution_id] = execution
            
            # Store in Redis
            await self.store_execution_order(execution)
            
            logger.info(f"📋 Created hedge execution order: {execution.execution_id}")
            return execution.execution_id
            
        except Exception as e:
            logger.error(f"❌ Error executing hedge recommendation: {e}")
            return ""
    
    async def create_hedge_execution(self, recommendation: Dict[str, Any]) -> HedgeExecution:
        """Create hedge execution order from recommendation"""
        try:
            execution_id = str(uuid.uuid4())
            hedge_id = f"hedge_{int(time.time())}"
            
            primary_symbol = recommendation.get('primary_symbol', '')
            hedge_symbol = recommendation.get('recommended_hedge_symbol', '')
            hedge_ratio = recommendation.get('hedge_ratio', 0.0)
            
            # Calculate target hedge size
            primary_position = await self.get_position_size(primary_symbol)
            target_hedge_size = abs(primary_position * hedge_ratio)
            
            # Determine execution type based on size and urgency
            urgency = recommendation.get('urgency', 0.5)
            if urgency > 0.8 or target_hedge_size < 50.0:
                execution_type = HedgeExecutionType.IMMEDIATE
            elif urgency > 0.5:
                execution_type = HedgeExecutionType.GRADUAL
            else:
                execution_type = HedgeExecutionType.CONDITIONAL
            
            return HedgeExecution(
                execution_id=execution_id,
                hedge_id=hedge_id,
                primary_symbol=primary_symbol,
                hedge_symbol=hedge_symbol,
                hedge_ratio=hedge_ratio,
                target_hedge_size=target_hedge_size,
                current_hedge_size=0.0,
                execution_type=execution_type,
                status=HedgeExecutionStatus.PENDING,
                created_time=time.time(),
                start_time=None,
                completion_time=None,
                execution_progress=0.0,
                total_cost=0.0,
                slippage=0.0,
                effectiveness=0.0,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating hedge execution: {e}")
            raise
    
    async def process_execution_queue(self):
        """Process hedge execution queue"""
        try:
            while True:
                if self.execution_queue:
                    execution = self.execution_queue.pop(0)
                    
                    if execution.status == HedgeExecutionStatus.PENDING:
                        await self.execute_hedge_order(execution)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
        except Exception as e:
            logger.error(f"❌ Error processing execution queue: {e}")
    
    async def execute_hedge_order(self, execution: HedgeExecution):
        """Execute a hedge order"""
        try:
            logger.info(f"⚡ Executing hedge order: {execution.execution_id}")
            
            # Update status
            execution.status = HedgeExecutionStatus.EXECUTING
            execution.start_time = time.time()
            
            # Execute based on type
            if execution.execution_type == HedgeExecutionType.IMMEDIATE:
                success = await self.execute_immediate_hedge(execution)
            elif execution.execution_type == HedgeExecutionType.GRADUAL:
                success = await self.execute_gradual_hedge(execution)
            elif execution.execution_type == HedgeExecutionType.CONDITIONAL:
                success = await self.execute_conditional_hedge(execution)
            else:
                success = await self.execute_scheduled_hedge(execution)
            
            # Update final status
            if success:
                execution.status = HedgeExecutionStatus.COMPLETED
                execution.completion_time = time.time()
                execution.execution_progress = 1.0
                
                # Calculate effectiveness
                execution.effectiveness = await self.calculate_hedge_effectiveness(execution)
                
                logger.info(f"✅ Hedge execution completed: {execution.execution_id}")
            else:
                execution.status = HedgeExecutionStatus.FAILED
                logger.error(f"❌ Hedge execution failed: {execution.execution_id}")
            
            # Update tracking
            await self.update_execution_tracking(execution)
            
        except Exception as e:
            execution.status = HedgeExecutionStatus.FAILED
            execution.error_message = str(e)
            logger.error(f"❌ Error executing hedge order: {e}")
    
    async def execute_immediate_hedge(self, execution: HedgeExecution) -> bool:
        """Execute hedge immediately"""
        try:
            logger.info(f"⚡ Immediate hedge execution for {execution.hedge_symbol}")
            
            # Send trading signal for hedge position
            trading_signal = {
                'signal_type': 'hedge_execution',
                'symbol': execution.hedge_symbol,
                'side': 'buy' if execution.hedge_ratio < 0 else 'sell',
                'quantity': execution.target_hedge_size,
                'hedge_id': execution.hedge_id,
                'execution_id': execution.execution_id,
                'urgency': 'high',
                'timestamp': time.time()
            }
            
            # Send to trading system
            success = await self.send_trading_signal(trading_signal)
            
            if success:
                execution.current_hedge_size = execution.target_hedge_size
                execution.execution_progress = 1.0
                
                # Estimate cost and slippage
                execution.total_cost = execution.target_hedge_size * 0.001  # 0.1% estimated cost
                execution.slippage = 0.005  # 0.5% estimated slippage
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error in immediate hedge execution: {e}")
            return False
    
    async def execute_gradual_hedge(self, execution: HedgeExecution) -> bool:
        """Execute hedge gradually to minimize market impact"""
        try:
            logger.info(f"📈 Gradual hedge execution for {execution.hedge_symbol}")
            
            # Split into smaller orders
            num_orders = min(5, max(2, int(execution.target_hedge_size / 20)))  # 2-5 orders
            order_size = execution.target_hedge_size / num_orders
            
            total_executed = 0.0
            total_cost = 0.0
            
            for i in range(num_orders):
                # Execute partial order
                partial_signal = {
                    'signal_type': 'hedge_execution_partial',
                    'symbol': execution.hedge_symbol,
                    'side': 'buy' if execution.hedge_ratio < 0 else 'sell',
                    'quantity': order_size,
                    'hedge_id': execution.hedge_id,
                    'execution_id': execution.execution_id,
                    'part': f"{i+1}/{num_orders}",
                    'timestamp': time.time()
                }
                
                success = await self.send_trading_signal(partial_signal)
                
                if success:
                    total_executed += order_size
                    total_cost += order_size * 0.0008  # Lower cost for gradual execution
                    
                    # Update progress
                    execution.current_hedge_size = total_executed
                    execution.execution_progress = total_executed / execution.target_hedge_size
                    
                    # Wait between orders to reduce impact
                    await asyncio.sleep(10)
                else:
                    logger.warning(f"⚠️ Partial hedge execution failed: part {i+1}")
                    break
            
            execution.total_cost = total_cost
            execution.slippage = 0.003  # Lower slippage for gradual execution
            
            return total_executed >= execution.target_hedge_size * 0.9  # 90% success threshold
            
        except Exception as e:
            logger.error(f"❌ Error in gradual hedge execution: {e}")
            return False
    
    async def execute_conditional_hedge(self, execution: HedgeExecution) -> bool:
        """Execute hedge based on market conditions"""
        try:
            logger.info(f"🎯 Conditional hedge execution for {execution.hedge_symbol}")
            
            # Check market conditions
            market_conditions = await self.check_market_conditions(execution.hedge_symbol)
            
            if not market_conditions.get('suitable_for_hedging', False):
                logger.info(f"⏳ Market conditions not suitable, delaying hedge execution")
                return False
            
            # Execute when conditions are favorable
            return await self.execute_immediate_hedge(execution)
            
        except Exception as e:
            logger.error(f"❌ Error in conditional hedge execution: {e}")
            return False
    
    async def execute_scheduled_hedge(self, execution: HedgeExecution) -> bool:
        """Execute hedge at scheduled time"""
        try:
            logger.info(f"⏰ Scheduled hedge execution for {execution.hedge_symbol}")
            
            # For now, treat as gradual execution
            return await self.execute_gradual_hedge(execution)
            
        except Exception as e:
            logger.error(f"❌ Error in scheduled hedge execution: {e}")
            return False

    async def monitor_active_hedges(self):
        """Monitor active hedge positions"""
        try:
            while True:
                for execution in self.active_executions.values():
                    if execution.status == HedgeExecutionStatus.COMPLETED:
                        await self.monitor_hedge_effectiveness(execution)

                await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"❌ Error monitoring active hedges: {e}")

    async def monitor_hedge_effectiveness(self, execution: HedgeExecution):
        """Monitor hedge effectiveness and generate alerts"""
        try:
            current_effectiveness = await self.calculate_current_hedge_effectiveness(execution)

            # Check if effectiveness has degraded
            if current_effectiveness < self.min_effectiveness_threshold:
                alert = HedgeMonitoringAlert(
                    alert_id=str(uuid.uuid4()),
                    hedge_id=execution.hedge_id,
                    alert_type="effectiveness_degraded",
                    severity="high",
                    message=f"Hedge effectiveness dropped to {current_effectiveness:.1%}",
                    current_effectiveness=current_effectiveness,
                    target_effectiveness=self.min_effectiveness_threshold,
                    recommended_action="rebalance_or_close",
                    timestamp=time.time()
                )

                self.monitoring_alerts.append(alert)
                await self.send_hedge_alert(alert)

            # Check if hedge ratio has drifted
            current_ratio = await self.calculate_current_hedge_ratio(execution)
            ratio_drift = abs(current_ratio - execution.hedge_ratio) / abs(execution.hedge_ratio)

            if ratio_drift > self.rebalance_threshold:
                await self.schedule_hedge_rebalance(execution, current_ratio)

        except Exception as e:
            logger.error(f"❌ Error monitoring hedge effectiveness: {e}")

    async def check_hedge_rebalancing(self):
        """Check for hedge rebalancing needs"""
        try:
            while True:
                rebalance_orders = await self.identify_rebalancing_needs()

                for order in rebalance_orders:
                    await self.execute_hedge_rebalance(order)

                await asyncio.sleep(300)  # Check every 5 minutes

        except Exception as e:
            logger.error(f"❌ Error checking hedge rebalancing: {e}")

    async def schedule_hedge_rebalance(self, execution: HedgeExecution, current_ratio: float):
        """Schedule hedge rebalancing"""
        try:
            rebalance_order = HedgeRebalanceOrder(
                order_id=str(uuid.uuid4()),
                hedge_id=execution.hedge_id,
                current_ratio=current_ratio,
                target_ratio=execution.hedge_ratio,
                adjustment_size=abs(current_ratio - execution.hedge_ratio) * execution.target_hedge_size,
                urgency=min(1.0, abs(current_ratio - execution.hedge_ratio) / abs(execution.hedge_ratio)),
                reason=f"Hedge ratio drift: {current_ratio:.2f} vs target {execution.hedge_ratio:.2f}",
                timestamp=time.time()
            )

            await self.execute_hedge_rebalance(rebalance_order)

        except Exception as e:
            logger.error(f"❌ Error scheduling hedge rebalance: {e}")

    async def execute_hedge_rebalance(self, rebalance_order: HedgeRebalanceOrder):
        """Execute hedge rebalancing"""
        try:
            logger.info(f"⚖️ Executing hedge rebalance: {rebalance_order.order_id}")

            # Find the execution to rebalance
            execution = None
            for exec_order in self.active_executions.values():
                if exec_order.hedge_id == rebalance_order.hedge_id:
                    execution = exec_order
                    break

            if not execution:
                logger.warning(f"⚠️ Hedge execution not found for rebalance: {rebalance_order.hedge_id}")
                return

            # Calculate adjustment needed
            if rebalance_order.current_ratio > rebalance_order.target_ratio:
                # Need to reduce hedge position
                action = 'reduce'
                adjustment_signal = {
                    'signal_type': 'hedge_rebalance',
                    'symbol': execution.hedge_symbol,
                    'side': 'sell' if execution.hedge_ratio < 0 else 'buy',
                    'quantity': rebalance_order.adjustment_size,
                    'hedge_id': execution.hedge_id,
                    'action': action,
                    'timestamp': time.time()
                }
            else:
                # Need to increase hedge position
                action = 'increase'
                adjustment_signal = {
                    'signal_type': 'hedge_rebalance',
                    'symbol': execution.hedge_symbol,
                    'side': 'buy' if execution.hedge_ratio < 0 else 'sell',
                    'quantity': rebalance_order.adjustment_size,
                    'hedge_id': execution.hedge_id,
                    'action': action,
                    'timestamp': time.time()
                }

            # Execute rebalance
            success = await self.send_trading_signal(adjustment_signal)

            if success:
                # Update execution tracking
                if action == 'increase':
                    execution.current_hedge_size += rebalance_order.adjustment_size
                else:
                    execution.current_hedge_size -= rebalance_order.adjustment_size

                logger.info(f"✅ Hedge rebalance completed: {rebalance_order.order_id}")
            else:
                logger.error(f"❌ Hedge rebalance failed: {rebalance_order.order_id}")

        except Exception as e:
            logger.error(f"❌ Error executing hedge rebalance: {e}")

    # Helper methods
    async def send_trading_signal(self, signal: Dict[str, Any]) -> bool:
        """Send trading signal to execution system"""
        try:
            # Send signal via Redis
            signal_key = "overmind:trading_signals"
            self.redis_client.lpush(signal_key, json.dumps(signal))

            logger.debug(f"📡 Sent trading signal: {signal.get('signal_type')}")
            return True

        except Exception as e:
            logger.error(f"❌ Error sending trading signal: {e}")
            return False

    async def get_position_size(self, symbol: str) -> float:
        """Get current position size for symbol"""
        try:
            position_key = f"overmind:position:{symbol}"
            position_str = self.redis_client.get(position_key)

            if position_str:
                position = json.loads(position_str)
                return position.get('quantity', 0.0)

            return 0.0

        except Exception as e:
            logger.error(f"❌ Error getting position size: {e}")
            return 0.0

    async def calculate_hedge_effectiveness(self, execution: HedgeExecution) -> float:
        """Calculate hedge effectiveness"""
        try:
            # Simplified effectiveness calculation
            # In practice, this would analyze actual price movements and hedge performance

            if execution.current_hedge_size >= execution.target_hedge_size * 0.9:
                base_effectiveness = 0.8
            else:
                base_effectiveness = 0.6

            # Adjust for slippage and cost
            cost_penalty = min(0.2, execution.total_cost / execution.target_hedge_size)
            slippage_penalty = min(0.1, execution.slippage)

            effectiveness = base_effectiveness - cost_penalty - slippage_penalty

            return max(0.0, min(1.0, effectiveness))

        except Exception as e:
            logger.error(f"❌ Error calculating hedge effectiveness: {e}")
            return 0.5

    async def calculate_current_hedge_effectiveness(self, execution: HedgeExecution) -> float:
        """Calculate current hedge effectiveness"""
        try:
            # This would analyze real-time performance
            # For now, return stored effectiveness with some variation
            base_effectiveness = execution.effectiveness

            # Add some time-based degradation
            time_since_execution = time.time() - (execution.completion_time or time.time())
            time_degradation = min(0.1, time_since_execution / (24 * 3600) * 0.05)  # 5% per day max

            current_effectiveness = base_effectiveness - time_degradation

            return max(0.0, min(1.0, current_effectiveness))

        except Exception as e:
            logger.error(f"❌ Error calculating current hedge effectiveness: {e}")
            return 0.5

    async def calculate_current_hedge_ratio(self, execution: HedgeExecution) -> float:
        """Calculate current hedge ratio"""
        try:
            # Get current position sizes
            primary_position = await self.get_position_size(execution.primary_symbol)
            hedge_position = await self.get_position_size(execution.hedge_symbol)

            if primary_position == 0:
                return 0.0

            current_ratio = hedge_position / primary_position

            # Adjust sign based on original hedge ratio
            if execution.hedge_ratio < 0:
                current_ratio = -current_ratio

            return current_ratio

        except Exception as e:
            logger.error(f"❌ Error calculating current hedge ratio: {e}")
            return execution.hedge_ratio

    async def check_market_conditions(self, symbol: str) -> Dict[str, Any]:
        """Check market conditions for hedge execution"""
        try:
            # Simplified market condition check
            # In practice, this would analyze volatility, liquidity, spread, etc.

            conditions = {
                'suitable_for_hedging': True,
                'volatility': 'normal',
                'liquidity': 'good',
                'spread': 'tight',
                'market_hours': True
            }

            return conditions

        except Exception as e:
            logger.error(f"❌ Error checking market conditions: {e}")
            return {'suitable_for_hedging': False}

    async def identify_rebalancing_needs(self) -> List[HedgeRebalanceOrder]:
        """Identify hedges that need rebalancing"""
        try:
            rebalance_orders = []

            for execution in self.active_executions.values():
                if execution.status == HedgeExecutionStatus.COMPLETED:
                    current_ratio = await self.calculate_current_hedge_ratio(execution)
                    ratio_drift = abs(current_ratio - execution.hedge_ratio) / abs(execution.hedge_ratio)

                    if ratio_drift > self.rebalance_threshold:
                        order = HedgeRebalanceOrder(
                            order_id=str(uuid.uuid4()),
                            hedge_id=execution.hedge_id,
                            current_ratio=current_ratio,
                            target_ratio=execution.hedge_ratio,
                            adjustment_size=abs(current_ratio - execution.hedge_ratio) * execution.target_hedge_size,
                            urgency=ratio_drift,
                            reason=f"Ratio drift: {ratio_drift:.1%}",
                            timestamp=time.time()
                        )
                        rebalance_orders.append(order)

            return rebalance_orders

        except Exception as e:
            logger.error(f"❌ Error identifying rebalancing needs: {e}")
            return []

    async def send_hedge_alert(self, alert: HedgeMonitoringAlert):
        """Send hedge monitoring alert"""
        try:
            alert_key = "overmind:hedge_alerts"
            self.redis_client.lpush(alert_key, json.dumps(asdict(alert)))

            logger.warning(f"🚨 Hedge alert: {alert.message}")

        except Exception as e:
            logger.error(f"❌ Error sending hedge alert: {e}")

    async def store_execution_order(self, execution: HedgeExecution):
        """Store execution order in Redis"""
        try:
            execution_key = f"overmind:hedge_execution:{execution.execution_id}"
            self.redis_client.setex(execution_key, 86400, json.dumps(asdict(execution)))  # 24 hour expiry

        except Exception as e:
            logger.error(f"❌ Error storing execution order: {e}")

    async def update_execution_tracking(self, execution: HedgeExecution):
        """Update execution tracking and statistics"""
        try:
            # Add to history
            self.execution_history.append(execution)

            # Update statistics
            completed_executions = [e for e in self.execution_history if e.status == HedgeExecutionStatus.COMPLETED]

            if completed_executions:
                self.success_rate = len(completed_executions) / len(self.execution_history)

                execution_times = [
                    (e.completion_time or 0) - (e.start_time or 0)
                    for e in completed_executions
                    if e.completion_time and e.start_time
                ]

                if execution_times:
                    self.average_execution_time = sum(execution_times) / len(execution_times)

                costs = [e.total_cost for e in completed_executions if e.total_cost > 0]
                if costs:
                    self.average_cost = sum(costs) / len(costs)

            # Store updated execution
            await self.store_execution_order(execution)

        except Exception as e:
            logger.error(f"❌ Error updating execution tracking: {e}")

    async def get_hedge_execution_status(self) -> Dict[str, Any]:
        """Get hedge execution system status"""
        try:
            return {
                'timestamp': time.time(),
                'active_executions': len(self.active_executions),
                'execution_queue_size': len(self.execution_queue),
                'monitoring_alerts': len(self.monitoring_alerts),
                'success_rate': self.success_rate,
                'average_execution_time': self.average_execution_time,
                'average_cost': self.average_cost,
                'configuration': {
                    'max_execution_time': self.max_execution_time,
                    'rebalance_threshold': self.rebalance_threshold,
                    'min_effectiveness_threshold': self.min_effectiveness_threshold,
                    'max_slippage_tolerance': self.max_slippage_tolerance
                }
            }

        except Exception as e:
            logger.error(f"❌ Error getting hedge execution status: {e}")
            return {'error': str(e)}

async def main():
    """Test the dynamic hedge executor"""
    executor = DynamicHedgeExecutor()

    # Test hedge execution
    sample_recommendation = {
        'primary_symbol': 'SOL',
        'recommended_hedge_symbol': 'USDC',
        'hedge_ratio': -0.5,
        'urgency': 0.7
    }

    execution_id = await executor.execute_hedge_recommendation(sample_recommendation)
    print(f"Created hedge execution: {execution_id}")

    status = await executor.get_hedge_execution_status()
    print(f"Executor status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
