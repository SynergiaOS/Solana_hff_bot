#!/usr/bin/env python3
"""THE OVERMIND PROTOCOL - Integration Validation Script
Comprehensive validation of Mission Control and dynamic goal management integration.
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add brain module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'brain', 'src'))

class IntegrationValidator:
    """Comprehensive integration validation for THE OVERMIND PROTOCOL."""
    
    def __init__(self, base_url: str = "http://localhost:8501", api_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.api_url = api_url
        self.session = None
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.results.append({
            'test_name': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        })
    
    async def test_mission_control_health(self) -> bool:
        """Test Mission Control dashboard health."""
        try:
            async with self.session.get(f"{self.base_url}/health", timeout=10) as response:
                if response.status == 200:
                    self.log_result("Mission Control Health", True, "Dashboard is responding")
                    return True
                else:
                    self.log_result("Mission Control Health", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Mission Control Health", False, f"Connection failed: {e}")
            return False
    
    async def test_mission_control_ui(self) -> bool:
        """Test Mission Control UI accessibility."""
        try:
            async with self.session.get(f"{self.base_url}/", timeout=15) as response:
                if response.status == 200:
                    content = await response.text()
                    if "THE OVERMIND PROTOCOL" in content:
                        self.log_result("Mission Control UI", True, "UI is accessible and loading")
                        return True
                    else:
                        self.log_result("Mission Control UI", False, "UI content not found")
                        return False
                else:
                    self.log_result("Mission Control UI", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Mission Control UI", False, f"UI access failed: {e}")
            return False
    
    async def test_goal_management_api(self) -> bool:
        """Test goal management API endpoints."""
        try:
            # Test health endpoint
            async with self.session.get(f"{self.api_url}/api/v1/control/health", timeout=10) as response:
                if response.status == 200:
                    health_data = await response.json()
                    self.log_result("Goal Management API Health", True, "API is responding", health_data)
                    return True
                else:
                    self.log_result("Goal Management API Health", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Goal Management API Health", False, f"API not available: {e}")
            return False
    
    async def test_goal_setting_workflow(self) -> bool:
        """Test complete goal setting workflow."""
        try:
            # Test goal setting
            goal_data = {
                "goal_type": "REACH_BALANCE",
                "target_sol": 2.0,
                "target_usd": 300.0,
                "reason": "Integration test goal",
                "changed_by": "integration_validator"
            }
            
            async with self.session.post(
                f"{self.api_url}/api/v1/control/set-goal",
                json=goal_data,
                timeout=10
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.log_result("Goal Setting", True, "Goal set successfully", result)
                    
                    # Test goal retrieval
                    async with self.session.get(f"{self.api_url}/api/v1/control/current-goal") as get_response:
                        if get_response.status == 200:
                            current_goal = await get_response.json()
                            if current_goal.get('target_sol') == 2.0:
                                self.log_result("Goal Retrieval", True, "Goal retrieved correctly", current_goal)
                                return True
                            else:
                                self.log_result("Goal Retrieval", False, "Goal data mismatch")
                                return False
                        else:
                            self.log_result("Goal Retrieval", False, f"HTTP {get_response.status}")
                            return False
                else:
                    self.log_result("Goal Setting", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Goal Setting Workflow", False, f"Workflow failed: {e}")
            return False
    
    async def test_portfolio_monitoring(self) -> bool:
        """Test portfolio monitoring functionality."""
        try:
            async with self.session.get(f"{self.api_url}/api/v1/portfolio/state", timeout=10) as response:
                if response.status == 200:
                    portfolio_data = await response.json()
                    required_fields = ['total_value_sol', 'total_value_usd', 'goal_progress_percentage']
                    
                    if all(field in portfolio_data for field in required_fields):
                        self.log_result("Portfolio Monitoring", True, "Portfolio data available", portfolio_data)
                        return True
                    else:
                        self.log_result("Portfolio Monitoring", False, "Missing required fields")
                        return False
                else:
                    self.log_result("Portfolio Monitoring", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Portfolio Monitoring", False, f"Portfolio API failed: {e}")
            return False
    
    async def test_strategy_mapping(self) -> bool:
        """Test strategy mapping functionality."""
        try:
            async with self.session.get(f"{self.api_url}/api/v1/strategy/active-profile", timeout=10) as response:
                if response.status == 200:
                    strategy_data = await response.json()
                    required_fields = ['current_profile', 'recommended_profile', 'confidence']
                    
                    if all(field in strategy_data for field in required_fields):
                        self.log_result("Strategy Mapping", True, "Strategy data available", strategy_data)
                        return True
                    else:
                        self.log_result("Strategy Mapping", False, "Missing required fields")
                        return False
                else:
                    self.log_result("Strategy Mapping", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Strategy Mapping", False, f"Strategy API failed: {e}")
            return False
    
    async def test_performance_requirements(self) -> bool:
        """Test performance requirements (sub-50ms latency)."""
        try:
            latencies = []
            
            for i in range(10):
                start_time = time.time()
                async with self.session.get(f"{self.api_url}/api/v1/control/health", timeout=5) as response:
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000  # Convert to milliseconds
                    latencies.append(latency)
                    
                    if response.status != 200:
                        self.log_result("Performance Test", False, f"HTTP {response.status} on iteration {i+1}")
                        return False
                
                await asyncio.sleep(0.1)  # Small delay between requests
            
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            
            if avg_latency < 50 and max_latency < 100:
                self.log_result("Performance Requirements", True, 
                              f"Avg: {avg_latency:.2f}ms, Max: {max_latency:.2f}ms",
                              {'avg_latency': avg_latency, 'max_latency': max_latency, 'all_latencies': latencies})
                return True
            else:
                self.log_result("Performance Requirements", False,
                              f"Latency too high - Avg: {avg_latency:.2f}ms, Max: {max_latency:.2f}ms")
                return False
        except Exception as e:
            self.log_result("Performance Requirements", False, f"Performance test failed: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling and resilience."""
        try:
            # Test invalid goal data
            invalid_goal = {
                "goal_type": "INVALID_TYPE",
                "target_sol": -1.0,
                "reason": "Invalid goal test"
            }
            
            async with self.session.post(
                f"{self.api_url}/api/v1/control/set-goal",
                json=invalid_goal,
                timeout=10
            ) as response:
                if response.status in [400, 422]:  # Expected error codes
                    self.log_result("Error Handling", True, "Invalid goal properly rejected")
                    return True
                else:
                    self.log_result("Error Handling", False, f"Unexpected response: HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Error Handling", False, f"Error handling test failed: {e}")
            return False
    
    async def test_data_persistence(self) -> bool:
        """Test data persistence and consistency."""
        try:
            # Set a test goal
            test_goal = {
                "goal_type": "MAXIMIZE_PROFIT",
                "target_sol": 3.5,
                "reason": "Data persistence test"
            }
            
            async with self.session.post(
                f"{self.api_url}/api/v1/control/set-goal",
                json=test_goal,
                timeout=10
            ) as response:
                if response.status != 200:
                    self.log_result("Data Persistence", False, "Failed to set test goal")
                    return False
            
            # Wait a moment
            await asyncio.sleep(2)
            
            # Retrieve goal and verify persistence
            async with self.session.get(f"{self.api_url}/api/v1/control/current-goal") as response:
                if response.status == 200:
                    goal_data = await response.json()
                    if goal_data.get('target_sol') == 3.5 and goal_data.get('goal_type') == 'MAXIMIZE_PROFIT':
                        self.log_result("Data Persistence", True, "Goal data persisted correctly")
                        return True
                    else:
                        self.log_result("Data Persistence", False, "Goal data not persisted correctly")
                        return False
                else:
                    self.log_result("Data Persistence", False, f"HTTP {response.status}")
                    return False
        except Exception as e:
            self.log_result("Data Persistence", False, f"Persistence test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests."""
        print("🧪 Starting THE OVERMIND PROTOCOL Integration Validation")
        print(f"Mission Control URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print("-" * 60)
        
        # Define test suite
        tests = [
            ("Mission Control Health Check", self.test_mission_control_health),
            ("Mission Control UI Access", self.test_mission_control_ui),
            ("Goal Management API", self.test_goal_management_api),
            ("Goal Setting Workflow", self.test_goal_setting_workflow),
            ("Portfolio Monitoring", self.test_portfolio_monitoring),
            ("Strategy Mapping", self.test_strategy_mapping),
            ("Performance Requirements", self.test_performance_requirements),
            ("Error Handling", self.test_error_handling),
            ("Data Persistence", self.test_data_persistence),
        ]
        
        # Run tests
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                result = await test_func()
                if result:
                    passed += 1
            except Exception as e:
                self.log_result(test_name, False, f"Test execution failed: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🎯 Integration Validation Summary")
        print(f"Passed: {passed}/{total} tests")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All tests passed! Integration is successful.")
            status = "SUCCESS"
        elif passed >= total * 0.8:
            print("⚠️ Most tests passed. Minor issues detected.")
            status = "WARNING"
        else:
            print("❌ Multiple test failures. Integration needs attention.")
            status = "FAILURE"
        
        return {
            'status': status,
            'passed': passed,
            'total': total,
            'success_rate': (passed/total)*100,
            'results': self.results,
            'timestamp': datetime.utcnow().isoformat()
        }

async def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='THE OVERMIND PROTOCOL Integration Validator')
    parser.add_argument('--mission-control-url', default='http://localhost:8501',
                       help='Mission Control dashboard URL')
    parser.add_argument('--api-url', default='http://localhost:8080',
                       help='API base URL')
    parser.add_argument('--output', help='Output file for results (JSON)')
    
    args = parser.parse_args()
    
    async with IntegrationValidator(args.mission_control_url, args.api_url) as validator:
        results = await validator.run_all_tests()
        
        # Save results if output file specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to: {args.output}")
        
        # Exit with appropriate code
        if results['status'] == 'SUCCESS':
            sys.exit(0)
        elif results['status'] == 'WARNING':
            sys.exit(1)
        else:
            sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
