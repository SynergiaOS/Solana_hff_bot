#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Market Scanning and AI Brain Test
Comprehensive test script for market scanning activation, AI Brain analysis,
paper trading execution, and real-time performance monitoring.
"""

import asyncio
import json
import time
import subprocess
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OvermindMarketScanner:
    """Market scanner for THE OVERMIND PROTOCOL"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
        
    def check_system_health(self) -> bool:
        """Check if THE OVERMIND PROTOCOL is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"System Health: {health_data}")
                return health_data.get("status") == "healthy"
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        try:
            response = self.session.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}
    
    def simulate_memcoin_discovery(self) -> List[Dict]:
        """Simulate discovery of new memcoins"""
        # Simulate realistic memcoin data
        memcoins = [
            {
                "symbol": "PEPE2",
                "mint": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
                "market_cap": 1250000,
                "volume_24h": 850000,
                "price_change_24h": 45.7,
                "liquidity": 320000,
                "holder_count": 1250,
                "creation_time": datetime.now() - timedelta(hours=2),
                "dex": "Raydium",
                "risk_score": 0.65
            },
            {
                "symbol": "DOGE3",
                "mint": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                "market_cap": 890000,
                "volume_24h": 1200000,
                "price_change_24h": -12.3,
                "liquidity": 450000,
                "holder_count": 2100,
                "creation_time": datetime.now() - timedelta(hours=6),
                "dex": "Jupiter",
                "risk_score": 0.45
            },
            {
                "symbol": "MOON",
                "mint": "5fTwKZP2AK39LtFN9Ayppu6hdCVKfMGVm79F2EgHCtsi",
                "market_cap": 2100000,
                "volume_24h": 3200000,
                "price_change_24h": 89.2,
                "liquidity": 780000,
                "holder_count": 3500,
                "creation_time": datetime.now() - timedelta(hours=1),
                "dex": "Orca",
                "risk_score": 0.75
            }
        ]
        
        logger.info(f"🔍 Discovered {len(memcoins)} potential memcoins")
        for coin in memcoins:
            logger.info(f"  📊 {coin['symbol']}: ${coin['market_cap']:,} cap, {coin['price_change_24h']:+.1f}% change")
        
        return memcoins
    
    def analyze_with_ai_brain(self, memcoins: List[Dict]) -> List[Dict]:
        """Simulate AI Brain analysis of memcoins"""
        logger.info("🧠 AI Brain analyzing memcoins...")
        
        analyzed_coins = []
        for coin in memcoins:
            # Simulate AI analysis
            ai_score = self._calculate_ai_score(coin)
            recommendation = self._get_ai_recommendation(ai_score)
            
            analyzed_coin = coin.copy()
            analyzed_coin.update({
                "ai_score": ai_score,
                "ai_recommendation": recommendation,
                "confidence": random.uniform(0.6, 0.95),
                "analysis_timestamp": datetime.now(),
                "ai_reasoning": self._generate_ai_reasoning(coin, ai_score)
            })
            
            analyzed_coins.append(analyzed_coin)
            logger.info(f"  🤖 {coin['symbol']}: AI Score {ai_score:.2f}, {recommendation}")
        
        return analyzed_coins
    
    def _calculate_ai_score(self, coin: Dict) -> float:
        """Calculate AI score based on multiple factors"""
        score = 0.0
        
        # Volume/Market Cap ratio (higher is better)
        volume_ratio = coin['volume_24h'] / coin['market_cap']
        score += min(volume_ratio * 10, 0.3)
        
        # Price momentum (positive change is good, but not too extreme)
        price_change = coin['price_change_24h']
        if 10 <= price_change <= 100:
            score += 0.25
        elif 0 <= price_change < 10:
            score += 0.15
        elif price_change > 100:
            score += 0.1  # Too volatile
        
        # Liquidity score
        if coin['liquidity'] > 500000:
            score += 0.2
        elif coin['liquidity'] > 200000:
            score += 0.15
        else:
            score += 0.05
        
        # Holder count (more holders = more stable)
        if coin['holder_count'] > 2000:
            score += 0.15
        elif coin['holder_count'] > 1000:
            score += 0.1
        else:
            score += 0.05
        
        # Risk adjustment
        score *= (1 - coin['risk_score'] * 0.3)
        
        return min(score, 1.0)
    
    def _get_ai_recommendation(self, ai_score: float) -> str:
        """Get AI recommendation based on score"""
        if ai_score >= 0.7:
            return "STRONG_BUY"
        elif ai_score >= 0.5:
            return "BUY"
        elif ai_score >= 0.3:
            return "HOLD"
        else:
            return "AVOID"
    
    def _generate_ai_reasoning(self, coin: Dict, ai_score: float) -> str:
        """Generate AI reasoning for the decision"""
        reasons = []
        
        if coin['volume_24h'] / coin['market_cap'] > 0.5:
            reasons.append("High trading volume indicates strong interest")
        
        if 10 <= coin['price_change_24h'] <= 50:
            reasons.append("Healthy price momentum without excessive volatility")
        
        if coin['liquidity'] > 300000:
            reasons.append("Sufficient liquidity for safe entry/exit")
        
        if coin['holder_count'] > 1500:
            reasons.append("Growing community support")
        
        if coin['risk_score'] < 0.5:
            reasons.append("Low risk profile")
        
        return "; ".join(reasons) if reasons else "Mixed signals require caution"
    
    def execute_paper_trades(self, analyzed_coins: List[Dict]) -> List[Dict]:
        """Execute paper trades on recommended coins"""
        logger.info("💰 Executing paper trades...")
        
        trade_results = []
        for coin in analyzed_coins:
            if coin['ai_recommendation'] in ['STRONG_BUY', 'BUY']:
                # Simulate trade execution
                trade_amount = 1000 if coin['ai_recommendation'] == 'STRONG_BUY' else 500
                
                trade_result = {
                    "symbol": coin['symbol'],
                    "mint": coin['mint'],
                    "action": "BUY",
                    "amount_usd": trade_amount,
                    "ai_score": coin['ai_score'],
                    "confidence": coin['confidence'],
                    "execution_time": datetime.now(),
                    "status": "EXECUTED",
                    "simulated_price": coin['market_cap'] / 1000000,  # Simulate price
                    "slippage": random.uniform(0.1, 0.5),
                    "gas_fee": random.uniform(0.01, 0.05)
                }
                
                trade_results.append(trade_result)
                logger.info(f"  ✅ {coin['symbol']}: ${trade_amount} paper trade executed")
        
        return trade_results
    
    def monitor_positions(self, trades: List[Dict]) -> Dict:
        """Monitor paper trading positions"""
        logger.info("📈 Monitoring positions...")
        
        total_invested = sum(trade['amount_usd'] for trade in trades)
        total_positions = len(trades)
        
        # Simulate position performance
        total_pnl = 0
        for trade in trades:
            # Simulate price movement
            price_change = random.uniform(-10, 15)  # -10% to +15%
            pnl = trade['amount_usd'] * (price_change / 100)
            total_pnl += pnl
            
            trade['current_pnl'] = pnl
            trade['current_pnl_percent'] = price_change
        
        portfolio_summary = {
            "total_positions": total_positions,
            "total_invested": total_invested,
            "total_pnl": total_pnl,
            "total_pnl_percent": (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            "timestamp": datetime.now()
        }
        
        logger.info(f"  📊 Portfolio: {total_positions} positions, ${total_pnl:+.2f} PnL ({portfolio_summary['total_pnl_percent']:+.1f}%)")
        
        return portfolio_summary

async def run_market_scanning_cycle():
    """Run complete market scanning and trading cycle"""
    logger.info("🚀 Starting THE OVERMIND PROTOCOL Market Scanning Cycle")
    
    scanner = OvermindMarketScanner()
    
    # 1. Check system health
    if not scanner.check_system_health():
        logger.error("❌ System health check failed!")
        return
    
    # 2. Get initial metrics
    initial_metrics = scanner.get_system_metrics()
    logger.info(f"📊 Initial metrics: {initial_metrics}")
    
    # 3. Simulate market scanning
    memcoins = scanner.simulate_memcoin_discovery()
    
    # 4. AI Brain analysis
    analyzed_coins = scanner.analyze_with_ai_brain(memcoins)
    
    # 5. Execute paper trades
    trade_results = scanner.execute_paper_trades(analyzed_coins)
    
    # 6. Monitor positions
    portfolio = scanner.monitor_positions(trade_results)
    
    # 7. Final metrics
    final_metrics = scanner.get_system_metrics()
    
    # 8. Generate summary report
    logger.info("📋 CYCLE SUMMARY:")
    logger.info(f"  🔍 Scanned: {len(memcoins)} memcoins")
    logger.info(f"  🧠 Analyzed: {len(analyzed_coins)} coins")
    logger.info(f"  💰 Executed: {len(trade_results)} trades")
    logger.info(f"  📈 Portfolio PnL: ${portfolio['total_pnl']:+.2f} ({portfolio['total_pnl_percent']:+.1f}%)")
    
    return {
        "memcoins_discovered": len(memcoins),
        "coins_analyzed": len(analyzed_coins),
        "trades_executed": len(trade_results),
        "portfolio_summary": portfolio,
        "initial_metrics": initial_metrics,
        "final_metrics": final_metrics
    }

if __name__ == "__main__":
    asyncio.run(run_market_scanning_cycle())
