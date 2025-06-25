"""THE OVERMIND PROTOCOL - OVERMIND Brain Manager
Main agent manager using MinionAgent framework for coordinating specialized agents.
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis.asyncio as aioredis

# Try to import MinionAgent, fall back to mock if not available
try:
    from minion_agent import AgentConfig, MinionAgent
    print("🎯 Using real MinionAgent framework")
except ImportError:
    from .mock_minion_agent import AgentConfig, MinionAgent
    print("⚠️ Using mock MinionAgent for testing")

from .managed_agents import (
    create_market_data_agent,
    create_social_sentiment_agent,
    create_risk_analysis_agent,
    create_onchain_analysis_agent
)
from .strategy_manager import strategy_manager, StrategyMatch
from .strategy_config import strategy_config
# from .vector_memory import VectorMemory  # Disabled for testing

logger = logging.getLogger(__name__)

class OVERMINDBrainManager:
    """Main OVERMIND Brain Manager using MinionAgent framework."""
    
    def __init__(self, 
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 openai_api_key: Optional[str] = None):
        """Initialize the OVERMIND Brain Manager.
        
        Args:
            redis_host: DragonflyDB/Redis host
            redis_port: DragonflyDB/Redis port
            openai_api_key: OpenAI API key for LLM operations
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize main agent config
        self.config = AgentConfig(
            name="overmind_brain_manager",
            description="Main OVERMIND Brain Manager that coordinates specialized agents for comprehensive market analysis and trading decisions",
            model_id="deepseek/deepseek-reasoner",
            agent_type="CodeAgent",
            tools=[
                "coordinate_market_analysis",
                "execute_trading_decision_pipeline",
                "manage_agent_workflow",
                "synthesize_agent_results"
            ]
        )
        
        # Initialize the main MinionAgent
        self.main_agent = MinionAgent(self.config)
        
        # Initialize specialized agents
        self.market_data_agent = None
        self.social_sentiment_agent = None
        self.risk_analysis_agent = None
        self.onchain_analysis_agent = None
        
        # Initialize vector memory for long-term experience storage
        self.vector_memory = None
        
        # Redis connection for Dragonfly communication
        self.redis_client = None
        
        # Agent workflow state
        self.active_workflows = {}
        self.workflow_results = {}
        
        # Register tools with main agent
        self._register_main_agent_tools()
        
        logger.info("🧠 OVERMIND Brain Manager initialized")
        logger.info(f"📊 Strategy Configuration: {strategy_config.get_configuration_summary()}")
    
    async def initialize(self):
        """Initialize all components and connections."""
        try:
            # Initialize Redis connection to DragonflyDB  
            self.redis_client = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"✅ Connected to DragonflyDB at {self.redis_host}:{self.redis_port}")
            
            # Initialize vector memory (disabled for testing)
            # self.vector_memory = VectorMemory(
            #     collection_name="overmind_experiences",
            #     openai_api_key=self.openai_api_key
            # )
            # await self.vector_memory.initialize()
            self.vector_memory = None
            
            # Initialize specialized agents
            self.market_data_agent = create_market_data_agent()
            self.social_sentiment_agent = create_social_sentiment_agent()
            self.risk_analysis_agent = create_risk_analysis_agent()
            self.onchain_analysis_agent = create_onchain_analysis_agent()
            
            logger.info("🚀 OVERMIND Brain Manager fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OVERMIND Brain Manager: {e}")
            raise
    
    def _register_main_agent_tools(self):
        """Register tools with the main agent."""
        self.main_agent.register_tool("coordinate_market_analysis", self._coordinate_market_analysis)
        self.main_agent.register_tool("execute_trading_decision_pipeline", self._execute_trading_decision_pipeline)
        self.main_agent.register_tool("manage_agent_workflow", self._manage_agent_workflow)
        self.main_agent.register_tool("synthesize_agent_results", self._synthesize_agent_results)
    
    async def _coordinate_market_analysis(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate comprehensive market analysis using specialized agents.
        
        Args:
            signal_data: Raw market signal data
            
        Returns:
            Dict containing coordinated analysis results
        """
        logger.info(f"📊 Coordinating market analysis for {signal_data.get('symbol', 'unknown')}")
        
        # PHASE 1: STRATEGY SELECTION AND VALIDATION
        logger.info("🎯 Phase 1: Strategy Selection and Validation")
        qualified_strategies = strategy_manager.select_and_validate_strategies(signal_data)
        
        if not qualified_strategies:
            logger.warning("❌ No strategies qualified for this signal - returning HOLD recommendation")
            return {
                "strategy_analysis": {
                    "qualified_strategies": [],
                    "recommendation": "HOLD",
                    "reason": "No trading strategies met validation criteria for this signal"
                },
                "analysis_results": {},
                "decision": "HOLD"
            }
        
        # Log qualified strategies
        for strategy in qualified_strategies:
            logger.info(f"✅ Qualified: {strategy.strategy_type.value} (score: {strategy.match_score:.2f})")
        
        workflow_id = f"analysis_{datetime.utcnow().isoformat()}"
        self.active_workflows[workflow_id] = {
            "status": "running",
            "agents": [],
            "start_time": datetime.utcnow(),
            "signal_data": signal_data,
            "qualified_strategies": qualified_strategies
        }
        
        try:
            # Create analysis tasks for parallel execution
            tasks = []
            
            # Task 1: Market Data Analysis
            if self.market_data_agent:
                market_task = asyncio.create_task(
                    self.market_data_agent.fetch_token_data(signal_data.get("token_address", ""))
                )
                tasks.append(("market_data", market_task))
                self.active_workflows[workflow_id]["agents"].append("market_data_agent")
            
            # Task 2: Social Sentiment Analysis  
            if self.social_sentiment_agent and signal_data.get("symbol"):
                social_task = asyncio.create_task(
                    self.social_sentiment_agent.analyze_token_social_sentiment(
                        signal_data["symbol"], 
                        signal_data.get("token_address")
                    )
                )
                tasks.append(("social_sentiment", social_task))
                self.active_workflows[workflow_id]["agents"].append("social_sentiment_agent")
            
            # Task 3: On-Chain Analysis
            if self.onchain_analysis_agent and signal_data.get("token_address"):
                onchain_task = asyncio.create_task(
                    self.onchain_analysis_agent.comprehensive_onchain_analysis(
                        signal_data["token_address"]
                    )
                )
                tasks.append(("onchain_analysis", onchain_task))
                self.active_workflows[workflow_id]["agents"].append("onchain_analysis_agent")
            
            # Execute all tasks in parallel
            results = {}
            for task_name, task in tasks:
                try:
                    results[task_name] = await task
                    logger.info(f"✅ {task_name} completed")
                except Exception as e:
                    logger.error(f"❌ {task_name} failed: {e}")
                    results[task_name] = {"error": str(e)}
            
            # Store results for synthesis
            self.workflow_results[workflow_id] = results
            self.active_workflows[workflow_id]["status"] = "completed"
            
            return {
                "workflow_id": workflow_id,
                "strategy_analysis": {
                    "qualified_strategies": [
                        {
                            "strategy": s.strategy_type.value,
                            "score": s.match_score,
                            "reasoning": s.reasoning
                        } for s in qualified_strategies
                    ],
                    "top_strategy": qualified_strategies[0].strategy_type.value,
                    "strategy_context": strategy_manager.generate_strategy_context_for_ai(
                        qualified_strategies, 
                        strategy_manager._parse_signal(signal_data)
                    )
                },
                "analysis_results": results,
                "agents_used": self.active_workflows[workflow_id]["agents"],
                "completion_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Market analysis coordination failed: {e}")
            self.active_workflows[workflow_id]["status"] = "failed"
            return {
                "workflow_id": workflow_id,
                "error": str(e),
                "status": "failed"
            }
    
    async def _execute_trading_decision_pipeline(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete trading decision pipeline.
        
        Args:
            analysis_results: Results from market analysis coordination
            
        Returns:
            Dict containing trading decision and execution plan
        """
        logger.info("🎯 Executing trading decision pipeline")
        
        try:
            # Extract analysis data
            market_data = analysis_results.get("analysis_results", {}).get("market_data", {})
            social_data = analysis_results.get("analysis_results", {}).get("social_sentiment", {})
            onchain_data = analysis_results.get("analysis_results", {}).get("onchain_analysis", {})
            
            # Create decision context
            decision_context = {
                "market_analysis": market_data,
                "social_sentiment": social_data,
                "onchain_analysis": onchain_data,
                "analysis_workflow_id": analysis_results.get("workflow_id")
            }
            
            # Phase 1: Risk Analysis
            if self.risk_analysis_agent:
                risk_assessment = await self.risk_analysis_agent.comprehensive_risk_analysis(
                    market_data=market_data,
                    decision_data=decision_context
                )
                decision_context["risk_analysis"] = risk_assessment
            
            # Phase 2: Strategy-Aware Decision Synthesis using main agent
            strategy_context = analysis_results.get("strategy_analysis", {}).get("strategy_context", "")
            top_strategy = analysis_results.get("strategy_analysis", {}).get("top_strategy", "default")
            
            decision_prompt = f"""
            🎯 THE OVERMIND PROTOCOL - STRATEGY-AWARE TRADING DECISION
            
            {strategy_context}
            
            📊 AGENT ANALYSIS RESULTS:
            Market Data: {market_data}
            Social Sentiment: {social_data}  
            On-Chain Analysis: {onchain_data}
            Risk Assessment: {decision_context.get('risk_analysis', {})}
            
            🎯 SELECTED STRATEGY: {top_strategy}
            
            Based on the qualified strategy analysis and comprehensive agent data, make final trading decision following the strategy-specific criteria:
            
            Provide final decision in JSON format:
            {{
                "decision": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "position_size": percentage,
                "reasoning": "clear explanation based on strategy criteria",
                "risk_level": "LOW|MEDIUM|HIGH|EXTREME",
                "execution_priority": "LOW|MEDIUM|HIGH|URGENT",
                "strategy_used": "{top_strategy}",
                "strategy_confidence": 0.0-1.0
            }}
            """
            
            final_decision = await self.main_agent.execute(decision_prompt)
            
            # Phase 3: Store experience in vector memory
            if self.vector_memory:
                experience_id = await self.vector_memory.store_experience(
                    context=decision_context,
                    decision=final_decision,
                    timestamp=datetime.utcnow().isoformat()
                )
                final_decision["experience_id"] = experience_id
            
            return {
                "trading_decision": final_decision,
                "decision_context": decision_context,
                "pipeline_completion_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Trading decision pipeline failed: {e}")
            return {
                "error": str(e),
                "decision": "HOLD",
                "reasoning": "Pipeline execution failed - defaulting to HOLD for safety"
            }
    
    async def _manage_agent_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Manage complex agent workflows.
        
        Args:
            workflow_config: Configuration for the workflow
            
        Returns:
            Dict containing workflow execution results
        """
        logger.info(f"🔄 Managing agent workflow: {workflow_config.get('name', 'unnamed')}")
        
        # Implementation for complex workflow management
        # This would handle more sophisticated agent coordination patterns
        
        return {
            "workflow_status": "managed",
            "config": workflow_config
        }
    
    async def _synthesize_agent_results(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from multiple agents into coherent insights.
        
        Args:
            agent_results: Results from multiple specialized agents
            
        Returns:
            Dict containing synthesized insights
        """
        logger.info("🧩 Synthesizing agent results")
        
        synthesis_prompt = f"""
        Synthesize insights from multiple specialized agents into coherent trading intelligence:
        
        Agent Results: {agent_results}
        
        Provide synthesis in JSON format with:
        - Key insights from each agent
        - Conflicting signals and resolutions
        - Overall market assessment
        - Recommended actions
        - Risk considerations
        """
        
        try:
            synthesis = await self.main_agent.execute(synthesis_prompt)
            return synthesis
        except Exception as e:
            logger.error(f"❌ Agent result synthesis failed: {e}")
            return {"error": str(e)}
    
    async def process_market_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming market signal through the complete agent pipeline.
        
        Args:
            signal_data: Raw market signal from Rust executor
            
        Returns:
            Dict containing complete analysis and trading decision
        """
        logger.info(f"🚨 Processing market signal: {signal_data.get('type', 'unknown')}")
        
        try:
            # Phase 1: Coordinate market analysis
            analysis_results = await self._coordinate_market_analysis(signal_data)
            
            # Phase 2: Execute trading decision pipeline
            trading_decision = await self._execute_trading_decision_pipeline(analysis_results)
            
            # Phase 3: Prepare response for Rust executor
            response = {
                "signal_id": signal_data.get("signal_id"),
                "analysis_results": analysis_results,
                "trading_decision": trading_decision,
                "processing_time": datetime.utcnow().isoformat(),
                "brain_version": "v2.0-minion-agent"
            }
            
            # Send response back through DragonflyDB
            await self._send_decision_to_executor(response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Market signal processing failed: {e}")
            
            # Send safe default response
            error_response = {
                "signal_id": signal_data.get("signal_id"),
                "decision": "HOLD",
                "error": str(e),
                "reasoning": "Signal processing failed - defaulting to HOLD for safety"
            }
            
            await self._send_decision_to_executor(error_response)
            return error_response
    
    async def _send_decision_to_executor(self, decision_data: Dict[str, Any]):
        """Send trading decision back to Rust executor via DragonflyDB.
        
        Args:
            decision_data: Decision data to send
        """
        try:
            if self.redis_client:
                # Send to the channel that Rust executor is listening on
                await self.redis_client.publish(
                    "overmind:decisions",
                    json.dumps(decision_data)
                )
                logger.info(f"📤 Decision sent to executor: {decision_data.get('signal_id')}")
            else:
                logger.warning("⚠️ No Redis connection - decision not sent")
        except Exception as e:
            logger.error(f"❌ Failed to send decision to executor: {e}")
    
    async def start_listening(self):
        """Start listening for signals from Rust executor."""
        if not self.redis_client:
            raise RuntimeError("Redis client not initialized")
        
        logger.info("👂 Starting to listen for market signals...")
        
        # Subscribe to signals channel
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("overmind:signals")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        signal_data = json.loads(message["data"])
                        logger.info(f"📡 Received signal: {signal_data.get('type', 'unknown')}")
                        
                        # Process signal in background task
                        asyncio.create_task(self.process_market_signal(signal_data))
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Failed to decode signal data: {e}")
                    except Exception as e:
                        logger.error(f"❌ Error processing signal: {e}")
                        
        except asyncio.CancelledError:
            logger.info("🛑 Signal listening cancelled")
        finally:
            await pubsub.close()
    
    async def start(self):
        """Start the OVERMIND Brain Manager."""
        try:
            await self.initialize()
            await self.start_listening()
        except Exception as e:
            logger.error(f"❌ Failed to start OVERMIND Brain Manager: {e}")
            raise
    
    async def stop(self):
        """Stop the OVERMIND Brain Manager."""
        logger.info("🛑 Stopping OVERMIND Brain Manager...")
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("✅ OVERMIND Brain Manager stopped")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the brain manager."""
        return {
            "status": "running",
            "agents": {
                "market_data_agent": self.market_data_agent is not None,
                "social_sentiment_agent": self.social_sentiment_agent is not None,
                "risk_analysis_agent": self.risk_analysis_agent is not None,
                "onchain_analysis_agent": self.onchain_analysis_agent is not None
            },
            "connections": {
                "dragonfly_connected": self.redis_client is not None,
                "vector_memory_initialized": self.vector_memory is not None
            },
            "active_workflows": len(self.active_workflows),
            "workflow_results_cached": len(self.workflow_results)
        }

# Factory function for easy instantiation
def create_overmind_brain_manager(**kwargs) -> OVERMINDBrainManager:
    """Create and return a configured OVERMIND Brain Manager instance."""
    return OVERMINDBrainManager(**kwargs)