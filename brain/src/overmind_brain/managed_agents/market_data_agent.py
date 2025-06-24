"""THE OVERMIND PROTOCOL - Market Data Agent
Specialized agent for fetching and analyzing real-time market data.
"""

import logging
from typing import Dict, Any, Optional, List

# Try to import MinionAgent, fall back to mock if not available
try:
    from minion_agent import AgentConfig, MinionAgent
except ImportError:
    from ..mock_minion_agent import AgentConfig, MinionAgent

from ..tools.market_data_tool import (
    get_sol_price,
    get_multiple_prices,
    get_price_with_volume,
    get_asset_info_from_helius
)

logger = logging.getLogger(__name__)

class MarketDataAgent:
    """Specialized agent for market data operations using MinionAgent framework."""
    
    def __init__(self):
        """Initialize the MarketDataAgent with proper configuration."""
        self.config = AgentConfig(
            name="market_data_agent",
            description="Agent specialized in fetching and analyzing real-time market data from Helius, CoinGecko, and DexScreener",
            model_id="deepseek/deepseek-reasoner",
            agent_type="CodeAgent",
            tools=[
                "get_sol_price",
                "get_multiple_prices", 
                "get_price_with_volume",
                "get_asset_info_from_helius"
            ]
        )
        
        # Initialize the MinionAgent with our config
        self.agent = MinionAgent(self.config)
        
        # Register our tools with the agent
        self._register_tools()
    
    def _register_tools(self):
        """Register market data tools with the MinionAgent."""
        # Register our async tools with the agent
        self.agent.register_tool("get_sol_price", get_sol_price)
        self.agent.register_tool("get_multiple_prices", get_multiple_prices)
        self.agent.register_tool("get_price_with_volume", get_price_with_volume)
        self.agent.register_tool("get_asset_info_from_helius", get_asset_info_from_helius)
    
    async def fetch_token_data(self, token_address: str) -> Dict[str, Any]:
        """Fetch comprehensive token data for a specific address.
        
        Args:
            token_address: The token mint address to analyze
            
        Returns:
            Dict containing comprehensive token analysis
        """
        prompt = f"""
        Analyze the token at address {token_address}. Please:
        1. Fetch token metadata from Helius
        2. Get current price data if available
        3. Analyze the token's basic characteristics
        4. Provide a risk assessment based on available data
        
        Return a comprehensive analysis in JSON format.
        """
        
        try:
            result = await self.agent.execute(prompt)
            logger.info(f"📊 Token data fetched for {token_address}")
            return result
        except Exception as e:
            logger.error(f"❌ Error fetching token data for {token_address}: {e}")
            return {"error": str(e), "token_address": token_address}
    
    async def fetch_market_overview(self) -> Dict[str, Any]:
        """Fetch comprehensive market overview.
        
        Returns:
            Dict containing market analysis
        """
        prompt = """
        Provide a comprehensive market overview. Please:
        1. Get prices for major cryptocurrencies (SOL, BTC, ETH, USDC)
        2. Get extended market data for SOL including volume and market cap
        3. Analyze current market conditions
        4. Provide trading sentiment assessment
        
        Return analysis in JSON format with clear structure.
        """
        
        try:
            result = await self.agent.execute(prompt)
            logger.info("📊 Market overview fetched successfully")
            return result
        except Exception as e:
            logger.error(f"❌ Error fetching market overview: {e}")
            return {"error": str(e)}
    
    async def analyze_price_movement(self, symbol: str = "solana") -> Dict[str, Any]:
        """Analyze price movement and trends for a specific asset.
        
        Args:
            symbol: Asset symbol to analyze (default: solana)
            
        Returns:
            Dict containing price movement analysis
        """
        prompt = f"""
        Analyze price movement for {symbol}. Please:
        1. Get current price with volume data
        2. Analyze 24h price change percentage
        3. Assess volume trends
        4. Provide trading signals based on the data
        
        Return analysis in JSON format with actionable insights.
        """
        
        try:
            result = await self.agent.execute(prompt)
            logger.info(f"📊 Price movement analysis completed for {symbol}")
            return result
        except Exception as e:
            logger.error(f"❌ Error analyzing price movement for {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
    
    async def get_trading_pairs_analysis(self, token_addresses: List[str]) -> Dict[str, Any]:
        """Analyze multiple trading pairs simultaneously.
        
        Args:
            token_addresses: List of token addresses to analyze
            
        Returns:
            Dict containing comparative analysis
        """
        prompt = f"""
        Analyze multiple trading pairs: {token_addresses}. Please:
        1. Fetch metadata for each token from Helius
        2. Compare their characteristics
        3. Identify the most promising opportunities
        4. Provide risk-adjusted recommendations
        
        Return comparative analysis in JSON format.
        """
        
        try:
            result = await self.agent.execute(prompt)
            logger.info(f"📊 Trading pairs analysis completed for {len(token_addresses)} tokens")
            return result
        except Exception as e:
            logger.error(f"❌ Error analyzing trading pairs: {e}")
            return {"error": str(e), "token_addresses": token_addresses}

# Factory function for easy instantiation
def create_market_data_agent() -> MarketDataAgent:
    """Create and return a configured MarketDataAgent instance."""
    return MarketDataAgent()