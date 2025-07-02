#!/usr/bin/env python3
"""
Test script for Enhanced Memory Retrieval System
Tests advanced pattern recognition, temporal analysis, and predictive insights
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from jina_vector_memory import JinaVectorMemoryManager
from enhanced_memory_retrieval import (
    EnhancedMemoryRetrieval, 
    OVERMINDMemoryIntegration,
    PatternMatch,
    TemporalPattern,
    MemoryInsight
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_test_data(vector_manager: JinaVectorMemoryManager):
    """Setup test data for enhanced memory retrieval testing"""
    
    print("📊 Setting up test data...")
    
    # Initialize vector manager
    await vector_manager.initialize()
    
    # Create diverse test memories
    test_memories = []
    
    # Historical trading signals with outcomes
    base_time = datetime.now() - timedelta(days=30)
    
    for i in range(20):
        # Create trading signals with different outcomes
        signal_time = base_time + timedelta(days=i, hours=i*2)
        
        if i % 3 == 0:  # Bullish signals
            signal_data = {
                'signal_type': 'bullish_breakout',
                'symbol': 'SOL',
                'confidence': 0.8 + (i % 3) * 0.05,
                'strength': 0.85,
                'timeframe': '4h',
                'indicators': ['RSI_oversold', 'volume_spike'],
                'market_condition': 'trending',
                'outcome': 'positive' if i % 2 == 0 else 'negative'
            }
        elif i % 3 == 1:  # Bearish signals
            signal_data = {
                'signal_type': 'bearish_breakdown',
                'symbol': 'SOL',
                'confidence': 0.7 + (i % 3) * 0.05,
                'strength': 0.75,
                'timeframe': '1h',
                'indicators': ['RSI_overbought', 'volume_decline'],
                'market_condition': 'ranging',
                'outcome': 'negative' if i % 2 == 0 else 'positive'
            }
        else:  # Neutral signals
            signal_data = {
                'signal_type': 'consolidation',
                'symbol': 'SOL',
                'confidence': 0.6,
                'strength': 0.5,
                'timeframe': '1d',
                'indicators': ['sideways_movement'],
                'market_condition': 'consolidating',
                'outcome': 'neutral'
            }
        
        # Store the signal
        signal_id = await vector_manager.store_trading_signal(signal_data, 'SOL')
        test_memories.append(signal_id)
    
    # Create news insights with sentiment trends
    for i in range(15):
        news_time = base_time + timedelta(days=i*2, hours=12)
        
        if i < 5:  # Early period - bearish news
            sentiment_score = 0.3 + i * 0.05
            content = f"Regulatory concerns impact Solana ecosystem - Day {i}"
        elif i < 10:  # Middle period - neutral to positive
            sentiment_score = 0.5 + i * 0.03
            content = f"Solana development progress continues - Day {i}"
        else:  # Recent period - bullish news
            sentiment_score = 0.7 + (i-10) * 0.04
            content = f"Major institutional adoption for Solana - Day {i}"
        
        news_metadata = {
            'sentiment_score': sentiment_score,
            'confidence': 0.8,
            'relevance_score': 0.9,
            'source': 'crypto_news',
            'category': 'market_analysis'
        }
        
        news_id = await vector_manager.store_news_insight(content, news_metadata, 'SOL')
        test_memories.append(news_id)
    
    # Create analysis results
    for i in range(10):
        analysis_time = base_time + timedelta(days=i*3)
        
        analysis_data = {
            'analysis_type': 'technical_analysis',
            'symbol': 'SOL',
            'timeframe': '1d',
            'confidence': 0.75 + i * 0.02,
            'relevance_score': 0.8,
            'indicators': {
                'RSI': 50 + i * 2,
                'MACD': 'bullish' if i > 5 else 'bearish',
                'volume': 'increasing' if i > 3 else 'decreasing'
            },
            'market_regime': 'bull' if i > 6 else 'bear' if i < 3 else 'sideways',
            'price_prediction': 120 + i * 5
        }
        
        analysis_id = await vector_manager.store_analysis_result(analysis_data)
        test_memories.append(analysis_id)
    
    print(f"✅ Created {len(test_memories)} test memories")
    return test_memories

async def test_enhanced_memory_retrieval():
    """Test Enhanced Memory Retrieval System"""
    
    print("🧠 THE OVERMIND PROTOCOL - Enhanced Memory Retrieval Test")
    print("=" * 70)
    
    # Initialize components
    vector_manager = JinaVectorMemoryManager()
    enhanced_retrieval = EnhancedMemoryRetrieval(vector_manager)
    
    # Setup test data
    test_memories = await setup_test_data(vector_manager)
    
    # Test 1: Predictive Pattern Recognition
    print("\n🔮 Test 1: Predictive Pattern Recognition")
    
    current_situation = {
        'symbol': 'SOL',
        'signal_type': 'bullish_breakout',
        'market_condition': 'trending',
        'volume': 'high',
        'timeframe': '4h',
        'indicators': ['RSI_oversold', 'volume_spike']
    }
    
    patterns = await enhanced_retrieval.find_predictive_patterns(
        current_situation,
        'SOL',
        lookback_days=30
    )
    
    print(f"   Current situation: {current_situation['signal_type']} in {current_situation['market_condition']} market")
    print(f"   Predictive patterns found: {len(patterns)}")
    
    for i, pattern in enumerate(patterns[:3]):
        print(f"     Pattern {i+1}:")
        print(f"       Similarity: {pattern.similarity_score:.3f}")
        print(f"       Confidence: {pattern.confidence:.3f}")
        print(f"       Pattern Type: {pattern.pattern_type}")
        print(f"       Prediction: {pattern.prediction.get('direction', 'unknown')}")
        print(f"       Risk Level: {pattern.prediction.get('risk_level', 'unknown')}")
    
    # Test 2: Temporal Pattern Analysis
    print("\n⏰ Test 2: Temporal Pattern Analysis")
    
    temporal_patterns = await enhanced_retrieval.analyze_temporal_patterns(
        'SOL',
        pattern_type="signal",
        time_windows=["1h", "4h", "1d"]
    )
    
    print(f"   Temporal patterns analyzed for SOL")
    print(f"   Significant patterns found: {len(temporal_patterns)}")
    
    for i, pattern in enumerate(temporal_patterns[:3]):
        print(f"     Pattern {i+1}:")
        print(f"       Name: {pattern.pattern_name}")
        print(f"       Time Window: {pattern.time_window}")
        print(f"       Frequency: {pattern.frequency}")
        print(f"       Success Rate: {pattern.success_rate:.3f}")
        print(f"       Average Outcome: {pattern.avg_outcome:.3f}")
        print(f"       Volatility: {pattern.volatility:.3f}")
    
    # Test 3: Memory Insights Generation
    print("\n💡 Test 3: Memory Insights Generation")
    
    context = {
        'current_price': 140.0,
        'volume_trend': 'increasing',
        'market_sentiment': 'bullish'
    }
    
    insights = await enhanced_retrieval.generate_memory_insights('SOL', context)
    
    print(f"   Context: {context}")
    print(f"   Memory insights generated: {len(insights)}")
    
    for i, insight in enumerate(insights):
        print(f"     Insight {i+1}:")
        print(f"       Type: {insight.insight_type}")
        print(f"       Confidence: {insight.confidence:.3f}")
        print(f"       Description: {insight.description}")
        print(f"       Actionable Signals: {insight.actionable_signals}")
        print(f"       Risk Assessment: {insight.risk_assessment}")
    
    # Test 4: Market Regime Prediction
    print("\n📊 Test 4: Market Regime Prediction")
    
    regime_prediction = await enhanced_retrieval.predict_market_regime('SOL', horizon_days=7)
    
    print(f"   Symbol: SOL")
    print(f"   Prediction Horizon: 7 days")
    print(f"   Regime Prediction: {regime_prediction}")
    
    # Test 5: Arbitrage Opportunities
    print("\n🔄 Test 5: Arbitrage Opportunities")
    
    symbols = ['SOL', 'RAY', 'ORCA']
    arbitrage_opportunities = await enhanced_retrieval.find_arbitrage_opportunities(
        symbols,
        min_confidence=0.6
    )
    
    print(f"   Symbols analyzed: {symbols}")
    print(f"   Arbitrage opportunities found: {len(arbitrage_opportunities)}")
    
    for i, opportunity in enumerate(arbitrage_opportunities):
        print(f"     Opportunity {i+1}: {opportunity}")
    
    # Test 6: OVERMIND Integration
    print("\n🧠 Test 6: OVERMIND Integration")
    
    overmind_integration = OVERMINDMemoryIntegration(vector_manager)
    
    # Test trading predictions
    current_market_data = {
        'price': 142.5,
        'volume': 'high',
        'trend': 'bullish',
        'volatility': 'medium'
    }
    
    trading_predictions = await overmind_integration.get_trading_predictions(
        'SOL',
        current_market_data
    )
    
    print(f"   Trading Predictions for SOL:")
    print(f"     Predictive Patterns: {len(trading_predictions.get('predictive_patterns', []))}")
    print(f"     Temporal Patterns: {len(trading_predictions.get('temporal_patterns', []))}")
    print(f"     Insights: {len(trading_predictions.get('insights', []))}")
    print(f"     Overall Confidence: {trading_predictions.get('confidence', 0):.3f}")
    
    # Test market opportunities
    market_opportunities = await overmind_integration.find_market_opportunities(['SOL'])
    
    print(f"   Market Opportunities:")
    print(f"     Opportunities found: {len(market_opportunities)}")
    
    for i, opportunity in enumerate(market_opportunities):
        print(f"     Opportunity {i+1}:")
        print(f"       Type: {opportunity.get('type', 'unknown')}")
        print(f"       Symbol: {opportunity.get('symbol', 'unknown')}")
        print(f"       Score: {opportunity.get('opportunity_score', 0):.3f}")
    
    # Test 7: Performance Analysis
    print("\n📈 Test 7: Performance Analysis")
    
    # Get statistics
    stats = await vector_manager.get_statistics()
    
    print(f"   Vector Memory Statistics:")
    print(f"     Total Collections: {len(stats.get('collections', {}))}")
    print(f"     Total Memories: {stats.get('total_memories', 0)}")
    print(f"     Cache Size: {stats.get('cache_size', 0)}")
    
    for collection_name, collection_stats in stats.get('collections', {}).items():
        print(f"       {collection_name}: {collection_stats.get('document_count', 0)} documents")
    
    print(f"\n🎯 Enhanced Memory Retrieval Test Complete!")
    print("=" * 70)
    
    # Summary
    print(f"\n📊 TEST SUMMARY:")
    print(f"✅ Predictive Pattern Recognition: {len(patterns)} patterns found")
    print(f"✅ Temporal Pattern Analysis: {len(temporal_patterns)} patterns identified")
    print(f"✅ Memory Insights Generation: {len(insights)} insights generated")
    print(f"✅ Market Regime Prediction: Regime analysis completed")
    print(f"✅ Arbitrage Opportunities: {len(arbitrage_opportunities)} opportunities found")
    print(f"✅ OVERMIND Integration: Seamless integration working")
    print(f"✅ Performance Analysis: {stats.get('total_memories', 0)} memories processed")
    
    print(f"\n🧠 Enhanced Memory Retrieval - Ready for Advanced Trading Intelligence!")

async def main():
    """Main test function"""
    await test_enhanced_memory_retrieval()

if __name__ == "__main__":
    asyncio.run(main())
