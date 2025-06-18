"""THE OVERMIND PROTOCOL - Market Analyzer
AI-powered market data analysis with pattern recognition and trend analysis.
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)

@dataclass
class MarketAnalysis:
    """Comprehensive market analysis result"""
    symbol: str
    trend_direction: str  # BULLISH, BEARISH, SIDEWAYS
    trend_strength: float  # 0.0 (weak) to 1.0 (strong)
    support_levels: List[float]
    resistance_levels: List[float]
    volatility_score: float
    momentum_score: float
    volume_analysis: Dict[str, Any]
    technical_indicators: Dict[str, float]
    pattern_signals: List[str]
    market_sentiment: str  # POSITIVE, NEGATIVE, NEUTRAL
    confidence_score: float
    analysis_timestamp: str

class MarketAnalyzer:
    """AI-powered market analyzer for THE OVERMIND PROTOCOL"""
    
    def __init__(self, 
                 lookback_periods: int = 20,
                 volatility_window: int = 14,
                 momentum_window: int = 10):
        """
        Initialize market analyzer
        
        Args:
            lookback_periods: Number of periods for analysis
            volatility_window: Window for volatility calculation
            momentum_window: Window for momentum calculation
        """
        self.lookback_periods = lookback_periods
        self.volatility_window = volatility_window
        self.momentum_window = momentum_window
        
        logger.info("📊 Market Analyzer initialized")
    
    async def analyze_market(self, 
                           current_data: Dict[str, Any],
                           historical_data: Optional[List[Dict[str, Any]]] = None,
                           additional_context: Optional[Dict[str, Any]] = None) -> MarketAnalysis:
        """
        Comprehensive market analysis
        
        Args:
            current_data: Current market data
            historical_data: Historical price/volume data
            additional_context: Additional market context
            
        Returns:
            Market analysis result
        """
        try:
            symbol = current_data.get("symbol", "unknown")
            current_price = float(current_data.get("price", 0))
            
            # Prepare historical prices
            prices = self._extract_prices(historical_data) if historical_data else [current_price]
            volumes = self._extract_volumes(historical_data) if historical_data else [current_data.get("volume", 0)]
            
            # Perform analysis components
            trend_analysis = self._analyze_trend(prices)
            support_resistance = self._find_support_resistance(prices)
            volatility_analysis = self._analyze_volatility(prices)
            momentum_analysis = self._analyze_momentum(prices)
            volume_analysis = self._analyze_volume(volumes, current_data)
            technical_indicators = self._calculate_technical_indicators(prices, volumes)
            pattern_signals = self._detect_patterns(prices)
            sentiment_analysis = self._analyze_sentiment(current_data, additional_context)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(
                trend_analysis, volatility_analysis, len(prices)
            )
            
            # Create analysis result
            analysis = MarketAnalysis(
                symbol=symbol,
                trend_direction=trend_analysis["direction"],
                trend_strength=trend_analysis["strength"],
                support_levels=support_resistance["support"],
                resistance_levels=support_resistance["resistance"],
                volatility_score=volatility_analysis["score"],
                momentum_score=momentum_analysis["score"],
                volume_analysis=volume_analysis,
                technical_indicators=technical_indicators,
                pattern_signals=pattern_signals,
                market_sentiment=sentiment_analysis["sentiment"],
                confidence_score=confidence,
                analysis_timestamp=datetime.utcnow().isoformat()
            )
            
            logger.info(f"📊 Market Analysis: {symbol} - {trend_analysis['direction']} "
                       f"(Strength: {trend_analysis['strength']:.2f}, Confidence: {confidence:.2f})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Market analysis failed: {e}")
            # Return default analysis
            return MarketAnalysis(
                symbol=current_data.get("symbol", "unknown"),
                trend_direction="SIDEWAYS",
                trend_strength=0.0,
                support_levels=[],
                resistance_levels=[],
                volatility_score=0.5,
                momentum_score=0.0,
                volume_analysis={},
                technical_indicators={},
                pattern_signals=[],
                market_sentiment="NEUTRAL",
                confidence_score=0.0,
                analysis_timestamp=datetime.utcnow().isoformat()
            )
    
    def _extract_prices(self, historical_data: List[Dict[str, Any]]) -> List[float]:
        """Extract price data from historical data"""
        prices = []
        for data in historical_data[-self.lookback_periods:]:
            price = data.get("price") or data.get("close") or data.get("last")
            if price is not None:
                prices.append(float(price))
        return prices
    
    def _extract_volumes(self, historical_data: List[Dict[str, Any]]) -> List[float]:
        """Extract volume data from historical data"""
        volumes = []
        for data in historical_data[-self.lookback_periods:]:
            volume = data.get("volume", 0)
            volumes.append(float(volume))
        return volumes
    
    def _analyze_trend(self, prices: List[float]) -> Dict[str, Any]:
        """Analyze price trend"""
        if len(prices) < 3:
            return {"direction": "SIDEWAYS", "strength": 0.0}
        
        # Calculate moving averages
        short_ma = statistics.mean(prices[-5:]) if len(prices) >= 5 else prices[-1]
        long_ma = statistics.mean(prices[-10:]) if len(prices) >= 10 else statistics.mean(prices)
        
        # Calculate trend direction
        if short_ma > long_ma * 1.02:  # 2% threshold
            direction = "BULLISH"
        elif short_ma < long_ma * 0.98:  # 2% threshold
            direction = "BEARISH"
        else:
            direction = "SIDEWAYS"
        
        # Calculate trend strength
        if len(prices) >= 5:
            price_changes = [(prices[i] - prices[i-1]) / prices[i-1] 
                           for i in range(1, len(prices))]
            
            # Count consecutive moves in same direction
            consecutive_moves = 0
            if price_changes:
                current_direction = 1 if price_changes[-1] > 0 else -1
                for change in reversed(price_changes):
                    if (change > 0 and current_direction > 0) or (change < 0 and current_direction < 0):
                        consecutive_moves += 1
                    else:
                        break
            
            strength = min(consecutive_moves / 5.0, 1.0)  # Normalize to 0-1
        else:
            strength = 0.0
        
        return {"direction": direction, "strength": strength}
    
    def _find_support_resistance(self, prices: List[float]) -> Dict[str, List[float]]:
        """Find support and resistance levels"""
        if len(prices) < 5:
            return {"support": [], "resistance": []}
        
        # Find local minima (support) and maxima (resistance)
        support_levels = []
        resistance_levels = []
        
        for i in range(2, len(prices) - 2):
            # Local minimum (support)
            if (prices[i] < prices[i-1] and prices[i] < prices[i-2] and
                prices[i] < prices[i+1] and prices[i] < prices[i+2]):
                support_levels.append(prices[i])
            
            # Local maximum (resistance)
            if (prices[i] > prices[i-1] and prices[i] > prices[i-2] and
                prices[i] > prices[i+1] and prices[i] > prices[i+2]):
                resistance_levels.append(prices[i])
        
        # Keep only the most significant levels (closest to current price)
        current_price = prices[-1]
        
        support_levels = sorted([s for s in support_levels if s < current_price], reverse=True)[:3]
        resistance_levels = sorted([r for r in resistance_levels if r > current_price])[:3]
        
        return {"support": support_levels, "resistance": resistance_levels}
    
    def _analyze_volatility(self, prices: List[float]) -> Dict[str, Any]:
        """Analyze price volatility"""
        if len(prices) < 2:
            return {"score": 0.5, "level": "UNKNOWN"}
        
        # Calculate returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                  for i in range(1, min(len(prices), self.volatility_window + 1))]
        
        if not returns:
            return {"score": 0.5, "level": "UNKNOWN"}
        
        # Calculate volatility (standard deviation of returns)
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        # Normalize volatility score (0-1)
        # Typical daily volatility ranges from 0.01 (1%) to 0.1 (10%)
        volatility_score = min(volatility / 0.05, 1.0)  # Normalize to 5% as max
        
        # Determine volatility level
        if volatility_score < 0.3:
            level = "LOW"
        elif volatility_score < 0.7:
            level = "MEDIUM"
        else:
            level = "HIGH"
        
        return {"score": volatility_score, "level": level, "raw_volatility": volatility}
    
    def _analyze_momentum(self, prices: List[float]) -> Dict[str, Any]:
        """Analyze price momentum"""
        if len(prices) < self.momentum_window:
            return {"score": 0.0, "direction": "NEUTRAL"}
        
        # Calculate momentum as rate of change
        current_price = prices[-1]
        past_price = prices[-self.momentum_window]
        
        momentum = (current_price - past_price) / past_price
        
        # Normalize momentum score (-1 to 1, then 0 to 1)
        momentum_score = (momentum + 1) / 2
        momentum_score = max(0, min(momentum_score, 1))
        
        # Determine momentum direction
        if momentum > 0.02:  # 2% threshold
            direction = "POSITIVE"
        elif momentum < -0.02:
            direction = "NEGATIVE"
        else:
            direction = "NEUTRAL"
        
        return {"score": momentum_score, "direction": direction, "raw_momentum": momentum}
    
    def _analyze_volume(self, volumes: List[float], current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trading volume"""
        if not volumes:
            return {"status": "NO_DATA"}
        
        current_volume = current_data.get("volume", 0)
        avg_volume = statistics.mean(volumes) if volumes else current_volume
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Determine volume status
        if volume_ratio > 1.5:
            status = "HIGH"
        elif volume_ratio < 0.5:
            status = "LOW"
        else:
            status = "NORMAL"
        
        return {
            "status": status,
            "current_volume": current_volume,
            "average_volume": avg_volume,
            "volume_ratio": volume_ratio
        }
    
    def _calculate_technical_indicators(self, prices: List[float], volumes: List[float]) -> Dict[str, float]:
        """Calculate basic technical indicators"""
        indicators = {}
        
        if len(prices) >= 5:
            # Simple Moving Averages
            indicators["sma_5"] = statistics.mean(prices[-5:])
            
        if len(prices) >= 10:
            indicators["sma_10"] = statistics.mean(prices[-10:])
            
        if len(prices) >= 20:
            indicators["sma_20"] = statistics.mean(prices[-20:])
        
        # RSI approximation (simplified)
        if len(prices) >= 14:
            gains = []
            losses = []
            
            for i in range(1, min(15, len(prices))):
                change = prices[-i] - prices[-i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = statistics.mean(gains) if gains else 0
            avg_loss = statistics.mean(losses) if losses else 0
            
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                indicators["rsi"] = rsi
        
        return indicators
    
    def _detect_patterns(self, prices: List[float]) -> List[str]:
        """Detect basic chart patterns"""
        patterns = []
        
        if len(prices) < 5:
            return patterns
        
        # Simple pattern detection
        recent_prices = prices[-5:]
        
        # Ascending pattern
        if all(recent_prices[i] >= recent_prices[i-1] for i in range(1, len(recent_prices))):
            patterns.append("ASCENDING_TREND")
        
        # Descending pattern
        elif all(recent_prices[i] <= recent_prices[i-1] for i in range(1, len(recent_prices))):
            patterns.append("DESCENDING_TREND")
        
        # Consolidation pattern
        elif max(recent_prices) - min(recent_prices) < statistics.mean(recent_prices) * 0.02:
            patterns.append("CONSOLIDATION")
        
        # Breakout detection
        if len(prices) >= 10:
            recent_range = max(prices[-5:]) - min(prices[-5:])
            historical_range = max(prices[-10:-5]) - min(prices[-10:-5])
            
            if recent_range > historical_range * 1.5:
                patterns.append("BREAKOUT")
        
        return patterns
    
    def _analyze_sentiment(self, current_data: Dict[str, Any], additional_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze market sentiment"""
        sentiment_score = 0.0
        factors = []
        
        # Price momentum sentiment
        price_change = current_data.get("price_change_24h", 0)
        if price_change > 0.05:  # 5% gain
            sentiment_score += 0.3
            factors.append("Strong price momentum")
        elif price_change < -0.05:  # 5% loss
            sentiment_score -= 0.3
            factors.append("Negative price momentum")
        
        # Volume sentiment
        volume_ratio = current_data.get("volume_ratio", 1.0)
        if volume_ratio > 1.5:
            sentiment_score += 0.2
            factors.append("High volume activity")
        elif volume_ratio < 0.5:
            sentiment_score -= 0.1
            factors.append("Low volume concern")
        
        # Additional context sentiment
        if additional_context:
            news_sentiment = additional_context.get("news_sentiment", 0)
            sentiment_score += news_sentiment * 0.3
            
            if additional_context.get("market_fear_greed"):
                fear_greed = additional_context["market_fear_greed"]
                if fear_greed > 70:
                    sentiment_score += 0.2
                elif fear_greed < 30:
                    sentiment_score -= 0.2
        
        # Determine overall sentiment
        if sentiment_score > 0.2:
            sentiment = "POSITIVE"
        elif sentiment_score < -0.2:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
        
        return {
            "sentiment": sentiment,
            "score": sentiment_score,
            "factors": factors
        }
    
    def _calculate_confidence(self, trend_analysis: Dict, volatility_analysis: Dict, data_points: int) -> float:
        """Calculate analysis confidence score"""
        confidence = 0.5  # Base confidence
        
        # Data quality factor
        if data_points >= 20:
            confidence += 0.3
        elif data_points >= 10:
            confidence += 0.2
        elif data_points >= 5:
            confidence += 0.1
        
        # Trend strength factor
        confidence += trend_analysis["strength"] * 0.2
        
        # Volatility factor (lower volatility = higher confidence)
        volatility_score = volatility_analysis.get("score", 0.5)
        confidence += (1 - volatility_score) * 0.1
        
        return min(confidence, 1.0)
