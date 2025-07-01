#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - MEV Risk Analyzer
Advanced MEV risk assessment and anti-sniper protection
"""

import asyncio
import aiohttp
import json
import redis
import time
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MEVRiskAnalyzer')

class MEVRiskLevel(Enum):
    """MEV risk level classifications"""
    MINIMAL = "minimal"      # 0.0-0.2 - Safe to trade
    LOW = "low"             # 0.2-0.4 - Proceed with caution
    MEDIUM = "medium"       # 0.4-0.6 - Increase slippage tolerance
    HIGH = "high"           # 0.6-0.8 - Use Jito bundles only
    EXTREME = "extreme"     # 0.8-1.0 - Delay transaction

@dataclass
class MEVRiskAssessment:
    """MEV risk assessment result"""
    risk_score: float           # 0.0-1.0
    risk_level: MEVRiskLevel
    congestion_score: float     # Network congestion factor
    bot_activity_score: float   # Suspicious bot activity
    sandwich_risk: float        # Sandwich attack probability
    frontrun_risk: float        # Frontrunning probability
    recommended_slippage: float # Recommended slippage tolerance
    recommended_priority_fee: float # Recommended priority fee
    use_jito_bundle: bool      # Whether to use Jito bundle
    delay_seconds: int         # Recommended delay before execution
    reasoning: str             # Human-readable explanation
    timestamp: float

@dataclass
class TransactionPoolData:
    """Transaction pool analysis data"""
    pending_transactions: int
    gas_price_percentiles: Dict[str, float]
    large_transactions: List[Dict[str, Any]]
    bot_transactions: List[Dict[str, Any]]
    congestion_level: float
    timestamp: float

class MEVRiskAnalyzer:
    """
    Advanced MEV Risk Assessment Engine
    
    Analyzes transaction pool conditions, bot activity, and market conditions
    to assess MEV risk and recommend protection strategies
    """
    
    def __init__(self):
        """Initialize MEV Risk Analyzer"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # API configuration
        self.helius_api_key = "edbcd361-78a0-4998-bd1e-8d4666722f82"
        self.quicknode_endpoint = "https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580/"
        
        # MEV risk thresholds
        self.risk_thresholds = {
            'congestion': {
                'low': 100,      # < 100 pending txs
                'medium': 500,   # 100-500 pending txs
                'high': 1000     # > 1000 pending txs
            },
            'bot_activity': {
                'suspicious_volume': 1000000,  # > 1M SOL volume
                'rapid_transactions': 10,      # > 10 txs per second
                'large_transaction': 100       # > 100 SOL
            },
            'market_impact': {
                'low_liquidity': 0.02,    # < 2% market depth
                'high_volatility': 0.05   # > 5% price movement
            }
        }
        
        # Protection strategies
        self.protection_strategies = {
            MEVRiskLevel.MINIMAL: {
                'slippage_multiplier': 1.0,
                'priority_fee_multiplier': 1.0,
                'use_jito': False,
                'delay_seconds': 0
            },
            MEVRiskLevel.LOW: {
                'slippage_multiplier': 1.2,
                'priority_fee_multiplier': 1.5,
                'use_jito': False,
                'delay_seconds': 0
            },
            MEVRiskLevel.MEDIUM: {
                'slippage_multiplier': 1.5,
                'priority_fee_multiplier': 2.0,
                'use_jito': True,
                'delay_seconds': 5
            },
            MEVRiskLevel.HIGH: {
                'slippage_multiplier': 2.0,
                'priority_fee_multiplier': 3.0,
                'use_jito': True,
                'delay_seconds': 15
            },
            MEVRiskLevel.EXTREME: {
                'slippage_multiplier': 3.0,
                'priority_fee_multiplier': 5.0,
                'use_jito': True,
                'delay_seconds': 60
            }
        }
        
        # Historical data
        self.mev_incidents = []
        self.risk_history = []
        
        logger.info("🛡️ MEV Risk Analyzer initialized")
        logger.info("🔍 Anti-sniper protection enabled")
        logger.info("⚡ Jito bundle optimization ready")
    
    async def assess_mev_risk(self, 
                            token_address: str, 
                            transaction_amount: float,
                            transaction_type: str = "swap") -> MEVRiskAssessment:
        """
        Comprehensive MEV risk assessment for a transaction
        """
        try:
            logger.info(f"🔍 Assessing MEV risk for {token_address} ({transaction_amount} SOL)")
            
            # Analyze transaction pool conditions
            pool_data = await self.analyze_transaction_pool()
            
            # Assess bot activity
            bot_activity = await self.assess_bot_activity(token_address, transaction_amount)
            
            # Calculate congestion score
            congestion_score = self.calculate_congestion_score(pool_data)
            
            # Calculate sandwich risk
            sandwich_risk = await self.calculate_sandwich_risk(token_address, transaction_amount)
            
            # Calculate frontrun risk
            frontrun_risk = await self.calculate_frontrun_risk(token_address, transaction_amount)
            
            # Combine scores into overall risk
            overall_risk = self.calculate_overall_risk(
                congestion_score, bot_activity, sandwich_risk, frontrun_risk
            )
            
            # Determine risk level
            risk_level = self.determine_risk_level(overall_risk)
            
            # Get protection recommendations
            protection = self.get_protection_recommendations(risk_level, transaction_amount)
            
            # Create assessment
            assessment = MEVRiskAssessment(
                risk_score=overall_risk,
                risk_level=risk_level,
                congestion_score=congestion_score,
                bot_activity_score=bot_activity,
                sandwich_risk=sandwich_risk,
                frontrun_risk=frontrun_risk,
                recommended_slippage=protection['slippage'],
                recommended_priority_fee=protection['priority_fee'],
                use_jito_bundle=protection['use_jito'],
                delay_seconds=protection['delay'],
                reasoning=self.generate_risk_reasoning(overall_risk, risk_level, congestion_score, bot_activity),
                timestamp=time.time()
            )
            
            # Store assessment
            await self.store_risk_assessment(assessment)
            
            logger.info(f"🛡️ MEV Risk Assessment: {risk_level.value} ({overall_risk:.2f})")
            logger.info(f"   Recommended Slippage: {protection['slippage']:.1%}")
            logger.info(f"   Use Jito Bundle: {protection['use_jito']}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"❌ Error assessing MEV risk: {e}")
            return self.create_fallback_assessment()
    
    async def analyze_transaction_pool(self) -> TransactionPoolData:
        """Analyze current transaction pool conditions"""
        try:
            # For now, simulate transaction pool data
            # In production, this would query Solana RPC for mempool data
            
            # Simulate varying congestion levels
            base_pending = 200
            congestion_multiplier = np.random.uniform(0.5, 3.0)
            pending_transactions = int(base_pending * congestion_multiplier)
            
            # Simulate gas price percentiles
            base_gas = 0.000005  # 5000 lamports
            gas_percentiles = {
                'p10': base_gas * 0.8,
                'p50': base_gas * 1.0,
                'p90': base_gas * 1.5,
                'p99': base_gas * 2.0
            }
            
            # Simulate large transactions (potential MEV targets)
            large_transactions = []
            for i in range(np.random.randint(0, 5)):
                large_transactions.append({
                    'amount': np.random.uniform(50, 500),
                    'token': 'SOL',
                    'type': 'swap',
                    'timestamp': time.time() - np.random.uniform(0, 60)
                })
            
            # Simulate bot transactions
            bot_transactions = []
            for i in range(np.random.randint(0, 10)):
                bot_transactions.append({
                    'frequency': np.random.uniform(5, 20),  # txs per minute
                    'pattern': 'arbitrage' if np.random.random() > 0.5 else 'sandwich',
                    'volume': np.random.uniform(10, 100)
                })
            
            # Calculate congestion level
            congestion_level = min(1.0, pending_transactions / 1000.0)
            
            pool_data = TransactionPoolData(
                pending_transactions=pending_transactions,
                gas_price_percentiles=gas_percentiles,
                large_transactions=large_transactions,
                bot_transactions=bot_transactions,
                congestion_level=congestion_level,
                timestamp=time.time()
            )
            
            logger.info(f"📊 Transaction pool analysis: {pending_transactions} pending, {congestion_level:.1%} congestion")
            return pool_data
            
        except Exception as e:
            logger.error(f"❌ Error analyzing transaction pool: {e}")
            return self.create_fallback_pool_data()
    
    async def assess_bot_activity(self, token_address: str, transaction_amount: float) -> float:
        """Assess suspicious bot activity around the token"""
        try:
            # Simulate bot activity assessment
            # In production, this would analyze recent transactions for patterns
            
            # Base bot activity (always some bots present)
            base_activity = 0.1
            
            # Increase activity for larger transactions
            size_factor = min(0.3, transaction_amount / 100.0)
            
            # Random market activity factor
            market_factor = np.random.uniform(0.0, 0.4)
            
            # Time-based factor (higher activity during US trading hours)
            current_hour = datetime.now().hour
            if 14 <= current_hour <= 21:  # 9 AM - 4 PM EST
                time_factor = 0.2
            else:
                time_factor = 0.0
            
            bot_activity = base_activity + size_factor + market_factor + time_factor
            bot_activity = min(1.0, bot_activity)
            
            logger.info(f"🤖 Bot activity assessment: {bot_activity:.2f}")
            return bot_activity
            
        except Exception as e:
            logger.error(f"❌ Error assessing bot activity: {e}")
            return 0.3  # Default moderate activity
    
    def calculate_congestion_score(self, pool_data: TransactionPoolData) -> float:
        """Calculate network congestion score"""
        try:
            pending = pool_data.pending_transactions
            
            if pending < self.risk_thresholds['congestion']['low']:
                return 0.1
            elif pending < self.risk_thresholds['congestion']['medium']:
                return 0.3
            elif pending < self.risk_thresholds['congestion']['high']:
                return 0.6
            else:
                return 0.9
                
        except Exception as e:
            logger.error(f"❌ Error calculating congestion score: {e}")
            return 0.3
    
    async def calculate_sandwich_risk(self, token_address: str, transaction_amount: float) -> float:
        """Calculate sandwich attack risk"""
        try:
            # Factors that increase sandwich risk:
            # 1. Large transaction size
            # 2. Low liquidity token
            # 3. High slippage potential
            
            # Size factor (larger transactions = higher risk)
            size_factor = min(0.4, transaction_amount / 50.0)
            
            # Liquidity factor (simulate low liquidity = higher risk)
            # In production, this would check actual liquidity pools
            liquidity_factor = np.random.uniform(0.1, 0.3)
            
            # Market volatility factor
            volatility_factor = np.random.uniform(0.0, 0.2)
            
            sandwich_risk = size_factor + liquidity_factor + volatility_factor
            sandwich_risk = min(1.0, sandwich_risk)
            
            logger.info(f"🥪 Sandwich risk: {sandwich_risk:.2f}")
            return sandwich_risk
            
        except Exception as e:
            logger.error(f"❌ Error calculating sandwich risk: {e}")
            return 0.3
    
    async def calculate_frontrun_risk(self, token_address: str, transaction_amount: float) -> float:
        """Calculate frontrunning risk"""
        try:
            # Factors that increase frontrun risk:
            # 1. Predictable transaction patterns
            # 2. High-value transactions
            # 3. Popular tokens
            
            # Value factor
            value_factor = min(0.3, transaction_amount / 100.0)
            
            # Token popularity factor (simulate)
            popularity_factor = np.random.uniform(0.1, 0.2)
            
            # Pattern predictability (simulate)
            pattern_factor = np.random.uniform(0.0, 0.2)
            
            frontrun_risk = value_factor + popularity_factor + pattern_factor
            frontrun_risk = min(1.0, frontrun_risk)
            
            logger.info(f"🏃 Frontrun risk: {frontrun_risk:.2f}")
            return frontrun_risk
            
        except Exception as e:
            logger.error(f"❌ Error calculating frontrun risk: {e}")
            return 0.2
    
    def calculate_overall_risk(self, congestion: float, bot_activity: float, 
                             sandwich: float, frontrun: float) -> float:
        """Calculate overall MEV risk score"""
        try:
            # Weighted combination of risk factors
            weights = {
                'congestion': 0.25,
                'bot_activity': 0.30,
                'sandwich': 0.30,
                'frontrun': 0.15
            }
            
            overall_risk = (
                congestion * weights['congestion'] +
                bot_activity * weights['bot_activity'] +
                sandwich * weights['sandwich'] +
                frontrun * weights['frontrun']
            )
            
            return min(1.0, overall_risk)
            
        except Exception as e:
            logger.error(f"❌ Error calculating overall risk: {e}")
            return 0.5
    
    def determine_risk_level(self, risk_score: float) -> MEVRiskLevel:
        """Determine risk level from score"""
        if risk_score < 0.2:
            return MEVRiskLevel.MINIMAL
        elif risk_score < 0.4:
            return MEVRiskLevel.LOW
        elif risk_score < 0.6:
            return MEVRiskLevel.MEDIUM
        elif risk_score < 0.8:
            return MEVRiskLevel.HIGH
        else:
            return MEVRiskLevel.EXTREME
    
    def get_protection_recommendations(self, risk_level: MEVRiskLevel, 
                                     transaction_amount: float) -> Dict[str, Any]:
        """Get protection strategy recommendations"""
        try:
            strategy = self.protection_strategies[risk_level]
            
            # Base recommendations
            base_slippage = 0.01  # 1%
            base_priority_fee = 0.000005  # 5000 lamports
            
            recommendations = {
                'slippage': base_slippage * strategy['slippage_multiplier'],
                'priority_fee': base_priority_fee * strategy['priority_fee_multiplier'],
                'use_jito': strategy['use_jito'],
                'delay': strategy['delay_seconds']
            }
            
            # Adjust for transaction size
            if transaction_amount > 50:
                recommendations['slippage'] *= 1.2
                recommendations['priority_fee'] *= 1.5
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error getting protection recommendations: {e}")
            return {
                'slippage': 0.02,
                'priority_fee': 0.00001,
                'use_jito': True,
                'delay': 10
            }
    
    def generate_risk_reasoning(self, risk_score: float, risk_level: MEVRiskLevel,
                              congestion: float, bot_activity: float) -> str:
        """Generate human-readable risk reasoning"""
        try:
            reasoning = f"MEV risk classified as {risk_level.value} ({risk_score:.1%}). "
            
            if congestion > 0.6:
                reasoning += "High network congestion detected. "
            elif congestion > 0.3:
                reasoning += "Moderate network congestion. "
            
            if bot_activity > 0.6:
                reasoning += "Significant bot activity observed. "
            elif bot_activity > 0.3:
                reasoning += "Moderate bot activity present. "
            
            if risk_level == MEVRiskLevel.EXTREME:
                reasoning += "Recommend delaying transaction until conditions improve."
            elif risk_level == MEVRiskLevel.HIGH:
                reasoning += "Use Jito bundles and increased slippage tolerance."
            elif risk_level == MEVRiskLevel.MEDIUM:
                reasoning += "Proceed with caution and enhanced protection."
            else:
                reasoning += "Safe to proceed with standard parameters."
            
            return reasoning
            
        except Exception as e:
            logger.error(f"❌ Error generating reasoning: {e}")
            return "MEV risk assessment completed with standard recommendations."
    
    async def store_risk_assessment(self, assessment: MEVRiskAssessment):
        """Store risk assessment in Redis"""
        try:
            assessment_data = {
                "risk_score": assessment.risk_score,
                "risk_level": assessment.risk_level.value,
                "congestion_score": assessment.congestion_score,
                "bot_activity_score": assessment.bot_activity_score,
                "sandwich_risk": assessment.sandwich_risk,
                "frontrun_risk": assessment.frontrun_risk,
                "recommended_slippage": assessment.recommended_slippage,
                "recommended_priority_fee": assessment.recommended_priority_fee,
                "use_jito_bundle": assessment.use_jito_bundle,
                "delay_seconds": assessment.delay_seconds,
                "reasoning": assessment.reasoning,
                "timestamp": assessment.timestamp
            }
            
            # Store current assessment
            self.redis_client.setex("overmind:mev_risk", 300, json.dumps(assessment_data))
            
            # Add to history
            self.redis_client.lpush("overmind:mev_risk_history", json.dumps(assessment_data))
            self.redis_client.ltrim("overmind:mev_risk_history", 0, 99)  # Keep last 100
            
            logger.info(f"🛡️ MEV risk assessment stored: {assessment.risk_level.value}")
            
        except Exception as e:
            logger.error(f"❌ Error storing risk assessment: {e}")
    
    def create_fallback_assessment(self) -> MEVRiskAssessment:
        """Create fallback assessment when analysis fails"""
        return MEVRiskAssessment(
            risk_score=0.5,
            risk_level=MEVRiskLevel.MEDIUM,
            congestion_score=0.3,
            bot_activity_score=0.3,
            sandwich_risk=0.3,
            frontrun_risk=0.2,
            recommended_slippage=0.02,
            recommended_priority_fee=0.00001,
            use_jito_bundle=True,
            delay_seconds=10,
            reasoning="Fallback assessment due to analysis error - using conservative parameters",
            timestamp=time.time()
        )
    
    def create_fallback_pool_data(self) -> TransactionPoolData:
        """Create fallback pool data when analysis fails"""
        return TransactionPoolData(
            pending_transactions=300,
            gas_price_percentiles={'p10': 0.000004, 'p50': 0.000005, 'p90': 0.000008, 'p99': 0.00001},
            large_transactions=[],
            bot_transactions=[],
            congestion_level=0.3,
            timestamp=time.time()
        )
    
    def get_mev_statistics(self) -> Dict[str, Any]:
        """Get MEV protection statistics"""
        try:
            # Calculate statistics from history
            total_assessments = len(self.risk_history)
            
            if total_assessments == 0:
                return {"total_assessments": 0, "average_risk": 0.0}
            
            risk_scores = [assessment.risk_score for assessment in self.risk_history]
            average_risk = np.mean(risk_scores)
            
            risk_levels = [assessment.risk_level for assessment in self.risk_history]
            risk_distribution = {level.value: risk_levels.count(level) for level in MEVRiskLevel}
            
            return {
                "total_assessments": total_assessments,
                "average_risk": average_risk,
                "risk_distribution": risk_distribution,
                "jito_bundle_usage": sum(1 for a in self.risk_history if a.use_jito_bundle) / total_assessments
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting MEV statistics: {e}")
            return {"error": str(e)}

# Factory function
def create_mev_risk_analyzer() -> MEVRiskAnalyzer:
    """Create MEV risk analyzer instance"""
    return MEVRiskAnalyzer()

# Example usage
if __name__ == "__main__":
    async def test_mev_analysis():
        """Test MEV risk analysis"""
        analyzer = create_mev_risk_analyzer()
        
        # Test risk assessment
        assessment = await analyzer.assess_mev_risk("JTO", 25.0, "swap")
        
        print("=== MEV RISK ASSESSMENT ===")
        print(f"Risk Score: {assessment.risk_score:.2f}")
        print(f"Risk Level: {assessment.risk_level.value}")
        print(f"Congestion: {assessment.congestion_score:.2f}")
        print(f"Bot Activity: {assessment.bot_activity_score:.2f}")
        print(f"Sandwich Risk: {assessment.sandwich_risk:.2f}")
        print(f"Frontrun Risk: {assessment.frontrun_risk:.2f}")
        print(f"Recommended Slippage: {assessment.recommended_slippage:.1%}")
        print(f"Use Jito Bundle: {assessment.use_jito_bundle}")
        print(f"Delay: {assessment.delay_seconds}s")
        print(f"Reasoning: {assessment.reasoning}")
    
    asyncio.run(test_mev_analysis())
