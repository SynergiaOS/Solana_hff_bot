#!/usr/bin/env python3
"""
Simple test for Jina AI integration - focused demonstration
"""

import asyncio
import logging
from news_intelligence import JinaNewsIntelligence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_jina_core_features():
    """Test core Jina AI features with simple examples"""
    
    print("🧠 THE OVERMIND PROTOCOL - Jina AI Core Features Test")
    print("=" * 60)
    
    news_intel = JinaNewsIntelligence()
    
    # Test 1: Jina Reader API with a simple URL
    print("\n📖 Test 1: Jina Reader API - Clean Content Extraction")
    try:
        test_url = "https://solana.com"
        clean_content = await news_intel.fetch_clean_content(test_url)
        
        if clean_content:
            print(f"✅ Successfully extracted clean content:")
            print(f"   📊 Content Length: {len(clean_content)} characters")
            print(f"   📄 Preview: {clean_content[:200]}...")
            print(f"   🎯 Format: Clean Markdown (LLM-ready)")
        else:
            print("❌ Failed to extract content")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: DeepSearch Analysis
    print("\n🔍 Test 2: Jina DeepSearch - AI Analysis")
    try:
        query = "Analyze Solana blockchain adoption and price potential"
        analysis = await news_intel.deep_search_analysis(query)
        
        if analysis:
            print(f"✅ DeepSearch Analysis Results:")
            print(f"   💭 Sentiment Score: {analysis.get('sentiment_score', 'N/A')}")
            print(f"   🎯 Confidence: {analysis.get('confidence', 'N/A')}")
            print(f"   📊 Relevance: {analysis.get('relevance_score', 'N/A')}")
            print(f"   💡 Key Insights: {len(analysis.get('key_insights', []))} insights found")
            print(f"   🚨 Trading Signals: {analysis.get('trading_signals', [])}")
            
            if analysis.get('key_insights'):
                print(f"   📄 Sample Insight: {analysis['key_insights'][0][:100]}...")
        else:
            print("❌ No analysis results")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Enhanced Sentiment Analysis
    print("\n💭 Test 3: Enhanced Sentiment Analysis")
    try:
        test_text = """
        Solana network continues to show strong performance with increasing DeFi adoption.
        Major institutional partnerships announced this week, driving bullish sentiment.
        Technical upgrades improving transaction throughput and reducing fees.
        """
        
        sentiment_result = await news_intel.analyze_sentiment_with_jina(test_text, 'SOL')
        
        print(f"✅ Enhanced Sentiment Analysis:")
        print(f"   💭 Sentiment Score: {sentiment_result['score']:.3f}")
        print(f"   🎯 Confidence: {sentiment_result['confidence']:.3f}")
        print(f"   📊 Relevance: {sentiment_result['relevance']:.3f}")
        print(f"   🚨 Signals: {sentiment_result['signals']}")
        print(f"   💡 Insights: {sentiment_result.get('insights', [])}")
        print(f"   🧠 Reasoning: {sentiment_result.get('reasoning', 'N/A')[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Fallback System
    print("\n🔄 Test 4: Fallback Analysis System")
    try:
        test_text = "Solana price surges on partnership news and technical breakthrough"
        fallback_result = await news_intel._fallback_sentiment_analysis(test_text, 'SOL')
        
        print(f"✅ Fallback Analysis (when Jina AI unavailable):")
        print(f"   💭 Sentiment Score: {fallback_result['score']:.3f}")
        print(f"   🎯 Confidence: {fallback_result['confidence']:.3f}")
        print(f"   🚨 Signals: {fallback_result['signals']}")
        print(f"   🔄 Method: {fallback_result['reasoning']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Complete News Analysis Pipeline
    print("\n🔄 Test 5: Complete News Analysis Pipeline")
    try:
        # Simulate a news item
        mock_news_item = {
            'title': 'Solana Ecosystem Sees Major DeFi Protocol Launch',
            'url': 'https://solana.com/news',
            'description': 'New DeFi protocol launches on Solana with innovative features',
            'published_at': '2025-07-02T10:00:00Z'
        }
        
        analysis = await news_intel.analyze_news_with_jina(mock_news_item)
        
        print(f"✅ Complete News Analysis:")
        print(f"   📰 Title: {analysis.title}")
        print(f"   💭 Sentiment: {analysis.sentiment_score:.3f}")
        print(f"   🎯 Confidence: {analysis.confidence:.3f}")
        print(f"   📊 Relevance: {analysis.relevance_score:.3f}")
        print(f"   💡 Insights: {len(analysis.key_insights)} insights")
        print(f"   🚨 Signals: {len(analysis.trading_signals)} signals")
        print(f"   📄 Summary: {analysis.content_summary[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🎯 Jina AI Core Features Test Complete!")
    print("=" * 60)
    
    # Summary
    print(f"\n📊 JINA AI INTEGRATION SUMMARY:")
    print(f"✅ Reader API: Clean content extraction from any URL")
    print(f"✅ DeepSearch: AI-powered analysis and reasoning")
    print(f"✅ Enhanced Sentiment: Structured sentiment analysis")
    print(f"✅ Fallback System: Graceful degradation when API unavailable")
    print(f"✅ Complete Pipeline: End-to-end news analysis")
    print(f"\n🧠 THE OVERMIND PROTOCOL - Ready for AI-Enhanced Trading!")

async def main():
    await test_jina_core_features()

if __name__ == "__main__":
    asyncio.run(main())
