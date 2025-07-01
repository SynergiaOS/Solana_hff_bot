#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Market Regime Detector
Advanced multi-indicator market regime detection for optimal capital allocation
"""

import numpy as np
import pandas as pd
import asyncio
import aiohttp
import json
import redis
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('MarketRegimeDetector')

class MarketRegime(Enum):
    """Market regime classifications"""
    BULL_STRONG = "bull_strong"      # Strong uptrend, high momentum
    BULL_WEAK = "bull_weak"          # Weak uptrend, consolidation
    BEAR_STRONG = "bear_strong"      # Strong downtrend, high selling
    BEAR_WEAK = "bear_weak"          # Weak downtrend, oversold bounce
    SIDEWAYS = "sideways"            # Range-bound, low directional bias
    HIGH_VOLATILITY = "high_volatility"  # High volatility, uncertain direction
    CRASH = "crash"                  # Extreme downward movement

@dataclass
class MarketData:
    """Market data structure"""
    timestamp: float
    price: float
    volume_24h: float
    price_change_1h: float
    price_change_24h: float
    price_change_7d: float
    market_cap: float
    volatility: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    bb_position: Optional[float] = None  # Bollinger Band position (0-1)

@dataclass
class RegimeAnalysis:
    """Market regime analysis result"""
    regime: MarketRegime
    confidence: float
    regime_strength: float
    allocation_multiplier: float
    risk_level: str
    indicators: Dict[str, float]
    reasoning: str
    timestamp: float

class MarketRegimeDetector:
    """
    Advanced Market Regime Detector
    
    Uses multiple technical indicators and market metrics to classify
    current market conditions into distinct regimes for optimal trading
    """
    
    def __init__(self):
        """Initialize Market Regime Detector"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # API configuration
        self.helius_api_key = "edbcd361-78a0-4998-bd1e-8d4666722f82"
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
        # Regime detection parameters
        self.regime_thresholds = {
            'bull_strong': {'price_change_24h': 8.0, 'volume_spike': 2.0, 'rsi': 70},
            'bull_weak': {'price_change_24h': 2.0, 'volume_spike': 1.2, 'rsi': 60},
            'bear_strong': {'price_change_24h': -8.0, 'volume_spike': 2.0, 'rsi': 30},
            'bear_weak': {'price_change_24h': -2.0, 'volume_spike': 1.2, 'rsi': 40},
            'sideways': {'price_change_24h': 2.0, 'volatility': 0.3},
            'high_volatility': {'volatility': 0.8, 'price_change_1h': 5.0},
            'crash': {'price_change_24h': -15.0, 'volume_spike': 3.0}
        }
        
        # Allocation multipliers for each regime
        self.allocation_multipliers = {
            MarketRegime.BULL_STRONG: 1.5,      # Increase allocation in strong bull
            MarketRegime.BULL_WEAK: 1.2,        # Slight increase in weak bull
            MarketRegime.BEAR_STRONG: 0.3,      # Drastically reduce in strong bear
            MarketRegime.BEAR_WEAK: 0.6,        # Reduce in weak bear
            MarketRegime.SIDEWAYS: 0.8,         # Conservative in sideways
            MarketRegime.HIGH_VOLATILITY: 0.4,  # Very conservative in high vol
            MarketRegime.CRASH: 0.1             # Minimal allocation in crash
        }
        
        # Historical data cache
        self.price_history = []
        self.volume_history = []
        self.regime_history = []
        
        logger.info("📊 Market Regime Detector initialized")
        logger.info(f"🎯 Monitoring {len(self.regime_thresholds)} regime types")
        logger.info("📈 Multi-indicator analysis enabled")
    
    async def detect_current_regime(self, symbol: str = "SOL") -> RegimeAnalysis:
        """
        Detect current market regime using multi-indicator analysis
        """
        try:
            logger.info(f"🔍 Detecting market regime for {symbol}...")
            
            # Fetch comprehensive market data
            market_data = await self.fetch_market_data(symbol)
            
            # Calculate technical indicators
            indicators = await self.calculate_indicators(market_data)
            
            # Analyze regime using multiple factors
            regime_analysis = self.analyze_regime(market_data, indicators)
            
            # Store in Redis for other modules
            await self.store_regime_analysis(regime_analysis)
            
            logger.info(f"📊 Market regime detected: {regime_analysis.regime.value}")
            logger.info(f"   Confidence: {regime_analysis.confidence:.2f}")
            logger.info(f"   Allocation Multiplier: {regime_analysis.allocation_multiplier:.2f}x")
            logger.info(f"   Risk Level: {regime_analysis.risk_level}")
            
            return regime_analysis
            
        except Exception as e:
            logger.error(f"❌ Error detecting market regime: {e}")
            return self.create_fallback_analysis()
    
    async def fetch_market_data(self, symbol: str) -> MarketData:
        """Fetch comprehensive market data from multiple sources"""
        try:
            # Fetch from CoinGecko (primary source)
            coingecko_data = await self.fetch_coingecko_data(symbol)
            
            # Fetch additional data from Helius if available
            helius_data = await self.fetch_helius_data(symbol)
            
            # Combine data sources
            market_data = self.combine_market_data(coingecko_data, helius_data)
            
            # Update historical data
            self.update_historical_data(market_data)
            
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Error fetching market data: {e}")
            return self.create_fallback_market_data()
    
    async def fetch_coingecko_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data from CoinGecko API"""
        try:
            # Map symbol to CoinGecko ID
            coin_id = self.get_coingecko_id(symbol)
            
            async with aiohttp.ClientSession() as session:
                # Fetch current price and market data
                url = f"{self.coingecko_base_url}/coins/{coin_id}"
                params = {
                    'localization': 'false',
                    'tickers': 'false',
                    'market_data': 'true',
                    'community_data': 'false',
                    'developer_data': 'false'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self.parse_coingecko_data(data)
                    else:
                        logger.warning(f"⚠️ CoinGecko API error: {response.status}")
                        return {}
                        
        except Exception as e:
            logger.error(f"❌ CoinGecko fetch error: {e}")
            return {}
    
    async def fetch_helius_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch additional data from Helius API"""
        try:
            # Helius integration for Solana-specific data
            # For now, return empty dict - can be expanded later
            return {}
            
        except Exception as e:
            logger.error(f"❌ Helius fetch error: {e}")
            return {}
    
    def get_coingecko_id(self, symbol: str) -> str:
        """Map trading symbol to CoinGecko ID"""
        symbol_map = {
            'SOL': 'solana',
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'JTO': 'jito-governance-token',
            'RAY': 'raydium',
            'JUP': 'jupiter-exchange-solana',
            'BONK': 'bonk',
            'WIF': 'dogwifcoin'
        }
        return symbol_map.get(symbol.upper(), 'solana')
    
    def parse_coingecko_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CoinGecko API response"""
        try:
            market_data = data.get('market_data', {})
            
            return {
                'price': market_data.get('current_price', {}).get('usd', 0.0),
                'volume_24h': market_data.get('total_volume', {}).get('usd', 0.0),
                'market_cap': market_data.get('market_cap', {}).get('usd', 0.0),
                'price_change_1h': market_data.get('price_change_percentage_1h_in_currency', {}).get('usd', 0.0),
                'price_change_24h': market_data.get('price_change_percentage_24h_in_currency', {}).get('usd', 0.0),
                'price_change_7d': market_data.get('price_change_percentage_7d_in_currency', {}).get('usd', 0.0),
                'volatility': abs(market_data.get('price_change_percentage_24h_in_currency', {}).get('usd', 0.0)) / 100.0
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing CoinGecko data: {e}")
            return {}
    
    def combine_market_data(self, coingecko_data: Dict[str, Any], helius_data: Dict[str, Any]) -> MarketData:
        """Combine data from multiple sources"""
        return MarketData(
            timestamp=time.time(),
            price=coingecko_data.get('price', 100.0),
            volume_24h=coingecko_data.get('volume_24h', 1000000.0),
            price_change_1h=coingecko_data.get('price_change_1h', 0.0),
            price_change_24h=coingecko_data.get('price_change_24h', 0.0),
            price_change_7d=coingecko_data.get('price_change_7d', 0.0),
            market_cap=coingecko_data.get('market_cap', 10000000.0),
            volatility=coingecko_data.get('volatility', 0.3)
        )
    
    async def calculate_indicators(self, market_data: MarketData) -> Dict[str, float]:
        """Calculate technical indicators"""
        indicators = {}
        
        try:
            # RSI calculation (simplified)
            if len(self.price_history) >= 14:
                indicators['rsi'] = self.calculate_rsi()
            else:
                indicators['rsi'] = 50.0  # Neutral default
            
            # Volume spike detection
            if len(self.volume_history) >= 7:
                avg_volume = np.mean(self.volume_history[-7:])
                indicators['volume_spike'] = market_data.volume_24h / max(avg_volume, 1.0)
            else:
                indicators['volume_spike'] = 1.0
            
            # Volatility indicator
            indicators['volatility'] = market_data.volatility
            
            # Momentum indicator
            indicators['momentum'] = market_data.price_change_24h
            
            # Fear & Greed proxy
            indicators['fear_greed'] = self.calculate_fear_greed_proxy(market_data)
            
            logger.info(f"📊 Technical indicators calculated: RSI={indicators['rsi']:.1f}, Vol Spike={indicators['volume_spike']:.2f}x")
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error calculating indicators: {e}")
            return {'rsi': 50.0, 'volume_spike': 1.0, 'volatility': 0.3, 'momentum': 0.0, 'fear_greed': 50.0}
    
    def calculate_rsi(self, period: int = 14) -> float:
        """Calculate RSI indicator"""
        try:
            if len(self.price_history) < period:
                return 50.0
            
            prices = np.array(self.price_history[-period-1:])
            deltas = np.diff(prices)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return max(0.0, min(100.0, rsi))
            
        except Exception as e:
            logger.error(f"❌ RSI calculation error: {e}")
            return 50.0
    
    def calculate_fear_greed_proxy(self, market_data: MarketData) -> float:
        """Calculate Fear & Greed proxy based on market metrics"""
        try:
            # Combine multiple factors for fear/greed score
            price_momentum = max(-50, min(50, market_data.price_change_24h * 2))  # -50 to +50
            volatility_fear = max(-25, min(0, (0.5 - market_data.volatility) * 50))  # Lower vol = less fear
            
            # Base score of 50 (neutral) + momentum + volatility adjustment
            fear_greed = 50 + price_momentum + volatility_fear
            
            return max(0.0, min(100.0, fear_greed))
            
        except Exception as e:
            logger.error(f"❌ Fear & Greed calculation error: {e}")
            return 50.0
    
    def analyze_regime(self, market_data: MarketData, indicators: Dict[str, float]) -> RegimeAnalysis:
        """Analyze market regime using multi-factor approach"""
        try:
            # Score each regime based on current conditions
            regime_scores = {}
            
            # Bull Strong: Strong upward momentum + high volume + high RSI
            regime_scores[MarketRegime.BULL_STRONG] = self.score_bull_strong(market_data, indicators)
            
            # Bull Weak: Moderate upward momentum + normal volume
            regime_scores[MarketRegime.BULL_WEAK] = self.score_bull_weak(market_data, indicators)
            
            # Bear Strong: Strong downward momentum + high volume + low RSI
            regime_scores[MarketRegime.BEAR_STRONG] = self.score_bear_strong(market_data, indicators)
            
            # Bear Weak: Moderate downward momentum + normal volume
            regime_scores[MarketRegime.BEAR_WEAK] = self.score_bear_weak(market_data, indicators)
            
            # Sideways: Low momentum + low volatility
            regime_scores[MarketRegime.SIDEWAYS] = self.score_sideways(market_data, indicators)
            
            # High Volatility: High volatility regardless of direction
            regime_scores[MarketRegime.HIGH_VOLATILITY] = self.score_high_volatility(market_data, indicators)
            
            # Crash: Extreme downward movement + panic selling
            regime_scores[MarketRegime.CRASH] = self.score_crash(market_data, indicators)
            
            # Select regime with highest score
            best_regime = max(regime_scores, key=regime_scores.get)
            confidence = regime_scores[best_regime]
            
            # Calculate regime strength and allocation multiplier
            regime_strength = min(1.0, confidence / 0.8)  # Normalize to 0-1
            allocation_multiplier = self.allocation_multipliers[best_regime]
            
            # Determine risk level
            risk_level = self.get_risk_level(best_regime, confidence)
            
            # Generate reasoning
            reasoning = self.generate_reasoning(best_regime, market_data, indicators, confidence)
            
            return RegimeAnalysis(
                regime=best_regime,
                confidence=confidence,
                regime_strength=regime_strength,
                allocation_multiplier=allocation_multiplier,
                risk_level=risk_level,
                indicators=indicators,
                reasoning=reasoning,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"❌ Error analyzing regime: {e}")
            return self.create_fallback_analysis()
    
    def score_bull_strong(self, market_data: MarketData, indicators: Dict[str, float]) -> float:
        """Score Bull Strong regime"""
        score = 0.0
        
        # Strong positive price movement
        if market_data.price_change_24h > 8.0:
            score += 0.4
        elif market_data.price_change_24h > 5.0:
            score += 0.2
        
        # High volume spike
        if indicators['volume_spike'] > 2.0:
            score += 0.3
        elif indicators['volume_spike'] > 1.5:
            score += 0.15
        
        # High RSI (overbought but strong)
        if indicators['rsi'] > 70:
            score += 0.2
        elif indicators['rsi'] > 60:
            score += 0.1
        
        # Fear & Greed (extreme greed)
        if indicators['fear_greed'] > 80:
            score += 0.1
        
        return min(1.0, score)
    
    def score_bear_strong(self, market_data: MarketData, indicators: Dict[str, float]) -> float:
        """Score Bear Strong regime"""
        score = 0.0
        
        # Strong negative price movement
        if market_data.price_change_24h < -8.0:
            score += 0.4
        elif market_data.price_change_24h < -5.0:
            score += 0.2
        
        # High volume spike (panic selling)
        if indicators['volume_spike'] > 2.0:
            score += 0.3
        elif indicators['volume_spike'] > 1.5:
            score += 0.15
        
        # Low RSI (oversold)
        if indicators['rsi'] < 30:
            score += 0.2
        elif indicators['rsi'] < 40:
            score += 0.1
        
        # Fear & Greed (extreme fear)
        if indicators['fear_greed'] < 20:
            score += 0.1
        
        return min(1.0, score)
    
    def score_sideways(self, market_data: MarketData, indicators: Dict[str, float]) -> float:
        """Score Sideways regime"""
        score = 0.0
        
        # Low price movement
        if abs(market_data.price_change_24h) < 2.0:
            score += 0.4
        elif abs(market_data.price_change_24h) < 4.0:
            score += 0.2
        
        # Normal volume
        if 0.8 <= indicators['volume_spike'] <= 1.2:
            score += 0.3
        
        # Neutral RSI
        if 40 <= indicators['rsi'] <= 60:
            score += 0.2
        
        # Low volatility
        if indicators['volatility'] < 0.3:
            score += 0.1
        
        return min(1.0, score)
    
    def score_high_volatility(self, market_data: MarketData, indicators: Dict[str, float]) -> float:
        """Score High Volatility regime"""
        score = 0.0
        
        # High volatility
        if indicators['volatility'] > 0.8:
            score += 0.5
        elif indicators['volatility'] > 0.6:
            score += 0.3
        
        # Large intraday movements
        if abs(market_data.price_change_1h) > 5.0:
            score += 0.3
        elif abs(market_data.price_change_1h) > 3.0:
            score += 0.15
        
        # High volume
        if indicators['volume_spike'] > 1.5:
            score += 0.2
        
        return min(1.0, score)
    
    def score_crash(self, market_data: MarketData, indicators: Dict[str, float]) -> float:
        """Score Crash regime"""
        score = 0.0
        
        # Extreme negative movement
        if market_data.price_change_24h < -15.0:
            score += 0.5
        elif market_data.price_change_24h < -10.0:
            score += 0.3
        
        # Panic volume
        if indicators['volume_spike'] > 3.0:
            score += 0.3
        elif indicators['volume_spike'] > 2.0:
            score += 0.15
        
        # Extreme fear
        if indicators['fear_greed'] < 10:
            score += 0.2
        
        return min(1.0, score)
    
    def score_bull_weak(self, market_data: MarketData, indicators: Dict[str, float]) -> float:
        """Score Bull Weak regime"""
        score = 0.0
        
        # Moderate positive movement
        if 2.0 <= market_data.price_change_24h <= 8.0:
            score += 0.4
        
        # Normal to slightly elevated volume
        if 1.0 <= indicators['volume_spike'] <= 2.0:
            score += 0.3
        
        # Moderate RSI
        if 50 <= indicators['rsi'] <= 70:
            score += 0.2
        
        # Moderate greed
        if 60 <= indicators['fear_greed'] <= 80:
            score += 0.1
        
        return min(1.0, score)
    
    def score_bear_weak(self, market_data: MarketData, indicators: Dict[str, float]) -> float:
        """Score Bear Weak regime"""
        score = 0.0
        
        # Moderate negative movement
        if -8.0 <= market_data.price_change_24h <= -2.0:
            score += 0.4
        
        # Normal to slightly elevated volume
        if 1.0 <= indicators['volume_spike'] <= 2.0:
            score += 0.3
        
        # Moderate RSI
        if 30 <= indicators['rsi'] <= 50:
            score += 0.2
        
        # Moderate fear
        if 20 <= indicators['fear_greed'] <= 40:
            score += 0.1
        
        return min(1.0, score)
    
    def get_risk_level(self, regime: MarketRegime, confidence: float) -> str:
        """Determine risk level based on regime and confidence"""
        high_risk_regimes = [MarketRegime.CRASH, MarketRegime.HIGH_VOLATILITY, MarketRegime.BEAR_STRONG]
        
        if regime in high_risk_regimes:
            return "HIGH"
        elif regime in [MarketRegime.BEAR_WEAK, MarketRegime.SIDEWAYS]:
            return "MEDIUM"
        else:
            return "LOW" if confidence > 0.7 else "MEDIUM"
    
    def generate_reasoning(self, regime: MarketRegime, market_data: MarketData, indicators: Dict[str, float], confidence: float) -> str:
        """Generate human-readable reasoning for regime classification"""
        price_change = market_data.price_change_24h
        volume_spike = indicators['volume_spike']
        rsi = indicators['rsi']
        
        reasoning = f"Market classified as {regime.value} with {confidence:.1%} confidence. "
        reasoning += f"24h price change: {price_change:+.1f}%, "
        reasoning += f"Volume spike: {volume_spike:.1f}x, "
        reasoning += f"RSI: {rsi:.1f}. "
        
        if regime == MarketRegime.BULL_STRONG:
            reasoning += "Strong bullish momentum with high volume support."
        elif regime == MarketRegime.BEAR_STRONG:
            reasoning += "Strong bearish pressure with panic selling."
        elif regime == MarketRegime.SIDEWAYS:
            reasoning += "Range-bound market with low directional bias."
        elif regime == MarketRegime.HIGH_VOLATILITY:
            reasoning += "High volatility environment with uncertain direction."
        elif regime == MarketRegime.CRASH:
            reasoning += "Extreme downward movement indicating market crash."
        
        return reasoning
    
    def update_historical_data(self, market_data: MarketData):
        """Update historical data for indicator calculations"""
        self.price_history.append(market_data.price)
        self.volume_history.append(market_data.volume_24h)
        
        # Keep only last 100 data points
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        if len(self.volume_history) > 100:
            self.volume_history = self.volume_history[-100:]
    
    async def store_regime_analysis(self, analysis: RegimeAnalysis):
        """Store regime analysis in Redis for other modules"""
        try:
            regime_data = {
                "regime": analysis.regime.value,
                "confidence": analysis.confidence,
                "allocation_multiplier": analysis.allocation_multiplier,
                "risk_level": analysis.risk_level,
                "reasoning": analysis.reasoning,
                "timestamp": analysis.timestamp,
                "indicators": analysis.indicators
            }
            
            # Store current regime
            self.redis_client.setex("overmind:current_regime", 300, json.dumps(regime_data))
            
            # Add to regime history
            self.redis_client.lpush("overmind:regime_history", json.dumps(regime_data))
            self.redis_client.ltrim("overmind:regime_history", 0, 99)  # Keep last 100
            
            logger.info(f"📊 Regime analysis stored in Redis: {analysis.regime.value}")
            
        except Exception as e:
            logger.error(f"❌ Error storing regime analysis: {e}")
    
    def create_fallback_analysis(self) -> RegimeAnalysis:
        """Create fallback analysis when detection fails"""
        return RegimeAnalysis(
            regime=MarketRegime.SIDEWAYS,
            confidence=0.5,
            regime_strength=0.5,
            allocation_multiplier=0.8,
            risk_level="MEDIUM",
            indicators={'rsi': 50.0, 'volume_spike': 1.0, 'volatility': 0.3},
            reasoning="Fallback analysis due to data unavailability",
            timestamp=time.time()
        )
    
    def create_fallback_market_data(self) -> MarketData:
        """Create fallback market data when fetch fails"""
        return MarketData(
            timestamp=time.time(),
            price=100.0,
            volume_24h=1000000.0,
            price_change_1h=0.0,
            price_change_24h=0.0,
            price_change_7d=0.0,
            market_cap=10000000.0,
            volatility=0.3
        )

# Factory function
def create_market_regime_detector() -> MarketRegimeDetector:
    """Create market regime detector instance"""
    return MarketRegimeDetector()

# Example usage
if __name__ == "__main__":
    async def test_regime_detection():
        """Test market regime detection"""
        detector = create_market_regime_detector()
        
        # Test regime detection
        analysis = await detector.detect_current_regime("SOL")
        
        print("=== MARKET REGIME ANALYSIS ===")
        print(f"Regime: {analysis.regime.value}")
        print(f"Confidence: {analysis.confidence:.2f}")
        print(f"Allocation Multiplier: {analysis.allocation_multiplier:.2f}x")
        print(f"Risk Level: {analysis.risk_level}")
        print(f"Reasoning: {analysis.reasoning}")
        print("\nIndicators:")
        for key, value in analysis.indicators.items():
            print(f"  {key}: {value:.2f}")
    
    asyncio.run(test_regime_detection())
