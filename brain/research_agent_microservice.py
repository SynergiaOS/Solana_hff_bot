#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - ResearchAgent Microservice
Jina-Serve powered microservice for autonomous research and analysis
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import time

from jina import Executor, requests, DocumentArray, Document
from jina.serve import deployment
from news_intelligence import JinaNewsIntelligence

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

class ResearchAgentExecutor(Executor):
    """
    Jina-Serve Executor for ResearchAgent
    Handles autonomous research requests with Jina AI integration
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.news_intelligence = JinaNewsIntelligence()
        self.research_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info("🧠 ResearchAgent Microservice initialized with Jina AI")
    
    @requests(on='/research')
    async def research(self, docs: DocumentArray, **kwargs) -> DocumentArray:
        """
        Main research endpoint
        Processes research requests and returns structured analysis
        """
        results = DocumentArray()
        
        for doc in docs:
            try:
                start_time = time.time()
                
                # Parse research request
                request_data = json.loads(doc.text)
                research_req = ResearchRequest(**request_data)
                
                logger.info(f"🔍 Processing research request: {research_req.query[:50]}...")
                
                # Check cache first
                cache_key = f"{research_req.query}_{research_req.symbol}_{research_req.research_type}"
                if self._is_cached(cache_key):
                    logger.info("📋 Returning cached research result")
                    cached_result = self.research_cache[cache_key]['data']
                    result_doc = Document(text=json.dumps(asdict(cached_result)))
                    results.append(result_doc)
                    continue
                
                # Perform research based on type
                if research_req.research_type == "comprehensive":
                    result = await self._comprehensive_research(research_req)
                elif research_req.research_type == "sentiment":
                    result = await self._sentiment_research(research_req)
                elif research_req.research_type == "news":
                    result = await self._news_research(research_req)
                elif research_req.research_type == "technical":
                    result = await self._technical_research(research_req)
                else:
                    result = await self._comprehensive_research(research_req)
                
                # Calculate processing time
                processing_time = time.time() - start_time
                result.processing_time = processing_time
                result.analysis_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Cache the result
                self._cache_result(cache_key, result)
                
                # Create response document
                result_doc = Document(text=json.dumps(asdict(result)))
                results.append(result_doc)
                
                logger.info(f"✅ Research completed in {processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Error processing research request: {e}")
                
                # Return error result
                error_result = ResearchResult(
                    request_id=request_data.get('request_id', ''),
                    query=request_data.get('query', ''),
                    symbol=request_data.get('symbol'),
                    sentiment_score=0.5,
                    confidence=0.0,
                    key_insights=[f"Error: {str(e)}"],
                    trading_signals=[],
                    news_items=[],
                    analysis_timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    processing_time=0.0,
                    research_method="error"
                )
                
                error_doc = Document(text=json.dumps(asdict(error_result)))
                results.append(error_doc)
        
        return results
    
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
            # Use enhanced sentiment analysis
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
            # Use DeepSearch for technical analysis
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
        
        # Clean old cache entries
        current_time = time.time()
        expired_keys = [
            key for key, value in self.research_cache.items()
            if (current_time - value['timestamp']) > self.cache_ttl
        ]
        for key in expired_keys:
            del self.research_cache[key]

# Jina-Serve deployment configuration
if __name__ == "__main__":
    # Create and run the ResearchAgent microservice
    logger.info("🚀 Starting ResearchAgent Microservice with Jina-Serve...")
    
    # This would normally be configured via flow.yml
    # For now, we'll create a simple deployment
    from jina import Flow
    
    flow = Flow(port=8080).add(
        uses=ResearchAgentExecutor,
        name='research_agent',
        replicas=2,  # Scale to 2 instances
        port=8081
    )
    
    with flow:
        logger.info("🧠 ResearchAgent Microservice running on port 8080")
        logger.info("📡 Ready to process research requests via HTTP/gRPC")
        flow.block()
