import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from src.overmind_brain.brain import OVERMINDBrain
from src.overmind_brain.models import TradingDecision, MarketEvent

@pytest.fixture
async def brain():
    """Create a test brain instance with mocked dependencies"""
    with patch("src.overmind_brain.brain.redis.Redis") as mock_redis:
        # Configure mock
        mock_redis.return_value.lpush = AsyncMock()
        mock_redis.return_value.blpop = AsyncMock()
        
        brain = OVERMINDBrain()
        yield brain

@pytest.mark.asyncio
async def test_process_market_event(brain):
    """Test that market events are processed correctly"""
    # Arrange
    test_event = MarketEvent(
        event_id="test-123",
        symbol="SOL/USDC",
        price=100.0,
        volume=1000000,
        timestamp=datetime.now(timezone.utc),
        event_type="PRICE_UPDATE",
        metadata={
            "trend": "bullish",
            "volatility": 0.02
        }
    )
    
    # Act
    decision = await brain.process_market_event(test_event)
    
    # Assert
    assert decision is not None
    assert decision.symbol == "SOL/USDC"
    assert decision.action in ["BUY", "SELL", "HOLD"]
    assert 0.0 <= decision.confidence <= 1.0