#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - English Prompt Formatter
Optimizes prompts for DeepSeek-V2 model performance
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class PromptFormatter:
    """
    Formats trading data into optimized English prompts for DeepSeek-V2
    Ensures maximum model performance and decision accuracy
    """
    
    def __init__(self):
        self.model_name = "DeepSeek-V2"
        self.language = "English"
        
    def format_market_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """
        Format market data into comprehensive English analysis prompt
        """
        prompt = f"""MARKET ANALYSIS REQUEST - {self.model_name}

CURRENT MARKET CONDITIONS:
Token: {market_data.get('symbol', 'UNKNOWN')}
Current Price: ${market_data.get('price', 0.0):.6f}
24h Change: {market_data.get('price_change_24h', 0.0):+.2f}%
Volume (24h): ${market_data.get('volume_24h', 0.0):,.0f}
Market Cap: ${market_data.get('market_cap', 0.0):,.0f}
Liquidity: ${market_data.get('liquidity', 0.0):,.0f}

TECHNICAL INDICATORS:
RSI (14): {market_data.get('rsi', 50.0):.1f}
Moving Average (20): ${market_data.get('ma_20', 0.0):.6f}
Moving Average (50): ${market_data.get('ma_50', 0.0):.6f}
Bollinger Bands: Upper ${market_data.get('bb_upper', 0.0):.6f}, Lower ${market_data.get('bb_lower', 0.0):.6f}
MACD: {market_data.get('macd', 0.0):.4f}

SENTIMENT ANALYSIS:
Social Media Sentiment: {market_data.get('sentiment_score', 0.5):.2f} ({self._sentiment_label(market_data.get('sentiment_score', 0.5))})
News Sentiment: {market_data.get('news_sentiment', 0.5):.2f}
Fear & Greed Index: {market_data.get('fear_greed', 50)}/100

TRADING CONTEXT:
Current Strategy: {market_data.get('strategy', 'unknown')}
Portfolio Exposure: {market_data.get('portfolio_exposure', 0.0):.1f}%
Available Capital: ${market_data.get('available_capital', 0.0):.2f}
Risk Tolerance: {market_data.get('risk_tolerance', 'MEDIUM')}

QUESTION:
Based on this comprehensive market analysis, should we BUY, SELL, or HOLD this position?

Please provide:
1. Clear recommendation (BUY/SELL/HOLD)
2. Confidence level (0.0 to 1.0)
3. Detailed reasoning (2-3 sentences)
4. Risk assessment
5. Suggested position size (if BUY)
6. Stop-loss level (if applicable)

Format your response as structured analysis with clear actionable insights."""

        return prompt
    
    def format_execution_memory_prompt(self, execution_data: Dict[str, Any]) -> str:
        """
        Format execution result into memory storage prompt
        """
        action = execution_data.get('action', 'UNKNOWN')
        symbol = execution_data.get('symbol', 'UNKNOWN')
        status = execution_data.get('status', 'UNKNOWN')
        profit = execution_data.get('profit', 0.0)
        confidence = execution_data.get('confidence_score', 0.5)
        strategy = execution_data.get('strategy', 'unknown')
        
        prompt = f"""TRADING MEMORY FORMATION - {self.model_name}

EXECUTION SUMMARY:
Action: {action}
Symbol: {symbol}
Strategy: {strategy}
Confidence: {confidence:.2f}
Status: {status}
Profit/Loss: ${profit:.6f}
Execution Time: {execution_data.get('execution_latency_ms', 0)}ms

CONTEXT:
Market Price: ${execution_data.get('executed_price', 0.0):.6f}
Slippage: {execution_data.get('slippage', 0.0):.3f}%
Fees Paid: ${execution_data.get('fees_paid', 0.0):.6f}
TensorZero Optimization: {execution_data.get('tensorzero_optimization', 'None')}

TASK:
Create a concise memory entry (1-2 sentences) that captures the key learning from this trade execution.
Focus on:
- Strategy effectiveness
- Market conditions impact
- Execution quality
- Lessons learned

The memory should help improve future trading decisions."""

        return prompt
    
    def format_strategy_optimization_prompt(self, strategy_data: Dict[str, Any]) -> str:
        """
        Format strategy performance data into optimization prompt
        """
        prompt = f"""STRATEGY OPTIMIZATION ANALYSIS - {self.model_name}

STRATEGY PERFORMANCE REVIEW:
Strategy Name: {strategy_data.get('strategy_name', 'unknown')}
Total Trades: {strategy_data.get('total_trades', 0)}
Successful Trades: {strategy_data.get('successful_trades', 0)}
Success Rate: {strategy_data.get('success_rate', 0.0):.1f}%
Total Profit: ${strategy_data.get('total_profit', 0.0):.6f}
Average Profit per Trade: ${strategy_data.get('avg_profit', 0.0):.6f}
Maximum Drawdown: {strategy_data.get('max_drawdown', 0.0):.2f}%

RECENT PERFORMANCE:
Last 10 Trades: {strategy_data.get('recent_success_rate', 0.0):.1f}% success
Recent Profit: ${strategy_data.get('recent_profit', 0.0):.6f}
Trend: {strategy_data.get('performance_trend', 'STABLE')}

MARKET CONDITIONS:
Volatility: {strategy_data.get('market_volatility', 'MEDIUM')}
Trend: {strategy_data.get('market_trend', 'SIDEWAYS')}
Liquidity: {strategy_data.get('market_liquidity', 'NORMAL')}

ANALYSIS REQUEST:
1. Evaluate strategy effectiveness
2. Identify improvement opportunities
3. Suggest parameter adjustments
4. Recommend market condition filters
5. Assess risk management adequacy

Provide actionable optimization recommendations to enhance strategy performance."""

        return prompt
    
    def format_risk_assessment_prompt(self, portfolio_data: Dict[str, Any]) -> str:
        """
        Format portfolio data into risk assessment prompt
        """
        prompt = f"""RISK ASSESSMENT ANALYSIS - {self.model_name}

PORTFOLIO OVERVIEW:
Total Value: ${portfolio_data.get('total_value', 0.0):.2f}
Available Cash: ${portfolio_data.get('available_cash', 0.0):.2f}
Invested Capital: ${portfolio_data.get('invested_capital', 0.0):.2f}
Unrealized P&L: ${portfolio_data.get('unrealized_pnl', 0.0):.2f}
Daily P&L: ${portfolio_data.get('daily_pnl', 0.0):.2f}

POSITION BREAKDOWN:
Active Positions: {portfolio_data.get('active_positions', 0)}
Largest Position: {portfolio_data.get('largest_position_pct', 0.0):.1f}% of portfolio
Concentration Risk: {portfolio_data.get('concentration_risk', 'LOW')}

RISK METRICS:
Portfolio Beta: {portfolio_data.get('portfolio_beta', 1.0):.2f}
Value at Risk (95%): ${portfolio_data.get('var_95', 0.0):.2f}
Maximum Drawdown: {portfolio_data.get('max_drawdown', 0.0):.2f}%
Sharpe Ratio: {portfolio_data.get('sharpe_ratio', 0.0):.2f}

EXPOSURE ANALYSIS:
Sector Concentration: {portfolio_data.get('sector_exposure', {})}
Geographic Exposure: {portfolio_data.get('geographic_exposure', {})}
Market Cap Exposure: {portfolio_data.get('market_cap_exposure', {})}

RISK ASSESSMENT REQUEST:
1. Evaluate current risk level (LOW/MEDIUM/HIGH)
2. Identify concentration risks
3. Assess portfolio diversification
4. Recommend position sizing adjustments
5. Suggest risk mitigation strategies

Provide comprehensive risk analysis with specific actionable recommendations."""

        return prompt
    
    def format_market_opportunity_prompt(self, opportunity_data: Dict[str, Any]) -> str:
        """
        Format market opportunity data into analysis prompt
        """
        prompt = f"""MARKET OPPORTUNITY ANALYSIS - {self.model_name}

OPPORTUNITY IDENTIFICATION:
Token: {opportunity_data.get('symbol', 'UNKNOWN')}
Opportunity Type: {opportunity_data.get('opportunity_type', 'unknown')}
Confidence Score: {opportunity_data.get('confidence', 0.5):.2f}
Time Sensitivity: {opportunity_data.get('time_sensitivity', 'MEDIUM')}

MARKET SIGNALS:
Price Movement: {opportunity_data.get('price_movement', 0.0):+.2f}%
Volume Spike: {opportunity_data.get('volume_spike', 0.0):+.2f}%
Social Mentions: {opportunity_data.get('social_mentions', 0):+d}%
News Impact: {opportunity_data.get('news_impact', 'NEUTRAL')}

TECHNICAL SETUP:
Support Level: ${opportunity_data.get('support_level', 0.0):.6f}
Resistance Level: ${opportunity_data.get('resistance_level', 0.0):.6f}
Breakout Probability: {opportunity_data.get('breakout_probability', 0.5):.2f}
Risk/Reward Ratio: {opportunity_data.get('risk_reward_ratio', 1.0):.1f}:1

FUNDAMENTAL FACTORS:
Market Cap: ${opportunity_data.get('market_cap', 0.0):,.0f}
Liquidity: ${opportunity_data.get('liquidity', 0.0):,.0f}
Trading Volume: ${opportunity_data.get('trading_volume', 0.0):,.0f}
Community Strength: {opportunity_data.get('community_strength', 'MEDIUM')}

OPPORTUNITY EVALUATION:
1. Assess opportunity validity and potential
2. Evaluate risk factors and mitigation strategies
3. Recommend optimal entry strategy
4. Suggest position sizing and timing
5. Define exit criteria and profit targets

Provide detailed opportunity analysis with clear go/no-go recommendation."""

        return prompt
    
    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to human-readable label"""
        if score >= 0.8:
            return "VERY BULLISH"
        elif score >= 0.6:
            return "BULLISH"
        elif score >= 0.4:
            return "NEUTRAL"
        elif score >= 0.2:
            return "BEARISH"
        else:
            return "VERY BEARISH"
    
    def format_deepseek_system_prompt(self) -> str:
        """
        Generate optimized system prompt for DeepSeek-V2
        """
        return """You are an expert cryptocurrency trading AI with deep market analysis capabilities.

