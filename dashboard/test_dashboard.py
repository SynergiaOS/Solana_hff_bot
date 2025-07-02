#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Dashboard Integration Test
Test script to verify dashboard functionality and data connectivity
"""

import asyncio
import json
import time
import redis
import logging
import httpx
from typing import Dict, Any
import sys
import os

# Add dashboard directory to path
sys.path.append(os.path.dirname(__file__))

from comprehensive_overmind_dashboard import OVERMINDDataConnector
from dashboard_config import DASHBOARD_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardTester:
    """Test suite for OVERMIND dashboard"""
    
    def __init__(self):
        self.data_connector = OVERMINDDataConnector()
        self.test_results = {}
    
    async def test_redis_connection(self) -> bool:
        """Test Redis/DragonflyDB connection"""
        try:
            logger.info("🔍 Testing Redis connection...")
            
            # Test basic connection
            result = self.data_connector.redis_client.ping()
            
            if result:
                logger.info("✅ Redis connection successful")
                return True
            else:
                logger.error("❌ Redis ping failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Redis connection error: {e}")
            return False
    
    async def test_api_endpoints(self) -> Dict[str, bool]:
        """Test API endpoint connectivity"""
        results = {}
        
        endpoints = {
            "Brain API": DASHBOARD_CONFIG.brain_api_url,
            "Executor API": DASHBOARD_CONFIG.executor_api_url
        }
        
        for name, url in endpoints.items():
            try:
                logger.info(f"🔍 Testing {name} at {url}...")
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{url}/health", timeout=5.0)
                    
                    if response.status_code == 200:
                        logger.info(f"✅ {name} is accessible")
                        results[name] = True
                    else:
                        logger.warning(f"⚠️ {name} returned status {response.status_code}")
                        results[name] = False
                        
            except Exception as e:
                logger.error(f"❌ {name} connection error: {e}")
                results[name] = False
        
        return results
    
    async def test_data_connectors(self) -> Dict[str, bool]:
        """Test data connector methods"""
        results = {}
        
        test_methods = [
            ("System Health", self.data_connector.get_system_health),
            ("Hedging Status", self.data_connector.get_hedging_status),
            ("MEV Protection", self.data_connector.get_mev_protection_metrics),
            ("Strategy Performance", self.data_connector.get_strategy_performance),
            ("Portfolio Metrics", self.data_connector.get_portfolio_metrics)
        ]
        
        for name, method in test_methods:
            try:
                logger.info(f"🔍 Testing {name} data connector...")
                
                data = await method()
                
                if data and not data.get("error"):
                    logger.info(f"✅ {name} data connector working")
                    results[name] = True
                else:
                    logger.warning(f"⚠️ {name} data connector returned empty/error data")
                    results[name] = False
                    
            except Exception as e:
                logger.error(f"❌ {name} data connector error: {e}")
                results[name] = False
        
        return results
    
    async def test_sample_data_generation(self) -> bool:
        """Test sample data generation for dashboard"""
        try:
            logger.info("🔍 Testing sample data generation...")
            
            # Generate sample data for Redis
            sample_data = {
                "overmind:portfolio_value": "1247.83",
                "overmind:daily_pnl": json.dumps([
                    {"timestamp": time.time(), "pnl": 47.23},
                    {"timestamp": time.time() - 3600, "pnl": 23.45}
                ]),
                "overmind:active_positions": json.dumps(["SOL", "BTC", "ETH"]),
                "overmind:hedging_status": json.dumps({
                    "active_hedges": 3,
                    "hedge_coverage": 0.67,
                    "last_update": time.time()
                }),
                "overmind:mev_risk_scores": json.dumps([
                    {"timestamp": time.time(), "risk_score": 0.23},
                    {"timestamp": time.time() - 300, "risk_score": 0.31}
                ])
            }
            
            # Store sample data
            for key, value in sample_data.items():
                self.data_connector.redis_client.setex(key, 3600, value)
            
            logger.info("✅ Sample data generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Sample data generation error: {e}")
            return False
    
    async def test_dashboard_components(self) -> Dict[str, bool]:
        """Test dashboard component functionality"""
        results = {}
        
        try:
            logger.info("🔍 Testing dashboard components...")
            
            # Test data fetching
            system_health = await self.data_connector.get_system_health()
            results["System Health Fetch"] = bool(system_health)
            
            hedging_data = await self.data_connector.get_hedging_status()
            results["Hedging Data Fetch"] = bool(hedging_data)
            
            portfolio_data = await self.data_connector.get_portfolio_metrics()
            results["Portfolio Data Fetch"] = bool(portfolio_data)
            
            logger.info("✅ Dashboard components tested")
            
        except Exception as e:
            logger.error(f"❌ Dashboard component test error: {e}")
            results["Dashboard Components"] = False
        
        return results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive dashboard test suite"""
        logger.info("🧠 Starting THE OVERMIND PROTOCOL Dashboard Test Suite")
        logger.info("=" * 60)
        
        test_results = {
            "timestamp": time.time(),
            "tests": {}
        }
        
        # Test Redis connection
        test_results["tests"]["redis_connection"] = await self.test_redis_connection()
        
        # Test API endpoints
        test_results["tests"]["api_endpoints"] = await self.test_api_endpoints()
        
        # Generate sample data
        test_results["tests"]["sample_data"] = await self.test_sample_data_generation()
        
        # Test data connectors
        test_results["tests"]["data_connectors"] = await self.test_data_connectors()
        
        # Test dashboard components
        test_results["tests"]["dashboard_components"] = await self.test_dashboard_components()
        
        return test_results
    
    def print_test_summary(self, results: Dict[str, Any]):
        """Print test results summary"""
        logger.info("\n" + "=" * 60)
        logger.info("🧠 THE OVERMIND PROTOCOL Dashboard Test Summary")
        logger.info("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, test_data in results["tests"].items():
            logger.info(f"\n📊 {category.replace('_', ' ').title()}:")
            
            if isinstance(test_data, dict):
                for test_name, result in test_data.items():
                    status = "✅ PASS" if result else "❌ FAIL"
                    logger.info(f"  {test_name}: {status}")
                    total_tests += 1
                    if result:
                        passed_tests += 1
            else:
                status = "✅ PASS" if test_data else "❌ FAIL"
                logger.info(f"  {category}: {status}")
                total_tests += 1
                if test_data:
                    passed_tests += 1
        
        logger.info(f"\n📈 Overall Results:")
        logger.info(f"  Total Tests: {total_tests}")
        logger.info(f"  Passed: {passed_tests}")
        logger.info(f"  Failed: {total_tests - passed_tests}")
        logger.info(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            logger.info("\n🎉 All tests passed! Dashboard is ready to use.")
        else:
            logger.info(f"\n⚠️ {total_tests - passed_tests} test(s) failed. Check configuration and system components.")
        
        logger.info("\n🚀 To start the dashboard:")
        logger.info("  python start_dashboard.py")
        logger.info("  or")
        logger.info("  ./launch.sh")

async def main():
    """Main test execution"""
    tester = DashboardTester()
    
    try:
        results = await tester.run_comprehensive_test()
        tester.print_test_summary(results)
        
        # Save results to file
        with open("dashboard_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n💾 Test results saved to: dashboard_test_results.json")
        
    except Exception as e:
        logger.error(f"❌ Test suite error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
