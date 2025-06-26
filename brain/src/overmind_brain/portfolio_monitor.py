"""THE OVERMIND PROTOCOL - Portfolio Monitor
Real-time portfolio monitoring system with dynamic goal tracking.
"""

import asyncio
import logging
import json
import httpx
import redis.asyncio as aioredis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import os

from .goal_manager import dynamic_goal_manager, TradingGoal

logger = logging.getLogger(__name__)

@dataclass
class PortfolioState:
    """Portfolio state data structure with dynamic goal support."""
    total_value_usd: float
    total_value_sol: float
    goal_progress_percentage: float
    wallet_balances: Dict[str, Dict[str, float]]
    last_updated: str
    price_data: Dict[str, float]
    historical_progression: List[Dict[str, Any]]
    current_goal: Optional[Dict[str, Any]] = None  # Current trading goal
    goal_last_modified: Optional[str] = None       # Goal modification timestamp

class PortfolioMonitor:
    """Real-time portfolio monitoring system for THE OVERMIND PROTOCOL."""
    
    def __init__(self,
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 helius_api_key: Optional[str] = None,
                 target_sol_goal: float = 2.0,  # Fallback if no dynamic goal
                 update_interval: int = 60):
        """Initialize the Portfolio Monitor with dynamic goal support.

        Args:
            redis_host: DragonflyDB/Redis host
            redis_port: DragonflyDB/Redis port
            helius_api_key: Helius API key for blockchain data
            target_sol_goal: Fallback SOL goal (default: 2.0)
            update_interval: Update interval in seconds (default: 60)
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.helius_api_key = helius_api_key or os.getenv("HELIUS_API_KEY")
        self.fallback_target_sol = target_sol_goal  # Fallback target
        self.update_interval = update_interval

        # Dynamic goal tracking
        self.current_goal = None
        self.goal_last_checked = None
        
        # Redis connection
        self.redis_client = None
        
        # HTTP client for API calls
        self.http_client = None
        
        # Monitoring state
        self.is_running = False
        self.last_update = None
        self.error_count = 0
        self.max_errors = 10
        
        # Monitored wallets (will be loaded from config)
        self.monitored_wallets = []
        
        # Price cache
        self.price_cache = {}
        self.price_cache_expiry = None
        
        logger.info(f"💰 Portfolio Monitor initialized with dynamic goal support")
    
    async def initialize(self):
        """Initialize connections and load configuration."""
        try:
            # Initialize Redis connection
            self.redis_client = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info(f"✅ Portfolio Monitor connected to DragonflyDB")
            
            # Initialize HTTP client
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
            # Load monitored wallets from configuration
            await self._load_wallet_configuration()

            # Initialize goal manager
            await dynamic_goal_manager.initialize()

            # Load current goal
            await self._update_current_goal()

            logger.info("🚀 Portfolio Monitor fully initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Portfolio Monitor: {e}")
            raise
    
    async def _load_wallet_configuration(self):
        """Load wallet configuration from DragonflyDB or environment."""
        try:
            # Try to load from DragonflyDB first
            config_data = await self.redis_client.get("config:monitored_wallets")
            
            if config_data:
                self.monitored_wallets = json.loads(config_data)
                logger.info(f"📋 Loaded {len(self.monitored_wallets)} wallets from DragonflyDB")
            else:
                # Fallback to environment variable or default
                wallet_env = os.getenv("MONITORED_WALLETS")
                if wallet_env:
                    self.monitored_wallets = json.loads(wallet_env)
                else:
                    # Default test wallet (replace with actual wallet addresses)
                    self.monitored_wallets = [
                        {
                            "address": "11111111111111111111111111111112",  # System program (placeholder)
                            "name": "main_wallet",
                            "type": "trading"
                        }
                    ]
                
                # Store in DragonflyDB for future use
                await self.redis_client.set(
                    "config:monitored_wallets",
                    json.dumps(self.monitored_wallets)
                )
                
                logger.info(f"📋 Configured {len(self.monitored_wallets)} default wallets")
                
        except Exception as e:
            logger.error(f"❌ Failed to load wallet configuration: {e}")
            # Use minimal default configuration
            self.monitored_wallets = []

    async def _update_current_goal(self):
        """Update current goal from goal manager."""
        try:
            self.current_goal = await dynamic_goal_manager.get_current_goal()
            if self.current_goal:
                logger.info(f"🎯 Current goal: {self.current_goal.description}")
            else:
                logger.warning("⚠️ No current goal found, using fallback")
        except Exception as e:
            logger.error(f"❌ Failed to update current goal: {e}")

    async def _get_target_sol(self) -> float:
        """Get current target SOL amount from dynamic goal or fallback."""
        try:
            # Check for goal changes
            if await dynamic_goal_manager.check_for_goal_changes():
                await self._update_current_goal()

            if self.current_goal:
                return self.current_goal.target_sol
            else:
                return self.fallback_target_sol
        except Exception as e:
            logger.error(f"❌ Failed to get target SOL: {e}")
            return self.fallback_target_sol
    
    async def _fetch_sol_price(self) -> float:
        """Fetch current SOL price in USD."""
        try:
            # Check cache first
            if (self.price_cache_expiry and 
                datetime.utcnow() < self.price_cache_expiry and 
                "SOL" in self.price_cache):
                return self.price_cache["SOL"]
            
            # Fetch from CoinGecko API (free tier)
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": "solana",
                "vs_currencies": "usd"
            }
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            sol_price = data["solana"]["usd"]
            
            # Update cache
            self.price_cache["SOL"] = sol_price
            self.price_cache_expiry = datetime.utcnow() + timedelta(minutes=5)
            
            logger.debug(f"💲 SOL price updated: ${sol_price:.2f}")
            return sol_price
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch SOL price: {e}")
            # Return cached price or fallback
            return self.price_cache.get("SOL", 100.0)  # Fallback price
    
    async def _fetch_wallet_balance(self, wallet_address: str) -> Dict[str, float]:
        """Fetch balance for a specific wallet using Helius API."""
        try:
            if not self.helius_api_key:
                logger.warning("⚠️ No Helius API key - using mock data")
                return {"SOL": 0.1, "USDC": 10.0}  # Mock data for testing
            
            # Use Helius API to get wallet balance
            url = f"https://api.helius.xyz/v0/addresses/{wallet_address}/balances"
            params = {"api-key": self.helius_api_key}
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Process balance data
            balances = {}
            
            # Extract SOL balance
            if "nativeBalance" in data:
                balances["SOL"] = data["nativeBalance"] / 1e9  # Convert lamports to SOL
            
            # Extract token balances
            if "tokens" in data:
                for token in data["tokens"]:
                    symbol = token.get("mint", "UNKNOWN")
                    amount = token.get("amount", 0) / (10 ** token.get("decimals", 9))
                    balances[symbol] = amount
            
            return balances
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch wallet balance for {wallet_address}: {e}")
            return {}
    
    async def _calculate_portfolio_value(self, all_balances: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Calculate total portfolio value in USD and SOL."""
        try:
            sol_price = await self._fetch_sol_price()
            
            total_value_usd = 0.0
            total_sol_equivalent = 0.0
            
            for wallet_name, balances in all_balances.items():
                for token, amount in balances.items():
                    if token == "SOL":
                        value_usd = amount * sol_price
                        total_value_usd += value_usd
                        total_sol_equivalent += amount
                    elif token == "USDC":
                        # Assume USDC = $1
                        total_value_usd += amount
                        total_sol_equivalent += amount / sol_price
                    else:
                        # For other tokens, we'd need additional price data
                        # For now, skip or use mock values
                        pass
            
            return {
                "total_value_usd": total_value_usd,
                "total_value_sol": total_sol_equivalent,
                "sol_price": sol_price
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to calculate portfolio value: {e}")
            return {
                "total_value_usd": 0.0,
                "total_value_sol": 0.0,
                "sol_price": 100.0
            }

    async def _update_portfolio_state(self) -> PortfolioState:
        """Update and return current portfolio state."""
        try:
            # Fetch balances for all monitored wallets
            all_balances = {}

            for wallet in self.monitored_wallets:
                wallet_address = wallet["address"]
                wallet_name = wallet["name"]

                balances = await self._fetch_wallet_balance(wallet_address)
                all_balances[wallet_name] = balances

                logger.debug(f"💰 {wallet_name}: {balances}")

            # Calculate total portfolio value
            portfolio_value = await self._calculate_portfolio_value(all_balances)

            # Calculate progress toward dynamic goal
            total_sol = portfolio_value["total_value_sol"]
            target_sol = await self._get_target_sol()
            progress_percentage = min((total_sol / target_sol) * 100, 100.0)

            # Load historical data
            historical_data = await self._load_historical_progression()

            # Create new progression entry
            new_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_value_usd": portfolio_value["total_value_usd"],
                "total_value_sol": total_sol,
                "progress_percentage": progress_percentage,
                "sol_price": portfolio_value["sol_price"]
            }

            # Add to historical data (keep last 1000 entries)
            historical_data.append(new_entry)
            if len(historical_data) > 1000:
                historical_data = historical_data[-1000:]

            # Get current goal information
            current_goal_dict = None
            goal_last_modified = None
            if self.current_goal:
                current_goal_dict = {
                    "goal_type": self.current_goal.goal_type.value,
                    "target_sol": self.current_goal.target_sol,
                    "target_usd": self.current_goal.target_usd,
                    "description": self.current_goal.description
                }
                goal_last_modified = self.current_goal.modified_at

            # Create portfolio state with goal information
            portfolio_state = PortfolioState(
                total_value_usd=portfolio_value["total_value_usd"],
                total_value_sol=total_sol,
                goal_progress_percentage=progress_percentage,
                wallet_balances=all_balances,
                last_updated=datetime.utcnow().isoformat(),
                price_data={"SOL": portfolio_value["sol_price"]},
                historical_progression=historical_data,
                current_goal=current_goal_dict,
                goal_last_modified=goal_last_modified
            )

            # Store in DragonflyDB
            await self._store_portfolio_state(portfolio_state)

            # Store historical data
            await self._store_historical_progression(historical_data)

            logger.info(f"📊 Portfolio updated: {total_sol:.4f} SOL (${portfolio_value['total_value_usd']:.2f}) - {progress_percentage:.1f}% to goal")

            return portfolio_state

        except Exception as e:
            logger.error(f"❌ Failed to update portfolio state: {e}")
            raise

    async def _store_portfolio_state(self, state: PortfolioState):
        """Store portfolio state in DragonflyDB."""
        try:
            state_data = asdict(state)
            await self.redis_client.set(
                "state:portfolio",
                json.dumps(state_data, default=str)
            )

            # Also store with timestamp for historical tracking
            timestamp_key = f"state:portfolio:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            await self.redis_client.setex(
                timestamp_key,
                86400,  # 24 hour expiry
                json.dumps(state_data, default=str)
            )

        except Exception as e:
            logger.error(f"❌ Failed to store portfolio state: {e}")

    async def _load_historical_progression(self) -> List[Dict[str, Any]]:
        """Load historical progression data."""
        try:
            data = await self.redis_client.get("state:portfolio_history")
            if data:
                return json.loads(data)
            return []
        except Exception as e:
            logger.error(f"❌ Failed to load historical progression: {e}")
            return []

    async def _store_historical_progression(self, historical_data: List[Dict[str, Any]]):
        """Store historical progression data."""
        try:
            await self.redis_client.set(
                "state:portfolio_history",
                json.dumps(historical_data, default=str)
            )
        except Exception as e:
            logger.error(f"❌ Failed to store historical progression: {e}")

    async def get_current_state(self) -> Optional[PortfolioState]:
        """Get current portfolio state from DragonflyDB."""
        try:
            data = await self.redis_client.get("state:portfolio")
            if data:
                state_dict = json.loads(data)
                return PortfolioState(**state_dict)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get current portfolio state: {e}")
            return None

    async def _monitoring_loop(self):
        """Main monitoring loop that runs continuously."""
        logger.info(f"🔄 Starting portfolio monitoring loop (interval: {self.update_interval}s)")

        while self.is_running:
            try:
                # Update portfolio state
                await self._update_portfolio_state()

                # Reset error count on successful update
                self.error_count = 0
                self.last_update = datetime.utcnow()

                # Wait for next update
                await asyncio.sleep(self.update_interval)

            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Portfolio monitoring error ({self.error_count}/{self.max_errors}): {e}")

                if self.error_count >= self.max_errors:
                    logger.error("🚨 Too many errors - stopping portfolio monitoring")
                    self.is_running = False
                    break

                # Exponential backoff on errors
                backoff_time = min(300, 30 * (2 ** (self.error_count - 1)))
                logger.info(f"⏳ Backing off for {backoff_time} seconds")
                await asyncio.sleep(backoff_time)

    async def start_monitoring(self):
        """Start the portfolio monitoring service."""
        if self.is_running:
            logger.warning("⚠️ Portfolio monitoring already running")
            return

        self.is_running = True
        self.error_count = 0

        logger.info("🚀 Starting portfolio monitoring service")

        # Start monitoring loop in background
        asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop the portfolio monitoring service."""
        logger.info("🛑 Stopping portfolio monitoring service")
        self.is_running = False

        if self.http_client:
            await self.http_client.aclose()

        if self.redis_client:
            await self.redis_client.close()

    async def get_status(self) -> Dict[str, Any]:
        """Get monitoring service status."""
        return {
            "is_running": self.is_running,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "error_count": self.error_count,
            "monitored_wallets": len(self.monitored_wallets),
            "target_sol_goal": self.target_sol_goal,
            "update_interval": self.update_interval
        }
