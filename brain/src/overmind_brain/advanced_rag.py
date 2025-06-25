"""THE OVERMIND PROTOCOL - Advanced RAG Implementation
Enhanced Retrieval-Augmented Generation with vector similarity search,
semantic chunking, and multi-modal knowledge integration.
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from abc import ABC, abstractmethod

# Vector and embedding libraries
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("ChromaDB not available, using mock vector store")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("SentenceTransformers not available, using mock embeddings")

logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Types of documents in the knowledge base"""
    MARKET_DATA = "market_data"
    TRADING_STRATEGY = "trading_strategy"
    RISK_ANALYSIS = "risk_analysis"
    HISTORICAL_TRADE = "historical_trade"
    NEWS_ARTICLE = "news_article"
    TECHNICAL_ANALYSIS = "technical_analysis"
    SENTIMENT_DATA = "sentiment_data"
    REGULATORY_INFO = "regulatory_info"

@dataclass
class Document:
    """Document structure for RAG system"""
    id: str
    content: str
    doc_type: DocumentType
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: datetime = None
    relevance_score: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

@dataclass
class RetrievalResult:
    """Result from document retrieval"""
    documents: List[Document]
    query: str
    total_results: int
    retrieval_time_ms: float
    similarity_scores: List[float]
    metadata: Dict[str, Any]

@dataclass
class RAGResponse:
    """Response from RAG system"""
    answer: str
    confidence: float
    source_documents: List[Document]
    reasoning: str
    metadata: Dict[str, Any]
    processing_time_ms: float

class BaseVectorStore(ABC):
    """Abstract base class for vector stores"""
    
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to the vector store"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[Document]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from the vector store"""
        pass
    
    @abstractmethod
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        pass

class ChromaVectorStore(BaseVectorStore):
    """ChromaDB implementation of vector store"""
    
    def __init__(self, collection_name: str = "overmind_knowledge", persist_directory: str = "./chroma_db"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        
    async def initialize(self) -> bool:
        """Initialize ChromaDB client and collection"""
        try:
            if not CHROMADB_AVAILABLE:
                logger.warning("ChromaDB not available, using mock mode")
                return False
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "THE OVERMIND PROTOCOL Knowledge Base"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return False
    
    async def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to ChromaDB"""
        try:
            if not self.collection:
                return False
            
            ids = [doc.id for doc in documents]
            documents_text = [doc.content for doc in documents]
            metadatas = [
                {
                    **doc.metadata,
                    "doc_type": doc.doc_type.value,
                    "timestamp": doc.timestamp.isoformat()
                }
                for doc in documents
            ]
            
            # Add embeddings if available
            embeddings = None
            if documents[0].embedding:
                embeddings = [doc.embedding for doc in documents]
            
            self.collection.add(
                ids=ids,
                documents=documents_text,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(documents)} documents to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {e}")
            return False
    
    async def search(self, query: str, limit: int = 10, filters: Dict[str, Any] = None) -> List[Document]:
        """Search for similar documents in ChromaDB"""
        try:
            if not self.collection:
                return []
            
            # Build where clause for filtering
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if key == "doc_type" and isinstance(value, DocumentType):
                        where_clause[key] = value.value
                    else:
                        where_clause[key] = value
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Convert results to Document objects
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc_text in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0.0
                    
                    # Convert distance to similarity score (1 - distance)
                    similarity_score = max(0.0, 1.0 - distance)
                    
                    doc = Document(
                        id=results['ids'][0][i],
                        content=doc_text,
                        doc_type=DocumentType(metadata.get('doc_type', 'market_data')),
                        metadata=metadata,
                        relevance_score=similarity_score,
                        timestamp=datetime.fromisoformat(metadata.get('timestamp', datetime.now().isoformat()))
                    )
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to search ChromaDB: {e}")
            return []
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from ChromaDB"""
        try:
            if not self.collection:
                return False
            
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from ChromaDB: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get ChromaDB collection statistics"""
        try:
            if not self.collection:
                return {}
            
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Failed to get ChromaDB stats: {e}")
            return {}

class EmbeddingModel:
    """Embedding model for converting text to vectors"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        
    async def initialize(self) -> bool:
        """Initialize the embedding model"""
        try:
            if not SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.warning("SentenceTransformers not available, using mock embeddings")
                return False
            
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Initialized embedding model: {self.model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            return False
    
    async def encode(self, texts: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Encode text(s) to embeddings"""
        try:
            if not self.model:
                # Return mock embeddings
                if isinstance(texts, str):
                    return [0.1] * 384  # Mock 384-dimensional embedding
                else:
                    return [[0.1] * 384 for _ in texts]
            
            if isinstance(texts, str):
                embedding = self.model.encode(texts).tolist()
                return embedding
            else:
                embeddings = self.model.encode(texts).tolist()
                return embeddings
                
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            if isinstance(texts, str):
                return [0.1] * 384
            else:
                return [[0.1] * 384 for _ in texts]

class SemanticChunker:
    """Semantic chunking for better document processing"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split document into semantic chunks"""
        # Simple sentence-based chunking (can be enhanced with semantic similarity)
        sentences = self._split_into_sentences(content)
        chunks = []
        
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Create chunk
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": {**metadata, "chunk_index": len(chunks)}
                })
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk, self.overlap)
                current_chunk = overlap_sentences + " " + sentence
                current_length = len(current_chunk.split())
            else:
                current_chunk += " " + sentence
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": {**metadata, "chunk_index": len(chunks)}
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be enhanced with NLP libraries)
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_sentences(self, text: str, overlap_words: int) -> str:
        """Get last N words for overlap"""
        words = text.split()
        if len(words) <= overlap_words:
            return text
        return " ".join(words[-overlap_words:])

