#!/usr/bin/env python3
"""
Real-time Strategy Optimizer
Dynamic strategy optimization based on live performance feedback
"""

import asyncio
import logging
import json
import time
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import statistics
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class StrategyPerformanceMetrics:
    """Real-time strategy performance metrics"""
    strategy_name: str
    total_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    recent_performance: float  # Last 10 trades performance
    confidence_accuracy: float  # How accurate confidence predictions are
    timestamp: float

@dataclass
class OptimizationRecommendation:
    """Strategy optimization recommendation"""
    strategy_name: str
    parameter_name: str
    current_value: float
    recommended_value: float
    confidence: float
    reasoning: str
    expected_improvement: float
    timestamp: float

class RealtimeStrategyOptimizer:
    """
    Real-time strategy optimization based on live trading performance
    
    Features:
    - Continuous performance monitoring
    - Dynamic parameter adjustment
    - Adaptive strategy selection
    - Real-time feedback integration
    - Performance-based optimization
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Performance tracking
        self.strategy_metrics = {}
        self.optimization_history = []
        self.last_optimization = {}
        
        # Optimization parameters
        self.min_trades_for_optimization = 10
        self.optimization_interval = 3600  # 1 hour
        self.performance_window = 24 * 3600  # 24 hours
        
        # Strategy parameter ranges
        self.parameter_ranges = {
            "memecoin_hunter": {
                "confidence_threshold": (0.4, 0.8, 0.05),
                "volume_threshold": (1.2, 3.0, 0.2),
                "momentum_threshold": (0.1, 0.5, 0.05)
            },
            "high_vol_sniper": {
                "volatility_threshold": (0.15, 0.40, 0.05),
                "volume_spike_threshold": (2.0, 5.0, 0.5),
                "confidence_threshold": (0.5, 0.9, 0.05)
            },
            "governance_alpha_hunter": {
                "sentiment_threshold": (0.7, 0.95, 0.05),
                "proposal_impact_threshold": (0.6, 0.9, 0.05),
                "timing_window": (12, 72, 6)  # hours
            }
        }
        
        logger.info("🔧 Real-time Strategy Optimizer initialized")
    
    async def monitor_strategy_performance(self):
        """Continuously monitor strategy performance"""
        while True:
            try:
                # Get recent execution results
                execution_results = self.redis_client.lrange('overmind:execution_results', 0, 99)
                
                # Analyze performance by strategy
                for result_str in execution_results:
                    result = json.loads(result_str)
                    strategy = result.get('strategy', 'unknown')
                    
                    if strategy != 'unknown':
                        await self.update_strategy_metrics(strategy, result)
                
                # Check if optimization is needed
                await self.check_optimization_triggers()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"❌ Error in performance monitoring: {e}")
                await asyncio.sleep(60)
    
    async def update_strategy_metrics(self, strategy: str, execution_result: Dict[str, Any]):
        """Update performance metrics for a strategy"""
        try:
            if strategy not in self.strategy_metrics:
                self.strategy_metrics[strategy] = {
                    'trades': [],
                    'total_profit': 0.0,
                    'total_trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'confidence_predictions': [],
                    'actual_outcomes': []
                }
            
            metrics = self.strategy_metrics[strategy]
            
            # Extract trade data
            profit = execution_result.get('estimated_profit', 0.0)
            confidence = execution_result.get('confidence', 0.5)
            timestamp = execution_result.get('timestamp', time.time())
            
            # Update metrics
            metrics['trades'].append({
                'profit': profit,
                'confidence': confidence,
                'timestamp': timestamp
            })
            
            metrics['total_profit'] += profit
            metrics['total_trades'] += 1
            
            if profit > 0:
                metrics['wins'] += 1
            else:
                metrics['losses'] += 1
            
            # Track confidence accuracy
            metrics['confidence_predictions'].append(confidence)
            metrics['actual_outcomes'].append(1 if profit > 0 else 0)
            
            # Keep only recent trades (last 24 hours)
            cutoff_time = time.time() - self.performance_window
            metrics['trades'] = [
                trade for trade in metrics['trades'] 
                if trade['timestamp'] > cutoff_time
            ]
            
            logger.debug(f"📊 Updated metrics for {strategy}: {metrics['total_trades']} trades, ${metrics['total_profit']:.6f} profit")
            
        except Exception as e:
            logger.error(f"❌ Error updating strategy metrics: {e}")
    
    async def check_optimization_triggers(self):
        """Check if any strategy needs optimization"""
        try:
            current_time = time.time()
            
            for strategy, metrics in self.strategy_metrics.items():
                # Check if enough trades and time passed
                if (len(metrics['trades']) >= self.min_trades_for_optimization and
                    current_time - self.last_optimization.get(strategy, 0) > self.optimization_interval):
                    
                    # Calculate current performance
                    performance_metrics = self.calculate_strategy_performance(strategy, metrics)
                    
                    # Check if optimization is needed
                    if self.should_optimize_strategy(strategy, performance_metrics):
                        await self.optimize_strategy_parameters(strategy, performance_metrics)
                        self.last_optimization[strategy] = current_time
            
        except Exception as e:
            logger.error(f"❌ Error checking optimization triggers: {e}")
    
    def calculate_strategy_performance(self, strategy: str, metrics: Dict[str, Any]) -> StrategyPerformanceMetrics:
        """Calculate comprehensive performance metrics for a strategy"""
        try:
            trades = metrics['trades']
            
            if not trades:
                return StrategyPerformanceMetrics(
                    strategy_name=strategy,
                    total_trades=0,
                    win_rate=0.0,
                    avg_profit=0.0,
                    avg_loss=0.0,
                    profit_factor=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    recent_performance=0.0,
                    confidence_accuracy=0.0,
                    timestamp=time.time()
                )
            
            # Basic metrics
            profits = [trade['profit'] for trade in trades]
            wins = [p for p in profits if p > 0]
            losses = [p for p in profits if p <= 0]
            
            total_trades = len(trades)
            win_rate = len(wins) / total_trades if total_trades > 0 else 0
            avg_profit = statistics.mean(wins) if wins else 0
            avg_loss = statistics.mean(losses) if losses else 0
            
            # Profit factor
            total_wins = sum(wins) if wins else 0
            total_losses = abs(sum(losses)) if losses else 0
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Sharpe ratio (simplified)
            if len(profits) > 1:
                sharpe_ratio = statistics.mean(profits) / statistics.stdev(profits) if statistics.stdev(profits) > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Max drawdown (simplified)
            cumulative = 0
            peak = 0
            max_drawdown = 0
            for profit in profits:
                cumulative += profit
                if cumulative > peak:
                    peak = cumulative
                drawdown = (peak - cumulative) / peak if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            # Recent performance (last 10 trades)
            recent_trades = trades[-10:] if len(trades) >= 10 else trades
            recent_performance = sum(trade['profit'] for trade in recent_trades) / len(recent_trades)
            
            # Confidence accuracy
            if metrics['confidence_predictions'] and metrics['actual_outcomes']:
                # Calculate correlation between confidence and actual outcomes
                confidences = metrics['confidence_predictions'][-len(trades):]
                outcomes = metrics['actual_outcomes'][-len(trades):]
                
                if len(confidences) == len(outcomes) and len(confidences) > 1:
                    confidence_accuracy = np.corrcoef(confidences, outcomes)[0, 1]
                    confidence_accuracy = max(0, confidence_accuracy)  # Ensure non-negative
                else:
                    confidence_accuracy = 0.5
            else:
                confidence_accuracy = 0.5
            
            return StrategyPerformanceMetrics(
                strategy_name=strategy,
                total_trades=total_trades,
                win_rate=win_rate,
                avg_profit=avg_profit,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                recent_performance=recent_performance,
                confidence_accuracy=confidence_accuracy,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating strategy performance: {e}")
            return StrategyPerformanceMetrics(
                strategy_name=strategy,
                total_trades=0,
                win_rate=0.0,
                avg_profit=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                recent_performance=0.0,
                confidence_accuracy=0.0,
                timestamp=time.time()
            )
    
    def should_optimize_strategy(self, strategy: str, performance: StrategyPerformanceMetrics) -> bool:
        """Determine if a strategy needs optimization"""
        try:
            # Optimization triggers
            triggers = []
            
            # Poor recent performance
            if performance.recent_performance < -0.01:  # Losing money recently
                triggers.append("poor_recent_performance")
            
            # Low win rate
            if performance.win_rate < 0.4:
                triggers.append("low_win_rate")
            
            # High drawdown
            if performance.max_drawdown > 0.15:
                triggers.append("high_drawdown")
            
            # Poor confidence accuracy
            if performance.confidence_accuracy < 0.3:
                triggers.append("poor_confidence_accuracy")
            
            # Low profit factor
            if performance.profit_factor < 1.2:
                triggers.append("low_profit_factor")
            
            should_optimize = len(triggers) >= 2  # Need at least 2 triggers
            
            if should_optimize:
                logger.info(f"🔧 Strategy {strategy} needs optimization. Triggers: {', '.join(triggers)}")
            
            return should_optimize
            
        except Exception as e:
            logger.error(f"❌ Error checking optimization need: {e}")
            return False

    async def optimize_strategy_parameters(self, strategy: str, performance: StrategyPerformanceMetrics):
        """Optimize parameters for a specific strategy"""
        try:
            logger.info(f"🔧 Starting optimization for {strategy}")

            if strategy not in self.parameter_ranges:
                logger.warning(f"⚠️ No parameter ranges defined for {strategy}")
                return

            recommendations = []

            # Analyze each parameter
            for param_name, (min_val, max_val, step) in self.parameter_ranges[strategy].items():
                recommendation = await self.optimize_single_parameter(
                    strategy, param_name, min_val, max_val, step, performance
                )

                if recommendation:
                    recommendations.append(recommendation)

            # Apply best recommendations
            if recommendations:
                await self.apply_optimization_recommendations(strategy, recommendations)

        except Exception as e:
            logger.error(f"❌ Error optimizing strategy parameters: {e}")

    async def optimize_single_parameter(self, strategy: str, param_name: str,
                                      min_val: float, max_val: float, step: float,
                                      performance: StrategyPerformanceMetrics) -> Optional[OptimizationRecommendation]:
        """Optimize a single parameter based on performance analysis"""
        try:
            current_value = await self.get_current_parameter_value(strategy, param_name)

            # Determine optimization direction based on performance issues
            if performance.win_rate < 0.4:
                # Low win rate - try to be more selective
                if param_name.endswith('_threshold'):
                    recommended_value = min(max_val, current_value + step)
                    reasoning = "Increasing threshold to be more selective due to low win rate"
                else:
                    recommended_value = current_value
                    reasoning = "No clear optimization direction for this parameter"

            elif performance.recent_performance < -0.01:
                # Recent losses - adjust based on parameter type
                if param_name == 'confidence_threshold':
                    recommended_value = min(max_val, current_value + step)
                    reasoning = "Increasing confidence threshold due to recent losses"
                elif param_name == 'volume_threshold':
                    recommended_value = min(max_val, current_value + step)
                    reasoning = "Increasing volume threshold to avoid low-volume trades"
                else:
                    recommended_value = current_value
                    reasoning = "Maintaining current value pending more data"

            elif performance.confidence_accuracy < 0.3:
                # Poor confidence calibration
                if param_name == 'confidence_threshold':
                    recommended_value = max(min_val, current_value - step)
                    reasoning = "Lowering confidence threshold due to poor calibration"
                else:
                    recommended_value = current_value
                    reasoning = "No adjustment needed for this parameter"

            else:
                # Performance is acceptable, minor adjustments
                recommended_value = current_value
                reasoning = "Performance acceptable, no changes needed"

            # Only recommend if there's a meaningful change
            if abs(recommended_value - current_value) >= step:
                confidence = self.calculate_optimization_confidence(performance, param_name)
                expected_improvement = self.estimate_improvement(performance, param_name, current_value, recommended_value)

                return OptimizationRecommendation(
                    strategy_name=strategy,
                    parameter_name=param_name,
                    current_value=current_value,
                    recommended_value=recommended_value,
                    confidence=confidence,
                    reasoning=reasoning,
                    expected_improvement=expected_improvement,
                    timestamp=time.time()
                )

            return None

        except Exception as e:
            logger.error(f"❌ Error optimizing parameter {param_name}: {e}")
            return None

    async def get_current_parameter_value(self, strategy: str, param_name: str) -> float:
        """Get current parameter value from strategy configuration"""
        try:
            # Try to get from Redis configuration
            config_key = f"overmind:strategy_config:{strategy}"
            config_str = self.redis_client.get(config_key)

            if config_str:
                config = json.loads(config_str)
                return config.get(param_name, self.get_default_parameter_value(strategy, param_name))

            return self.get_default_parameter_value(strategy, param_name)

        except Exception as e:
            logger.error(f"❌ Error getting parameter value: {e}")
            return self.get_default_parameter_value(strategy, param_name)

    def get_default_parameter_value(self, strategy: str, param_name: str) -> float:
        """Get default parameter value"""
        defaults = {
            "memecoin_hunter": {
                "confidence_threshold": 0.6,
                "volume_threshold": 2.0,
                "momentum_threshold": 0.2
            },
            "high_vol_sniper": {
                "volatility_threshold": 0.25,
                "volume_spike_threshold": 3.0,
                "confidence_threshold": 0.7
            },
            "governance_alpha_hunter": {
                "sentiment_threshold": 0.8,
                "proposal_impact_threshold": 0.75,
                "timing_window": 24
            }
        }

        return defaults.get(strategy, {}).get(param_name, 0.5)

    def calculate_optimization_confidence(self, performance: StrategyPerformanceMetrics, param_name: str) -> float:
        """Calculate confidence in optimization recommendation"""
        try:
            # Base confidence on amount of data and performance clarity
            data_confidence = min(1.0, performance.total_trades / 50.0)  # More trades = higher confidence

            # Performance clarity - how clear the performance issues are
            performance_issues = 0
            if performance.win_rate < 0.4:
                performance_issues += 1
            if performance.recent_performance < -0.01:
                performance_issues += 1
            if performance.confidence_accuracy < 0.3:
                performance_issues += 1
            if performance.max_drawdown > 0.15:
                performance_issues += 1

            clarity_confidence = performance_issues / 4.0  # More issues = clearer need for optimization

            # Combine confidences
            total_confidence = (data_confidence + clarity_confidence) / 2.0

            return max(0.1, min(0.9, total_confidence))

        except Exception as e:
            logger.error(f"❌ Error calculating optimization confidence: {e}")
            return 0.5

    def estimate_improvement(self, performance: StrategyPerformanceMetrics,
                           param_name: str, current_value: float, new_value: float) -> float:
        """Estimate expected improvement from parameter change"""
        try:
            # Simple heuristic-based improvement estimation
            change_magnitude = abs(new_value - current_value) / current_value if current_value > 0 else 0.1

            # Base improvement on current performance issues
            if performance.win_rate < 0.3:
                base_improvement = 0.15  # Expect significant improvement
            elif performance.win_rate < 0.4:
                base_improvement = 0.10
            elif performance.recent_performance < -0.02:
                base_improvement = 0.08
            else:
                base_improvement = 0.05

            # Scale by change magnitude
            estimated_improvement = base_improvement * min(1.0, change_magnitude * 2)

            return estimated_improvement

        except Exception as e:
            logger.error(f"❌ Error estimating improvement: {e}")
            return 0.05

    async def apply_optimization_recommendations(self, strategy: str, recommendations: List[OptimizationRecommendation]):
        """Apply optimization recommendations to strategy configuration"""
        try:
            # Sort by confidence and expected improvement
            recommendations.sort(key=lambda r: r.confidence * r.expected_improvement, reverse=True)

            # Apply top recommendations
            applied_changes = {}

            for rec in recommendations[:3]:  # Apply top 3 recommendations
                if rec.confidence > 0.6:  # Only apply high-confidence recommendations
                    applied_changes[rec.parameter_name] = rec.recommended_value

                    logger.info(f"🔧 Optimizing {strategy}.{rec.parameter_name}: {rec.current_value:.3f} → {rec.recommended_value:.3f}")
                    logger.info(f"   Reasoning: {rec.reasoning}")
                    logger.info(f"   Confidence: {rec.confidence:.2f}, Expected improvement: {rec.expected_improvement:.1%}")

            if applied_changes:
                # Update strategy configuration
                await self.update_strategy_configuration(strategy, applied_changes)

                # Store optimization history
                optimization_record = {
                    'strategy': strategy,
                    'timestamp': time.time(),
                    'changes': applied_changes,
                    'recommendations': [asdict(rec) for rec in recommendations],
                    'performance_before': asdict(self.calculate_strategy_performance(
                        strategy, self.strategy_metrics[strategy]
                    ))
                }

                self.optimization_history.append(optimization_record)

                # Store in Redis
                self.redis_client.lpush('overmind:optimization_history', json.dumps(optimization_record))
                self.redis_client.ltrim('overmind:optimization_history', 0, 99)

                logger.info(f"✅ Applied {len(applied_changes)} optimizations to {strategy}")
            else:
                logger.info(f"⚠️ No high-confidence optimizations found for {strategy}")

        except Exception as e:
            logger.error(f"❌ Error applying optimization recommendations: {e}")

    async def update_strategy_configuration(self, strategy: str, changes: Dict[str, float]):
        """Update strategy configuration with optimized parameters"""
        try:
            config_key = f"overmind:strategy_config:{strategy}"

            # Get current configuration
            current_config_str = self.redis_client.get(config_key)
            if current_config_str:
                current_config = json.loads(current_config_str)
            else:
                current_config = {}

            # Apply changes
            current_config.update(changes)

            # Store updated configuration
            self.redis_client.setex(config_key, 86400, json.dumps(current_config))  # 24 hour expiry

            # Notify system of configuration change
            notification = {
                'type': 'strategy_optimization',
                'strategy': strategy,
                'changes': changes,
                'timestamp': time.time()
            }

            self.redis_client.lpush('overmind:system_notifications', json.dumps(notification))

            logger.info(f"📝 Updated configuration for {strategy}")

        except Exception as e:
            logger.error(f"❌ Error updating strategy configuration: {e}")

    async def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status and metrics"""
        try:
            status = {
                'timestamp': time.time(),
                'strategies_monitored': len(self.strategy_metrics),
                'total_optimizations': len(self.optimization_history),
                'strategy_performance': {},
                'recent_optimizations': []
            }

            # Add strategy performance
            for strategy, metrics in self.strategy_metrics.items():
                performance = self.calculate_strategy_performance(strategy, metrics)
                status['strategy_performance'][strategy] = asdict(performance)

            # Add recent optimizations
            recent_optimizations = sorted(
                self.optimization_history,
                key=lambda x: x['timestamp'],
                reverse=True
            )[:5]

            status['recent_optimizations'] = recent_optimizations

            return status

        except Exception as e:
            logger.error(f"❌ Error getting optimization status: {e}")
            return {'error': str(e)}

async def main():
    """Test the real-time optimizer"""
    optimizer = RealtimeStrategyOptimizer()

    # Start monitoring
    await optimizer.monitor_strategy_performance()

if __name__ == "__main__":
    asyncio.run(main())
