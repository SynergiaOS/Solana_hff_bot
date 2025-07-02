#!/usr/bin/env python3
"""
Test script for ResearchAgent Microservice
Tests the complete Jina-Serve microservice architecture
"""

import asyncio
import logging
import time
import subprocess
import signal
import os
from research_agent_client import ResearchAgentClient, OVERMINDBrainManagerIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchAgentTester:
    """Comprehensive tester for ResearchAgent microservice"""
    
    def __init__(self):
        self.microservice_process = None
        self.base_url = "http://localhost:8080"
        
    async def start_microservice(self):
        """Start the ResearchAgent microservice"""
        try:
            logger.info("🚀 Starting ResearchAgent microservice...")
            
            # Start the microservice in background
            self.microservice_process = subprocess.Popen(
                ["python", "research_agent_microservice.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for startup
            await asyncio.sleep(10)
            
            # Check if it's running
            async with ResearchAgentClient(self.base_url) as client:
                for attempt in range(10):
                    if await client.health_check():
                        logger.info("✅ ResearchAgent microservice started successfully")
                        return True
                    await asyncio.sleep(2)
            
            logger.error("❌ Failed to start ResearchAgent microservice")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error starting microservice: {e}")
            return False
    
    def stop_microservice(self):
        """Stop the ResearchAgent microservice"""
        if self.microservice_process:
            try:
                # Kill the process group
                os.killpg(os.getpgid(self.microservice_process.pid), signal.SIGTERM)
                self.microservice_process.wait(timeout=10)
                logger.info("✅ ResearchAgent microservice stopped")
            except:
                # Force kill if needed
                os.killpg(os.getpgid(self.microservice_process.pid), signal.SIGKILL)
                logger.info("🔥 ResearchAgent microservice force killed")
    
    async def test_basic_functionality(self):
        """Test basic ResearchAgent functionality"""
        print("\n🧪 Test 1: Basic Functionality")
        
        async with ResearchAgentClient(self.base_url) as client:
            # Test health check
            is_healthy = await client.health_check()
            print(f"   Health Check: {'✅ Pass' if is_healthy else '❌ Fail'}")
            
            if not is_healthy:
                return False
            
            # Test comprehensive research
            result = await client.comprehensive_research(
                "Analyze Solana ecosystem growth and adoption trends", 
                "SOL"
            )
            
            print(f"   Research Query: Solana ecosystem analysis")
            print(f"   Sentiment Score: {result.get('sentiment_score', 0):.3f}")
            print(f"   Confidence: {result.get('confidence', 0):.3f}")
            print(f"   Processing Time: {result.get('processing_time', 0):.2f}s")
            print(f"   Method: {result.get('research_method', 'unknown')}")
            print(f"   Insights Found: {len(result.get('key_insights', []))}")
            
            return result.get('confidence', 0) > 0
    
    async def test_different_research_types(self):
        """Test different types of research"""
        print("\n🧪 Test 2: Different Research Types")
        
        async with ResearchAgentClient(self.base_url) as client:
            research_types = [
                ("comprehensive", "Overall Solana market analysis"),
                ("sentiment", "Current market sentiment for Solana"),
                ("news", "Latest Solana news and developments"),
                ("technical", "Solana technical analysis and price prediction")
            ]
            
            results = {}
            for research_type, query in research_types:
                try:
                    result = await client.research(query, "SOL", research_type)
                    results[research_type] = result
                    
                    print(f"   {research_type.title()}: "
                          f"Sentiment {result.get('sentiment_score', 0):.3f}, "
                          f"Confidence {result.get('confidence', 0):.3f}")
                    
                except Exception as e:
                    print(f"   {research_type.title()}: ❌ Error - {e}")
                    results[research_type] = None
            
            # Check if at least 2 research types worked
            successful = sum(1 for r in results.values() if r and r.get('confidence', 0) > 0)
            print(f"   Successful Research Types: {successful}/4")
            
            return successful >= 2
    
    async def test_overmind_integration(self):
        """Test OVERMIND Brain integration"""
        print("\n🧪 Test 3: OVERMIND Integration")
        
        try:
            integration = OVERMINDBrainManagerIntegration(self.base_url)
            
            # Test market research
            market_research = await integration.get_market_research("SOL")
            print(f"   Market Research Components: {list(market_research.keys())}")
            
            # Test trading signals
            trading_signals = await integration.get_trading_signals("SOL")
            print(f"   Trading Signals: {trading_signals}")
            
            # Test market sentiment
            market_sentiment = await integration.get_market_sentiment("SOL")
            print(f"   Market Sentiment: {market_sentiment:.3f}")
            
            # Check if integration worked
            has_data = (
                len(market_research) > 2 and
                isinstance(trading_signals, list) and
                0 <= market_sentiment <= 1
            )
            
            print(f"   Integration Status: {'✅ Working' if has_data else '❌ Failed'}")
            return has_data
            
        except Exception as e:
            print(f"   Integration Status: ❌ Error - {e}")
            return False
    
    async def test_performance_and_scaling(self):
        """Test performance and concurrent requests"""
        print("\n🧪 Test 4: Performance & Scaling")
        
        async with ResearchAgentClient(self.base_url) as client:
            # Test concurrent requests
            start_time = time.time()
            
            tasks = [
                client.research(f"Analysis query {i}", "SOL", "sentiment")
                for i in range(5)  # 5 concurrent requests
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            successful_requests = sum(
                1 for r in results 
                if not isinstance(r, Exception) and r.get('confidence', 0) > 0
            )
            
            print(f"   Concurrent Requests: 5")
            print(f"   Successful Requests: {successful_requests}")
            print(f"   Total Time: {total_time:.2f}s")
            print(f"   Average Time per Request: {total_time/5:.2f}s")
            print(f"   Requests per Second: {5/total_time:.2f}")
            
            return successful_requests >= 3 and total_time < 30
    
    async def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        print("\n🧪 Test 5: Error Handling")
        
        async with ResearchAgentClient(self.base_url) as client:
            # Test with invalid research type
            result1 = await client.research("Test query", "SOL", "invalid_type")
            
            # Test with empty query
            result2 = await client.research("", "SOL", "comprehensive")
            
            # Test with invalid symbol
            result3 = await client.research("Test query", "INVALID", "sentiment")
            
            # Check if all requests returned valid fallback results
            all_valid = all(
                isinstance(r, dict) and 'sentiment_score' in r
                for r in [result1, result2, result3]
            )
            
            print(f"   Invalid Type Handling: {'✅ Pass' if result1.get('research_method') else '❌ Fail'}")
            print(f"   Empty Query Handling: {'✅ Pass' if result2.get('research_method') else '❌ Fail'}")
            print(f"   Invalid Symbol Handling: {'✅ Pass' if result3.get('research_method') else '❌ Fail'}")
            print(f"   Overall Error Handling: {'✅ Pass' if all_valid else '❌ Fail'}")
            
            return all_valid

async def main():
    """Main test function"""
    print("🧠 THE OVERMIND PROTOCOL - ResearchAgent Microservice Test")
    print("=" * 70)
    
    tester = ResearchAgentTester()
    
    try:
        # Start microservice
        if not await tester.start_microservice():
            print("❌ Failed to start microservice - aborting tests")
            return
        
        # Run all tests
        tests = [
            tester.test_basic_functionality(),
            tester.test_different_research_types(),
            tester.test_overmind_integration(),
            tester.test_performance_and_scaling(),
            tester.test_error_handling()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Calculate results
        passed_tests = sum(1 for r in results if r is True)
        total_tests = len(tests)
        
        print(f"\n📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("   🎉 ALL TESTS PASSED - ResearchAgent microservice is ready!")
        elif passed_tests >= total_tests * 0.8:
            print("   ✅ MOSTLY WORKING - Minor issues detected")
        else:
            print("   ⚠️ ISSUES DETECTED - Review failed tests")
        
        print(f"\n🎯 ResearchAgent Microservice Test Complete!")
        
    finally:
        # Always stop the microservice
        tester.stop_microservice()

if __name__ == "__main__":
    asyncio.run(main())
