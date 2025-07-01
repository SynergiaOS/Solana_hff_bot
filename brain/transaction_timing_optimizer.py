#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Transaction Timing Optimizer
Intelligent transaction timing with Jito bundle optimization
"""

import asyncio
import json
import redis
import time
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from mev_risk_analyzer import create_mev_risk_analyzer, MEVRiskLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TransactionTimingOptimizer')

class TimingStrategy(Enum):
    """Transaction timing strategies"""
    IMMEDIATE = "immediate"      # Execute immediately
    DELAYED = "delayed"          # Wait for better conditions
    BUNDLED = "bundled"          # Use Jito bundle
    ADAPTIVE = "adaptive"        # Adapt based on conditions

@dataclass
class TimingRecommendation:
    """Transaction timing recommendation"""
    strategy: TimingStrategy
    delay_seconds: int
    use_jito_bundle: bool
    priority_fee_multiplier: float
    optimal_execution_time: float
    confidence: float
    reasoning: str
    timestamp: float

@dataclass
class MarketConditions:
    """Current market conditions for timing"""
    network_congestion: float
    gas_price_trend: str
    trading_volume: float
    volatility: float
    time_of_day_factor: float
    timestamp: float

class TransactionTimingOptimizer:
    """
    Intelligent Transaction Timing Optimizer
    
    Analyzes market conditions and MEV risk to determine optimal
    transaction timing and execution strategy
    """
    
    def __init__(self):
        """Initialize Transaction Timing Optimizer"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.mev_analyzer = create_mev_risk_analyzer()
        
        # Timing optimization parameters
        self.timing_windows = {
            'peak_hours': (14, 21),      # 9 AM - 4 PM EST (high activity)
            'off_hours': (2, 8),         # 9 PM - 3 AM EST (low activity)
            'transition': (8, 14)        # 3 AM - 9 AM EST (moderate)
        }
        
        # Optimal timing thresholds
        self.timing_thresholds = {
            'low_congestion': 0.3,       # < 30% congestion
            'high_volatility': 0.05,     # > 5% volatility
            'high_volume': 1000000,      # > 1M SOL volume
            'gas_spike': 2.0             # > 2x normal gas price
        }
        
        # Jito bundle configuration
        self.jito_config = {
            'bundle_size_limit': 5,      # Max transactions per bundle
            'tip_multiplier': 1.5,       # Tip multiplier for bundle inclusion
            'max_bundle_wait': 30        # Max seconds to wait for bundle
        }
        
        # Historical timing data
        self.timing_history = []
        self.execution_results = []
        
        logger.info("⏰ Transaction Timing Optimizer initialized")
        logger.info("🎯 Intelligent execution timing enabled")
        logger.info("📦 Jito bundle optimization ready")
    
    async def optimize_transaction_timing(self, 
                                        token_address: str,
                                        transaction_amount: float,
                                        urgency_level: str = "normal") -> TimingRecommendation:
        """
        Optimize transaction timing based on current conditions
        """
        try:
            logger.info(f"⏰ Optimizing timing for {token_address} ({transaction_amount} SOL)")
            
            # Assess current MEV risk
            mev_assessment = await self.mev_analyzer.assess_mev_risk(
                token_address, transaction_amount
            )
            
            # Analyze market conditions
            market_conditions = await self.analyze_market_conditions()
            
            # Determine optimal timing strategy
            timing_strategy = self.determine_timing_strategy(
                mev_assessment, market_conditions, urgency_level
            )
            
            # Calculate optimal execution parameters
            execution_params = self.calculate_execution_parameters(
                timing_strategy, mev_assessment, market_conditions
            )
            
            # Create timing recommendation
            recommendation = TimingRecommendation(
                strategy=timing_strategy,
                delay_seconds=execution_params['delay'],
                use_jito_bundle=execution_params['use_jito'],
                priority_fee_multiplier=execution_params['priority_multiplier'],
                optimal_execution_time=time.time() + execution_params['delay'],
                confidence=execution_params['confidence'],
                reasoning=self.generate_timing_reasoning(
                    timing_strategy, mev_assessment, market_conditions
                ),
                timestamp=time.time()
            )
            
            # Store recommendation
            await self.store_timing_recommendation(recommendation)
            
            logger.info(f"⏰ Timing Strategy: {timing_strategy.value}")
            logger.info(f"   Delay: {execution_params['delay']} seconds")
            logger.info(f"   Jito Bundle: {execution_params['use_jito']}")
            logger.info(f"   Priority Multiplier: {execution_params['priority_multiplier']:.1f}x")
            
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Error optimizing transaction timing: {e}")
            return self.create_fallback_recommendation()
    
    async def analyze_market_conditions(self) -> MarketConditions:
        """Analyze current market conditions for timing optimization"""
        try:
            # Network congestion analysis
            network_congestion = await self.assess_network_congestion()
            
            # Gas price trend analysis
            gas_trend = await self.analyze_gas_price_trend()
            
            # Trading volume analysis
            trading_volume = await self.assess_trading_volume()
            
            # Volatility analysis
            volatility = await self.assess_market_volatility()
            
            # Time of day factor
            time_factor = self.calculate_time_of_day_factor()
            
            conditions = MarketConditions(
                network_congestion=network_congestion,
                gas_price_trend=gas_trend,
                trading_volume=trading_volume,
                volatility=volatility,
                time_of_day_factor=time_factor,
                timestamp=time.time()
            )
            
            logger.info(f"📊 Market conditions: congestion={network_congestion:.1%}, "
                       f"volume={trading_volume:.0f}, volatility={volatility:.1%}")
            
            return conditions
            
        except Exception as e:
            logger.error(f"❌ Error analyzing market conditions: {e}")
            return self.create_fallback_conditions()
    
    async def assess_network_congestion(self) -> float:
        """Assess current network congestion"""
        try:
            # Simulate network congestion assessment
            # In production, this would query Solana RPC for real data
            
            base_congestion = 0.2
            time_factor = self.calculate_time_of_day_factor()
            random_factor = np.random.uniform(-0.1, 0.3)
            
            congestion = base_congestion + (time_factor * 0.3) + random_factor
            return max(0.0, min(1.0, congestion))
            
        except Exception as e:
            logger.error(f"❌ Error assessing network congestion: {e}")
            return 0.3
    
    async def analyze_gas_price_trend(self) -> str:
        """Analyze gas price trend"""
        try:
            # Simulate gas price trend analysis
            # In production, this would analyze recent gas price history
            
            trends = ["rising", "falling", "stable"]
            weights = [0.3, 0.3, 0.4]  # Slightly favor stable
            
            return np.random.choice(trends, p=weights)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing gas price trend: {e}")
            return "stable"
    
    async def assess_trading_volume(self) -> float:
        """Assess current trading volume"""
        try:
            # Simulate trading volume assessment
            base_volume = 500000  # 500K SOL
            time_factor = self.calculate_time_of_day_factor()
            volatility_factor = np.random.uniform(0.5, 2.0)
            
            volume = base_volume * (1 + time_factor) * volatility_factor
            return max(0.0, volume)
            
        except Exception as e:
            logger.error(f"❌ Error assessing trading volume: {e}")
            return 500000.0
    
    async def assess_market_volatility(self) -> float:
        """Assess current market volatility"""
        try:
            # Simulate volatility assessment
            base_volatility = 0.02  # 2%
            time_factor = self.calculate_time_of_day_factor()
            random_factor = np.random.uniform(0.5, 2.0)
            
            volatility = base_volatility * (1 + time_factor * 0.5) * random_factor
            return max(0.0, min(0.2, volatility))
            
        except Exception as e:
            logger.error(f"❌ Error assessing market volatility: {e}")
            return 0.03
    
    def calculate_time_of_day_factor(self) -> float:
        """Calculate time of day factor for market activity"""
        try:
            current_hour = datetime.now().hour
            
            # Peak trading hours (US market open)
            if self.timing_windows['peak_hours'][0] <= current_hour <= self.timing_windows['peak_hours'][1]:
                return 1.0  # High activity
            # Off hours (late night/early morning)
            elif self.timing_windows['off_hours'][0] <= current_hour <= self.timing_windows['off_hours'][1]:
                return 0.3  # Low activity
            # Transition hours
            else:
                return 0.6  # Moderate activity
                
        except Exception as e:
            logger.error(f"❌ Error calculating time factor: {e}")
            return 0.5
    
    def determine_timing_strategy(self, mev_assessment, market_conditions, urgency: str) -> TimingStrategy:
        """Determine optimal timing strategy"""
        try:
            # High urgency - execute immediately regardless of conditions
            if urgency == "high":
                return TimingStrategy.IMMEDIATE
            
            # Extreme MEV risk - always delay
            if mev_assessment.risk_level == MEVRiskLevel.EXTREME:
                return TimingStrategy.DELAYED
            
            # High MEV risk - use bundle
            if mev_assessment.risk_level == MEVRiskLevel.HIGH:
                return TimingStrategy.BUNDLED
            
            # High congestion - delay or bundle
            if market_conditions.network_congestion > 0.7:
                return TimingStrategy.BUNDLED if mev_assessment.risk_score > 0.3 else TimingStrategy.DELAYED
            
            # High volatility - be adaptive
            if market_conditions.volatility > self.timing_thresholds['high_volatility']:
                return TimingStrategy.ADAPTIVE
            
            # Good conditions - execute immediately
            if (market_conditions.network_congestion < 0.3 and 
                mev_assessment.risk_level in [MEVRiskLevel.MINIMAL, MEVRiskLevel.LOW]):
                return TimingStrategy.IMMEDIATE
            
            # Default to adaptive
            return TimingStrategy.ADAPTIVE
            
        except Exception as e:
            logger.error(f"❌ Error determining timing strategy: {e}")
            return TimingStrategy.ADAPTIVE
    
    def calculate_execution_parameters(self, strategy: TimingStrategy, 
                                     mev_assessment, market_conditions) -> Dict[str, Any]:
        """Calculate execution parameters based on strategy"""
        try:
            params = {
                'delay': 0,
                'use_jito': False,
                'priority_multiplier': 1.0,
                'confidence': 0.8
            }
            
            if strategy == TimingStrategy.IMMEDIATE:
                params.update({
                    'delay': 0,
                    'use_jito': mev_assessment.risk_level != MEVRiskLevel.MINIMAL,
                    'priority_multiplier': 1.0 + market_conditions.network_congestion,
                    'confidence': 0.9
                })
            
            elif strategy == TimingStrategy.DELAYED:
                delay = self.calculate_optimal_delay(market_conditions)
                params.update({
                    'delay': delay,
                    'use_jito': True,
                    'priority_multiplier': 1.5,
                    'confidence': 0.7
                })
            
            elif strategy == TimingStrategy.BUNDLED:
                params.update({
                    'delay': 5,  # Small delay to prepare bundle
                    'use_jito': True,
                    'priority_multiplier': 2.0,
                    'confidence': 0.8
                })
            
            elif strategy == TimingStrategy.ADAPTIVE:
                # Adapt based on conditions
                if market_conditions.network_congestion > 0.5:
                    params['delay'] = 10
                    params['use_jito'] = True
                    params['priority_multiplier'] = 1.8
                else:
                    params['delay'] = 2
                    params['use_jito'] = mev_assessment.risk_score > 0.4
                    params['priority_multiplier'] = 1.2
                params['confidence'] = 0.75
            
            return params
            
        except Exception as e:
            logger.error(f"❌ Error calculating execution parameters: {e}")
            return {'delay': 10, 'use_jito': True, 'priority_multiplier': 1.5, 'confidence': 0.5}
    
    def calculate_optimal_delay(self, market_conditions: MarketConditions) -> int:
        """Calculate optimal delay based on market conditions"""
        try:
            base_delay = 30  # 30 seconds base
            
            # Reduce delay if conditions are improving
            if market_conditions.gas_price_trend == "falling":
                base_delay *= 0.7
            elif market_conditions.gas_price_trend == "rising":
                base_delay *= 1.3
            
            # Adjust for congestion
            congestion_factor = 1 + market_conditions.network_congestion
            base_delay *= congestion_factor
            
            # Adjust for time of day
            if market_conditions.time_of_day_factor < 0.5:  # Off hours
                base_delay *= 0.5  # Shorter delay during off hours
            
            return max(5, min(300, int(base_delay)))  # 5 seconds to 5 minutes
            
        except Exception as e:
            logger.error(f"❌ Error calculating optimal delay: {e}")
            return 30
    
    def generate_timing_reasoning(self, strategy: TimingStrategy, 
                                mev_assessment, market_conditions) -> str:
        """Generate human-readable timing reasoning"""
        try:
            reasoning = f"Timing strategy: {strategy.value}. "
            
            if strategy == TimingStrategy.IMMEDIATE:
                reasoning += "Conditions favorable for immediate execution. "
            elif strategy == TimingStrategy.DELAYED:
                reasoning += f"Delaying execution due to {mev_assessment.risk_level.value} MEV risk. "
            elif strategy == TimingStrategy.BUNDLED:
                reasoning += "Using Jito bundle for MEV protection. "
            elif strategy == TimingStrategy.ADAPTIVE:
                reasoning += "Adapting timing based on current market conditions. "
            
            if market_conditions.network_congestion > 0.6:
                reasoning += "High network congestion detected. "
            
            if market_conditions.volatility > 0.05:
                reasoning += "High market volatility observed. "
            
            if market_conditions.gas_price_trend == "rising":
                reasoning += "Gas prices trending upward. "
            
            return reasoning
            
        except Exception as e:
            logger.error(f"❌ Error generating timing reasoning: {e}")
            return "Timing optimization completed with standard parameters."
    
    async def store_timing_recommendation(self, recommendation: TimingRecommendation):
        """Store timing recommendation in Redis"""
        try:
            recommendation_data = {
                "strategy": recommendation.strategy.value,
                "delay_seconds": recommendation.delay_seconds,
                "use_jito_bundle": recommendation.use_jito_bundle,
                "priority_fee_multiplier": recommendation.priority_fee_multiplier,
                "optimal_execution_time": recommendation.optimal_execution_time,
                "confidence": recommendation.confidence,
                "reasoning": recommendation.reasoning,
                "timestamp": recommendation.timestamp
            }
            
            # Store current recommendation
            self.redis_client.setex("overmind:timing_recommendation", 300, json.dumps(recommendation_data))
            
            # Add to history
            self.redis_client.lpush("overmind:timing_history", json.dumps(recommendation_data))
            self.redis_client.ltrim("overmind:timing_history", 0, 99)  # Keep last 100
            
            logger.info(f"⏰ Timing recommendation stored: {recommendation.strategy.value}")
            
        except Exception as e:
            logger.error(f"❌ Error storing timing recommendation: {e}")
    
    async def execute_with_optimal_timing(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transaction with optimal timing"""
        try:
            # Get timing recommendation
            recommendation = await self.optimize_transaction_timing(
                transaction_data.get('token_address', 'unknown'),
                transaction_data.get('amount', 0.0),
                transaction_data.get('urgency', 'normal')
            )
            
            # Apply timing strategy
            if recommendation.delay_seconds > 0:
                logger.info(f"⏰ Delaying execution for {recommendation.delay_seconds} seconds...")
                await asyncio.sleep(recommendation.delay_seconds)
            
            # Prepare execution parameters
            execution_params = {
                'use_jito_bundle': recommendation.use_jito_bundle,
                'priority_fee_multiplier': recommendation.priority_fee_multiplier,
                'timing_strategy': recommendation.strategy.value,
                'execution_time': time.time()
            }
            
            # Merge with original transaction data
            optimized_transaction = {**transaction_data, **execution_params}
            
            logger.info(f"🚀 Executing with optimized timing: {recommendation.strategy.value}")
            return optimized_transaction
            
        except Exception as e:
            logger.error(f"❌ Error executing with optimal timing: {e}")
            return transaction_data
    
    def create_fallback_recommendation(self) -> TimingRecommendation:
        """Create fallback recommendation when optimization fails"""
        return TimingRecommendation(
            strategy=TimingStrategy.ADAPTIVE,
            delay_seconds=10,
            use_jito_bundle=True,
            priority_fee_multiplier=1.5,
            optimal_execution_time=time.time() + 10,
            confidence=0.5,
            reasoning="Fallback timing recommendation due to optimization error",
            timestamp=time.time()
        )
    
    def create_fallback_conditions(self) -> MarketConditions:
        """Create fallback market conditions when analysis fails"""
        return MarketConditions(
            network_congestion=0.3,
            gas_price_trend="stable",
            trading_volume=500000.0,
            volatility=0.03,
            time_of_day_factor=0.5,
            timestamp=time.time()
        )
    
    def get_timing_statistics(self) -> Dict[str, Any]:
        """Get timing optimization statistics"""
        try:
            total_recommendations = len(self.timing_history)
            
            if total_recommendations == 0:
                return {"total_recommendations": 0}
            
            strategies = [rec.strategy for rec in self.timing_history]
            strategy_distribution = {strategy.value: strategies.count(strategy) for strategy in TimingStrategy}
            
            delays = [rec.delay_seconds for rec in self.timing_history]
            average_delay = np.mean(delays) if delays else 0
            
            jito_usage = sum(1 for rec in self.timing_history if rec.use_jito_bundle) / total_recommendations
            
            return {
                "total_recommendations": total_recommendations,
                "strategy_distribution": strategy_distribution,
                "average_delay": average_delay,
                "jito_bundle_usage": jito_usage,
                "average_confidence": np.mean([rec.confidence for rec in self.timing_history])
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting timing statistics: {e}")
            return {"error": str(e)}

# Factory function
def create_transaction_timing_optimizer() -> TransactionTimingOptimizer:
    """Create transaction timing optimizer instance"""
    return TransactionTimingOptimizer()

# Example usage
if __name__ == "__main__":
    async def test_timing_optimization():
        """Test transaction timing optimization"""
        optimizer = create_transaction_timing_optimizer()
        
        # Test timing optimization
        recommendation = await optimizer.optimize_transaction_timing("JTO", 50.0, "normal")
        
        print("=== TRANSACTION TIMING OPTIMIZATION ===")
        print(f"Strategy: {recommendation.strategy.value}")
        print(f"Delay: {recommendation.delay_seconds} seconds")
        print(f"Use Jito Bundle: {recommendation.use_jito_bundle}")
        print(f"Priority Fee Multiplier: {recommendation.priority_fee_multiplier:.1f}x")
        print(f"Confidence: {recommendation.confidence:.1%}")
        print(f"Reasoning: {recommendation.reasoning}")
        
        # Test execution with timing
        transaction_data = {
            'token_address': 'JTO',
            'amount': 50.0,
            'action': 'BUY',
            'urgency': 'normal'
        }
        
        optimized_tx = await optimizer.execute_with_optimal_timing(transaction_data)
        print(f"\nOptimized Transaction: {optimized_tx}")
    
    asyncio.run(test_timing_optimization())
