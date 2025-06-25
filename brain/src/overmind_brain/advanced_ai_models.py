"""THE OVERMIND PROTOCOL - Advanced AI Models Integration
Enhanced AI capabilities with multiple model support, ensemble learning, and advanced RAG.
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

# AI Model Clients
import openai
from anthropic import AsyncAnthropic
import httpx

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Supported AI model types"""
    GPT4_TURBO = "gpt-4-turbo"
    GPT4O = "gpt-4o"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    DEEPSEEK_V3 = "deepseek-chat"
    GEMINI_PRO = "gemini-pro"

@dataclass
class ModelResponse:
    """Standardized response from AI models"""
    content: str
    confidence: float
    model_type: ModelType
    reasoning: str
    metadata: Dict[str, Any]
    processing_time_ms: float

@dataclass
class EnsembleDecision:
    """Ensemble decision combining multiple model outputs"""
    final_decision: str
    confidence: float
    model_votes: Dict[ModelType, ModelResponse]
    consensus_score: float
    reasoning: str
    metadata: Dict[str, Any]

class BaseAIModel(ABC):
    """Abstract base class for AI models"""
    
    def __init__(self, model_type: ModelType, config: Dict[str, Any]):
        self.model_type = model_type
        self.config = config
        self.client = None
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the model client"""
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        """Generate response from the model"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if model is healthy and responsive"""
        pass

