#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Governance Memory Manager
Stores governance events and outcomes in vector memory for learning
"""

import json
import redis
import time
import logging
import chromadb
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('GovernanceMemoryManager')

class GovernanceMemoryManager:
    """
    Manages governance event storage and retrieval in vector memory
    """
    
    def __init__(self):
        """Initialize governance memory manager"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Use Redis for simple memory storage
        self.memory_key_prefix = "overmind:governance_memory"

        logger.info("🧠 Governance Memory Manager initialized")
        logger.info("📚 Connected to Redis memory storage")
    
    async def start_memory_management(self):
        """Start monitoring for governance events to store"""
        logger.info("🎯 Starting Governance Memory Management...")
        
        while True:
            try:
                # Listen for governance signals
                result = self.redis_client.blpop("overmind:strategy_signals", timeout=5)
                
                if result:
                    _, signal_data = result
                    signal = json.loads(signal_data)
                    
                    if signal.get('signal_type') == 'governance_alpha':
                        await self.store_governance_event(signal)
                
                # Also check for execution results related to governance
                result = self.redis_client.blpop("overmind:execution_results", timeout=1)
                
                if result:
                    _, execution_data = result
                    execution = json.loads(execution_data)
                    
                    if execution.get('strategy') == 'governance_alpha_hunter':
                        await self.store_execution_outcome(execution)
                        
            except Exception as e:
                logger.error(f"❌ Error in memory management: {e}")
                await asyncio.sleep(5)
    
    async def store_governance_event(self, signal: Dict[str, Any]):
        """Store governance event in Redis memory"""
        try:
            # Create comprehensive memory entry
            memory_text = self.create_governance_memory_text(signal)

            # Generate unique ID
            memory_id = f"governance_{signal['dao']}_{int(signal['timestamp'])}"

            # Create memory entry
            memory_entry = {
                "id": memory_id,
                "text": memory_text,
                "type": "governance_event",
                "dao": signal['dao'],
                "token": signal['token'],
                "proposal_type": signal['proposal_type'],
                "sentiment_score": signal['sentiment_score'],
                "impact_score": signal['impact_score'],
                "strategy": signal['strategy'],
                "timestamp": signal['timestamp'],
                "date": datetime.fromtimestamp(signal['timestamp']).isoformat()
            }

            # Store in Redis
            redis_key = f"{self.memory_key_prefix}:events:{memory_id}"
            self.redis_client.setex(redis_key, 86400 * 30, json.dumps(memory_entry))  # 30 days TTL

            # Add to index
            self.redis_client.sadd(f"{self.memory_key_prefix}:event_index", memory_id)

            logger.info(f"📚 Governance event stored in memory: {signal['dao'].upper()} - {signal['token']}")
            logger.info(f"   Memory ID: {memory_id}")
            logger.info(f"   Sentiment: {signal['sentiment_score']:.2f}")
            logger.info(f"   Impact: {signal['impact_score']:.2f}")

        except Exception as e:
            logger.error(f"❌ Failed to store governance event: {e}")
    
    async def store_execution_outcome(self, execution: Dict[str, Any]):
        """Store governance trade execution outcome"""
        try:
            # Create execution memory entry
            memory_text = self.create_execution_memory_text(execution)

            # Generate unique ID
            memory_id = f"governance_execution_{execution.get('command_id', int(time.time()))}"

            # Create memory entry
            memory_entry = {
                "id": memory_id,
                "text": memory_text,
                "type": "governance_execution",
                "action": execution.get('action', 'UNKNOWN'),
                "symbol": execution.get('symbol', 'UNKNOWN'),
                "status": execution.get('status', 'UNKNOWN'),
                "profit": execution.get('profit', 0.0),
                "strategy": execution.get('strategy', 'governance_alpha_hunter'),
                "timestamp": execution.get('timestamp', time.time()),
                "date": datetime.now().isoformat()
            }

            # Store in Redis
            redis_key = f"{self.memory_key_prefix}:executions:{memory_id}"
            self.redis_client.setex(redis_key, 86400 * 30, json.dumps(memory_entry))  # 30 days TTL

            # Add to index
            self.redis_client.sadd(f"{self.memory_key_prefix}:execution_index", memory_id)

            logger.info(f"📚 Execution outcome stored in memory: {execution.get('action')} {execution.get('symbol')}")
            logger.info(f"   Status: {execution.get('status')}")
            logger.info(f"   Profit: ${execution.get('profit', 0.0):.6f}")

        except Exception as e:
            logger.error(f"❌ Failed to store execution outcome: {e}")
    
    def create_governance_memory_text(self, signal: Dict[str, Any]) -> str:
        """Create comprehensive memory text for governance event"""
        return f"""GOVERNANCE ALPHA EVENT DETECTED

DAO: {signal['dao'].upper()} ({signal['token']})
Proposal: {signal['title']}
Type: {signal['proposal_type']}
Sentiment Score: {signal['sentiment_score']:.2f}/1.0
Impact Score: {signal['impact_score']:.2f}/1.0

ANALYSIS:
Detected high-impact governance proposal with {signal['sentiment_score']:.0%} positive sentiment. 
Proposal type '{signal['proposal_type']}' historically correlates with {signal['impact_score']:.0%} price impact.
Strategy 'governance_alpha_hunter' triggered based on sentiment threshold and keyword analysis.

MARKET CONTEXT:
Token: {signal['token']}
Expected Impact: {signal['impact_score']:.1%}
Strategy Confidence: HIGH
Trading Signal: BUY recommendation based on governance alpha

LEARNING NOTES:
This type of {signal['proposal_type']} proposal for {signal['dao'].upper()} DAO typically results in positive price movement.
Monitor execution results to validate prediction accuracy and refine future governance alpha detection."""
    
    def create_execution_memory_text(self, execution: Dict[str, Any]) -> str:
        """Create memory text for execution outcome"""
        return f"""GOVERNANCE ALPHA EXECUTION RESULT

Trade Details:
Action: {execution.get('action', 'UNKNOWN')}
Symbol: {execution.get('symbol', 'UNKNOWN')}
Quantity: {execution.get('quantity', 0.0)}
Price: ${execution.get('executed_price', 0.0):.6f}
Status: {execution.get('status', 'UNKNOWN')}

Financial Outcome:
Profit/Loss: ${execution.get('profit', 0.0):.6f}
Fees: ${execution.get('fees', 0.0):.6f}
Execution Time: {execution.get('execution_latency_ms', 0)}ms

Strategy Performance:
Strategy: {execution.get('strategy', 'governance_alpha_hunter')}
Confidence: {execution.get('confidence_score', 0.0):.2f}
Success: {'YES' if execution.get('status') == 'SUCCESS' else 'NO'}

LEARNING INSIGHTS:
Governance alpha strategy execution {'successful' if execution.get('status') == 'SUCCESS' else 'failed'}.
{'Positive' if execution.get('profit', 0.0) > 0 else 'Negative'} financial outcome validates governance proposal impact prediction.
Update strategy parameters based on this execution result."""
    
    def query_governance_history(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Query governance history from Redis memory"""
        try:
            results = []

            # Get all event IDs
            event_ids = self.redis_client.smembers(f"{self.memory_key_prefix}:event_index")
            execution_ids = self.redis_client.smembers(f"{self.memory_key_prefix}:execution_index")

            # Search through events
            for event_id in list(event_ids)[:n_results]:
                event_key = f"{self.memory_key_prefix}:events:{event_id}"
                event_data = self.redis_client.get(event_key)
                if event_data:
                    event = json.loads(event_data)
                    if query.lower() in event.get('text', '').lower():
                        results.append(event)

            # Search through executions
            for exec_id in list(execution_ids)[:n_results]:
                exec_key = f"{self.memory_key_prefix}:executions:{exec_id}"
                exec_data = self.redis_client.get(exec_key)
                if exec_data:
                    execution = json.loads(exec_data)
                    if query.lower() in execution.get('text', '').lower():
                        results.append(execution)

            return results[:n_results]

        except Exception as e:
            logger.error(f"❌ Failed to query governance history: {e}")
            return []
    
    def get_governance_stats(self) -> Dict[str, Any]:
        """Get governance memory statistics"""
        try:
            # Get counts from Redis
            event_count = self.redis_client.scard(f"{self.memory_key_prefix}:event_index")
            execution_count = self.redis_client.scard(f"{self.memory_key_prefix}:execution_index")

            # Simple stats for now
            return {
                "total_governance_events": event_count,
                "total_executions": execution_count,
                "successful_executions": 0,  # Would need to iterate to calculate
                "success_rate": 0.0,
                "daos_tracked": 6,  # From config
                "tokens_traded": 0
            }

        except Exception as e:
            logger.error(f"❌ Failed to get governance stats: {e}")
            return {}

# Test function
async def test_governance_memory():
    """Test governance memory functionality"""
    manager = GovernanceMemoryManager()
    
    # Test storing a governance event
    test_signal = {
        "signal_type": "governance_alpha",
        "dao": "jito",
        "token": "JTO",
        "title": "JIP-16: Increase Revenue Distribution to 75% Buyback Program",
        "sentiment_score": 0.88,
        "impact_score": 0.85,
        "proposal_type": "buyback",
        "strategy": "governance_alpha_hunter",
        "timestamp": time.time()
    }
    
    await manager.store_governance_event(test_signal)
    
    # Test querying
    results = manager.query_governance_history("JTO buyback proposal")
    print("=== GOVERNANCE MEMORY QUERY ===")
    for i, result in enumerate(results):
        print(f"Result {i+1}: {result.get('text', '')[:100]}...")

    # Test stats
    stats = manager.get_governance_stats()
    print("=== GOVERNANCE STATS ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_governance_memory())