CORE COMPETENCIES:
- Advanced technical analysis and pattern recognition
- Fundamental analysis of cryptocurrency projects
- Risk assessment and portfolio management
- Market sentiment analysis and social media monitoring
- High-frequency trading strategy optimization

DECISION FRAMEWORK:
- Always provide clear, actionable recommendations
- Include confidence levels for all decisions
- Consider risk-adjusted returns over pure profit
- Factor in market conditions and volatility
- Maintain strict risk management principles

RESPONSE FORMAT:
- Be concise but comprehensive
- Use structured analysis with clear sections
- Provide specific numerical targets when applicable
- Include reasoning for all recommendations
- Consider multiple scenarios and contingencies

TRADING PHILOSOPHY:
- Preserve capital above all else
- Seek asymmetric risk/reward opportunities
- Adapt strategies to changing market conditions
- Learn from both successful and failed trades
- Maintain emotional discipline in decision making

You are operating within THE OVERMIND PROTOCOL - a sophisticated AI trading system with real-time market data, vector memory for learning, and sub-50ms execution capabilities."""

def create_optimized_prompt(prompt_type: str, data: Dict[str, Any]) -> str:
    """
    Factory function to create optimized prompts for different scenarios
    """
    formatter = PromptFormatter()
    
    if prompt_type == "market_analysis":
        return formatter.format_market_analysis_prompt(data)
    elif prompt_type == "execution_memory":
        return formatter.format_execution_memory_prompt(data)
    elif prompt_type == "strategy_optimization":
        return formatter.format_strategy_optimization_prompt(data)
    elif prompt_type == "risk_assessment":
        return formatter.format_risk_assessment_prompt(data)
    elif prompt_type == "market_opportunity":
        return formatter.format_market_opportunity_prompt(data)
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")

# Example usage
if __name__ == "__main__":
    # Test market analysis prompt
    sample_data = {
        'symbol': 'BONK/SOL',
        'price': 0.000025,
        'price_change_24h': 12.5,
        'volume_24h': 2500000,
        'rsi': 65.2,
        'sentiment_score': 0.75,
        'strategy': 'memecoin_hunter',
        'confidence': 0.87
    }
    
    prompt = create_optimized_prompt("market_analysis", sample_data)
    print("=== OPTIMIZED DEEPSEEK PROMPT ===")
    print(prompt)
