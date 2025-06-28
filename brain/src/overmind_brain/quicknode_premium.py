"""
THE OVERMIND PROTOCOL - QuickNode Premium API Integration
Advanced Solana analytics and market data with QuickNode premium features
"""

import os
import asyncio
import aiohttp
import logging
import websockets
import json
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class QuickNodePremiumClient:
    """
    QuickNode Premium API client for advanced Solana analytics
    Provides market data streams, historical data, and performance optimization
    """
    
    def __init__(self):
        # Import environment loader for dynamic configuration
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config'))
            from environment_loader import get_environment_loader

            # Get dynamic configuration
            env_loader = get_environment_loader()
            config = env_loader.get_config()

            # Set configuration from environment loader
            self.api_key = os.getenv('QUICKNODE_API_KEY') or os.getenv('SNIPER_QUICKNODE_API_KEY')
            self.rpc_url = config.quicknode_rpc_url
            self.ws_url = config.quicknode_ws_url
            self.environment = env_loader.get_environment().value
            self.is_mainnet = config.is_mainnet
            self.network_name = config.network_name

            # Current URLs (already set by environment loader)
            self.current_rpc_url = self.rpc_url
            self.current_ws_url = self.ws_url

            logger.info(f"QuickNode Premium initialized for {self.network_name} ({self.environment})")

        except ImportError as e:
            logger.warning(f"Environment loader not available, using fallback configuration: {e}")
            # Fallback to old behavior
            self.api_key = os.getenv('QUICKNODE_API_KEY')
            self.rpc_url = os.getenv('QUICKNODE_RPC_URL', 'https://api.mainnet-beta.solana.com')
            self.devnet_rpc_url = os.getenv('QUICKNODE_DEVNET_RPC_URL', 'https://api.devnet.solana.com')
            self.ws_url = os.getenv('QUICKNODE_WS_URL', 'wss://api.mainnet-beta.solana.com')
            self.devnet_ws_url = os.getenv('QUICKNODE_DEVNET_WS_URL', 'wss://api.devnet.solana.com')

            # Use devnet by default for safety
            self.environment = os.getenv('SNIPER_ENVIRONMENT', 'devnet')
            self.current_rpc_url = self.devnet_rpc_url if self.environment == 'devnet' else self.rpc_url
            self.current_ws_url = self.devnet_ws_url if self.environment == 'devnet' else self.ws_url
            self.is_mainnet = self.environment != 'devnet'
            self.network_name = 'mainnet' if self.is_mainnet else 'devnet'
        
        if not self.api_key:
            logger.warning("QuickNode API key not found. Using basic RPC only.")
        
        self.session = None
        self.websocket = None
        
    async def initialize(self):
        """Initialize the QuickNode client"""
        self.session = aiohttp.ClientSession()
        logger.info(f"QuickNode Premium client initialized for {self.environment}")
    
    async def close(self):
        """Close the client and cleanup resources"""
        if self.session:
            await self.session.close()
        if self.websocket:
            await self.websocket.close()
    
    async def get_market_data_stream(self, symbols: List[str]) -> AsyncGenerator[Dict, None]:
        """
        Get real-time market data stream for specified symbols
        Premium feature: Enhanced market data with volume, OHLC, and analytics
        """
        try:
            if not self.api_key:
                logger.warning("API key required for premium market data stream")
                return
            
            # Connect to WebSocket with premium features
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'X-API-Key': self.api_key
            }
            
            async with websockets.connect(self.current_ws_url, extra_headers=headers) as websocket:
                # Subscribe to account updates for token accounts
                subscription = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "accountSubscribe",
                    "params": [
                        symbols[0] if symbols else "11111111111111111111111111111112",  # System program
                        {
                            "encoding": "jsonParsed",
                            "commitment": "confirmed"
                        }
                    ]
                }
                
                await websocket.send(json.dumps(subscription))
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        if 'result' in data:
                            logger.info(f"Subscribed to market data: {data['result']}")
                        elif 'params' in data:
                            # Process market data update
                            market_update = self._parse_market_update(data['params'])
                            if market_update:
                                yield market_update
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse WebSocket message: {message}")
                    except Exception as e:
                        logger.error(f"Error processing market data: {e}")
                        
        except Exception as e:
            logger.error(f"Market data stream error: {e}")
    
    async def get_historical_data(self, 
                                 token_address: str, 
                                 start_date: datetime, 
                                 end_date: datetime,
                                 interval: str = '1h') -> pd.DataFrame:
        """
        Get historical price and volume data for a token
        Premium feature: Historical data analysis
        """
        try:
            # QuickNode doesn't have direct historical price API, but we can get transaction history
            # and derive price data from DEX transactions
            transactions = await self.get_token_transactions(token_address, start_date, end_date)
            
            # Process transactions to extract price data
            price_data = []
            for tx in transactions:
                if self._is_dex_transaction(tx):
                    price_info = self._extract_price_from_transaction(tx)
                    if price_info:
                        price_data.append(price_info)
            
            # Convert to DataFrame and resample to requested interval
            if price_data:
                df = pd.DataFrame(price_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # Resample to requested interval
                resampled = df.resample(interval).agg({
                    'price': ['first', 'max', 'min', 'last'],
                    'volume': 'sum'
                }).round(6)
                
                # Flatten column names
                resampled.columns = ['open', 'high', 'low', 'close', 'volume']
                return resampled
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return pd.DataFrame()
    
    async def get_token_transactions(self, 
                                   token_address: str, 
                                   start_date: datetime, 
                                   end_date: datetime,
                                   limit: int = 1000) -> List[Dict]:
        """
        Get transaction history for a token
        Premium feature: Enhanced transaction data
        """
        try:
            # Use getSignaturesForAddress to get transaction signatures
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    token_address,
                    {
                        "limit": limit,
                        "commitment": "confirmed"
                    }
                ]
            }
            
            async with self.session.post(self.current_rpc_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data:
                        signatures = data['result']
                        
                        # Get detailed transaction data for each signature
                        transactions = []
                        for sig_info in signatures[:100]:  # Limit to avoid rate limits
                            tx_detail = await self.get_transaction_detail(sig_info['signature'])
                            if tx_detail:
                                transactions.append(tx_detail)
                        
                        return transactions
                    
        except Exception as e:
            logger.error(f"Error getting token transactions: {e}")
            
        return []
    
    async def get_transaction_detail(self, signature: str) -> Optional[Dict]:
        """Get detailed transaction information"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            
            async with self.session.post(self.current_rpc_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data and data['result']:
                        return data['result']
                        
        except Exception as e:
            logger.error(f"Error getting transaction detail: {e}")
            
        return None
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get QuickNode performance metrics
        Premium feature: Performance monitoring
        """
        try:
            # Test latency with multiple requests
            latencies = []
            for _ in range(5):
                start_time = datetime.now()
                
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSlot"
                }
                
                async with self.session.post(self.current_rpc_url, json=payload) as response:
                    if response.status == 200:
                        latency = (datetime.now() - start_time).total_seconds() * 1000
                        latencies.append(latency)
            
            return {
                'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
                'min_latency_ms': min(latencies) if latencies else 0,
                'max_latency_ms': max(latencies) if latencies else 0,
                'success_rate': len(latencies) / 5 * 100,
                'timestamp': datetime.utcnow().isoformat(),
                'environment': self.environment
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}
    
    def _parse_market_update(self, params: Dict) -> Optional[Dict]:
        """Parse market data update from WebSocket"""
        try:
            if 'result' in params:
                account_info = params['result']['value']
                return {
                    'type': 'account_update',
                    'account': params['result']['context']['slot'],
                    'data': account_info,
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Error parsing market update: {e}")
        return None
    
    def _is_dex_transaction(self, transaction: Dict) -> bool:
        """Check if transaction is a DEX trade"""
        try:
            # Look for common DEX program IDs
            dex_programs = [
                '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',  # Serum DEX
                'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4',   # Jupiter
                '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',   # Raydium
            ]
            
            if 'transaction' in transaction and 'message' in transaction['transaction']:
                instructions = transaction['transaction']['message'].get('instructions', [])
                for instruction in instructions:
                    if instruction.get('programId') in dex_programs:
                        return True
                        
        except Exception as e:
            logger.error(f"Error checking DEX transaction: {e}")
            
        return False
    
    def _extract_price_from_transaction(self, transaction: Dict) -> Optional[Dict]:
        """Extract price information from DEX transaction"""
        try:
            # This is a simplified extraction - in practice, you'd need to parse
            # the specific DEX instruction data to get accurate price information
            block_time = transaction.get('blockTime')
            if block_time:
                return {
                    'timestamp': datetime.fromtimestamp(block_time),
                    'price': 100.0,  # Placeholder - would extract from instruction data
                    'volume': 1000.0,  # Placeholder - would extract from instruction data
                    'signature': transaction.get('transaction', {}).get('signatures', [''])[0]
                }
                
        except Exception as e:
            logger.error(f"Error extracting price from transaction: {e}")
            
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get QuickNode integration status"""
        return {
            'api_key_configured': bool(self.api_key),
            'environment': self.environment,
            'rpc_url': self.current_rpc_url.split('?')[0] if self.current_rpc_url else None,
            'ws_url': self.current_ws_url.split('?')[0] if self.current_ws_url else None,
            'premium_features_available': [
                'market_data_stream',
                'historical_data',
                'transaction_history',
                'performance_metrics',
                'enhanced_analytics'
            ] if self.api_key else ['basic_rpc_only']
        }

# Global QuickNode Premium client instance
quicknode_premium = QuickNodePremiumClient()

async def get_market_analytics(token_address: str) -> Dict[str, Any]:
    """
    Get comprehensive market analytics for a token using QuickNode premium features
    """
    try:
        # Get performance metrics
        performance = await quicknode_premium.get_performance_metrics()
        
        # Get recent transaction data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)
        transactions = await quicknode_premium.get_token_transactions(
            token_address, start_date, end_date, limit=100
        )
        
        # Get historical price data
        historical_data = await quicknode_premium.get_historical_data(
            token_address, start_date, end_date, interval='1h'
        )
        
        return {
            'token_address': token_address,
            'performance_metrics': performance,
            'transaction_count_24h': len(transactions),
            'historical_data_points': len(historical_data) if not historical_data.empty else 0,
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'quicknode_premium'
        }
        
    except Exception as e:
        logger.error(f"Error getting market analytics: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'quicknode_premium'
        }
