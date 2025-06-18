"""
THE OVERMIND PROTOCOL - Helius API Premium Integration
Enhanced Solana data access with Helius premium features
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class HeliusAPIClient:
    """
    Helius API Premium client for enhanced Solana data access
    Provides advanced features like enhanced transactions, NFT data, and DAS API
    """
    
    def __init__(self):
        self.api_key = os.getenv('HELIUS_API_KEY')
        self.rpc_url = os.getenv('HELIUS_RPC_URL', 'https://mainnet.helius-rpc.com')
        self.devnet_rpc_url = os.getenv('HELIUS_DEVNET_RPC_URL', 'https://devnet.helius-rpc.com')
        self.ws_url = os.getenv('HELIUS_WS_URL', 'wss://mainnet.helius-rpc.com')
        self.devnet_ws_url = os.getenv('HELIUS_DEVNET_WS_URL', 'wss://devnet.helius-rpc.com')
        
        # Use devnet by default for safety
        self.environment = os.getenv('SNIPER_ENVIRONMENT', 'devnet')
        self.current_rpc_url = self.devnet_rpc_url if self.environment == 'devnet' else self.rpc_url
        
        if not self.api_key:
            logger.warning("Helius API key not found. Some features may be limited.")
        
        # Add API key to URLs if available
        if self.api_key:
            self.current_rpc_url = f"{self.current_rpc_url}/?api-key={self.api_key}"
    
    async def get_enhanced_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """
        Get enhanced transaction data for an address using Helius premium features
        """
        try:
            url = f"{self.current_rpc_url.split('?')[0]}/v0/addresses/{address}/transactions"
            params = {
                'api-key': self.api_key,
                'limit': limit,
                'commitment': 'confirmed'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Retrieved {len(data)} enhanced transactions for {address}")
                        return data
                    else:
                        logger.error(f"Failed to get enhanced transactions: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting enhanced transactions: {e}")
            return []
    
    async def get_token_metadata(self, mint_address: str) -> Optional[Dict]:
        """
        Get comprehensive token metadata using Helius DAS API
        """
        try:
            url = f"{self.current_rpc_url.split('?')[0]}/v0/token-metadata"
            params = {
                'api-key': self.api_key,
                'mint-accounts': [mint_address]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and len(data) > 0:
                            logger.info(f"Retrieved metadata for token {mint_address}")
                            return data[0]
                    else:
                        logger.error(f"Failed to get token metadata: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting token metadata: {e}")
            return None
    
    async def get_nft_events(self, collection_id: str, limit: int = 50) -> List[Dict]:
        """
        Get NFT events for a collection using Helius premium features
        """
        try:
            url = f"{self.current_rpc_url.split('?')[0]}/v1/nft-events"
            params = {
                'api-key': self.api_key,
                'accounts': [collection_id],
                'limit': limit,
                'commitment': 'confirmed'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Retrieved {len(data)} NFT events for collection {collection_id}")
                        return data
                    else:
                        logger.error(f"Failed to get NFT events: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting NFT events: {e}")
            return []
    
    async def get_webhook_data(self, webhook_id: str) -> Optional[Dict]:
        """
        Get webhook configuration and data
        """
        try:
            url = f"{self.current_rpc_url.split('?')[0]}/v0/webhooks/{webhook_id}"
            params = {'api-key': self.api_key}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Retrieved webhook data for {webhook_id}")
                        return data
                    else:
                        logger.error(f"Failed to get webhook data: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting webhook data: {e}")
            return None
    
    async def search_assets(self, query: Dict) -> List[Dict]:
        """
        Search for assets using Helius DAS API
        """
        try:
            url = f"{self.current_rpc_url.split('?')[0]}/v0/assets/search"
            
            payload = {
                'jsonrpc': '2.0',
                'id': 'search-assets',
                'method': 'searchAssets',
                'params': query
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}' if self.api_key else ''
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            logger.info(f"Found {len(data['result']['items'])} assets")
                            return data['result']['items']
                    else:
                        logger.error(f"Failed to search assets: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching assets: {e}")
            return []
    
    async def get_priority_fee_estimate(self, account_keys: List[str]) -> Optional[Dict]:
        """
        Get priority fee estimates for transactions
        """
        try:
            url = self.current_rpc_url
            
            payload = {
                'jsonrpc': '2.0',
                'id': 'priority-fee',
                'method': 'getPriorityFeeEstimate',
                'params': [
                    {
                        'accountKeys': account_keys,
                        'options': {
                            'includeAllPriorityFeeLevels': True
                        }
                    }
                ]
            }
            
            headers = {'Content-Type': 'application/json'}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            logger.info("Retrieved priority fee estimate")
                            return data['result']
                    else:
                        logger.error(f"Failed to get priority fee estimate: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting priority fee estimate: {e}")
            return None
    
    async def get_compressed_nft_proof(self, asset_id: str) -> Optional[Dict]:
        """
        Get proof for compressed NFT
        """
        try:
            url = self.current_rpc_url
            
            payload = {
                'jsonrpc': '2.0',
                'id': 'compressed-nft-proof',
                'method': 'getAssetProof',
                'params': {
                    'id': asset_id
                }
            }
            
            headers = {'Content-Type': 'application/json'}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            logger.info(f"Retrieved compressed NFT proof for {asset_id}")
                            return data['result']
                    else:
                        logger.error(f"Failed to get compressed NFT proof: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting compressed NFT proof: {e}")
            return None
    
    async def get_token_accounts_by_owner(self, owner: str, mint: Optional[str] = None) -> List[Dict]:
        """
        Get token accounts owned by an address
        """
        try:
            url = self.current_rpc_url
            
            params = {'owner': owner}
            if mint:
                params['mint'] = mint
            
            payload = {
                'jsonrpc': '2.0',
                'id': 'token-accounts',
                'method': 'getTokenAccountsByOwner',
                'params': [
                    owner,
                    {'mint': mint} if mint else {'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'},
                    {'encoding': 'jsonParsed'}
                ]
            }
            
            headers = {'Content-Type': 'application/json'}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            accounts = data['result']['value']
                            logger.info(f"Retrieved {len(accounts)} token accounts for {owner}")
                            return accounts
                    else:
                        logger.error(f"Failed to get token accounts: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting token accounts: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get Helius integration status
        """
        return {
            'api_key_configured': bool(self.api_key),
            'environment': self.environment,
            'rpc_url': self.current_rpc_url.split('?')[0] if self.current_rpc_url else None,
            'features_available': [
                'enhanced_transactions',
                'token_metadata',
                'nft_events',
                'asset_search',
                'priority_fees',
                'compressed_nfts',
                'token_accounts'
            ] if self.api_key else ['basic_rpc_only']
        }

