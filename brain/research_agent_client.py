#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - ResearchAgent Client
Client for communicating with ResearchAgent microservice
"""

import asyncio
import aiohttp
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResearchRequest:
    """Research request structure"""
    query: str
    symbol: Optional[str] = None
    research_type: str = "comprehensive"  # comprehensive, sentiment, news, technical
    max_results: int = 10
    confidence_threshold: float = 0.3
    request_id: str = ""

class ResearchAgentClient:
    """
    Client for communicating with ResearchAgent microservice
    Supports both HTTP and gRPC communication
    """
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def research(self, 
                      query: str, 
                      symbol: Optional[str] = None,
                      research_type: str = "comprehensive",
                      max_results: int = 10,
                      confidence_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Send research request to ResearchAgent microservice
        
        Args:
            query: Research query/question
            symbol: Optional trading symbol (e.g., 'SOL', 'BONK')
            research_type: Type of research (comprehensive, sentiment, news, technical)
            max_results: Maximum number of results to return
            confidence_threshold: Minimum confidence threshold for results
            
        Returns:
            Research results as dictionary
        """
        try:
            # Create research request
            request = ResearchRequest(
                query=query,
                symbol=symbol,
                research_type=research_type,
                max_results=max_results,
                confidence_threshold=confidence_threshold,
                request_id=str(uuid.uuid4())
            )
            
            logger.info(f"🔍 Sending research request: {query[:50]}...")
            
            # Send HTTP POST request to microservice
            async with self.session.post(
                f"{self.base_url}/research",
                json={"data": [{"text": json.dumps(asdict(request))}]},
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Parse response
                    if result.get('data') and len(result['data']) > 0:
                        research_result = json.loads(result['data'][0]['text'])
                        logger.info(f"✅ Research completed in {research_result.get('processing_time', 0):.2f}s")
                        return research_result
                    else:
                        logger.warning("⚠️ Empty response from ResearchAgent")
                        return self._empty_result(request)
                else:
                    logger.error(f"❌ ResearchAgent returned status {response.status}")
                    return self._empty_result(request)
                    
        except Exception as e:
            logger.error(f"❌ Error communicating with ResearchAgent: {e}")
            return self._empty_result(ResearchRequest(query=query, symbol=symbol))
    
    async def comprehensive_research(self, query: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive research"""
        return await self.research(query, symbol, "comprehensive")
    
    async def sentiment_analysis(self, query: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Perform sentiment analysis"""
        return await self.research(query, symbol, "sentiment")
    
    async def news_analysis(self, symbol: str) -> Dict[str, Any]:
        """Perform news analysis for specific symbol"""
        return await self.research(f"Latest news and developments for {symbol}", symbol, "news")
    
    async def technical_analysis(self, query: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Perform technical analysis"""
        return await self.research(query, symbol, "technical")
    
    async def health_check(self) -> bool:
        """Check if ResearchAgent microservice is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except:
            return False
    
    def _empty_result(self, request: ResearchRequest) -> Dict[str, Any]:
        """Return empty result when request fails"""
        return {
            'request_id': request.request_id,
            'query': request.query,
            'symbol': request.symbol,
            'sentiment_score': 0.5,
            'confidence': 0.0,
            'key_insights': [],
            'trading_signals': [],
            'news_items': [],
            'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'processing_time': 0.0,
            'research_method': 'failed'
        }

# Integration with OVERMINDBrainManager
class OVERMINDBrainManagerIntegration:
    """
    Integration layer for OVERMINDBrainManager to use ResearchAgent microservice
    """
    
    def __init__(self, research_agent_url: str = "http://localhost:8080"):
        self.research_agent_url = research_agent_url
        
    async def get_market_research(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market research for a symbol"""
        async with ResearchAgentClient(self.research_agent_url) as client:
            # Parallel research requests
            tasks = [
                client.comprehensive_research(f"Market analysis for {symbol}", symbol),
                client.sentiment_analysis(f"Current sentiment for {symbol}", symbol),
                client.news_analysis(symbol),
                client.technical_analysis(f"Technical indicators for {symbol}", symbol)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            combined_result = {
                'symbol': symbol,
                'comprehensive': results[0] if not isinstance(results[0], Exception) else {},
                'sentiment': results[1] if not isinstance(results[1], Exception) else {},
                'news': results[2] if not isinstance(results[2], Exception) else {},
                'technical': results[3] if not isinstance(results[3], Exception) else {},
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return combined_result
    
    async def get_trading_signals(self, symbol: str) -> List[str]:
        """Get trading signals from research analysis"""
        research_data = await self.get_market_research(symbol)
        
        all_signals = []
        for analysis_type, data in research_data.items():
            if isinstance(data, dict) and 'trading_signals' in data:
                all_signals.extend(data['trading_signals'])
        
        # Remove duplicates and return
        return list(set(all_signals))
    
    async def get_market_sentiment(self, symbol: str) -> float:
        """Get overall market sentiment for a symbol"""
        async with ResearchAgentClient(self.research_agent_url) as client:
            sentiment_result = await client.sentiment_analysis(f"Overall market sentiment for {symbol}", symbol)
            return sentiment_result.get('sentiment_score', 0.5)

# Test function
async def test_research_agent_client():
    """Test the ResearchAgent client"""
    print("🧠 THE OVERMIND PROTOCOL - ResearchAgent Client Test")
    print("=" * 60)
    
    async with ResearchAgentClient() as client:
        # Test 1: Health check
        print("\n🏥 Test 1: Health Check")
        is_healthy = await client.health_check()
        print(f"   ResearchAgent Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
        
        if not is_healthy:
            print("   ⚠️ ResearchAgent microservice not running - start it first!")
            return
        
        # Test 2: Comprehensive research
        print("\n🔍 Test 2: Comprehensive Research")
        result = await client.comprehensive_research("Solana ecosystem developments and price outlook", "SOL")
        print(f"   Query: Solana ecosystem developments")
        print(f"   Sentiment: {result.get('sentiment_score', 0):.3f}")
        print(f"   Confidence: {result.get('confidence', 0):.3f}")
        print(f"   Insights: {len(result.get('key_insights', []))} found")
        print(f"   Method: {result.get('research_method', 'unknown')}")
        
        # Test 3: Sentiment analysis
        print("\n💭 Test 3: Sentiment Analysis")
        sentiment_result = await client.sentiment_analysis("Bullish momentum building for Solana", "SOL")
        print(f"   Sentiment Score: {sentiment_result.get('sentiment_score', 0):.3f}")
        print(f"   Confidence: {sentiment_result.get('confidence', 0):.3f}")
        print(f"   Signals: {sentiment_result.get('trading_signals', [])}")
        
        # Test 4: OVERMIND Integration
        print("\n🧠 Test 4: OVERMIND Integration")
        integration = OVERMINDBrainManagerIntegration()
        market_research = await integration.get_market_research("SOL")
        trading_signals = await integration.get_trading_signals("SOL")
        market_sentiment = await integration.get_market_sentiment("SOL")
        
        print(f"   Market Research Types: {list(market_research.keys())}")
        print(f"   Trading Signals: {trading_signals}")
        print(f"   Overall Sentiment: {market_sentiment:.3f}")
    
    print(f"\n🎯 ResearchAgent Client Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_research_agent_client())
