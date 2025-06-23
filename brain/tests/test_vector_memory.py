"""
Unit tests for Vector Memory component
"""

import os
import pytest
from dotenv import load_dotenv
from overmind_brain.vector_memory import VectorMemory

# Load environment variables
load_dotenv()

@pytest.fixture
def vector_memory():
    """Create a test vector memory instance"""
    # Use a test-specific collection to avoid polluting main data
    return VectorMemory(collection_name="test_overmind_memory")

def test_add_and_retrieve_memory(vector_memory):
    """Test adding and retrieving memories"""
    # Test data
    test_text = "SOL price increased by 5% after Solana network upgrade"
    test_metadata = {
        "symbol": "SOL",
        "event_type": "price_change",
        "change_percent": 5.0
    }
    
    # Add memory
    memory_id = vector_memory.add_memory(test_text, test_metadata)
    
    # Verify memory was added
    assert memory_id is not None
    assert isinstance(memory_id, str)
    
    # Retrieve similar memories
    similar_memories = vector_memory.find_similar("SOL price increase", limit=1)
    
    # Verify retrieval
    assert len(similar_memories) == 1
    assert similar_memories[0]["text"] == test_text
    assert similar_memories[0]["symbol"] == "SOL"
    assert similar_memories[0]["event_type"] == "price_change"
    assert similar_memories[0]["similarity"] > 0.7  # Should be highly similar

def test_store_and_retrieve_experience(vector_memory):
    """Test storing and retrieving trading experiences"""
    # Test market data
    market_data = {
        "symbol": "SOL/USDC",
        "price": 150.25,
        "volume": 1250000,
        "timestamp": "2023-06-15T14:30:00Z"
    }
    
    # Test decision
    decision = {
        "action": "BUY",
        "confidence": 0.85,
        "reasoning": "Technical indicators show strong upward momentum",
        "result": "PROFIT"
    }
    
    # Store experience
    memory_id = vector_memory.store_experience(market_data, decision)
    
    # Verify experience was stored
    assert memory_id is not None
    
    # Retrieve relevant experiences
    similar_market_data = {
        "symbol": "SOL/USDC",
        "price": 152.50,
        "volume": 1300000
    }
    
    relevant_experiences = vector_memory.get_relevant_experiences(similar_market_data, limit=1)
    
    # Verify retrieval
    assert len(relevant_experiences) == 1
    assert "SOL/USDC" in relevant_experiences[0]["text"]
    assert relevant_experiences[0]["symbol"] == "SOL/USDC"
    assert relevant_experiences[0]["action"] == "BUY"