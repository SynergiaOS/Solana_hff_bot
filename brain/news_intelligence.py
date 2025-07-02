#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - News Intelligence (Jina AI Enhanced)
Real-time news monitoring and sentiment analysis powered by Jina AI
- Jina Reader API for clean content extraction
- Jina DeepSearch for iterative analysis and reasoning
- Enhanced sentiment analysis with AI-powered insights
"""

import asyncio
import json
import time
import redis
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Jina AI Configuration
JINA_API_KEY = "jina_72cc7ed00e21496290ed9e018d56de3bETDGPqW-TUXuYYIxk4jwHLN9h0C6"
JINA_READER_URL = "https://r.jina.ai/"
JINA_DEEPSEARCH_URL = "https://s.jina.ai/"

@dataclass
class NewsAnalysis:
    """Structured news analysis result from Jina AI"""
    title: str
    url: str
    content_summary: str
    sentiment_score: float
    confidence: float
    key_insights: List[str]
    trading_signals: List[str]
    relevance_score: float
    published_at: str
    analysis_timestamp: str

class JinaNewsIntelligence:
    """Enhanced News Intelligence powered by Jina AI"""

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        self.news_cache = {}
        self.analysis_cache = {}

        # Jina AI Configuration
        self.jina_api_key = JINA_API_KEY
        self.reader_headers = {
            'Authorization': f'Bearer {self.jina_api_key}',
            'Content-Type': 'application/json'
        }

        # APIs for news sources
        self.coingecko_url = "https://api.coingecko.com/api/v3"

        # Enhanced analysis prompts for Jina DeepSearch
        self.analysis_prompts = {
            'sentiment': """
            Analyze this cryptocurrency news content and provide:
            1. Overall sentiment score (0.0 = very bearish, 0.5 = neutral, 1.0 = very bullish)
            2. Confidence level in the analysis (0.0 to 1.0)
            3. Key insights that could affect token price
            4. Specific trading signals (bullish/bearish indicators)
            5. Relevance to cryptocurrency trading (0.0 to 1.0)

            Return structured JSON with these fields:
            {
                "sentiment_score": float,
                "confidence": float,
                "key_insights": [list of strings],
                "trading_signals": [list of strings],
                "relevance_score": float,
                "reasoning": "explanation of analysis"
            }
            """,

            'deep_research': """
            Perform deep research on this cryptocurrency topic:
            1. Find related news and developments
            2. Analyze market implications
            3. Identify potential price catalysts
            4. Assess risk factors
            5. Generate actionable trading insights

            Focus on: partnerships, technical developments, regulatory news,
            institutional adoption, market trends, and community sentiment.
            """
        }

    async def fetch_clean_content(self, url: str) -> Optional[str]:
        """Fetch clean, LLM-ready content using Jina Reader API"""
        try:
            async with aiohttp.ClientSession() as session:
                reader_url = f"{JINA_READER_URL}{url}"

                async with session.get(reader_url, headers=self.reader_headers) as response:
                    if response.status == 200:
                        clean_content = await response.text()
                        logger.info(f"✅ Successfully fetched clean content from {url}")
                        return clean_content
                    else:
                        logger.warning(f"⚠️ Jina Reader API returned status {response.status} for {url}")
                        return None

        except Exception as e:
            logger.error(f"❌ Error fetching content with Jina Reader API: {e}")
            return None

    async def deep_search_analysis(self, query: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Perform deep search analysis using Jina DeepSearch API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Use GET request with query parameter for DeepSearch
                search_url = f"{JINA_DEEPSEARCH_URL}{query}"

                async with session.get(
                    search_url,
                    headers=self.reader_headers
                ) as response:
                    if response.status == 200:
                        # Try to get JSON response
                        try:
                            result = await response.json()
                            logger.info(f"✅ DeepSearch analysis completed for query: {query[:50]}...")
                            return result
                        except:
                            # If JSON parsing fails, try text response and parse manually
                            text_result = await response.text()
                            logger.info(f"✅ DeepSearch text response received: {len(text_result)} chars")

                            # Parse the text response for sentiment analysis
                            return self._parse_deepsearch_text_response(text_result, query)
                    else:
                        logger.warning(f"⚠️ Jina DeepSearch API returned status {response.status}")
                        return {}

        except Exception as e:
            logger.error(f"❌ Error with Jina DeepSearch API: {e}")
            return {}

    def _parse_deepsearch_text_response(self, text_response: str, query: str) -> Dict[str, Any]:
        """Parse text response from DeepSearch into structured format"""
        try:
            # Basic sentiment analysis from the response text
            text_lower = text_response.lower()

            # Look for sentiment indicators in the response
            positive_indicators = ['positive', 'bullish', 'good', 'strong', 'growth', 'increase']
            negative_indicators = ['negative', 'bearish', 'bad', 'weak', 'decline', 'decrease']

            positive_count = sum(1 for indicator in positive_indicators if indicator in text_lower)
            negative_count = sum(1 for indicator in negative_indicators if indicator in text_lower)

            # Calculate sentiment score
            total_indicators = positive_count + negative_count
            if total_indicators > 0:
                sentiment_score = positive_count / total_indicators
                confidence = min(total_indicators / 10.0, 0.8)
            else:
                sentiment_score = 0.5
                confidence = 0.3

            # Extract key insights (first few sentences)
            sentences = text_response.split('.')[:3]
            key_insights = [s.strip() for s in sentences if len(s.strip()) > 10]

            # Generate trading signals based on sentiment
            trading_signals = []
            if sentiment_score > 0.6:
                trading_signals.append('bullish_sentiment')
            elif sentiment_score < 0.4:
                trading_signals.append('bearish_sentiment')

            return {
                'sentiment_score': sentiment_score,
                'confidence': confidence,
                'key_insights': key_insights,
                'trading_signals': trading_signals,
                'relevance_score': 0.7,  # Default relevance
                'reasoning': f'Analyzed DeepSearch response for: {query[:50]}...'
            }

        except Exception as e:
            logger.error(f"❌ Error parsing DeepSearch text response: {e}")
            return {
                'sentiment_score': 0.5,
                'confidence': 0.1,
                'key_insights': [],
                'trading_signals': [],
                'relevance_score': 0.3,
                'reasoning': 'Failed to parse DeepSearch response'
            }

    async def analyze_news_with_jina(self, news_item: Dict) -> NewsAnalysis:
        """Analyze news item using Jina AI for enhanced insights"""
        try:
            title = news_item.get('title', '')
            url = news_item.get('url', '')
            description = news_item.get('description', '')

            # Step 1: Fetch clean content using Jina Reader API
            clean_content = await self.fetch_clean_content(url) if url else None

            # Step 2: Prepare content for analysis
            analysis_content = clean_content or f"{title}\n{description}"

            if not analysis_content.strip():
                # Fallback analysis
                return NewsAnalysis(
                    title=title,
                    url=url,
                    content_summary="No content available",
                    sentiment_score=0.5,
                    confidence=0.0,
                    key_insights=[],
                    trading_signals=[],
                    relevance_score=0.0,
                    published_at=news_item.get('published_at', ''),
                    analysis_timestamp=datetime.now().isoformat()
                )

            # Step 3: Perform deep analysis using Jina DeepSearch
            analysis_query = f"Analyze this cryptocurrency news for trading insights: {title}"
            deep_analysis = await self.deep_search_analysis(analysis_query, analysis_content)

            # Step 4: Extract structured results
            sentiment_score = deep_analysis.get('sentiment_score', 0.5)
            confidence = deep_analysis.get('confidence', 0.0)
            key_insights = deep_analysis.get('key_insights', [])
            trading_signals = deep_analysis.get('trading_signals', [])
            relevance_score = deep_analysis.get('relevance_score', 0.0)

            # Step 5: Generate content summary
            content_summary = analysis_content[:500] + "..." if len(analysis_content) > 500 else analysis_content

            return NewsAnalysis(
                title=title,
                url=url,
                content_summary=content_summary,
                sentiment_score=sentiment_score,
                confidence=confidence,
                key_insights=key_insights,
                trading_signals=trading_signals,
                relevance_score=relevance_score,
                published_at=news_item.get('published_at', ''),
                analysis_timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"❌ Error analyzing news with Jina AI: {e}")
            # Return fallback analysis
            return NewsAnalysis(
                title=news_item.get('title', ''),
                url=news_item.get('url', ''),
                content_summary="Analysis failed",
                sentiment_score=0.5,
                confidence=0.0,
                key_insights=[],
                trading_signals=[],
                relevance_score=0.0,
                published_at=news_item.get('published_at', ''),
                analysis_timestamp=datetime.now().isoformat()
            )

    async def fetch_coingecko_news(self, symbol: str) -> List[Dict]:
        """Fetch news from CoinGecko for specific token using async HTTP"""
        try:
            # Get coin ID
            symbol_map = {
                'SOL': 'solana',
                'BONK': 'bonk',
                'RAY': 'raydium',
                'ORCA': 'orca',
                'USDC': 'usd-coin'
            }

            coin_id = symbol_map.get(symbol)
            if not coin_id:
                return []

            # Fetch trending news using aiohttp
            url = f"{self.coingecko_url}/coins/{coin_id}/news"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])[:10]  # Last 10 news items

        except Exception as e:
            logger.error(f"❌ Error fetching CoinGecko news for {symbol}: {e}")

        return []

    async def fetch_general_crypto_news(self) -> List[Dict]:
        """Fetch general crypto news using async HTTP"""
        try:
            # Using CoinGecko trending news
            url = f"{self.coingecko_url}/news"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])[:20]  # Last 20 news items

        except Exception as e:
            logger.error(f"❌ Error fetching general crypto news: {e}")

        return []
    
    async def analyze_sentiment_with_jina(self, text: str, symbol: Optional[str] = None) -> Dict:
        """Enhanced sentiment analysis using Jina AI"""
        if not text:
            return {'score': 0.5, 'confidence': 0.0, 'signals': [], 'relevance': 0.0}

        try:
            # Create analysis query
            analysis_query = f"Analyze sentiment and trading implications for {symbol or 'cryptocurrency'}: {text[:200]}"

            # Use Jina DeepSearch for sentiment analysis
            analysis_result = await self.deep_search_analysis(analysis_query, text)

            if analysis_result:
                return {
                    'score': analysis_result.get('sentiment_score', 0.5),
                    'confidence': analysis_result.get('confidence', 0.0),
                    'relevance': analysis_result.get('relevance_score', 0.0),
                    'signals': analysis_result.get('trading_signals', []),
                    'insights': analysis_result.get('key_insights', []),
                    'reasoning': analysis_result.get('reasoning', '')
                }
            else:
                # Fallback to basic analysis
                return await self._fallback_sentiment_analysis(text, symbol)

        except Exception as e:
            logger.error(f"❌ Error in Jina sentiment analysis: {e}")
            return await self._fallback_sentiment_analysis(text, symbol)

    async def _fallback_sentiment_analysis(self, text: str, symbol: Optional[str] = None) -> Dict:
        """Fallback sentiment analysis when Jina AI is unavailable"""
        text_lower = text.lower()

        # Basic keyword analysis
        positive_keywords = ['bullish', 'moon', 'pump', 'surge', 'rally', 'breakout', 'adoption']
        negative_keywords = ['bearish', 'dump', 'crash', 'decline', 'drop', 'fall', 'sell-off']

        positive_count = sum(1 for keyword in positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text_lower)

        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            sentiment_score = 0.5
            confidence = 0.1
        else:
            sentiment_score = positive_count / total_keywords
            confidence = min(total_keywords / 10.0, 1.0)

        signals = []
        if positive_count >= 2:
            signals.append('POSITIVE_SENTIMENT')
        if negative_count >= 2:
            signals.append('NEGATIVE_SENTIMENT')

        return {
            'score': sentiment_score,
            'confidence': confidence,
            'relevance': 0.5,  # Default relevance
            'signals': signals,
            'insights': [],
            'reasoning': 'Fallback keyword-based analysis'
        }
    
    async def process_news_for_symbol_with_jina(self, symbol: str) -> Dict:
        """Process all news for a specific symbol using Jina AI enhanced analysis"""
        try:
            # Fetch symbol-specific news
            symbol_news = await self.fetch_coingecko_news(symbol)

            # Fetch general crypto news and filter for relevance
            general_news = await self.fetch_general_crypto_news()

            all_news = symbol_news + general_news

            if not all_news:
                return {
                    'symbol': symbol,
                    'news_count': 0,
                    'avg_sentiment': 0.5,
                    'confidence': 0.0,
                    'signals': [],
                    'insights': [],
                    'last_update': time.time()
                }

            # Analyze news using Jina AI
            analyzed_news = []
            all_insights = []
            all_signals = []

            for news_item in all_news:
                try:
                    # Use Jina AI for comprehensive analysis
                    analysis = await self.analyze_news_with_jina(news_item)

                    # Only include if relevant
                    if analysis.relevance_score > 0.3 or analysis.confidence > 0.4:
                        analyzed_news.append(analysis)
                        all_insights.extend(analysis.key_insights)
                        all_signals.extend(analysis.trading_signals)

                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.warning(f"⚠️ Failed to analyze news item: {e}")
                    continue

            if not analyzed_news:
                return {
                    'symbol': symbol,
                    'news_count': 0,
                    'avg_sentiment': 0.5,
                    'confidence': 0.0,
                    'signals': [],
                    'insights': [],
                    'last_update': time.time()
                }

            # Calculate weighted average sentiment from Jina AI analyses
            total_weight = sum(analysis.confidence for analysis in analyzed_news)
            if total_weight > 0:
                weighted_sentiment = sum(
                    analysis.sentiment_score * analysis.confidence
                    for analysis in analyzed_news
                ) / total_weight
                avg_confidence = total_weight / len(analyzed_news)
            else:
                weighted_sentiment = 0.5
                avg_confidence = 0.0

            # Count signal frequency
            signal_counts = {}
            for signal in all_signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1

            # Only include signals that appear multiple times
            significant_signals = [signal for signal, count in signal_counts.items() if count >= 2]

            # Get unique insights
            unique_insights = list(set(all_insights))[:10]  # Top 10 unique insights

            # Convert analyses to dict format for compatibility
            news_items = []
            for analysis in analyzed_news[:5]:  # Top 5 most relevant
                news_items.append({
                    'title': analysis.title,
                    'url': analysis.url,
                    'published_at': analysis.published_at,
                    'sentiment_score': analysis.sentiment_score,
                    'confidence': analysis.confidence,
                    'key_insights': analysis.key_insights,
                    'trading_signals': analysis.trading_signals
                })

            return {
                'symbol': symbol,
                'news_count': len(analyzed_news),
                'avg_sentiment': weighted_sentiment,
                'confidence': avg_confidence,
                'signals': significant_signals,
                'insights': unique_insights,
                'news_items': news_items,
                'last_update': time.time(),
                'analysis_method': 'jina_ai_enhanced'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing news for {symbol}: {e}")
            return {
                'symbol': symbol,
                'news_count': 0,
                'avg_sentiment': 0.5,
                'confidence': 0.0,
                'signals': [],
                'error': str(e),
                'last_update': time.time()
            }
    
    async def monitor_all_symbols(self, symbols: List[str]):
        """Monitor news for all symbols using Jina AI enhanced analysis"""
        news_intelligence = {}

        for symbol in symbols:
            logger.info(f"📰 Processing news for {symbol} with Jina AI...")
            news_data = await self.process_news_for_symbol_with_jina(symbol)
            news_intelligence[symbol] = news_data

            # Longer delay to respect Jina AI rate limits
            await asyncio.sleep(5)

        return news_intelligence
    
    async def publish_news_intelligence(self, intelligence_data: Dict):
        """Publish news intelligence to Redis"""
        try:
            intelligence_update = {
                'timestamp': time.time(),
                'news_intelligence': intelligence_data,
                'update_type': 'news_intelligence'
            }
            
            self.redis_client.lpush('overmind:news_intelligence', json.dumps(intelligence_update))
            
            # Keep only last 50 updates
            self.redis_client.ltrim('overmind:news_intelligence', 0, 49)
            
        except Exception as e:
            logger.error(f"❌ Error publishing news intelligence: {e}")
    
    def print_news_summary(self, intelligence_data: Dict):
        """Print news intelligence summary"""
        print("\n📰 THE OVERMIND PROTOCOL - NEWS INTELLIGENCE")
        print("=" * 60)
        
        for symbol, data in intelligence_data.items():
            sentiment = data['avg_sentiment']
            confidence = data['confidence']
            news_count = data['news_count']
            signals = data.get('signals', [])
            
            # Sentiment indicator
            if sentiment > 0.6 and confidence > 0.3:
                indicator = "🟢 BULLISH"
            elif sentiment < 0.4 and confidence > 0.3:
                indicator = "🔴 BEARISH"
            else:
                indicator = "⚪ NEUTRAL"
            
            print(f"{indicator} {symbol}: Sentiment {sentiment:.2f} "
                  f"(Conf: {confidence:.2f}) | News: {news_count}")
            
            if signals:
                print(f"   📊 Signals: {', '.join(signals)}")
        
        print(f"🔄 Last Update: {datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')}")
    
    async def news_monitoring_loop(self):
        """Main news monitoring loop"""
        logger.info("🚀 Starting News Intelligence Monitor...")
        
        # Get symbols from Redis positions
        symbols = ['SOL', 'BONK', 'RAY', 'ORCA', 'USDC']  # Default symbols
        
        while True:
            try:
                # Monitor news for all symbols
                intelligence_data = await self.monitor_all_symbols(symbols)
                
                # Publish to Redis
                await self.publish_news_intelligence(intelligence_data)
                
                # Print summary
                self.print_news_summary(intelligence_data)
                
                # Wait 5 minutes before next update (to avoid rate limiting)
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Error in news monitoring loop: {e}")
                await asyncio.sleep(60)

# Alias for backward compatibility
NewsIntelligence = JinaNewsIntelligence

async def main():
    """Main function to run Jina AI enhanced news intelligence"""
    news_intel = JinaNewsIntelligence()
    await news_intel.news_monitoring_loop()

if __name__ == "__main__":
    asyncio.run(main())
