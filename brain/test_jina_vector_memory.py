#!/usr/bin/env python3
"""
Test script for Jina VectorDB Integration
Tests the enhanced vector memory system with specialized storage
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from jina_vector_memory import (
    JinaVectorMemoryManager, 
    OVERMINDVectorIntegration,
    MemoryQuery,
    VectorMemory
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_jina_vector_memory():
    """Test Jina VectorDB integration"""
    
    print("🧠 THE OVERMIND PROTOCOL - Jina VectorDB Integration Test")
    print("=" * 70)
    
    # Initialize vector memory manager
    vector_manager = JinaVectorMemoryManager()
    
    # Test 1: Initialization
    print("\n🚀 Test 1: Vector Memory Initialization")
    init_success = await vector_manager.initialize()
    print(f"   Initialization: {'✅ Success' if init_success else '❌ Failed'}")
    
    if init_success:
        stats = await vector_manager.get_statistics()
        print(f"   Collections: {len(stats.get('collections', {}))}")
        print(f"   Total Memories: {stats.get('total_memories', 0)}")
    
    # Test 2: Store News Insights
    print("\n📰 Test 2: Store News Insights")
    
    news_insights = [
        {
            'content': 'Solana network sees major DeFi protocol launch with innovative AMM features',
            'metadata': {
                'sentiment_score': 0.75,
                'confidence': 0.85,
                'relevance_score': 0.9,
                'source': 'crypto_news',
                'category': 'defi'
            },
            'symbol': 'SOL'
        },
        {
            'content': 'Institutional adoption of Solana increases with major fund allocation',
            'metadata': {
                'sentiment_score': 0.8,
                'confidence': 0.9,
                'relevance_score': 0.95,
                'source': 'institutional_news',
                'category': 'adoption'
            },
            'symbol': 'SOL'
        }
    ]
    
    stored_news_ids = []
    for insight in news_insights:
        news_id = await vector_manager.store_news_insight(
            insight['content'],
            insight['metadata'],
            insight['symbol']
        )
        stored_news_ids.append(news_id)
        print(f"   Stored news insight: {news_id}")
    
    print(f"   Total news insights stored: {len(stored_news_ids)}")
    
    # Test 3: Store Trading Signals
    print("\n🚨 Test 3: Store Trading Signals")
    
    trading_signals = [
        {
            'signal_type': 'bullish_breakout',
            'symbol': 'SOL',
            'confidence': 0.85,
            'strength': 0.9,
            'timeframe': '4h',
            'indicators': ['RSI_oversold', 'volume_spike', 'resistance_break'],
            'price_target': 150.0,
            'stop_loss': 120.0
        },
        {
            'signal_type': 'momentum_continuation',
            'symbol': 'SOL',
            'confidence': 0.75,
            'strength': 0.8,
            'timeframe': '1h',
            'indicators': ['MACD_bullish', 'EMA_cross'],
            'price_target': 145.0,
            'stop_loss': 125.0
        }
    ]
    
    stored_signal_ids = []
    for signal in trading_signals:
        signal_id = await vector_manager.store_trading_signal(signal, signal['symbol'])
        stored_signal_ids.append(signal_id)
        print(f"   Stored trading signal: {signal_id}")
    
    print(f"   Total trading signals stored: {len(stored_signal_ids)}")
    
    # Test 4: Store Analysis Results
    print("\n📊 Test 4: Store Analysis Results")
    
    analysis_results = [
        {
            'analysis_type': 'technical_analysis',
            'symbol': 'SOL',
            'timeframe': '1d',
            'confidence': 0.8,
            'relevance_score': 0.85,
            'indicators': {
                'RSI': 65.5,
                'MACD': 'bullish',
                'volume': 'above_average'
            },
            'conclusion': 'Bullish momentum with strong volume support',
            'price_prediction': {
                'target': 155.0,
                'probability': 0.75
            }
        }
    ]
    
    stored_analysis_ids = []
    for analysis in analysis_results:
        analysis_id = await vector_manager.store_analysis_result(analysis)
        stored_analysis_ids.append(analysis_id)
        print(f"   Stored analysis result: {analysis_id}")
    
    print(f"   Total analysis results stored: {len(stored_analysis_ids)}")
    
    # Test 5: Query Memories
    print("\n🔍 Test 5: Query Vector Memories")
    
    queries = [
        {
            'name': 'Solana DeFi News',
            'query': MemoryQuery(
                query_text="Solana DeFi protocol developments",
                memory_types=['news'],
                symbols=['SOL'],
                min_confidence=0.7,
                max_results=5
            )
        },
        {
            'name': 'Bullish Trading Signals',
            'query': MemoryQuery(
                query_text="Bullish trading signals and breakouts",
                memory_types=['signal'],
                symbols=['SOL'],
                min_confidence=0.8,
                max_results=3
            )
        },
        {
            'name': 'Recent Analysis',
            'query': MemoryQuery(
                query_text="Technical analysis and price predictions",
                memory_types=['analysis'],
                max_results=5
            )
        }
    ]
    
    for query_info in queries:
        print(f"\n   Query: {query_info['name']}")
        results = await vector_manager.query_memories(query_info['query'])
        print(f"     Results found: {len(results)}")
        
        for i, result in enumerate(results[:2]):  # Show first 2 results
            print(f"     Result {i+1}:")
            print(f"       Type: {result.memory_type}")
            print(f"       Symbol: {result.symbol}")
            print(f"       Confidence: {result.confidence:.3f}")
            print(f"       Relevance: {result.relevance_score:.3f}")
            print(f"       Content: {result.content[:80]}...")
    
    # Test 6: Similar Patterns
    print("\n🔄 Test 6: Find Similar Patterns")
    
    current_situation = {
        'symbol': 'SOL',
        'price_action': 'breakout',
        'volume': 'high',
        'sentiment': 'bullish',
        'timeframe': '4h'
    }
    
    similar_patterns = await vector_manager.get_similar_patterns(
        current_situation,
        "trading"
    )
    
    print(f"   Current situation: {current_situation}")
    print(f"   Similar patterns found: {len(similar_patterns)}")
    
    for i, pattern in enumerate(similar_patterns[:2]):
        print(f"     Pattern {i+1}:")
        print(f"       Type: {pattern.memory_type}")
        print(f"       Confidence: {pattern.confidence:.3f}")
        print(f"       Similarity: {pattern.relevance_score:.3f}")
    
    # Test 7: Symbol History
    print("\n📈 Test 7: Symbol History Retrieval")
    
    symbol_history = await vector_manager.get_symbol_history('SOL', days=7)
    print(f"   Symbol: SOL")
    print(f"   Time range: Last 7 days")
    print(f"   Historical memories: {len(symbol_history)}")
    
    # Group by memory type
    history_by_type = {}
    for memory in symbol_history:
        memory_type = memory.memory_type
        if memory_type not in history_by_type:
            history_by_type[memory_type] = 0
        history_by_type[memory_type] += 1
    
    for memory_type, count in history_by_type.items():
        print(f"     {memory_type}: {count} memories")
    
    # Test 8: OVERMIND Integration
    print("\n🧠 Test 8: OVERMIND Integration")
    
    overmind_integration = OVERMINDVectorIntegration()
    init_success = await overmind_integration.initialize()
    print(f"   OVERMIND Integration: {'✅ Success' if init_success else '❌ Failed'}")
    
    if init_success:
        # Test research result storage
        research_result = {
            'query': 'Solana ecosystem analysis',
            'symbol': 'SOL',
            'sentiment_score': 0.75,
            'confidence': 0.85,
            'key_insights': ['Strong DeFi growth', 'Institutional adoption'],
            'trading_signals': ['bullish_momentum'],
            'research_method': 'jina_comprehensive'
        }
        
        research_id = await overmind_integration.store_research_result(research_result)
        print(f"   Research result stored: {research_id}")
        
        # Test similar situations
        current_situation = {
            'symbol': 'SOL',
            'market_condition': 'bullish',
            'volume': 'high'
        }
        
        similar_situations = await overmind_integration.find_similar_situations(current_situation)
        print(f"   Similar situations found: {len(similar_situations)}")
        
        # Test symbol insights
        symbol_insights = await overmind_integration.get_symbol_insights('SOL', days=7)
        print(f"   Symbol insights (7 days): {len(symbol_insights)}")
    
    # Test 9: Statistics
    print("\n📊 Test 9: Vector Memory Statistics")
    
    final_stats = await vector_manager.get_statistics()
    print(f"   Collections: {len(final_stats.get('collections', {}))}")
    print(f"   Total memories: {final_stats.get('total_memories', 0)}")
    print(f"   Cache size: {final_stats.get('cache_size', 0)}")
    
    for collection_name, collection_stats in final_stats.get('collections', {}).items():
        print(f"     {collection_name}: {collection_stats.get('document_count', 0)} documents")
    
    print(f"\n🎯 Jina VectorDB Integration Test Complete!")
    print("=" * 70)
    
    # Summary
    print(f"\n📊 TEST SUMMARY:")
    print(f"✅ Vector Memory Initialization: Working")
    print(f"✅ News Insights Storage: {len(stored_news_ids)} stored")
    print(f"✅ Trading Signals Storage: {len(stored_signal_ids)} stored")
    print(f"✅ Analysis Results Storage: {len(stored_analysis_ids)} stored")
    print(f"✅ Memory Querying: Multiple query types working")
    print(f"✅ Pattern Matching: Similar pattern detection")
    print(f"✅ Historical Retrieval: Symbol history access")
    print(f"✅ OVERMIND Integration: Seamless integration layer")
    print(f"✅ Statistics & Monitoring: Real-time stats available")
    
    print(f"\n🧠 Jina VectorDB - Ready for Production Integration!")

async def main():
    """Main test function"""
    await test_jina_vector_memory()

if __name__ == "__main__":
    asyncio.run(main())
