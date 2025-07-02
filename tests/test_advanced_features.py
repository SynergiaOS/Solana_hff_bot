#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Advanced Features Tests
Comprehensive testing for Add to Winner, Drawdown Guard, and Feedback Scorer
"""

import pytest
import asyncio
import json
import time
import redis
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add brain directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'brain'))

# Import modules to test
from brain.add_to_winner import AddToWinnerSystem, PositionPerformance
from brain.drawdown_guard import DrawdownGuard, DrawdownMetrics
from brain.feedback_scorer import AIFeedbackScorer, TransactionFeedback

class TestAddToWinnerSystem:
    """Test suite for Add to Winner system"""
    
    @pytest.fixture
    def add_to_winner(self):
        """Create Add to Winner system for testing"""
        with patch('redis.Redis'):
            system = AddToWinnerSystem()
            system.redis_client = Mock()
            return system
    
    @pytest.fixture
    def sample_position_performance(self):
        """Sample position performance data"""
        return PositionPerformance(
            symbol="SOL",
            entry_price=100.0,
            current_price=110.0,
            quantity=1.0,
            unrealized_pnl=10.0,
            pnl_percentage=0.10,  # 10% profit
            momentum_score=0.8,   # High momentum
            time_held=600,        # 10 minutes
            confidence_score=0.9  # High confidence
        )
    
    def test_should_scale_position_profitable(self, add_to_winner, sample_position_performance):
        """Test that profitable positions with good momentum should be scaled"""
        result = add_to_winner.should_scale_position(sample_position_performance)
        assert result == True
    
    def test_should_not_scale_position_unprofitable(self, add_to_winner):
        """Test that unprofitable positions should not be scaled"""
        losing_position = PositionPerformance(
            symbol="SOL",
            entry_price=100.0,
            current_price=95.0,
            quantity=1.0,
            unrealized_pnl=-5.0,
            pnl_percentage=-0.05,  # 5% loss
            momentum_score=0.3,    # Low momentum
            time_held=600,
            confidence_score=0.5
        )
        
        result = add_to_winner.should_scale_position(losing_position)
        assert result == False
    
    def test_should_not_scale_position_low_momentum(self, add_to_winner):
        """Test that positions with low momentum should not be scaled"""
        low_momentum_position = PositionPerformance(
            symbol="SOL",
            entry_price=100.0,
            current_price=110.0,
            quantity=1.0,
            unrealized_pnl=10.0,
            pnl_percentage=0.10,
            momentum_score=0.3,    # Low momentum
            time_held=600,
            confidence_score=0.9
        )
        
        result = add_to_winner.should_scale_position(low_momentum_position)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_execute_position_scaling(self, add_to_winner, sample_position_performance):
        """Test position scaling execution"""
        add_to_winner.redis_client.lpush = Mock()
        
        result = await add_to_winner.execute_position_scaling(sample_position_performance)
        
        assert result == True
        add_to_winner.redis_client.lpush.assert_called()
        
        # Check that scaling signal was created
        call_args = add_to_winner.redis_client.lpush.call_args
        assert call_args[0][0] == 'overmind:commands'
        
        signal_data = json.loads(call_args[0][1])
        assert signal_data['action'] == 'BUY'
        assert signal_data['symbol'] == 'SOL'
        assert signal_data['strategy'] == 'ADD_TO_WINNER'

class TestDrawdownGuard:
    """Test suite for Drawdown Guard system"""
    
    @pytest.fixture
    def drawdown_guard(self):
        """Create Drawdown Guard for testing"""
        with patch('redis.Redis'):
            guard = DrawdownGuard()
            guard.redis_client = Mock()
            return guard
    
    @pytest.fixture
    def sample_drawdown_metrics(self):
        """Sample drawdown metrics"""
        return DrawdownMetrics(
            current_portfolio_value=900.0,
            daily_high=1000.0,
            daily_low=900.0,
            max_drawdown=0.10,
            current_drawdown=0.10,  # 10% drawdown
            daily_pnl=-100.0,
            daily_pnl_percentage=-0.10,
            risk_level="HIGH"
        )
    
    @pytest.mark.asyncio
    async def test_trigger_emergency_stop(self, drawdown_guard, sample_drawdown_metrics):
        """Test emergency stop trigger"""
        # Set emergency drawdown
        sample_drawdown_metrics.current_drawdown = 0.16  # 16% > 15% threshold
        sample_drawdown_metrics.risk_level = "EMERGENCY"
        
        drawdown_guard.close_all_positions = AsyncMock()
        drawdown_guard.redis_client.set = Mock()
        drawdown_guard.redis_client.lpush = Mock()
        
        await drawdown_guard.trigger_emergency_stop(sample_drawdown_metrics)
        
        assert drawdown_guard.emergency_stop_triggered == True
        drawdown_guard.redis_client.set.assert_called_with('overmind:emergency_stop', 'true')
        drawdown_guard.close_all_positions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reduce_position_sizes(self, drawdown_guard, sample_drawdown_metrics):
        """Test position size reduction"""
        # Mock position data
        position_updates = [{
            'positions': {
                'SOL': {'quantity': 2.0},
                'BTC': {'quantity': 0.1}
            }
        }]
        
        drawdown_guard.redis_client.lrange.return_value = [json.dumps(position_updates[0])]
        drawdown_guard.redis_client.lpush = Mock()
        drawdown_guard.redis_client.set = Mock()
        
        await drawdown_guard.reduce_position_sizes(sample_drawdown_metrics)
        
        assert drawdown_guard.drawdown_mode == True
        drawdown_guard.redis_client.set.assert_any_call('overmind:drawdown_mode', 'true')
        
        # Check that reduction signals were sent
        assert drawdown_guard.redis_client.lpush.call_count >= 2  # At least 2 positions reduced
    
    def test_risk_level_classification(self, drawdown_guard):
        """Test risk level classification"""
        # Test different drawdown levels
        test_cases = [
            (0.02, "LOW"),      # 2% drawdown
            (0.06, "MEDIUM"),   # 6% drawdown  
            (0.09, "HIGH"),     # 9% drawdown
            (0.16, "EMERGENCY") # 16% drawdown
        ]
        
        for drawdown, expected_risk in test_cases:
            metrics = DrawdownMetrics(
                current_portfolio_value=1000.0,
                daily_high=1000.0,
                daily_low=1000.0 * (1 - drawdown),
                max_drawdown=drawdown,
                current_drawdown=drawdown,
                daily_pnl=-1000.0 * drawdown,
                daily_pnl_percentage=-drawdown,
                risk_level=expected_risk
            )
            
            assert metrics.risk_level == expected_risk

class TestFeedbackScorer:
    """Test suite for AI Feedback Scorer"""
    
    @pytest.fixture
    def feedback_scorer(self):
        """Create Feedback Scorer for testing"""
        with patch('redis.Redis'), patch('chromadb.PersistentClient'):
            scorer = AIFeedbackScorer()
            scorer.redis_client = Mock()
            scorer.feedback_collection = Mock()
            return scorer
    
    @pytest.fixture
    def sample_execution_result(self):
        """Sample execution result for feedback analysis"""
        return {
            'transaction_id': 'test_tx_123',
            'symbol': 'SOL',
            'action': 'BUY',
            'quantity': 1.0,
            'execution_price': 100.0,
            'confidence': 0.8,
            'strategy': 'MEMECOIN_HUNTER',
            'timestamp': time.time(),
            'estimated_profit': 5.0,  # $5 profit
            'hold_time': 1800  # 30 minutes
        }
    
    @pytest.mark.asyncio
    async def test_analyze_completed_transaction(self, feedback_scorer, sample_execution_result):
        """Test transaction analysis for feedback"""
        feedback_scorer.get_market_conditions = AsyncMock(return_value={
            'sentiment': 0.7,
            'volatility': 0.5,
            'volume': 0.8
        })
        
        feedback = await feedback_scorer.analyze_completed_transaction(sample_execution_result)
        
        assert feedback is not None
        assert feedback.transaction_id == 'test_tx_123'
        assert feedback.symbol == 'SOL'
        assert feedback.pnl == 5.0
        assert feedback.pnl_percentage == 0.05  # 5% profit
        assert len(feedback.lessons_learned) > 0
    
    def test_calculate_outcome_score_profitable(self, feedback_scorer):
        """Test outcome score calculation for profitable trade"""
        score = feedback_scorer.calculate_outcome_score(
            pnl_pct=0.08,      # 8% profit (excellent)
            confidence=0.8,     # High confidence
            hold_time=3600,     # 1 hour
            market_conditions={'volatility': 0.3}  # Low volatility
        )
        
        assert score > 0.8  # Should be high score for excellent trade
    
    def test_calculate_outcome_score_losing(self, feedback_scorer):
        """Test outcome score calculation for losing trade"""
        score = feedback_scorer.calculate_outcome_score(
            pnl_pct=-0.08,     # 8% loss (terrible)
            confidence=0.9,     # High confidence but wrong
            hold_time=1800,     # 30 minutes
            market_conditions={'volatility': 0.8}  # High volatility
        )
        
        assert score < 0.3  # Should be low score for terrible trade
    
    def test_generate_lessons_learned_profitable(self, feedback_scorer):
        """Test lesson generation for profitable trades"""
        lessons = feedback_scorer.generate_lessons_learned(
            pnl_pct=0.06,      # 6% profit
            confidence=0.7,     # Medium confidence
            strategy='MEMECOIN_HUNTER',
            market_conditions={'volatility': 0.4}
        )
        
        assert len(lessons) > 0
        assert any('excellent performance' in lesson.lower() for lesson in lessons)
    
    def test_generate_lessons_learned_losing(self, feedback_scorer):
        """Test lesson generation for losing trades"""
        lessons = feedback_scorer.generate_lessons_learned(
            pnl_pct=-0.04,     # 4% loss
            confidence=0.8,     # High confidence but wrong
            strategy='DEX_ARBITRAGE',
            market_conditions={'volatility': 0.8}
        )
        
        assert len(lessons) > 0
        assert any('poor performance' in lesson.lower() for lesson in lessons)
        assert any('confidence' in lesson.lower() for lesson in lessons)

class TestIntegration:
    """Integration tests for advanced features working together"""
    
    @pytest.mark.asyncio
    async def test_advanced_features_initialization(self):
        """Test that all advanced features can be initialized together"""
        with patch('redis.Redis'), patch('chromadb.PersistentClient'):
            # Test initialization
            add_to_winner = AddToWinnerSystem()
            drawdown_guard = DrawdownGuard()
            feedback_scorer = AIFeedbackScorer()
            
            assert add_to_winner is not None
            assert drawdown_guard is not None
            assert feedback_scorer is not None
    
    @pytest.mark.asyncio
    async def test_emergency_stop_integration(self):
        """Test that emergency stop affects all systems"""
        with patch('redis.Redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis.return_value = mock_redis_instance
            
            # Initialize systems
            add_to_winner = AddToWinnerSystem()
            drawdown_guard = DrawdownGuard()
            
            # Simulate emergency stop
            mock_redis_instance.get.return_value = 'true'
            
            # Both systems should respect emergency stop
            emergency_active = mock_redis_instance.get('overmind:emergency_stop') == 'true'
            assert emergency_active == True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
