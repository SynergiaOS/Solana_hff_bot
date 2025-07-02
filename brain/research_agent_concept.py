#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - ResearchAgent Concept Demo
Demonstrates the ResearchAgent architecture without Jina-Serve dependencies
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from news_intelligence import JinaNewsIntelligence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResearchRequest:
    """Research request structure"""
    query: str
    symbol: Optional[str] = None
    research_type: str = "comprehensive"
    max_results: int = 10
    confidence_threshold: float = 0.3
    request_id: str = ""

@dataclass
class ResearchResult:
    """Research result structure"""
    request_id: str
    query: str
    symbol: Optional[str]
    sentiment_score: float
    confidence: float
    key_insights: List[str]
    trading_signals: List[str]
    news_items: List[Dict]
    analysis_timestamp: str
    processing_time: float
    research_method: str

class ResearchAgentCore:
    """
    Core ResearchAgent functionality (without Jina-Serve)
    Demonstrates the research capabilities that would be deployed as microservice
    """
    
    def __init__(self):
        self.news_intelligence = JinaNewsIntelligence()
        self.research_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("🧠 ResearchAgent Core initialized with Jina AI")
    
    async def research(self, request: ResearchRequest) -> ResearchResult:
        """
        Main research method - processes research requests
        """
        try:
            start_time = time.time()
            
            logger.info(f"🔍 Processing research request: {request.query[:50]}...")
            
            # Check cache first
            cache_key = f"{request.query}_{request.symbol}_{request.research_type}"
            if self._is_cached(cache_key):
                logger.info("📋 Returning cached research result")
                return self.research_cache[cache_key]['data']
            
            # Perform research based on type
            if request.research_type == "comprehensive":
                result = await self._comprehensive_research(request)
            elif request.research_type == "sentiment":
                result = await self._sentiment_research(request)
            elif request.research_type == "news":
                result = await self._news_research(request)
            elif request.research_type == "technical":
                result = await self._technical_research(request)
            else:
                result = await self._comprehensive_research(request)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            result.analysis_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Cache the result
            self._cache_result(cache_key, result)
            
            logger.info(f"✅ Research completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing research request: {e}")
            return self._fallback_research_result(request)
    
    async def _comprehensive_research(self, request: ResearchRequest) -> ResearchResult:
        """Perform comprehensive research using all available methods"""
        try:
            # Use Jina DeepSearch for comprehensive analysis
            analysis = await self.news_intelligence.deep_search_analysis(
                request.query, 
                None
            )
            
            # If symbol provided, get symbol-specific news
            news_items = []
            if request.symbol:
                symbol_data = await self.news_intelligence.process_news_for_symbol_with_jina(request.symbol)
                news_items = symbol_data.get('news_items', [])
            
            return ResearchResult(
                request_id=request.request_id,
                query=request.query,
                symbol=request.symbol,
                sentiment_score=analysis.get('sentiment_score', 0.5),
                confidence=analysis.get('confidence', 0.0),
                key_insights=analysis.get('key_insights', [])[:request.max_results],
                trading_signals=analysis.get('trading_signals', []),
                news_items=news_items[:request.max_results],
                analysis_timestamp="",
                processing_time=0.0,
                research_method="jina_comprehensive"
            )
            
        except Exception as e:
            logger.error(f"❌ Error in comprehensive research: {e}")
            return self._fallback_research_result(request)
    
    async def _sentiment_research(self, request: ResearchRequest) -> ResearchResult:
        """Perform sentiment-focused research"""
        try:
            sentiment_result = await self.news_intelligence.analyze_sentiment_with_jina(
                request.query, 
                request.symbol
            )
            
            return ResearchResult(
                request_id=request.request_id,
                query=request.query,
                symbol=request.symbol,
                sentiment_score=sentiment_result.get('score', 0.5),
                confidence=sentiment_result.get('confidence', 0.0),
                key_insights=sentiment_result.get('insights', [])[:request.max_results],
                trading_signals=sentiment_result.get('signals', []),
                news_items=[],
                analysis_timestamp="",
                processing_time=0.0,
                research_method="jina_sentiment"
            )
            
        except Exception as e:
            logger.error(f"❌ Error in sentiment research: {e}")
            return self._fallback_research_result(request)
    
    async def _news_research(self, request: ResearchRequest) -> ResearchResult:
        """Perform news-focused research"""
        try:
            if request.symbol:
                news_data = await self.news_intelligence.process_news_for_symbol_with_jina(request.symbol)
                
                return ResearchResult(
                    request_id=request.request_id,
                    query=request.query,
                    symbol=request.symbol,
                    sentiment_score=news_data.get('avg_sentiment', 0.5),
                    confidence=news_data.get('confidence', 0.0),
                    key_insights=news_data.get('insights', [])[:request.max_results],
                    trading_signals=news_data.get('signals', []),
                    news_items=news_data.get('news_items', [])[:request.max_results],
                    analysis_timestamp="",
                    processing_time=0.0,
                    research_method="jina_news"
                )
            else:
                return self._fallback_research_result(request)
                
        except Exception as e:
            logger.error(f"❌ Error in news research: {e}")
            return self._fallback_research_result(request)
    
    async def _technical_research(self, request: ResearchRequest) -> ResearchResult:
        """Perform technical analysis research"""
        try:
            technical_query = f"Technical analysis and price prediction for {request.symbol or 'cryptocurrency'}: {request.query}"
            analysis = await self.news_intelligence.deep_search_analysis(technical_query)
            
            return ResearchResult(
                request_id=request.request_id,
                query=request.query,
                symbol=request.symbol,
                sentiment_score=analysis.get('sentiment_score', 0.5),
                confidence=analysis.get('confidence', 0.0),
                key_insights=analysis.get('key_insights', [])[:request.max_results],
                trading_signals=analysis.get('trading_signals', []),
                news_items=[],
                analysis_timestamp="",
                processing_time=0.0,
                research_method="jina_technical"
            )
            
        except Exception as e:
            logger.error(f"❌ Error in technical research: {e}")
            return self._fallback_research_result(request)
    
    def _fallback_research_result(self, request: ResearchRequest) -> ResearchResult:
        """Fallback research result when all methods fail"""
        return ResearchResult(
            request_id=request.request_id,
            query=request.query,
            symbol=request.symbol,
            sentiment_score=0.5,
            confidence=0.1,
            key_insights=["Fallback analysis - limited data available"],
            trading_signals=["neutral"],
            news_items=[],
            analysis_timestamp="",
            processing_time=0.0,
            research_method="fallback"
        )
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if result is cached and still valid"""
        if cache_key in self.research_cache:
            cache_time = self.research_cache[cache_key]['timestamp']
            return (time.time() - cache_time) < self.cache_ttl
        return False
    
    def _cache_result(self, cache_key: str, result: ResearchResult):
        """Cache research result"""
        self.research_cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }

class OVERMINDBrainIntegration:
    """
    Integration layer showing how OVERMINDBrainManager would use ResearchAgent
    """
    
    def __init__(self):
        self.research_agent = ResearchAgentCore()
    
    async def get_trading_intelligence(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive trading intelligence for a symbol"""
        
        # Parallel research requests
        requests = [
            ResearchRequest(
                query=f"Comprehensive market analysis for {symbol}",
                symbol=symbol,
                research_type="comprehensive",
                request_id="comp_001"
            ),
            ResearchRequest(
                query=f"Current market sentiment for {symbol}",
                symbol=symbol,
                research_type="sentiment",
                request_id="sent_001"
            ),
            ResearchRequest(
                query=f"Latest news affecting {symbol}",
                symbol=symbol,
                research_type="news",
                request_id="news_001"
            ),
            ResearchRequest(
                query=f"Technical analysis for {symbol}",
                symbol=symbol,
                research_type="technical",
                request_id="tech_001"
            )
        ]
        
        # Execute all research requests
        tasks = [self.research_agent.research(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        intelligence = {
            'symbol': symbol,
            'comprehensive': asdict(results[0]) if not isinstance(results[0], Exception) else {},
            'sentiment': asdict(results[1]) if not isinstance(results[1], Exception) else {},
            'news': asdict(results[2]) if not isinstance(results[2], Exception) else {},
            'technical': asdict(results[3]) if not isinstance(results[3], Exception) else {},
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return intelligence

async def test_research_agent_concept():
    """Test the ResearchAgent concept"""
    
    print("🧠 THE OVERMIND PROTOCOL - ResearchAgent Concept Demo")
    print("=" * 60)
    
    # Initialize ResearchAgent
    research_agent = ResearchAgentCore()
    
    # Test 1: Individual research types
    print("\n🔍 Test 1: Individual Research Types")
    
    research_types = [
        ("comprehensive", "Solana ecosystem growth and adoption"),
        ("sentiment", "Current bullish sentiment for Solana"),
        ("technical", "Solana price technical analysis")
    ]
    
    for research_type, query in research_types:
        request = ResearchRequest(
            query=query,
            symbol="SOL",
            research_type=research_type,
            request_id=f"test_{research_type}"
        )
        
        result = await research_agent.research(request)
        
        print(f"   {research_type.title()}:")
        print(f"     Sentiment: {result.sentiment_score:.3f}")
        print(f"     Confidence: {result.confidence:.3f}")
        print(f"     Method: {result.research_method}")
        print(f"     Processing Time: {result.processing_time:.2f}s")
        print(f"     Insights: {len(result.key_insights)} found")
    
    # Test 2: OVERMIND Integration
    print("\n🧠 Test 2: OVERMIND Brain Integration")
    
    integration = OVERMINDBrainIntegration()
    intelligence = await integration.get_trading_intelligence("SOL")
    
    print(f"   Symbol: {intelligence['symbol']}")
    print(f"   Research Components: {list(intelligence.keys())}")
    
    for component, data in intelligence.items():
        if isinstance(data, dict) and 'sentiment_score' in data:
            print(f"     {component.title()}: Sentiment {data['sentiment_score']:.3f}, "
                  f"Confidence {data['confidence']:.3f}")
    
    print(f"\n🎯 ResearchAgent Concept Demo Complete!")
    print("=" * 60)
    
    print(f"\n📊 CONCEPT SUMMARY:")
    print(f"✅ ResearchAgent Core: Autonomous research with Jina AI")
    print(f"✅ Multiple Research Types: Comprehensive, sentiment, news, technical")
    print(f"✅ Caching System: 5-minute TTL for performance")
    print(f"✅ OVERMIND Integration: Parallel research execution")
    print(f"✅ Fallback Mechanisms: Graceful degradation")
    print(f"\n🚀 Ready for Jina-Serve microservice deployment!")

if __name__ == "__main__":
    asyncio.run(test_research_agent_concept())
