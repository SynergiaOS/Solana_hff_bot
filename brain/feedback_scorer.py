#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - AI Feedback Scorer
Learns from every transaction and improves decision making
"""

import asyncio
import json
import time
import redis
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import chromadb
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TransactionFeedback:
    transaction_id: str
    symbol: str
    action: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    confidence: float
    strategy: str
    pnl: float
    pnl_percentage: float
    hold_time: float
    market_conditions: Dict
    decision_factors: Dict
    outcome_score: float
    lessons_learned: List[str]

class AIFeedbackScorer:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Initialize ChromaDB for vector memory
        self.chroma_client = chromadb.PersistentClient(path="./chroma_feedback_db")
        self.feedback_collection = self.chroma_client.get_or_create_collection(
            name="transaction_feedback",
            metadata={"description": "AI feedback and learning from transactions"}
        )
        
        # Scoring configuration
        self.config = {
            'min_hold_time_for_scoring': 60,     # 1 minute minimum
            'excellent_threshold': 0.05,          # 5% profit = excellent
            'good_threshold': 0.02,               # 2% profit = good
            'poor_threshold': -0.02,              # -2% = poor
            'terrible_threshold': -0.05,          # -5% = terrible
            'confidence_weight': 0.3,             # Weight of confidence in scoring
            'timing_weight': 0.2,                 # Weight of timing in scoring
            'market_condition_weight': 0.2,       # Weight of market conditions
            'strategy_effectiveness_weight': 0.3, # Weight of strategy effectiveness
        }
        
    async def analyze_completed_transaction(self, execution_result: dict) -> Optional[TransactionFeedback]:
        """Analyze a completed transaction and generate feedback"""
        try:
            transaction_id = execution_result.get('transaction_id', '')
            symbol = execution_result.get('symbol', '')
            action = execution_result.get('action', '')
            
            if not all([transaction_id, symbol, action]):
                return None
            
            # Get transaction details
            entry_price = execution_result.get('execution_price', 0)
            quantity = execution_result.get('quantity', 0)
            confidence = execution_result.get('confidence', 0.5)
            strategy = execution_result.get('strategy', 'UNKNOWN')
            
            # Calculate performance metrics
            pnl = execution_result.get('estimated_profit', 0)
            pnl_percentage = pnl / (entry_price * quantity) if (entry_price * quantity) > 0 else 0
            
            # Get hold time (simplified for now)
            hold_time = execution_result.get('hold_time', 300)  # Default 5 minutes
            
            # Analyze market conditions at time of trade
            market_conditions = await self.get_market_conditions(symbol, execution_result.get('timestamp', time.time()))
            
            # Extract decision factors
            decision_factors = {
                'confidence': confidence,
                'strategy': strategy,
                'market_sentiment': market_conditions.get('sentiment', 0.5),
                'volatility': market_conditions.get('volatility', 0.5),
                'volume': market_conditions.get('volume', 0.5)
            }
            
            # Calculate outcome score
            outcome_score = self.calculate_outcome_score(pnl_percentage, confidence, hold_time, market_conditions)
            
            # Generate lessons learned
            lessons_learned = self.generate_lessons_learned(pnl_percentage, confidence, strategy, market_conditions)
            
            feedback = TransactionFeedback(
                transaction_id=transaction_id,
                symbol=symbol,
                action=action,
                entry_price=entry_price,
                exit_price=entry_price + (pnl / quantity) if quantity > 0 else entry_price,
                quantity=quantity,
                confidence=confidence,
                strategy=strategy,
                pnl=pnl,
                pnl_percentage=pnl_percentage,
                hold_time=hold_time,
                market_conditions=market_conditions,
                decision_factors=decision_factors,
                outcome_score=outcome_score,
                lessons_learned=lessons_learned
            )
            
            return feedback
            
        except Exception as e:
            logger.error(f"❌ Error analyzing transaction: {e}")
            return None
    
    def calculate_outcome_score(self, pnl_pct: float, confidence: float, hold_time: float, market_conditions: dict) -> float:
        """Calculate a comprehensive outcome score (0-1)"""
        
        # Base score from P&L performance
        if pnl_pct >= self.config['excellent_threshold']:
            base_score = 1.0
        elif pnl_pct >= self.config['good_threshold']:
            base_score = 0.8
        elif pnl_pct >= 0:
            base_score = 0.6
        elif pnl_pct >= self.config['poor_threshold']:
            base_score = 0.4
        elif pnl_pct >= self.config['terrible_threshold']:
            base_score = 0.2
        else:
            base_score = 0.0
        
        # Confidence alignment bonus/penalty
        confidence_alignment = 1.0 - abs(confidence - (0.5 + pnl_pct))
        confidence_score = confidence_alignment * self.config['confidence_weight']
        
        # Timing score (longer profitable holds are better)
        if pnl_pct > 0:
            timing_score = min(1.0, hold_time / 3600) * self.config['timing_weight']  # Up to 1 hour
        else:
            timing_score = max(0.0, 1.0 - hold_time / 1800) * self.config['timing_weight']  # Faster exits for losses
        
        # Market condition score
        market_difficulty = market_conditions.get('volatility', 0.5)
        market_score = (1.0 - market_difficulty) * self.config['market_condition_weight']
        
        # Combine scores
        total_score = (
            base_score * (1 - self.config['confidence_weight'] - self.config['timing_weight'] - self.config['market_condition_weight']) +
            confidence_score +
            timing_score +
            market_score
        )
        
        return max(0.0, min(1.0, total_score))
    
    def generate_lessons_learned(self, pnl_pct: float, confidence: float, strategy: str, market_conditions: dict) -> List[str]:
        """Generate lessons learned from the transaction"""
        lessons = []
        
        # Performance-based lessons
        if pnl_pct > self.config['excellent_threshold']:
            lessons.append(f"Excellent performance with {strategy} strategy - replicate conditions")
            if confidence < 0.8:
                lessons.append("High profit with low confidence - consider increasing confidence in similar setups")
        elif pnl_pct < self.config['poor_threshold']:
            lessons.append(f"Poor performance with {strategy} strategy - review entry criteria")
            if confidence > 0.7:
                lessons.append("High confidence but poor result - reassess confidence calibration")
        
        # Market condition lessons
        volatility = market_conditions.get('volatility', 0.5)
        if volatility > 0.7 and pnl_pct < 0:
            lessons.append("High volatility led to losses - consider reducing position sizes in volatile markets")
        elif volatility < 0.3 and pnl_pct > 0:
            lessons.append("Low volatility environment was favorable - increase allocation in stable conditions")
        
        # Strategy-specific lessons
        if strategy == "MEMECOIN_HUNTER" and pnl_pct < 0:
            lessons.append("Memecoin strategy failed - review sentiment and volume indicators")
        elif strategy == "DEX_ARBITRAGE" and pnl_pct > 0:
            lessons.append("DEX arbitrage successful - monitor for similar opportunities")
        
        return lessons
    
    async def get_market_conditions(self, symbol: str, timestamp: float) -> dict:
        """Get market conditions at the time of trade"""
        try:
            # Simplified market conditions - in production, this would fetch real data
            return {
                'sentiment': 0.6,  # Neutral to positive
                'volatility': 0.5,  # Medium volatility
                'volume': 0.7,     # High volume
                'trend': 'BULLISH',
                'support_level': 0.8,
                'resistance_level': 0.9
            }
        except Exception as e:
            logger.error(f"❌ Error getting market conditions: {e}")
            return {'sentiment': 0.5, 'volatility': 0.5, 'volume': 0.5}
    
    async def store_feedback_in_vector_memory(self, feedback: TransactionFeedback):
        """Store feedback in vector memory for future learning"""
        try:
            # Create embedding text
            embedding_text = f"""
            Transaction: {feedback.action} {feedback.symbol}
            Strategy: {feedback.strategy}
            Confidence: {feedback.confidence:.2f}
            P&L: {feedback.pnl_percentage:.2%}
            Outcome Score: {feedback.outcome_score:.2f}
            Market Conditions: {json.dumps(feedback.market_conditions)}
            Lessons: {' | '.join(feedback.lessons_learned)}
            """
            
            # Store in ChromaDB
            self.feedback_collection.add(
                documents=[embedding_text],
                metadatas=[{
                    'transaction_id': feedback.transaction_id,
                    'symbol': feedback.symbol,
                    'strategy': feedback.strategy,
                    'pnl_percentage': feedback.pnl_percentage,
                    'outcome_score': feedback.outcome_score,
                    'timestamp': time.time()
                }],
                ids=[feedback.transaction_id]
            )
            
            logger.info(f"📚 Stored feedback for {feedback.transaction_id} in vector memory")
            
        except Exception as e:
            logger.error(f"❌ Error storing feedback in vector memory: {e}")
    
    async def get_similar_transaction_insights(self, symbol: str, strategy: str, confidence: float) -> List[str]:
        """Get insights from similar past transactions"""
        try:
            query_text = f"Strategy: {strategy} Symbol: {symbol} Confidence: {confidence:.2f}"
            
            results = self.feedback_collection.query(
                query_texts=[query_text],
                n_results=5
            )
            
            insights = []
            if results['metadatas']:
                for metadata in results['metadatas'][0]:
                    outcome_score = metadata.get('outcome_score', 0)
                    pnl_pct = metadata.get('pnl_percentage', 0)
                    
                    if outcome_score > 0.8:
                        insights.append(f"Similar {strategy} trade achieved {pnl_pct:.2%} profit")
                    elif outcome_score < 0.3:
                        insights.append(f"Similar {strategy} trade lost {abs(pnl_pct):.2%}")
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error getting similar transaction insights: {e}")
            return []
    
    async def run_feedback_scoring_system(self):
        """Main feedback scoring loop"""
        logger.info("🧠 Starting AI Feedback Scorer System")
        
        processed_transactions = set()
        
        while True:
            try:
                # Get recent execution results
                execution_results = self.redis_client.lrange('overmind:execution_results', 0, 9)
                
                for result_str in execution_results:
                    result = json.loads(result_str)
                    transaction_id = result.get('transaction_id', '')
                    
                    # Skip if already processed
                    if transaction_id in processed_transactions:
                        continue
                    
                    # Skip if too recent (need time for position to develop)
                    result_time = result.get('timestamp', 0)
                    if time.time() - result_time < self.config['min_hold_time_for_scoring']:
                        continue
                    
                    # Analyze transaction
                    feedback = await self.analyze_completed_transaction(result)
                    
                    if feedback:
                        # Store feedback
                        await self.store_feedback_in_vector_memory(feedback)
                        
                        # Store in Redis for immediate access
                        feedback_data = {
                            'transaction_id': feedback.transaction_id,
                            'symbol': feedback.symbol,
                            'strategy': feedback.strategy,
                            'outcome_score': feedback.outcome_score,
                            'pnl_percentage': feedback.pnl_percentage,
                            'lessons_learned': feedback.lessons_learned,
                            'timestamp': time.time()
                        }
                        
                        self.redis_client.lpush('overmind:ai_feedback', json.dumps(feedback_data))
                        
                        # Mark as processed
                        processed_transactions.add(transaction_id)
                        
                        logger.info(f"📊 Scored transaction {transaction_id}: {feedback.outcome_score:.2f}")
                        
                        # Log lessons learned
                        for lesson in feedback.lessons_learned:
                            logger.info(f"📚 Lesson: {lesson}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Error in feedback scoring system: {e}")
                await asyncio.sleep(30)

    async def get_strategy_performance_analysis(self, strategy: str) -> Dict[str, Any]:
        """Analyze overall performance of a specific strategy"""
        try:
            # Query all transactions for this strategy
            results = self.feedback_collection.query(
                query_texts=[f"Strategy: {strategy}"],
                n_results=100,
                where={"strategy": strategy}
            )

            if not results['metadatas'] or not results['metadatas'][0]:
                return {"strategy": strategy, "analysis": "No data available"}

            # Analyze performance metrics
            scores = [meta.get('outcome_score', 0) for meta in results['metadatas'][0]]
            pnl_values = [meta.get('pnl_percentage', 0) for meta in results['metadatas'][0]]

            analysis = {
                "strategy": strategy,
                "total_trades": len(scores),
                "avg_outcome_score": sum(scores) / len(scores) if scores else 0,
                "avg_pnl_percentage": sum(pnl_values) / len(pnl_values) if pnl_values else 0,
                "success_rate": len([s for s in scores if s > 0.6]) / len(scores) if scores else 0,
                "recommendation": "CONTINUE" if (sum(scores) / len(scores) if scores else 0) > 0.6 else "REVIEW"
            }

            logger.info(f"📊 Strategy {strategy} analysis: {analysis['success_rate']:.1%} success rate")
            return analysis

        except Exception as e:
            logger.error(f"❌ Error analyzing strategy performance: {e}")
            return {"strategy": strategy, "analysis": "Error in analysis"}

    async def get_adaptive_recommendations(self, current_market_conditions: Dict[str, Any]) -> List[str]:
        """Get adaptive recommendations based on current market conditions and past performance"""
        try:
            recommendations = []

            # Query similar market conditions
            volatility = current_market_conditions.get('volatility', 0.5)
            sentiment = current_market_conditions.get('sentiment', 0.5)

            # Find successful trades in similar conditions
            query_text = f"Volatility: {volatility:.2f} Sentiment: {sentiment:.2f}"

            results = self.feedback_collection.query(
                query_texts=[query_text],
                n_results=10
            )

            if results['metadatas'] and results['metadatas'][0]:
                successful_trades = [
                    meta for meta in results['metadatas'][0]
                    if meta.get('outcome_score', 0) > 0.7
                ]

                if successful_trades:
                    # Analyze successful strategies
                    strategies = [trade.get('strategy', '') for trade in successful_trades]
                    strategy_counts = {}
                    for strategy in strategies:
                        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

                    # Recommend most successful strategy
                    best_strategy = max(strategy_counts, key=strategy_counts.get)
                    recommendations.append(f"In similar market conditions, {best_strategy} strategy performed best")

                    # Analyze confidence levels
                    confidences = [trade.get('confidence', 0.5) for trade in successful_trades]
                    avg_confidence = sum(confidences) / len(confidences)
                    recommendations.append(f"Optimal confidence level for these conditions: {avg_confidence:.2f}")

            return recommendations

        except Exception as e:
            logger.error(f"❌ Error getting adaptive recommendations: {e}")
            return []

async def main():
    scorer = AIFeedbackScorer()
    await scorer.run_feedback_scoring_system()

if __name__ == "__main__":
    asyncio.run(main())
