#!/usr/bin/env python3
"""
Advanced Correlation Analysis System
Real-time correlation analysis for hedging opportunities and risk management
"""

import asyncio
import logging
import json
import time
import redis
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from scipy.stats import pearsonr
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

class CorrelationType(Enum):
    """Types of correlation analysis"""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    ROLLING = "rolling"
    DYNAMIC = "dynamic"

class CorrelationStrength(Enum):
    """Correlation strength categories"""
    VERY_WEAK = "very_weak"      # 0.0 - 0.2
    WEAK = "weak"                # 0.2 - 0.4
    MODERATE = "moderate"        # 0.4 - 0.6
    STRONG = "strong"            # 0.6 - 0.8
    VERY_STRONG = "very_strong"  # 0.8 - 1.0

@dataclass
class CorrelationPair:
    """Correlation between two assets"""
    symbol1: str
    symbol2: str
    correlation: float
    correlation_type: CorrelationType
    strength: CorrelationStrength
    p_value: float
    confidence: float
    lookback_days: int
    last_updated: float
    stability: float  # How stable the correlation is over time

@dataclass
class CorrelationCluster:
    """Group of highly correlated assets"""
    cluster_id: str
    symbols: List[str]
    avg_correlation: float
    cluster_strength: CorrelationStrength
    total_exposure: float
    risk_contribution: float
    hedge_candidates: List[str]
    timestamp: float

@dataclass
class HedgeOpportunity:
    """Identified hedging opportunity based on correlation"""
    primary_assets: List[str]
    hedge_asset: str
    correlation_strength: float
    hedge_effectiveness: float
    risk_reduction: float
    cost_estimate: float
    confidence: float
    reasoning: str
    urgency: float
    timestamp: float

