"""THE OVERMIND PROTOCOL - Real-time Market Sentiment Analysis
Advanced sentiment analysis combining social media, news, and market data
for comprehensive market sentiment assessment.
"""

import asyncio
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import hashlib

logger = logging.getLogger(__name__)

class SentimentScore(Enum):
    """Sentiment score categories"""
    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2

class DataSource(Enum):
    """Data sources for sentiment analysis"""
    TWITTER = "twitter"
    REDDIT = "reddit"
    NEWS = "news"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    MARKET_DATA = "market_data"
    SOCIAL_VOLUME = "social_volume"

@dataclass
class SentimentData:
    """Individual sentiment data point"""
    id: str
    source: DataSource
    content: str
    sentiment_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    metadata: Dict[str, Any]
    keywords: List[str]
    influence_score: float  # 0.0 to 1.0 (how influential the source is)

@dataclass
class AggregatedSentiment:
    """Aggregated sentiment analysis result"""
    symbol: str
    overall_sentiment: float  # -1.0 to 1.0
    sentiment_category: SentimentScore
    confidence: float
    data_points: int
    source_breakdown: Dict[DataSource, float]
    trending_keywords: List[Tuple[str, int]]  # (keyword, frequency)
    sentiment_trend: List[Tuple[datetime, float]]  # Historical trend
    metadata: Dict[str, Any]
    analysis_timestamp: datetime

@dataclass
class MarketSentimentSignal:
    """Trading signal based on sentiment analysis"""
    symbol: str
    signal_type: str  # BUY/SELL/HOLD
    strength: float  # 0.0 to 1.0
    sentiment_score: float
    confidence: float
    reasoning: str
    supporting_data: List[SentimentData]
    timestamp: datetime

