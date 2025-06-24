"""THE OVERMIND PROTOCOL - Mock MinionAgent Implementation
Temporary mock implementation for testing integration without full MinionAgent dependency.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Mock AgentConfig class."""
    name: str
    description: str
    model_id: str
    agent_type: str
    tools: List[str]

class MinionAgent:
    """Mock MinionAgent class for testing."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.tools = {}
        logger.info(f"🤖 Mock MinionAgent created: {config.name}")
    
    def register_tool(self, name: str, tool_func):
        """Register a tool with the agent."""
        self.tools[name] = tool_func
        logger.info(f"🔧 Tool registered: {name}")
    
    async def execute(self, prompt: str) -> Dict[str, Any]:
        """Mock execute method that returns a simple response."""
        logger.info(f"🧠 Mock agent {self.config.name} executing prompt: {prompt[:100]}...")
        
        # Simple mock response based on agent type
        if "market_data" in self.config.name:
            return {
                "analysis_type": "market_data",
                "price_data": {"SOL": 143.24, "BTC": 67420.0},
                "volume_24h": 1500000,
                "trend": "neutral",
                "confidence": 0.75,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        
        elif "social_sentiment" in self.config.name:
            return {
                "analysis_type": "social_sentiment",
                "sentiment_score": 0.65,
                "twitter_mentions": 1250,
                "telegram_activity": "high",
                "trending_keywords": ["bullish", "hodl", "moon"],
                "confidence": 0.68,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        
        elif "risk_analysis" in self.config.name:
            return {
                "analysis_type": "risk_analysis", 
                "risk_score": 0.45,
                "risk_level": "MEDIUM",
                "position_size_recommendation": 0.05,
                "stop_loss_recommendation": 135.0,
                "confidence": 0.82,
                "warnings": ["Medium volatility detected"],
                "timestamp": "2024-01-01T12:00:00Z"
            }
        
        elif "onchain_analysis" in self.config.name:
            return {
                "analysis_type": "onchain_analysis",
                "holder_concentration": 0.72,
                "liquidity_score": 0.78,
                "whale_activity": "moderate",
                "rug_pull_risk": "LOW",
                "confidence": 0.85,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        
        elif "overmind_brain_manager" in self.config.name:
            return {
                "decision": "BUY",
                "confidence": 0.78,
                "position_size": 0.05,
                "reasoning": "Mock analysis shows positive signals across market data, sentiment, and on-chain metrics",
                "risk_level": "MEDIUM",
                "execution_priority": "MEDIUM",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        
        else:
            return {
                "analysis_type": "generic",
                "result": "Mock agent response",
                "confidence": 0.5,
                "timestamp": "2024-01-01T12:00:00Z"
            }