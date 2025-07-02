#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Enhanced Memory Retrieval System
Advanced memory retrieval with pattern recognition, temporal analysis, and predictive insights
"""

import asyncio
import json
import time
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from jina_vector_memory import JinaVectorMemoryManager, VectorMemory, MemoryQuery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PatternMatch:
    """Pattern match result"""
    pattern_id: str
    similarity_score: float
    confidence: float
    pattern_type: str
    historical_outcome: Dict[str, Any]
    context_memories: List[VectorMemory]
    prediction: Dict[str, Any]

@dataclass
class TemporalPattern:
    """Temporal pattern analysis"""
    pattern_name: str
    time_window: str
    frequency: int
    success_rate: float
    avg_outcome: float
    volatility: float
    conditions: List[str]

@dataclass
class MemoryInsight:
    """Enhanced memory insight"""
    insight_type: str
    confidence: float
    description: str
    supporting_memories: List[str]
    actionable_signals: List[str]
    risk_assessment: Dict[str, float]

class EnhancedMemoryRetrieval:
    """
    Enhanced memory retrieval system with advanced pattern recognition
    """
    
    def __init__(self, vector_manager: JinaVectorMemoryManager):
        self.vector_manager = vector_manager
        self.pattern_cache = {}
        self.temporal_patterns = {}
        self.insight_cache = {}
        
        # Pattern recognition thresholds
        self.similarity_threshold = 0.7
        self.confidence_threshold = 0.6
        self.pattern_frequency_threshold = 3
        
        logger.info("🧠 Enhanced Memory Retrieval System initialized")
    
    async def find_predictive_patterns(self, 
                                     current_situation: Dict[str, Any],
                                     symbol: str,
                                     lookback_days: int = 90) -> List[PatternMatch]:
        """
        Find predictive patterns based on current situation
        """
        try:
            logger.info(f"🔮 Finding predictive patterns for {symbol}...")
            
            # Get historical memories
            historical_memories = await self.vector_manager.get_symbol_history(
                symbol, 
                lookback_days
            )
            
            if not historical_memories:
                logger.warning(f"⚠️ No historical data found for {symbol}")
                return []
            
            # Find similar situations
            similar_patterns = await self._find_similar_situations(
                current_situation,
                historical_memories
            )
            
            # Analyze outcomes of similar patterns
            pattern_matches = []
            for pattern in similar_patterns:
                outcome_analysis = await self._analyze_pattern_outcome(
                    pattern,
                    historical_memories
                )
                
                if outcome_analysis['confidence'] > self.confidence_threshold:
                    pattern_match = PatternMatch(
                        pattern_id=pattern.id,
                        similarity_score=pattern.relevance_score,
                        confidence=outcome_analysis['confidence'],
                        pattern_type=outcome_analysis['pattern_type'],
                        historical_outcome=outcome_analysis['outcome'],
                        context_memories=outcome_analysis['context'],
                        prediction=outcome_analysis['prediction']
                    )
                    pattern_matches.append(pattern_match)
            
            # Sort by confidence and similarity
            pattern_matches.sort(
                key=lambda x: (x.confidence * x.similarity_score), 
                reverse=True
            )
            
            logger.info(f"✅ Found {len(pattern_matches)} predictive patterns")
            return pattern_matches[:5]  # Top 5 patterns
            
        except Exception as e:
            logger.error(f"❌ Error finding predictive patterns: {e}")
            return []
    
    async def analyze_temporal_patterns(self, 
                                      symbol: str,
                                      pattern_type: str = "all",
                                      time_windows: List[str] = None) -> List[TemporalPattern]:
        """
        Analyze temporal patterns in historical data
        """
        try:
            if time_windows is None:
                time_windows = ["1h", "4h", "1d", "1w"]
            
            logger.info(f"⏰ Analyzing temporal patterns for {symbol}...")
            
            # Get extended historical data
            historical_memories = await self.vector_manager.get_symbol_history(
                symbol, 
                180  # 6 months
            )
            
            temporal_patterns = []
            
            for time_window in time_windows:
                patterns = await self._extract_temporal_patterns(
                    historical_memories,
                    time_window,
                    pattern_type
                )
                temporal_patterns.extend(patterns)
            
            # Filter by frequency and success rate
            significant_patterns = [
                pattern for pattern in temporal_patterns
                if (pattern.frequency >= self.pattern_frequency_threshold and
                    pattern.success_rate > 0.6)
            ]
            
            # Sort by success rate and frequency
            significant_patterns.sort(
                key=lambda x: (x.success_rate * x.frequency), 
                reverse=True
            )
            
            logger.info(f"✅ Found {len(significant_patterns)} significant temporal patterns")
            return significant_patterns
            
        except Exception as e:
            logger.error(f"❌ Error analyzing temporal patterns: {e}")
            return []
    
    async def generate_memory_insights(self, 
                                     symbol: str,
                                     context: Dict[str, Any] = None) -> List[MemoryInsight]:
        """
        Generate actionable insights from memory analysis
        """
        try:
            logger.info(f"💡 Generating memory insights for {symbol}...")
            
            # Get recent memories
            recent_memories = await self.vector_manager.get_symbol_history(symbol, 30)
            
            insights = []
            
            # Sentiment trend analysis
            sentiment_insight = await self._analyze_sentiment_trends(recent_memories)
            if sentiment_insight:
                insights.append(sentiment_insight)
            
            # Volume pattern analysis
            volume_insight = await self._analyze_volume_patterns(recent_memories)
            if volume_insight:
                insights.append(volume_insight)
            
            # Signal convergence analysis
            signal_insight = await self._analyze_signal_convergence(recent_memories)
            if signal_insight:
                insights.append(signal_insight)
            
            # Risk pattern analysis
            risk_insight = await self._analyze_risk_patterns(recent_memories, context)
            if risk_insight:
                insights.append(risk_insight)
            
            # News impact analysis
            news_insight = await self._analyze_news_impact(recent_memories)
            if news_insight:
                insights.append(news_insight)
            
            # Sort by confidence
            insights.sort(key=lambda x: x.confidence, reverse=True)
            
            logger.info(f"✅ Generated {len(insights)} memory insights")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error generating memory insights: {e}")
            return []
    
    async def predict_market_regime(self, 
                                  symbol: str,
                                  horizon_days: int = 7) -> Dict[str, Any]:
        """
        Predict market regime based on historical patterns
        """
        try:
            logger.info(f"📊 Predicting market regime for {symbol} ({horizon_days} days)...")
            
            # Get historical data
            historical_memories = await self.vector_manager.get_symbol_history(symbol, 90)
            
            # Analyze regime patterns
            regime_patterns = await self._analyze_regime_patterns(historical_memories)
            
            # Current market state
            current_state = await self._assess_current_market_state(symbol)
            
            # Predict regime transition
            regime_prediction = await self._predict_regime_transition(
                regime_patterns,
                current_state,
                horizon_days
            )
            
            logger.info(f"✅ Market regime prediction completed")
            return regime_prediction
            
        except Exception as e:
            logger.error(f"❌ Error predicting market regime: {e}")
            return {}
    
    async def find_arbitrage_opportunities(self, 
                                         symbols: List[str],
                                         min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find arbitrage opportunities based on historical patterns
        """
        try:
            logger.info(f"🔄 Finding arbitrage opportunities for {symbols}...")
            
            opportunities = []
            
            # Analyze cross-symbol patterns
            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    opportunity = await self._analyze_cross_symbol_patterns(
                        symbol1, 
                        symbol2,
                        min_confidence
                    )
                    
                    if opportunity and opportunity['confidence'] >= min_confidence:
                        opportunities.append(opportunity)
            
            # Sort by expected return
            opportunities.sort(
                key=lambda x: x.get('expected_return', 0), 
                reverse=True
            )
            
            logger.info(f"✅ Found {len(opportunities)} arbitrage opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Error finding arbitrage opportunities: {e}")
            return []
    
    async def _find_similar_situations(self, 
                                     current_situation: Dict[str, Any],
                                     historical_memories: List[VectorMemory]) -> List[VectorMemory]:
        """Find historically similar situations"""
        try:
            # Convert current situation to searchable format
            situation_text = json.dumps(current_situation)
            
            # Use vector similarity search
            similar_patterns = await self.vector_manager.get_similar_patterns(
                current_situation,
                "trading"
            )
            
            # Additional filtering based on metadata similarity
            filtered_patterns = []
            for pattern in similar_patterns:
                if pattern.relevance_score > self.similarity_threshold:
                    filtered_patterns.append(pattern)
            
            return filtered_patterns
            
        except Exception as e:
            logger.error(f"❌ Error finding similar situations: {e}")
            return []
    
    async def _analyze_pattern_outcome(self, 
                                     pattern: VectorMemory,
                                     historical_memories: List[VectorMemory]) -> Dict[str, Any]:
        """Analyze the outcome of a historical pattern"""
        try:
            # Find memories that occurred after this pattern
            pattern_time = datetime.fromisoformat(pattern.timestamp.replace('Z', '+00:00'))
            
            subsequent_memories = [
                memory for memory in historical_memories
                if datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00')) > pattern_time
            ]
            
            # Analyze outcomes within different time windows
            outcomes = {
                '1h': [],
                '4h': [],
                '1d': [],
                '1w': []
            }
            
            time_windows = {
                '1h': timedelta(hours=1),
                '4h': timedelta(hours=4),
                '1d': timedelta(days=1),
                '1w': timedelta(weeks=1)
            }
            
            for window_name, window_duration in time_windows.items():
                window_end = pattern_time + window_duration
                
                window_memories = [
                    memory for memory in subsequent_memories
                    if datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00')) <= window_end
                ]
                
                if window_memories:
                    # Calculate average sentiment/confidence in this window
                    avg_sentiment = statistics.mean([m.confidence for m in window_memories])
                    outcomes[window_name] = {
                        'avg_sentiment': avg_sentiment,
                        'memory_count': len(window_memories),
                        'outcome_type': 'positive' if avg_sentiment > 0.6 else 'negative' if avg_sentiment < 0.4 else 'neutral'
                    }
            
            # Determine overall pattern type and confidence
            pattern_metadata = json.loads(pattern.content) if pattern.content.startswith('{') else {}
            
            analysis = {
                'pattern_type': pattern_metadata.get('signal_type', 'general'),
                'confidence': pattern.confidence,
                'outcome': outcomes,
                'context': subsequent_memories[:5],  # First 5 subsequent memories
                'prediction': self._generate_prediction(outcomes)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing pattern outcome: {e}")
            return {'confidence': 0.0, 'outcome': {}, 'context': [], 'prediction': {}}
    
    async def _extract_temporal_patterns(self, 
                                       memories: List[VectorMemory],
                                       time_window: str,
                                       pattern_type: str) -> List[TemporalPattern]:
        """Extract temporal patterns from memories"""
        try:
            patterns = []
            
            # Group memories by time window
            time_groups = self._group_memories_by_time(memories, time_window)
            
            # Analyze patterns in each group
            for group_key, group_memories in time_groups.items():
                if len(group_memories) >= self.pattern_frequency_threshold:
                    pattern = await self._analyze_memory_group(
                        group_memories,
                        time_window,
                        pattern_type
                    )
                    
                    if pattern:
                        patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error extracting temporal patterns: {e}")
            return []
    
    def _group_memories_by_time(self, 
                              memories: List[VectorMemory],
                              time_window: str) -> Dict[str, List[VectorMemory]]:
        """Group memories by time window"""
        groups = defaultdict(list)
        
        for memory in memories:
            try:
                memory_time = datetime.fromisoformat(memory.timestamp.replace('Z', '+00:00'))
                
                if time_window == "1h":
                    group_key = memory_time.strftime("%Y-%m-%d-%H")
                elif time_window == "4h":
                    group_key = memory_time.strftime("%Y-%m-%d") + f"-{memory_time.hour // 4 * 4}"
                elif time_window == "1d":
                    group_key = memory_time.strftime("%Y-%m-%d")
                elif time_window == "1w":
                    group_key = memory_time.strftime("%Y-W%U")
                else:
                    group_key = memory_time.strftime("%Y-%m-%d")
                
                groups[group_key].append(memory)
                
            except Exception as e:
                logger.warning(f"⚠️ Error grouping memory {memory.id}: {e}")
                continue
        
        return dict(groups)
    
    async def _analyze_memory_group(self, 
                                  group_memories: List[VectorMemory],
                                  time_window: str,
                                  pattern_type: str) -> Optional[TemporalPattern]:
        """Analyze a group of memories for patterns"""
        try:
            if len(group_memories) < 2:
                return None
            
            # Calculate pattern metrics
            confidences = [memory.confidence for memory in group_memories]
            avg_confidence = statistics.mean(confidences)
            
            # Determine success rate (memories with confidence > 0.6)
            successful_memories = [m for m in group_memories if m.confidence > 0.6]
            success_rate = len(successful_memories) / len(group_memories)
            
            # Calculate volatility
            volatility = statistics.stdev(confidences) if len(confidences) > 1 else 0.0
            
            # Extract common conditions
            conditions = self._extract_common_conditions(group_memories)
            
            pattern = TemporalPattern(
                pattern_name=f"{pattern_type}_{time_window}_pattern",
                time_window=time_window,
                frequency=len(group_memories),
                success_rate=success_rate,
                avg_outcome=avg_confidence,
                volatility=volatility,
                conditions=conditions
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"❌ Error analyzing memory group: {e}")
            return None
    
    def _extract_common_conditions(self, memories: List[VectorMemory]) -> List[str]:
        """Extract common conditions from memory metadata"""
        conditions = []
        
        try:
            # Analyze metadata for common patterns
            metadata_fields = defaultdict(list)
            
            for memory in memories:
                if hasattr(memory, 'metadata') and memory.metadata:
                    for key, value in memory.metadata.items():
                        metadata_fields[key].append(value)
            
            # Find common values
            for field, values in metadata_fields.items():
                if len(values) >= len(memories) * 0.7:  # 70% commonality
                    most_common = max(set(values), key=values.count)
                    conditions.append(f"{field}:{most_common}")
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting conditions: {e}")
        
        return conditions[:5]  # Top 5 conditions
    
    def _generate_prediction(self, outcomes: Dict[str, Any]) -> Dict[str, Any]:
        """Generate prediction based on historical outcomes"""
        try:
            # Analyze outcome patterns
            positive_outcomes = 0
            total_outcomes = 0
            
            for window, outcome_data in outcomes.items():
                if outcome_data:
                    total_outcomes += 1
                    if outcome_data.get('outcome_type') == 'positive':
                        positive_outcomes += 1
            
            if total_outcomes == 0:
                return {'confidence': 0.0, 'direction': 'neutral', 'probability': 0.5}
            
            success_probability = positive_outcomes / total_outcomes
            
            prediction = {
                'confidence': min(success_probability * 1.2, 1.0),  # Boost confidence slightly
                'direction': 'positive' if success_probability > 0.6 else 'negative' if success_probability < 0.4 else 'neutral',
                'probability': success_probability,
                'time_horizon': '1d',  # Default prediction horizon
                'risk_level': 'high' if success_probability < 0.4 or success_probability > 0.8 else 'medium'
            }
            
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Error generating prediction: {e}")
            return {'confidence': 0.0, 'direction': 'neutral', 'probability': 0.5}
    
    async def _analyze_sentiment_trends(self, memories: List[VectorMemory]) -> Optional[MemoryInsight]:
        """Analyze sentiment trends in recent memories"""
        try:
            if len(memories) < 5:
                return None
            
            # Extract sentiment scores over time
            sentiment_data = []
            for memory in sorted(memories, key=lambda x: x.timestamp):
                if memory.memory_type == 'news' and hasattr(memory, 'metadata'):
                    sentiment_score = memory.metadata.get('sentiment_score', memory.confidence)
                    sentiment_data.append(sentiment_score)
            
            if len(sentiment_data) < 3:
                return None
            
            # Calculate trend
            recent_sentiment = statistics.mean(sentiment_data[-3:])
            older_sentiment = statistics.mean(sentiment_data[:-3]) if len(sentiment_data) > 3 else sentiment_data[0]
            
            trend_direction = "increasing" if recent_sentiment > older_sentiment else "decreasing"
            trend_strength = abs(recent_sentiment - older_sentiment)
            
            if trend_strength > 0.1:  # Significant trend
                insight = MemoryInsight(
                    insight_type="sentiment_trend",
                    confidence=min(trend_strength * 2, 1.0),
                    description=f"Sentiment trend is {trend_direction} with strength {trend_strength:.2f}",
                    supporting_memories=[m.id for m in memories if m.memory_type == 'news'][:5],
                    actionable_signals=[f"{trend_direction}_sentiment"],
                    risk_assessment={
                        'trend_risk': trend_strength,
                        'volatility_risk': statistics.stdev(sentiment_data) if len(sentiment_data) > 1 else 0.0
                    }
                )
                
                return insight
            
        except Exception as e:
            logger.error(f"❌ Error analyzing sentiment trends: {e}")
        
        return None
    
    async def _analyze_volume_patterns(self, memories: List[VectorMemory]) -> Optional[MemoryInsight]:
        """Analyze volume patterns in trading signals"""
        # Implementation for volume pattern analysis
        # This would analyze volume-related metadata in trading signals
        return None
    
    async def _analyze_signal_convergence(self, memories: List[VectorMemory]) -> Optional[MemoryInsight]:
        """Analyze convergence of trading signals"""
        # Implementation for signal convergence analysis
        # This would look for multiple signals pointing in the same direction
        return None
    
    async def _analyze_risk_patterns(self, memories: List[VectorMemory], context: Dict[str, Any]) -> Optional[MemoryInsight]:
        """Analyze risk patterns in historical data"""
        # Implementation for risk pattern analysis
        # This would identify recurring risk scenarios
        return None
    
    async def _analyze_news_impact(self, memories: List[VectorMemory]) -> Optional[MemoryInsight]:
        """Analyze news impact on market movements"""
        # Implementation for news impact analysis
        # This would correlate news events with subsequent market movements
        return None
    
    async def _analyze_regime_patterns(self, memories: List[VectorMemory]) -> Dict[str, Any]:
        """Analyze market regime patterns"""
        # Implementation for regime pattern analysis
        return {}
    
    async def _assess_current_market_state(self, symbol: str) -> Dict[str, Any]:
        """Assess current market state"""
        # Implementation for current market state assessment
        return {}
    
    async def _predict_regime_transition(self, 
                                       regime_patterns: Dict[str, Any],
                                       current_state: Dict[str, Any],
                                       horizon_days: int) -> Dict[str, Any]:
        """Predict regime transition"""
        # Implementation for regime transition prediction
        return {}
    
    async def _analyze_cross_symbol_patterns(self,
                                           symbol1: str,
                                           symbol2: str,
                                           min_confidence: float) -> Optional[Dict[str, Any]]:
        """Analyze patterns between two symbols"""
        # Implementation for cross-symbol pattern analysis
        return None

# Integration with OVERMIND Brain Manager
class OVERMINDMemoryIntegration:
    """Integration layer for OVERMIND Brain Manager to use Enhanced Memory Retrieval"""

    def __init__(self, vector_manager: JinaVectorMemoryManager):
        self.enhanced_retrieval = EnhancedMemoryRetrieval(vector_manager)

    async def get_trading_predictions(self, symbol: str, current_market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive trading predictions for a symbol"""
        try:
            # Find predictive patterns
            patterns = await self.enhanced_retrieval.find_predictive_patterns(
                current_market_data,
                symbol
            )

            # Analyze temporal patterns
            temporal_patterns = await self.enhanced_retrieval.analyze_temporal_patterns(symbol)

            # Generate insights
            insights = await self.enhanced_retrieval.generate_memory_insights(symbol, current_market_data)

            # Predict market regime
            regime_prediction = await self.enhanced_retrieval.predict_market_regime(symbol)

            return {
                'symbol': symbol,
                'predictive_patterns': [asdict(p) for p in patterns],
                'temporal_patterns': [asdict(p) for p in temporal_patterns],
                'insights': [asdict(i) for i in insights],
                'regime_prediction': regime_prediction,
                'confidence': max([p.confidence for p in patterns] + [0.0]),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Error getting trading predictions: {e}")
            return {'symbol': symbol, 'error': str(e)}

    async def find_market_opportunities(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Find market opportunities across multiple symbols"""
        try:
            opportunities = []

            # Find arbitrage opportunities
            arbitrage_ops = await self.enhanced_retrieval.find_arbitrage_opportunities(symbols)
            opportunities.extend(arbitrage_ops)

            # Find individual symbol opportunities
            for symbol in symbols:
                current_data = {'symbol': symbol, 'analysis_type': 'opportunity_scan'}
                predictions = await self.get_trading_predictions(symbol, current_data)

                if predictions.get('confidence', 0) > 0.7:
                    opportunities.append({
                        'type': 'individual_opportunity',
                        'symbol': symbol,
                        'predictions': predictions,
                        'opportunity_score': predictions['confidence']
                    })

            # Sort by opportunity score
            opportunities.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)

            return opportunities

        except Exception as e:
            logger.error(f"❌ Error finding market opportunities: {e}")
            return []
