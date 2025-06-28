"""
THE OVERMIND PROTOCOL - Premium API Manager
Unified management of Helius and QuickNode premium features
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import pandas as pd

from .helius_integration import (
    helius_client, 
    get_enhanced_token_data, 
    monitor_wallet_activity,
    get_defi_analytics,
    get_historical_token_data,
    parse_transaction_details
)
from .quicknode_premium import quicknode_premium, get_market_analytics

logger = logging.getLogger(__name__)

class PremiumAPIManager:
    """
    Unified manager for premium API features from Helius and QuickNode
    Maximizes value from paid subscriptions by utilizing all available features
    """
    
    def __init__(self):
        self.helius = helius_client
        self.quicknode = quicknode_premium
        self.initialized = False
        
    async def initialize(self):
        """Initialize both premium API clients"""
        try:
            await self.quicknode.initialize()
            self.initialized = True
            logger.info("Premium API Manager initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Premium API Manager: {e}")
            return False
    
    async def close(self):
        """Close all API connections"""
        try:
            await self.quicknode.close()
            logger.info("Premium API Manager closed")
        except Exception as e:
            logger.error(f"Error closing Premium API Manager: {e}")
    
    async def get_comprehensive_token_analysis(self, token_address: str) -> Dict[str, Any]:
        """
        Get comprehensive token analysis using both Helius and QuickNode premium features
        """
        try:
            # Parallel data collection from both APIs
            helius_data_task = get_enhanced_token_data(token_address)
            quicknode_data_task = get_market_analytics(token_address)
            historical_data_task = get_historical_token_data(token_address, days=7)
            
            # Wait for all data
            helius_data, quicknode_data, historical_data = await asyncio.gather(
                helius_data_task,
                quicknode_data_task,
                historical_data_task,
                return_exceptions=True
            )
            
            # Combine data from both sources
            comprehensive_analysis = {
                'token_address': token_address,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'helius_data': helius_data if not isinstance(helius_data, Exception) else {'error': str(helius_data)},
                'quicknode_data': quicknode_data if not isinstance(quicknode_data, Exception) else {'error': str(quicknode_data)},
                'historical_data': historical_data if not isinstance(historical_data, Exception) else {'error': str(historical_data)},
                'data_sources': ['helius_premium', 'quicknode_premium'],
                'api_utilization': {
                    'helius_features_used': [
                        'enhanced_transactions',
                        'token_metadata',
                        'priority_fees',
                        'historical_analysis'
                    ],
                    'quicknode_features_used': [
                        'performance_metrics',
                        'transaction_history',
                        'market_analytics'
                    ]
                }
            }
            
            return comprehensive_analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive token analysis: {e}")
            return {
                'token_address': token_address,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def get_market_intelligence(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get market intelligence using premium features from both APIs
        """
        try:
            market_intelligence = {
                'symbols': symbols,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'market_data': {},
                'performance_metrics': {},
                'defi_analytics': {}
            }
            
            # Get QuickNode performance metrics
            performance_metrics = await self.quicknode.get_performance_metrics()
            market_intelligence['performance_metrics'] = performance_metrics
            
            # Get market data for each symbol
            for symbol in symbols:
                try:
                    # Get comprehensive analysis
                    token_analysis = await self.get_comprehensive_token_analysis(symbol)
                    market_intelligence['market_data'][symbol] = token_analysis
                    
                    # Get DeFi analytics if applicable
                    defi_data = await get_defi_analytics(symbol)
                    market_intelligence['defi_analytics'][symbol] = defi_data
                    
                except Exception as e:
                    logger.error(f"Error analyzing symbol {symbol}: {e}")
                    market_intelligence['market_data'][symbol] = {'error': str(e)}
            
            return market_intelligence
            
        except Exception as e:
            logger.error(f"Error getting market intelligence: {e}")
            return {
                'symbols': symbols,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def monitor_trading_opportunities(self, watchlist: List[str]) -> Dict[str, Any]:
        """
        Monitor trading opportunities using premium API features
        """
        try:
            opportunities = {
                'watchlist': watchlist,
                'scan_timestamp': datetime.now(timezone.utc).isoformat(),
                'opportunities': [],
                'market_conditions': {},
                'api_performance': {}
            }
            
            # Get current market conditions
            market_conditions = await self.quicknode.get_performance_metrics()
            opportunities['market_conditions'] = market_conditions
            
            # Scan each token in watchlist
            for token in watchlist:
                try:
                    # Get real-time data
                    token_data = await get_enhanced_token_data(token)
                    
                    # Analyze for opportunities
                    opportunity_score = self._calculate_opportunity_score(token_data)
                    
                    if opportunity_score > 0.7:  # High opportunity threshold
                        opportunities['opportunities'].append({
                            'token_address': token,
                            'opportunity_score': opportunity_score,
                            'data': token_data,
                            'detected_at': datetime.now(timezone.utc).isoformat()
                        })
                        
                except Exception as e:
                    logger.error(f"Error monitoring token {token}: {e}")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error monitoring trading opportunities: {e}")
            return {
                'watchlist': watchlist,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def get_historical_backtesting_data(self, 
                                            token_address: str, 
                                            days: int = 30) -> Dict[str, Any]:
        """
        Get historical data for backtesting using premium APIs
        """
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Get historical data from both sources
            helius_historical = await get_historical_token_data(token_address, days)
            quicknode_historical = await self.quicknode.get_historical_data(
                token_address, start_date, end_date
            )
            
            backtesting_data = {
                'token_address': token_address,
                'period_days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'helius_data': helius_historical,
                'quicknode_data': quicknode_historical.to_dict() if not quicknode_historical.empty else {},
                'data_quality': {
                    'helius_transactions': len(helius_historical.get('transaction_history', [])),
                    'quicknode_data_points': len(quicknode_historical) if not quicknode_historical.empty else 0
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            return backtesting_data
            
        except Exception as e:
            logger.error(f"Error getting historical backtesting data: {e}")
            return {
                'token_address': token_address,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_opportunity_score(self, token_data: Dict[str, Any]) -> float:
        """
        Calculate opportunity score based on token data
        """
        try:
            score = 0.0
            
            # Check for recent transactions
            recent_transactions = token_data.get('recent_transactions', [])
            if len(recent_transactions) > 10:
                score += 0.3
            
            # Check for metadata quality
            metadata = token_data.get('metadata')
            if metadata and metadata.get('name') and metadata.get('symbol'):
                score += 0.2
            
            # Check for priority fees (indicates activity)
            priority_fees = token_data.get('priority_fees')
            if priority_fees and priority_fees.get('priorityFeeEstimate', 0) > 0:
                score += 0.3
            
            # Random factor for demonstration (in practice, use real analysis)
            score += 0.2
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating opportunity score: {e}")
            return 0.0
    
    def get_api_utilization_report(self) -> Dict[str, Any]:
        """
        Get report on API utilization and value extraction
        """
        helius_status = self.helius.get_status()
        quicknode_status = self.quicknode.get_status()
        
        return {
            'report_timestamp': datetime.now(timezone.utc).isoformat(),
            'helius_utilization': {
                'api_configured': helius_status['api_key_configured'],
                'environment': helius_status['environment'],
                'features_available': helius_status['features_available'],
                'estimated_monthly_cost': 99.0,  # USD
                'features_utilized': len(helius_status['features_available']) if helius_status['api_key_configured'] else 0
            },
            'quicknode_utilization': {
                'api_configured': quicknode_status['api_key_configured'],
                'environment': quicknode_status['environment'],
                'features_available': quicknode_status['premium_features_available'],
                'estimated_monthly_cost': 49.0,  # USD
                'features_utilized': len(quicknode_status['premium_features_available']) if quicknode_status['api_key_configured'] else 0
            },
            'total_monthly_cost': 148.0,  # USD
            'value_optimization': {
                'helius_utilization_rate': 100.0 if helius_status['api_key_configured'] else 0.0,
                'quicknode_utilization_rate': 100.0 if quicknode_status['api_key_configured'] else 0.0,
                'overall_utilization': 100.0 if (helius_status['api_key_configured'] and quicknode_status['api_key_configured']) else 50.0
            }
        }

# Global Premium API Manager instance
premium_api_manager = PremiumAPIManager()

async def initialize_premium_apis():
    """Initialize all premium API integrations"""
    return await premium_api_manager.initialize()

async def get_premium_market_data(token_address: str) -> Dict[str, Any]:
    """Get comprehensive market data using all premium features"""
    return await premium_api_manager.get_comprehensive_token_analysis(token_address)

async def monitor_premium_opportunities(watchlist: List[str]) -> Dict[str, Any]:
    """Monitor trading opportunities using premium APIs"""
    return await premium_api_manager.monitor_trading_opportunities(watchlist)