# Global Helius client instance
helius_client = HeliusAPIClient()

async def get_enhanced_token_data(mint_address: str) -> Dict[str, Any]:
    """
    Get comprehensive token data using Helius premium features
    """
    try:
        # Get basic metadata
        metadata = await helius_client.get_token_metadata(mint_address)
        
        # Get recent transactions
        transactions = await helius_client.get_enhanced_transactions(mint_address, limit=50)
        
        # Get priority fee estimates
        priority_fees = await helius_client.get_priority_fee_estimate([mint_address])
        
        return {
            'mint_address': mint_address,
            'metadata': metadata,
            'recent_transactions': transactions,
            'priority_fees': priority_fees,
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'helius_premium'
        }
    except Exception as e:
        logger.error(f"Error getting enhanced token data: {e}")
        return {
            'mint_address': mint_address,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'helius_premium'
        }

async def monitor_wallet_activity(wallet_address: str, callback=None) -> Dict[str, Any]:
    """
    Monitor wallet activity using Helius enhanced features
    """
    try:
        # Get recent transactions
        transactions = await helius_client.get_enhanced_transactions(wallet_address, limit=100)
        
        # Get token accounts
        token_accounts = await helius_client.get_token_accounts_by_owner(wallet_address)
        
        activity_summary = {
            'wallet_address': wallet_address,
            'total_transactions': len(transactions),
            'token_accounts_count': len(token_accounts),
            'recent_activity': transactions[:10] if transactions else [],
            'token_holdings': token_accounts,
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'helius_premium'
        }
        
        if callback:
            await callback(activity_summary)
        
        return activity_summary
    except Exception as e:
        logger.error(f"Error monitoring wallet activity: {e}")
        return {
            'wallet_address': wallet_address,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat(),
            'data_source': 'helius_premium'
        }
