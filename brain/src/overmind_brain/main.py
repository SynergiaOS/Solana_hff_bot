"""THE OVERMIND PROTOCOL - Python AI Brain Main Entry Point
FastAPI server with comprehensive endpoints for brain monitoring and control.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from .brain import OVERMINDBrain
from .helius_integration import helius_client, get_enhanced_token_data, monitor_wallet_activity

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global brain instance
brain_instance: Optional[OVERMINDBrain] = None

# Pydantic models for API
class MarketDataRequest(BaseModel):
    symbol: str
    price: float
    volume: Optional[float] = None
    timestamp: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

class ExperienceOutcomeRequest(BaseModel):
    memory_id: str
    outcome: Dict[str, Any]

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage brain lifecycle"""
    global brain_instance

    try:
        # Startup
        logger.info("🚀 Starting THE OVERMIND PROTOCOL Brain...")

        brain_instance = OVERMINDBrain(
            redis_host=os.getenv("DRAGONFLY_HOST", "localhost"),
            redis_port=int(os.getenv("DRAGONFLY_PORT", "6379")),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Start brain in background
        brain_task = asyncio.create_task(brain_instance.start())

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start brain: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down THE OVERMIND PROTOCOL Brain...")
        if brain_instance:
            await brain_instance.stop()

# Create FastAPI app
app = FastAPI(
    title="THE OVERMIND PROTOCOL - AI Brain",
    description="Advanced AI Brain for autonomous trading decisions",
    version="1.0.0",
    lifespan=lifespan
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
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    try:
        status = await brain_instance.get_brain_status()
        return status
    except Exception as e:
        logger.error(f"❌ Failed to get brain status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analysis endpoints
@app.post("/analyze")
async def analyze_market_data(request: MarketDataRequest):
    """Perform manual market analysis"""
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    try:
        # Prepare market data
        market_data = {
            "symbol": request.symbol,
            "price": request.price,
            "volume": request.volume,
            "timestamp": request.timestamp,
            **(request.additional_data or {})
        }

        # Perform analysis
        results = await brain_instance.manual_analysis(
            symbol=request.symbol,
            market_data=market_data
        )

        return results

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Memory endpoints
@app.get("/memory/stats")
async def get_memory_stats():
    """Get vector memory statistics"""
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    try:
        stats = await brain_instance.vector_memory.get_memory_stats()
        return stats
    except Exception as e:
        logger.error(f"❌ Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/recent")
async def get_recent_experiences(limit: int = 10, symbol: Optional[str] = None):
    """Get recent trading experiences"""
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    try:
        experiences = await brain_instance.vector_memory.get_recent_experiences(
            limit=limit,
            symbol=symbol
        )
        return {"experiences": experiences}
    except Exception as e:
        logger.error(f"❌ Failed to get recent experiences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/update-outcome")
async def update_experience_outcome(request: ExperienceOutcomeRequest):
    """Update experience with outcome data"""
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    try:
        success = await brain_instance.update_experience_outcome(
            memory_id=request.memory_id,
            outcome=request.outcome
        )

        return {"success": success, "memory_id": request.memory_id}

    except Exception as e:
        logger.error(f"❌ Failed to update experience outcome: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Control endpoints
@app.post("/control/emergency-stop")
async def emergency_stop():
    """Emergency stop the brain"""
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    try:
        await brain_instance.emergency_stop()
        return {"status": "emergency_stop_initiated"}
    except Exception as e:
        logger.error(f"❌ Emergency stop failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search endpoints
@app.get("/memory/search")
async def search_experiences(query: str, top_k: int = 5):
    """Search for similar experiences"""
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    try:
        results = await brain_instance.vector_memory.similarity_search(
            query=query,
            top_k=top_k
        )
        return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"❌ Memory search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Development and testing endpoints
@app.get("/debug/components")
async def debug_components():
    """Debug information about brain components"""
    if not brain_instance:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    return {
        "vector_memory": {
            "collection_name": brain_instance.vector_memory.collection_name,
            "embedding_model": brain_instance.vector_memory.embedding_model_name
        },
        "decision_engine": {
            "model": brain_instance.decision_engine.model,
            "temperature": brain_instance.decision_engine.temperature
        },
        "risk_analyzer": {
            "max_portfolio_risk": brain_instance.risk_analyzer.max_portfolio_risk,
            "max_position_size": brain_instance.risk_analyzer.max_position_size
        },
        "dragonfly_connection": {
            "host": brain_instance.redis_host,
            "port": brain_instance.redis_port
        }
    }

# Helius API Premium Endpoints
@app.get("/helius/status")
async def get_helius_status():
    """Get Helius API integration status"""
    try:
        status = helius_client.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get Helius status: {e}")
        raise HTTPException(status_code=500, detail=f"Helius status error: {str(e)}")

@app.get("/helius/token/{mint_address}")
async def get_enhanced_token_info(mint_address: str):
    """Get enhanced token information using Helius premium features"""
    try:
        token_data = await get_enhanced_token_data(mint_address)
        return token_data
    except Exception as e:
        logger.error(f"Failed to get enhanced token data: {e}")
        raise HTTPException(status_code=500, detail=f"Token data error: {str(e)}")

@app.get("/helius/wallet/{wallet_address}")
async def get_wallet_activity(wallet_address: str):
    """Monitor wallet activity using Helius enhanced features"""
    try:
        activity = await monitor_wallet_activity(wallet_address)
        return activity
    except Exception as e:
        logger.error(f"Failed to get wallet activity: {e}")
        raise HTTPException(status_code=500, detail=f"Wallet activity error: {str(e)}")

@app.get("/helius/transactions/{address}")
async def get_enhanced_transactions_endpoint(address: str, limit: int = 50):
    """Get enhanced transaction data for an address"""
    try:
        transactions = await helius_client.get_enhanced_transactions(address, limit)
        return {"address": address, "transactions": transactions, "count": len(transactions)}
    except Exception as e:
        logger.error(f"Failed to get enhanced transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Transaction data error: {str(e)}")

@app.get("/helius/metadata/{mint_address}")
async def get_token_metadata_endpoint(mint_address: str):
    """Get comprehensive token metadata using Helius DAS API"""
    try:
        metadata = await helius_client.get_token_metadata(mint_address)
        return {"mint_address": mint_address, "metadata": metadata}
    except Exception as e:
        logger.error(f"Failed to get token metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Metadata error: {str(e)}")

# Main entry point for standalone execution
async def main():
    """Main entry point for standalone execution"""
    logger.info("🧠 THE OVERMIND PROTOCOL Python Brain starting in standalone mode...")

    try:
        brain = OVERMINDBrain(
            redis_host=os.getenv("DRAGONFLY_HOST", "localhost"),
            redis_port=int(os.getenv("DRAGONFLY_PORT", "6379")),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        await brain.start()

    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Brain execution failed: {e}")
        raise

# FastAPI server entry point
def start_server():
    """Start FastAPI server"""
    uvicorn.run(
        "overmind_brain.main:app",
        host="0.0.0.0",
        port=int(os.getenv("BRAIN_PORT", "8000")),
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Start FastAPI server
        start_server()
    else:
        # Run standalone brain
        asyncio.run(main())
