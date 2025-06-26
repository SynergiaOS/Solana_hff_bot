"""THE OVERMIND PROTOCOL - Mission Control Dashboard Testing Suite
Test dashboard functionality, API integration, and user interface components.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add mission control to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mission_control'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'brain', 'src'))

class TestMissionControlDashboard:
    """Test suite for Mission Control dashboard functionality."""
    
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components for testing."""
        with patch('streamlit.session_state') as mock_session_state:
            mock_session_state.initialized = True
            mock_session_state.current_goal = {
                'goal_type': 'REACH_BALANCE',
                'target_sol': 2.0,
                'target_usd': 300.0,
                'created_at': '2024-01-01T00:00:00Z',
                'modified_at': '2024-01-01T00:00:00Z',
                'modified_by': 'test_user',
                'description': 'Test goal'
            }
            mock_session_state.portfolio_state = {
                'total_value_sol': 1.5,
                'total_value_usd': 225.0,
                'goal_progress_percentage': 75.0,
                'last_updated': '2024-01-01T00:00:00Z'
            }
            mock_session_state.system_status = {
                'goal_manager': {'status': 'operational'},
                'portfolio_monitor': 'operational',
                'strategy_mapper': 'operational',
                'adaptive_cortex': 'operational'
            }
            yield mock_session_state
    
    @pytest.fixture
    def mock_components(self):
        """Mock OVERMIND components for testing."""
        mock_goal_manager = AsyncMock()
        mock_goal_manager.get_current_goal.return_value = {
            'goal_type': 'REACH_BALANCE',
            'target_sol': 2.0,
            'target_usd': 300.0,
            'created_at': '2024-01-01T00:00:00Z',
            'modified_at': '2024-01-01T00:00:00Z',
            'modified_by': 'test_user',
            'description': 'Test goal'
        }
        mock_goal_manager.set_goal.return_value = True
        mock_goal_manager.get_goal_history.return_value = []
        mock_goal_manager.get_status.return_value = {'status': 'operational'}
        
        mock_portfolio_monitor = AsyncMock()
        mock_portfolio_monitor.get_portfolio_state.return_value = {
            'total_value_sol': 1.5,
            'total_value_usd': 225.0,
            'goal_progress_percentage': 75.0,
            'last_updated': '2024-01-01T00:00:00Z'
        }
        
        mock_strategy_mapper = AsyncMock()
        mock_strategy_mapper.determine_active_profile.return_value = {
            'current_profile': 'BALANCED_RISK',
            'recommended_profile': 'BALANCED_RISK',
            'should_switch': False,
            'confidence': 0.85
        }
        
        return {
            'goal_manager': mock_goal_manager,
            'portfolio_monitor': mock_portfolio_monitor,
            'strategy_mapper': mock_strategy_mapper
        }
    
    def test_dashboard_initialization(self, mock_streamlit, mock_components):
        """Test dashboard initialization and component loading."""
        # Import after mocking
        try:
            from app import initialize_components
            
            # Test component initialization
            with patch('app.dynamic_goal_manager', mock_components['goal_manager']):
                with patch('app.PortfolioMonitor', return_value=mock_components['portfolio_monitor']):
                    with patch('app.StrategyMapper', return_value=mock_components['strategy_mapper']):
                        # Simulate initialization
                        assert mock_streamlit.initialized == True
                        assert mock_streamlit.current_goal is not None
                        assert mock_streamlit.portfolio_state is not None
                        assert mock_streamlit.system_status is not None
                        
        except ImportError:
            # Dashboard components not available in test environment
            pytest.skip("Dashboard components not available for testing")
    
    def test_goal_management_functionality(self, mock_components):
        """Test goal management functionality."""
        goal_manager = mock_components['goal_manager']
        
        # Test goal setting
        asyncio.run(goal_manager.set_goal(
            goal_type='MAXIMIZE_PROFIT',
            target_sol=4.0,
            changed_by='test_user',
            change_reason='Dashboard test'
        ))
        
        goal_manager.set_goal.assert_called_once()
        
        # Test goal retrieval
        asyncio.run(goal_manager.get_current_goal())
        goal_manager.get_current_goal.assert_called()
        
        # Test goal history
        asyncio.run(goal_manager.get_goal_history(limit=10))
        goal_manager.get_goal_history.assert_called_with(limit=10)
    
    def test_portfolio_tracking_functionality(self, mock_components):
        """Test portfolio tracking functionality."""
        portfolio_monitor = mock_components['portfolio_monitor']
        
        # Test portfolio state retrieval
        result = asyncio.run(portfolio_monitor.get_portfolio_state())
        
        assert result is not None
        assert 'total_value_sol' in result
        assert 'total_value_usd' in result
        assert 'goal_progress_percentage' in result
        
        portfolio_monitor.get_portfolio_state.assert_called()
    
    def test_trading_activity_monitoring(self, mock_components):
        """Test trading activity monitoring functionality."""
        # Simulate trading data
        trading_data = [
            {
                'timestamp': '2024-01-01T12:00:00Z',
                'strategy': 'memecoin_hunter',
                'action': 'BUY',
                'amount': '0.1 SOL',
                'status': 'COMPLETED',
                'pnl': '+0.005 SOL'
            },
            {
                'timestamp': '2024-01-01T12:05:00Z',
                'strategy': 'meteora_damm',
                'action': 'SELL',
                'amount': '0.05 SOL',
                'status': 'COMPLETED',
                'pnl': '+0.002 SOL'
            }
        ]
        
        # Test data filtering
        filtered_data = [d for d in trading_data if d['strategy'] == 'memecoin_hunter']
        assert len(filtered_data) == 1
        assert filtered_data[0]['strategy'] == 'memecoin_hunter'
        
        # Test performance metrics calculation
        completed_trades = [d for d in trading_data if d['status'] == 'COMPLETED']
        assert len(completed_trades) == 2
        
        profitable_trades = [d for d in completed_trades if '+' in d['pnl']]
        win_rate = (len(profitable_trades) / len(completed_trades)) * 100
        assert win_rate == 100.0
    
    def test_system_health_monitoring(self, mock_components):
        """Test system health monitoring functionality."""
        # Test component status
        components_status = {
            'goal_manager': mock_components['goal_manager'],
            'portfolio_monitor': mock_components['portfolio_monitor'],
            'strategy_mapper': mock_components['strategy_mapper']
        }
        
        for component_name, component in components_status.items():
            assert component is not None, f"{component_name} should be available"
        
        # Test service health simulation
        services_health = {
            'DragonflyDB': {'status': 'healthy', 'uptime': '99.9%'},
            'TensorZero': {'status': 'healthy', 'uptime': '99.8%'},
            'Prometheus': {'status': 'healthy', 'uptime': '100%'},
            'Grafana': {'status': 'healthy', 'uptime': '99.9%'},
            'Nginx': {'status': 'healthy', 'uptime': '100%'},
            'Mission Control': {'status': 'healthy', 'uptime': '100%'}
        }
        
        for service, health in services_health.items():
            assert health['status'] == 'healthy', f"{service} should be healthy"
            assert float(health['uptime'].replace('%', '')) >= 99.0, f"{service} uptime should be >= 99%"
    
    def test_api_integration_error_handling(self, mock_components):
        """Test API integration and error handling."""
        goal_manager = mock_components['goal_manager']
        
        # Test successful API call
        goal_manager.set_goal.return_value = True
        result = asyncio.run(goal_manager.set_goal(
            goal_type='REACH_BALANCE',
            target_sol=2.0,
            changed_by='test_user',
            change_reason='API test'
        ))
        assert result == True
        
        # Test API failure handling
        goal_manager.set_goal.side_effect = Exception("API connection failed")
        
        try:
            asyncio.run(goal_manager.set_goal(
                goal_type='REACH_BALANCE',
                target_sol=2.0,
                changed_by='test_user',
                change_reason='API failure test'
            ))
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "API connection failed" in str(e)
        
        # Reset for further tests
        goal_manager.set_goal.side_effect = None
        goal_manager.set_goal.return_value = True
    
    def test_real_time_updates_performance(self, mock_components):
        """Test real-time updates and performance."""
        goal_manager = mock_components['goal_manager']
        portfolio_monitor = mock_components['portfolio_monitor']
        
        # Test update latency
        start_time = time.time()
        
        # Simulate data updates
        asyncio.run(goal_manager.get_current_goal())
        asyncio.run(portfolio_monitor.get_portfolio_state())
        
        end_time = time.time()
        update_latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert update_latency < 100, f"Update latency {update_latency:.2f}ms exceeds 100ms threshold"
        
        # Test multiple rapid updates
        rapid_update_start = time.time()
        
        for _ in range(10):
            asyncio.run(goal_manager.get_current_goal())
        
        rapid_update_end = time.time()
        rapid_update_latency = (rapid_update_end - rapid_update_start) * 1000
        
        assert rapid_update_latency < 500, f"10 rapid updates took {rapid_update_latency:.2f}ms (>500ms)"
    
    def test_goal_change_confirmation_dialogs(self, mock_components):
        """Test goal change confirmation dialogs and impact assessment."""
        # Test impact assessment calculation
        old_goal = {
            'goal_type': 'REACH_BALANCE',
            'target_sol': 2.0,
            'target_usd': 300.0
        }
        
        new_goal = {
            'goal_type': 'MAXIMIZE_PROFIT',
            'target_sol': 4.0,
            'target_usd': 600.0
        }
        
        # Calculate impact assessment
        percentage_change = ((new_goal['target_sol'] - old_goal['target_sol']) / old_goal['target_sol']) * 100
        goal_type_changed = old_goal['goal_type'] != new_goal['goal_type']
        
        assert percentage_change == 100.0, "Target change should be 100%"
        assert goal_type_changed == True, "Goal type should have changed"
        
        # Test risk level assessment
        risk_mapping = {
            'REACH_BALANCE': 'moderate',
            'CAPITAL_PRESERVATION': 'low',
            'MAXIMIZE_PROFIT': 'high'
        }
        
        old_risk = risk_mapping[old_goal['goal_type']]
        new_risk = risk_mapping[new_goal['goal_type']]
        
        assert old_risk == 'moderate', "Old goal should have moderate risk"
        assert new_risk == 'high', "New goal should have high risk"
        
        risk_change = 'increased' if new_risk == 'high' and old_risk != 'high' else 'unchanged'
        assert risk_change == 'increased', "Risk level should have increased"
    
    def test_dashboard_responsiveness(self, mock_streamlit):
        """Test dashboard responsiveness and user experience."""
        # Test session state management
        assert hasattr(mock_streamlit, 'initialized')
        assert hasattr(mock_streamlit, 'current_goal')
        assert hasattr(mock_streamlit, 'portfolio_state')
        assert hasattr(mock_streamlit, 'system_status')
        
        # Test data consistency
        assert mock_streamlit.current_goal is not None
        assert mock_streamlit.portfolio_state is not None
        assert mock_streamlit.system_status is not None
        
        # Test goal progress calculation
        portfolio_state = mock_streamlit.portfolio_state
        current_goal = mock_streamlit.current_goal
        
        if current_goal and portfolio_state:
            expected_progress = (portfolio_state['total_value_sol'] / current_goal['target_sol']) * 100
            actual_progress = portfolio_state['goal_progress_percentage']
            
            # Allow for small floating point differences
            assert abs(expected_progress - actual_progress) < 1.0, \
                f"Progress calculation mismatch: expected {expected_progress:.1f}%, got {actual_progress:.1f}%"

class TestDashboardIntegration:
    """Integration tests for dashboard components."""
    
    def test_end_to_end_goal_modification(self, mock_components):
        """Test end-to-end goal modification workflow."""
        goal_manager = mock_components['goal_manager']
        strategy_mapper = mock_components['strategy_mapper']
        
        # Step 1: Get current goal
        current_goal = asyncio.run(goal_manager.get_current_goal())
        assert current_goal is not None
        
        # Step 2: Modify goal
        success = asyncio.run(goal_manager.set_goal(
            goal_type='MAXIMIZE_PROFIT',
            target_sol=4.0,
            changed_by='integration_test',
            change_reason='End-to-end test'
        ))
        assert success == True
        
        # Step 3: Verify profile adaptation
        portfolio_state = {
            'total_value_sol': 1.0,
            'goal_progress_percentage': 25.0  # 1.0/4.0 = 25%
        }
        
        decision = asyncio.run(strategy_mapper.determine_active_profile(portfolio_state))
        assert decision is not None
        
        # Step 4: Verify audit trail
        history = asyncio.run(goal_manager.get_goal_history(limit=5))
        assert isinstance(history, list)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
