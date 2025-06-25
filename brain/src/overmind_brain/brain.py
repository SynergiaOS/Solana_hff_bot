"""THE OVERMIND PROTOCOL - AI Brain Implementation
Main orchestrator integrating all AI components for strategic decision making.
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import redis.asyncio as redis
from dataclasses import asdict

# Import OVERMIND components
from .vector_memory import VectorMemory
from .decision_engine import DecisionEngine, TradingDecision
from .risk_analyzer import RiskAnalyzer, RiskAssessment
from .market_analyzer import MarketAnalyzer, MarketAnalysis
from .helius_integration import helius_client, get_enhanced_token_data

# Import advanced AI components
try:
    from .advanced_ai_models import EnsembleLearning
    from .advanced_rag import AdvancedRAG
    from .sentiment_analyzer import SentimentAnalyzer
    ADVANCED_AI_AVAILABLE = True
except ImportError:
    ADVANCED_AI_AVAILABLE = False

logger = logging.getLogger(__name__)

class OVERMINDBrain:
    """Main AI Brain for THE OVERMIND PROTOCOL"""

    def __init__(self):
        """Initialize the OVERMIND Brain with all components"""
        # Initialize vector memory for long-term storage
        self.vector_memory = VectorMemory(
            collection_name=os.getenv("QDRANT_COLLECTION", "overmind_memory")
        )

        # Initialize enhanced decision engine with advanced AI
        self.decision_engine = DecisionEngine(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4-turbo",
            temperature=0.3,
            max_tokens=2000
        )

        # Initialize risk analyzer
        self.risk_analyzer = RiskAnalyzer()

        # Initialize market analyzer
        self.market_analyzer = MarketAnalyzer()

        # Connect to DragonflyDB for communication with Rust
        self.redis = redis.Redis(
            host=os.getenv("DRAGONFLY_HOST", "localhost"),
            port=int(os.getenv("DRAGONFLY_PORT", 6379)),
            password=os.getenv("DRAGONFLY_PASSWORD", None),
            db=int(os.getenv("DRAGONFLY_DB", 0)),
            decode_responses=True
        )

        # Initialize state
        self.is_running = False

        # Initialize communication channels
        self.market_events_queue = "overmind:market_events"
        self.trading_commands_queue = "overmind:commands"

        # Initialize Helius client
        from .helius_integration import helius_client
        self.helius_client = helius_client

        # Initialize DragonflyDB connection (alias for compatibility)
        self.dragonfly = self.redis

        # Advanced AI status
        self.advanced_ai_enabled = ADVANCED_AI_AVAILABLE

        if self.advanced_ai_enabled:
            logger.info("🧠 THE OVERMIND PROTOCOL Brain initialized with ADVANCED AI capabilities")
            logger.info("🚀 Enhanced features: Ensemble Learning, Advanced RAG, Sentiment Analysis")
        else:
            logger.info("🧠 THE OVERMIND PROTOCOL Brain initialized with standard AI capabilities")
            logger.info("💡 Install advanced AI dependencies for enhanced features")

    async def initialize(self):
        """Async initialization of components that require async setup"""
        try:
            # Test DragonflyDB connection
            await self.redis.ping()
            logger.info("✅ DragonflyDB connection established")

            # Vector memory collection is already initialized in __init__
            # Just verify it's working
            try:
                metrics = self.vector_memory.get_metrics()
                logger.info(f"✅ Vector memory ready - {metrics.get('total_points', 0)} memories stored")
            except Exception as e:
                logger.warning(f"⚠️ Vector memory check failed: {e}")

            # Test Helius connection
            helius_status = self.helius_client.get_status()
            if helius_status['api_key_configured']:
                logger.info("✅ Helius API connection ready")
            else:
                logger.warning("⚠️ Helius API key not configured - using basic mode")

            logger.info("🚀 THE OVERMIND PROTOCOL Brain fully initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize brain: {e}")
            return False

    async def shutdown(self):
        """Graceful shutdown of the brain"""
        try:
            logger.info("🛑 Shutting down THE OVERMIND PROTOCOL Brain...")

            # Stop the brain if running
            if self.is_running:
                await self.stop()

            # Close DragonflyDB connection
            if self.redis:
                await self.redis.close()
                logger.info("✅ DragonflyDB connection closed")

            logger.info("🛑 THE OVERMIND PROTOCOL Brain shutdown complete")

        except Exception as e:
            logger.error(f"❌ Error during brain shutdown: {e}")
        
        # Queue names for communication
        self.market_events_queue = os.getenv("OVERMIND_MARKET_EVENTS_QUEUE", "overmind:market_events")
        self.trading_commands_queue = os.getenv("OVERMIND_TRADING_COMMANDS_QUEUE", "overmind:trading_commands")
        self.execution_results_queue = os.getenv("OVERMIND_EXECUTION_RESULTS_QUEUE", "overmind:execution_results")
        
        logger.info("OVERMIND Brain initialized successfully")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics from VectorMemory"""
        try:
            # Get collection info from Qdrant
            collection_info = self.vector_memory.client.get_collection(
                collection_name=self.vector_memory.collection_name
            )

            return {
                "collection_name": self.vector_memory.collection_name,
                "total_memories": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.value,
                "status": "operational"
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"status": "error", "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check including memory status"""
        try:
            health_status = {
                "brain_status": "operational",
                "timestamp": datetime.now().isoformat(),
                "components": {}
            }

            # Check VectorMemory health
            try:
                memory_stats = self.get_memory_stats()
                health_status["components"]["vector_memory"] = {
                    "status": "operational",
                    "stats": memory_stats
                }
            except Exception as e:
                health_status["components"]["vector_memory"] = {
                    "status": "error",
                    "error": str(e)
                }

            # Check DecisionEngine health
            health_status["components"]["decision_engine"] = {
                "status": "operational" if self.decision_engine else "not_initialized"
            }

            # Check RiskAnalyzer health
            health_status["components"]["risk_analyzer"] = {
                "status": "operational" if self.risk_analyzer else "not_initialized"
            }

            # Check MarketAnalyzer health
            health_status["components"]["market_analyzer"] = {
                "status": "operational" if self.market_analyzer else "not_initialized"
            }

            # Check Redis connection
            try:
                await self.redis.ping()
                health_status["components"]["redis_connection"] = {
                    "status": "connected"
                }
            except Exception as e:
                health_status["components"]["redis_connection"] = {
                    "status": "disconnected",
                    "error": str(e)
                }

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "brain_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def process_market_event(self, event_data: Dict[str, Any]) -> Optional[TradingDecision]:
        """
        Process a market event and make a trading decision
        
        Args:
            event_data: Market event data from Rust executor
            
        Returns:
            Trading decision or None if no action should be taken
        """
        try:
            logger.info(f"Processing market event: {event_data.get('event_type', 'unknown')}")
            
            # 1. Analyze market data
            market_analysis = await self.market_analyzer.analyze_market(event_data)

            # 2. Retrieve relevant historical context from vector memory
            relevant_experiences = self.vector_memory.get_relevant_experiences(event_data, limit=3)

            # 3. Assess risk
            risk_assessment = await self.risk_analyzer.assess_risk(
                market_data=event_data,
                decision_data=asdict(market_analysis)
            )

            # 4. Make decision with context
            decision = await self.decision_engine.analyze_market_data(
                market_data=event_data,
                historical_context=relevant_experiences,
                additional_context={
                    "market_analysis": market_analysis,
                    "risk_assessment": risk_assessment
                }
            )
            
            # 5. Store experience in vector memory
            if decision:
                self.vector_memory.store_experience(event_data, asdict(decision))
            
            return decision
            
        except Exception as e:
            logger.error(f"Error processing market event: {str(e)}", exc_info=True)
            return None
    
    async def start(self):
        """Start the OVERMIND Brain processing loop"""
        logger.info("Starting OVERMIND Brain processing loop")
        
        try:
            while True:
                # Listen for market events from Rust
                try:
                    # Use brpop with timeout for non-blocking operation
                    result = await self.redis.brpop([self.market_events_queue], timeout=1)  # type: ignore
                    message = result if result else None
                except Exception as e:
                    logger.debug(f"Redis brpop timeout or error: {e}")
                    message = None

                if message:
                    _, event_json = message
                    event_data = json.loads(event_json)

                    # Process the event
                    decision = await self.process_market_event(event_data)

                    # Send decision back to Rust if action needed
                    if decision:
                        await self.redis.rpush(  # type: ignore
                            self.trading_commands_queue,
                            json.dumps(asdict(decision))
                        )
                        logger.info(f"Sent trading decision: {decision.action} for {decision.symbol}")

                # Small sleep to prevent CPU spinning
                await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            logger.info("OVERMIND Brain processing loop cancelled")
        except Exception as e:
            logger.error(f"Error in OVERMIND Brain processing loop: {str(e)}", exc_info=True)
            raise

    async def process_cycle(self):
        """Process one cycle of AI brain operations"""
        try:
            # Listen for market events from Rust executor
            market_event = await self.dragonfly.blpop(  # type: ignore
                ['overmind:market_events'],
                timeout=1
            )

            if market_event:
                # Parse market event
                event_data = json.loads(market_event[1])
                logger.info(f"📊 Processing market event: {event_data.get('symbol', 'unknown')}")

                # Process with AI brain
                decision = await self.process_market_event(event_data)

                # Send decision back to Rust executor
                if decision:
                    await self.send_trading_decision(decision)

        except redis.TimeoutError:
            # Normal timeout, continue loop
            pass
        except Exception as e:
            logger.error(f"❌ Brain cycle error: {e}")
            await asyncio.sleep(5)  # Wait before retrying

    async def process_market_event(self, event_data: Dict[str, Any]) -> Optional[TradingDecision]:
        """
        Process market event with full AI analysis pipeline

        Args:
            event_data: Market event data from Rust executor

        Returns:
            Trading decision or None
        """
        try:
            symbol = event_data.get("symbol", "unknown")
            logger.info(f"🧠 Analyzing market event for {symbol}")

            # Step 1: Market Analysis
            market_analysis = await self.market_analyzer.analyze_market(
                current_data=event_data,
                historical_data=event_data.get("historical_data"),
                additional_context=event_data.get("context")
            )

            # Step 2: Retrieve relevant experiences from vector memory
            query = f"Market event: {symbol} price: {event_data.get('price', 'unknown')}"
            historical_context = self.vector_memory.find_similar(
                query_text=query,
                limit=5
            )

            # Step 3: AI Decision Making
            decision = await self.decision_engine.analyze_market_data(
                market_data=event_data,
                historical_context=historical_context,
                additional_context={
                    "market_analysis": asdict(market_analysis),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

            # Step 4: Risk Assessment
            risk_assessment = await self.risk_analyzer.assess_risk(
                market_data=event_data,
                decision_data=asdict(decision),
                portfolio_data=event_data.get("portfolio_data"),
                historical_data=event_data.get("historical_data")
            )

            # Step 5: Apply risk adjustments
            decision = self._apply_risk_adjustments(decision, risk_assessment)

            # Step 6: Store experience in vector memory
            self.vector_memory.store_experience(
                market_data=event_data,
                decision=asdict(decision)
            )

            logger.info(f"🎯 Decision generated: {decision.action} {symbol} "
                       f"(Confidence: {decision.confidence:.2f}, Risk: {risk_assessment.risk_level})")

            return decision

        except Exception as e:
            logger.error(f"❌ Failed to process market event: {e}")
            return None

    def _apply_risk_adjustments(self,
                               decision: TradingDecision,
                               risk_assessment: RiskAssessment) -> TradingDecision:
        """Apply risk-based adjustments to trading decision"""

        # Adjust confidence based on risk
        decision.confidence *= risk_assessment.confidence_adjustment

        # Apply position size recommendation
        if hasattr(decision, 'quantity') and decision.quantity:
            decision.quantity *= risk_assessment.position_size_recommendation

        # Apply stop loss recommendation
        if risk_assessment.stop_loss_recommendation:
            decision.stop_loss = risk_assessment.stop_loss_recommendation

        # Override decision if risk is too high
        if risk_assessment.risk_level == "EXTREME":
            logger.warning(f"⚠️ EXTREME risk detected - overriding to HOLD")
            decision.action = "HOLD"
            decision.confidence *= 0.1  # Drastically reduce confidence
            decision.reasoning = f"RISK OVERRIDE: {decision.reasoning} | Risk level: EXTREME"

        return decision

    async def send_trading_decision(self, decision: TradingDecision) -> bool:
        """
        Send trading decision to Rust executor via DragonflyDB

        Args:
            decision: Trading decision to send

        Returns:
            Success status
        """
        try:
            # Only send decisions with sufficient confidence
            min_confidence = 0.6  # 60% minimum confidence

            if decision.confidence < min_confidence:
                logger.info(f"🔒 Decision confidence too low ({decision.confidence:.2f} < {min_confidence}) - not sending")
                return False

            # Prepare decision message
            decision_message = {
                "symbol": decision.symbol,
                "action": decision.action,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "quantity": decision.quantity,
                "price_target": decision.price_target,
                "stop_loss": decision.stop_loss,
                "risk_score": decision.risk_score,
                "timestamp": decision.timestamp,
                "source": "overmind_brain"
            }

            # Send to Rust executor
            await self.dragonfly.lpush(  # type: ignore
                'overmind:commands',
                json.dumps(decision_message)
            )

            logger.info(f"📤 Sent trading decision: {decision.action} {decision.symbol} "
                       f"(Confidence: {decision.confidence:.2f})")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to send trading decision: {e}")
            return False

    async def get_brain_status(self) -> Dict[str, Any]:
        """Get comprehensive brain status and statistics"""
        try:
            # Get memory statistics
            memory_stats = self.vector_memory.get_metrics()

            # Get Helius status
            helius_status = self.helius_client.get_status()

            # Get system status
            status = {
                "brain_running": self.is_running,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "components": {
                    "vector_memory": "operational",
                    "decision_engine": "operational",
                    "risk_analyzer": "operational",
                    "market_analyzer": "operational",
                    "helius_integration": "premium" if helius_status['api_key_configured'] else "basic",
                    "dragonfly_connection": "connected" if self.dragonfly else "disconnected"
                },
                "memory_stats": memory_stats,
                "helius_status": helius_status,
                "version": "1.0.0"
            }

            return status

        except Exception as e:
            logger.error(f"❌ Failed to get brain status: {e}")
            return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

    async def manual_analysis(self,
                             symbol: str,
                             market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform manual analysis for a specific symbol

        Args:
            symbol: Symbol to analyze
            market_data: Market data for analysis

        Returns:
            Complete analysis results
        """
        try:
            logger.info(f"🔍 Manual analysis requested for {symbol}")

            # Perform market analysis
            market_analysis = await self.market_analyzer.analyze_market(
                current_data=market_data
            )

            # Get historical context
            query = f"Symbol: {symbol} analysis"
            historical_context = self.vector_memory.find_similar(
                query_text=query,
                limit=3
            )

            # Generate decision
            decision = await self.decision_engine.analyze_market_data(
                market_data=market_data,
                historical_context=historical_context
            )

            # Assess risk
            risk_assessment = await self.risk_analyzer.assess_risk(
                market_data=market_data,
                decision_data=asdict(decision)
            )

            # Get detailed explanation
            explanation = await self.decision_engine.explain_decision(decision)

            # Send trading decision if it's actionable (BUY/SELL)
            command_sent = False
            if decision.action in ["BUY", "SELL"]:
                command_sent = await self.send_trading_decision(decision)
                if command_sent:
                    logger.info(f"📤 Trading command sent to executor: {decision.action} {symbol}")
                else:
                    logger.warning(f"⚠️ Trading command not sent (low confidence or error)")

            # Compile results
            results = {
                "symbol": symbol,
                "market_analysis": asdict(market_analysis),
                "decision": asdict(decision),
                "risk_assessment": asdict(risk_assessment),
                "explanation": explanation,
                "historical_context": historical_context,
                "command_sent": command_sent,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"✅ Manual analysis completed for {symbol}")
            return results

        except Exception as e:
            logger.error(f"❌ Manual analysis failed for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}

    async def update_experience_outcome(self,
                                       memory_id: str,
                                       outcome: Dict[str, Any]) -> bool:
        """
        Update a stored experience with outcome data

        Args:
            memory_id: ID of the memory to update
            outcome: Outcome data (profit/loss, success, etc.)

        Returns:
            Success status
        """
        try:
            # Update memory with outcome using the update_memory method
            success = self.vector_memory.update_memory(
                memory_id=memory_id,
                metadata={"outcome": outcome, "outcome_timestamp": datetime.now().isoformat()}
            )

            if success:
                logger.info(f"✅ Updated experience outcome: {memory_id}")
            else:
                logger.warning(f"⚠️ Failed to update experience: {memory_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Failed to update experience outcome: {e}")
            return False

    async def stop(self):
        """Stop the AI brain gracefully"""
        try:
            self.is_running = False

            # Close DragonflyDB connection
            if self.dragonfly:
                await self.dragonfly.close()

            logger.info("🛑 THE OVERMIND PROTOCOL Brain stopped gracefully")

        except Exception as e:
            logger.error(f"❌ Error during brain shutdown: {e}")

    async def emergency_stop(self):
        """Emergency stop - immediate shutdown"""
        logger.warning("🚨 EMERGENCY STOP - THE OVERMIND PROTOCOL Brain shutting down immediately")
        self.is_running = False

        try:
            if self.dragonfly:
                await self.dragonfly.close()
        except:
            pass  # Ignore errors during emergency stop
