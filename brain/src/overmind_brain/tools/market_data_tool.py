"""THE OVERMIND PROTOCOL - Market Data Tool
Tools for fetching real-time market data from various sources.
"""

import asyncio
import logging
import os
from typing import Optional, Dict, Any
import json

# Use urllib for simple HTTP requests to avoid certificate issues
import urllib.request
import urllib.parse
import urllib.error

# Setup logging
logger = logging.getLogger(__name__)

async def get_sol_price() -> Optional[float]:
    """Get current SOL/USD price from CoinGecko API.

    Returns:
        float: Current SOL price in USD, or None if failed
    """
    url = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"

    try:
        # Use urllib for simple HTTP requests
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; OVERMIND/1.0)')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Extract SOL price
        sol_price = data.get("solana", {}).get("usd")

        if sol_price is not None:
            logger.info(f"📊 SOL Price: ${sol_price:.4f}")
            return float(sol_price)
        else:
            logger.error("❌ SOL price not found in API response")
            return None

    except urllib.error.HTTPError as e:
        logger.error(f"❌ HTTP Error fetching SOL price: {e.code} - {e.reason}")
        return None
    except urllib.error.URLError as e:
        logger.error(f"❌ URL Error fetching SOL price: {e.reason}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to fetch SOL price: {e}")
        return None

async def get_asset_info_from_helius(token_address: str) -> Optional[Dict[str, Any]]:
    """Get asset information from Helius API.

    Args:
        token_address: The token mint address

    Returns:
        dict: Asset information, or None if failed
    """
    helius_api_url = os.getenv("HELIUS_API_URL", "https://api.helius.xyz/v0")
    helius_api_key = os.getenv("HELIUS_API_KEY")

    if not helius_api_key:
        logger.error("❌ HELIUS_API_KEY not found in environment variables")
        return None

    url = f"{helius_api_url}/token-metadata"

    payload = {
        "mintAccounts": [token_address]
    }

    # Add API key to URL
    url_with_key = f"{url}?api-key={helius_api_key}"

    try:
        # Use urllib for HTTP POST request
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url_with_key, data=data_bytes)
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; OVERMIND/1.0)')

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data and len(data) > 0:
            asset_info = data[0]
            logger.info(f"📊 Asset info retrieved for {token_address}")
            return asset_info
        else:
            logger.warning(f"⚠️ No asset info found for {token_address}")
            return None

    except urllib.error.HTTPError as e:
        logger.error(f"❌ HTTP Error fetching asset info: {e.code} - {e.reason}")
        return None
    except urllib.error.URLError as e:
        logger.error(f"❌ URL Error fetching asset info: {e.reason}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to fetch asset info from Helius: {e}")
        return None

async def get_multiple_prices() -> Dict[str, Optional[float]]:
    """Get prices for multiple cryptocurrencies.

    Returns:
        dict: Mapping of symbol to price
    """
    url = "https://api.coingecko.com/api/v3/simple/price?ids=solana,bitcoin,ethereum,usd-coin&vs_currencies=usd"

    try:
        # Use urllib for simple HTTP requests
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; OVERMIND/1.0)')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Extract prices
        prices = {
            "SOL": data.get("solana", {}).get("usd"),
            "BTC": data.get("bitcoin", {}).get("usd"),
            "ETH": data.get("ethereum", {}).get("usd"),
            "USDC": data.get("usd-coin", {}).get("usd")
        }

        logger.info(f"📊 Multiple prices fetched: {prices}")
        return prices

    except urllib.error.HTTPError as e:
        logger.error(f"❌ HTTP Error fetching multiple prices: {e.code} - {e.reason}")
        return {"SOL": None, "BTC": None, "ETH": None, "USDC": None}
    except urllib.error.URLError as e:
        logger.error(f"❌ URL Error fetching multiple prices: {e.reason}")
        return {"SOL": None, "BTC": None, "ETH": None, "USDC": None}
    except Exception as e:
        logger.error(f"❌ Failed to fetch multiple prices: {e}")
        return {"SOL": None, "BTC": None, "ETH": None, "USDC": None}

async def get_price_with_volume(symbol: str = "solana") -> Optional[Dict[str, Any]]:
    """Get price with additional market data including volume.

    Args:
        symbol: CoinGecko symbol (default: solana)

    Returns:
        dict: Price and market data, or None if failed
    """
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}"

    try:
        # Use urllib for simple HTTP requests
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; OVERMIND/1.0)')

        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Extract relevant market data
        market_data = data.get("market_data", {})

        result = {
            "symbol": symbol.upper(),
            "price_usd": market_data.get("current_price", {}).get("usd"),
            "volume_24h": market_data.get("total_volume", {}).get("usd"),
            "market_cap": market_data.get("market_cap", {}).get("usd"),
            "price_change_24h": market_data.get("price_change_percentage_24h"),
            "last_updated": data.get("last_updated")
        }

        logger.info(f"📊 Extended market data for {symbol}: ${result['price_usd']:.4f}")
        return result

    except urllib.error.HTTPError as e:
        logger.error(f"❌ HTTP Error fetching extended market data: {e.code} - {e.reason}")
        return None
    except urllib.error.URLError as e:
        logger.error(f"❌ URL Error fetching extended market data: {e.reason}")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to fetch extended market data for {symbol}: {e}")
        return None

# Test function
async def test_market_data_tools():
    """Test all market data functions"""
    logger.info("🧪 Testing market data tools...")
    
    # Test SOL price
    sol_price = await get_sol_price()
    print(f"SOL Price: ${sol_price}")
    
    # Test multiple prices
    prices = await get_multiple_prices()
    print(f"Multiple Prices: {prices}")
    
    # Test extended data
    extended_data = await get_price_with_volume()
    print(f"Extended Data: {extended_data}")
    
    # Test Helius (if API key available)
    sol_mint = "So11111111111111111111111111111111111111112"  # SOL mint address
    helius_data = await get_asset_info_from_helius(sol_mint)
    print(f"Helius Data: {helius_data}")

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_market_data_tools())
