"""THE OVERMIND PROTOCOL - AI Brain Implementation
Main orchestrator integrating all AI components for strategic decision making.
"""

import asyncio
import logging
import json
import os
import time
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
from .strategy_manager import StrategyManager
from .exit_strategy_manager import ExitStrategyManager, Position, ExitDecision
from .drawdown_guard import DrawdownGuard
from .market_regime_detector import MarketRegimeDetector, MarketRegime
from .strategy_profiles import StrategyRegimeMapper, MarketRegime as RegimeEnum
from .performance_analytics import PerformanceAnalyzer, PerformanceMetrics
from .performance_benchmarking import PerformanceBenchmarkingSystem
from .realtime_strategy_optimizer import RealtimeStrategyOptimizer
from .hedging_strategy_engine import HedgingStrategyEngine
from .correlation_analysis_system import CorrelationAnalysisSystem
from .dynamic_hedge_executor import DynamicHedgeExecutor
from .risk_neutralization_engine import RiskNeutralizationEngine

# Import advanced AI components
try:
    from .advanced_ai_models import EnsembleLearning
    from .advanced_rag import AdvancedRAG
    from .sentiment_analyzer import SentimentAnalyzer
    ADVANCED_AI_AVAILABLE = True
except ImportError:
    ADVANCED_AI_AVAILABLE = False