class CorrelationAnalysisSystem:
    """
    Advanced correlation analysis system for THE OVERMIND PROTOCOL
    
    Features:
    - Real-time correlation matrix calculation
    - Dynamic correlation tracking
    - Correlation clustering
    - Hedge opportunity identification
    - Risk-based correlation analysis
    - Statistical significance testing
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Analysis configuration
        self.lookback_periods = [7, 14, 30, 60]  # Days for correlation analysis
        self.min_data_points = 20  # Minimum data points for reliable correlation
        self.correlation_threshold = 0.6  # Threshold for significant correlation
        self.update_interval = 3600  # Update every hour
        
        # Correlation data storage
        self.correlation_matrix = {}
        self.correlation_history = {}
        self.correlation_clusters = {}
        self.hedge_opportunities = []
        
        # Statistical thresholds
        self.significance_level = 0.05  # p-value threshold
        self.stability_threshold = 0.8  # Correlation stability threshold
        
        logger.info("📊 Correlation Analysis System initialized")
    
    async def start_correlation_monitoring(self):
        """Start continuous correlation monitoring"""
        try:
            logger.info("🔄 Starting correlation monitoring")
            
            while True:
                # Update correlation matrix
                await self.update_correlation_matrix()
                
                # Identify correlation clusters
                await self.identify_correlation_clusters()
                
                # Find hedge opportunities
                await self.find_hedge_opportunities()
                
                # Store results
                await self.store_correlation_analysis()
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
        except Exception as e:
            logger.error(f"❌ Error in correlation monitoring: {e}")
    
    async def update_correlation_matrix(self):
        """Update correlation matrix with latest price data"""
        try:
            logger.debug("📊 Updating correlation matrix")
            
            # Get price data for all tracked assets
            price_data = await self.get_price_data()
            
            if not price_data:
                logger.warning("⚠️ No price data available for correlation analysis")
                return
            
            # Calculate correlations for different time periods
            for lookback_days in self.lookback_periods:
                correlations = await self.calculate_correlations(price_data, lookback_days)
                
                if correlations:
                    self.correlation_matrix[f"{lookback_days}d"] = correlations
                    logger.debug(f"📊 Updated {lookback_days}d correlation matrix with {len(correlations)} pairs")
            
        except Exception as e:
            logger.error(f"❌ Error updating correlation matrix: {e}")
    
    async def calculate_correlations(self, price_data: Dict[str, List[Tuple[float, float]]], 
                                   lookback_days: int) -> Dict[str, CorrelationPair]:
        """Calculate correlations between all asset pairs"""
        try:
            correlations = {}
            symbols = list(price_data.keys())
            
            # Filter data to lookback period
            cutoff_time = time.time() - (lookback_days * 24 * 3600)
            filtered_data = {}
            
            for symbol, data in price_data.items():
                filtered_data[symbol] = [
                    (timestamp, price) for timestamp, price in data 
                    if timestamp > cutoff_time
                ]
            
            # Calculate correlations for each pair
            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    correlation_pair = await self.calculate_pair_correlation(
                        symbol1, symbol2, filtered_data[symbol1], filtered_data[symbol2], lookback_days
                    )
                    
                    if correlation_pair:
                        pair_key = f"{symbol1}_{symbol2}"
                        correlations[pair_key] = correlation_pair
            
            return correlations
            
        except Exception as e:
            logger.error(f"❌ Error calculating correlations: {e}")
            return {}
    
    async def calculate_pair_correlation(self, symbol1: str, symbol2: str,
                                       data1: List[Tuple[float, float]], 
                                       data2: List[Tuple[float, float]],
                                       lookback_days: int) -> Optional[CorrelationPair]:
        """Calculate correlation between two assets"""
        try:
            # Check minimum data requirements
            if len(data1) < self.min_data_points or len(data2) < self.min_data_points:
                return None
            
            # Align data by timestamp
            aligned_data = await self.align_price_data(data1, data2)
            
            if len(aligned_data) < self.min_data_points:
                return None
            
            # Extract price series
            prices1 = [price1 for _, price1, _ in aligned_data]
            prices2 = [price2 for _, _, price2 in aligned_data]
            
            # Calculate returns
            returns1 = np.diff(np.log(prices1))
            returns2 = np.diff(np.log(prices2))
            
            if len(returns1) < self.min_data_points - 1:
                return None
            
            # Calculate Pearson correlation
            correlation, p_value = pearsonr(returns1, returns2)
            
            # Determine correlation strength
            strength = self.classify_correlation_strength(abs(correlation))
            
            # Calculate correlation stability
            stability = await self.calculate_correlation_stability(
                symbol1, symbol2, returns1, returns2
            )
            
            # Calculate confidence based on p-value and data quality
            confidence = self.calculate_correlation_confidence(
                correlation, p_value, len(returns1), stability
            )
            
            return CorrelationPair(
                symbol1=symbol1,
                symbol2=symbol2,
                correlation=correlation,
                correlation_type=CorrelationType.PEARSON,
                strength=strength,
                p_value=p_value,
                confidence=confidence,
                lookback_days=lookback_days,
                last_updated=time.time(),
                stability=stability
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating pair correlation {symbol1}-{symbol2}: {e}")
            return None
    
    async def align_price_data(self, data1: List[Tuple[float, float]], 
                             data2: List[Tuple[float, float]]) -> List[Tuple[float, float, float]]:
        """Align price data by timestamp"""
        try:
            # Convert to dictionaries for easier lookup
            dict1 = {timestamp: price for timestamp, price in data1}
            dict2 = {timestamp: price for timestamp, price in data2}
            
            # Find common timestamps
            common_timestamps = set(dict1.keys()) & set(dict2.keys())
            
            # Create aligned data
            aligned = [
                (timestamp, dict1[timestamp], dict2[timestamp])
                for timestamp in sorted(common_timestamps)
            ]
            
            return aligned
            
        except Exception as e:
            logger.error(f"❌ Error aligning price data: {e}")
            return []
    
    def classify_correlation_strength(self, correlation: float) -> CorrelationStrength:
        """Classify correlation strength"""
        abs_corr = abs(correlation)
        
        if abs_corr >= 0.8:
            return CorrelationStrength.VERY_STRONG
        elif abs_corr >= 0.6:
            return CorrelationStrength.STRONG
        elif abs_corr >= 0.4:
            return CorrelationStrength.MODERATE
        elif abs_corr >= 0.2:
            return CorrelationStrength.WEAK
        else:
            return CorrelationStrength.VERY_WEAK
    
    async def calculate_correlation_stability(self, symbol1: str, symbol2: str,
                                            returns1: np.ndarray, returns2: np.ndarray) -> float:
        """Calculate how stable the correlation is over time"""
        try:
            if len(returns1) < 40:  # Need enough data for rolling correlation
                return 0.5  # Default moderate stability
            
            # Calculate rolling correlation
            window_size = min(20, len(returns1) // 2)
            rolling_correlations = []
            
            for i in range(window_size, len(returns1)):
                window_returns1 = returns1[i-window_size:i]
                window_returns2 = returns2[i-window_size:i]
                
                if len(window_returns1) > 5:  # Minimum for correlation
                    corr, _ = pearsonr(window_returns1, window_returns2)
                    if not np.isnan(corr):
                        rolling_correlations.append(corr)
            
            if len(rolling_correlations) < 3:
                return 0.5
            
            # Stability is inverse of standard deviation of rolling correlations
            stability = 1.0 - min(1.0, np.std(rolling_correlations) / 0.5)
            
            return max(0.0, min(1.0, stability))
            
        except Exception as e:
            logger.error(f"❌ Error calculating correlation stability: {e}")
            return 0.5
    
    def calculate_correlation_confidence(self, correlation: float, p_value: float,
                                       sample_size: int, stability: float) -> float:
        """Calculate confidence in correlation estimate"""
        try:
            # Base confidence on statistical significance
            significance_confidence = 1.0 - p_value if p_value < self.significance_level else 0.5
            
            # Adjust for sample size
            size_confidence = min(1.0, sample_size / 100.0)  # Full confidence at 100+ samples
            
            # Adjust for correlation strength
            strength_confidence = abs(correlation)
            
            # Combine factors
            confidence = (significance_confidence * 0.4 + 
                         size_confidence * 0.3 + 
                         strength_confidence * 0.2 + 
                         stability * 0.1)
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"❌ Error calculating correlation confidence: {e}")
            return 0.5

    async def identify_correlation_clusters(self):
        """Identify clusters of highly correlated assets"""
        try:
            logger.debug("🔍 Identifying correlation clusters")

            # Use 30-day correlations for clustering
            correlations = self.correlation_matrix.get("30d", {})

            if not correlations:
                return

            # Build correlation graph
            correlation_graph = await self.build_correlation_graph(correlations)

            # Find clusters using correlation threshold
            clusters = await self.find_correlation_clusters(correlation_graph)

            # Analyze clusters for risk and hedging opportunities
            for cluster_id, cluster_symbols in clusters.items():
                cluster_analysis = await self.analyze_correlation_cluster(
                    cluster_id, cluster_symbols, correlations
                )

                if cluster_analysis:
                    self.correlation_clusters[cluster_id] = cluster_analysis

            logger.info(f"📊 Identified {len(self.correlation_clusters)} correlation clusters")

        except Exception as e:
            logger.error(f"❌ Error identifying correlation clusters: {e}")

    async def build_correlation_graph(self, correlations: Dict[str, CorrelationPair]) -> Dict[str, List[str]]:
        """Build graph of correlated assets"""
        try:
            graph = {}

            for pair_key, correlation_pair in correlations.items():
                if (correlation_pair.strength in [CorrelationStrength.STRONG, CorrelationStrength.VERY_STRONG] and
                    correlation_pair.confidence > 0.7):

                    symbol1 = correlation_pair.symbol1
                    symbol2 = correlation_pair.symbol2

                    if symbol1 not in graph:
                        graph[symbol1] = []
                    if symbol2 not in graph:
                        graph[symbol2] = []

                    graph[symbol1].append(symbol2)
                    graph[symbol2].append(symbol1)

            return graph

        except Exception as e:
            logger.error(f"❌ Error building correlation graph: {e}")
            return {}

    async def find_correlation_clusters(self, graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Find clusters using simple connected components"""
        try:
            visited = set()
            clusters = {}
            cluster_id = 0

            for symbol in graph:
                if symbol not in visited:
                    cluster = []
                    await self.dfs_cluster(symbol, graph, visited, cluster)

                    if len(cluster) > 1:  # Only clusters with multiple assets
                        clusters[f"cluster_{cluster_id}"] = cluster
                        cluster_id += 1

            return clusters

        except Exception as e:
            logger.error(f"❌ Error finding correlation clusters: {e}")
            return {}

    async def dfs_cluster(self, symbol: str, graph: Dict[str, List[str]],
                         visited: set, cluster: List[str]):
        """Depth-first search for cluster identification"""
        visited.add(symbol)
        cluster.append(symbol)

        for neighbor in graph.get(symbol, []):
            if neighbor not in visited:
                await self.dfs_cluster(neighbor, graph, visited, cluster)

    async def analyze_correlation_cluster(self, cluster_id: str, symbols: List[str],
                                        correlations: Dict[str, CorrelationPair]) -> Optional[CorrelationCluster]:
        """Analyze a correlation cluster for risk and hedging"""
        try:
            # Calculate average correlation within cluster
            cluster_correlations = []

            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    pair_key1 = f"{symbol1}_{symbol2}"
                    pair_key2 = f"{symbol2}_{symbol1}"

                    correlation_pair = correlations.get(pair_key1) or correlations.get(pair_key2)
                    if correlation_pair:
                        cluster_correlations.append(abs(correlation_pair.correlation))

            if not cluster_correlations:
                return None

            avg_correlation = statistics.mean(cluster_correlations)
            cluster_strength = self.classify_correlation_strength(avg_correlation)

            # Get portfolio exposure for cluster
            total_exposure = await self.get_cluster_exposure(symbols)

            # Calculate risk contribution
            risk_contribution = await self.calculate_cluster_risk(symbols, avg_correlation)

            # Find hedge candidates
            hedge_candidates = await self.find_cluster_hedge_candidates(symbols)

            return CorrelationCluster(
                cluster_id=cluster_id,
                symbols=symbols,
                avg_correlation=avg_correlation,
                cluster_strength=cluster_strength,
                total_exposure=total_exposure,
                risk_contribution=risk_contribution,
                hedge_candidates=hedge_candidates,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"❌ Error analyzing correlation cluster: {e}")
            return None

    async def find_hedge_opportunities(self):
        """Find hedging opportunities based on correlation analysis"""
        try:
            logger.debug("🔍 Finding hedge opportunities")

            self.hedge_opportunities = []

            # Analyze each correlation cluster for hedging
            for cluster in self.correlation_clusters.values():
                cluster_hedges = await self.analyze_cluster_hedging(cluster)
                self.hedge_opportunities.extend(cluster_hedges)

            # Find pair-wise hedging opportunities
            correlations = self.correlation_matrix.get("30d", {})
            for correlation_pair in correlations.values():
                if (correlation_pair.strength == CorrelationStrength.VERY_STRONG and
                    correlation_pair.correlation < -0.7):  # Strong negative correlation

                    hedge_opportunity = await self.analyze_negative_correlation_hedge(correlation_pair)
                    if hedge_opportunity:
                        self.hedge_opportunities.append(hedge_opportunity)

            # Sort by urgency and effectiveness
            self.hedge_opportunities.sort(
                key=lambda h: h.urgency * h.hedge_effectiveness, reverse=True
            )

            logger.info(f"🎯 Found {len(self.hedge_opportunities)} hedge opportunities")

        except Exception as e:
            logger.error(f"❌ Error finding hedge opportunities: {e}")

    async def get_price_data(self) -> Dict[str, List[Tuple[float, float]]]:
        """Get price data for correlation analysis"""
        try:
            # Get list of tracked symbols from Redis
            symbols_key = "overmind:tracked_symbols"
            symbols_str = self.redis_client.get(symbols_key)

            if not symbols_str:
                # Default symbols if none configured
                symbols = ['SOL', 'BTC', 'ETH', 'USDC']
            else:
                symbols = json.loads(symbols_str)

            price_data = {}

            for symbol in symbols:
                # Get price history from Redis
                price_key = f"overmind:price_history:{symbol}"
                price_history = self.redis_client.lrange(price_key, 0, 1000)  # Last 1000 data points

                if price_history:
                    symbol_data = []
                    for price_str in price_history:
                        try:
                            price_point = json.loads(price_str)
                            timestamp = price_point.get('timestamp', time.time())
                            price = price_point.get('price', 0.0)
                            symbol_data.append((timestamp, price))
                        except:
                            continue

                    if symbol_data:
                        price_data[symbol] = sorted(symbol_data, key=lambda x: x[0])

            return price_data

        except Exception as e:
            logger.error(f"❌ Error getting price data: {e}")
            return {}

    async def get_cluster_exposure(self, symbols: List[str]) -> float:
        """Get total portfolio exposure for a cluster"""
        try:
            total_exposure = 0.0

            for symbol in symbols:
                position_key = f"overmind:position:{symbol}"
                position_str = self.redis_client.get(position_key)

                if position_str:
                    position = json.loads(position_str)
                    exposure = position.get('value', 0.0)
                    total_exposure += exposure

            return total_exposure

        except Exception as e:
            logger.error(f"❌ Error getting cluster exposure: {e}")
            return 0.0

    async def calculate_cluster_risk(self, symbols: List[str], avg_correlation: float) -> float:
        """Calculate risk contribution of a correlation cluster"""
        try:
            # Simplified risk calculation based on correlation and exposure
            cluster_exposure = await self.get_cluster_exposure(symbols)

            # Risk increases with correlation and exposure
            risk_multiplier = 1.0 + (avg_correlation * 0.5)  # Up to 50% risk increase
            cluster_risk = cluster_exposure * risk_multiplier * len(symbols) / 10.0

            return cluster_risk

        except Exception as e:
            logger.error(f"❌ Error calculating cluster risk: {e}")
            return 0.0

    async def find_cluster_hedge_candidates(self, symbols: List[str]) -> List[str]:
        """Find hedge candidates for a correlation cluster"""
        try:
            hedge_candidates = []

            # Common hedge assets for different types of clusters
            if any('SOL' in symbol or 'ETH' in symbol for symbol in symbols):
                hedge_candidates.extend(['USDC', 'USDT'])  # Stable assets

            if any('meme' in symbol.lower() for symbol in symbols):
                hedge_candidates.extend(['SOL', 'BTC'])  # Base assets

            if len(symbols) > 3:  # Large cluster
                hedge_candidates.append('BTC')  # Bitcoin as portfolio hedge

            return list(set(hedge_candidates))  # Remove duplicates

        except Exception as e:
            logger.error(f"❌ Error finding cluster hedge candidates: {e}")
            return []

    async def analyze_cluster_hedging(self, cluster: CorrelationCluster) -> List[HedgeOpportunity]:
        """Analyze hedging opportunities for a correlation cluster"""
        try:
            opportunities = []

            # Only hedge significant clusters
            if cluster.total_exposure < 50.0:  # Less than $50 exposure
                return opportunities

            for hedge_asset in cluster.hedge_candidates:
                # Calculate hedge effectiveness
                effectiveness = await self.calculate_hedge_effectiveness_for_cluster(
                    cluster.symbols, hedge_asset
                )

                if effectiveness > 0.5:  # Minimum 50% effectiveness
                    opportunity = HedgeOpportunity(
                        primary_assets=cluster.symbols,
                        hedge_asset=hedge_asset,
                        correlation_strength=cluster.avg_correlation,
                        hedge_effectiveness=effectiveness,
                        risk_reduction=effectiveness * cluster.risk_contribution,
                        cost_estimate=0.005,  # 0.5% estimated cost
                        confidence=0.7,
                        reasoning=f"Cluster hedge for {len(cluster.symbols)} correlated assets",
                        urgency=min(1.0, cluster.risk_contribution / 100.0),
                        timestamp=time.time()
                    )
                    opportunities.append(opportunity)

            return opportunities

        except Exception as e:
            logger.error(f"❌ Error analyzing cluster hedging: {e}")
            return []

    async def analyze_negative_correlation_hedge(self, correlation_pair: CorrelationPair) -> Optional[HedgeOpportunity]:
        """Analyze hedging opportunity from negative correlation"""
        try:
            # Strong negative correlation can be used for natural hedging
            if correlation_pair.correlation > -0.7:
                return None

            # Check if both assets have significant exposure
            exposure1 = await self.get_asset_exposure(correlation_pair.symbol1)
            exposure2 = await self.get_asset_exposure(correlation_pair.symbol2)

            if exposure1 < 20.0 and exposure2 < 20.0:  # Both positions too small
                return None

            # Determine primary and hedge asset
            if exposure1 > exposure2:
                primary_asset = correlation_pair.symbol1
                hedge_asset = correlation_pair.symbol2
                primary_exposure = exposure1
            else:
                primary_asset = correlation_pair.symbol2
                hedge_asset = correlation_pair.symbol1
                primary_exposure = exposure2

            effectiveness = abs(correlation_pair.correlation) * correlation_pair.confidence

            return HedgeOpportunity(
                primary_assets=[primary_asset],
                hedge_asset=hedge_asset,
                correlation_strength=abs(correlation_pair.correlation),
                hedge_effectiveness=effectiveness,
                risk_reduction=effectiveness * primary_exposure / 100.0,
                cost_estimate=0.002,  # Lower cost for natural hedge
                confidence=correlation_pair.confidence,
                reasoning=f"Natural hedge using negative correlation ({correlation_pair.correlation:.2f})",
                urgency=min(1.0, primary_exposure / 200.0),
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"❌ Error analyzing negative correlation hedge: {e}")
            return None

    async def calculate_hedge_effectiveness_for_cluster(self, symbols: List[str], hedge_asset: str) -> float:
        """Calculate hedge effectiveness for a cluster"""
        try:
            correlations = []

            for symbol in symbols:
                correlation = await self.get_correlation_between_assets(symbol, hedge_asset)
                if correlation is not None:
                    correlations.append(abs(correlation))

            if not correlations:
                return 0.3  # Default moderate effectiveness

            # Average correlation strength determines effectiveness
            avg_correlation = statistics.mean(correlations)

            # Negative correlation is better for hedging
            if any(await self.get_correlation_between_assets(symbol, hedge_asset) or 0 < 0 for symbol in symbols):
                effectiveness = avg_correlation * 1.2  # Bonus for negative correlation
            else:
                effectiveness = avg_correlation * 0.8  # Penalty for positive correlation

            return min(0.9, effectiveness)

        except Exception as e:
            logger.error(f"❌ Error calculating hedge effectiveness: {e}")
            return 0.5

    async def get_correlation_between_assets(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Get correlation between two specific assets"""
        try:
            correlations = self.correlation_matrix.get("30d", {})

            # Try both directions
            pair_key1 = f"{symbol1}_{symbol2}"
            pair_key2 = f"{symbol2}_{symbol1}"

            correlation_pair = correlations.get(pair_key1) or correlations.get(pair_key2)

            if correlation_pair:
                return correlation_pair.correlation

            return None

        except Exception as e:
            logger.error(f"❌ Error getting correlation between assets: {e}")
            return None

    async def get_asset_exposure(self, symbol: str) -> float:
        """Get current exposure for an asset"""
        try:
            position_key = f"overmind:position:{symbol}"
            position_str = self.redis_client.get(position_key)

            if position_str:
                position = json.loads(position_str)
                return position.get('value', 0.0)

            return 0.0

        except Exception as e:
            logger.error(f"❌ Error getting asset exposure: {e}")
            return 0.0

    async def store_correlation_analysis(self):
        """Store correlation analysis results"""
        try:
            # Store correlation matrix
            for period, correlations in self.correlation_matrix.items():
                matrix_key = f"overmind:correlation_matrix:{period}"
                matrix_data = {
                    pair_key: asdict(correlation_pair)
                    for pair_key, correlation_pair in correlations.items()
                }
                self.redis_client.setex(matrix_key, 7200, json.dumps(matrix_data))  # 2 hour expiry

            # Store correlation clusters
            clusters_key = "overmind:correlation_clusters"
            clusters_data = {
                cluster_id: asdict(cluster)
                for cluster_id, cluster in self.correlation_clusters.items()
            }
            self.redis_client.setex(clusters_key, 7200, json.dumps(clusters_data))

            # Store hedge opportunities
            hedges_key = "overmind:hedge_opportunities"
            hedges_data = [asdict(hedge) for hedge in self.hedge_opportunities]
            self.redis_client.setex(hedges_key, 3600, json.dumps(hedges_data))  # 1 hour expiry

            logger.debug("💾 Stored correlation analysis results")

        except Exception as e:
            logger.error(f"❌ Error storing correlation analysis: {e}")

    async def get_correlation_analysis_status(self) -> Dict[str, Any]:
        """Get current correlation analysis status"""
        try:
            total_pairs = sum(len(correlations) for correlations in self.correlation_matrix.values())

            return {
                'timestamp': time.time(),
                'correlation_pairs': total_pairs,
                'correlation_clusters': len(self.correlation_clusters),
                'hedge_opportunities': len(self.hedge_opportunities),
                'lookback_periods': self.lookback_periods,
                'configuration': {
                    'correlation_threshold': self.correlation_threshold,
                    'min_data_points': self.min_data_points,
                    'significance_level': self.significance_level,
                    'stability_threshold': self.stability_threshold
                }
            }

        except Exception as e:
            logger.error(f"❌ Error getting correlation analysis status: {e}")
            return {'error': str(e)}

async def main():
    """Test the correlation analysis system"""
    system = CorrelationAnalysisSystem()

    # Start monitoring (would run continuously in production)
    await system.update_correlation_matrix()
    await system.identify_correlation_clusters()
    await system.find_hedge_opportunities()

    status = await system.get_correlation_analysis_status()
    print(f"Correlation Analysis Status: {status}")

if __name__ == "__main__":
    asyncio.run(main())