class AdvancedRAG:
    """Advanced RAG system with vector similarity search"""
    
    def __init__(self, vector_store: BaseVectorStore, embedding_model: EmbeddingModel):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.chunker = SemanticChunker()
        self.query_history = []
        
    async def initialize(self) -> bool:
        """Initialize the RAG system"""
        try:
            vector_store_ok = await self.vector_store.initialize()
            embedding_model_ok = await self.embedding_model.initialize()
            
            if vector_store_ok and embedding_model_ok:
                logger.info("Advanced RAG system initialized successfully")
                return True
            else:
                logger.warning("RAG system initialized with limited functionality")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            return False
    
    async def add_knowledge(self, content: str, doc_type: DocumentType, metadata: Dict[str, Any] = None) -> str:
        """Add knowledge to the RAG system"""
        try:
            if metadata is None:
                metadata = {}
            
            # Generate document ID
            doc_id = self._generate_document_id(content, doc_type)
            
            # Chunk the document if it's large
            if len(content.split()) > 400:
                chunks = self.chunker.chunk_document(content, metadata)
                documents = []
                
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    embedding = await self.embedding_model.encode(chunk["content"])
                    
                    doc = Document(
                        id=chunk_id,
                        content=chunk["content"],
                        doc_type=doc_type,
                        metadata=chunk["metadata"],
                        embedding=embedding
                    )
                    documents.append(doc)
            else:
                # Single document
                embedding = await self.embedding_model.encode(content)
                doc = Document(
                    id=doc_id,
                    content=content,
                    doc_type=doc_type,
                    metadata=metadata,
                    embedding=embedding
                )
                documents = [doc]
            
            # Add to vector store
            success = await self.vector_store.add_documents(documents)
            
            if success:
                logger.info(f"Added knowledge: {doc_type.value} ({len(documents)} chunks)")
                return doc_id
            else:
                logger.error("Failed to add knowledge to vector store")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return ""
    
    async def retrieve_relevant_knowledge(self, query: str, limit: int = 5, 
                                        doc_types: List[DocumentType] = None) -> RetrievalResult:
        """Retrieve relevant knowledge for a query"""
        start_time = datetime.now()
        
        try:
            # Build filters
            filters = {}
            if doc_types:
                # For multiple doc types, we'll need to do separate queries
                # For now, use the first doc type as filter
                filters["doc_type"] = doc_types[0]
            
            # Search vector store
            documents = await self.vector_store.search(query, limit, filters)
            
            # Calculate retrieval time
            retrieval_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Extract similarity scores
            similarity_scores = [doc.relevance_score for doc in documents]
            
            result = RetrievalResult(
                documents=documents,
                query=query,
                total_results=len(documents),
                retrieval_time_ms=retrieval_time,
                similarity_scores=similarity_scores,
                metadata={
                    "filters_applied": filters,
                    "doc_types_requested": [dt.value for dt in doc_types] if doc_types else None
                }
            )
            
            # Store query in history
            self.query_history.append({
                "query": query,
                "timestamp": datetime.now(),
                "results_count": len(documents)
            })
            
            # Keep only last 100 queries
            if len(self.query_history) > 100:
                self.query_history = self.query_history[-100:]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve knowledge: {e}")
            return RetrievalResult(
                documents=[],
                query=query,
                total_results=0,
                retrieval_time_ms=0.0,
                similarity_scores=[],
                metadata={"error": str(e)}
            )
    
    async def generate_rag_response(self, query: str, context: Dict[str, Any] = None) -> RAGResponse:
        """Generate response using RAG"""
        start_time = datetime.now()
        
        try:
            # Retrieve relevant knowledge
            retrieval_result = await self.retrieve_relevant_knowledge(query, limit=3)
            
            if not retrieval_result.documents:
                return RAGResponse(
                    answer="No relevant knowledge found for this query.",
                    confidence=0.1,
                    source_documents=[],
                    reasoning="No documents retrieved from knowledge base",
                    metadata={"retrieval_result": asdict(retrieval_result)},
                    processing_time_ms=0.0
                )
            
            # Combine retrieved knowledge
            knowledge_context = self._combine_retrieved_knowledge(retrieval_result.documents)
            
            # Generate response (this would integrate with AI models)
            answer = self._generate_answer_from_knowledge(query, knowledge_context, context)
            confidence = self._calculate_response_confidence(retrieval_result)
            reasoning = self._generate_reasoning(query, retrieval_result.documents)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return RAGResponse(
                answer=answer,
                confidence=confidence,
                source_documents=retrieval_result.documents,
                reasoning=reasoning,
                metadata={
                    "retrieval_result": asdict(retrieval_result),
                    "knowledge_context_length": len(knowledge_context)
                },
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {e}")
            return RAGResponse(
                answer="Error generating response",
                confidence=0.0,
                source_documents=[],
                reasoning=f"Error: {str(e)}",
                metadata={"error": str(e)},
                processing_time_ms=0.0
            )
    
    def _generate_document_id(self, content: str, doc_type: DocumentType) -> str:
        """Generate unique document ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = int(datetime.now().timestamp())
        return f"{doc_type.value}_{timestamp}_{content_hash}"
    
    def _combine_retrieved_knowledge(self, documents: List[Document]) -> str:
        """Combine retrieved documents into context"""
        knowledge_parts = []
        for doc in documents:
            knowledge_parts.append(f"[{doc.doc_type.value}] {doc.content}")
        return "\n\n".join(knowledge_parts)
    
    def _generate_answer_from_knowledge(self, query: str, knowledge: str, context: Dict[str, Any] = None) -> str:
        """Generate answer from retrieved knowledge (simplified)"""
        # This would integrate with AI models for actual generation
        return f"Based on the retrieved knowledge: {knowledge[:200]}..."
    
    def _calculate_response_confidence(self, retrieval_result: RetrievalResult) -> float:
        """Calculate confidence based on retrieval quality"""
        if not retrieval_result.similarity_scores:
            return 0.0
        
        avg_similarity = sum(retrieval_result.similarity_scores) / len(retrieval_result.similarity_scores)
        return min(avg_similarity, 1.0)
    
    def _generate_reasoning(self, query: str, documents: List[Document]) -> str:
        """Generate reasoning for the response"""
        doc_types = [doc.doc_type.value for doc in documents]
        return f"Retrieved {len(documents)} relevant documents of types: {', '.join(set(doc_types))}"
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            vector_stats = await self.vector_store.get_collection_stats()
            
            return {
                **vector_stats,
                "recent_queries": len(self.query_history),
                "embedding_model": self.embedding_model.model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge stats: {e}")
            return {"error": str(e)}
