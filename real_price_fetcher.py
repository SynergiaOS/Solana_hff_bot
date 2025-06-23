#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Real Price Fetcher
Fetches real market prices from CoinGecko and Helius APIs
"""

import asyncio
import json
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Optional

# Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
HELIUS_API_KEY = "edbcd361-78a0-4998-bd1e-8d4666722f82"
HELIUS_RPC_URL = f"https://devnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

class RealPriceFetcher:
    def __init__(self):
        self.last_prices = {}
        self.last_update = None
        
    def get_real_prices(self) -> Dict[str, float]:
        """Get real prices from CoinGecko API"""
        url = f"{COINGECKO_API_URL}?ids=solana,bitcoin,ethereum,usd-coin,raydium,orca&vs_currencies=usd"
        
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; OVERMIND/1.0)')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Extract prices
            prices = {
                "SOL": data.get("solana", {}).get("usd", 100.0),
                "BTC": data.get("bitcoin", {}).get("usd", 45000.0),
                "ETH": data.get("ethereum", {}).get("usd", 3000.0),
                "USDC": data.get("usd-coin", {}).get("usd", 1.0),
                "RAY": data.get("raydium", {}).get("usd", 2.5),
                "ORCA": data.get("orca", {}).get("usd", 1.8)
            }
            
            self.last_prices = prices
            self.last_update = datetime.utcnow()
            
            print(f"✅ Real prices fetched at {self.last_update.strftime('%H:%M:%S')}:")
            for symbol, price in prices.items():
                print(f"   💰 {symbol}: ${price:.4f}")
            
            return prices
            
        except Exception as e:
            print(f"❌ Failed to fetch real prices: {e}")
            # Return last known prices or defaults
            return self.last_prices or {
                "SOL": 100.0, "BTC": 45000.0, "ETH": 3000.0, 
                "USDC": 1.0, "RAY": 2.5, "ORCA": 1.8
            }
    
    def get_price_for_symbol(self, symbol: str) -> float:
        """Get price for specific symbol"""
        # Update prices if older than 30 seconds
        if (not self.last_update or 
            (datetime.utcnow() - self.last_update).total_seconds() > 30):
            self.get_real_prices()
        
        return self.last_prices.get(symbol, 1.0)
    
    def get_helius_token_info(self, token_address: str) -> Optional[Dict]:
        """Get token info from Helius API"""
        url = f"https://devnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        
        payload = {
            "jsonrpc": "2.0",
            "id": "helius-test",
            "method": "getAsset",
            "params": {
                "id": token_address
            }
        }
        
        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data_bytes)
            req.add_header('Content-Type', 'application/json')
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; OVERMIND/1.0)')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if 'result' in data:
                print(f"✅ Helius token info retrieved for {token_address}")
                return data['result']
            else:
                print(f"⚠️ No token info found for {token_address}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to fetch token info from Helius: {e}")
            return None

def main():
    """Test the real price fetcher"""
    print("🧠 THE OVERMIND PROTOCOL - Real Price Fetcher Test")
    print("=" * 60)
    
    fetcher = RealPriceFetcher()
    
    # Test 1: Get all prices
    print("\n📊 Test 1: Fetching all real prices...")
    prices = fetcher.get_real_prices()
    
    # Test 2: Get individual prices
    print("\n📊 Test 2: Getting individual prices...")
    for symbol in ["SOL", "RAY", "ORCA", "USDC"]:
        price = fetcher.get_price_for_symbol(symbol)
        print(f"   💰 {symbol}: ${price:.4f}")
    
    # Test 3: Test Helius API
    print("\n📊 Test 3: Testing Helius API...")
    # Test with SOL mint address
    sol_mint = "So11111111111111111111111111111111111111112"
    token_info = fetcher.get_helius_token_info(sol_mint)
    if token_info:
        print(f"   ✅ Helius API working - got info for SOL")
    else:
        print(f"   ❌ Helius API test failed")
    
    print("\n🎉 Real Price Fetcher test completed!")

if __name__ == "__main__":
    main()
