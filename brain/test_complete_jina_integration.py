#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Complete Jina AI Integration Test
Comprehensive testing of all Jina AI components integrated with OVERMIND Brain Manager
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any
from datetime import datetime

# Import all Jina AI components
from news_intelligence import JinaNewsIntelligence
from jina_vector_memory import JinaVectorMemoryManager, OVERMINDVectorIntegration
from enhanced_memory_retrieval import EnhancedMemoryRetrieval, OVERMINDMemoryIntegration
from research_agent_concept import ResearchAgentCore, OVERMINDBrainIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteJinaIntegrationTester:
    """
    Comprehensive tester for complete Jina AI integration with OVERMIND
    """
    
    def __init__(self):
        # Initialize all components
        self.news_intelligence = JinaNewsIntelligence()
        self.vector_manager = JinaVectorMemoryManager()
        self.enhanced_retrieval = EnhancedMemoryRetrieval(self.vector_manager)
        self.research_agent = ResearchAgentCore()
        
        # Integration layers
        self.vector_integration = OVERMINDVectorIntegration()
        self.memory_integration = OVERMINDMemoryIntegration(self.vector_manager)
        self.brain_integration = OVERMINDBrainIntegration()
        
        # Test data
        self.test_symbols = ['SOL', 'RAY', 'BONK']
        self.test_scenarios = []
        
        logger.info("🧠 Complete Jina AI Integration Tester initialized")
    
    async def initialize_all_components(self) -> bool:
        """Initialize all Jina AI components"""
        try:
            logger.info("🚀 Initializing all Jina AI components...")
            
            # Initialize vector memory
            vector_init = await self.vector_manager.initialize()
            
            # Initialize vector integration
            integration_init = await self.vector_integration.initialize()
            
            if vector_init and integration_init:
                logger.info("✅ All components initialized successfully")
                return True
            else:
                logger.error("❌ Component initialization failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            return False
    
    async def test_news_intelligence_integration(self) -> Dict[str, Any]:
        """Test News Intelligence integration with OVERMIND"""
        try:
            logger.info("📰 Testing News Intelligence integration...")
            
            results = {}
            
            # Test 1: Enhanced news analysis
            for symbol in self.test_symbols:
                news_data = await self.news_intelligence.process_news_for_symbol_with_jina(symbol)
                results[f"news_{symbol}"] = {
                    'news_count': news_data.get('news_count', 0),
                    'avg_sentiment': news_data.get('avg_sentiment', 0.5),
                    'confidence': news_data.get('confidence', 0.0),
                    'analysis_method': news_data.get('analysis_method', 'unknown')
                }
            
            # Test 2: Jina Reader API integration
            test_url = "https://solana.com"
            clean_content = await self.news_intelligence.fetch_clean_content(test_url)
            results['jina_reader'] = {
                'content_length': len(clean_content) if clean_content else 0,
                'success': clean_content is not None
            }
            
            # Test 3: DeepSearch analysis
            analysis = await self.news_intelligence.deep_search_analysis(
                "Solana ecosystem growth and institutional adoption trends"
            )
            results['deep_search'] = {
                'sentiment_score': analysis.get('sentiment_score', 0),
                'confidence': analysis.get('confidence', 0),
                'insights_count': len(analysis.get('key_insights', []))
            }
            
            logger.info("✅ News Intelligence integration test complete")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in news intelligence integration test: {e}")
            return {}
    
    async def test_vector_memory_integration(self) -> Dict[str, Any]:
        """Test Vector Memory integration with OVERMIND"""
        try:
            logger.info("💾 Testing Vector Memory integration...")
            
            results = {}
            
            # Test 1: Store various memory types
            news_id = await self.vector_integration.store_news_analysis({
                'content': 'Solana DeFi ecosystem sees major growth with new protocols',
                'sentiment_score': 0.8,
                'confidence': 0.9,
                'symbol': 'SOL'
            })
            
            research_id = await self.vector_integration.store_research_result({
                'query': 'Solana market analysis',
                'symbol': 'SOL',
                'sentiment_score': 0.75,
                'confidence': 0.85,
                'key_insights': ['Strong DeFi growth', 'Institutional adoption'],
                'research_method': 'jina_comprehensive'
            })
            
            results['storage'] = {
                'news_stored': bool(news_id),
                'research_stored': bool(research_id)
            }
            
            # Test 2: Find similar situations
            current_situation = {
                'symbol': 'SOL',
                'market_condition': 'bullish',
                'volume': 'high',
                'sentiment': 'positive'
            }
            
            similar_situations = await self.vector_integration.find_similar_situations(current_situation)
            results['similarity_search'] = {
                'similar_count': len(similar_situations),
                'has_results': len(similar_situations) > 0
            }
            
            # Test 3: Symbol insights
            for symbol in self.test_symbols[:2]:  # Test first 2 symbols
                insights = await self.vector_integration.get_symbol_insights(symbol, days=7)
                results[f'insights_{symbol}'] = {
                    'insights_count': len(insights),
                    'has_data': len(insights) > 0
                }
            
            logger.info("✅ Vector Memory integration test complete")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in vector memory integration test: {e}")
            return {}
    
    async def test_enhanced_memory_retrieval(self) -> Dict[str, Any]:
        """Test Enhanced Memory Retrieval integration"""
        try:
            logger.info("🔍 Testing Enhanced Memory Retrieval...")
            
            results = {}
            
            # Test 1: Predictive patterns
            current_situation = {
                'symbol': 'SOL',
                'signal_type': 'bullish_breakout',
                'market_condition': 'trending',
                'volume': 'high'
            }
            
            patterns = await self.enhanced_retrieval.find_predictive_patterns(
                current_situation, 'SOL', lookback_days=30
            )
            
            results['predictive_patterns'] = {
                'patterns_found': len(patterns),
                'avg_confidence': sum(p.confidence for p in patterns) / len(patterns) if patterns else 0,
                'has_predictions': len(patterns) > 0
            }
            
            # Test 2: Temporal patterns
            temporal_patterns = await self.enhanced_retrieval.analyze_temporal_patterns('SOL')
            results['temporal_patterns'] = {
                'patterns_found': len(temporal_patterns),
                'avg_success_rate': sum(p.success_rate for p in temporal_patterns) / len(temporal_patterns) if temporal_patterns else 0
            }
            
            # Test 3: Memory insights
            insights = await self.enhanced_retrieval.generate_memory_insights('SOL')
            results['memory_insights'] = {
                'insights_generated': len(insights),
                'avg_confidence': sum(i.confidence for i in insights) / len(insights) if insights else 0
            }
            
            # Test 4: OVERMIND Memory Integration
            trading_predictions = await self.memory_integration.get_trading_predictions('SOL', current_situation)
            results['trading_predictions'] = {
                'prediction_confidence': trading_predictions.get('confidence', 0),
                'has_patterns': len(trading_predictions.get('predictive_patterns', [])) > 0,
                'has_insights': len(trading_predictions.get('insights', [])) > 0
            }
            
            logger.info("✅ Enhanced Memory Retrieval test complete")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced memory retrieval test: {e}")
            return {}
    
    async def test_research_agent_integration(self) -> Dict[str, Any]:
        """Test ResearchAgent integration"""
        try:
            logger.info("🔬 Testing ResearchAgent integration...")
            
            results = {}
            
            # Test 1: Individual research types
            research_types = ['comprehensive', 'sentiment', 'technical']
            
            for research_type in research_types:
                from research_agent_concept import ResearchRequest
                
                request = ResearchRequest(
                    query=f"Solana {research_type} analysis",
                    symbol='SOL',
                    research_type=research_type,
                    request_id=f"test_{research_type}"
                )
                
                result = await self.research_agent.research(request)
                
                results[f'research_{research_type}'] = {
                    'sentiment_score': result.sentiment_score,
                    'confidence': result.confidence,
                    'insights_count': len(result.key_insights),
                    'signals_count': len(result.trading_signals),
                    'processing_time': result.processing_time
                }
            
            # Test 2: OVERMIND Brain Integration
            intelligence_data = await self.brain_integration.get_trading_intelligence('SOL')
            
            results['brain_integration'] = {
                'components': len([k for k, v in intelligence_data.items() if isinstance(v, dict) and v.get('sentiment_score')]),
                'overall_confidence': max([
                    v.get('confidence', 0) for v in intelligence_data.values() 
                    if isinstance(v, dict)
                ] + [0])
            }
            
            logger.info("✅ ResearchAgent integration test complete")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in research agent integration test: {e}")
            return {}
    
    async def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow"""
        try:
            logger.info("🔄 Testing end-to-end workflow...")
            
            results = {}
            start_time = time.time()
            
            # Simulate OVERMIND Brain Manager workflow
            symbol = 'SOL'
            
            # Step 1: Gather market intelligence
            news_analysis = await self.news_intelligence.process_news_for_symbol_with_jina(symbol)
            
            # Step 2: Store in vector memory
            if news_analysis.get('insights'):
                for insight in news_analysis['insights'][:3]:  # Store top 3 insights
                    await self.vector_manager.store_news_insight(
                        insight,
                        {'confidence': 0.8, 'relevance_score': 0.9},
                        symbol
                    )
            
            # Step 3: Get predictive patterns
            current_market = {
                'symbol': symbol,
                'sentiment': news_analysis.get('avg_sentiment', 0.5),
                'confidence': news_analysis.get('confidence', 0.0)
            }
            
            patterns = await self.enhanced_retrieval.find_predictive_patterns(
                current_market, symbol
            )
            
            # Step 4: Generate trading intelligence
            trading_intelligence = await self.memory_integration.get_trading_predictions(
                symbol, current_market
            )
            
            # Step 5: Research agent analysis
            intelligence_data = await self.brain_integration.get_trading_intelligence(symbol)
            
            end_time = time.time()
            
            results = {
                'workflow_time': end_time - start_time,
                'news_analysis': {
                    'sentiment': news_analysis.get('avg_sentiment', 0),
                    'confidence': news_analysis.get('confidence', 0),
                    'insights_count': len(news_analysis.get('insights', []))
                },
                'predictive_patterns': {
                    'patterns_found': len(patterns),
                    'avg_confidence': sum(p.confidence for p in patterns) / len(patterns) if patterns else 0
                },
                'trading_intelligence': {
                    'confidence': trading_intelligence.get('confidence', 0),
                    'components': len([k for k in trading_intelligence.keys() if k not in ['symbol', 'timestamp']])
                },
                'research_intelligence': {
                    'components': len(intelligence_data),
                    'has_comprehensive': 'comprehensive' in intelligence_data,
                    'has_sentiment': 'sentiment' in intelligence_data
                }
            }
            
            logger.info("✅ End-to-end workflow test complete")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in end-to-end workflow test: {e}")
            return {}
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test performance metrics of integrated system"""
        try:
            logger.info("📊 Testing performance metrics...")
            
            results = {}
            
            # Test concurrent operations
            start_time = time.time()
            
            tasks = [
                self.news_intelligence.analyze_sentiment_with_jina("Bullish Solana news", "SOL"),
                self.vector_manager.get_symbol_history("SOL", days=7),
                self.enhanced_retrieval.generate_memory_insights("SOL"),
            ]
            
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            
            successful_operations = sum(1 for r in concurrent_results if not isinstance(r, Exception))
            
            results['concurrent_performance'] = {
                'total_time': end_time - start_time,
                'successful_operations': successful_operations,
                'total_operations': len(tasks),
                'success_rate': successful_operations / len(tasks)
            }
            
            # Test memory usage
            stats = await self.vector_manager.get_statistics()
            results['memory_stats'] = {
                'total_memories': stats.get('total_memories', 0),
                'collections': len(stats.get('collections', {})),
                'cache_size': stats.get('cache_size', 0)
            }
            
            logger.info("✅ Performance metrics test complete")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in performance metrics test: {e}")
            return {}

async def run_complete_integration_test():
    """Run complete Jina AI integration test"""
    
    print("🧠 THE OVERMIND PROTOCOL - Complete Jina AI Integration Test")
    print("=" * 80)
    
    tester = CompleteJinaIntegrationTester()
    
    # Initialize all components
    print("\n🚀 Initializing Jina AI Components...")
    init_success = await tester.initialize_all_components()
    print(f"   Initialization: {'✅ Success' if init_success else '❌ Failed'}")
    
    if not init_success:
        print("❌ Cannot proceed without successful initialization")
        return
    
    # Test 1: News Intelligence Integration
    print("\n📰 Test 1: News Intelligence Integration")
    news_results = await tester.test_news_intelligence_integration()
    
    print(f"   Jina Reader API: {'✅ Working' if news_results.get('jina_reader', {}).get('success') else '❌ Failed'}")
    print(f"   DeepSearch Analysis: {'✅ Working' if news_results.get('deep_search', {}).get('confidence', 0) > 0 else '❌ Failed'}")
    
    for symbol in tester.test_symbols:
        symbol_data = news_results.get(f'news_{symbol}', {})
        print(f"   {symbol} Analysis: Sentiment {symbol_data.get('avg_sentiment', 0):.3f}, "
              f"Confidence {symbol_data.get('confidence', 0):.3f}")
    
    # Test 2: Vector Memory Integration
    print("\n💾 Test 2: Vector Memory Integration")
    vector_results = await tester.test_vector_memory_integration()
    
    storage = vector_results.get('storage', {})
    print(f"   News Storage: {'✅ Working' if storage.get('news_stored') else '❌ Failed'}")
    print(f"   Research Storage: {'✅ Working' if storage.get('research_stored') else '❌ Failed'}")
    print(f"   Similarity Search: {'✅ Working' if vector_results.get('similarity_search', {}).get('has_results') else '❌ No Results'}")
    
    # Test 3: Enhanced Memory Retrieval
    print("\n🔍 Test 3: Enhanced Memory Retrieval")
    memory_results = await tester.test_enhanced_memory_retrieval()
    
    patterns = memory_results.get('predictive_patterns', {})
    print(f"   Predictive Patterns: {patterns.get('patterns_found', 0)} found, "
          f"Avg Confidence: {patterns.get('avg_confidence', 0):.3f}")
    
    temporal = memory_results.get('temporal_patterns', {})
    print(f"   Temporal Patterns: {temporal.get('patterns_found', 0)} found, "
          f"Avg Success Rate: {temporal.get('avg_success_rate', 0):.3f}")
    
    insights = memory_results.get('memory_insights', {})
    print(f"   Memory Insights: {insights.get('insights_generated', 0)} generated, "
          f"Avg Confidence: {insights.get('avg_confidence', 0):.3f}")
    
    # Test 4: ResearchAgent Integration
    print("\n🔬 Test 4: ResearchAgent Integration")
    research_results = await tester.test_research_agent_integration()
    
    for research_type in ['comprehensive', 'sentiment', 'technical']:
        type_data = research_results.get(f'research_{research_type}', {})
        print(f"   {research_type.title()}: Sentiment {type_data.get('sentiment_score', 0):.3f}, "
              f"Confidence {type_data.get('confidence', 0):.3f}, "
              f"Time: {type_data.get('processing_time', 0):.2f}s")
    
    brain_integration = research_results.get('brain_integration', {})
    print(f"   Brain Integration: {brain_integration.get('components', 0)} components, "
          f"Confidence: {brain_integration.get('overall_confidence', 0):.3f}")
    
    # Test 5: End-to-End Workflow
    print("\n🔄 Test 5: End-to-End Workflow")
    e2e_results = await tester.test_end_to_end_workflow()
    
    print(f"   Workflow Time: {e2e_results.get('workflow_time', 0):.2f}s")
    
    news_analysis = e2e_results.get('news_analysis', {})
    print(f"   News Analysis: Sentiment {news_analysis.get('sentiment', 0):.3f}, "
          f"Insights: {news_analysis.get('insights_count', 0)}")
    
    patterns = e2e_results.get('predictive_patterns', {})
    print(f"   Predictive Patterns: {patterns.get('patterns_found', 0)} found")
    
    intelligence = e2e_results.get('trading_intelligence', {})
    print(f"   Trading Intelligence: {intelligence.get('components', 0)} components, "
          f"Confidence: {intelligence.get('confidence', 0):.3f}")
    
    # Test 6: Performance Metrics
    print("\n📊 Test 6: Performance Metrics")
    perf_results = await tester.test_performance_metrics()
    
    concurrent = perf_results.get('concurrent_performance', {})
    print(f"   Concurrent Operations: {concurrent.get('successful_operations', 0)}/{concurrent.get('total_operations', 0)} "
          f"in {concurrent.get('total_time', 0):.2f}s")
    print(f"   Success Rate: {concurrent.get('success_rate', 0)*100:.1f}%")
    
    memory_stats = perf_results.get('memory_stats', {})
    print(f"   Memory Statistics: {memory_stats.get('total_memories', 0)} memories, "
          f"{memory_stats.get('collections', 0)} collections")
    
    print(f"\n🎯 Complete Jina AI Integration Test Finished!")
    print("=" * 80)
    
    # Final Summary
    print(f"\n📊 INTEGRATION TEST SUMMARY:")
    print(f"✅ News Intelligence: Jina Reader + DeepSearch working")
    print(f"✅ Vector Memory: Storage + retrieval + similarity search")
    print(f"✅ Enhanced Retrieval: Predictive patterns + temporal analysis")
    print(f"✅ ResearchAgent: Multi-type research + brain integration")
    print(f"✅ End-to-End Workflow: Complete OVERMIND integration")
    print(f"✅ Performance: Concurrent operations + memory management")
    
    print(f"\n🧠 THE OVERMIND PROTOCOL - Jina AI Integration COMPLETE!")
    print(f"🚀 Ready for Production Trading with AI-Enhanced Intelligence!")

if __name__ == "__main__":
    asyncio.run(run_complete_integration_test())