# Import advanced trading features
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
    from brain.drawdown_guard import DrawdownGuard
    from brain.feedback_scorer import AIFeedbackScorer
    from brain.add_to_winner import AddToWinnerSystem
    from brain.post_trade_orchestrator import PostTradeOrchestrator
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Advanced trading features not available: {e}")
    ADVANCED_FEATURES_AVAILABLE = False

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

        # Initialize Drawdown Guard - CRITICAL SAFETY COMPONENT
        try:
            self.drawdown_guard = DrawdownGuard(
                max_daily_loss_percentage=0.15,
                max_hourly_loss_percentage=0.05,
                emergency_threshold_percentage=0.20
            )
            logger.info("🛡️ Drawdown Guard initialized - Portfolio protection active")
        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to initialize Drawdown Guard: {e}")
            raise RuntimeError("Cannot start trading without Drawdown Guard protection")

        # Initialize Market Regime Detector - MARKET AWARENESS
        try:
            self.regime_detector = MarketRegimeDetector()
            self.strategy_mapper = StrategyRegimeMapper()
            self.current_market_regime = MarketRegime.NEUTRAL
            logger.info("📊 Market Regime Detector initialized - Market awareness active")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Market Regime Detector: {e}")
            # Non-critical - system can work without regime detection
            self.regime_detector = None
            self.strategy_mapper = None
            self.current_market_regime = MarketRegime.NEUTRAL

        # Initialize other Advanced Trading Features
        self.advanced_features_enabled = ADVANCED_FEATURES_AVAILABLE
        self.feedback_scorer = None
        self.add_to_winner = None
        self.post_trade_orchestrator = None
        self.performance_analyzer = None
        self.benchmarking_system = None
        self.realtime_optimizer = None
        self.hedging_strategy_engine = None
        self.correlation_analysis_system = None
        self.dynamic_hedge_executor = None
        self.risk_neutralization_engine = None

        if self.advanced_features_enabled:
            try:
                self.feedback_scorer = AIFeedbackScorer()
                self.add_to_winner = AddToWinnerSystem()
                self.post_trade_orchestrator = PostTradeOrchestrator()
                self.performance_analyzer = PerformanceAnalyzer()
                self.benchmarking_system = PerformanceBenchmarkingSystem()
                self.realtime_optimizer = RealtimeStrategyOptimizer()
                self.hedging_strategy_engine = HedgingStrategyEngine()
                self.correlation_analysis_system = CorrelationAnalysisSystem()
                self.dynamic_hedge_executor = DynamicHedgeExecutor()
                self.risk_neutralization_engine = RiskNeutralizationEngine()
                logger.info("🚀 Advanced Features initialized: Feedback Scorer, Add to Winner, Post-Trade Orchestrator, Performance Analytics, Real-time Optimizer, Hedging Layer")
            except Exception as e:
                logger.error(f"❌ Failed to initialize additional features: {e}")
                self.advanced_features_enabled = False

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

        # Start Post-Trade Intelligence if available
        if self.post_trade_orchestrator:
            asyncio.create_task(self.post_trade_orchestrator.orchestrator_main_loop())
            logger.info("🧠 Post-Trade Intelligence Orchestrator started")

        # Start Real-time Strategy Optimizer if available
        if self.realtime_optimizer:
            asyncio.create_task(self.realtime_optimizer.monitor_strategy_performance())
            logger.info("🔧 Real-time Strategy Optimizer started")

        # Start Hedging Layer if available
        if self.correlation_analysis_system:
            asyncio.create_task(self.correlation_analysis_system.start_correlation_monitoring())
            logger.info("📊 Correlation Analysis System started")

        if self.dynamic_hedge_executor:
            asyncio.create_task(self.dynamic_hedge_executor.start_hedge_execution_engine())
            logger.info("🔄 Dynamic Hedge Executor started")

        if self.risk_neutralization_engine:
            asyncio.create_task(self.risk_neutralization_engine.start_risk_neutralization_monitoring())
            logger.info("⚖️ Risk Neutralization Engine started")

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
            # STEP 1: DRAWDOWN GUARD - GLOBALNY BEZPIECZNIK (NAJWYŻSZY PRIORYTET)
            is_safe = self.drawdown_guard.check_portfolio_health()
            if not is_safe:
                if not self.is_emergency_stop_active():
                    await self.emergency_stop("Drawdown limit exceeded - Portfolio protection activated")

                # Przerwij obecny cykl i poczekaj, nie przetwarzaj nowych sygnałów
                logger.warning("⏸️ Trading cycle paused due to drawdown protection")
                await asyncio.sleep(60)  # Czekaj minutę przed następnym sprawdzeniem
                return

            # STEP 2: MARKET REGIME DETECTION - ŚWIADOMOŚĆ RYNKOWA
            if self.regime_detector:
                try:
                    regime_str = await self.regime_detector.detect_regime()
                    self.current_market_regime = MarketRegime(regime_str)
                    logger.info(f"📊 Current market regime: {self.current_market_regime.value}")
                except Exception as e:
                    logger.warning(f"⚠️ Market regime detection failed: {e}")
                    self.current_market_regime = MarketRegime.NEUTRAL

            # STEP 3: Przetwórz wyniki transakcji i zaktualizuj Drawdown Guard
            await self.process_execution_results()

            # STEP 4: Check exit conditions for all active positions
            await self._check_exit_conditions()

            # STEP 5: Listen for market events from Rust executor
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
            strategy = event_data.get("strategy", "unknown")
            confidence = event_data.get("confidence", 0.5)

            logger.info(f"🧠 Analyzing market event for {symbol} (Strategy: {strategy})")

            # Step 0: MARKET REGIME VALIDATION - Sprawdź czy strategia jest dozwolona w obecnej fazie rynku
            if self.strategy_mapper:
                validation_result = self.strategy_mapper.validate_strategy_signal(
                    strategy=strategy,
                    confidence=confidence,
                    current_regime=self.current_market_regime,
                    market_indicators=self.regime_detector.last_analysis.indicators.__dict__ if self.regime_detector and self.regime_detector.last_analysis else None
                )

                if not validation_result["allowed"]:
                    logger.info(f"🚫 Strategy {strategy} rejected by regime filter: {validation_result['reason']}")
                    return None

                # Użyj dostosowanej pewności
                confidence = validation_result["adjusted_confidence"]
                event_data["confidence"] = confidence

                logger.info(f"✅ Strategy {strategy} validated for {self.current_market_regime.value} regime (Confidence: {confidence:.2f})")

            # Step 1: Strategy Selection and Validation (legacy system)
            # TODO: Migrate to new regime-based validation
            try:
                strategy_matches = self.strategy_manager.select_and_validate_strategies(event_data)

                if not strategy_matches:
                    logger.info(f"❌ No applicable strategies found for signal {event_data.get('signal_id', 'unknown')}. Ignoring.")
                    return None

                logger.info(f"✅ {len(strategy_matches)} strategies qualified for {symbol}")
            except AttributeError:
                # strategy_manager nie istnieje - używamy nowej walidacji regime-based
                logger.info(f"✅ Using regime-based validation for {symbol}")

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

            # Step 3: Generate Strategy Context for AI
            signal = self.strategy_manager._parse_signal(event_data)
            strategy_context = self.strategy_manager.generate_strategy_context_for_ai(strategy_matches, signal)
            
            # Step 4: AI Decision Making with Strategy Context
            decision = await self.decision_engine.analyze_market_data(
                market_data=event_data,
                historical_context=historical_context,
                additional_context={
                    "market_analysis": asdict(market_analysis),
                    "timestamp": datetime.now(timezone.utc).isoformat()
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

            # Step 6: Store experience in vector memory
            self.vector_memory.store_experience(
                market_data=event_data,
                decision=asdict(decision)
            )

            # Step 7: Enhanced feedback scoring for AI learning
            if self.advanced_features_enabled and self.feedback_scorer:
                await self._process_decision_feedback(decision, event_data, risk_assessment)

            # Step 8: Hedging Analysis (if hedging layer is available)
            if self.hedging_strategy_engine and decision and decision.action in ["BUY", "SELL"]:
                await self._analyze_hedging_opportunities(decision, event_data)

            logger.info(f"🎯 Decision generated: {decision.action} {symbol} "
                       f"(Confidence: {decision.confidence:.2f}, Risk: {risk_assessment.risk_level})")

            # Handle position tracking for BUY decisions
            if decision and decision.action == "BUY":
                await self._track_new_position(decision, strategy_matches)

            return decision

        except Exception as e:
            logger.error(f"❌ Failed to process market event: {e}")
            return None

    async def _analyze_hedging_opportunities(self, decision: TradingDecision, event_data: Dict[str, Any]):
        """Analyze hedging opportunities for the trading decision"""
        try:
            if not self.hedging_strategy_engine:
                return

            logger.debug(f"🛡️ Analyzing hedging opportunities for {decision.symbol}")

            # Get current portfolio positions
            portfolio_positions = await self._get_portfolio_positions()

            # Analyze hedging opportunities
            hedge_recommendations = await self.hedging_strategy_engine.analyze_hedging_opportunities(portfolio_positions)

            if hedge_recommendations:
                logger.info(f"🎯 Found {len(hedge_recommendations)} hedging opportunities")

                # Execute high-priority hedge recommendations
                for recommendation in hedge_recommendations[:2]:  # Top 2 recommendations
                    if recommendation.urgency > 0.7 and self.dynamic_hedge_executor:
                        execution_id = await self.dynamic_hedge_executor.execute_hedge_recommendation(
                            asdict(recommendation)
                        )
                        if execution_id:
                            logger.info(f"✅ Hedge execution initiated: {execution_id}")

        except Exception as e:
            logger.error(f"❌ Error analyzing hedging opportunities: {e}")

    async def _get_portfolio_positions(self) -> Dict[str, Any]:
        """Get current portfolio positions for hedging analysis"""
        try:
            # This would typically get positions from the portfolio manager
            # For now, return a simplified structure
            positions = {}

            # Try to get positions from Redis
            try:
                positions_key = "overmind:active_positions"
                positions_str = self.redis_client.get(positions_key)

                if positions_str:
                    position_symbols = json.loads(positions_str)

                    for symbol in position_symbols:
                        position_key = f"overmind:position:{symbol}"
                        position_str = self.redis_client.get(position_key)

                        if position_str:
                            position = json.loads(position_str)
                            positions[symbol] = position
            except Exception as e:
                logger.debug(f"Could not get positions from Redis: {e}")

            return positions

        except Exception as e:
            logger.error(f"❌ Error getting portfolio positions: {e}")
            return {}

    async def _get_hedging_status(self) -> Dict[str, Any]:
        """Get hedging layer status"""
        try:
            hedging_status = {
                "hedging_strategy_engine": "disabled",
                "correlation_analysis_system": "disabled",
                "dynamic_hedge_executor": "disabled",
                "risk_neutralization_engine": "disabled"
            }

            if self.hedging_strategy_engine:
                hedging_status["hedging_strategy_engine"] = "operational"
                try:
                    engine_status = await self.hedging_strategy_engine.get_hedging_status()
                    hedging_status["hedging_engine_details"] = engine_status
                except:
                    pass

            if self.correlation_analysis_system:
                hedging_status["correlation_analysis_system"] = "operational"
                try:
                    correlation_status = await self.correlation_analysis_system.get_correlation_analysis_status()
                    hedging_status["correlation_details"] = correlation_status
                except:
                    pass

            if self.dynamic_hedge_executor:
                hedging_status["dynamic_hedge_executor"] = "operational"
                try:
                    executor_status = await self.dynamic_hedge_executor.get_hedge_execution_status()
                    hedging_status["executor_details"] = executor_status
                except:
                    pass

            if self.risk_neutralization_engine:
                hedging_status["risk_neutralization_engine"] = "operational"
                try:
                    risk_status = await self.risk_neutralization_engine.get_risk_neutralization_status()
                    hedging_status["risk_neutralization_details"] = risk_status
                except:
                    pass

            return hedging_status

        except Exception as e:
            logger.error(f"❌ Error getting hedging status: {e}")
            return {"error": str(e)}

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
                    "strategy_manager": "operational",
                    "exit_strategy_manager": "operational",
                    "post_trade_intelligence": "operational" if self.post_trade_orchestrator else "disabled",
                    "performance_analytics": "operational" if self.performance_analyzer else "disabled",
                    "benchmarking_system": "operational" if self.benchmarking_system else "disabled",
                    "realtime_optimizer": "operational" if self.realtime_optimizer else "disabled",
                    "hedging_strategy_engine": "operational" if self.hedging_strategy_engine else "disabled",
                    "correlation_analysis_system": "operational" if self.correlation_analysis_system else "disabled",
                    "dynamic_hedge_executor": "operational" if self.dynamic_hedge_executor else "disabled",
                    "risk_neutralization_engine": "operational" if self.risk_neutralization_engine else "disabled",
                    "helius_integration": "premium" if helius_status['api_key_configured'] else "basic",
                    "dragonfly_connection": "connected" if self.dragonfly else "disconnected"
                },
                "memory_stats": memory_stats,
                "helius_status": helius_status,
                "hedging_status": await self._get_hedging_status(),
                "positions_summary": await self.get_positions_summary(),
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
            historical_context = self.vector_memory.find_similar(
                query_text=query,
                limit=3
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

    async def _check_drawdown_protection(self):
        """Check drawdown protection and trigger emergency measures if needed"""
        try:
            if not self.drawdown_guard:
                return

            # Get current portfolio metrics
            metrics = await self.drawdown_guard.get_current_portfolio_metrics()

            if not metrics:
                return

            # Check emergency stop condition
            if (metrics.current_drawdown >= self.drawdown_guard.config['emergency_stop_drawdown']
                and not self.drawdown_guard.emergency_stop_triggered):
                logger.critical("🚨 DRAWDOWN GUARD: Emergency stop triggered!")
                await self.drawdown_guard.trigger_emergency_stop(metrics)

                # Set emergency stop in brain
                await self.emergency_stop()

            # Check position reduction condition
            elif (metrics.current_drawdown >= self.drawdown_guard.config['position_reduction_threshold']
                  and not self.drawdown_guard.drawdown_mode):
                logger.warning("⚠️ DRAWDOWN GUARD: Reducing position sizes")
                await self.drawdown_guard.reduce_position_sizes(metrics)

            # Check recovery conditions
            await self.drawdown_guard.check_recovery_conditions(metrics)

        except Exception as e:
            logger.error(f"❌ Error in drawdown protection: {e}")

    async def _process_decision_feedback(self, decision: TradingDecision, event_data: Dict[str, Any], risk_assessment):
        """Process decision feedback for AI learning"""
        try:
            if not self.feedback_scorer:
                return

            # Create execution result for feedback analysis
            execution_result = {
                'transaction_id': f"decision_{decision.symbol}_{int(time.time())}",
                'symbol': decision.symbol,
                'action': decision.action,
                'quantity': decision.quantity,
                'execution_price': decision.price_target or event_data.get('price', 0),
                'confidence': decision.confidence,
                'strategy': event_data.get('strategy', 'AI_DECISION'),
                'timestamp': time.time(),
                'estimated_profit': 0,  # Will be updated later
                'hold_time': 300,  # Default 5 minutes
                'market_conditions': {
                    'volatility': risk_assessment.volatility if hasattr(risk_assessment, 'volatility') else 0.5,
                    'sentiment': event_data.get('sentiment', 0.5),
                    'volume': event_data.get('volume', 0.5)
                }
            }

            # Store for later feedback analysis
            await self.redis.lpush('overmind:execution_results', json.dumps(execution_result))  # type: ignore

            logger.info(f"📊 Decision feedback prepared for {decision.symbol}")

        except Exception as e:
            logger.error(f"❌ Error processing decision feedback: {e}")

    async def process_execution_results(self):
        """
        Przetwarza wyniki wykonanych transakcji i aktualizuje Drawdown Guard
        Ta metoda powinna być wywoływana regularnie w głównej pętli
        """
        try:
            # Pobierz najnowsze wyniki transakcji z kolejki
            execution_results = await self.redis.lrange('overmind:execution_results', 0, 9)  # type: ignore

            if not execution_results:
                return

            for result_str in execution_results:
                result = json.loads(result_str)

                # Sprawdź czy to jest nowy wynik (nie przetworzony wcześniej)
                transaction_id = result.get('transaction_id', '')
                if not transaction_id:
                    continue

                # Sprawdź czy już przetworzono ten wynik
                processed_key = f"processed_tx:{transaction_id}"
                already_processed = await self.redis.get(processed_key)  # type: ignore

                if already_processed:
                    continue

                # Pobierz P&L z transakcji
                pnl_change = result.get('estimated_profit', 0.0)

                if pnl_change != 0.0:
                    # Aktualizuj Drawdown Guard
                    self.drawdown_guard.update_pnl(pnl_change)

                    logger.info(f"📊 Drawdown Guard updated with transaction: {transaction_id}")
                    logger.info(f"   P&L: ${pnl_change:.4f}")
                    logger.info(f"   Daily P&L: ${self.drawdown_guard.daily_pnl:.4f}")
                    logger.info(f"   Hourly P&L: ${self.drawdown_guard.hourly_pnl:.4f}")

                # Oznacz jako przetworzony (ważne 1 godzinę)
                await self.redis.setex(processed_key, 3600, "1")  # type: ignore

        except Exception as e:
            logger.error(f"❌ Error processing execution results: {e}")

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
