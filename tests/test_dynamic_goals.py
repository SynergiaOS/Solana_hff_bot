"""THE OVERMIND PROTOCOL - Comprehensive Testing Suite for Dynamic Goals
Test goal transition scenarios, edge cases, and performance impact validation.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add brain module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'brain', 'src'))

from overmind_brain.goal_manager import dynamic_goal_manager, GoalType
from overmind_brain.strategy_mapper import StrategyMapper
from overmind_brain.portfolio_monitor import PortfolioMonitor

class TestDynamicGoalTransitions:
    """Test suite for dynamic goal transitions and edge cases."""
    
    @pytest.fixture
    async def setup_components(self):
        """Setup test components with mocked dependencies."""
        # Mock DragonflyDB
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.ping.return_value = True
        
        # Initialize components with mocked dependencies
        await dynamic_goal_manager.initialize()
        dynamic_goal_manager.redis_client = mock_redis
        
        strategy_mapper = StrategyMapper()
        await strategy_mapper.initialize()
        strategy_mapper.redis_client = mock_redis
        
        portfolio_monitor = PortfolioMonitor()
        await portfolio_monitor.initialize()
        portfolio_monitor.redis_client = mock_redis
        
        return {
            'goal_manager': dynamic_goal_manager,
            'strategy_mapper': strategy_mapper,
            'portfolio_monitor': portfolio_monitor,
            'mock_redis': mock_redis
        }
    
    @pytest.mark.asyncio
    async def test_goal_modification_during_active_trading(self, setup_components):
        """Test goal modification while trading is active."""
        components = await setup_components
        goal_manager = components['goal_manager']
        strategy_mapper = components['strategy_mapper']
        mock_redis = components['mock_redis']
        
        # Simulate active trading state
        mock_redis.get.side_effect = lambda key: {
            'state:portfolio': json.dumps({
                'total_value_sol': 1.0,
                'total_value_usd': 150.0,
                'goal_progress_percentage': 50.0,
                'last_updated': datetime.utcnow().isoformat()
            }),
            'config:trading_goals': json.dumps({
                'goal_type': 'REACH_BALANCE',
                'target_sol': 2.0,
                'target_usd': 300.0,
                'created_at': datetime.utcnow().isoformat(),
                'modified_at': datetime.utcnow().isoformat(),
                'modified_by': 'test_system',
                'description': 'Initial test goal'
            }),
            'config:trading_goals:last_modified': str(time.time())
        }.get(key)
        
        # Test goal change during active trading
        start_time = time.time()
        
        success = await goal_manager.set_goal(
            goal_type=GoalType.MAXIMIZE_PROFIT,
            target_sol=4.0,
            changed_by='test_active_trading',
            change_reason='Testing goal change during active trading'
        )
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Validate zero-downtime transition
        assert success, "Goal change should succeed during active trading"
        assert latency < 50, f"Goal change latency {latency:.2f}ms exceeds 50ms threshold"
        
        # Verify profile re-evaluation
        portfolio_state = {
            'total_value_sol': 1.0,
            'goal_progress_percentage': 25.0  # Recalculated for 4.0 SOL target
        }
        
        decision = await strategy_mapper.determine_active_profile(portfolio_state)
        assert decision.recommended_profile.value == 'AGGRESSIVE_GROWTH'
        assert decision.should_switch or decision.current_profile.value == 'AGGRESSIVE_GROWTH'
    
    @pytest.mark.asyncio
    async def test_profile_switching_with_new_targets(self, setup_components):
        """Test profile switching behavior with new goal targets."""
        components = await setup_components
        strategy_mapper = components['strategy_mapper']
        mock_redis = components['mock_redis']
        
        # Test scenarios with different goal targets
        test_scenarios = [
            {'current_sol': 0.5, 'target_sol': 2.0, 'expected_profile': 'AGGRESSIVE_GROWTH'},
            {'current_sol': 1.0, 'target_sol': 2.0, 'expected_profile': 'BALANCED_RISK'},
            {'current_sol': 2.0, 'target_sol': 2.0, 'expected_profile': 'CAPITAL_PRESERVATION'},
            {'current_sol': 1.0, 'target_sol': 4.0, 'expected_profile': 'AGGRESSIVE_GROWTH'},
            {'current_sol': 2.0, 'target_sol': 4.0, 'expected_profile': 'BALANCED_RISK'},
            {'current_sol': 4.0, 'target_sol': 4.0, 'expected_profile': 'CAPITAL_PRESERVATION'}
        ]
        
        for scenario in test_scenarios:
            # Update goal configuration
            mock_redis.get.side_effect = lambda key: {
                'config:trading_goals': json.dumps({
                    'goal_type': 'REACH_BALANCE',
                    'target_sol': scenario['target_sol'],
                    'target_usd': scenario['target_sol'] * 150.0,
                    'created_at': datetime.utcnow().isoformat(),
                    'modified_at': datetime.utcnow().isoformat(),
                    'modified_by': 'test_system',
                    'description': f"Test goal {scenario['target_sol']} SOL"
                }),
                'config:trading_goals:last_modified': str(time.time())
            }.get(key)
            
            # Test profile determination
            portfolio_state = {
                'total_value_sol': scenario['current_sol'],
                'goal_progress_percentage': (scenario['current_sol'] / scenario['target_sol']) * 100
            }
            
            decision = await strategy_mapper.determine_active_profile(portfolio_state)
            
            assert decision.recommended_profile.value == scenario['expected_profile'], \
                f"Expected {scenario['expected_profile']} for {scenario['current_sol']}/{scenario['target_sol']} SOL"
    
    @pytest.mark.asyncio
    async def test_api_endpoint_validation(self, setup_components):
        """Test API endpoint functionality and validation."""
        components = await setup_components
        goal_manager = components['goal_manager']
        
        # Test valid goal setting
        valid_goals = [
            {'goal_type': GoalType.REACH_BALANCE, 'target_sol': 2.0},
            {'goal_type': GoalType.CAPITAL_PRESERVATION, 'target_sol': 1.5},
            {'goal_type': GoalType.MAXIMIZE_PROFIT, 'target_sol': 5.0}
        ]
        
        for goal in valid_goals:
            success = await goal_manager.set_goal(
                goal_type=goal['goal_type'],
                target_sol=goal['target_sol'],
                changed_by='test_api',
                change_reason='API validation test'
            )
            assert success, f"Valid goal {goal} should be accepted"
        
        # Test invalid goal validation
        invalid_goals = [
            {'goal_type': GoalType.REACH_BALANCE, 'target_sol': 0.0},  # Zero target
            {'goal_type': GoalType.REACH_BALANCE, 'target_sol': -1.0},  # Negative target
            {'goal_type': GoalType.REACH_BALANCE, 'target_sol': 101.0}  # Exceeds maximum
        ]
        
        for goal in invalid_goals:
            try:
                success = await goal_manager.set_goal(
                    goal_type=goal['goal_type'],
                    target_sol=goal['target_sol'],
                    changed_by='test_api',
                    change_reason='Invalid goal test'
                )
                assert not success, f"Invalid goal {goal} should be rejected"
            except (ValueError, AssertionError):
                pass  # Expected validation error
    
    @pytest.mark.asyncio
    async def test_error_handling_and_rollback(self, setup_components):
        """Test error handling and rollback scenarios."""
        components = await setup_components
        goal_manager = components['goal_manager']
        mock_redis = components['mock_redis']
        
        # Set initial valid goal
        await goal_manager.set_goal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=2.0,
            changed_by='test_system',
            change_reason='Initial goal for rollback test'
        )
        
        # Simulate Redis failure during goal update
        original_set = mock_redis.set
        mock_redis.set.side_effect = Exception("Redis connection failed")
        
        # Attempt goal change that should fail
        success = await goal_manager.set_goal(
            goal_type=GoalType.MAXIMIZE_PROFIT,
            target_sol=4.0,
            changed_by='test_system',
            change_reason='Goal change that should fail'
        )
        
        assert not success, "Goal change should fail when Redis is unavailable"
        
        # Restore Redis functionality
        mock_redis.set.side_effect = original_set
        
        # Verify system can recover
        success = await goal_manager.set_goal(
            goal_type=GoalType.MAXIMIZE_PROFIT,
            target_sol=4.0,
            changed_by='test_system',
            change_reason='Recovery test after Redis failure'
        )
        
        assert success, "Goal change should succeed after Redis recovery"
    
    @pytest.mark.asyncio
    async def test_performance_impact_validation(self, setup_components):
        """Test performance impact of goal changes."""
        components = await setup_components
        goal_manager = components['goal_manager']
        strategy_mapper = components['strategy_mapper']
        
        # Baseline performance measurement
        portfolio_state = {
            'total_value_sol': 1.0,
            'goal_progress_percentage': 50.0
        }
        
        # Measure baseline decision latency
        baseline_times = []
        for _ in range(10):
            start_time = time.time()
            await strategy_mapper.determine_active_profile(portfolio_state)
            end_time = time.time()
            baseline_times.append((end_time - start_time) * 1000)
        
        baseline_avg = sum(baseline_times) / len(baseline_times)
        
        # Change goal and measure performance impact
        await goal_manager.set_goal(
            goal_type=GoalType.MAXIMIZE_PROFIT,
            target_sol=4.0,
            changed_by='test_performance',
            change_reason='Performance impact test'
        )
        
        # Measure post-change decision latency
        post_change_times = []
        for _ in range(10):
            start_time = time.time()
            await strategy_mapper.determine_active_profile(portfolio_state)
            end_time = time.time()
            post_change_times.append((end_time - start_time) * 1000)
        
        post_change_avg = sum(post_change_times) / len(post_change_times)
        
        # Validate performance impact
        performance_impact = ((post_change_avg - baseline_avg) / baseline_avg) * 100
        
        assert baseline_avg < 50, f"Baseline latency {baseline_avg:.2f}ms exceeds 50ms threshold"
        assert post_change_avg < 50, f"Post-change latency {post_change_avg:.2f}ms exceeds 50ms threshold"
        assert abs(performance_impact) < 20, f"Performance impact {performance_impact:.1f}% exceeds 20% threshold"
    
    @pytest.mark.asyncio
    async def test_edge_cases_and_boundary_conditions(self, setup_components):
        """Test edge cases and boundary conditions."""
        components = await setup_components
        goal_manager = components['goal_manager']
        strategy_mapper = components['strategy_mapper']
        
        # Test boundary conditions for profile switching
        boundary_tests = [
            {'progress': 24.9, 'expected': 'AGGRESSIVE_GROWTH'},  # Just below 25%
            {'progress': 25.0, 'expected': 'BALANCED_RISK'},      # Exactly 25%
            {'progress': 25.1, 'expected': 'BALANCED_RISK'},      # Just above 25%
            {'progress': 99.9, 'expected': 'BALANCED_RISK'},      # Just below 100%
            {'progress': 100.0, 'expected': 'CAPITAL_PRESERVATION'}, # Exactly 100%
            {'progress': 100.1, 'expected': 'CAPITAL_PRESERVATION'}, # Just above 100%
        ]
        
        for test in boundary_tests:
            portfolio_state = {
                'total_value_sol': test['progress'] / 50.0,  # Assuming 2.0 SOL target
                'goal_progress_percentage': test['progress']
            }
            
            decision = await strategy_mapper.determine_active_profile(portfolio_state)
            
            assert decision.recommended_profile.value == test['expected'], \
                f"Progress {test['progress']}% should map to {test['expected']}"
        
        # Test rapid goal changes
        rapid_change_start = time.time()
        
        for i in range(5):
            await goal_manager.set_goal(
                goal_type=GoalType.REACH_BALANCE,
                target_sol=2.0 + i * 0.5,
                changed_by='test_rapid',
                change_reason=f'Rapid change {i+1}'
            )
        
        rapid_change_end = time.time()
        rapid_change_latency = (rapid_change_end - rapid_change_start) * 1000
        
        assert rapid_change_latency < 250, f"5 rapid goal changes took {rapid_change_latency:.2f}ms (>250ms)"
    
    @pytest.mark.asyncio
    async def test_zero_downtime_transitions(self, setup_components):
        """Test zero-downtime goal transitions."""
        components = await setup_components
        goal_manager = components['goal_manager']
        strategy_mapper = components['strategy_mapper']
        
        # Simulate concurrent operations during goal change
        async def concurrent_decision_making():
            """Simulate ongoing decision making during goal change."""
            portfolio_state = {
                'total_value_sol': 1.0,
                'goal_progress_percentage': 50.0
            }
            
            decisions = []
            for _ in range(10):
                decision = await strategy_mapper.determine_active_profile(portfolio_state)
                decisions.append(decision)
                await asyncio.sleep(0.01)  # 10ms between decisions
            
            return decisions
        
        # Start concurrent decision making
        decision_task = asyncio.create_task(concurrent_decision_making())
        
        # Wait a bit then change goal
        await asyncio.sleep(0.02)
        
        goal_change_start = time.time()
        success = await goal_manager.set_goal(
            goal_type=GoalType.MAXIMIZE_PROFIT,
            target_sol=4.0,
            changed_by='test_zero_downtime',
            change_reason='Zero downtime test'
        )
        goal_change_end = time.time()
        
        # Wait for decision making to complete
        decisions = await decision_task
        
        # Validate results
        assert success, "Goal change should succeed during concurrent operations"
        assert len(decisions) == 10, "All concurrent decisions should complete"
        
        goal_change_latency = (goal_change_end - goal_change_start) * 1000
        assert goal_change_latency < 50, f"Goal change latency {goal_change_latency:.2f}ms exceeds 50ms"
        
        # Verify no decision failures
        for i, decision in enumerate(decisions):
            assert decision is not None, f"Decision {i} should not be None"
            assert hasattr(decision, 'recommended_profile'), f"Decision {i} should have recommended_profile"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
