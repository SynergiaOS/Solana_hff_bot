"""THE OVERMIND PROTOCOL - Decision Engine
AI-powered decision making using LLM integration and multi-agent reasoning.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
import openai
from openai import AsyncOpenAI
import os
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Import new advanced AI components
try:
    from .advanced_ai_models import (
        EnsembleLearning, OpenAIModel, AnthropicModel, DeepSeekModel,
        ModelType, EnsembleDecision
    )
    from .advanced_rag import AdvancedRAG, ChromaVectorStore, EmbeddingModel, DocumentType
    from .sentiment_analyzer import SentimentAnalyzer, MarketSentimentSignal
    ADVANCED_AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Advanced AI components not available: {e}")
    ADVANCED_AI_AVAILABLE = False

@dataclass
class TradingDecision:
    """Structured trading decision"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 to 1.0
    reasoning: str
    quantity: Optional[float] = None
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    risk_score: Optional[float] = None
    timestamp: Optional[str] = None

class DecisionEngine:
    """AI-powered decision engine for THE OVERMIND PROTOCOL"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-4",
                 temperature: float = 0.1,
                 max_tokens: int = 1000):
        """
        Initialize decision engine with OpenAI integration
        
        Args:
            api_key: OpenAI API key (or from environment)
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens for response
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("OpenAI API key required for decision engine")
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)

        # Initialize advanced AI components
        self.ensemble_learning = None
        self.advanced_rag = None
        self.sentiment_analyzer = None
        self.use_advanced_ai = ADVANCED_AI_AVAILABLE

        # Decision templates and prompts
        self.system_prompt = self._create_system_prompt()

        logger.info(f"🧠 Decision Engine initialized with model: {model}")

        # Initialize advanced components if available
        if self.use_advanced_ai:
            asyncio.create_task(self._initialize_advanced_components())

    async def _initialize_advanced_components(self):
        """Initialize advanced AI components"""
        try:
            if not ADVANCED_AI_AVAILABLE:
                return

            # Initialize AI models for ensemble learning
            models = []

            # OpenAI model
            if os.getenv("OPENAI_API_KEY"):
                openai_model = OpenAIModel(ModelType.GPT4_TURBO, {"temperature": 0.3})
                if await openai_model.initialize():
                    models.append(openai_model)

            # Anthropic model
            if os.getenv("ANTHROPIC_API_KEY"):
                anthropic_model = AnthropicModel(ModelType.CLAUDE_3_5_SONNET, {"temperature": 0.3})
                if await anthropic_model.initialize():
                    models.append(anthropic_model)

            # DeepSeek model
            if os.getenv("DEEPSEEK_API_KEY"):
                deepseek_model = DeepSeekModel(ModelType.DEEPSEEK_V3, {"temperature": 0.3})
                if await deepseek_model.initialize():
                    models.append(deepseek_model)

            # Initialize ensemble learning if we have models
            if models:
                self.ensemble_learning = EnsembleLearning(models, {})
                logger.info(f"🤖 Ensemble learning initialized with {len(models)} models")

            # Initialize advanced RAG
            vector_store = ChromaVectorStore()
            embedding_model = EmbeddingModel()

            if await vector_store.initialize() and await embedding_model.initialize():
                self.advanced_rag = AdvancedRAG(vector_store, embedding_model)
                await self.advanced_rag.initialize()
                logger.info("📚 Advanced RAG system initialized")

            # Initialize sentiment analyzer
            sentiment_config = {
                "twitter_api_key": os.getenv("TWITTER_API_KEY"),
                "reddit_client_id": os.getenv("REDDIT_CLIENT_ID"),
                "news_api_key": os.getenv("NEWS_API_KEY")
            }

            self.sentiment_analyzer = SentimentAnalyzer(sentiment_config)
            if await self.sentiment_analyzer.initialize():
                logger.info("📊 Sentiment analyzer initialized")

        except Exception as e:
            logger.error(f"Failed to initialize advanced components: {e}")
            self.use_advanced_ai = False

    def _create_system_prompt(self) -> str:
        """Create system prompt for AI decision making"""
        return """You are THE OVERMIND PROTOCOL AI Brain, an advanced trading decision system.

Your role is to analyze market data and make intelligent trading decisions based on:
1. Current market conditions
2. Historical patterns and experiences
3. Risk assessment
4. Technical and fundamental analysis

DECISION FRAMEWORK:
- BUY: Strong positive signals, good risk/reward ratio
- SELL: Strong negative signals, risk mitigation needed
- HOLD: Uncertain conditions, wait for clearer signals

CONFIDENCE LEVELS:
- 0.9-1.0: Extremely confident, strong signals
- 0.7-0.8: High confidence, good signals
- 0.5-0.6: Moderate confidence, mixed signals
- 0.3-0.4: Low confidence, weak signals
- 0.0-0.2: Very low confidence, avoid trading

Always provide:
1. Clear action (BUY/SELL/HOLD)
2. Confidence score (0.0-1.0)
3. Detailed reasoning
4. Risk assessment

Be conservative and prioritize capital preservation."""

    async def analyze_market_data(self,
                                market_data: Dict[str, Any],
                                historical_context: Optional[List[Dict[str, Any]]] = None,
                                additional_context: Optional[Dict[str, Any]] = None) -> TradingDecision:
        """
        Enhanced analyze market data with ensemble learning and advanced AI

        Args:
            market_data: Current market data
            historical_context: Historical experiences from vector memory
            additional_context: Additional context data

        Returns:
            Trading decision
        """
        try:
            # Check for demo/mock mode
            if os.getenv("OPENAI_API_KEY") in ["demo-mode", "mock", "test"] or os.getenv("MOCK_OPENAI_RESPONSES") == "true":
                logger.info("🎭 Running in DEMO mode - generating mock AI decision")
                return self._generate_mock_decision(market_data)

            # Use advanced AI if available
            if self.use_advanced_ai and self.ensemble_learning:
                return await self._analyze_with_ensemble(market_data, historical_context, additional_context)

            # Fallback to standard analysis
            return await self._analyze_with_standard_ai(market_data, historical_context, additional_context)
            
            # Get AI decision
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            decision_data = json.loads(response.choices[0].message.content)
            
            # Create structured decision
            decision = TradingDecision(
                symbol=market_data.get("symbol", "unknown"),
                action=decision_data.get("action", "HOLD").upper(),
                confidence=float(decision_data.get("confidence", 0.5)),
                reasoning=decision_data.get("reasoning", "No reasoning provided"),
                quantity=decision_data.get("quantity"),
                price_target=decision_data.get("price_target"),
                stop_loss=decision_data.get("stop_loss"),
                risk_score=decision_data.get("risk_score"),
                timestamp=datetime.utcnow().isoformat()
            )
            
            # Validate decision
            decision = self._validate_decision(decision)
            
            logger.info(f"🎯 Decision: {decision.action} {decision.symbol} "
                       f"(Confidence: {decision.confidence:.2f})")
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ Decision analysis failed: {e}")
            # Return safe default decision
            return TradingDecision(
                symbol=market_data.get("symbol", "unknown"),
                action="HOLD",
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                timestamp=datetime.utcnow().isoformat()
            )
    
    def _create_analysis_prompt(self,
                              market_data: Dict[str, Any],
                              historical_context: Optional[List[Dict[str, Any]]] = None,
                              additional_context: Optional[Dict[str, Any]] = None) -> str:
        """Create analysis prompt for LLM"""
        
        prompt_parts = [
            "MARKET ANALYSIS REQUEST",
            "=" * 50,
            "",
            "CURRENT MARKET DATA:",
            json.dumps(market_data, indent=2),
            ""
        ]
        
        # Add historical context
        if historical_context:
            prompt_parts.extend([
                "HISTORICAL CONTEXT (Similar Past Experiences):",
                ""
            ])
            for i, context in enumerate(historical_context[:3]):  # Limit to top 3
                prompt_parts.append(f"Experience {i+1}:")
                prompt_parts.append(f"- Content: {context.get('content', 'N/A')}")
                prompt_parts.append(f"- Similarity: {context.get('similarity', 0.0):.2f}")
                prompt_parts.append("")
        
        # Add additional context
        if additional_context:
            prompt_parts.extend([
                "ADDITIONAL CONTEXT:",
                json.dumps(additional_context, indent=2),
                ""
            ])
        
        prompt_parts.extend([
            "REQUIRED OUTPUT FORMAT (JSON):",
            "{",
            '  "action": "BUY|SELL|HOLD",',
            '  "confidence": 0.0-1.0,',
            '  "reasoning": "Detailed explanation of decision",',
            '  "quantity": optional_trade_size,',
            '  "price_target": optional_target_price,',
            '  "stop_loss": optional_stop_loss_price,',
            '  "risk_score": 0.0-1.0',
            "}",
            "",
            "Analyze the data and provide your trading decision:"
        ])
        
        return "\n".join(prompt_parts)

    def _generate_mock_decision(self, market_data: Dict[str, Any]) -> TradingDecision:
        """Generate mock AI decision for demo/testing purposes"""

        symbol = market_data.get("symbol", "UNKNOWN")
        price = market_data.get("price", 100.0)
        volume = market_data.get("volume", 1000000)
        additional_data = market_data.get("additional_data", {})

        # Simulate intelligent decision based on market data
        trend = additional_data.get("trend", "neutral")
        volatility = float(additional_data.get("volatility", 0.02))
        sentiment = additional_data.get("social_sentiment", "neutral")

        logger.info(f"🎭 MOCK AI analyzing: trend={trend}, volatility={volatility}, sentiment={sentiment}")

        # Mock decision logic - more aggressive for testing
        if trend == "bullish" and sentiment in ["positive", "neutral"] and volatility < 0.1:
            action = "BUY"
            confidence = 0.75
            reasoning = f"🎭 DEMO: Bullish trend detected with {sentiment} sentiment and manageable volatility ({volatility:.3f}). Executing BUY for {symbol}."
            quantity = min(price * 0.01, 1.0)  # 1% of price or max 1 SOL
            price_target = price * 1.05  # 5% target
            stop_loss = price * 0.97  # 3% stop loss
        elif trend == "bearish" or volatility > 0.08:
            action = "SELL"
            confidence = 0.65
            reasoning = f"🎭 DEMO: Bearish conditions or high volatility ({volatility:.3f}) detected. Executing SELL for {symbol}."
            quantity = min(price * 0.005, 0.5)  # 0.5% of price or max 0.5 SOL
            price_target = price * 0.95  # 5% down target
            stop_loss = price * 1.02  # 2% stop loss
        elif trend == "neutral" and volatility < 0.03:
            action = "BUY"  # Changed from HOLD to BUY for testing
            confidence = 0.60
            reasoning = f"🎭 DEMO: Neutral trend with low volatility ({volatility:.3f}). Small position BUY for {symbol}."
            quantity = min(price * 0.005, 0.3)  # Small position
            price_target = price * 1.02  # 2% target
            stop_loss = price * 0.98  # 2% stop loss
        else:
            action = "HOLD"
            confidence = 0.55
            reasoning = f"🎭 DEMO: Mixed signals for {symbol}. Trend: {trend}, Sentiment: {sentiment}, Volatility: {volatility:.3f}. Conservative HOLD."
            quantity = None
            price_target = None
            stop_loss = None

        return TradingDecision(
            symbol=symbol,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            quantity=quantity,
            price_target=price_target,
            stop_loss=stop_loss,
            risk_score=volatility,  # Use volatility as risk proxy
            timestamp=datetime.utcnow().isoformat()
        )

    def _validate_decision(self, decision: TradingDecision) -> TradingDecision:
        """Validate and sanitize decision"""
        
        # Validate action
        valid_actions = ["BUY", "SELL", "HOLD"]
        if decision.action not in valid_actions:
            logger.warning(f"⚠️ Invalid action '{decision.action}', defaulting to HOLD")
            decision.action = "HOLD"
        
        # Validate confidence
        decision.confidence = max(0.0, min(1.0, decision.confidence))
        
        # Validate risk score
        if decision.risk_score is not None:
            decision.risk_score = max(0.0, min(1.0, decision.risk_score))
        
        # Ensure reasoning exists
        if not decision.reasoning or len(decision.reasoning.strip()) < 10:
            decision.reasoning = "Insufficient reasoning provided"
            decision.confidence = min(decision.confidence, 0.3)
        
        return decision
    
    async def multi_agent_consensus(self, 
                                  market_data: Dict[str, Any],
                                  num_agents: int = 3) -> TradingDecision:
        """
        Get consensus decision from multiple AI agents
        
        Args:
            market_data: Market data to analyze
            num_agents: Number of agents to consult
            
        Returns:
            Consensus trading decision
        """
        try:
            # Get decisions from multiple agents
            decisions = []
            
            for i in range(num_agents):
                # Vary temperature slightly for each agent
                temp_variation = self.temperature + (i * 0.05)
                
                # Create agent-specific prompt
                agent_prompt = f"""You are Agent {i+1} of {num_agents} in THE OVERMIND PROTOCOL.
                
Analyze this market data independently and provide your decision:

{json.dumps(market_data, indent=2)}

Consider your unique perspective and provide a JSON response."""
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": agent_prompt}
                    ],
                    temperature=temp_variation,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                decision_data = json.loads(response.choices[0].message.content)
                decisions.append(decision_data)
            
            # Calculate consensus
            consensus = self._calculate_consensus(decisions, market_data)
            
            logger.info(f"🤝 Multi-agent consensus: {consensus.action} "
                       f"(Confidence: {consensus.confidence:.2f})")
            
            return consensus
            
        except Exception as e:
            logger.error(f"❌ Multi-agent consensus failed: {e}")
            # Fallback to single agent
            return await self.analyze_market_data(market_data)
    
    def _calculate_consensus(self, 
                           decisions: List[Dict[str, Any]], 
                           market_data: Dict[str, Any]) -> TradingDecision:
        """Calculate consensus from multiple agent decisions"""
        
        # Count actions
        action_votes = {"BUY": 0, "SELL": 0, "HOLD": 0}
        confidences = []
        reasonings = []
        
        for decision in decisions:
            action = decision.get("action", "HOLD").upper()
            if action in action_votes:
                action_votes[action] += 1
            
            confidences.append(decision.get("confidence", 0.5))
            reasonings.append(decision.get("reasoning", ""))
        
        # Determine consensus action
        consensus_action = max(action_votes, key=action_votes.get)
        
        # Calculate consensus confidence
        avg_confidence = sum(confidences) / len(confidences)
        
        # Adjust confidence based on agreement level
        max_votes = max(action_votes.values())
        agreement_ratio = max_votes / len(decisions)
        
        # Lower confidence if agents disagree
        consensus_confidence = avg_confidence * agreement_ratio
        
        # Combine reasonings
        consensus_reasoning = f"Multi-agent consensus ({max_votes}/{len(decisions)} agents agree): " + \
                            " | ".join(reasonings[:2])  # Limit reasoning length
        
        return TradingDecision(
            symbol=market_data.get("symbol", "unknown"),
            action=consensus_action,
            confidence=consensus_confidence,
            reasoning=consensus_reasoning,
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def explain_decision(self, decision: TradingDecision) -> str:
        """
        Get detailed explanation of a decision
        
        Args:
            decision: Trading decision to explain
            
        Returns:
            Detailed explanation
        """
        try:
            explanation_prompt = f"""Provide a detailed explanation of this trading decision:

Action: {decision.action}
Symbol: {decision.symbol}
Confidence: {decision.confidence}
Reasoning: {decision.reasoning}

Explain:
1. Why this action was chosen
2. What factors influenced the confidence level
3. Potential risks and opportunities
4. Alternative scenarios considered

Provide a clear, educational explanation."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert trading educator explaining AI decisions."},
                    {"role": "user", "content": explanation_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Decision explanation failed: {e}")
            return f"Unable to generate explanation: {str(e)}"

    async def _analyze_with_ensemble(self, market_data: Dict[str, Any],
                                   historical_context: Optional[List[Dict[str, Any]]] = None,
                                   additional_context: Optional[Dict[str, Any]] = None) -> TradingDecision:
        """Analyze market data using ensemble learning"""
        try:
            # Prepare prompt for ensemble models
            prompt = self._create_analysis_prompt(
                market_data,
                historical_context or [],
                additional_context or {}
            )

            # Get ensemble decision
            ensemble_decision = await self.ensemble_learning.get_ensemble_decision(
                prompt,
                {"market_data": market_data}
            )

            # Enhance with sentiment analysis if available
            sentiment_signal = None
            if self.sentiment_analyzer and market_data.get("symbol"):
                sentiment_signal = await self.sentiment_analyzer.generate_sentiment_signal(
                    market_data["symbol"]
                )

            # Enhance with RAG knowledge if available
            rag_context = ""
            if self.advanced_rag:
                rag_result = await self.advanced_rag.retrieve_relevant_knowledge(
                    f"Trading analysis for {market_data.get('symbol', 'unknown')}",
                    limit=3,
                    doc_types=[DocumentType.TRADING_STRATEGY, DocumentType.MARKET_DATA]
                )
                if rag_result.documents:
                    rag_context = f"Relevant knowledge: {rag_result.documents[0].content[:200]}..."

            # Combine all insights
            final_confidence = ensemble_decision.confidence
            final_reasoning = ensemble_decision.reasoning

            if sentiment_signal:
                # Adjust confidence based on sentiment
                sentiment_weight = 0.3
                final_confidence = (final_confidence * 0.7 +
                                  sentiment_signal.confidence * sentiment_weight)
                final_reasoning += f" | Sentiment: {sentiment_signal.reasoning}"

            if rag_context:
                final_reasoning += f" | {rag_context}"

            return TradingDecision(
                symbol=market_data.get("symbol", "unknown"),
                action=ensemble_decision.final_decision,
                confidence=final_confidence,
                reasoning=final_reasoning,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        except Exception as e:
            logger.error(f"Ensemble analysis failed: {e}")
            return await self._analyze_with_standard_ai(market_data, historical_context, additional_context)

    async def _analyze_with_standard_ai(self, market_data: Dict[str, Any],
                                      historical_context: Optional[List[Dict[str, Any]]] = None,
                                      additional_context: Optional[Dict[str, Any]] = None) -> TradingDecision:
        """Standard AI analysis using OpenAI"""
        try:
            # Prepare analysis prompt
            analysis_prompt = self._create_analysis_prompt(
                market_data,
                historical_context or [],
                additional_context or {}
            )

            # Get AI decision
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from AI model")

            decision_data = json.loads(content)

            # Create structured decision
            decision = TradingDecision(
                symbol=market_data.get("symbol", "unknown"),
                action=decision_data.get("action", "HOLD").upper(),
                confidence=float(decision_data.get("confidence", 0.5)),
                reasoning=decision_data.get("reasoning", "No reasoning provided"),
                quantity=decision_data.get("quantity"),
                price_target=decision_data.get("price_target"),
                stop_loss=decision_data.get("stop_loss"),
                risk_score=decision_data.get("risk_score"),
                timestamp=datetime.now(timezone.utc).isoformat()
            )

            # Validate decision
            decision = self._validate_decision(decision)

            logger.info(f"🎯 Standard AI Decision: {decision.action} {decision.symbol} "
                       f"(Confidence: {decision.confidence:.2f})")

            return decision

        except Exception as e:
            logger.error(f"Standard AI analysis failed: {e}")
            return self._generate_mock_decision(market_data)
