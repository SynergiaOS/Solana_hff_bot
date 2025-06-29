"""THE OVERMIND PROTOCOL - Enhanced Memory System
Human-inspired multi-tier memory architecture with advanced RAG capabilities.
Based on NVIDIA Enterprise Data Flywheel and human memory research.
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import numpy as np

# Vector and embedding imports
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False

# MongoDB integration for advanced RAG
try:
    from pymongo import MongoClient
    from pymongo.collection import Collection
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    """Base memory item structure"""
    id: str
    content: str
    memory_type: str
    timestamp: datetime
    metadata: Dict[str, Any]
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed: Optional[datetime] = None

@dataclass
class TradingEpisode:
    """Episodic memory for trading experiences"""
    episode_id: str
    market_context: Dict[str, Any]
    decision_made: Dict[str, Any]
    outcome: Dict[str, Any]
    lessons_learned: List[str]
    timestamp: datetime
    success_score: float

class SensoryMemory:
    """Immediate perception processing - very short-term buffer"""
    
    def __init__(self, buffer_size: int = 100, retention_seconds: float = 2.0):
        self.buffer = deque(maxlen=buffer_size)
        self.retention_seconds = retention_seconds
        
    def add_perception(self, data: Dict[str, Any]) -> None:
        """Add new sensory input"""
        perception = {
            'data': data,
            'timestamp': datetime.now(),
            'processed': False
        }
        self.buffer.append(perception)
        
    def get_recent_perceptions(self, max_age_seconds: float = None) -> List[Dict]:
        """Get recent unprocessed perceptions"""
        if max_age_seconds is None:
            max_age_seconds = self.retention_seconds
            
        cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
        recent = [p for p in self.buffer 
                 if p['timestamp'] > cutoff_time and not p['processed']]
        
        # Mark as processed
        for p in recent:
            p['processed'] = True
            
        return recent

class WorkingMemory:
    """Active processing space - current context and attention"""
    
    def __init__(self, capacity: int = 7):  # Miller's magic number
        self.capacity = capacity
        self.active_items = {}
        self.attention_focus = None
        self.context_stack = deque(maxlen=10)
        
    def add_to_working_memory(self, key: str, item: Any, importance: float = 0.5) -> bool:
        """Add item to working memory with capacity management"""
        if len(self.active_items) >= self.capacity:
            # Remove least important item
            least_important = min(self.active_items.items(), 
                                key=lambda x: x[1].get('importance', 0))
            del self.active_items[least_important[0]]
            
        self.active_items[key] = {
            'item': item,
            'importance': importance,
            'added_at': datetime.now(),
            'access_count': 0
        }
        return True
        
    def get_current_context(self) -> Dict[str, Any]:
        """Get current working memory context"""
        return {
            'active_items': self.active_items,
            'attention_focus': self.attention_focus,
            'context_stack': list(self.context_stack)
        }
        
    def set_attention_focus(self, focus: str) -> None:
        """Set current attention focus"""
        if self.attention_focus:
            self.context_stack.append(self.attention_focus)
        self.attention_focus = focus

class SemanticMemory:
    """General knowledge and concepts - trading rules, patterns, etc."""
    
    def __init__(self):
        self.knowledge_base = {}
        self.concept_relationships = defaultdict(list)
        self.trading_rules = {}
        self.market_patterns = {}
        
    def add_concept(self, concept: str, definition: str, 
                   related_concepts: List[str] = None) -> None:
        """Add a new concept to semantic memory"""
        self.knowledge_base[concept] = {
            'definition': definition,
            'added_at': datetime.now(),
            'access_count': 0,
            'related_concepts': related_concepts or []
        }
        
        # Update relationships
        if related_concepts:
            for related in related_concepts:
                self.concept_relationships[concept].append(related)
                self.concept_relationships[related].append(concept)
                
    def add_trading_rule(self, rule_name: str, rule_logic: str, 
                        conditions: List[str], confidence: float) -> None:
        """Add trading rule to semantic memory"""
        self.trading_rules[rule_name] = {
            'logic': rule_logic,
            'conditions': conditions,
            'confidence': confidence,
            'success_rate': 0.0,
            'usage_count': 0,
            'added_at': datetime.now()
        }
        
    def get_related_concepts(self, concept: str, max_depth: int = 2) -> List[str]:
        """Get concepts related to given concept"""
        related = set()
        to_explore = [(concept, 0)]
        explored = set()
        
        while to_explore:
            current, depth = to_explore.pop(0)
            if current in explored or depth >= max_depth:
                continue
                
            explored.add(current)
            for rel in self.concept_relationships.get(current, []):
                if rel not in explored:
                    related.add(rel)
                    to_explore.append((rel, depth + 1))
                    
        return list(related)

class EpisodicMemory:
    """Specific trading experiences and episodes"""
    
    def __init__(self, max_episodes: int = 10000):
        self.episodes = {}
        self.max_episodes = max_episodes
        self.episode_index = {}  # For fast retrieval
        
    def add_episode(self, episode: TradingEpisode) -> None:
        """Add new trading episode"""
        self.episodes[episode.episode_id] = episode
        
        # Update index for fast retrieval
        market_type = episode.market_context.get('market_type', 'unknown')
        if market_type not in self.episode_index:
            self.episode_index[market_type] = []
        self.episode_index[market_type].append(episode.episode_id)
        
        # Manage capacity
        if len(self.episodes) > self.max_episodes:
            self._cleanup_old_episodes()
            
    def get_similar_episodes(self, market_context: Dict[str, Any], 
                           limit: int = 5) -> List[TradingEpisode]:
        """Get episodes similar to current market context"""
        market_type = market_context.get('market_type', 'unknown')
        similar_episodes = []
        
        if market_type in self.episode_index:
            episode_ids = self.episode_index[market_type][-limit:]  # Most recent
            similar_episodes = [self.episodes[eid] for eid in episode_ids 
                              if eid in self.episodes]
                              
        return similar_episodes
        
    def _cleanup_old_episodes(self) -> None:
        """Remove oldest episodes to maintain capacity"""
        # Keep episodes with high success scores
        episodes_by_score = sorted(self.episodes.items(), 
                                 key=lambda x: x[1].success_score, reverse=True)
        
        # Keep top 80% by score
        keep_count = int(self.max_episodes * 0.8)
        episodes_to_keep = dict(episodes_by_score[:keep_count])
        
        # Update episodes and index
        self.episodes = episodes_to_keep
        self._rebuild_index()
        
    def _rebuild_index(self) -> None:
        """Rebuild episode index after cleanup"""
        self.episode_index = {}
        for episode in self.episodes.values():
            market_type = episode.market_context.get('market_type', 'unknown')
            if market_type not in self.episode_index:
                self.episode_index[market_type] = []
            self.episode_index[market_type].append(episode.episode_id)

class AdvancedRAGSystem:
    """Advanced RAG system with MongoDB + Voyage AI integration"""
    
    def __init__(self, mongodb_uri: str = None, collection_name: str = "overmind_rag"):
        self.mongodb_uri = mongodb_uri or "mongodb://localhost:27017"
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_model = None
        
        if MONGODB_AVAILABLE:
            self._initialize_mongodb()
        if VECTOR_AVAILABLE:
            self._initialize_embeddings()
            
    def _initialize_mongodb(self) -> None:
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(self.mongodb_uri)
            db = self.client.overmind_db
            self.collection = db[self.collection_name]
            
            # Create vector search index if needed
            self._ensure_vector_index()
            logger.info("✅ MongoDB connection established")
            
        except Exception as e:
            logger.error(f"❌ MongoDB initialization failed: {e}")
            
    def _initialize_embeddings(self) -> None:
        """Initialize embedding model"""
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"❌ Embedding model initialization failed: {e}")
            
    def _ensure_vector_index(self) -> None:
        """Ensure vector search index exists"""
        try:
            # Create vector search index for MongoDB Atlas
            # This would be configured in MongoDB Atlas UI or via API
            pass
        except Exception as e:
            logger.warning(f"Vector index setup: {e}")
            
    async def store_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Store document with vector embedding"""
        if not self.collection or not self.embedding_model:
            return None
            
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(content).tolist()
            
            # Create document
            doc = {
                'content': content,
                'metadata': metadata,
                'embedding': embedding,
                'timestamp': datetime.now(),
                'access_count': 0
            }
            
            # Store in MongoDB
            result = self.collection.insert_one(doc)
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Document storage failed: {e}")
            return None
            
    async def vector_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        if not self.collection or not self.embedding_model:
            return []
            
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Perform vector search (simplified - would use MongoDB Atlas Vector Search)
            # For now, using basic similarity calculation
            documents = list(self.collection.find({}))
            
            # Calculate similarities
            similarities = []
            for doc in documents:
                if 'embedding' in doc:
                    similarity = self._cosine_similarity(query_embedding, doc['embedding'])
                    similarities.append((similarity, doc))
                    
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            results = [doc for _, doc in similarities[:limit]]
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
            
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        except:
            return 0.0

