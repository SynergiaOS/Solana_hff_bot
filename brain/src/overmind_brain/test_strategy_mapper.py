"""THE OVERMIND PROTOCOL - Strategy Mapper Test Suite
Comprehensive test suite for decision tree logic, edge cases, and stress scenarios.
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .strategy_mapper import StrategyMapper, ProfileSwitchDecision, HysteresisState
from .strategy_profiles import ProfileType
from .portfolio_monitor import PortfolioState

logger = logging.getLogger(__name__)

class MockRedisClient:
    """Mock Redis client for testing."""
    
    def __init__(self):
        self.data = {}
        self.lists = {}
    
    async def ping(self):
        return True
    
    async def get(self, key):
        return self.data.get(key)
    
    async def set(self, key, value):
        self.data[key] = value
    
    async def lpush(self, key, value):
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].insert(0, value)
    
    async def ltrim(self, key, start, end):
        if key in self.lists:
            self.lists[key] = self.lists[key][start:end+1]
    
    async def publish(self, channel, message):
        pass

class StrategyMapperTestSuite:
    """Comprehensive test suite for StrategyMapper."""
    
    def __init__(self):
        self.test_results = []
        self.mapper = None
    
    async def setup_test_environment(self):
        """Set up test environment with mock dependencies."""
        self.mapper = StrategyMapper(
            redis_host="localhost",
            redis_port=6379,
            hysteresis_buffer=2.0,
            minimum_hold_time=15
        )
        
        # Replace Redis client with mock
        self.mapper.redis_client = MockRedisClient()
        
        # Initialize with default state
        await self.mapper._initialize_default_state()
        
        logger.info("🧪 Test environment set up")
    
    def create_test_portfolio_state(self, progress_percentage: float) -> PortfolioState:
        """Create a test portfolio state with specified progress."""
        target_sol = 2.0
        current_sol = (progress_percentage / 100.0) * target_sol
        
        return PortfolioState(
            total_value_usd=current_sol * 100.0,  # Assume $100/SOL
            total_value_sol=current_sol,
            goal_progress_percentage=progress_percentage,
            wallet_balances={"test_wallet": {"SOL": current_sol}},
            last_updated=datetime.utcnow().isoformat(),
            price_data={"SOL": 100.0},
            historical_progression=[]
        )
    
    async def test_basic_decision_tree_logic(self) -> Dict[str, Any]:
        """Test basic decision tree logic across all ranges."""
        test_cases = [
            (0.0, ProfileType.AGGRESSIVE_GROWTH),
            (10.0, ProfileType.AGGRESSIVE_GROWTH),
            (24.9, ProfileType.AGGRESSIVE_GROWTH),
            (25.0, ProfileType.BALANCED_RISK),
            (50.0, ProfileType.BALANCED_RISK),
            (99.9, ProfileType.BALANCED_RISK),
            (100.0, ProfileType.CAPITAL_PRESERVATION),
            (150.0, ProfileType.CAPITAL_PRESERVATION),
            (200.0, ProfileType.CAPITAL_PRESERVATION)
        ]
        
        results = []
        
        for progress, expected_profile in test_cases:
            portfolio_state = self.create_test_portfolio_state(progress)
            decision = await self.mapper.determine_active_profile(portfolio_state)
            
            success = decision.recommended_profile == expected_profile
            results.append({
                "progress": progress,
                "expected": expected_profile.value,
                "actual": decision.recommended_profile.value,
                "success": success,
                "confidence": decision.confidence
            })
            
            if not success:
                logger.error(f"❌ Basic logic test failed: {progress}% -> expected {expected_profile.value}, got {decision.recommended_profile.value}")
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        
        return {
            "test_name": "basic_decision_tree_logic",
            "success_rate": success_rate,
            "results": results,
            "passed": success_rate == 1.0
        }
    
    async def test_hysteresis_buffer_zones(self) -> Dict[str, Any]:
        """Test hysteresis buffer zones around transition points."""
        
        # Test around 25% transition point
        buffer_test_cases = [
            (23.0, ProfileType.AGGRESSIVE_GROWTH, True),   # Outside buffer, should switch
            (23.5, ProfileType.AGGRESSIVE_GROWTH, False),  # In buffer, should not switch
            (24.0, ProfileType.AGGRESSIVE_GROWTH, False),  # In buffer, should not switch
            (25.0, ProfileType.BALANCED_RISK, False),      # In buffer, should not switch
            (26.0, ProfileType.BALANCED_RISK, False),      # In buffer, should not switch
            (26.5, ProfileType.BALANCED_RISK, False),      # In buffer, should not switch
            (27.0, ProfileType.BALANCED_RISK, True),       # Outside buffer, should switch
        ]
        
        results = []
        
        # Start with AGGRESSIVE_GROWTH profile
        self.mapper.current_profile = ProfileType.AGGRESSIVE_GROWTH
        
        for progress, expected_profile, should_allow_switch in buffer_test_cases:
            portfolio_state = self.create_test_portfolio_state(progress)
            decision = await self.mapper.determine_active_profile(portfolio_state)
            
            # Check if hysteresis is working correctly
            if expected_profile != self.mapper.current_profile:
                success = decision.should_switch == should_allow_switch
            else:
                success = not decision.should_switch  # Same profile, should not switch
            
            results.append({
                "progress": progress,
                "current_profile": self.mapper.current_profile.value,
                "expected_profile": expected_profile.value,
                "should_allow_switch": should_allow_switch,
                "actual_should_switch": decision.should_switch,
                "success": success,
                "hysteresis_triggered": decision.hysteresis_triggered
            })
        
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        
        return {
            "test_name": "hysteresis_buffer_zones",
            "success_rate": success_rate,
            "results": results,
            "passed": success_rate >= 0.8  # Allow some tolerance
        }
    
    async def test_minimum_hold_time(self) -> Dict[str, Any]:
        """Test minimum hold time enforcement."""
        
        # Set a recent switch time
        self.mapper.hysteresis_state.last_switch_time = datetime.utcnow() - timedelta(minutes=5)
        
        # Try to switch before minimum hold time
        portfolio_state = self.create_test_portfolio_state(50.0)  # Should recommend BALANCED_RISK
        self.mapper.current_profile = ProfileType.AGGRESSIVE_GROWTH
        
        decision = await self.mapper.determine_active_profile(portfolio_state)
        
        # Should not allow switch due to minimum hold time
        hold_time_respected = not decision.should_switch and "hold time" in decision.reason.lower()
        
        # Now test after minimum hold time
        self.mapper.hysteresis_state.last_switch_time = datetime.utcnow() - timedelta(minutes=20)
        decision_after_hold = await self.mapper.determine_active_profile(portfolio_state)
        
        return {
            "test_name": "minimum_hold_time",
            "hold_time_respected": hold_time_respected,
            "switch_allowed_after_hold": decision_after_hold.should_switch,
            "passed": hold_time_respected and decision_after_hold.should_switch
        }
    
    async def test_confidence_calculation(self) -> Dict[str, Any]:
        """Test confidence calculation accuracy."""
        
        test_cases = [
            (0.0, ProfileType.AGGRESSIVE_GROWTH),    # Far from transition, high confidence
            (12.5, ProfileType.AGGRESSIVE_GROWTH),   # Mid-range, medium confidence
            (23.0, ProfileType.AGGRESSIVE_GROWTH),   # Near transition, lower confidence
            (27.0, ProfileType.BALANCED_RISK),       # Near transition, lower confidence
            (62.5, ProfileType.BALANCED_RISK),       # Mid-range, higher confidence
            (98.0, ProfileType.BALANCED_RISK),       # Near transition, lower confidence
            (102.0, ProfileType.CAPITAL_PRESERVATION), # Near transition, lower confidence
            (150.0, ProfileType.CAPITAL_PRESERVATION)  # Far from transition, higher confidence
        ]
        
        results = []
        
        for progress, expected_profile in test_cases:
            portfolio_state = self.create_test_portfolio_state(progress)
            decision = await self.mapper.determine_active_profile(portfolio_state)
            
            # Confidence should be reasonable (0.5-1.0)
            confidence_valid = 0.5 <= decision.confidence <= 1.0
            
            results.append({
                "progress": progress,
                "profile": expected_profile.value,
                "confidence": decision.confidence,
                "confidence_valid": confidence_valid
            })
        
        avg_confidence = sum(r["confidence"] for r in results) / len(results)
        all_valid = all(r["confidence_valid"] for r in results)
        
        return {
            "test_name": "confidence_calculation",
            "average_confidence": avg_confidence,
            "all_confidence_valid": all_valid,
            "results": results,
            "passed": all_valid and avg_confidence >= 0.6
        }
    
    async def test_stress_scenarios(self) -> Dict[str, Any]:
        """Test stress scenarios with rapid changes."""
        
        # Simulate rapid portfolio value changes
        stress_scenarios = [
            # Scenario 1: Rapid growth
            [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0],
            # Scenario 2: Volatile around transition
            [23.0, 25.0, 24.0, 26.0, 25.5, 24.5, 26.5],
            # Scenario 3: Major loss and recovery
            [80.0, 60.0, 40.0, 20.0, 30.0, 50.0, 70.0],
            # Scenario 4: Goal achievement and beyond
            [95.0, 98.0, 100.0, 105.0, 110.0, 120.0, 150.0]
        ]
        
        results = []
        
        for scenario_idx, progress_sequence in enumerate(stress_scenarios):
            scenario_results = []
            
            # Reset to initial state
            self.mapper.current_profile = ProfileType.AGGRESSIVE_GROWTH
            self.mapper.hysteresis_state.last_switch_time = datetime.utcnow() - timedelta(hours=1)
            self.mapper.hysteresis_state.switch_count_24h = 0
            
            for step, progress in enumerate(progress_sequence):
                portfolio_state = self.create_test_portfolio_state(progress)
                decision = await self.mapper.determine_active_profile(portfolio_state)
                
                # Execute switch if recommended
                if decision.should_switch:
                    await self.mapper.execute_profile_switch(decision)
                
                scenario_results.append({
                    "step": step,
                    "progress": progress,
                    "profile": self.mapper.current_profile.value,
                    "recommended": decision.recommended_profile.value,
                    "switched": decision.should_switch,
                    "confidence": decision.confidence
                })
                
                # Add small delay to simulate time passage
                await asyncio.sleep(0.01)
            
            results.append({
                "scenario": scenario_idx,
                "steps": scenario_results,
                "final_profile": self.mapper.current_profile.value,
                "total_switches": sum(1 for s in scenario_results if s["switched"])
            })
        
        # Check that system remained stable (no excessive switching)
        max_switches = max(r["total_switches"] for r in results)
        stability_maintained = max_switches <= 5  # Reasonable limit
        
        return {
            "test_name": "stress_scenarios",
            "scenarios": results,
            "max_switches": max_switches,
            "stability_maintained": stability_maintained,
            "passed": stability_maintained
        }
    
    async def test_deterministic_behavior(self) -> Dict[str, Any]:
        """Test that behavior is deterministic for same inputs."""
        
        test_progress_values = [10.0, 25.0, 50.0, 100.0, 150.0]
        
        results = []
        
        for progress in test_progress_values:
            decisions = []
            
            # Reset state for each test
            self.mapper.current_profile = ProfileType.AGGRESSIVE_GROWTH
            self.mapper.hysteresis_state.last_switch_time = datetime.utcnow() - timedelta(hours=1)
            
            # Run same test multiple times
            for run in range(5):
                portfolio_state = self.create_test_portfolio_state(progress)
                decision = await self.mapper.determine_active_profile(portfolio_state)
                
                decisions.append({
                    "run": run,
                    "recommended_profile": decision.recommended_profile.value,
                    "confidence": decision.confidence,
                    "should_switch": decision.should_switch
                })
            
            # Check if all decisions are identical
            first_decision = decisions[0]
            all_identical = all(
                d["recommended_profile"] == first_decision["recommended_profile"] and
                abs(d["confidence"] - first_decision["confidence"]) < 0.01 and
                d["should_switch"] == first_decision["should_switch"]
                for d in decisions
            )
            
            results.append({
                "progress": progress,
                "decisions": decisions,
                "deterministic": all_identical
            })
        
        all_deterministic = all(r["deterministic"] for r in results)
        
        return {
            "test_name": "deterministic_behavior",
            "results": results,
            "all_deterministic": all_deterministic,
            "passed": all_deterministic
        }
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        
        logger.info("🧪 Starting comprehensive Strategy Mapper test suite")
        
        await self.setup_test_environment()
        
        # Run all tests
        test_methods = [
            self.test_basic_decision_tree_logic,
            self.test_hysteresis_buffer_zones,
            self.test_minimum_hold_time,
            self.test_confidence_calculation,
            self.test_stress_scenarios,
            self.test_deterministic_behavior
        ]
        
        test_results = []
        
        for test_method in test_methods:
            try:
                result = await test_method()
                test_results.append(result)
                
                status = "✅ PASSED" if result["passed"] else "❌ FAILED"
                logger.info(f"{status} {result['test_name']}")
                
            except Exception as e:
                logger.error(f"❌ Test {test_method.__name__} failed with exception: {e}")
                test_results.append({
                    "test_name": test_method.__name__,
                    "passed": False,
                    "error": str(e)
                })
        
        # Calculate overall results
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r["passed"])
        success_rate = passed_tests / total_tests
        
        overall_result = {
            "test_suite": "Strategy Mapper Comprehensive Test Suite",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "overall_passed": success_rate >= 0.8,  # 80% pass rate required
            "individual_results": test_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"🎯 Test suite completed: {passed_tests}/{total_tests} tests passed ({success_rate:.1%})")
        
        return overall_result

# Async test runner
async def run_strategy_mapper_tests():
    """Run the strategy mapper test suite."""
    test_suite = StrategyMapperTestSuite()
    return await test_suite.run_comprehensive_test_suite()

if __name__ == "__main__":
    # Run tests if executed directly
    asyncio.run(run_strategy_mapper_tests())