class SentimentAnalyzer:
    """Advanced sentiment analysis engine"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sentiment_history = {}  # symbol -> List[SentimentData]
        self.keyword_patterns = self._initialize_keyword_patterns()
        self.sentiment_models = {}
        self.data_sources = {}
        
    def _initialize_keyword_patterns(self) -> Dict[str, Dict[str, float]]:
        """Initialize keyword patterns for sentiment analysis"""
        return {
            "bullish": {
                "moon": 0.8, "pump": 0.7, "bullish": 0.9, "buy": 0.6,
                "hodl": 0.5, "diamond hands": 0.8, "to the moon": 0.9,
                "rocket": 0.7, "green": 0.4, "up": 0.3, "rise": 0.5,
                "breakout": 0.7, "rally": 0.8, "surge": 0.7
            },
            "bearish": {
                "dump": -0.7, "bearish": -0.9, "sell": -0.6, "crash": -0.9,
                "red": -0.4, "down": -0.3, "fall": -0.5, "drop": -0.6,
                "correction": -0.5, "dip": -0.4, "decline": -0.6,
                "bear market": -0.8, "panic": -0.8, "fear": -0.6
            },
            "neutral": {
                "hold": 0.0, "wait": 0.0, "sideways": 0.0, "consolidation": 0.0,
                "range": 0.0, "stable": 0.0, "flat": 0.0
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize sentiment analyzer"""
        try:
            # Initialize data source connections
            await self._initialize_data_sources()
            
            # Load or initialize sentiment models
            await self._initialize_sentiment_models()
            
            logger.info("Sentiment analyzer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {e}")
            return False
    
    async def _initialize_data_sources(self):
        """Initialize connections to data sources"""
        # Twitter API (would require actual API keys)
        if self.config.get("twitter_api_key"):
            self.data_sources[DataSource.TWITTER] = {
                "enabled": True,
                "api_key": self.config["twitter_api_key"],
                "rate_limit": 100  # requests per hour
            }
        
        # Reddit API
        if self.config.get("reddit_client_id"):
            self.data_sources[DataSource.REDDIT] = {
                "enabled": True,
                "client_id": self.config["reddit_client_id"],
                "rate_limit": 60
            }
        
        # News API
        if self.config.get("news_api_key"):
            self.data_sources[DataSource.NEWS] = {
                "enabled": True,
                "api_key": self.config["news_api_key"],
                "rate_limit": 1000
            }
        
        # For demo purposes, enable mock data sources
        for source in DataSource:
            if source not in self.data_sources:
                self.data_sources[source] = {
                    "enabled": True,
                    "mock": True,
                    "rate_limit": 100
                }
    
    async def _initialize_sentiment_models(self):
        """Initialize sentiment analysis models"""
        # In a real implementation, this would load pre-trained models
        # For now, use rule-based sentiment analysis
        self.sentiment_models["rule_based"] = {
            "type": "rule_based",
            "keywords": self.keyword_patterns,
            "enabled": True
        }
        
        # Mock ML model
        self.sentiment_models["ml_model"] = {
            "type": "machine_learning",
            "model_path": "mock_sentiment_model.pkl",
            "enabled": False  # Disabled for demo
        }
    
    async def analyze_symbol_sentiment(self, symbol: str, hours_back: int = 24) -> AggregatedSentiment:
        """Analyze sentiment for a specific symbol"""
        try:
            # Collect sentiment data from all sources
            sentiment_data = await self._collect_sentiment_data(symbol, hours_back)
            
            if not sentiment_data:
                return self._create_neutral_sentiment(symbol)
            
            # Aggregate sentiment scores
            overall_sentiment = self._calculate_weighted_sentiment(sentiment_data)
            sentiment_category = self._categorize_sentiment(overall_sentiment)
            confidence = self._calculate_confidence(sentiment_data)
            
            # Analyze source breakdown
            source_breakdown = self._analyze_source_breakdown(sentiment_data)
            
            # Extract trending keywords
            trending_keywords = self._extract_trending_keywords(sentiment_data)
            
            # Build sentiment trend
            sentiment_trend = self._build_sentiment_trend(symbol, hours_back)
            
            return AggregatedSentiment(
                symbol=symbol,
                overall_sentiment=overall_sentiment,
                sentiment_category=sentiment_category,
                confidence=confidence,
                data_points=len(sentiment_data),
                source_breakdown=source_breakdown,
                trending_keywords=trending_keywords,
                sentiment_trend=sentiment_trend,
                metadata={
                    "analysis_period_hours": hours_back,
                    "sources_analyzed": list(source_breakdown.keys()),
                    "total_influence_score": sum(data.influence_score for data in sentiment_data)
                },
                analysis_timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment for {symbol}: {e}")
            return self._create_neutral_sentiment(symbol)
    
    async def _collect_sentiment_data(self, symbol: str, hours_back: int) -> List[SentimentData]:
        """Collect sentiment data from all enabled sources"""
        all_sentiment_data = []
        
        # Collect from each enabled source
        for source, config in self.data_sources.items():
            if config.get("enabled", False):
                try:
                    if config.get("mock", False):
                        # Generate mock data for demo
                        source_data = await self._generate_mock_sentiment_data(symbol, source, hours_back)
                    else:
                        # Collect real data (would implement actual API calls)
                        source_data = await self._collect_real_sentiment_data(symbol, source, hours_back)
                    
                    all_sentiment_data.extend(source_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to collect sentiment from {source}: {e}")
        
        return all_sentiment_data
    
    async def _generate_mock_sentiment_data(self, symbol: str, source: DataSource, hours_back: int) -> List[SentimentData]:
        """Generate mock sentiment data for demonstration"""
        import random
        
        mock_data = []
        num_points = random.randint(5, 20)  # Random number of data points
        
        for i in range(num_points):
            # Generate mock content based on source
            if source == DataSource.TWITTER:
                content = f"${symbol} looking {'bullish' if random.random() > 0.5 else 'bearish'} today! #crypto"
            elif source == DataSource.REDDIT:
                content = f"Discussion about {symbol} - {'moon' if random.random() > 0.6 else 'dip'} incoming?"
            elif source == DataSource.NEWS:
                content = f"{symbol} shows {'positive' if random.random() > 0.4 else 'negative'} market indicators"
            else:
                content = f"Market sentiment for {symbol} is {'optimistic' if random.random() > 0.5 else 'cautious'}"
            
            # Calculate sentiment score based on content
            sentiment_score = self._analyze_text_sentiment(content)
            
            # Generate timestamp within the specified period
            hours_ago = random.uniform(0, hours_back)
            timestamp = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            
            # Generate influence score based on source
            influence_scores = {
                DataSource.TWITTER: random.uniform(0.3, 0.8),
                DataSource.REDDIT: random.uniform(0.4, 0.7),
                DataSource.NEWS: random.uniform(0.7, 1.0),
                DataSource.TELEGRAM: random.uniform(0.2, 0.6),
                DataSource.DISCORD: random.uniform(0.2, 0.5),
                DataSource.MARKET_DATA: random.uniform(0.8, 1.0),
                DataSource.SOCIAL_VOLUME: random.uniform(0.3, 0.6)
            }
            
            mock_data.append(SentimentData(
                id=f"mock_{source.value}_{i}_{int(timestamp.timestamp())}",
                source=source,
                content=content,
                sentiment_score=sentiment_score,
                confidence=random.uniform(0.6, 0.9),
                timestamp=timestamp,
                metadata={"mock": True, "source_specific": f"{source.value}_data"},
                keywords=self._extract_keywords(content),
                influence_score=influence_scores.get(source, 0.5)
            ))
        
        return mock_data
    
    async def _collect_real_sentiment_data(self, symbol: str, source: DataSource, hours_back: int) -> List[SentimentData]:
        """Collect real sentiment data from APIs (placeholder)"""
        # This would implement actual API calls to Twitter, Reddit, News APIs, etc.
        # For now, return empty list
        return []
    
    def _analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using rule-based approach"""
        text_lower = text.lower()
        sentiment_score = 0.0
        word_count = 0
        
        # Check for keyword patterns
        for category, keywords in self.keyword_patterns.items():
            for keyword, weight in keywords.items():
                if keyword in text_lower:
                    sentiment_score += weight
                    word_count += 1
        
        # Normalize score
        if word_count > 0:
            sentiment_score = sentiment_score / word_count
        
        # Clamp to [-1, 1] range
        return max(-1.0, min(1.0, sentiment_score))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        text_lower = text.lower()
        keywords = []
        
        # Extract known sentiment keywords
        for category, keyword_dict in self.keyword_patterns.items():
            for keyword in keyword_dict.keys():
                if keyword in text_lower:
                    keywords.append(keyword)
        
        # Extract crypto-related terms
        crypto_terms = ["btc", "eth", "sol", "crypto", "blockchain", "defi", "nft"]
        for term in crypto_terms:
            if term in text_lower:
                keywords.append(term)
        
        return list(set(keywords))  # Remove duplicates
    
    def _calculate_weighted_sentiment(self, sentiment_data: List[SentimentData]) -> float:
        """Calculate weighted average sentiment"""
        if not sentiment_data:
            return 0.0
        
        total_weighted_sentiment = 0.0
        total_weight = 0.0
        
        for data in sentiment_data:
            # Weight by confidence and influence score
            weight = data.confidence * data.influence_score
            total_weighted_sentiment += data.sentiment_score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return total_weighted_sentiment / total_weight
    
    def _categorize_sentiment(self, sentiment_score: float) -> SentimentScore:
        """Categorize sentiment score"""
        if sentiment_score <= -0.6:
            return SentimentScore.VERY_BEARISH
        elif sentiment_score <= -0.2:
            return SentimentScore.BEARISH
        elif sentiment_score >= 0.6:
            return SentimentScore.VERY_BULLISH
        elif sentiment_score >= 0.2:
            return SentimentScore.BULLISH
        else:
            return SentimentScore.NEUTRAL
    
    def _calculate_confidence(self, sentiment_data: List[SentimentData]) -> float:
        """Calculate overall confidence in sentiment analysis"""
        if not sentiment_data:
            return 0.0
        
        # Average confidence weighted by influence
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for data in sentiment_data:
            weight = data.influence_score
            total_weighted_confidence += data.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        base_confidence = total_weighted_confidence / total_weight
        
        # Adjust confidence based on data volume
        volume_factor = min(1.0, len(sentiment_data) / 10.0)  # More data = higher confidence
        
        return base_confidence * volume_factor
    
    def _analyze_source_breakdown(self, sentiment_data: List[SentimentData]) -> Dict[DataSource, float]:
        """Analyze sentiment breakdown by source"""
        source_sentiments = {}
        source_counts = {}
        
        for data in sentiment_data:
            if data.source not in source_sentiments:
                source_sentiments[data.source] = 0.0
                source_counts[data.source] = 0
            
            source_sentiments[data.source] += data.sentiment_score
            source_counts[data.source] += 1
        
        # Calculate average sentiment per source
        breakdown = {}
        for source, total_sentiment in source_sentiments.items():
            count = source_counts[source]
            breakdown[source] = total_sentiment / count if count > 0 else 0.0
        
        return breakdown
    
    def _extract_trending_keywords(self, sentiment_data: List[SentimentData]) -> List[Tuple[str, int]]:
        """Extract trending keywords from sentiment data"""
        keyword_counts = {}
        
        for data in sentiment_data:
            for keyword in data.keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Sort by frequency and return top 10
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_keywords[:10]
    
    def _build_sentiment_trend(self, symbol: str, hours_back: int) -> List[Tuple[datetime, float]]:
        """Build sentiment trend over time"""
        # For demo, generate mock trend data
        trend = []
        current_time = datetime.now(timezone.utc)
        
        for i in range(hours_back):
            timestamp = current_time - timedelta(hours=i)
            # Generate mock sentiment trend
            import random
            sentiment = random.uniform(-0.5, 0.5)
            trend.append((timestamp, sentiment))
        
        return list(reversed(trend))  # Chronological order
    
    def _create_neutral_sentiment(self, symbol: str) -> AggregatedSentiment:
        """Create neutral sentiment when no data is available"""
        return AggregatedSentiment(
            symbol=symbol,
            overall_sentiment=0.0,
            sentiment_category=SentimentScore.NEUTRAL,
            confidence=0.1,
            data_points=0,
            source_breakdown={},
            trending_keywords=[],
            sentiment_trend=[],
            metadata={"no_data": True},
            analysis_timestamp=datetime.now(timezone.utc)
        )
    
    async def generate_sentiment_signal(self, symbol: str) -> MarketSentimentSignal:
        """Generate trading signal based on sentiment analysis"""
        try:
            # Analyze current sentiment
            sentiment_analysis = await self.analyze_symbol_sentiment(symbol)
            
            # Generate signal based on sentiment
            signal_type = "HOLD"  # Default
            strength = 0.0
            reasoning = "Neutral sentiment"
            
            if sentiment_analysis.sentiment_category == SentimentScore.VERY_BULLISH:
                signal_type = "BUY"
                strength = 0.8
                reasoning = "Very bullish sentiment detected"
            elif sentiment_analysis.sentiment_category == SentimentScore.BULLISH:
                signal_type = "BUY"
                strength = 0.6
                reasoning = "Bullish sentiment detected"
            elif sentiment_analysis.sentiment_category == SentimentScore.VERY_BEARISH:
                signal_type = "SELL"
                strength = 0.8
                reasoning = "Very bearish sentiment detected"
            elif sentiment_analysis.sentiment_category == SentimentScore.BEARISH:
                signal_type = "SELL"
                strength = 0.6
                reasoning = "Bearish sentiment detected"
            
            # Adjust strength based on confidence and data volume
            strength *= sentiment_analysis.confidence
            if sentiment_analysis.data_points < 5:
                strength *= 0.5  # Reduce strength for low data volume
            
            return MarketSentimentSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                sentiment_score=sentiment_analysis.overall_sentiment,
                confidence=sentiment_analysis.confidence,
                reasoning=reasoning,
                supporting_data=[],  # Could include top sentiment data points
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Failed to generate sentiment signal for {symbol}: {e}")
            return MarketSentimentSignal(
                symbol=symbol,
                signal_type="HOLD",
                strength=0.0,
                sentiment_score=0.0,
                confidence=0.0,
                reasoning=f"Error: {str(e)}",
                supporting_data=[],
                timestamp=datetime.now(timezone.utc)
            )
    
    async def get_sentiment_stats(self) -> Dict[str, Any]:
        """Get sentiment analyzer statistics"""
        try:
            total_sources = len(self.data_sources)
            enabled_sources = sum(1 for config in self.data_sources.values() if config.get("enabled", False))
            
            return {
                "total_sources": total_sources,
                "enabled_sources": enabled_sources,
                "sentiment_models": list(self.sentiment_models.keys()),
                "keyword_patterns": len(self.keyword_patterns),
                "symbols_tracked": len(self.sentiment_history)
            }
            
        except Exception as e:
            logger.error(f"Failed to get sentiment stats: {e}")
            return {"error": str(e)}
