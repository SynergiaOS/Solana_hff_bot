"""THE OVERMIND PROTOCOL - Python AI Brain Main Entry Point
FastAPI server with comprehensive endpoints for brain monitoring and control.
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import redis.asyncio as redis

from .brain import OVERMINDBrain
from .overmind_brain_manager import OVERMINDBrainManager, create_overmind_brain_manager
from .helius_integration import helius_client, get_enhanced_token_data, monitor_wallet_activity

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("overmind-brain")

# Global brain instances
brain_instance: Optional[OVERMINDBrain] = None
brain_manager_instance: Optional[OVERMINDBrainManager] = None

# Enable new MinionAgent brain manager
USE_MINION_AGENT_BRAIN = os.getenv("OVERMIND_USE_MINION_AGENT", "true").lower() == "true"

# Models for API requests/responses
class EmergencyStopRequest(BaseModel):
    reason: Optional[str] = "Manual emergency stop"

class WalletBalance(BaseModel):
    address: str
    balance_sol: float
    balance_usdc: float
    other_tokens: Dict[str, float] = {}

class TransactionLog(BaseModel):
    timestamp: str
    action: str
    symbol: str
    price: float
    quantity: float
    result: str
    pnl: Optional[float] = None
    tx_hash: Optional[str] = None

# Redis connection for caching
async def get_redis():
    redis_url = os.getenv("DRAGONFLY_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url)
    return redis_client

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage brain lifecycle"""
    global brain_instance, brain_manager_instance

    try:
        # Startup
        if USE_MINION_AGENT_BRAIN:
            logger.info("🚀 Starting THE OVERMIND PROTOCOL Brain Manager (MinionAgent)...")

            brain_manager_instance = create_overmind_brain_manager(
                redis_host=os.getenv("DRAGONFLY_HOST", "localhost"),
                redis_port=int(os.getenv("DRAGONFLY_PORT", "6379")),
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )

            # Start brain manager in background
            brain_task = asyncio.create_task(brain_manager_instance.start())
        else:
            logger.info("🚀 Starting THE OVERMIND PROTOCOL Brain (Legacy)...")

            brain_instance = OVERMINDBrain()

            # Start brain in background
            brain_task = asyncio.create_task(brain_instance.start())

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start brain: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down THE OVERMIND PROTOCOL Brain...")
        if brain_manager_instance:
            await brain_manager_instance.stop()
        if brain_instance:
            await brain_instance.stop()

# Create FastAPI app
app = FastAPI(
    title="THE OVERMIND PROTOCOL - AI Brain",
    description="Advanced AI Brain for autonomous trading decisions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health and status endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "overmind-brain",
        "version": "1.0.0"
    }

@app.get("/status")
async def get_brain_status():
    """Get comprehensive brain status"""
    if USE_MINION_AGENT_BRAIN:
        if not brain_manager_instance:
            raise HTTPException(status_code=503, detail="Brain Manager not initialized")
        try:
            status = await brain_manager_instance.get_status()
            status["brain_type"] = "minion_agent_manager"
            return status
        except Exception as e:
            logger.error(f"❌ Failed to get brain manager status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        if not brain_instance:
            raise HTTPException(status_code=503, detail="Brain not initialized")
        try:
            status = await brain_instance.get_brain_status()
            status["brain_type"] = "legacy"
            return status
        except Exception as e:
            logger.error(f"❌ Failed to get brain status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/transactions", response_model=List[TransactionLog])
async def get_transaction_logs(limit: int = Query(50, ge=1, le=1000)):
    """Get recent transaction logs"""
    try:
        redis_client = await get_redis()
        
        # Get transaction logs from Redis
        logs_json = await redis_client.lrange("overmind:logs:transactions", 0, limit-1)
        
        if not logs_json:
            return []
        
        import json
        logs = [json.loads(log) for log in logs_json]
        
        # Convert to TransactionLog model
        transaction_logs = []
        for log in logs:
            transaction_logs.append(TransactionLog(
                timestamp=log.get("timestamp", ""),
                action=log.get("action", ""),
                symbol=log.get("symbol", ""),
                price=log.get("price", 0.0),
                quantity=log.get("quantity", 0.0),
                result=log.get("result", "UNKNOWN"),
                pnl=log.get("pnl"),
                tx_hash=log.get("tx_hash")
            ))
        
        return transaction_logs
    except Exception as e:
        logger.error(f"❌ Failed to get transaction logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wallets/status", response_model=Dict[str, WalletBalance])
async def get_wallet_status():
    """Get wallet balances"""
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    try:
        # Request wallet balances from Rust executor
        command = {
            "action": "GET_WALLET_BALANCE",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send command to executor
        redis_client = await get_redis()
        await redis_client.lpush("overmind:commands", json.dumps(command))
        
        # Wait for response (with timeout)
        response = None
        start_time = time.time()
        while time.time() - start_time < 5:  # 5 second timeout
            response_json = await redis_client.brpop("overmind:wallet_balance_response", timeout=1)
            if response_json:
                response = json.loads(response_json[1])
                break
            await asyncio.sleep(0.1)
        
        if not response:
            # Check cache if no response
            cached_balance = await redis_client.get("overmind:cache:wallet_balance")
            if cached_balance:
                return json.loads(cached_balance)
            raise HTTPException(status_code=504, detail="Timeout waiting for wallet balance")
        
        # Cache the response
        await redis_client.set("overmind:cache:wallet_balance", json.dumps(response))
        await redis_client.expire("overmind:cache:wallet_balance", 300)  # 5 minute cache
        
        return response
    except Exception as e:
        logger.error(f"❌ Failed to get wallet status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/control/emergency-stop")
async def emergency_stop(request: EmergencyStopRequest):
    """Activate emergency stop"""
    global emergency_stop_active
    
    try:
        emergency_stop_active = True
        
        # Log the emergency stop
        logger.warning(f"🚨 EMERGENCY STOP ACTIVATED: {request.reason}")
        
        # Send emergency stop command to executor
        command = {
            "action": "EMERGENCY_STOP",
            "reason": request.reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        redis_client = await get_redis()
        await redis_client.lpush("overmind:commands", json.dumps(command))
        
        # Also set a flag in Redis
        await redis_client.set("overmind:emergency_stop", "true")
        
        return {"status": "EMERGENCY_STOP_ACTIVATED", "reason": request.reason}
    except Exception as e:
        logger.error(f"❌ Failed to activate emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/control/resume")
async def resume_trading():
    """Resume trading after emergency stop"""
    global emergency_stop_active
    
    try:
        if not emergency_stop_active:
            return {"status": "ALREADY_RUNNING"}
        
        emergency_stop_active = False
        
        # Log the resume
        logger.info("▶️ Trading resumed after emergency stop")
        
        # Send resume command to executor
        command = {
            "action": "RESUME_TRADING",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        redis_client = await get_redis()
        await redis_client.lpush("overmind:commands", json.dumps(command))
        
        # Clear the flag in Redis
        await redis_client.delete("overmind:emergency_stop")
        
        return {"status": "TRADING_RESUMED"}
    except Exception as e:
        logger.error(f"❌ Failed to resume trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Main entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run as server
        port = int(os.getenv("AI_BRAIN_PORT", "8000"))
        uvicorn.run("overmind_brain.main:app", host="0.0.0.0", port=port, reload=False)
    else:
        print("Usage: python -m overmind_brain.main server")
