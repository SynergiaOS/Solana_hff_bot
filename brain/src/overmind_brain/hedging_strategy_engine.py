#!/usr/bin/env python3
"""
Hedging Strategy Engine
Comprehensive position hedging and risk neutralization system
"""

import asyncio
import logging
import json
import time
import redis
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class HedgeType(Enum):
    """Types of hedging strategies"""
    DELTA_HEDGE = "delta_hedge"
    CORRELATION_HEDGE = "correlation_hedge"
    PORTFOLIO_HEDGE = "portfolio_hedge"
    VOLATILITY_HEDGE = "volatility_hedge"
    SECTOR_HEDGE = "sector_hedge"
    MARKET_NEUTRAL = "market_neutral"

class HedgeStatus(Enum):
    """Status of hedge positions"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    CLOSED = "closed"
    FAILED = "failed"

@dataclass
class HedgePosition:
    """Individual hedge position"""
    hedge_id: str
    primary_symbol: str
    hedge_symbol: str
    hedge_type: HedgeType
    hedge_ratio: float
    primary_quantity: float
    hedge_quantity: float
    entry_time: float
    expiry_time: Optional[float]
    status: HedgeStatus
    effectiveness: float
    cost: float
    pnl: float
    confidence: float
    reasoning: str

@dataclass
class HedgeRecommendation:
    """Hedge recommendation from analysis"""
    primary_symbol: str
    recommended_hedge_symbol: str
    hedge_type: HedgeType
    hedge_ratio: float
    confidence: float
    expected_effectiveness: float
    estimated_cost: float
    reasoning: str
    urgency: float
    risk_reduction: float
    timestamp: float

@dataclass
class PortfolioRisk:
    """Portfolio risk metrics for hedging analysis"""
    total_exposure: float
    sector_exposures: Dict[str, float]
    correlation_risk: float
    volatility_risk: float
    concentration_risk: float
    market_beta: float
    var_95: float
    expected_shortfall: float
    max_drawdown_risk: float

class HedgingStrategyEngine:
    """
    Comprehensive hedging strategy engine for THE OVERMIND PROTOCOL
    
    Features:
    - Delta hedging for directional risk
    - Correlation hedging for related assets
    - Portfolio-wide risk neutralization
    - Volatility hedging strategies
    - Sector exposure hedging
    - Market neutral positioning
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Hedging configuration
        self.hedge_threshold = 0.7  # Minimum correlation for hedge consideration
        self.max_hedge_cost = 0.02  # Maximum 2% cost for hedging
        self.min_effectiveness = 0.6  # Minimum 60% hedge effectiveness
        self.hedge_rebalance_threshold = 0.1  # 10% deviation triggers rebalance
        
        # Active hedges tracking
        self.active_hedges = {}
        self.hedge_history = []
        self.correlation_matrix = {}
        self.sector_mappings = {}
        
        # Risk thresholds
        self.max_portfolio_var = 0.05  # 5% daily VaR limit
        self.max_sector_exposure = 0.3  # 30% max sector exposure
        self.max_correlation_exposure = 0.4  # 40% max correlated exposure
        
        logger.info("🛡️ Hedging Strategy Engine initialized")
    
    async def analyze_hedging_opportunities(self, portfolio_positions: Dict[str, Any]) -> List[HedgeRecommendation]:
        """Analyze portfolio for hedging opportunities"""
        try:
            logger.info("🔍 Analyzing hedging opportunities")
            
            # Calculate portfolio risk metrics
            portfolio_risk = await self.calculate_portfolio_risk(portfolio_positions)
            
            recommendations = []
            
            # Check each position for hedging needs
            for symbol, position in portfolio_positions.items():
                position_recommendations = await self.analyze_position_hedging(
                    symbol, position, portfolio_risk, portfolio_positions
                )
                recommendations.extend(position_recommendations)
            
            # Check portfolio-level hedging needs
            portfolio_recommendations = await self.analyze_portfolio_hedging(
                portfolio_risk, portfolio_positions
            )
            recommendations.extend(portfolio_recommendations)
            
            # Sort by urgency and effectiveness
            recommendations.sort(key=lambda r: r.urgency * r.expected_effectiveness, reverse=True)
            
            logger.info(f"📊 Found {len(recommendations)} hedging opportunities")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error analyzing hedging opportunities: {e}")
            return []
    
    async def analyze_position_hedging(self, symbol: str, position: Dict[str, Any], 
                                     portfolio_risk: PortfolioRisk, 
                                     all_positions: Dict[str, Any]) -> List[HedgeRecommendation]:
        """Analyze hedging needs for a specific position"""
        try:
            recommendations = []
            position_value = position.get('value', 0.0)
            position_size = position.get('quantity', 0.0)
            
            # Skip small positions
            if position_value < portfolio_risk.total_exposure * 0.05:  # Less than 5% of portfolio
                return recommendations
            
            # 1. Delta Hedging Analysis
            delta_hedge = await self.analyze_delta_hedging(symbol, position, portfolio_risk)
            if delta_hedge:
                recommendations.append(delta_hedge)
            
            # 2. Correlation Hedging Analysis
            correlation_hedge = await self.analyze_correlation_hedging(
                symbol, position, all_positions, portfolio_risk
            )
            if correlation_hedge:
                recommendations.append(correlation_hedge)
            
            # 3. Volatility Hedging Analysis
            volatility_hedge = await self.analyze_volatility_hedging(symbol, position, portfolio_risk)
            if volatility_hedge:
                recommendations.append(volatility_hedge)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error analyzing position hedging for {symbol}: {e}")
            return []
    
    async def analyze_delta_hedging(self, symbol: str, position: Dict[str, Any], 
                                  portfolio_risk: PortfolioRisk) -> Optional[HedgeRecommendation]:
        """Analyze delta hedging opportunities"""
        try:
            position_value = position.get('value', 0.0)
            
            # Check if position is large enough to warrant delta hedging
            portfolio_percentage = position_value / portfolio_risk.total_exposure
            
            if portfolio_percentage < 0.15:  # Less than 15% of portfolio
                return None
            
            # Find suitable hedge instruments
            hedge_candidates = await self.find_delta_hedge_candidates(symbol)
            
            if not hedge_candidates:
                return None
            
            # Select best hedge candidate
            best_hedge = hedge_candidates[0]
            hedge_symbol = best_hedge['symbol']
            hedge_ratio = best_hedge['ratio']
            
            # Calculate hedge effectiveness and cost
            effectiveness = await self.calculate_hedge_effectiveness(symbol, hedge_symbol, hedge_ratio)
            cost = await self.estimate_hedge_cost(symbol, hedge_symbol, position_value)
            
            if effectiveness < self.min_effectiveness or cost > self.max_hedge_cost:
                return None
            
            # Calculate urgency based on position risk
            urgency = min(1.0, portfolio_percentage * 2)  # Higher for larger positions
            
            return HedgeRecommendation(
                primary_symbol=symbol,
                recommended_hedge_symbol=hedge_symbol,
                hedge_type=HedgeType.DELTA_HEDGE,
                hedge_ratio=hedge_ratio,
                confidence=0.8,
                expected_effectiveness=effectiveness,
                estimated_cost=cost,
                reasoning=f"Large position ({portfolio_percentage:.1%}) requires delta hedging",
                urgency=urgency,
                risk_reduction=effectiveness * portfolio_percentage,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"❌ Error analyzing delta hedging: {e}")
            return None
    
    async def analyze_correlation_hedging(self, symbol: str, position: Dict[str, Any],
                                        all_positions: Dict[str, Any], 
                                        portfolio_risk: PortfolioRisk) -> Optional[HedgeRecommendation]:
        """Analyze correlation hedging opportunities"""
        try:
            # Check if we have correlated positions that could be hedged together
            correlated_positions = await self.find_correlated_positions(symbol, all_positions)
            
            if not correlated_positions:
                return None
            
            # Calculate total correlated exposure
            total_correlated_value = sum(pos['value'] for pos in correlated_positions.values())
            correlation_exposure = total_correlated_value / portfolio_risk.total_exposure
            
            if correlation_exposure < 0.2:  # Less than 20% correlated exposure
                return None
            
            # Find hedge instrument that's negatively correlated
            hedge_candidates = await self.find_correlation_hedge_candidates(
                list(correlated_positions.keys())
            )
            
            if not hedge_candidates:
                return None
            
            best_hedge = hedge_candidates[0]
            hedge_symbol = best_hedge['symbol']
            hedge_ratio = best_hedge['ratio']
            
            effectiveness = await self.calculate_correlation_hedge_effectiveness(
                list(correlated_positions.keys()), hedge_symbol
            )
            cost = await self.estimate_hedge_cost(symbol, hedge_symbol, total_correlated_value)
            
            if effectiveness < self.min_effectiveness or cost > self.max_hedge_cost:
                return None
            
            urgency = min(1.0, correlation_exposure * 1.5)
            
            return HedgeRecommendation(
                primary_symbol=symbol,
                recommended_hedge_symbol=hedge_symbol,
                hedge_type=HedgeType.CORRELATION_HEDGE,
                hedge_ratio=hedge_ratio,
                confidence=0.75,
                expected_effectiveness=effectiveness,
                estimated_cost=cost,
                reasoning=f"High correlation exposure ({correlation_exposure:.1%}) across {len(correlated_positions)} positions",
                urgency=urgency,
                risk_reduction=effectiveness * correlation_exposure,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"❌ Error analyzing correlation hedging: {e}")
            return None
    
    async def analyze_volatility_hedging(self, symbol: str, position: Dict[str, Any],
                                       portfolio_risk: PortfolioRisk) -> Optional[HedgeRecommendation]:
        """Analyze volatility hedging opportunities"""
        try:
            # Get volatility metrics for the position
            volatility = await self.get_asset_volatility(symbol)
            
            if not volatility or volatility < 0.3:  # Low volatility doesn't need hedging
                return None
            
            position_value = position.get('value', 0.0)
            portfolio_percentage = position_value / portfolio_risk.total_exposure
            
            # Only hedge volatile positions that are significant
            if portfolio_percentage < 0.1:
                return None
            
            # Find volatility hedge instruments (typically inverse volatility products)
            hedge_candidates = await self.find_volatility_hedge_candidates(symbol)
            
            if not hedge_candidates:
                return None
            
            best_hedge = hedge_candidates[0]
            hedge_symbol = best_hedge['symbol']
            hedge_ratio = best_hedge['ratio']
            
            effectiveness = 0.6  # Volatility hedging typically 60% effective
            cost = await self.estimate_hedge_cost(symbol, hedge_symbol, position_value)
            
            if cost > self.max_hedge_cost:
                return None
            
            urgency = min(1.0, volatility * portfolio_percentage)
            
            return HedgeRecommendation(
                primary_symbol=symbol,
                recommended_hedge_symbol=hedge_symbol,
                hedge_type=HedgeType.VOLATILITY_HEDGE,
                hedge_ratio=hedge_ratio,
                confidence=0.7,
                expected_effectiveness=effectiveness,
                estimated_cost=cost,
                reasoning=f"High volatility ({volatility:.1%}) position needs volatility hedging",
                urgency=urgency,
                risk_reduction=effectiveness * portfolio_percentage,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"❌ Error analyzing volatility hedging: {e}")
            return None

    async def analyze_portfolio_hedging(self, portfolio_risk: PortfolioRisk,
                                      positions: Dict[str, Any]) -> List[HedgeRecommendation]:
        """Analyze portfolio-level hedging needs"""
        try:
            recommendations = []

            # 1. Market Beta Hedging
            if abs(portfolio_risk.market_beta) > 1.2:  # High market exposure
                market_hedge = await self.analyze_market_beta_hedging(portfolio_risk, positions)
                if market_hedge:
                    recommendations.append(market_hedge)

            # 2. Sector Concentration Hedging
            for sector, exposure in portfolio_risk.sector_exposures.items():
                if exposure > self.max_sector_exposure:
                    sector_hedge = await self.analyze_sector_hedging(sector, exposure, portfolio_risk)
                    if sector_hedge:
                        recommendations.append(sector_hedge)

            # 3. Portfolio VaR Hedging
            if portfolio_risk.var_95 > self.max_portfolio_var:
                var_hedge = await self.analyze_var_hedging(portfolio_risk, positions)
                if var_hedge:
                    recommendations.append(var_hedge)

            return recommendations

        except Exception as e:
            logger.error(f"❌ Error analyzing portfolio hedging: {e}")
            return []

    async def calculate_portfolio_risk(self, positions: Dict[str, Any]) -> PortfolioRisk:
        """Calculate comprehensive portfolio risk metrics"""
        try:
            total_exposure = sum(pos.get('value', 0.0) for pos in positions.values())

            # Calculate sector exposures (simplified)
            sector_exposures = {}
            for symbol, position in positions.items():
                sector = await self.get_asset_sector(symbol)
                if sector:
                    sector_exposures[sector] = sector_exposures.get(sector, 0.0) + position.get('value', 0.0)

            # Normalize sector exposures
            for sector in sector_exposures:
                sector_exposures[sector] /= total_exposure

            # Calculate other risk metrics (simplified)
            correlation_risk = await self.calculate_correlation_risk(positions)
            volatility_risk = await self.calculate_volatility_risk(positions)
            concentration_risk = await self.calculate_concentration_risk(positions)
            market_beta = await self.calculate_portfolio_beta(positions)
            var_95 = await self.calculate_portfolio_var(positions)
            expected_shortfall = var_95 * 1.3  # Simplified ES calculation
            max_drawdown_risk = await self.calculate_max_drawdown_risk(positions)

            return PortfolioRisk(
                total_exposure=total_exposure,
                sector_exposures=sector_exposures,
                correlation_risk=correlation_risk,
                volatility_risk=volatility_risk,
                concentration_risk=concentration_risk,
                market_beta=market_beta,
                var_95=var_95,
                expected_shortfall=expected_shortfall,
                max_drawdown_risk=max_drawdown_risk
            )

        except Exception as e:
            logger.error(f"❌ Error calculating portfolio risk: {e}")
            return PortfolioRisk(
                total_exposure=0.0,
                sector_exposures={},
                correlation_risk=0.0,
                volatility_risk=0.0,
                concentration_risk=0.0,
                market_beta=1.0,
                var_95=0.02,
                expected_shortfall=0.026,
                max_drawdown_risk=0.1
            )

    async def find_delta_hedge_candidates(self, symbol: str) -> List[Dict[str, Any]]:
        """Find suitable delta hedge candidates for a symbol"""
        try:
            # For Solana ecosystem, common hedge pairs
            hedge_mappings = {
                'SOL': [
                    {'symbol': 'ETH', 'ratio': -0.8, 'correlation': -0.3},
                    {'symbol': 'BTC', 'ratio': -0.6, 'correlation': -0.2}
                ],
                'USDC': [
                    {'symbol': 'USDT', 'ratio': -1.0, 'correlation': 0.95}
                ],
                # Add more mappings as needed
            }

            candidates = hedge_mappings.get(symbol, [])

            # Sort by correlation strength
            candidates.sort(key=lambda x: abs(x['correlation']), reverse=True)

            return candidates

        except Exception as e:
            logger.error(f"❌ Error finding delta hedge candidates: {e}")
            return []

    async def find_correlation_hedge_candidates(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Find hedge candidates for correlated positions"""
        try:
            # Find instruments negatively correlated with the group
            candidates = []

            # For DeFi tokens, common hedges might be:
            if any('DeFi' in await self.get_asset_sector(symbol) or '' for symbol in symbols):
                candidates.append({
                    'symbol': 'USDC',
                    'ratio': -0.5,
                    'correlation': -0.4
                })

            # For memecoins, hedge with stable assets
            if any('meme' in symbol.lower() for symbol in symbols):
                candidates.append({
                    'symbol': 'SOL',
                    'ratio': -0.3,
                    'correlation': -0.2
                })

            return candidates

        except Exception as e:
            logger.error(f"❌ Error finding correlation hedge candidates: {e}")
            return []

    async def find_volatility_hedge_candidates(self, symbol: str) -> List[Dict[str, Any]]:
        """Find volatility hedge candidates"""
        try:
            # Volatility hedging typically uses inverse volatility products
            candidates = [
                {'symbol': 'USDC', 'ratio': -0.2, 'type': 'stable_hedge'},
                {'symbol': 'SOL', 'ratio': -0.1, 'type': 'base_asset_hedge'}
            ]

            return candidates

        except Exception as e:
            logger.error(f"❌ Error finding volatility hedge candidates: {e}")
            return []

    async def calculate_hedge_effectiveness(self, primary_symbol: str, hedge_symbol: str,
                                         hedge_ratio: float) -> float:
        """Calculate expected hedge effectiveness"""
        try:
            # Get historical correlation
            correlation = await self.get_correlation(primary_symbol, hedge_symbol)

            if correlation is None:
                return 0.5  # Default effectiveness

            # Effectiveness based on correlation strength and hedge ratio
            effectiveness = abs(correlation) * abs(hedge_ratio)

            # Cap at reasonable maximum
            return min(0.9, effectiveness)

        except Exception as e:
            logger.error(f"❌ Error calculating hedge effectiveness: {e}")
            return 0.5

    async def estimate_hedge_cost(self, primary_symbol: str, hedge_symbol: str,
                                position_value: float) -> float:
        """Estimate cost of implementing hedge"""
        try:
            # Simplified cost calculation
            # Includes transaction costs, spread, and potential slippage

            base_cost = 0.001  # 0.1% base transaction cost
            spread_cost = 0.0005  # 0.05% spread cost
            slippage_cost = min(0.002, position_value / 1000000 * 0.001)  # Slippage based on size

            total_cost = base_cost + spread_cost + slippage_cost

            return total_cost

        except Exception as e:
            logger.error(f"❌ Error estimating hedge cost: {e}")
            return 0.01  # Default 1% cost

    async def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """Get correlation between two assets"""
        try:
            # Try to get from Redis cache first
            cache_key = f"overmind:correlation:{symbol1}:{symbol2}"
            cached_correlation = self.redis_client.get(cache_key)

            if cached_correlation:
                return float(cached_correlation)

            # Default correlations for common pairs
            default_correlations = {
                ('SOL', 'ETH'): 0.7,
                ('SOL', 'BTC'): 0.6,
                ('USDC', 'USDT'): 0.95,
                ('SOL', 'USDC'): -0.1,
            }

            # Check both directions
            correlation = default_correlations.get((symbol1, symbol2)) or \
                         default_correlations.get((symbol2, symbol1))

            if correlation:
                # Cache for 1 hour
                self.redis_client.setex(cache_key, 3600, str(correlation))
                return correlation

            return None

        except Exception as e:
            logger.error(f"❌ Error getting correlation: {e}")
            return None

    # Helper methods for missing functionality
    async def find_correlated_positions(self, symbol: str, all_positions: Dict[str, Any]) -> Dict[str, Any]:
        """Find positions correlated with the given symbol"""
        try:
            correlated = {}

            for other_symbol, position in all_positions.items():
                if other_symbol == symbol:
                    continue

                correlation = await self.get_correlation(symbol, other_symbol)
                if correlation and abs(correlation) > self.hedge_threshold:
                    correlated[other_symbol] = position

            return correlated

        except Exception as e:
            logger.error(f"❌ Error finding correlated positions: {e}")
            return {}

    async def calculate_correlation_hedge_effectiveness(self, symbols: List[str], hedge_symbol: str) -> float:
        """Calculate effectiveness of correlation hedge"""
        try:
            correlations = []
            for symbol in symbols:
                corr = await self.get_correlation(symbol, hedge_symbol)
                if corr:
                    correlations.append(abs(corr))

            if not correlations:
                return 0.5

            # Average correlation strength
            avg_correlation = sum(correlations) / len(correlations)
            return min(0.9, avg_correlation)

        except Exception as e:
            logger.error(f"❌ Error calculating correlation hedge effectiveness: {e}")
            return 0.5

    async def get_asset_volatility(self, symbol: str) -> Optional[float]:
        """Get asset volatility"""
        try:
            # Try Redis cache first
            cache_key = f"overmind:volatility:{symbol}"
            cached_vol = self.redis_client.get(cache_key)

            if cached_vol:
                return float(cached_vol)

            # Default volatilities for common assets
            default_volatilities = {
                'SOL': 0.45,
                'BTC': 0.35,
                'ETH': 0.40,
                'USDC': 0.02,
                'USDT': 0.02
            }

            volatility = default_volatilities.get(symbol, 0.5)  # Default 50% for unknown assets

            # Cache for 1 hour
            self.redis_client.setex(cache_key, 3600, str(volatility))
            return volatility

        except Exception as e:
            logger.error(f"❌ Error getting asset volatility: {e}")
            return 0.5

    async def analyze_market_beta_hedging(self, portfolio_risk: PortfolioRisk, positions: Dict[str, Any]) -> Optional[HedgeRecommendation]:
        """Analyze market beta hedging needs"""
        try:
            if abs(portfolio_risk.market_beta) < 1.2:
                return None

            # Recommend hedging with inverse beta instrument
            hedge_symbol = 'USDC'  # Stable asset for beta hedging
            hedge_ratio = -portfolio_risk.market_beta * 0.5  # Partial hedge

            effectiveness = min(0.8, abs(portfolio_risk.market_beta) / 2.0)
            cost = 0.005  # 0.5% cost for beta hedging

            return HedgeRecommendation(
                primary_symbol='PORTFOLIO',
                recommended_hedge_symbol=hedge_symbol,
                hedge_type=HedgeType.PORTFOLIO_HEDGE,
                hedge_ratio=hedge_ratio,
                confidence=0.75,
                expected_effectiveness=effectiveness,
                estimated_cost=cost,
                reasoning=f"High portfolio beta ({portfolio_risk.market_beta:.2f}) requires market hedging",
                urgency=min(1.0, abs(portfolio_risk.market_beta) / 2.0),
                risk_reduction=effectiveness * 0.3,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"❌ Error analyzing market beta hedging: {e}")
            return None

    async def analyze_sector_hedging(self, sector: str, exposure: float, portfolio_risk: PortfolioRisk) -> Optional[HedgeRecommendation]:
        """Analyze sector concentration hedging"""
        try:
            if exposure <= self.max_sector_exposure:
                return None

            # Find hedge for sector concentration
            hedge_symbol = 'SOL'  # Base asset hedge
            hedge_ratio = -(exposure - self.max_sector_exposure)

            effectiveness = min(0.7, exposure - self.max_sector_exposure)
            cost = 0.003  # 0.3% cost for sector hedging

            return HedgeRecommendation(
                primary_symbol=f'SECTOR_{sector}',
                recommended_hedge_symbol=hedge_symbol,
                hedge_type=HedgeType.SECTOR_HEDGE,
                hedge_ratio=hedge_ratio,
                confidence=0.7,
                expected_effectiveness=effectiveness,
                estimated_cost=cost,
                reasoning=f"Sector {sector} overexposed ({exposure:.1%} > {self.max_sector_exposure:.1%})",
                urgency=min(1.0, (exposure - self.max_sector_exposure) * 2),
                risk_reduction=effectiveness * 0.2,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"❌ Error analyzing sector hedging: {e}")
            return None

    async def analyze_var_hedging(self, portfolio_risk: PortfolioRisk, positions: Dict[str, Any]) -> Optional[HedgeRecommendation]:
        """Analyze VaR-based hedging needs"""
        try:
            if portfolio_risk.var_95 <= self.max_portfolio_var:
                return None

            # Recommend portfolio-wide hedge
            hedge_symbol = 'USDC'
            hedge_ratio = -(portfolio_risk.var_95 - self.max_portfolio_var) / portfolio_risk.var_95

            effectiveness = min(0.8, (portfolio_risk.var_95 - self.max_portfolio_var) / portfolio_risk.var_95)
            cost = 0.004  # 0.4% cost for VaR hedging

            return HedgeRecommendation(
                primary_symbol='PORTFOLIO_VAR',
                recommended_hedge_symbol=hedge_symbol,
                hedge_type=HedgeType.PORTFOLIO_HEDGE,
                hedge_ratio=hedge_ratio,
                confidence=0.8,
                expected_effectiveness=effectiveness,
                estimated_cost=cost,
                reasoning=f"Portfolio VaR ({portfolio_risk.var_95:.1%}) exceeds limit ({self.max_portfolio_var:.1%})",
                urgency=min(1.0, (portfolio_risk.var_95 - self.max_portfolio_var) * 10),
                risk_reduction=effectiveness * 0.4,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"❌ Error analyzing VaR hedging: {e}")
            return None

    # Additional helper methods for portfolio risk calculation
    async def get_asset_sector(self, symbol: str) -> Optional[str]:
        """Get asset sector classification"""
        try:
            # Simplified sector mapping
            sector_mappings = {
                'SOL': 'Layer1',
                'ETH': 'Layer1',
                'BTC': 'Layer1',
                'USDC': 'Stablecoin',
                'USDT': 'Stablecoin'
            }

            # Check if it's a memecoin (simplified)
            if any(keyword in symbol.lower() for keyword in ['doge', 'shib', 'pepe', 'bonk']):
                return 'Memecoin'

            return sector_mappings.get(symbol, 'DeFi')

        except Exception as e:
            logger.error(f"❌ Error getting asset sector: {e}")
            return 'Unknown'

    async def calculate_correlation_risk(self, positions: Dict[str, Any]) -> float:
        """Calculate portfolio correlation risk"""
        try:
            if len(positions) < 2:
                return 0.0

            symbols = list(positions.keys())
            total_correlation = 0.0
            pair_count = 0

            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:
                    correlation = await self.get_correlation(symbol1, symbol2)
                    if correlation:
                        total_correlation += abs(correlation)
                        pair_count += 1

            if pair_count == 0:
                return 0.3  # Default moderate correlation risk

            avg_correlation = total_correlation / pair_count
            return min(1.0, avg_correlation)

        except Exception as e:
            logger.error(f"❌ Error calculating correlation risk: {e}")
            return 0.3

    async def calculate_volatility_risk(self, positions: Dict[str, Any]) -> float:
        """Calculate portfolio volatility risk"""
        try:
            if not positions:
                return 0.0

            total_value = sum(pos.get('value', 0.0) for pos in positions.values())
            weighted_volatility = 0.0

            for symbol, position in positions.items():
                weight = position.get('value', 0.0) / total_value if total_value > 0 else 0
                volatility = await self.get_asset_volatility(symbol) or 0.5
                weighted_volatility += weight * volatility

            return weighted_volatility

        except Exception as e:
            logger.error(f"❌ Error calculating volatility risk: {e}")
            return 0.3

    async def calculate_concentration_risk(self, positions: Dict[str, Any]) -> float:
        """Calculate portfolio concentration risk"""
        try:
            if not positions:
                return 0.0

            total_value = sum(pos.get('value', 0.0) for pos in positions.values())

            if total_value == 0:
                return 0.0

            # Calculate Herfindahl-Hirschman Index (HHI)
            hhi = 0.0
            for position in positions.values():
                weight = position.get('value', 0.0) / total_value
                hhi += weight ** 2

            # Normalize HHI to 0-1 scale
            n = len(positions)
            min_hhi = 1.0 / n  # Perfectly diversified
            max_hhi = 1.0      # Fully concentrated

            if max_hhi > min_hhi:
                normalized_hhi = (hhi - min_hhi) / (max_hhi - min_hhi)
            else:
                normalized_hhi = 0.0

            return min(1.0, normalized_hhi)

        except Exception as e:
            logger.error(f"❌ Error calculating concentration risk: {e}")
            return 0.3

    async def calculate_portfolio_beta(self, positions: Dict[str, Any]) -> float:
        """Calculate portfolio beta (market exposure)"""
        try:
            if not positions:
                return 1.0

            # Simplified beta calculation
            # In crypto, SOL can be considered the "market"
            total_value = sum(pos.get('value', 0.0) for pos in positions.values())
            weighted_beta = 0.0

            # Default betas for common assets
            asset_betas = {
                'SOL': 1.0,
                'BTC': 0.8,
                'ETH': 0.9,
                'USDC': 0.0,
                'USDT': 0.0
            }

            for symbol, position in positions.items():
                weight = position.get('value', 0.0) / total_value if total_value > 0 else 0
                beta = asset_betas.get(symbol, 1.2)  # Default high beta for unknown assets
                weighted_beta += weight * beta

            return weighted_beta

        except Exception as e:
            logger.error(f"❌ Error calculating portfolio beta: {e}")
            return 1.0

    async def calculate_portfolio_var(self, positions: Dict[str, Any]) -> float:
        """Calculate portfolio Value at Risk (95% confidence)"""
        try:
            if not positions:
                return 0.0

            # Simplified VaR calculation
            volatility_risk = await self.calculate_volatility_risk(positions)
            correlation_risk = await self.calculate_correlation_risk(positions)
            concentration_risk = await self.calculate_concentration_risk(positions)

            # Combine risks (simplified)
            portfolio_var = (volatility_risk * 0.5 +
                           correlation_risk * 0.3 +
                           concentration_risk * 0.2) * 1.65  # 95% confidence multiplier

            return min(0.2, portfolio_var)  # Cap at 20%

        except Exception as e:
            logger.error(f"❌ Error calculating portfolio VaR: {e}")
            return 0.05

    async def calculate_max_drawdown_risk(self, positions: Dict[str, Any]) -> float:
        """Calculate maximum drawdown risk"""
        try:
            # Simplified calculation based on volatility and concentration
            volatility_risk = await self.calculate_volatility_risk(positions)
            concentration_risk = await self.calculate_concentration_risk(positions)

            # Max drawdown typically 2-3x daily volatility
            max_drawdown_risk = (volatility_risk + concentration_risk * 0.5) * 2.5

            return min(0.5, max_drawdown_risk)  # Cap at 50%

        except Exception as e:
            logger.error(f"❌ Error calculating max drawdown risk: {e}")
            return 0.15

    async def get_hedging_status(self) -> Dict[str, Any]:
        """Get current hedging system status"""
        try:
            return {
                'timestamp': time.time(),
                'active_hedges': len(self.active_hedges),
                'hedge_types': list(set(hedge.hedge_type.value for hedge in self.active_hedges.values())),
                'total_hedge_cost': sum(hedge.cost for hedge in self.active_hedges.values()),
                'average_effectiveness': statistics.mean([hedge.effectiveness for hedge in self.active_hedges.values()]) if self.active_hedges else 0.0,
                'configuration': {
                    'hedge_threshold': self.hedge_threshold,
                    'max_hedge_cost': self.max_hedge_cost,
                    'min_effectiveness': self.min_effectiveness,
                    'max_portfolio_var': self.max_portfolio_var,
                    'max_sector_exposure': self.max_sector_exposure
                }
            }

        except Exception as e:
            logger.error(f"❌ Error getting hedging status: {e}")
            return {'error': str(e)}

async def main():
    """Test the hedging strategy engine"""
    engine = HedgingStrategyEngine()

    # Test with sample portfolio
    sample_portfolio = {
        'SOL': {'value': 100.0, 'quantity': 1.0},
        'BTC': {'value': 50.0, 'quantity': 0.001}
    }

    recommendations = await engine.analyze_hedging_opportunities(sample_portfolio)
    print(f"Found {len(recommendations)} hedging recommendations")

    for rec in recommendations:
        print(f"- {rec.hedge_type.value}: {rec.primary_symbol} -> {rec.recommended_hedge_symbol}")

if __name__ == "__main__":
    asyncio.run(main())
