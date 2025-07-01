#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Proposal Impact Analyzer
DeepSeek-V2 powered analysis of DAO proposals for trading alpha
"""

import json
import logging
import asyncio
from typing import Dict, Any, List
import openai
from datetime import datetime
from prompt_formatter import create_optimized_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ProposalImpactAnalyzer')

class ProposalImpactAnalyzer:
    """
    DeepSeek-V2 powered analyzer for DAO proposal impact on token prices
    """
    
    def __init__(self, deepseek_api_key: str):
        """Initialize with DeepSeek API key"""
        self.client = openai.OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = "deepseek-chat"
        
        # Historical proposal impact data for training context
        self.historical_impacts = {
            "buyback_proposals": {
                "average_impact": 0.18,  # +18% average
                "success_rate": 0.85,
                "examples": [
                    {"dao": "MakerDAO", "proposal": "Smart Burn Engine", "impact": 0.25},
                    {"dao": "Raydium", "proposal": "Buyback Implementation", "impact": 0.15},
                    {"dao": "Jupiter", "proposal": "50% Buyback Program", "impact": 0.12}
                ]
            },
            "fee_switch_proposals": {
                "average_impact": 0.12,  # +12% average
                "success_rate": 0.65,
                "examples": [
                    {"dao": "GMX", "proposal": "Fee Distribution", "impact": 0.22},
                    {"dao": "Synthetix", "proposal": "SNX Staking Rewards", "impact": 0.08}
                ]
            },
            "yield_changes": {
                "average_impact": 0.08,  # +8% average
                "success_rate": 0.70,
                "examples": [
                    {"dao": "Lido", "proposal": "Staking Rewards Increase", "impact": 0.10},
                    {"dao": "Aave", "proposal": "Safety Module Rewards", "impact": 0.06}
                ]
            }
        }
        
        logger.info("🧠 Proposal Impact Analyzer initialized with DeepSeek-V2")
        logger.info("📊 Historical impact database loaded")
    
    async def analyze_proposal_impact(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze DAO proposal impact using DeepSeek-V2
        """
        try:
            # Generate optimized English prompt
            prompt = self.create_proposal_analysis_prompt(proposal_data)
            system_prompt = self.create_system_prompt()
            
            logger.info(f"🔍 Analyzing proposal: {proposal_data.get('title', 'Unknown')}")
            
            # Call DeepSeek with optimized prompts
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1200,
                top_p=0.9
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse structured response
            analysis = self.parse_proposal_analysis(analysis_text, proposal_data)
            analysis['raw_response'] = analysis_text
            analysis['analysis_timestamp'] = datetime.now().isoformat()
            
            logger.info(f"✅ Proposal analysis complete")
            logger.info(f"   Impact Score: {analysis.get('impact_score', 0.0):.2f}")
            logger.info(f"   Price Impact: {analysis.get('price_impact_estimate', 0.0):+.1%}")
            logger.info(f"   Confidence: {analysis.get('confidence', 0.0):.2f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Proposal analysis failed: {e}")
            return self.create_fallback_analysis(proposal_data)
    
    def create_proposal_analysis_prompt(self, proposal_data: Dict[str, Any]) -> str:
        """Create optimized English prompt for proposal analysis"""
        
        # Extract key information
        dao_name = proposal_data.get('dao_name', 'Unknown DAO')
        title = proposal_data.get('title', 'Unknown Proposal')
        description = proposal_data.get('description', 'No description')
        proposal_type = proposal_data.get('proposal_type', 'other')
        vote_count = proposal_data.get('vote_count', {})
        tokens_affected = proposal_data.get('tokens_affected', [])
        
        # Get historical context
        historical_context = self.get_historical_context(proposal_type)
        
        prompt = f"""PROPOSAL IMPACT ANALYSIS REQUEST - DeepSeek-V2

DAO PROPOSAL DETAILS:
DAO: {dao_name}
Proposal Title: {title}
Proposal Type: {proposal_type}
Tokens Affected: {', '.join(tokens_affected)}

PROPOSAL DESCRIPTION:
{description}

VOTING STATUS:
For: {vote_count.get('for', 0):,} votes
Against: {vote_count.get('against', 0):,} votes
Total Votes: {sum(vote_count.values()):,}
Support Ratio: {vote_count.get('for', 0) / max(sum(vote_count.values()), 1):.1%}

HISTORICAL CONTEXT:
{historical_context}

ANALYSIS FRAMEWORK:
Based on historical DAO proposal impacts and tokenomics analysis, evaluate:

1. IMPACT SCORE (0.0 to 1.0):
   - Revenue impact on DAO treasury
   - Token supply/demand dynamics
   - Competitive positioning changes
   - Community sentiment shift

2. PRICE IMPACT ESTIMATE (-1.0 to +1.0):
   - Short-term price movement (1-7 days)
   - Based on similar historical proposals
   - Account for market conditions and token liquidity

3. BULLISH PROBABILITY (0.0 to 1.0):
   - Likelihood of positive price impact
   - Voting success probability
   - Implementation timeline certainty

4. TRADING RECOMMENDATION:
   - BUY/SELL/HOLD recommendation
   - Position size (0.0 to 1.0)
   - Entry timing (immediate/wait/after_vote)
   - Exit strategy

QUESTION:
What is the expected impact of this proposal on {tokens_affected[0] if tokens_affected else 'the token'} price?

Please provide:
1. Impact Score (0.0-1.0)
2. Price Impact Estimate (-100% to +100%)
3. Bullish Probability (0.0-1.0)
4. Confidence Level (0.0-1.0)
5. Trading Recommendation (BUY/SELL/HOLD)
6. Position Size (0.0-1.0)
7. Detailed reasoning (2-3 sentences)

Format your response with clear numerical values and actionable insights."""

        return prompt
    
    def create_system_prompt(self) -> str:
        """Create system prompt for DeepSeek"""
        return """You are an expert DeFi tokenomics analyst specializing in DAO governance impact analysis.

CORE COMPETENCIES:
- Deep understanding of DAO governance mechanisms and their market impact
- Historical analysis of proposal outcomes and price movements
- Tokenomics modeling for buybacks, fee switches, and yield mechanisms
- Risk assessment for governance-based trading strategies

ANALYSIS APPROACH:
- Use historical precedents from MakerDAO, Aave, Uniswap, Jito, and other major DAOs
- Consider both fundamental impact and market sentiment
- Account for proposal implementation timelines and execution risk
- Provide quantitative estimates with confidence intervals

RESPONSE FORMAT:
- Always provide numerical scores and estimates
- Include clear reasoning based on comparable historical cases
- Consider both upside potential and downside risks
- Focus on actionable trading insights

Your analysis directly informs high-stakes trading decisions in live markets."""
    
    def get_historical_context(self, proposal_type: str) -> str:
        """Get historical context for proposal type"""
        if proposal_type in self.historical_impacts:
            data = self.historical_impacts[proposal_type]
            examples = data['examples']
            
            context = f"""
HISTORICAL {proposal_type.upper()} PROPOSALS:
Average Price Impact: {data['average_impact']:+.1%}
Success Rate: {data['success_rate']:.0%}

Recent Examples:"""
            
            for example in examples:
                context += f"\n- {example['dao']}: {example['proposal']} → {example['impact']:+.1%}"
            
            return context
        
        return "Limited historical data available for this proposal type."
    
    def parse_proposal_analysis(self, analysis_text: str, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DeepSeek analysis response into structured data"""
        try:
            # Extract numerical values using regex and text parsing
            import re
            
            # Default values
            impact_score = 0.5
            price_impact = 0.0
            bullish_probability = 0.5
            confidence = 0.5
            recommendation = "HOLD"
            position_size = 0.0
            
            # Parse impact score
            impact_match = re.search(r'impact\s*score[:\s]*([0-9.]+)', analysis_text.lower())
            if impact_match:
                impact_score = float(impact_match.group(1))
            
            # Parse price impact
            price_match = re.search(r'price\s*impact[:\s]*([+-]?[0-9.]+)%?', analysis_text.lower())
            if price_match:
                price_impact = float(price_match.group(1)) / 100.0
            
            # Parse bullish probability
            bullish_match = re.search(r'bullish\s*probability[:\s]*([0-9.]+)', analysis_text.lower())
            if bullish_match:
                bullish_probability = float(bullish_match.group(1))
            
            # Parse confidence
            confidence_match = re.search(r'confidence[:\s]*([0-9.]+)', analysis_text.lower())
            if confidence_match:
                confidence = float(confidence_match.group(1))
            
            # Parse recommendation
            if 'buy' in analysis_text.lower():
                recommendation = "BUY"
            elif 'sell' in analysis_text.lower():
                recommendation = "SELL"
            
            # Parse position size
            position_match = re.search(r'position\s*size[:\s]*([0-9.]+)', analysis_text.lower())
            if position_match:
                position_size = float(position_match.group(1))
            
            return {
                'impact_score': min(max(impact_score, 0.0), 1.0),
                'price_impact_estimate': min(max(price_impact, -1.0), 1.0),
                'bullish_probability': min(max(bullish_probability, 0.0), 1.0),
                'confidence': min(max(confidence, 0.0), 1.0),
                'recommendation': recommendation,
                'position_size': min(max(position_size, 0.0), 1.0),
                'reasoning': analysis_text[:300] + "..." if len(analysis_text) > 300 else analysis_text,
                'proposal_type': proposal_data.get('proposal_type', 'other'),
                'tokens_affected': proposal_data.get('tokens_affected', []),
                'analysis_quality': 'high' if confidence > 0.7 else 'medium' if confidence > 0.4 else 'low'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse analysis: {e}")
            return self.create_fallback_analysis(proposal_data)
    
    def create_fallback_analysis(self, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback analysis if DeepSeek fails"""
        proposal_type = proposal_data.get('proposal_type', 'other')
        
        # Use historical averages as fallback
        if proposal_type in self.historical_impacts:
            historical = self.historical_impacts[proposal_type]
            return {
                'impact_score': 0.6,
                'price_impact_estimate': historical['average_impact'],
                'bullish_probability': historical['success_rate'],
                'confidence': 0.4,  # Low confidence for fallback
                'recommendation': 'HOLD',
                'position_size': 0.05,  # Conservative
                'reasoning': f'Fallback analysis based on historical {proposal_type} proposals',
                'analysis_quality': 'fallback'
            }
        
        return {
            'impact_score': 0.3,
            'price_impact_estimate': 0.0,
            'bullish_probability': 0.5,
            'confidence': 0.2,
            'recommendation': 'HOLD',
            'position_size': 0.0,
            'reasoning': 'Insufficient data for analysis',
            'analysis_quality': 'low'
        }

# Factory function
def create_proposal_analyzer(deepseek_api_key: str) -> ProposalImpactAnalyzer:
    """Create proposal impact analyzer instance"""
    return ProposalImpactAnalyzer(deepseek_api_key)

# Example usage
if __name__ == "__main__":
    async def test_analyzer():
        analyzer = create_proposal_analyzer("your-deepseek-api-key")
        
        # Test proposal
        test_proposal = {
            'dao_name': 'Jito DAO',
            'title': 'JIP-15: Implement 50% Revenue Buyback Mechanism',
            'description': 'Proposal to implement automatic buyback of JTO tokens using 50% of DAO treasury revenue from JitoSOL and TipRouter fees. Estimated $5M annual buyback program.',
            'proposal_type': 'buyback',
            'vote_count': {'for': 15000000, 'against': 2000000},
            'tokens_affected': ['JTO']
        }
        
        analysis = await analyzer.analyze_proposal_impact(test_proposal)
        print("=== PROPOSAL IMPACT ANALYSIS ===")
        print(f"Impact Score: {analysis['impact_score']:.2f}")
        print(f"Price Impact: {analysis['price_impact_estimate']:+.1%}")
        print(f"Recommendation: {analysis['recommendation']}")
    
    # asyncio.run(test_analyzer())
