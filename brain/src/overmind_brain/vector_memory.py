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

# Try to import sentence_transformers, use mock if not available
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    # Mock SentenceTransformer for testing
    class SentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name

        def encode(self, texts):
            # Return mock embeddings
            import random
            if isinstance(texts, str):
                return [random.random() for _ in range(384)]
            return [[random.random() for _ in range(384)] for _ in texts]

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

    # 🧠 RUGPULL SCANNER - RAG Integration dla Historii Deweloperów

    def add_developer_history(self, developer_address: str, project_data: Dict[str, Any]) -> str:
        """Add developer project history to vector memory.

        Args:
            developer_address: Developer wallet address
            project_data: Project information including outcome, timeline, etc.

        Returns:
            Memory ID of stored developer history
        """
        logger.info(f"📝 Adding developer history for: {developer_address}")

        # Create comprehensive text description for embedding
        project_text = f"""
        Developer: {developer_address}
        Project: {project_data.get('name', 'Unknown')}
        Token: {project_data.get('token_symbol', 'N/A')}
        Launch Date: {project_data.get('launch_date', 'Unknown')}
        Outcome: {project_data.get('outcome', 'Unknown')}
        Duration: {project_data.get('duration_days', 0)} days
        Final Status: {project_data.get('final_status', 'Unknown')}
        Rug Pull: {project_data.get('was_rug_pull', False)}
        Exit Method: {project_data.get('exit_method', 'N/A')}
        Investor Losses: {project_data.get('investor_losses', 0)} SOL
        Red Flags: {', '.join(project_data.get('red_flags', []))}
        Community Response: {project_data.get('community_response', 'N/A')}
        """

        # Metadata for filtering and analysis
        metadata = {
            "type": "developer_history",
            "developer_address": developer_address,
            "project_name": project_data.get('name', 'Unknown'),
            "token_symbol": project_data.get('token_symbol', 'N/A'),
            "outcome": project_data.get('outcome', 'Unknown'),
            "was_rug_pull": project_data.get('was_rug_pull', False),
            "duration_days": project_data.get('duration_days', 0),
            "investor_losses": project_data.get('investor_losses', 0),
            "launch_date": project_data.get('launch_date', 'Unknown'),
            "final_status": project_data.get('final_status', 'Unknown'),
            "red_flags_count": len(project_data.get('red_flags', [])),
            "timestamp": datetime.now().isoformat()
        }

        memory_id = self.add_memory(project_text, metadata)
        logger.info(f"✅ Developer history stored with ID: {memory_id}")
        return memory_id

    def get_developer_history(self, developer_address: str) -> List[Dict[str, Any]]:
        """Get complete history for a specific developer.

        Args:
            developer_address: Developer wallet address to lookup

        Returns:
            List of developer's project history
        """
        logger.info(f"🔍 Retrieving developer history for: {developer_address}")

        try:
            # Search for all projects by this developer
            filters = {
                "type": "developer_history",
                "developer_address": developer_address
            }

            history = self.search_by_metadata(filters, limit=50)  # Get up to 50 projects

            logger.info(f"📊 Found {len(history)} projects for developer {developer_address}")
            return history

        except Exception as e:
            logger.error(f"❌ Error retrieving developer history: {e}")
            return []

    def analyze_developer_reputation(self, developer_address: str) -> Dict[str, Any]:
        """Analyze developer reputation based on project history.

        Args:
            developer_address: Developer wallet address to analyze

        Returns:
            Dict with reputation analysis and risk score
        """
        logger.info(f"🎯 Analyzing developer reputation for: {developer_address}")

        history = self.get_developer_history(developer_address)

        if not history:
            return {
                "developer_address": developer_address,
                "reputation_score": 0.5,  # Neutral for unknown developers
                "risk_level": "UNKNOWN",
                "total_projects": 0,
                "analysis": "No historical data available"
            }

        # Analyze project outcomes
        total_projects = len(history)
        rug_pulls = sum(1 for h in history if h.get("metadata", {}).get("was_rug_pull", False))
        failed_projects = sum(1 for h in history if h.get("metadata", {}).get("outcome") in ["failed", "abandoned", "rug_pull"])
        successful_projects = sum(1 for h in history if h.get("metadata", {}).get("outcome") in ["successful", "ongoing"])

        # Calculate average project duration
        durations = [h.get("metadata", {}).get("duration_days", 0) for h in history if h.get("metadata", {}).get("duration_days", 0) > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Calculate total investor losses
        total_losses = sum(h.get("metadata", {}).get("investor_losses", 0) for h in history)

        # Calculate reputation score (0.0 = worst, 1.0 = best)
        if total_projects == 0:
            reputation_score = 0.5
        else:
            success_rate = successful_projects / total_projects
            rug_pull_rate = rug_pulls / total_projects
            failure_rate = failed_projects / total_projects

            # Weighted scoring
            reputation_score = (
                success_rate * 0.5 +           # 50% weight for success
                (1 - rug_pull_rate) * 0.3 +    # 30% weight for no rug pulls
                (1 - failure_rate) * 0.2       # 20% weight for no failures
            )

        # Determine risk level
        if rug_pulls > 0:
            risk_level = "CRITICAL"
        elif failure_rate > 0.7:
            risk_level = "HIGH"
        elif reputation_score < 0.3:
            risk_level = "HIGH"
        elif reputation_score < 0.6:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Generate analysis summary
        analysis_points = []
        if rug_pulls > 0:
            analysis_points.append(f"🚨 {rug_pulls} confirmed rug pull(s)")
        if failed_projects > successful_projects:
            analysis_points.append(f"⚠️ More failures ({failed_projects}) than successes ({successful_projects})")
        if avg_duration < 30:
            analysis_points.append(f"⚠️ Short average project duration: {avg_duration:.1f} days")
        if total_losses > 100:
            analysis_points.append(f"💸 High investor losses: {total_losses:.1f} SOL")
        if successful_projects > 0:
            analysis_points.append(f"✅ {successful_projects} successful project(s)")

        result = {
            "developer_address": developer_address,
            "reputation_score": reputation_score,
            "risk_level": risk_level,
            "total_projects": total_projects,
            "project_breakdown": {
                "successful": successful_projects,
                "failed": failed_projects,
                "rug_pulls": rug_pulls
            },
            "metrics": {
                "success_rate": successful_projects / total_projects if total_projects > 0 else 0,
                "rug_pull_rate": rug_pulls / total_projects if total_projects > 0 else 0,
                "avg_duration_days": avg_duration,
                "total_investor_losses": total_losses
            },
            "analysis_points": analysis_points,
            "recommendation": "REJECT" if risk_level == "CRITICAL" else ("CAUTION" if risk_level == "HIGH" else "PROCEED")
        }

        logger.info(f"📊 Developer reputation analysis complete: {risk_level} risk, {reputation_score:.2f} score")
        return result

    def detect_scam_patterns(self, project_description: str, developer_address: str) -> Dict[str, Any]:
        """Detect scam patterns by comparing with historical scam projects.

        Args:
            project_description: Description of current project to analyze
            developer_address: Developer address to check

        Returns:
            Dict with scam pattern analysis and risk assessment
        """
        logger.info(f"🔍 Detecting scam patterns for project by: {developer_address}")

        # Get developer history first
        developer_reputation = self.analyze_developer_reputation(developer_address)

        # Search for similar failed/scam projects in vector memory
        scam_query = f"rug pull scam failed project abandoned {project_description}"
        similar_scams = self.find_similar(scam_query, limit=10)

        # Filter for actual scam projects
        confirmed_scams = [
            scam for scam in similar_scams
            if scam.get("metadata", {}).get("was_rug_pull", False) or
               scam.get("metadata", {}).get("outcome") in ["rug_pull", "scam", "abandoned"]
        ]

        # Analyze pattern similarities
        pattern_matches = []
        risk_factors = []

        if developer_reputation["risk_level"] == "CRITICAL":
            pattern_matches.append("Developer has history of rug pulls")
            risk_factors.append("CRITICAL: Known scammer")

        if len(confirmed_scams) > 0:
            pattern_matches.append(f"Similar to {len(confirmed_scams)} known scam projects")
            risk_factors.append(f"Project description matches {len(confirmed_scams)} scam patterns")

        # Check for common scam keywords in description
        scam_keywords = [
            "guaranteed returns", "100x", "moon", "diamond hands",
            "to the moon", "ape in", "HODL", "pump", "lambo",
            "get rich quick", "easy money", "no risk"
        ]

        found_keywords = [kw for kw in scam_keywords if kw.lower() in project_description.lower()]
        if found_keywords:
            pattern_matches.append(f"Contains scam keywords: {', '.join(found_keywords)}")
            risk_factors.append("Suspicious marketing language")

        # Calculate overall scam risk score
        scam_risk_score = 0.0

        # Developer history weight (40%)
        if developer_reputation["risk_level"] == "CRITICAL":
            scam_risk_score += 0.4
        elif developer_reputation["risk_level"] == "HIGH":
            scam_risk_score += 0.25
        elif developer_reputation["risk_level"] == "MEDIUM":
            scam_risk_score += 0.1

        # Similar scam projects weight (35%)
        if len(confirmed_scams) > 5:
            scam_risk_score += 0.35
        elif len(confirmed_scams) > 2:
            scam_risk_score += 0.25
        elif len(confirmed_scams) > 0:
            scam_risk_score += 0.15

        # Scam keywords weight (25%)
        keyword_ratio = len(found_keywords) / len(scam_keywords)
        scam_risk_score += keyword_ratio * 0.25

        # Determine final risk level
        if scam_risk_score > 0.7:
            final_risk = "CRITICAL"
            recommendation = "REJECT_IMMEDIATELY"
        elif scam_risk_score > 0.5:
            final_risk = "HIGH"
            recommendation = "AVOID"
        elif scam_risk_score > 0.3:
            final_risk = "MEDIUM"
            recommendation = "EXTREME_CAUTION"
        else:
            final_risk = "LOW"
            recommendation = "PROCEED_WITH_NORMAL_CAUTION"

        result = {
            "developer_address": developer_address,
            "scam_risk_score": scam_risk_score,
            "risk_level": final_risk,
            "recommendation": recommendation,
            "pattern_analysis": {
                "similar_scam_projects": len(confirmed_scams),
                "pattern_matches": pattern_matches,
                "scam_keywords_found": found_keywords,
                "developer_reputation": developer_reputation
            },
            "risk_factors": risk_factors,
            "confidence": min(0.95, 0.6 + (len(confirmed_scams) * 0.05) + (len(found_keywords) * 0.02))
        }

        if final_risk == "CRITICAL":
            logger.warning(f"🚨 CRITICAL scam risk detected for {developer_address}")
        elif final_risk == "HIGH":
            logger.warning(f"⚠️ HIGH scam risk detected for {developer_address}")
        else:
            logger.info(f"✅ Acceptable scam risk for {developer_address}")

        return result

    def perform_developer_rag_scan(self, developer_address: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform complete RAG-based developer history scan.

        Args:
            developer_address: Developer wallet address
            project_data: Current project information

        Returns:
            Dict with complete RAG analysis and verdict
        """
        logger.info(f"🧠 Starting Developer RAG Scan for: {developer_address}")

        try:
            # Get comprehensive developer analysis
            reputation_analysis = self.analyze_developer_reputation(developer_address)

            # Detect scam patterns
            project_description = f"{project_data.get('name', '')} {project_data.get('description', '')}"
            scam_analysis = self.detect_scam_patterns(project_description, developer_address)

            # Aggregate risk factors
            critical_risks = []
            high_risks = []
            warnings = []

            # Analyze reputation risks
            if reputation_analysis["risk_level"] == "CRITICAL":
                critical_risks.append("Developer has history of rug pulls")
            elif reputation_analysis["risk_level"] == "HIGH":
                high_risks.append("Developer has poor track record")
            elif reputation_analysis["risk_level"] == "MEDIUM":
                warnings.append("Developer has mixed track record")

            # Analyze scam pattern risks
            if scam_analysis["risk_level"] == "CRITICAL":
                critical_risks.append("Project matches known scam patterns")
            elif scam_analysis["risk_level"] == "HIGH":
                high_risks.append("Project shows scam indicators")
            elif scam_analysis["risk_level"] == "MEDIUM":
                warnings.append("Project has some concerning patterns")

            # Determine overall verdict
            if critical_risks:
                overall_risk = "CRITICAL"
                recommendation = "REJECT_IMMEDIATELY"
                verdict = "DEVELOPER_HISTORY_DISQUALIFIED"
            elif len(high_risks) >= 2:
                overall_risk = "CRITICAL"
                recommendation = "REJECT_IMMEDIATELY"
                verdict = "MULTIPLE_HIGH_RISKS"
            elif high_risks:
                overall_risk = "HIGH"
                recommendation = "AVOID"
                verdict = "CONDITIONAL_REJECT"
            elif warnings:
                overall_risk = "MEDIUM"
                recommendation = "PROCEED_WITH_EXTREME_CAUTION"
                verdict = "CONDITIONAL_PASS"
            else:
                overall_risk = "LOW"
                recommendation = "PROCEED"
                verdict = "PASS"

            # Compile comprehensive RAG scan report
            scan_result = {
                "developer_address": developer_address,
                "scan_level": "DEVELOPER_RAG_ANALYSIS",
                "timestamp": datetime.now().isoformat(),
                "overall_risk": overall_risk,
                "verdict": verdict,
                "recommendation": recommendation,
                "detailed_analyses": {
                    "reputation_analysis": reputation_analysis,
                    "scam_pattern_analysis": scam_analysis
                },
                "risk_summary": {
                    "critical_risks": len(critical_risks),
                    "high_risks": len(high_risks),
                    "warnings": len(warnings),
                    "total_issues": len(critical_risks) + len(high_risks) + len(warnings)
                },
                "risk_factors": {
                    "critical": critical_risks,
                    "high": high_risks,
                    "warnings": warnings
                },
                "next_steps": "Proceed to final aggregation" if verdict == "PASS" else "Developer disqualified"
            }

            # Log results
            if verdict in ["DEVELOPER_HISTORY_DISQUALIFIED", "MULTIPLE_HIGH_RISKS"]:
                logger.error(f"🚨 DEVELOPER RAG SCAN FAILED for {developer_address} - {verdict}")
            elif verdict == "CONDITIONAL_REJECT":
                logger.warning(f"⚠️ DEVELOPER RAG SCAN REJECT for {developer_address}")
            elif verdict == "CONDITIONAL_PASS":
                logger.warning(f"⚠️ DEVELOPER RAG SCAN WARNING for {developer_address}")
            else:
                logger.info(f"✅ DEVELOPER RAG SCAN PASSED for {developer_address}")

            return scan_result

        except Exception as e:
            logger.error(f"❌ Developer RAG scan failed for {developer_address}: {e}")
            return {
                "developer_address": developer_address,
                "scan_level": "DEVELOPER_RAG_ANALYSIS",
                "verdict": "ERROR",
                "recommendation": "REJECT_IMMEDIATELY",
                "error": str(e),
                "overall_risk": "CRITICAL"
            }
