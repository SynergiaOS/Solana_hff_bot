"""THE OVERMIND PROTOCOL - AI Brain Implementation
Main orchestrator integrating all AI components for strategic decision making.
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import redis.asyncio as redis
from dataclasses import asdict

# Import OVERMIND components
from .vector_memory import VectorMemory
from .decision_engine import DecisionEngine, TradingDecision
from .risk_analyzer import RiskAnalyzer, RiskAssessment
from .market_analyzer import MarketAnalyzer, MarketAnalysis
from .helius_integration import helius_client, get_enhanced_token_data

logger = logging.getLogger(__name__)

class OVERMINDBrain:
    """Main AI Brain for THE OVERMIND PROTOCOL

    Integrates all AI components:
    - Vector Memory: Long-term experience storage
    - Decision Engine: AI-powered decision making
    - Risk Analyzer: Comprehensive risk assessment
    - Market Analyzer: Market data analysis and pattern recognition
    """

    def __init__(self,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 openai_api_key: Optional[str] = None,
                 memory_collection: str = "overmind_memory"):
        """
        Initialize THE OVERMIND PROTOCOL AI Brain

        Args:
            redis_host: DragonflyDB/Redis host for communication
            redis_port: DragonflyDB/Redis port
            openai_api_key: OpenAI API key for LLM integration
            memory_collection: Vector memory collection name
        """
        self.is_running = False
        self.redis_host = redis_host
        self.redis_port = redis_port

        # Initialize AI components
        try:
            # Vector Memory for long-term learning
            self.vector_memory = VectorMemory(collection_name=memory_collection)
            logger.info("✅ Vector Memory initialized")

            # Decision Engine with LLM integration
            self.decision_engine = DecisionEngine(api_key=openai_api_key)
            logger.info("✅ Decision Engine initialized")

            # Risk Analyzer for comprehensive risk assessment
            self.risk_analyzer = RiskAnalyzer()
            logger.info("✅ Risk Analyzer initialized")

            # Market Analyzer for data analysis
            self.market_analyzer = MarketAnalyzer()
            logger.info("✅ Market Analyzer initialized")

            # Helius API integration for enhanced Solana data
            self.helius_client = helius_client
            helius_status = self.helius_client.get_status()
            if helius_status['api_key_configured']:
                logger.info("✅ Helius API Premium integration initialized")
            else:
                logger.warning("⚠️ Helius API key not configured - using basic features only")

            # DragonflyDB connection for communication with Rust executor
            self.dragonfly = None  # Will be initialized in start()

            logger.info("🧠 THE OVERMIND PROTOCOL Brain initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize OVERMIND Brain: {e}")
            raise

    async def start(self):
        """Start the AI brain and main processing loop"""
        try:
            self.is_running = True

            # Initialize DragonflyDB connection
            self.dragonfly = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )

            # Test connection
            await self.dragonfly.ping()
            logger.info(f"✅ Connected to DragonflyDB at {self.redis_host}:{self.redis_port}")

            logger.info("🚀 THE OVERMIND PROTOCOL Brain started")

            # Main brain loop
            while self.is_running:
                await self.process_cycle()
                await asyncio.sleep(1)  # 1 second cycle

        except Exception as e:
            logger.error(f"❌ Brain startup failed: {e}")
            self.is_running = False
            raise

    async def process_cycle(self):
        """Process one cycle of AI brain operations"""
        try:
            # Listen for market events from Rust executor
            market_event = await self.dragonfly.blpop(
                'overmind:market_events',
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
            historical_context = await self.vector_memory.similarity_search(
                query=query,
                top_k=5
            )

            # Step 3: AI Decision Making
            decision = await self.decision_engine.analyze_market_data(
                market_data=event_data,
                historical_context=historical_context,
                additional_context={
                    "market_analysis": asdict(market_analysis),
                    "timestamp": datetime.utcnow().isoformat()
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
            await self.vector_memory.store_experience(
                situation=event_data,
                decision=asdict(decision),
                context={
                    "market_analysis": asdict(market_analysis),
                    "risk_assessment": asdict(risk_assessment)
                }
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
            await self.dragonfly.lpush(
                'overmind:trading_commands',
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
            memory_stats = await self.vector_memory.get_memory_stats()

            # Get Helius status
            helius_status = self.helius_client.get_status()

            # Get system status
            status = {
                "brain_running": self.is_running,
                "timestamp": datetime.utcnow().isoformat(),
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
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

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
            historical_context = await self.vector_memory.similarity_search(
                query=query,
                top_k=3
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
                "timestamp": datetime.utcnow().isoformat()
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
            success = await self.vector_memory.update_experience_outcome(
                memory_id=memory_id,
                outcome=outcome
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