class EnhancedMemorySystem:
    """Complete enhanced memory system for THE OVERMIND PROTOCOL"""
    
    def __init__(self, mongodb_uri: str = None):
        # Initialize all memory components
        self.sensory_memory = SensoryMemory()
        self.working_memory = WorkingMemory()
        self.semantic_memory = SemanticMemory()
        self.episodic_memory = EpisodicMemory()
        self.advanced_rag = AdvancedRAGSystem(mongodb_uri)
        
        # Memory consolidation settings
        self.consolidation_interval = 300  # 5 minutes
        self.last_consolidation = datetime.now()
        
        logger.info("🧠 Enhanced Memory System initialized")
        
    async def process_market_perception(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process new market data through memory hierarchy"""
        # 1. Sensory Memory: Immediate perception
        self.sensory_memory.add_perception(market_data)
        
        # 2. Working Memory: Add to current context
        importance = self._calculate_importance(market_data)
        self.working_memory.add_to_working_memory(
            f"market_{datetime.now().timestamp()}", 
            market_data, 
            importance
        )
        
        # 3. Retrieve relevant memories
        context = await self._retrieve_relevant_context(market_data)
        
        # 4. Check for consolidation
        if self._should_consolidate():
            await self._consolidate_memories()
            
        return context
        
    async def _retrieve_relevant_context(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant context from all memory systems"""
        context = {
            'working_memory': self.working_memory.get_current_context(),
            'semantic_concepts': [],
            'similar_episodes': [],
            'rag_results': []
        }
        
        # Get semantic concepts
        market_type = market_data.get('symbol', 'unknown')
        context['semantic_concepts'] = self.semantic_memory.get_related_concepts(market_type)
        
        # Get similar episodes
        context['similar_episodes'] = self.episodic_memory.get_similar_episodes(market_data)
        
        # Get RAG results
        query = f"Trading decision for {market_type} with price {market_data.get('price', 0)}"
        context['rag_results'] = await self.advanced_rag.vector_search(query)
        
        return context
        
    def _calculate_importance(self, data: Dict[str, Any]) -> float:
        """Calculate importance score for memory item"""
        # Simple importance calculation based on price change, volume, etc.
        price_change = abs(data.get('price_change_percent', 0))
        volume_ratio = data.get('volume_ratio', 1.0)
        
        importance = min(1.0, (price_change / 10.0) + (volume_ratio / 5.0))
        return importance
        
    def _should_consolidate(self) -> bool:
        """Check if memory consolidation is needed"""
        time_since_last = (datetime.now() - self.last_consolidation).total_seconds()
        return time_since_last > self.consolidation_interval
        
    async def _consolidate_memories(self) -> None:
        """Consolidate memories from working to long-term storage"""
        try:
            # Move important items from working memory to long-term storage
            for key, item_data in self.working_memory.active_items.items():
                if item_data['importance'] > 0.7:  # High importance threshold
                    # Store in RAG system for future retrieval
                    content = json.dumps(item_data['item'])
                    metadata = {
                        'type': 'consolidated_memory',
                        'importance': item_data['importance'],
                        'original_key': key
                    }
                    await self.advanced_rag.store_document(content, metadata)
                    
            self.last_consolidation = datetime.now()
            logger.info("🔄 Memory consolidation completed")
            
        except Exception as e:
            logger.error(f"❌ Memory consolidation failed: {e}")

    async def add_trading_episode(self, episode: TradingEpisode) -> None:
        """Add a new trading episode to episodic memory"""
        self.episodic_memory.add_episode(episode)

        # Also store in RAG system for future retrieval
        content = json.dumps({
            'episode_id': episode.episode_id,
            'market_context': episode.market_context,
            'decision_made': episode.decision_made,
            'outcome': episode.outcome,
            'lessons_learned': episode.lessons_learned,
            'success_score': episode.success_score
        })

        metadata = {
            'type': 'trading_episode',
            'market_type': episode.market_context.get('market_type', 'unknown'),
            'success_score': episode.success_score,
            'timestamp': episode.timestamp.isoformat()
        }

        await self.advanced_rag.store_document(content, metadata)
        logger.info(f"📝 Trading episode {episode.episode_id} stored in memory")

    async def query_memory(self, query: str, memory_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Query all memory systems for relevant information"""
        if memory_types is None:
            memory_types = ['semantic', 'episodic', 'rag']

        results = {}

        # Query semantic memory
        if 'semantic' in memory_types:
            related_concepts = self.semantic_memory.get_related_concepts(query)
            results['semantic'] = {
                'related_concepts': related_concepts,
                'trading_rules': [rule for rule_name, rule in self.semantic_memory.trading_rules.items()
                                if query.lower() in rule_name.lower()]
            }

        # Query episodic memory
        if 'episodic' in memory_types:
            # Simple keyword matching for episodes
            matching_episodes = []
            for episode in self.episodic_memory.episodes.values():
                episode_text = json.dumps(episode.market_context).lower()
                if query.lower() in episode_text:
                    matching_episodes.append(episode)
            results['episodic'] = matching_episodes[:5]  # Top 5 matches

        # Query RAG system
        if 'rag' in memory_types:
            rag_results = await self.advanced_rag.vector_search(query, limit=5)
            results['rag'] = rag_results

        return results

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage"""
        return {
            'sensory_buffer_size': len(self.sensory_memory.buffer),
            'working_memory_items': len(self.working_memory.active_items),
            'semantic_concepts': len(self.semantic_memory.knowledge_base),
            'trading_rules': len(self.semantic_memory.trading_rules),
            'episodic_episodes': len(self.episodic_memory.episodes),
            'last_consolidation': self.last_consolidation.isoformat(),
            'rag_available': self.advanced_rag.collection is not None
        }
