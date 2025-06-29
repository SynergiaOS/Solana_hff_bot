"""Integration tests for THE OVERMIND PROTOCOL Enhanced Brain System"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from overmind_brain.enhanced_brain_orchestrator import EnhancedBrainOrchestrator
from overmind_brain.enhanced_memory_system import TradingEpisode
from overmind_brain.enhanced_planning_layer import PlanningPhase

class TestEnhancedBrainIntegration:
    """Test the complete enhanced brain system integration"""
    
    @pytest.fixture
    async def brain_orchestrator(self):
        """Create brain orchestrator for testing"""
        # Use in-memory setup for testing
        orchestrator = EnhancedBrainOrchestrator(mongodb_uri=None)
        yield orchestrator
        await orchestrator.shutdown()
        
    @pytest.mark.asyncio
    async def test_complete_decision_pipeline(self, brain_orchestrator):
        """Test the complete decision-making pipeline"""
        # Prepare market data
        market_data = {
            'symbol': 'SOL/USDC',
            'price': 150.50,
            'price_change_percent': 5.2,
            'volume': 1000000,
            'avg_volume': 800000,
            'volume_ratio': 1.25,
            'market_type': 'crypto',
            'volatility': 'medium',
            'timestamp': datetime.now().isoformat()
        }
        
        # Process market signal
        decision = await brain_orchestrator.process_market_signal(market_data)
        
        # Verify decision structure
        assert 'action' in decision
        assert 'confidence' in decision
        assert 'timestamp' in decision
        assert decision['action'] in ['BUY', 'SELL', 'HOLD']
        assert 0.0 <= decision['confidence'] <= 1.0
        
        # Verify decision was recorded
        assert brain_orchestrator.total_decisions == 1
        assert len(brain_orchestrator.decision_history) == 1
        
        print(f"✅ Decision made: {decision['action']} with confidence {decision['confidence']:.2f}")
        
    @pytest.mark.asyncio
    async def test_memory_system_integration(self, brain_orchestrator):
        """Test memory system integration and learning"""
        # Add some historical episodes to memory
        historical_episodes = [
            TradingEpisode(
                episode_id="ep_001",
                market_context={'symbol': 'SOL/USDC', 'market_type': 'crypto', 'volatility': 'medium'},
                decision_made={'action': 'BUY', 'confidence': 0.8},
                outcome={'profit_loss': 0.05, 'execution_time': 45},
                lessons_learned=['High confidence decisions in medium volatility work well'],
                timestamp=datetime.now() - timedelta(hours=1),
                success_score=0.8
            ),
            TradingEpisode(
                episode_id="ep_002",
                market_context={'symbol': 'SOL/USDC', 'market_type': 'crypto', 'volatility': 'high'},
                decision_made={'action': 'SELL', 'confidence': 0.6},
                outcome={'profit_loss': -0.02, 'execution_time': 30},
                lessons_learned=['Avoid trading in high volatility conditions'],
                timestamp=datetime.now() - timedelta(hours=2),
                success_score=0.3
            )
        ]
        
        # Add episodes to memory
        for episode in historical_episodes:
            await brain_orchestrator.memory_system.add_trading_episode(episode)
            
        # Test memory query
        memory_results = await brain_orchestrator.query_brain_memory("SOL/USDC trading")
        
        assert 'episodic' in memory_results
        assert len(memory_results['episodic']) > 0
        
        print(f"✅ Memory system contains {len(memory_results['episodic'])} relevant episodes")
        
    @pytest.mark.asyncio
    async def test_reflection_learning(self, brain_orchestrator):
        """Test reflection and learning from outcomes"""
        # Make initial decision
        market_data = {
            'symbol': 'ETH/USDC',
            'price': 2500.0,
            'price_change_percent': 3.5,
            'volume': 500000,
            'market_type': 'crypto'
        }
        
        decision = await brain_orchestrator.process_market_signal(market_data)
        decision_id = brain_orchestrator.decision_history[-1]['decision_id']
        
        # Record outcome
        outcome = {
            'profit_loss': 0.03,
            'execution_time': 60,
            'steps_executed': 3,
            'lessons_learned': ['Market timing was excellent', 'Position sizing was appropriate']
        }
        
        await brain_orchestrator.record_outcome(decision_id, outcome)
        
        # Verify learning occurred
        performance = brain_orchestrator.get_performance_metrics()
        assert performance['total_decisions'] == 1
        assert performance['successful_decisions'] == 1
        assert performance['success_rate'] == 1.0
        assert performance['total_profit_loss'] == 0.03
        
        print(f"✅ Learning recorded: Success rate {performance['success_rate']:.2f}")
        
    @pytest.mark.asyncio
    async def test_planning_phases(self, brain_orchestrator):
        """Test that all planning phases are executed"""
        market_data = {
            'symbol': 'BTC/USDC',
            'price': 45000.0,
            'price_change_percent': -2.1,
            'volume': 2000000,
            'market_type': 'crypto'
        }
        
        # Track phase changes during processing
        phases_executed = []
        original_setter = brain_orchestrator.__setattr__
        
        def track_phase_changes(name, value):
            if name == 'active_phase' and isinstance(value, PlanningPhase):
                phases_executed.append(value)
            original_setter(name, value)
            
        brain_orchestrator.__setattr__ = track_phase_changes
        
        # Process signal
        decision = await brain_orchestrator.process_market_signal(market_data)
        
        # Verify all phases were executed
        expected_phases = [
            PlanningPhase.PERCEPTION,
            PlanningPhase.REFLECTION,
            PlanningPhase.REASONING,
            PlanningPhase.DECOMPOSITION,
            PlanningPhase.ACTION_PLANNING
        ]
        
        for phase in expected_phases:
            assert phase in phases_executed, f"Phase {phase.value} was not executed"
            
        print(f"✅ All {len(expected_phases)} planning phases executed successfully")
        
    @pytest.mark.asyncio
    async def test_risk_management_integration(self, brain_orchestrator):
        """Test risk management integration in decision making"""
        # High volatility market data
        high_risk_market = {
            'symbol': 'MEME/USDC',
            'price': 0.001,
            'price_change_percent': 25.0,  # Very high volatility
            'volume': 10000000,
            'market_type': 'memecoin'
        }
        
        decision = await brain_orchestrator.process_market_signal(high_risk_market)
        
        # In high volatility, system should either:
        # 1. Reduce position size significantly
        # 2. Choose HOLD action
        # 3. Have lower confidence
        
        if decision['action'] != 'HOLD':
            assert 'position_size' in decision
            assert decision['position_size'] < 0.05  # Less than 5% position
            
        # Confidence should be adjusted for high risk
        assert decision['confidence'] <= 0.8  # Should not be overconfident in high volatility
        
        print(f"✅ Risk management applied: {decision['action']} with size {decision.get('position_size', 0):.4f}")
        
    @pytest.mark.asyncio
    async def test_semantic_memory_integration(self, brain_orchestrator):
        """Test semantic memory integration"""
        # Add trading rules to semantic memory
        brain_orchestrator.memory_system.semantic_memory.add_trading_rule(
            "momentum_rule",
            "Buy when price increases with high volume",
            ["price_change > 3%", "volume_ratio > 1.5"],
            0.7
        )
        
        brain_orchestrator.memory_system.semantic_memory.add_concept(
            "bull_market",
            "Market condition with sustained upward price movement",
            ["momentum", "volume", "sentiment"]
        )
        
        # Test market data that should trigger the rule
        market_data = {
            'symbol': 'ADA/USDC',
            'price': 1.20,
            'price_change_percent': 4.5,
            'volume_ratio': 2.0,
            'market_type': 'crypto'
        }
        
        decision = await brain_orchestrator.process_market_signal(market_data)
        
        # Should lean towards BUY due to momentum rule
        assert decision['action'] in ['BUY', 'HOLD']  # Should not be SELL
        
        # Query semantic memory
        memory_results = await brain_orchestrator.query_brain_memory("momentum")
        assert 'semantic' in memory_results
        
        print(f"✅ Semantic memory influenced decision: {decision['action']}")
        
    @pytest.mark.asyncio
    async def test_performance_tracking(self, brain_orchestrator):
        """Test performance tracking and metrics"""
        # Simulate multiple decisions and outcomes
        decisions_data = [
            ({'symbol': 'SOL/USDC', 'price': 150, 'price_change_percent': 5}, {'profit_loss': 0.04}),
            ({'symbol': 'ETH/USDC', 'price': 2500, 'price_change_percent': -3}, {'profit_loss': -0.01}),
            ({'symbol': 'BTC/USDC', 'price': 45000, 'price_change_percent': 2}, {'profit_loss': 0.02}),
        ]
        
        decision_ids = []
        
        # Process decisions
        for market_data, _ in decisions_data:
            market_data.update({'volume': 1000000, 'market_type': 'crypto'})
            decision = await brain_orchestrator.process_market_signal(market_data)
            decision_ids.append(brain_orchestrator.decision_history[-1]['decision_id'])
            
        # Record outcomes
        for i, (_, outcome) in enumerate(decisions_data):
            await brain_orchestrator.record_outcome(decision_ids[i], outcome)
            
        # Check performance metrics
        metrics = brain_orchestrator.get_performance_metrics()
        
        assert metrics['total_decisions'] == 3
        assert metrics['successful_decisions'] == 2  # Two profitable decisions
        assert metrics['success_rate'] == 2/3
        assert abs(metrics['total_profit_loss'] - 0.05) < 0.001  # 0.04 + (-0.01) + 0.02
        
        print(f"✅ Performance tracking: {metrics['success_rate']:.2f} success rate, "
              f"{metrics['total_profit_loss']:.4f} total P&L")
        
    @pytest.mark.asyncio
    async def test_working_memory_capacity(self, brain_orchestrator):
        """Test working memory capacity management"""
        # Add many items to working memory to test capacity limits
        working_memory = brain_orchestrator.memory_system.working_memory
        
        # Add items beyond capacity (capacity is 7)
        for i in range(10):
            working_memory.add_to_working_memory(
                f"item_{i}",
                {'data': f'test_data_{i}'},
                importance=0.5 + (i * 0.05)  # Increasing importance
            )
            
        # Should only keep 7 items (capacity limit)
        assert len(working_memory.active_items) == 7
        
        # Should keep the most important items
        importances = [item['importance'] for item in working_memory.active_items.values()]
        assert min(importances) >= 0.65  # Should have kept higher importance items
        
        print(f"✅ Working memory capacity managed: {len(working_memory.active_items)} items retained")

if __name__ == "__main__":
    # Run a quick integration test
    async def quick_test():
        orchestrator = EnhancedBrainOrchestrator()
        
        market_data = {
            'symbol': 'SOL/USDC',
            'price': 150.50,
            'price_change_percent': 5.2,
            'volume': 1000000,
            'avg_volume': 800000,
            'volume_ratio': 1.25,
            'market_type': 'crypto'
        }
        
        print("🧠 Testing Enhanced Brain Orchestrator...")
        decision = await orchestrator.process_market_signal(market_data)
        
        print(f"📊 Decision: {decision}")
        print(f"📈 Performance: {orchestrator.get_performance_metrics()}")
        
        await orchestrator.shutdown()
        print("✅ Quick test completed!")
        
    asyncio.run(quick_test())
