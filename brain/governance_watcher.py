#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Governance Watcher
Live monitoring of DAO proposals for alpha opportunities
"""

import asyncio
import httpx
import json
import redis
import time
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('GovernanceWatcher')

class GovernanceWatcher:
    """
    Live watcher for DAO governance proposals
    """
    
    def __init__(self):
        """Initialize governance watcher"""
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # DAO endpoints for live monitoring
        self.tracked_daos = {
            "jito": {
                "name": "Jito DAO",
                "forum_url": "https://forum.jito.network/latest.json",
                "token": "JTO",
                "keywords": ["buyback", "burn", "fee", "revenue", "distribution", "yield"]
            },
            "aave": {
                "name": "Aave DAO", 
                "forum_url": "https://governance.aave.com/latest.json",
                "token": "AAVE",
                "keywords": ["safety module", "staking", "rewards", "treasury", "revenue"]
            },
            "uniswap": {
                "name": "Uniswap DAO",
                "forum_url": "https://gov.uniswap.org/latest.json", 
                "token": "UNI",
                "keywords": ["fee switch", "protocol fees", "treasury", "v4"]
            },
            "maker": {
                "name": "MakerDAO/Sky",
                "token": "MKR",
                "keywords": ["burn", "surplus", "buffer", "smart burn engine", "sky"]
            },
            "raydium": {
                "name": "Raydium",
                "token": "RAY", 
                "keywords": ["buyback", "burn", "fees", "memecoin"]
            },
            "jupiter": {
                "name": "Jupiter",
                "token": "JUP",
                "keywords": ["buyback", "jupuary", "perps", "jlp", "treasury"]
            }
        }
        
        # Configuration from environment
        self.min_sentiment_score = float(os.getenv("GOVERNANCE_MIN_SENTIMENT_SCORE", "0.80"))
        self.monitoring_interval = int(os.getenv("GOVERNANCE_MONITORING_INTERVAL", "300"))
        self.positive_keywords = os.getenv("GOVERNANCE_POSITIVE_KEYWORDS", "buyback,burn,fee_switch,revenue_share").split(",")
        self.negative_keywords = os.getenv("GOVERNANCE_NEGATIVE_KEYWORDS", "dilution,unlock,emission_increase").split(",")
        
        # Tracking state
        self.seen_proposals = set()
        self.last_check = {}
        
        logger.info("🔍 Governance Watcher initialized")
        logger.info(f"📊 Monitoring {len(self.tracked_daos)} DAOs")
        logger.info(f"🎯 Min sentiment score: {self.min_sentiment_score}")
        logger.info(f"⏰ Check interval: {self.monitoring_interval}s")
    
    async def start_watching(self):
        """Start the governance watching process"""
        logger.info("🎯 Starting Governance Watcher...")
        
        while True:
            try:
                # Check all DAOs for new proposals
                for dao_id, config in self.tracked_daos.items():
                    await self.check_dao_proposals(dao_id, config)
                
                # Wait before next check
                logger.info(f"⏰ Waiting {self.monitoring_interval}s before next check...")
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in watching loop: {e}")
                await asyncio.sleep(60)
    
    async def check_dao_proposals(self, dao_id: str, config: Dict[str, Any]):
        """Check a specific DAO for new proposals"""
        try:
            logger.info(f"🔍 Checking {config['name']} for proposals...")
            
            # For now, simulate proposal detection
            # In production, this would scrape actual forums/governance sites
            await self.simulate_proposal_check(dao_id, config)
            
        except Exception as e:
            logger.error(f"❌ Error checking {config['name']}: {e}")
    
    async def simulate_proposal_check(self, dao_id: str, config: Dict[str, Any]):
        """Simulate proposal detection for testing"""
        # Simulate finding high-impact proposals periodically
        current_time = time.time()
        last_check = self.last_check.get(dao_id, 0)
        
        # Check every 30 minutes for new proposals
        if current_time - last_check > 1800:  # 30 minutes
            self.last_check[dao_id] = current_time
            
            # Simulate different types of proposals
            if dao_id == "jito":
                await self.simulate_jito_proposal()
            elif dao_id == "maker":
                await self.simulate_maker_proposal()
            elif dao_id == "aave":
                await self.simulate_aave_proposal()
    
    async def simulate_jito_proposal(self):
        """Simulate Jito DAO proposal"""
        proposal_id = f"jito_proposal_{int(time.time())}"
        
        if proposal_id not in self.seen_proposals:
            proposal = {
                "dao": "jito",
                "token": "JTO",
                "title": "JIP-16: Increase Revenue Distribution to 75% Buyback Program",
                "description": "Proposal to increase DAO revenue distribution from 50% to 75% for JTO buyback program. Estimated $7.5M annual buyback based on current revenue.",
                "sentiment_score": 0.88,
                "impact_score": 0.85,
                "proposal_type": "buyback",
                "keywords_found": ["buyback", "revenue", "distribution"],
                "timestamp": time.time()
            }
            
            await self.process_proposal(proposal)
            self.seen_proposals.add(proposal_id)
    
    async def simulate_maker_proposal(self):
        """Simulate MakerDAO proposal"""
        proposal_id = f"maker_proposal_{int(time.time())}"
        
        if proposal_id not in self.seen_proposals:
            proposal = {
                "dao": "maker",
                "token": "MKR",
                "title": "MIP-125: Restart Smart Burn Engine with Enhanced Parameters",
                "description": "Proposal to restart MKR Smart Burn Engine with increased burn rate and lower surplus buffer threshold.",
                "sentiment_score": 0.82,
                "impact_score": 0.78,
                "proposal_type": "burn",
                "keywords_found": ["burn", "smart burn engine"],
                "timestamp": time.time()
            }
            
            await self.process_proposal(proposal)
            self.seen_proposals.add(proposal_id)
    
    async def simulate_aave_proposal(self):
        """Simulate Aave DAO proposal"""
        proposal_id = f"aave_proposal_{int(time.time())}"
        
        if proposal_id not in self.seen_proposals:
            proposal = {
                "dao": "aave",
                "token": "AAVE",
                "title": "AIP-89: Increase Safety Module Rewards by 50%",
                "description": "Proposal to increase AAVE staking rewards in Safety Module from current rate to attract more stakers and improve protocol security.",
                "sentiment_score": 0.75,
                "impact_score": 0.65,
                "proposal_type": "yield_increase",
                "keywords_found": ["rewards", "staking", "safety module"],
                "timestamp": time.time()
            }
            
            await self.process_proposal(proposal)
            self.seen_proposals.add(proposal_id)
    
    async def process_proposal(self, proposal: Dict[str, Any]):
        """Process detected proposal"""
        try:
            logger.info(f"🎯 NEW PROPOSAL DETECTED: {proposal['title']}")
            logger.info(f"   DAO: {proposal['dao'].upper()}")
            logger.info(f"   Token: {proposal['token']}")
            logger.info(f"   Sentiment: {proposal['sentiment_score']:.2f}")
            logger.info(f"   Impact: {proposal['impact_score']:.2f}")
            
            # Check if proposal meets criteria
            if await self.should_trigger_signal(proposal):
                await self.publish_governance_signal(proposal)
            else:
                logger.info(f"   ⚠️ Proposal doesn't meet criteria - skipping")
                
        except Exception as e:
            logger.error(f"❌ Error processing proposal: {e}")
    
    async def should_trigger_signal(self, proposal: Dict[str, Any]) -> bool:
        """Determine if proposal should trigger trading signal"""
        sentiment_score = proposal.get('sentiment_score', 0.0)
        impact_score = proposal.get('impact_score', 0.0)
        
        # Check minimum thresholds
        min_impact = float(os.getenv("GOVERNANCE_MIN_IMPACT_SCORE", "0.70"))
        
        # Must meet both sentiment and impact thresholds
        meets_sentiment = sentiment_score >= self.min_sentiment_score
        meets_impact = impact_score >= min_impact
        
        # Check for positive keywords
        keywords_found = proposal.get('keywords_found', [])
        has_positive_keywords = any(kw in self.positive_keywords for kw in keywords_found)
        
        # Check for negative keywords (disqualifying)
        has_negative_keywords = any(kw in self.negative_keywords for kw in keywords_found)
        
        return meets_sentiment and meets_impact and has_positive_keywords and not has_negative_keywords
    
    async def publish_governance_signal(self, proposal: Dict[str, Any]):
        """Publish governance alpha signal to trading system"""
        try:
            # Create trading signal
            signal = {
                "signal_type": "governance_alpha",
                "token": proposal['token'],
                "dao": proposal['dao'],
                "title": proposal['title'],
                "sentiment_score": proposal['sentiment_score'],
                "impact_score": proposal['impact_score'],
                "proposal_type": proposal['proposal_type'],
                "strategy": "governance_alpha_hunter",
                "timestamp": time.time(),
                "source": "governance_watcher"
            }
            
            # Publish to strategy signals queue
            self.redis_client.lpush("overmind:strategy_signals", json.dumps(signal))
            
            # Also publish alert
            alert = {
                "type": "governance_alpha_signal",
                "message": f"High-impact {proposal['dao'].upper()} proposal detected: {proposal['title']}",
                "token": proposal['token'],
                "sentiment": proposal['sentiment_score'],
                "impact": proposal['impact_score'],
                "timestamp": time.time()
            }
            
            self.redis_client.lpush("overmind:alerts", json.dumps(alert))
            
            logger.info(f"🚀 GOVERNANCE ALPHA SIGNAL PUBLISHED!")
            logger.info(f"   Token: {proposal['token']}")
            logger.info(f"   Strategy: governance_alpha_hunter")
            logger.info(f"   Expected Impact: {proposal['impact_score']:.1%}")
            
        except Exception as e:
            logger.error(f"❌ Failed to publish signal: {e}")
    
    def get_watcher_stats(self) -> Dict[str, Any]:
        """Get governance watcher statistics"""
        return {
            "daos_monitored": len(self.tracked_daos),
            "proposals_seen": len(self.seen_proposals),
            "min_sentiment_threshold": self.min_sentiment_score,
            "monitoring_interval": self.monitoring_interval,
            "positive_keywords": self.positive_keywords,
            "last_checks": self.last_check
        }

async def main():
    """Main function"""
    watcher = GovernanceWatcher()
    
    try:
        await watcher.start_watching()
    except KeyboardInterrupt:
        logger.info("⏹️ Governance Watcher stopped by user")

if __name__ == "__main__":
    asyncio.run(main())
