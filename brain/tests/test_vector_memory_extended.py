#!/usr/bin/env python3
"""
Extended VectorMemory Tests for THE OVERMIND PROTOCOL
Comprehensive testing suite for vector memory functionality
"""

import pytest
import asyncio
import time
import random
import string
from unittest.mock import Mock, patch
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from overmind_brain.vector_memory import VectorMemory


class TestVectorMemoryExtended:
    """Extended test suite for VectorMemory"""
    
    @pytest.fixture
    def vector_memory(self):
        """Create VectorMemory instance for testing"""
        with patch('overmind_brain.vector_memory.QdrantClient'):
            with patch('overmind_brain.vector_memory.SentenceTransformer'):
                vm = VectorMemory("test_collection")
                # Mock the embedding model
                vm.embedding_model.encode = Mock(return_value=[0.1] * 384)
                vm.embedding_model.get_sentence_embedding_dimension = Mock(return_value=384)
                return vm
    
    def test_memory_storage_performance(self, vector_memory):
        """Test memory storage performance under load"""
        start_time = time.time()
        
        # Store 100 memories
        for i in range(100):
            text = f"Test memory {i}: " + ''.join(random.choices(string.ascii_letters, k=100))
            metadata = {
                "test_id": i,
                "category": f"category_{i % 10}",
                "priority": random.randint(1, 5)
            }
            vector_memory.add_memory(text, metadata)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should store 100 memories in less than 10 seconds
        assert duration < 10.0, f"Storage took too long: {duration:.2f}s"
        assert vector_memory.metrics['memories_stored'] == 100
    
    def test_query_performance(self, vector_memory):
        """Test query performance and accuracy"""
        # Mock search results
        mock_results = [
            Mock(id="mem_1", score=0.95, payload={"text": "Test memory 1", "category": "test"}),
            Mock(id="mem_2", score=0.87, payload={"text": "Test memory 2", "category": "test"}),
            Mock(id="mem_3", score=0.82, payload={"text": "Test memory 3", "category": "test"})
        ]
        vector_memory.client.search = Mock(return_value=mock_results)
        
        start_time = time.time()
        
        # Perform 50 queries
        for i in range(50):
            query = f"Test query {i}"
            results = vector_memory.find_similar(query, limit=5)
            assert len(results) == 3  # Mock returns 3 results
            assert all(r['similarity'] > 0.8 for r in results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 50 queries in less than 5 seconds
        assert duration < 5.0, f"Queries took too long: {duration:.2f}s"
        assert vector_memory.metrics['queries_total'] == 50
        assert vector_memory.metrics['queries_success'] == 50
        assert vector_memory.metrics['avg_query_time'] > 0
    
    def test_memory_similarity_accuracy(self, vector_memory):
        """Test similarity search accuracy"""
        # Mock search with different similarity scores
        mock_results = [
            Mock(id="mem_high", score=0.95, payload={"text": "Very similar text", "type": "high"}),
            Mock(id="mem_med", score=0.75, payload={"text": "Somewhat similar text", "type": "medium"}),
            Mock(id="mem_low", score=0.55, payload={"text": "Less similar text", "type": "low"})
        ]
        vector_memory.client.search = Mock(return_value=mock_results)
        
        results = vector_memory.find_similar("Test query", limit=3)
        
        # Results should be ordered by similarity (highest first)
        assert results[0]['similarity'] > results[1]['similarity']
        assert results[1]['similarity'] > results[2]['similarity']
        
        # High similarity results should be above threshold
        high_sim_results = [r for r in results if r['similarity'] > 0.9]
        assert len(high_sim_results) >= 1
    
    def test_trading_experience_storage(self, vector_memory):
        """Test trading experience storage and retrieval"""
        market_data = {
            "symbol": "SOL",
            "price": 138.50,
            "volume": 1000000,
            "timestamp": "2025-06-23T18:00:00Z"
        }
        
        decision = {
            "action": "BUY",
            "confidence": 0.85,
            "reasoning": "Strong upward momentum with high volume",
            "result": "profitable"
        }
        
        # Store experience
        memory_id = vector_memory.store_experience(market_data, decision)
        assert memory_id.startswith("mem_")
        
        # Mock retrieval
        mock_experience = Mock(
            id=memory_id,
            score=0.92,
            payload={
                "text": "Market situation with SOL trading",
                "type": "trading_experience",
                "symbol": "SOL",
                "action": "BUY",
                "result": "profitable"
            }
        )
        vector_memory.client.search = Mock(return_value=[mock_experience])
        
        # Retrieve similar experiences
        similar_experiences = vector_memory.get_relevant_experiences(market_data, limit=1)
        assert len(similar_experiences) == 1
        assert similar_experiences[0]['symbol'] == "SOL"
        assert similar_experiences[0]['action'] == "BUY"
    
    def test_metrics_collection(self, vector_memory):
        """Test metrics collection and reporting"""
        # Mock collection info
        mock_collection = Mock()
        mock_collection.points_count = 1000
        mock_collection.config.params.vectors.size = 384
        mock_collection.config.params.vectors.distance.value = "Cosine"
        vector_memory.client.get_collection = Mock(return_value=mock_collection)
        
        # Perform some operations to generate metrics
        vector_memory.metrics['queries_total'] = 100
        vector_memory.metrics['queries_success'] = 95
        vector_memory.metrics['queries_failed'] = 5
        vector_memory.metrics['memories_stored'] = 50
        
        metrics = vector_memory.get_metrics()
        
        assert metrics['queries_total'] == 100
        assert metrics['queries_success'] == 95
        assert metrics['queries_failed'] == 5
        assert metrics['total_points'] == 1000
        assert metrics['vector_size'] == 384
        assert metrics['status'] == 'operational'
    
    def test_error_handling(self, vector_memory):
        """Test error handling in various scenarios"""
        # Test search error handling
        vector_memory.client.search = Mock(side_effect=Exception("Connection error"))
        
        results = vector_memory.find_similar("test query")
        assert results == []
        assert vector_memory.metrics['queries_failed'] > 0
        
        # Test metrics error handling
        vector_memory.client.get_collection = Mock(side_effect=Exception("Collection error"))
        
        metrics = vector_memory.get_metrics()
        assert metrics['status'] == 'error'
        assert 'error' in metrics
    
    def test_concurrent_operations(self, vector_memory):
        """Test concurrent memory operations"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def worker(worker_id):
            try:
                # Each worker performs multiple operations
                for i in range(10):
                    # Add memory
                    text = f"Worker {worker_id} memory {i}"
                    memory_id = vector_memory.add_memory(text, {"worker": worker_id})
                    
                    # Query memory
                    vector_memory.client.search = Mock(return_value=[])
                    results = vector_memory.find_similar(f"query {i}")
                    
                results_queue.put(("success", worker_id))
            except Exception as e:
                results_queue.put(("error", worker_id, str(e)))
        
        # Start 5 concurrent workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results_queue.empty():
            result = results_queue.get()
            if result[0] == "success":
                success_count += 1
        
        assert success_count == 5, "All workers should complete successfully"
    
    def test_memory_cleanup(self, vector_memory):
        """Test memory cleanup functionality"""
        # This would test automatic cleanup of old memories
        # For now, we'll test the metrics reset functionality
        
        # Set some metrics
        vector_memory.metrics['queries_total'] = 100
        vector_memory.metrics['memories_stored'] = 50
        vector_memory.query_times = [0.1, 0.2, 0.3]
        
        # Reset metrics
        vector_memory.reset_metrics()
        
        assert vector_memory.metrics['queries_total'] == 0
        assert vector_memory.metrics['memories_stored'] == 0
        assert len(vector_memory.query_times) == 0
    
    def test_large_scale_operations(self, vector_memory):
        """Test large-scale memory operations"""
        # Mock for large-scale testing
        vector_memory.client.upsert = Mock()
        vector_memory.client.search = Mock(return_value=[])
        
        # Test storing 1000 memories
        start_time = time.time()
        for i in range(1000):
            text = f"Large scale memory {i}: " + "x" * 500  # 500 char text
            vector_memory.add_memory(text, {"batch": "large_scale", "index": i})
        
        duration = time.time() - start_time
        
        # Should handle 1000 memories efficiently
        assert duration < 30.0, f"Large scale storage took too long: {duration:.2f}s"
        
        # Test querying with large result sets
        mock_large_results = [
            Mock(id=f"mem_{i}", score=0.8 + (i * 0.01), 
                 payload={"text": f"Result {i}", "index": i})
            for i in range(100)
        ]
        vector_memory.client.search = Mock(return_value=mock_large_results)
        
        results = vector_memory.find_similar("large query", limit=100)
        assert len(results) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
