"""
Vector Memory implementation for THE OVERMIND PROTOCOL
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
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Import alerts system
try:
    from .vector_memory_alerts import VectorMemoryAlertsManager, AlertSeverity
except ImportError:
    # Fallback if alerts system is not available
    VectorMemoryAlertsManager = None
    AlertSeverity = None

class VectorMemory:
    """Vector database memory for THE OVERMIND PROTOCOL"""

    def __init__(self, collection_name: str = "overmind_memory"):
        """Initialize vector memory with ChromaDB connection"""
        self.collection_name = collection_name

        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

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
        self.query_times = []

        # Initialize alerts system
        if VectorMemoryAlertsManager:
            self.alerts_manager = VectorMemoryAlertsManager(self)
        else:
            self.alerts_manager = None

        # Get or create collection
        self.collection = self._get_or_create_collection()

        logger.info(f"VectorMemory initialized with collection: {self.collection_name}")

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

        # Store in ChromaDB
        self.collection.add(
            ids=[memory_id],
            documents=[text],
            metadatas=[metadata]
        )

        # Update metrics
        self.metrics['memories_stored'] += 1

        logger.info(f"Added memory with ID: {memory_id}")
        return memory_id
    
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
            if (search_result.get('ids') and search_result['ids'] and
                search_result['ids'][0] and search_result.get('documents')):

                for i, memory_id in enumerate(search_result['ids'][0]):
                    memory_data = {
                        "id": memory_id,
                        "text": search_result['documents'][0][i] if search_result['documents'][0] else "",
                        "similarity": 1.0 - search_result['distances'][0][i] if search_result.get('distances') else 0.0
                    }

                    # Add metadata if available
                    if search_result.get('metadatas') and search_result['metadatas'][0]:
                        metadata = search_result['metadatas'][0][i] or {}
                        memory_data.update(metadata)

                    memories.append(memory_data)

            # Update metrics
            query_time = time.time() - start_time
            self.query_times.append(query_time)
            self.metrics['queries_success'] += 1
            self.metrics['memories_retrieved'] += len(memories)
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
            ID of the stored memory
        """
        # Create a structured text representation
        experience_text = f"""
        Market Situation:
        Symbol: {market_data.get('symbol', 'unknown')}
        Price: {market_data.get('price', 0)}
        Volume: {market_data.get('volume', 0)}
        Timestamp: {market_data.get('timestamp', 'unknown')}
        
        Decision:
        Action: {decision.get('action', 'unknown')}
        Confidence: {decision.get('confidence', 0)}
        Reasoning: {decision.get('reasoning', 'unknown')}
        """
        
        # Store with metadata
        metadata = {
            "type": "trading_experience",
            "symbol": market_data.get('symbol', 'unknown'),
            "action": decision.get('action', 'unknown'),
            "result": decision.get('result', 'unknown'),
            "timestamp": datetime.now().isoformat()
        }
        
        return self.add_memory(experience_text, metadata)
    
    def get_relevant_experiences(self, market_data: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get relevant past experiences for current market situation
        
        Args:
            market_data: Current market data
            limit: Maximum number of experiences to return
            
        Returns:
            List of relevant past experiences
        """
        # Create a query text from market data
        query_text = f"""
        Symbol: {market_data.get('symbol', 'unknown')}
        Price: {market_data.get('price', 0)}
        Volume: {market_data.get('volume', 0)}
        """
        
        return self.find_similar(query_text, limit)

    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics for VectorMemory"""
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)

            return {
                **self.metrics,
                'collection_name': self.collection_name,
                'total_points': collection_info.points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance_metric': collection_info.config.params.vectors.distance.value,
                'status': 'operational'
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {
                **self.metrics,
                'status': 'error',
                'error': str(e)
            }

    def reset_metrics(self):
        """Reset monitoring metrics"""
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
        logger.info("VectorMemory metrics reset")

    def search_by_metadata(self, filters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories by metadata filters"""
        try:
            # Convert filters to Qdrant filter format
            filter_conditions = []
            for key, value in filters.items():
                filter_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )

            # Search with filters
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=filter_conditions
                ),
                limit=limit
            )

            # Format results
            memories = []
            for result in search_result[0]:  # scroll returns (points, next_page_offset)
                memory = {
                    "id": result.id,
                    "text": result.payload.get("text", ""),
                    **{k: v for k, v in result.payload.items() if k != "text"}
                }
                memories.append(memory)

            logger.info(f"Found {len(memories)} memories matching filters")
            return memories

        except Exception as e:
            logger.error(f"Error searching by metadata: {e}")
            return []

    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific memory by ID"""
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[memory_id]
            )

            if result:
                point = result[0]
                return {
                    "id": point.id,
                    "text": point.payload.get("text", ""),
                    **{k: v for k, v in point.payload.items() if k != "text"}
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving memory {memory_id}: {e}")
            return None

    def update_memory(self, memory_id: str, text: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update existing memory"""
        try:
            # Get existing memory
            existing = self.get_memory_by_id(memory_id)
            if not existing:
                logger.warning(f"Memory {memory_id} not found for update")
                return False

            # Prepare updated data
            updated_text = text if text is not None else existing["text"]
            updated_metadata = {**existing, **(metadata or {})}
            updated_metadata.pop("text", None)  # Remove text from metadata
            updated_metadata["updated_at"] = datetime.now().isoformat()

            # Generate new embedding if text changed
            if text is not None:
                embedding = self.embedding_model.encode(updated_text).tolist()
            else:
                # Keep existing embedding (we'd need to store it separately in real implementation)
                embedding = self.embedding_model.encode(updated_text).tolist()

            # Update in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=memory_id,
                        vector=embedding,
                        payload={
                            "text": updated_text,
                            **updated_metadata
                        }
                    )
                ]
            )

            logger.info(f"Updated memory {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating memory {memory_id}: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory by ID"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[memory_id]
                )
            )

            logger.info(f"Deleted memory {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            return False

    def cleanup_old_memories(self, days_old: int = 30) -> int:
        """Clean up memories older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()

            # Find old memories
            old_memories = self.search_by_metadata({
                "timestamp": {"$lt": cutoff_date}
            }, limit=1000)  # Process in batches

            deleted_count = 0
            for memory in old_memories:
                if self.delete_memory(memory["id"]):
                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old memories")
            return deleted_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
