"""
ChromaDB Vector Memory implementation for THE OVERMIND PROTOCOL
Provides long-term memory capabilities using ChromaDB vector database
"""

import os
import logging
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaVectorMemory:
    """ChromaDB-based vector database memory for THE OVERMIND PROTOCOL"""
    
    def __init__(self, collection_name: str = "overmind_memory"):
        """Initialize vector memory with ChromaDB connection"""
        self.collection_name = collection_name
        
        # Connect to ChromaDB
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8001"))
        
        self.client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(allow_reset=True)
        )
        
        # Monitoring metrics
        self.metrics = {
            'queries_total': 0,
            'queries_success': 0,
            'queries_failed': 0,
            'avg_query_time': 0.0,
            'memories_stored': 0,
            'memories_retrieved': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Query time tracking
        self.query_times = []
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"ChromaVectorMemory initialized with collection: {self.collection_name}")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
            return collection
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "THE OVERMIND PROTOCOL Vector Memory"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
            return collection
    
    def add_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add new memory to vector database
        
        Args:
            text: Text content to store
            metadata: Additional metadata about the memory
            
        Returns:
            ID of the stored memory
        """
        if metadata is None:
            metadata = {}
        
        # Add timestamp if not provided
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
        
        # Generate ID based on timestamp and content
        memory_id = f"mem_{int(datetime.now().timestamp())}_{hash(text) % 10000}"
        
        try:
            # Store in ChromaDB
            self.collection.add(
                ids=[memory_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            # Update metrics
            self.metrics['memories_stored'] += 1
            
            logger.debug(f"Added memory with ID: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise
    
    def find_similar(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find memories similar to the query text
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of similar memories with their metadata
        """
        start_time = time.time()
        self.metrics['queries_total'] += 1

        try:
            # Search in ChromaDB
            search_result = self.collection.query(
                query_texts=[query_text],
                n_results=limit
            )

            # Format results
            memories = []
            if search_result and search_result.get('ids') and search_result['ids'][0]:
                for i, memory_id in enumerate(search_result['ids'][0]):
                    memory_data = {
                        "id": memory_id,
                        "text": "",
                        "similarity": 0.0
                    }
                    
                    # Add document text if available
                    if (search_result.get('documents') and 
                        search_result['documents'][0] and 
                        i < len(search_result['documents'][0])):
                        memory_data["text"] = search_result['documents'][0][i]
                    
                    # Add similarity score if available
                    if (search_result.get('distances') and 
                        search_result['distances'][0] and 
                        i < len(search_result['distances'][0])):
                        # Convert distance to similarity (assuming cosine distance)
                        memory_data["similarity"] = 1.0 - search_result['distances'][0][i]
                    
                    # Add metadata if available
                    if (search_result.get('metadatas') and 
                        search_result['metadatas'][0] and 
                        i < len(search_result['metadatas'][0]) and
                        search_result['metadatas'][0][i]):
                        memory_data.update(search_result['metadatas'][0][i])
                    
                    memories.append(memory_data)

            # Update metrics
            query_time = time.time() - start_time
            self.query_times.append(query_time)
            self.metrics['queries_success'] += 1
            self.metrics['memories_retrieved'] += len(memories)
            if self.query_times:
                self.metrics['avg_query_time'] = sum(self.query_times) / len(self.query_times)

            logger.info(f"Found {len(memories)} similar memories for query in {query_time:.3f}s")
            return memories

        except Exception as e:
            self.metrics['queries_failed'] += 1
            logger.error(f"Error finding similar memories: {e}")
            return []
    
    def store_experience(self, market_data: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """
        Store a trading experience (market data + decision) in memory
        
        Args:
            market_data: Market data that led to the decision
            decision: The trading decision made
            
        Returns:
            ID of the stored experience
        """
        # Create a comprehensive text representation
        experience_text = f"""
        Market Situation: {json.dumps(market_data, default=str)}
        Decision Made: {json.dumps(decision, default=str)}
        """
        
        # Combine metadata
        metadata = {
            "type": "trading_experience",
            "timestamp": datetime.now().isoformat(),
            **{f"market_{k}": v for k, v in market_data.items()},
            **{f"decision_{k}": v for k, v in decision.items()}
        }
        
        return self.add_memory(experience_text, metadata)
    
    def get_relevant_experiences(self, current_market_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant past experiences based on current market data
        
        Args:
            current_market_data: Current market situation
            limit: Maximum number of experiences to return
            
        Returns:
            List of relevant past experiences
        """
        # Create query text from market data
        query_text = f"Market situation: {json.dumps(current_market_data, default=str)}"
        
        # Find similar experiences
        similar_memories = self.find_similar(query_text, limit)
        
        # Filter for trading experiences only
        experiences = [
            memory for memory in similar_memories 
            if memory.get("type") == "trading_experience"
        ]
        
        return experiences
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            # Get collection info
            collection_count = self.collection.count()
            
            return {
                **self.metrics,
                'collection_name': self.collection_name,
                'total_memories': collection_count,
                'status': 'operational'
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {
                **self.metrics,
                'collection_name': self.collection_name,
                'total_memories': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics = {
            'queries_total': 0,
            'queries_success': 0,
            'queries_failed': 0,
            'avg_query_time': 0.0,
            'memories_stored': 0,
            'memories_retrieved': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.query_times = []
        logger.info("Metrics reset")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test basic functionality
            test_id = self.add_memory("Health check test", {"test": True})
            results = self.find_similar("Health check", limit=1)
            
            return {
                "status": "healthy",
                "collection_name": self.collection_name,
                "test_successful": len(results) > 0,
                "metrics": self.get_metrics()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "collection_name": self.collection_name
            }
