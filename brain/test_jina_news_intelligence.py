#!/usr/bin/env python3
"""
Test script for Jina AI enhanced News Intelligence
Tests the new implementation with real Solana news
"""

import asyncio
import logging
from news_intelligence import JinaNewsIntelligence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_jina_news_intelligence():
    """Test the Jina AI enhanced news intelligence system"""
    
    print("🧠 THE OVERMIND PROTOCOL - Jina AI News Intelligence Test")
    print("=" * 60)
    
    # Initialize the enhanced news intelligence
    news_intel = JinaNewsIntelligence()
    
    # Test 1: Fetch and analyze news for SOL
    print("\n📰 Test 1: Analyzing Solana (SOL) news with Jina AI...")
    try:
        sol_news = await news_intel.process_news_for_symbol_with_jina('SOL')
        
        print(f"✅ SOL News Analysis Results:")
        print(f"   📊 News Count: {sol_news['news_count']}")
        print(f"   💭 Avg Sentiment: {sol_news['avg_sentiment']:.3f}")
        print(f"   🎯 Confidence: {sol_news['confidence']:.3f}")
        print(f"   🚨 Signals: {sol_news['signals']}")
        print(f"   💡 Insights: {sol_news.get('insights', [])[:3]}")  # Top 3 insights
        
        if sol_news.get('news_items'):
            print(f"\n📄 Sample News Item:")
            sample = sol_news['news_items'][0]
            print(f"   Title: {sample['title'][:80]}...")
            print(f"   Sentiment: {sample['sentiment_score']:.3f}")
            print(f"   Confidence: {sample['confidence']:.3f}")
            print(f"   Key Insights: {sample['key_insights'][:2]}")
        else:
            print(f"   ℹ️ No news items found (likely due to rate limiting)")

    except Exception as e:
        print(f"❌ Error in SOL news analysis: {e}")
    
    # Test 2: Test Jina Reader API directly
    print("\n📖 Test 2: Testing Jina Reader API...")
    try:
        test_url = "https://solana.com/news"  # Use official Solana news page
        clean_content = await news_intel.fetch_clean_content(test_url)
        
        if clean_content:
            print(f"✅ Successfully fetched clean content ({len(clean_content)} chars)")
            print(f"   Preview: {clean_content[:200]}...")
        else:
            print("⚠️ No content fetched from test URL")
            
    except Exception as e:
        print(f"❌ Error testing Jina Reader API: {e}")
    
    # Test 3: Test DeepSearch analysis
    print("\n🔍 Test 3: Testing Jina DeepSearch...")
    try:
        test_query = "Analyze Solana ecosystem developments and price implications"
        test_content = "Solana network has seen increased adoption with new DeFi protocols launching. Transaction fees remain low while throughput is high."
        
        analysis = await news_intel.deep_search_analysis(test_query, test_content)
        
        if analysis:
            print(f"✅ DeepSearch Analysis Results:")
            print(f"   Sentiment Score: {analysis.get('sentiment_score', 'N/A')}")
            print(f"   Confidence: {analysis.get('confidence', 'N/A')}")
            print(f"   Key Insights: {analysis.get('key_insights', [])}")
            print(f"   Trading Signals: {analysis.get('trading_signals', [])}")
        else:
            print("⚠️ No analysis results from DeepSearch")
            
    except Exception as e:
        print(f"❌ Error testing Jina DeepSearch: {e}")
    
    # Test 4: Compare with fallback analysis
    print("\n🔄 Test 4: Testing fallback sentiment analysis...")
    try:
        test_text = "Solana price surges as new partnerships drive bullish sentiment and adoption increases"
        
        fallback_result = await news_intel._fallback_sentiment_analysis(test_text, 'SOL')
        
        print(f"✅ Fallback Analysis Results:")
        print(f"   Sentiment Score: {fallback_result['score']:.3f}")
        print(f"   Confidence: {fallback_result['confidence']:.3f}")
        print(f"   Signals: {fallback_result['signals']}")
        print(f"   Reasoning: {fallback_result['reasoning']}")
        
    except Exception as e:
        print(f"❌ Error testing fallback analysis: {e}")
    
    # Test 5: Monitor multiple symbols
    print("\n📊 Test 5: Monitoring multiple symbols...")
    try:
        symbols = ['SOL', 'RAY']  # Limited to 2 symbols for testing
        
        print(f"🔄 Analyzing news for symbols: {symbols}")
        intelligence_data = await news_intel.monitor_all_symbols(symbols)
        
        print(f"\n📈 Multi-Symbol Analysis Results:")
        for symbol, data in intelligence_data.items():
            sentiment = data['avg_sentiment']
            confidence = data['confidence']
            news_count = data['news_count']
            
            # Sentiment indicator
            if sentiment > 0.6 and confidence > 0.3:
                indicator = "🟢 BULLISH"
            elif sentiment < 0.4 and confidence > 0.3:
                indicator = "🔴 BEARISH"
            else:
                indicator = "⚪ NEUTRAL"
            
            print(f"   {indicator} {symbol}: Sentiment {sentiment:.3f} "
                  f"(Conf: {confidence:.3f}) | News: {news_count}")
            
            if data.get('insights'):
                print(f"      💡 Top Insight: {data['insights'][0]}")
        
    except Exception as e:
        print(f"❌ Error in multi-symbol monitoring: {e}")
    
    print(f"\n🎯 Jina AI News Intelligence Test Complete!")
    print("=" * 60)

async def main():
    """Main test function"""
    await test_jina_news_intelligence()

if __name__ == "__main__":
    asyncio.run(main())