class OpenAIModel(BaseAIModel):
    """OpenAI GPT models implementation"""
    
    async def initialize(self) -> bool:
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key in ["demo-mode", "mock", "test"]:
                logger.warning("OpenAI API key not configured, using mock mode")
                return False
                
            self.client = openai.AsyncOpenAI(api_key=api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return False
    
    async def generate_response(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        start_time = datetime.now()
        
        try:
            if not self.client:
                return self._generate_mock_response(prompt, context)
            
            response = await self.client.chat.completions.create(
                model=self.model_type.value,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": self._format_prompt(prompt, context)}
                ],
                temperature=self.config.get("temperature", 0.3),
                max_tokens=self.config.get("max_tokens", 2000),
                response_format={"type": "json_object"}
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            content = response.choices[0].message.content
            parsed_content = json.loads(content)
            
            return ModelResponse(
                content=parsed_content.get("decision", ""),
                confidence=parsed_content.get("confidence", 0.5),
                model_type=self.model_type,
                reasoning=parsed_content.get("reasoning", ""),
                metadata=parsed_content.get("metadata", {}),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"OpenAI model error: {e}")
            return self._generate_mock_response(prompt, context)
    
    async def health_check(self) -> bool:
        try:
            if not self.client:
                return False
            
            response = await self.client.chat.completions.create(
                model=self.model_type.value,
                messages=[{"role": "user", "content": "Health check"}],
                max_tokens=10
            )
            return response.choices[0].message.content is not None
        except:
            return False
    
    def _get_system_prompt(self) -> str:
        return """You are an advanced AI trading analyst for THE OVERMIND PROTOCOL.
        Analyze market data and provide trading decisions in JSON format with:
        - decision: BUY/SELL/HOLD
        - confidence: 0.0-1.0
        - reasoning: detailed explanation
        - metadata: additional analysis data"""
    
    def _format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        return f"""
        Market Analysis Request:
        {prompt}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Provide your analysis in JSON format.
        """
    
    def _generate_mock_response(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        return ModelResponse(
            content="HOLD",
            confidence=0.6,
            model_type=self.model_type,
            reasoning="Mock response - OpenAI not configured",
            metadata={"mock": True},
            processing_time_ms=100.0
        )

class AnthropicModel(BaseAIModel):
    """Anthropic Claude models implementation"""
    
    async def initialize(self) -> bool:
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("Anthropic API key not configured, using mock mode")
                return False
                
            self.client = AsyncAnthropic(api_key=api_key)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            return False
    
    async def generate_response(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        start_time = datetime.now()
        
        try:
            if not self.client:
                return self._generate_mock_response(prompt, context)
            
            response = await self.client.messages.create(
                model=self.model_type.value,
                max_tokens=self.config.get("max_tokens", 2000),
                temperature=self.config.get("temperature", 0.3),
                messages=[
                    {"role": "user", "content": self._format_prompt(prompt, context)}
                ]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            content = response.content[0].text
            parsed_content = json.loads(content)
            
            return ModelResponse(
                content=parsed_content.get("decision", ""),
                confidence=parsed_content.get("confidence", 0.5),
                model_type=self.model_type,
                reasoning=parsed_content.get("reasoning", ""),
                metadata=parsed_content.get("metadata", {}),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Anthropic model error: {e}")
            return self._generate_mock_response(prompt, context)
    
    async def health_check(self) -> bool:
        try:
            if not self.client:
                return False
            
            response = await self.client.messages.create(
                model=self.model_type.value,
                max_tokens=10,
                messages=[{"role": "user", "content": "Health check"}]
            )
            return len(response.content) > 0
        except:
            return False
    
    def _format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        return f"""You are an advanced AI trading analyst for THE OVERMIND PROTOCOL.

Market Analysis Request:
{prompt}

Context:
{json.dumps(context, indent=2)}

Analyze the market data and provide a trading decision in JSON format with:
- decision: BUY/SELL/HOLD
- confidence: 0.0-1.0 (your confidence in this decision)
- reasoning: detailed explanation of your analysis
- metadata: additional analysis data

Respond only with valid JSON."""
    
    def _generate_mock_response(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        return ModelResponse(
            content="HOLD",
            confidence=0.7,
            model_type=self.model_type,
            reasoning="Mock response - Anthropic not configured",
            metadata={"mock": True},
            processing_time_ms=120.0
        )

class DeepSeekModel(BaseAIModel):
    """DeepSeek V3 model implementation"""
    
    async def initialize(self) -> bool:
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                logger.warning("DeepSeek API key not configured, using mock mode")
                return False
                
            self.client = httpx.AsyncClient(
                base_url="https://api.deepseek.com/v1",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek client: {e}")
            return False
    
    async def generate_response(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        start_time = datetime.now()
        
        try:
            if not self.client:
                return self._generate_mock_response(prompt, context)
            
            response = await self.client.post("/chat/completions", json={
                "model": self.model_type.value,
                "messages": [
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": self._format_prompt(prompt, context)}
                ],
                "temperature": self.config.get("temperature", 0.3),
                "max_tokens": self.config.get("max_tokens", 2000),
                "response_format": {"type": "json_object"}
            })
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code != 200:
                raise Exception(f"DeepSeek API error: {response.status_code}")
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed_content = json.loads(content)
            
            return ModelResponse(
                content=parsed_content.get("decision", ""),
                confidence=parsed_content.get("confidence", 0.5),
                model_type=self.model_type,
                reasoning=parsed_content.get("reasoning", ""),
                metadata=parsed_content.get("metadata", {}),
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"DeepSeek model error: {e}")
            return self._generate_mock_response(prompt, context)
    
    async def health_check(self) -> bool:
        try:
            if not self.client:
                return False
            
            response = await self.client.post("/chat/completions", json={
                "model": self.model_type.value,
                "messages": [{"role": "user", "content": "Health check"}],
                "max_tokens": 10
            })
            return response.status_code == 200
        except:
            return False
    
    def _get_system_prompt(self) -> str:
        return """You are an advanced AI trading analyst for THE OVERMIND PROTOCOL.
        Analyze market data and provide trading decisions in JSON format with:
        - decision: BUY/SELL/HOLD
        - confidence: 0.0-1.0
        - reasoning: detailed explanation
        - metadata: additional analysis data"""
    
    def _format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        return f"""
        Market Analysis Request:
        {prompt}
        
        Context:
        {json.dumps(context, indent=2)}
        
        Provide your analysis in JSON format.
        """
    
    def _generate_mock_response(self, prompt: str, context: Dict[str, Any]) -> ModelResponse:
        return ModelResponse(
            content="HOLD",
            confidence=0.65,
            model_type=self.model_type,
            reasoning="Mock response - DeepSeek not configured",
            metadata={"mock": True},
            processing_time_ms=90.0
        )

class EnsembleLearning:
    """Ensemble learning system combining multiple AI models"""
    
    def __init__(self, models: List[BaseAIModel], config: Dict[str, Any]):
        self.models = models
        self.config = config
        self.model_weights = self._initialize_weights()
        self.performance_history = {}
        
    def _initialize_weights(self) -> Dict[ModelType, float]:
        """Initialize equal weights for all models"""
        num_models = len(self.models)
        if num_models == 0:
            return {}
        
        equal_weight = 1.0 / num_models
        return {model.model_type: equal_weight for model in self.models}
    
    async def get_ensemble_decision(self, prompt: str, context: Dict[str, Any]) -> EnsembleDecision:
        """Get ensemble decision from all models"""
        start_time = datetime.now()
        
        # Get responses from all models concurrently
        tasks = [model.generate_response(prompt, context) for model in self.models]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failed responses
        valid_responses = []
        model_votes = {}
        
        for i, response in enumerate(responses):
            if isinstance(response, ModelResponse):
                valid_responses.append(response)
                model_votes[response.model_type] = response
            else:
                logger.warning(f"Model {self.models[i].model_type} failed: {response}")
        
        if not valid_responses:
            return self._generate_fallback_decision(prompt, context)
        
        # Calculate ensemble decision
        final_decision = self._calculate_weighted_decision(valid_responses)
        confidence = self._calculate_ensemble_confidence(valid_responses)
        consensus_score = self._calculate_consensus_score(valid_responses)
        reasoning = self._generate_ensemble_reasoning(valid_responses)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        ensemble_decision = EnsembleDecision(
            final_decision=final_decision,
            confidence=confidence,
            model_votes=model_votes,
            consensus_score=consensus_score,
            reasoning=reasoning,
            metadata={
                "num_models": len(valid_responses),
                "processing_time_ms": processing_time,
                "model_weights": self.model_weights
            }
        )
        
        # Update model performance tracking
        self._update_performance_tracking(ensemble_decision)
        
        return ensemble_decision
    
    def _calculate_weighted_decision(self, responses: List[ModelResponse]) -> str:
        """Calculate weighted decision based on model weights and confidence"""
        decision_scores = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        
        for response in responses:
            weight = self.model_weights.get(response.model_type, 0.0)
            confidence_weight = response.confidence * weight
            
            if response.content in decision_scores:
                decision_scores[response.content] += confidence_weight
        
        # Return decision with highest weighted score
        return max(decision_scores, key=decision_scores.get)
    
    def _calculate_ensemble_confidence(self, responses: List[ModelResponse]) -> float:
        """Calculate ensemble confidence based on individual confidences and consensus"""
        if not responses:
            return 0.0
        
        # Weighted average of individual confidences
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for response in responses:
            weight = self.model_weights.get(response.model_type, 0.0)
            weighted_confidence += response.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        base_confidence = weighted_confidence / total_weight
        
        # Adjust based on consensus
        consensus_score = self._calculate_consensus_score(responses)
        adjusted_confidence = base_confidence * (0.5 + 0.5 * consensus_score)
        
        return min(adjusted_confidence, 1.0)
    
    def _calculate_consensus_score(self, responses: List[ModelResponse]) -> float:
        """Calculate how much the models agree with each other"""
        if len(responses) <= 1:
            return 1.0
        
        decisions = [response.content for response in responses]
        decision_counts = {}
        
        for decision in decisions:
            decision_counts[decision] = decision_counts.get(decision, 0) + 1
        
        # Calculate consensus as the proportion of models agreeing with majority
        max_count = max(decision_counts.values())
        consensus_score = max_count / len(responses)
        
        return consensus_score
    
    def _generate_ensemble_reasoning(self, responses: List[ModelResponse]) -> str:
        """Generate combined reasoning from all models"""
        reasoning_parts = []
        
        for response in responses:
            model_name = response.model_type.value
            reasoning_parts.append(f"{model_name}: {response.reasoning}")
        
        return " | ".join(reasoning_parts)
    
    def _update_performance_tracking(self, decision: EnsembleDecision):
        """Update performance tracking for adaptive weighting"""
        # This would be implemented with actual trading results
        # For now, just log the decision
        logger.info(f"Ensemble decision: {decision.final_decision} "
                   f"(confidence: {decision.confidence:.2f}, "
                   f"consensus: {decision.consensus_score:.2f})")
    
    def _generate_fallback_decision(self, prompt: str, context: Dict[str, Any]) -> EnsembleDecision:
        """Generate fallback decision when all models fail"""
        return EnsembleDecision(
            final_decision="HOLD",
            confidence=0.1,
            model_votes={},
            consensus_score=0.0,
            reasoning="Fallback decision - all models failed",
            metadata={"fallback": True}
        )
    
    async def update_model_weights(self, performance_data: Dict[ModelType, float]):
        """Update model weights based on performance data"""
        total_performance = sum(performance_data.values())
        
        if total_performance > 0:
            for model_type, performance in performance_data.items():
                self.model_weights[model_type] = performance / total_performance
        
        logger.info(f"Updated model weights: {self.model_weights}")
    
    async def health_check_all_models(self) -> Dict[ModelType, bool]:
        """Check health of all models"""
        health_results = {}
        
        for model in self.models:
            try:
                health_results[model.model_type] = await model.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {model.model_type}: {e}")
                health_results[model.model_type] = False
        
        return health_results
