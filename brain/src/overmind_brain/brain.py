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
from .strategy_manager import StrategyManager
from .exit_strategy_manager import ExitStrategyManager, Position, ExitDecision

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

            # Strategy Manager for intelligent strategy selection
            self.strategy_manager = StrategyManager()
            logger.info("✅ Strategy Manager initialized")

            # Exit Strategy Manager for position management
            self.exit_strategy_manager = ExitStrategyManager()
            logger.info("✅ Exit Strategy Manager initialized")

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
            # Check exit conditions for all active positions FIRST
            await self._check_exit_conditions()
            
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

            # Step 0: Strategy Selection and Validation
            strategy_matches = self.strategy_manager.select_and_validate_strategies(event_data)
            
            if not strategy_matches:
                logger.info(f"❌ No applicable strategies found for signal {event_data.get('signal_id', 'unknown')}. Ignoring.")
                return None
            
            logger.info(f"✅ {len(strategy_matches)} strategies qualified for {symbol}")

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

            # Step 3: Generate Strategy Context for AI
            signal = self.strategy_manager._parse_signal(event_data)
            strategy_context = self.strategy_manager.generate_strategy_context_for_ai(strategy_matches, signal)
            
            # Step 4: AI Decision Making with Strategy Context
            decision = await self.decision_engine.analyze_market_data(
                market_data=event_data,
                historical_context=historical_context,
                additional_context={
                    "market_analysis": asdict(market_analysis),
                    "strategy_context": strategy_context,
                    "qualified_strategies": [match.strategy_type.value for match in strategy_matches],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            # Step 5: Risk Assessment
            risk_assessment = await self.risk_analyzer.assess_risk(
                market_data=event_data,
                decision_data=asdict(decision),
                portfolio_data=event_data.get("portfolio_data"),
                historical_data=event_data.get("historical_data")
            )

            # Step 6: Apply risk adjustments
            decision = self._apply_risk_adjustments(decision, risk_assessment)

            # Step 7: Store experience in vector memory with strategy context
            await self.vector_memory.store_experience(
                situation=event_data,
                decision=asdict(decision),
                context={
                    "market_analysis": asdict(market_analysis),
                    "risk_assessment": asdict(risk_assessment),
                    "strategy_matches": [asdict(match) for match in strategy_matches],
                    "strategy_context": strategy_context
                }
            )

            logger.info(f"🎯 Decision generated: {decision.action} {symbol} "
                       f"(Confidence: {decision.confidence:.2f}, Risk: {risk_assessment.risk_level})")

            # Handle position tracking for BUY decisions
            if decision and decision.action == "BUY":
                await self._track_new_position(decision, strategy_matches)

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
                    "strategy_manager": "operational",
                    "exit_strategy_manager": "operational",
                    "helius_integration": "premium" if helius_status['api_key_configured'] else "basic",
                    "dragonfly_connection": "connected" if self.dragonfly else "disconnected"
                },
                "memory_stats": memory_stats,
                "helius_status": helius_status,
                "strategy_summary": self.strategy_manager.get_strategy_summary(),
                "positions_summary": await self.get_positions_summary(),
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

            # Strategy selection and validation
            strategy_matches = self.strategy_manager.select_and_validate_strategies(market_data)
            
            if not strategy_matches:
                logger.warning(f"⚠️ No applicable strategies found for {symbol}")
                return {
                    "symbol": symbol,
                    "error": "No applicable strategies found",
                    "strategy_matches": [],
                    "timestamp": datetime.utcnow().isoformat()
                }

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

            # Generate strategy context for AI
            signal = self.strategy_manager._parse_signal(market_data)
            strategy_context = self.strategy_manager.generate_strategy_context_for_ai(strategy_matches, signal)

            # Generate decision with strategy context
            decision = await self.decision_engine.analyze_market_data(
                market_data=market_data,
                historical_context=historical_context,
                additional_context={
                    "strategy_context": strategy_context,
                    "qualified_strategies": [match.strategy_type.value for match in strategy_matches]
                }
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
                "strategy_matches": [asdict(match) for match in strategy_matches],
                "strategy_context": strategy_context,
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

    async def _check_exit_conditions(self):
        """Check exit conditions for all active positions"""
        try:
            active_positions = self.exit_strategy_manager.active_positions.copy()
            
            for symbol, position in active_positions.items():
                # Fetch current market data for this symbol
                # In production, this would fetch real-time data
                # For now, we'll simulate or skip if no data available
                
                # Check if we have recent market data
                market_data = await self._get_current_market_data(symbol)
                if not market_data:
                    continue
                
                # Evaluate exit decision
                exit_decision = self.exit_strategy_manager.evaluate_exit_decision(symbol, market_data)
                
                if exit_decision and exit_decision.should_exit:
                    logger.info(f"🚪 Exit decision triggered for {symbol}: {exit_decision.exit_reason.value}")
                    
                    # Create SELL decision
                    sell_decision = TradingDecision(
                        symbol=symbol,
                        action="SELL",
                        confidence=exit_decision.confidence,
                        reasoning=f"EXIT: {exit_decision.reasoning}",
                        quantity=position.quantity * exit_decision.exit_percentage,
                        price_target=exit_decision.suggested_price,
                        risk_score=1.0 - exit_decision.confidence,  # Higher risk = lower confidence
                        timestamp=datetime.utcnow().isoformat()
                    )
                    
                    # Send sell decision
                    if await self.send_trading_decision(sell_decision):
                        # Remove position if fully exited
                        if exit_decision.exit_percentage >= 1.0:
                            self.exit_strategy_manager.remove_position(symbol)
                        logger.info(f"📤 Exit order sent for {symbol}")
                    
        except Exception as e:
            logger.error(f"❌ Error checking exit conditions: {e}")

    async def _get_current_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current market data for symbol (placeholder for real implementation)"""
        try:
            # In production, this would fetch from market data API
            # For now, return None to indicate no data available
            # Real implementation would call Helius API or market data source
            
            # Placeholder implementation - in real system this would be:
            # return await self.helius_client.get_token_data(symbol)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get market data for {symbol}: {e}")
            return None

    async def _track_new_position(self, decision: TradingDecision, strategy_matches: List) -> bool:
        """Track new position from BUY decision"""
        try:
            if not decision.quantity or decision.quantity <= 0:
                logger.warning(f"⚠️ Invalid quantity for position tracking: {decision.quantity}")
                return False
            
            # Extract strategy name from strategy matches
            entry_strategy = strategy_matches[0].strategy_type.value if strategy_matches else "unknown"
            
            # Create position object
            position = Position(
                symbol=decision.symbol,
                entry_price=decision.price_target or 0.0,  # Use price_target as entry price
                quantity=decision.quantity,
                entry_time=datetime.now(),
                entry_strategy=entry_strategy,
                stop_loss=decision.stop_loss,
                take_profit=None,  # Could be calculated based on strategy
                max_hold_time_hours=24  # Default 24 hours
            )
            
            # Calculate take profit based on strategy
            if decision.price_target:
                if entry_strategy == "memecoin_hunter":
                    position.take_profit = decision.price_target * 1.20  # 20% profit for memecoins
                elif entry_strategy == "soul_meteor":
                    position.take_profit = decision.price_target * 1.15  # 15% profit for established tokens
                else:
                    position.take_profit = decision.price_target * 1.12  # 12% default profit
            
            # Add position to exit manager
            success = self.exit_strategy_manager.add_position(position)
            
            if success:
                logger.info(f"📊 Position tracked: {decision.symbol} @ ${position.entry_price:.4f} "
                           f"(Strategy: {entry_strategy}, SL: ${position.stop_loss or 0:.4f}, "
                           f"TP: ${position.take_profit or 0:.4f})")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to track position for {decision.symbol}: {e}")
            return False

    async def get_positions_summary(self) -> Dict[str, Any]:
        """Get summary of all active positions"""
        try:
            return self.exit_strategy_manager.get_position_summary()
        except Exception as e:
            logger.error(f"❌ Failed to get positions summary: {e}")
            return {"error": str(e), "positions": {}}
