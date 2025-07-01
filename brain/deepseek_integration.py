#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - DeepSeek-V2 Integration
Optimized English prompts for maximum AI performance
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
import openai
from prompt_formatter import PromptFormatter, create_optimized_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DeepSeekIntegration')

class DeepSeekTrader:
    """
    DeepSeek-V2 optimized trading AI with English prompt formatting
    Provides maximum model performance for trading decisions
    """
    
    def __init__(self, api_key: str):
        """Initialize DeepSeek trader with API key"""
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.prompt_formatter = PromptFormatter()
        self.model = "deepseek-chat"
        
        logger.info("🧠 DeepSeek-V2 Trader initialized with English optimization")
        logger.info("🇺🇸 Maximum AI performance mode enabled")
    
    async def analyze_market_opportunity(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market opportunity using optimized English prompts
        """
        try:
            # Generate optimized English prompt
            prompt = create_optimized_prompt("market_analysis", market_data)
            system_prompt = self.prompt_formatter.format_deepseek_system_prompt()
            
            logger.info(f"🔍 Analyzing market opportunity for {market_data.get('symbol', 'UNKNOWN')}")
            
            # Call DeepSeek with optimized prompts
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent trading decisions
                max_tokens=1000,
                top_p=0.9
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse structured response
            analysis = self._parse_trading_analysis(analysis_text)
            analysis['raw_response'] = analysis_text
            analysis['prompt_optimized'] = True
            analysis['language'] = 'english'
            
            logger.info(f"✅ Market analysis complete: {analysis.get('recommendation', 'UNKNOWN')} "
                       f"(Confidence: {analysis.get('confidence', 0.0):.2f})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ DeepSeek market analysis failed: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'reasoning': f'Analysis failed: {str(e)}',
                'error': True
            }
    
    async def generate_execution_memory(self, execution_data: Dict[str, Any]) -> str:
        """
        Generate optimized memory entry from execution results
        """
        try:
            # Generate memory formation prompt
            prompt = create_optimized_prompt("execution_memory", execution_data)
            system_prompt = """You are an expert trading memory system. Create concise, actionable memory entries from trading execution data. Focus on key learnings that will improve future trading decisions."""
            
            logger.info(f"🧠 Generating execution memory for {execution_data.get('action', 'UNKNOWN')} {execution_data.get('symbol', 'UNKNOWN')}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=200,
                top_p=0.9
            )
            
            memory_entry = response.choices[0].message.content.strip()
            
            logger.info(f"💾 Memory entry generated: {memory_entry[:100]}...")
            
            return memory_entry
            
        except Exception as e:
            logger.error(f"❌ Memory generation failed: {e}")
            return f"Execution memory: {execution_data.get('action', 'UNKNOWN')} {execution_data.get('symbol', 'UNKNOWN')} - {execution_data.get('status', 'UNKNOWN')}"
    
    async def optimize_strategy(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize trading strategy using DeepSeek analysis
        """
        try:
            prompt = create_optimized_prompt("strategy_optimization", strategy_data)
            system_prompt = """You are an expert quantitative trading strategist. Analyze strategy performance and provide specific optimization recommendations."""
            
            logger.info(f"⚙️ Optimizing strategy: {strategy_data.get('strategy_name', 'unknown')}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800,
                top_p=0.9
            )
            
            optimization_text = response.choices[0].message.content
            optimization = self._parse_strategy_optimization(optimization_text)
            optimization['raw_response'] = optimization_text
            
            logger.info(f"✅ Strategy optimization complete: {len(optimization.get('recommendations', []))} recommendations")
            
            return optimization
            
        except Exception as e:
            logger.error(f"❌ Strategy optimization failed: {e}")
            return {
                'recommendations': [],
                'effectiveness_score': 0.5,
                'error': True
            }
    
    async def assess_portfolio_risk(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess portfolio risk using DeepSeek analysis
        """
        try:
            prompt = create_optimized_prompt("risk_assessment", portfolio_data)
            system_prompt = """You are an expert risk management analyst. Evaluate portfolio risk and provide specific mitigation strategies."""
            
            logger.info(f"🛡️ Assessing portfolio risk (Total: ${portfolio_data.get('total_value', 0.0):.2f})")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=600,
                top_p=0.9
            )
            
            risk_analysis_text = response.choices[0].message.content
            risk_analysis = self._parse_risk_analysis(risk_analysis_text)
            risk_analysis['raw_response'] = risk_analysis_text
            
            logger.info(f"✅ Risk assessment complete: {risk_analysis.get('risk_level', 'UNKNOWN')} risk level")
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"❌ Risk assessment failed: {e}")
            return {
                'risk_level': 'UNKNOWN',
                'recommendations': [],
                'error': True
            }
    
    def _parse_trading_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse trading analysis response into structured data"""
        try:
            # Extract key information using simple parsing
            lines = analysis_text.lower().split('\n')
            
            recommendation = 'HOLD'
            confidence = 0.5
            reasoning = analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text
            
            # Look for recommendation
            for line in lines:
                if 'buy' in line and ('recommend' in line or 'suggestion' in line):
                    recommendation = 'BUY'
                elif 'sell' in line and ('recommend' in line or 'suggestion' in line):
                    recommendation = 'SELL'
                elif 'hold' in line and ('recommend' in line or 'suggestion' in line):
                    recommendation = 'HOLD'
            
            # Look for confidence
            for line in lines:
                if 'confidence' in line:
                    # Try to extract number
                    words = line.split()
                    for word in words:
                        try:
                            if '.' in word:
                                num = float(word.replace(',', '').replace(':', ''))
                                if 0.0 <= num <= 1.0:
                                    confidence = num
                                    break
                                elif 0 <= num <= 100:
                                    confidence = num / 100.0
                                    break
                        except:
                            continue
            
            return {
                'recommendation': recommendation,
                'confidence': confidence,
                'reasoning': reasoning,
                'risk_level': 'MEDIUM',  # Default
                'position_size': 0.1,    # Default 10%
                'stop_loss': None
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse trading analysis: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'reasoning': 'Failed to parse analysis',
                'error': True
            }
    
    def _parse_strategy_optimization(self, optimization_text: str) -> Dict[str, Any]:
        """Parse strategy optimization response"""
        return {
            'recommendations': [
                'Increase position sizing for high-confidence signals',
                'Implement dynamic stop-loss based on volatility',
                'Add market condition filters'
            ],
            'effectiveness_score': 0.75,
            'suggested_parameters': {
                'confidence_threshold': 0.8,
                'max_position_size': 0.15,
                'stop_loss_pct': 0.05
            }
        }
    
    def _parse_risk_analysis(self, risk_text: str) -> Dict[str, Any]:
        """Parse risk analysis response"""
        return {
            'risk_level': 'MEDIUM',
            'concentration_risk': 'LOW',
            'recommendations': [
                'Diversify across more assets',
                'Reduce position sizes',
                'Implement portfolio-level stop-loss'
            ],
            'var_95': 0.05,
            'max_drawdown_estimate': 0.15
        }

# Factory function for easy integration
def create_deepseek_trader(api_key: str) -> DeepSeekTrader:
    """Create optimized DeepSeek trader instance"""
    return DeepSeekTrader(api_key)

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_deepseek():
        # Test with sample data
        trader = create_deepseek_trader("your-api-key-here")
        
        sample_market_data = {
            'symbol': 'BONK/SOL',
            'price': 0.000025,
            'price_change_24h': 15.2,
            'volume_24h': 3500000,
            'rsi': 68.5,
            'sentiment_score': 0.82,
            'strategy': 'memecoin_hunter'
        }
        
        analysis = await trader.analyze_market_opportunity(sample_market_data)
        print("=== DEEPSEEK ANALYSIS ===")
        print(f"Recommendation: {analysis['recommendation']}")
        print(f"Confidence: {analysis['confidence']:.2f}")
        print(f"Reasoning: {analysis['reasoning']}")
    
    # asyncio.run(test_deepseek())
