#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - On-Chain Analytics
Whale tracking and large transaction monitoring for Post-Trade Intelligence
"""

import asyncio
import json
import time
import redis
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OnChainAnalytics:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        self.whale_cache = {}
        self.large_transactions = {}
        
        # APIs
        self.helius_api_key = "edbcd361-78a0-4998-bd1e-8d4666722f82"
        self.helius_url = f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}"
        
        # Token mint addresses
        self.token_mints = {
            'SOL': 'So11111111111111111111111111111111111111112',
            'BONK': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
            'RAY': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',
            'ORCA': 'orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE',
            'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
        }
        
        # Whale thresholds (USD value)
        self.whale_thresholds = {
            'SOL': 100000,    # $100k+ SOL transactions
            'BONK': 50000,    # $50k+ BONK transactions
            'RAY': 25000,     # $25k+ RAY transactions
            'ORCA': 25000,    # $25k+ ORCA transactions
            'USDC': 100000    # $100k+ USDC transactions
        }
    
    async def get_large_transactions(self, symbol: str, limit: int = 20) -> List[Dict]:
        """Get large transactions for a specific token"""
        try:
            mint_address = self.token_mints.get(symbol)
            if not mint_address:
                return []
            
            # Use Helius Enhanced Transactions API
            payload = {
                "jsonrpc": "2.0",
                "id": "helius-test",
                "method": "getSignaturesForAddress",
                "params": [
                    mint_address,
                    {
                        "limit": limit,
                        "commitment": "confirmed"
                    }
                ]
            }
            
            response = requests.post(self.helius_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                signatures = data.get('result', [])
                
                # Get transaction details for each signature
                large_txs = []
                for sig_info in signatures[:10]:  # Limit to 10 most recent
                    signature = sig_info['signature']
                    tx_details = await self.get_transaction_details(signature)
                    
                    if tx_details and self.is_whale_transaction(tx_details, symbol):
                        large_txs.append(tx_details)
                
                return large_txs
                
        except Exception as e:
            logger.error(f"❌ Error fetching large transactions for {symbol}: {e}")
            
        return []
    
    async def get_transaction_details(self, signature: str) -> Optional[Dict]:
        """Get detailed transaction information"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": "helius-test",
                "method": "getTransaction",
                "params": [
                    signature,
                    {
                        "encoding": "json",
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            
            response = requests.post(self.helius_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result')
                
        except Exception as e:
            logger.error(f"❌ Error fetching transaction details for {signature}: {e}")
            
        return None
    
    def is_whale_transaction(self, tx_details: Dict, symbol: str) -> bool:
        """Determine if transaction qualifies as whale activity"""
        try:
            if not tx_details or 'meta' not in tx_details:
                return False
            
            meta = tx_details['meta']
            
            # Check for large SOL transfers
            if symbol == 'SOL':
                pre_balances = meta.get('preBalances', [])
                post_balances = meta.get('postBalances', [])
                
                for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
                    balance_change = abs(post - pre) / 1e9  # Convert lamports to SOL
                    
                    # Estimate USD value (assuming $150 SOL)
                    usd_value = balance_change * 150
                    
                    if usd_value >= self.whale_thresholds[symbol]:
                        return True
            
            # Check token transfers in transaction
            if 'postTokenBalances' in meta and 'preTokenBalances' in meta:
                pre_token_balances = meta['preTokenBalances']
                post_token_balances = meta['postTokenBalances']
                
                # Look for significant token balance changes
                for post_balance in post_token_balances:
                    mint = post_balance.get('mint')
                    if mint == self.token_mints.get(symbol):
                        # Find corresponding pre-balance
                        account = post_balance.get('owner')
                        pre_amount = 0
                        
                        for pre_balance in pre_token_balances:
                            if pre_balance.get('owner') == account and pre_balance.get('mint') == mint:
                                pre_amount = float(pre_balance.get('uiTokenAmount', {}).get('uiAmount', 0))
                                break
                        
                        post_amount = float(post_balance.get('uiTokenAmount', {}).get('uiAmount', 0))
                        amount_change = abs(post_amount - pre_amount)
                        
                        # Estimate USD value (simplified)
                        token_price = self.get_estimated_token_price(symbol)
                        usd_value = amount_change * token_price
                        
                        if usd_value >= self.whale_thresholds.get(symbol, 50000):
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error analyzing whale transaction: {e}")
            return False
    
    def get_estimated_token_price(self, symbol: str) -> float:
        """Get estimated token price for whale calculation"""
        # Simplified price estimates (should use real-time data)
        price_estimates = {
            'SOL': 150.0,
            'BONK': 0.000025,
            'RAY': 2.5,
            'ORCA': 3.5,
            'USDC': 1.0
        }
        return price_estimates.get(symbol, 1.0)
    
    def analyze_whale_activity(self, transactions: List[Dict], symbol: str) -> Dict:
        """Analyze whale activity patterns"""
        if not transactions:
            return {
                'symbol': symbol,
                'whale_count': 0,
                'total_volume': 0,
                'buy_pressure': 0.5,
                'sell_pressure': 0.5,
                'signals': [],
                'last_update': time.time()
            }
        
        buy_volume = 0
        sell_volume = 0
        whale_count = len(transactions)
        
        # Simplified analysis (in real implementation, would analyze actual transfer directions)
        for tx in transactions:
            # Estimate volume and direction
            estimated_volume = 100000  # Placeholder
            
            # Random assignment for demo (should analyze actual transaction data)
            if hash(tx.get('signature', '')) % 2 == 0:
                buy_volume += estimated_volume
            else:
                sell_volume += estimated_volume
        
        total_volume = buy_volume + sell_volume
        
        if total_volume > 0:
            buy_pressure = buy_volume / total_volume
            sell_pressure = sell_volume / total_volume
        else:
            buy_pressure = 0.5
            sell_pressure = 0.5
        
        # Generate signals
        signals = []
        if whale_count >= 3:
            signals.append('HIGH_WHALE_ACTIVITY')
        
        if buy_pressure > 0.7:
            signals.append('WHALE_ACCUMULATION')
        elif sell_pressure > 0.7:
            signals.append('WHALE_DISTRIBUTION')
        
        return {
            'symbol': symbol,
            'whale_count': whale_count,
            'total_volume': total_volume,
            'buy_pressure': buy_pressure,
            'sell_pressure': sell_pressure,
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'signals': signals,
            'transactions': transactions[:3],  # Keep top 3 for reference
            'last_update': time.time()
        }
    
    async def monitor_symbol_whales(self, symbol: str) -> Dict:
        """Monitor whale activity for a specific symbol"""
        try:
            logger.info(f"🐋 Monitoring whale activity for {symbol}...")
            
            # Get large transactions
            large_txs = await self.get_large_transactions(symbol)
            
            # Analyze whale activity
            whale_analysis = self.analyze_whale_activity(large_txs, symbol)
            
            return whale_analysis
            
        except Exception as e:
            logger.error(f"❌ Error monitoring whales for {symbol}: {e}")
            return {
                'symbol': symbol,
                'whale_count': 0,
                'total_volume': 0,
                'buy_pressure': 0.5,
                'sell_pressure': 0.5,
                'signals': [],
                'error': str(e),
                'last_update': time.time()
            }
    
    async def monitor_all_symbols(self, symbols: List[str]) -> Dict:
        """Monitor whale activity for all symbols"""
        whale_analytics = {}
        
        for symbol in symbols:
            whale_data = await self.monitor_symbol_whales(symbol)
            whale_analytics[symbol] = whale_data
            
            # Delay to avoid rate limiting
            await asyncio.sleep(3)
        
        return whale_analytics
    
    async def publish_whale_analytics(self, analytics_data: Dict):
        """Publish whale analytics to Redis"""
        try:
            analytics_update = {
                'timestamp': time.time(),
                'whale_analytics': analytics_data,
                'update_type': 'whale_analytics'
            }
            
            self.redis_client.lpush('overmind:whale_analytics', json.dumps(analytics_update))
            
            # Keep only last 50 updates
            self.redis_client.ltrim('overmind:whale_analytics', 0, 49)
            
        except Exception as e:
            logger.error(f"❌ Error publishing whale analytics: {e}")
    
    def print_whale_summary(self, analytics_data: Dict):
        """Print whale analytics summary"""
        print("\n🐋 THE OVERMIND PROTOCOL - WHALE ANALYTICS")
        print("=" * 60)
        
        for symbol, data in analytics_data.items():
            whale_count = data['whale_count']
            buy_pressure = data['buy_pressure']
            sell_pressure = data['sell_pressure']
            signals = data.get('signals', [])
            
            # Pressure indicator
            if buy_pressure > 0.6:
                pressure_indicator = "🟢 BUYING"
            elif sell_pressure > 0.6:
                pressure_indicator = "🔴 SELLING"
            else:
                pressure_indicator = "⚪ NEUTRAL"
            
            print(f"{pressure_indicator} {symbol}: {whale_count} whales | "
                  f"Buy: {buy_pressure:.1%} | Sell: {sell_pressure:.1%}")
            
            if signals:
                print(f"   📊 Signals: {', '.join(signals)}")
        
        print(f"🔄 Last Update: {datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')}")
    
    async def whale_monitoring_loop(self):
        """Main whale monitoring loop"""
        logger.info("🚀 Starting Whale Analytics Monitor...")
        
        symbols = ['SOL', 'BONK', 'RAY', 'ORCA', 'USDC']
        
        while True:
            try:
                # Monitor whale activity for all symbols
                analytics_data = await self.monitor_all_symbols(symbols)
                
                # Publish to Redis
                await self.publish_whale_analytics(analytics_data)
                
                # Print summary
                self.print_whale_summary(analytics_data)
                
                # Wait 10 minutes before next update
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"❌ Error in whale monitoring loop: {e}")
                await asyncio.sleep(120)

async def main():
    whale_analytics = OnChainAnalytics()
    await whale_analytics.whale_monitoring_loop()

if __name__ == "__main__":
    asyncio.run(main())
