"""THE OVERMIND PROTOCOL - Vector Memory Module
Long-term AI memory using Chroma vector database for experience storage and retrieval.
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorMemory:
    """Vector database memory for THE OVERMIND PROTOCOL AI Brain"""
    
    def __init__(self, 
                 collection_name: str = "overmind_memory",
                 persist_directory: str = "./chroma_db",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize vector memory with Chroma database
        
        Args:
            collection_name: Name of the Chroma collection
            persist_directory: Directory to persist the database
            embedding_model: Sentence transformer model for embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model_name = embedding_model
        
        # Initialize Chroma client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"🧠 Loaded existing memory collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "THE OVERMIND PROTOCOL AI Memory"}
            )
            logger.info(f"🧠 Created new memory collection: {collection_name}")
    
    async def store_experience(self, 
                             situation: Dict[str, Any], 
                             decision: Dict[str, Any], 
                             context: Optional[Dict[str, Any]] = None,
                             outcome: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a trading experience in vector memory
        
        Args:
            situation: Market situation data
            decision: AI decision made
            context: Additional context
            outcome: Result of the decision (if available)
            
        Returns:
            Memory ID for the stored experience
        """
        try:
            # Create unique memory ID
            memory_id = str(uuid.uuid4())
            
            # Create experience document
            experience = {
                "id": memory_id,
                "timestamp": datetime.utcnow().isoformat(),
                "situation": situation,
                "decision": decision,
                "context": context or {},
                "outcome": outcome or {},
                "type": "trading_experience"
            }
            
            # Create text representation for embedding
            text_content = self._create_text_representation(experience)
            
            # Generate embedding
            embedding = self.embedding_model.encode(text_content).tolist()
            
            # Store in Chroma
            self.collection.add(
                documents=[text_content],
                embeddings=[embedding],
                metadatas=[{
                    "memory_id": memory_id,
                    "timestamp": experience["timestamp"],
                    "symbol": situation.get("symbol", "unknown"),
                    "action": decision.get("action", "unknown"),
                    "confidence": decision.get("confidence", 0.0),
                    "type": "trading_experience"
                }],
                ids=[memory_id]
            )
            
            logger.info(f"🧠 Stored experience: {memory_id} - {decision.get('action')} {situation.get('symbol')}")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to store experience: {e}")
            raise
    
    async def similarity_search(self, 
                               query: str, 
                               top_k: int = 5,
                               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar experiences using vector similarity
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of similar experiences
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                where_clause.update(filters)
            
            # Search in Chroma
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            experiences = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    experience = {
                        "content": doc,
                        "metadata": results["metadatas"][0][i],
                        "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                        "memory_id": results["metadatas"][0][i]["memory_id"]
                    }
                    experiences.append(experience)
            
            logger.info(f"🔍 Found {len(experiences)} similar experiences for query: {query[:50]}...")
            return experiences
            
        except Exception as e:
            logger.error(f"❌ Failed to search experiences: {e}")
            return []
    
    async def get_recent_experiences(self, 
                                   limit: int = 10,
                                   symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent trading experiences
        
        Args:
            limit: Maximum number of experiences to return
            symbol: Optional symbol filter
            
        Returns:
            List of recent experiences
        """
        try:
            where_clause = {"type": "trading_experience"}
            if symbol:
                where_clause["symbol"] = symbol
            
            # Get recent experiences
            results = self.collection.get(
                where=where_clause,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            # Sort by timestamp (most recent first)
            experiences = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    experience = {
                        "content": doc,
                        "metadata": results["metadatas"][i],
                        "memory_id": results["metadatas"][i]["memory_id"]
                    }
                    experiences.append(experience)
                
                # Sort by timestamp
                experiences.sort(
                    key=lambda x: x["metadata"]["timestamp"], 
                    reverse=True
                )
            
            logger.info(f"📚 Retrieved {len(experiences)} recent experiences")
            return experiences[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent experiences: {e}")
            return []
    
    async def update_experience_outcome(self, 
                                      memory_id: str, 
                                      outcome: Dict[str, Any]) -> bool:
        """
        Update an experience with outcome data
        
        Args:
            memory_id: ID of the memory to update
            outcome: Outcome data to add
            
        Returns:
            Success status
        """
        try:
            # Get existing experience
            result = self.collection.get(
                ids=[memory_id],
                include=["documents", "metadatas"]
            )
            
            if not result["documents"]:
                logger.warning(f"⚠️ Memory not found: {memory_id}")
                return False
            
            # Update metadata with outcome
            metadata = result["metadatas"][0]
            metadata["outcome_updated"] = datetime.utcnow().isoformat()
            metadata["has_outcome"] = True
            
            # Update the document
            self.collection.update(
                ids=[memory_id],
                metadatas=[metadata]
            )
            
            logger.info(f"✅ Updated experience outcome: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update experience outcome: {e}")
            return False
    
    def _create_text_representation(self, experience: Dict[str, Any]) -> str:
        """
        Create text representation of experience for embedding
        
        Args:
            experience: Experience data
            
        Returns:
            Text representation
        """
        situation = experience.get("situation", {})
        decision = experience.get("decision", {})
        context = experience.get("context", {})
        
        text_parts = [
            f"Symbol: {situation.get('symbol', 'unknown')}",
            f"Price: {situation.get('price', 'unknown')}",
            f"Action: {decision.get('action', 'unknown')}",
            f"Confidence: {decision.get('confidence', 0.0)}",
            f"Reasoning: {decision.get('reasoning', 'none')}"
        ]
        
        # Add context information
        if context:
            for key, value in context.items():
                if isinstance(value, (str, int, float)):
                    text_parts.append(f"{key}: {value}")
        
        return " | ".join(text_parts)
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory collection
        
        Returns:
            Memory statistics
        """
        try:
            # Get collection info
            collection_count = self.collection.count()
            
            # Get recent activity
            recent_experiences = await self.get_recent_experiences(limit=5)
            
            stats = {
                "total_experiences": collection_count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model_name,
                "recent_activity": len(recent_experiences),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            logger.info(f"📊 Memory stats: {collection_count} total experiences")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    async def clear_memory(self, confirm: bool = False) -> bool:
        """
        Clear all memory (use with caution!)
        
        Args:
            confirm: Must be True to actually clear
            
        Returns:
            Success status
        """
        if not confirm:
            logger.warning("⚠️ Memory clear not confirmed")
            return False
        
        try:
            # Delete and recreate collection
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "THE OVERMIND PROTOCOL AI Memory"}
            )
            
            logger.warning("🗑️ Memory cleared!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear memory: {e}")
            return False
