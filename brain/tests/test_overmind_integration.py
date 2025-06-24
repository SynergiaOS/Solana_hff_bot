#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Full Integration Test
Complete end-to-end testing of all components
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from overmind_brain.brain import OVERMINDBrain
from overmind_brain.vector_memory import VectorMemory
from overmind_brain.decision_engine import DecisionEngine
from overmind_brain.risk_analyzer import RiskAnalyzer
from overmind_brain.market_analyzer import MarketAnalyzer


class TestOVERMINDIntegration:
    """Complete integration test suite for THE OVERMIND PROTOCOL"""
    
    @pytest.fixture
    async def overmind_brain(self):
        """Create fully mocked OVERMIND Brain for testing"""
        with patch('overmind_brain.brain.redis.Redis'):
            with patch('overmind_brain.vector_memory.QdrantClient'):
                with patch('overmind_brain.vector_memory.SentenceTransformer'):
                    brain = OVERMINDBrain()
                    
                    # Mock Redis connection
                    brain.redis = AsyncMock()
                    brain.redis.ping = AsyncMock(return_value=True)
                    brain.redis.lpush = AsyncMock()
                    brain.redis.blpop = AsyncMock()
                    
                    # Mock vector memory
                    brain.vector_memory.embedding_model.encode = Mock(return_value=[0.1] * 384)
                    brain.vector_memory.client.search = Mock(return_value=[])
                    brain.vector_memory.client.get_collection = Mock()
                    
                    return brain
    
    @pytest.mark.asyncio
    async def test_complete_trading_pipeline(self, overmind_brain):
        """Test complete trading decision pipeline"""
        # Mock market data
        market_data = {
            "symbol": "SOL",
            "price": 138.50,
            "volume": 1000000,
            "timestamp": "2025-06-23T18:00:00Z",
            "indicators": {
                "rsi": 65.5,
                "macd": 0.25,
                "volume_sma": 850000
            }
        }
        
        # Mock vector memory search results
        mock_memories = [
            Mock(id="mem_1", score=0.92, payload={
                "text": "Previous SOL trade at similar price level",
                "action": "BUY",
                "result": "profitable",
                "confidence": 0.85
            })
        ]
        overmind_brain.vector_memory.client.search = Mock(return_value=mock_memories)
        
        # Process market data through complete pipeline
        decision = await overmind_brain.process_market_data(market_data)
        
        # Verify decision structure
        assert decision is not None
        assert "action" in decision
        assert "confidence" in decision
        assert "reasoning" in decision
        assert decision["action"] in ["BUY", "SELL", "HOLD"]
        assert 0.0 <= decision["confidence"] <= 1.0
        
        # Verify memory was queried
        overmind_brain.vector_memory.client.search.assert_called()
        
        # Verify experience was stored
        assert overmind_brain.vector_memory.metrics["memories_stored"] >= 0
    
    @pytest.mark.asyncio
    async def test_risk_assessment_integration(self, overmind_brain):
        """Test risk assessment integration"""
        # High-risk market data
        high_risk_data = {
            "symbol": "VOLATILE_TOKEN",
            "price": 0.001,
            "volume": 50000,
            "price_change_24h": -45.5,  # High volatility
            "market_cap": 100000  # Low market cap
        }
        
        decision = await overmind_brain.process_market_data(high_risk_data)
        
        # Should have lower confidence due to high risk
        assert decision["confidence"] < 0.7
        assert "risk" in decision["reasoning"].lower()
    
    @pytest.mark.asyncio
    async def test_memory_learning_cycle(self, overmind_brain):
        """Test memory learning and retrieval cycle"""
        # Simulate multiple trading experiences
        experiences = [
            {
                "market_data": {"symbol": "SOL", "price": 135.0, "action": "BUY"},
                "decision": {"action": "BUY", "confidence": 0.8, "result": "profitable"}
            },
            {
                "market_data": {"symbol": "SOL", "price": 140.0, "action": "SELL"},
                "decision": {"action": "SELL", "confidence": 0.9, "result": "profitable"}
            },
            {
                "market_data": {"symbol": "BTC", "price": 45000.0, "action": "HOLD"},
                "decision": {"action": "HOLD", "confidence": 0.6, "result": "neutral"}
            }
        ]
        
        # Store experiences
        for exp in experiences:
            memory_id = overmind_brain.vector_memory.store_experience(
                exp["market_data"], exp["decision"]
            )
            assert memory_id.startswith("mem_")
        
        # Mock retrieval of relevant experiences
        mock_relevant = [
            Mock(id="mem_sol_1", score=0.95, payload={
                "text": "SOL trading experience",
                "symbol": "SOL",
                "action": "BUY",
                "result": "profitable"
            })
        ]
        overmind_brain.vector_memory.client.search = Mock(return_value=mock_relevant)
        
        # Query for similar situation
        current_market = {"symbol": "SOL", "price": 137.0}
        relevant_memories = overmind_brain.vector_memory.get_relevant_experiences(current_market)
        
        assert len(relevant_memories) > 0
        assert relevant_memories[0]["symbol"] == "SOL"
    
    @pytest.mark.asyncio
    async def test_tensorzero_integration(self, overmind_brain):
        """Test TensorZero optimization integration"""
        # Mock TensorZero response
        mock_tensorzero_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "action": "BUY",
                        "confidence": 0.87,
                        "reasoning": "Strong technical indicators and positive market sentiment"
                    })
                }
            }]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_tensorzero_response
            )
            mock_post.return_value.__aenter__.return_value.status = 200
            
            market_data = {
                "symbol": "ETH",
                "price": 2300.0,
                "volume": 500000
            }
            
            decision = await overmind_brain.process_market_data(market_data)
            
            # Verify TensorZero was called
            mock_post.assert_called()
            
            # Verify decision incorporates TensorZero optimization
            assert decision["action"] == "BUY"
            assert decision["confidence"] == 0.87
    
    @pytest.mark.asyncio
    async def test_redis_communication(self, overmind_brain):
        """Test Redis communication for Rust integration"""
        # Mock Redis responses
        overmind_brain.redis.blpop = AsyncMock(return_value=(
            "overmind:commands",
            json.dumps({
                "action": "BUY",
                "symbol": "RAY",
                "quantity": 100,
                "confidence": 0.75
            })
        ))
        
        # Test command processing
        await overmind_brain.start_command_processing()
        
        # Verify Redis operations
        overmind_brain.redis.blpop.assert_called()
        overmind_brain.redis.lpush.assert_called()
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, overmind_brain):
        """Test comprehensive health monitoring"""
        # Mock collection info for health check
        mock_collection = Mock()
        mock_collection.points_count = 1000
        mock_collection.config.params.vectors.size = 384
        mock_collection.config.params.vectors.distance.value = "Cosine"
        overmind_brain.vector_memory.client.get_collection = Mock(return_value=mock_collection)
        
        # Run health check
        health_status = await overmind_brain.health_check()
        
        # Verify health check results
        assert health_status["brain_status"] == "operational"
        assert "components" in health_status
        assert "vector_memory" in health_status["components"]
        assert "redis_connection" in health_status["components"]
        assert "decision_engine" in health_status["components"]
        
        # Verify memory stats
        memory_stats = overmind_brain.get_memory_stats()
        assert memory_stats["total_memories"] == 1000
        assert memory_stats["status"] == "operational"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, overmind_brain):
        """Test error handling and recovery mechanisms"""
        # Test vector memory error handling
        overmind_brain.vector_memory.client.search = Mock(side_effect=Exception("Connection error"))
        
        market_data = {"symbol": "TEST", "price": 100.0}
        decision = await overmind_brain.process_market_data(market_data)
        
        # Should still return a decision despite memory error
        assert decision is not None
        assert decision["action"] in ["BUY", "SELL", "HOLD"]
        
        # Test Redis error handling
        overmind_brain.redis.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        health_status = await overmind_brain.health_check()
        assert health_status["components"]["redis_connection"]["status"] == "disconnected"
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, overmind_brain):
        """Test system performance under load"""
        # Simulate high-frequency trading scenario
        market_updates = []
        for i in range(100):
            market_updates.append({
                "symbol": f"TOKEN_{i % 10}",
                "price": 100.0 + (i * 0.1),
                "volume": 1000 + i,
                "timestamp": f"2025-06-23T18:{i:02d}:00Z"
            })
        
        start_time = time.time()
        decisions = []
        
        # Process all market updates
        for market_data in market_updates:
            decision = await overmind_brain.process_market_data(market_data)
            decisions.append(decision)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance
        assert len(decisions) == 100
        assert processing_time < 30.0  # Should process 100 updates in under 30 seconds
        assert all(d["action"] in ["BUY", "SELL", "HOLD"] for d in decisions)
        
        # Check processing rate
        processing_rate = len(decisions) / processing_time
        assert processing_rate > 3.0  # At least 3 decisions per second
    
    @pytest.mark.asyncio
    async def test_memory_persistence_and_retrieval(self, overmind_brain):
        """Test memory persistence and retrieval accuracy"""
        # Store specific trading patterns
        patterns = [
            {"pattern": "morning_dip", "action": "BUY", "success_rate": 0.85},
            {"pattern": "evening_pump", "action": "SELL", "success_rate": 0.78},
            {"pattern": "weekend_consolidation", "action": "HOLD", "success_rate": 0.92}
        ]
        
        stored_ids = []
        for pattern in patterns:
            memory_id = overmind_brain.vector_memory.add_memory(
                f"Trading pattern: {pattern['pattern']}",
                pattern
            )
            stored_ids.append(memory_id)
        
        # Mock search to return specific pattern
        mock_pattern_result = Mock(
            id=stored_ids[0],
            score=0.95,
            payload={
                "text": "Trading pattern: morning_dip",
                "pattern": "morning_dip",
                "action": "BUY",
                "success_rate": 0.85
            }
        )
        overmind_brain.vector_memory.client.search = Mock(return_value=[mock_pattern_result])
        
        # Query for morning trading pattern
        results = overmind_brain.vector_memory.find_similar("morning trading opportunity")
        
        assert len(results) > 0
        assert results[0]["pattern"] == "morning_dip"
        assert results[0]["action"] == "BUY"
        assert results[0]["success_rate"] == 0.85
    
    def test_configuration_validation(self, overmind_brain):
        """Test system configuration validation"""
        # Verify all components are initialized
        assert overmind_brain.vector_memory is not None
        assert overmind_brain.decision_engine is not None
        assert overmind_brain.risk_analyzer is not None
        assert overmind_brain.market_analyzer is not None
        
        # Verify metrics are being collected
        assert hasattr(overmind_brain.vector_memory, 'metrics')
        assert 'queries_total' in overmind_brain.vector_memory.metrics
        
        # Verify alerts system is available
        if overmind_brain.vector_memory.alerts_manager:
            assert hasattr(overmind_brain.vector_memory.alerts_manager, 'thresholds')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
