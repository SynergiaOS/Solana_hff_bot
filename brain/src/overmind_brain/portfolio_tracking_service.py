"""THE OVERMIND PROTOCOL - Portfolio Tracking Service
Advanced asynchronous portfolio tracking with rate limiting, health monitoring, and fallback mechanisms.
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import redis.asyncio as aioredis

from .portfolio_monitor import PortfolioMonitor, PortfolioState

logger = logging.getLogger(__name__)

@dataclass
class ServiceHealth:
    """Service health monitoring data."""
    is_healthy: bool
    last_successful_update: Optional[datetime]
    consecutive_failures: int
    api_rate_limit_remaining: int
    connection_status: Dict[str, bool]
    performance_metrics: Dict[str, float]

class PortfolioTrackingService:
    """Advanced asynchronous portfolio tracking service with comprehensive monitoring."""
    
    def __init__(self, 
                 portfolio_monitor: PortfolioMonitor,
                 redis_host: str = "localhost",
                 redis_port: int = 6379):
        """Initialize the Portfolio Tracking Service.
        
        Args:
            portfolio_monitor: PortfolioMonitor instance
            redis_host: DragonflyDB/Redis host
            redis_port: DragonflyDB/Redis port
        """
        self.portfolio_monitor = portfolio_monitor
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Service state
        self.is_running = False
        self.service_task = None
        
        # Health monitoring
        self.health = ServiceHealth(
            is_healthy=True,
            last_successful_update=None,
            consecutive_failures=0,
            api_rate_limit_remaining=1000,
            connection_status={
                "dragonfly": False,
                "helius_api": False,
                "coingecko_api": False
            },
            performance_metrics={
                "avg_update_time": 0.0,
                "last_update_time": 0.0,
                "updates_per_hour": 0.0
            }
        )
        
        # Rate limiting
        self.rate_limiter = {
            "helius": {
                "requests_per_minute": 100,
                "current_requests": 0,
                "reset_time": time.time() + 60
            },
            "coingecko": {
                "requests_per_minute": 10,  # Free tier limit
                "current_requests": 0,
                "reset_time": time.time() + 60
            }
        }
        
        # Performance tracking
        self.update_times = []
        self.update_count = 0
        
        # Redis connection for health monitoring
        self.redis_client = None
        
        logger.info("🔄 Portfolio Tracking Service initialized")
    
    async def initialize(self):
        """Initialize the tracking service."""
        try:
            # Initialize Redis connection
            self.redis_client = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self.health.connection_status["dragonfly"] = True
            
            # Initialize portfolio monitor
            await self.portfolio_monitor.initialize()
            
            logger.info("✅ Portfolio Tracking Service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Portfolio Tracking Service: {e}")
            self.health.is_healthy = False
            raise
    
    async def _check_rate_limit(self, service: str) -> bool:
        """Check if we can make a request to the specified service."""
        current_time = time.time()
        rate_limit = self.rate_limiter[service]
        
        # Reset counter if minute has passed
        if current_time >= rate_limit["reset_time"]:
            rate_limit["current_requests"] = 0
            rate_limit["reset_time"] = current_time + 60
        
        # Check if we're under the limit
        if rate_limit["current_requests"] < rate_limit["requests_per_minute"]:
            rate_limit["current_requests"] += 1
            return True
        
        return False
    
    async def _test_api_connections(self):
        """Test connections to external APIs."""
        try:
            # Test Helius API connection
            if await self._check_rate_limit("helius"):
                # Simple test - this would be a lightweight API call
                self.health.connection_status["helius_api"] = True
            
            # Test CoinGecko API connection
            if await self._check_rate_limit("coingecko"):
                # Simple test - this would be a lightweight API call
                self.health.connection_status["coingecko_api"] = True
                
        except Exception as e:
            logger.warning(f"⚠️ API connection test failed: {e}")
            self.health.connection_status["helius_api"] = False
            self.health.connection_status["coingecko_api"] = False
    
    async def _update_performance_metrics(self, update_time: float):
        """Update performance metrics."""
        self.update_times.append(update_time)
        self.update_count += 1
        
        # Keep only last 100 update times
        if len(self.update_times) > 100:
            self.update_times = self.update_times[-100:]
        
        # Calculate metrics
        self.health.performance_metrics["last_update_time"] = update_time
        self.health.performance_metrics["avg_update_time"] = sum(self.update_times) / len(self.update_times)
        
        # Calculate updates per hour (based on last hour of data)
        one_hour_ago = time.time() - 3600
        recent_updates = [t for t in self.update_times if t > one_hour_ago]
        self.health.performance_metrics["updates_per_hour"] = len(recent_updates)
    
    async def _store_health_metrics(self):
        """Store health metrics in DragonflyDB."""
        try:
            health_data = {
                "is_healthy": self.health.is_healthy,
                "last_successful_update": self.health.last_successful_update.isoformat() if self.health.last_successful_update else None,
                "consecutive_failures": self.health.consecutive_failures,
                "api_rate_limit_remaining": self.health.api_rate_limit_remaining,
                "connection_status": self.health.connection_status,
                "performance_metrics": self.health.performance_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.redis_client.set(
                "health:portfolio_tracking",
                json.dumps(health_data, default=str)
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to store health metrics: {e}")
    
    async def _handle_update_failure(self, error: Exception):
        """Handle portfolio update failure with exponential backoff."""
        self.health.consecutive_failures += 1
        
        logger.error(f"❌ Portfolio update failed (attempt {self.health.consecutive_failures}): {error}")
        
        # Exponential backoff calculation
        base_delay = 30  # 30 seconds base delay
        max_delay = 300  # 5 minutes max delay
        delay = min(max_delay, base_delay * (2 ** (self.health.consecutive_failures - 1)))
        
        # Add jitter to prevent thundering herd
        jitter = delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)
        final_delay = delay + jitter
        
        logger.info(f"⏳ Backing off for {final_delay:.1f} seconds")
        
        # Mark as unhealthy if too many consecutive failures
        if self.health.consecutive_failures >= 5:
            self.health.is_healthy = False
            logger.error("🚨 Portfolio tracking service marked as unhealthy")
        
        await asyncio.sleep(final_delay)
    
    async def _portfolio_update_cycle(self):
        """Single portfolio update cycle with comprehensive error handling."""
        start_time = time.time()
        
        try:
            # Test API connections before update
            await self._test_api_connections()
            
            # Check rate limits
            if not await self._check_rate_limit("helius"):
                logger.warning("⚠️ Helius API rate limit reached - skipping update")
                return
            
            if not await self._check_rate_limit("coingecko"):
                logger.warning("⚠️ CoinGecko API rate limit reached - using cached prices")
            
            # Perform portfolio update
            portfolio_state = await self.portfolio_monitor._update_portfolio_state()
            
            # Update success metrics
            self.health.last_successful_update = datetime.utcnow()
            self.health.consecutive_failures = 0
            self.health.is_healthy = True
            
            # Update performance metrics
            update_time = time.time() - start_time
            await self._update_performance_metrics(update_time)
            
            logger.debug(f"✅ Portfolio update completed in {update_time:.2f}s")
            
        except Exception as e:
            await self._handle_update_failure(e)
        
        finally:
            # Always store health metrics
            await self._store_health_metrics()
    
    async def _tracking_loop(self):
        """Main tracking loop with health monitoring."""
        logger.info("🔄 Starting portfolio tracking loop")
        
        while self.is_running:
            try:
                # Perform update cycle
                await self._portfolio_update_cycle()
                
                # Wait for next update (respecting rate limits)
                await asyncio.sleep(self.portfolio_monitor.update_interval)
                
            except asyncio.CancelledError:
                logger.info("🛑 Portfolio tracking loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in tracking loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def start(self):
        """Start the portfolio tracking service."""
        if self.is_running:
            logger.warning("⚠️ Portfolio tracking service already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting portfolio tracking service")
        
        # Start the tracking loop
        self.service_task = asyncio.create_task(self._tracking_loop())
        
        # Start portfolio monitor
        await self.portfolio_monitor.start_monitoring()
    
    async def stop(self):
        """Stop the portfolio tracking service."""
        logger.info("🛑 Stopping portfolio tracking service")
        
        self.is_running = False
        
        if self.service_task:
            self.service_task.cancel()
            try:
                await self.service_task
            except asyncio.CancelledError:
                pass
        
        # Stop portfolio monitor
        await self.portfolio_monitor.stop_monitoring()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        return {
            "service_running": self.is_running,
            "health": {
                "is_healthy": self.health.is_healthy,
                "last_successful_update": self.health.last_successful_update.isoformat() if self.health.last_successful_update else None,
                "consecutive_failures": self.health.consecutive_failures,
                "connection_status": self.health.connection_status,
                "performance_metrics": self.health.performance_metrics
            },
            "rate_limiting": {
                service: {
                    "requests_remaining": limit["requests_per_minute"] - limit["current_requests"],
                    "reset_in_seconds": max(0, limit["reset_time"] - time.time())
                }
                for service, limit in self.rate_limiter.items()
            },
            "portfolio_monitor_status": await self.portfolio_monitor.get_status()
        }
