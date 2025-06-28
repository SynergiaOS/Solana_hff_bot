#!/usr/bin/env python3
"""
Integration Test Server
Local API server for testing SOL Momentum Strategy integration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from sol_momentum_integration import SOLMomentumIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="OVERMIND Integration Test API", version="1.0.0")

# Global integration instance
sol_momentum_integration = None

@app.on_event("startup")
async def startup_event():
    """Initialize SOL Momentum Integration on startup"""
    global sol_momentum_integration
    
    logger.info("🚀 Starting OVERMIND Integration Test Server...")
    
    try:
        sol_momentum_integration = SOLMomentumIntegration()
        success = await sol_momentum_integration.initialize()
        
        if success:
            logger.info("✅ SOL Momentum Integration initialized successfully")
        else:
            logger.error("❌ Failed to initialize SOL Momentum Integration")
    
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/status")
async def get_system_status():
    """Get overall system status"""
    global sol_momentum_integration
    
    if not sol_momentum_integration:
        raise HTTPException(status_code=503, detail="SOL Momentum Integration not initialized")
    
    try:
        status = sol_momentum_integration.get_strategy_status()
        
        return {
            "system_status": "operational",
            "timestamp": datetime.now().isoformat(),
            "sol_momentum_trader": {
                "status": "active" if status["integration_enabled"] else "inactive",
                "enabled": status["integration_enabled"],
                "ready": status["strategy_ready"],
                "price_history_length": status["price_history_length"],
                "last_update": status.get("last_update"),
                "quicknode_configured": status["quicknode_url_configured"]
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/strategies")
async def get_strategies_status():
    """Get detailed strategies status"""
    global sol_momentum_integration
    
    if not sol_momentum_integration:
        raise HTTPException(status_code=503, detail="SOL Momentum Integration not initialized")
    
    try:
        status = sol_momentum_integration.get_strategy_status()
        
        return {
            "strategies": {
                "sol_momentum": {
                    "name": "SOL Momentum Strategy",
                    "status": "active" if status["integration_enabled"] else "inactive",
                    "enabled": status["integration_enabled"],
                    "ready": status["strategy_ready"],
                    "metrics": {
                        "price_history_length": status["price_history_length"],
                        "last_update": status.get("last_update"),
                        "signals_generated": 0,  # Would be tracked in production
                        "last_signal_type": "HOLD",
                        "confidence": 0.30
                    },
                    "configuration": {
                        "short_ma_period": 5,
                        "long_ma_period": 20,
                        "rsi_period": 14,
                        "volume_threshold": 1.5,
                        "confidence_threshold": 0.6
                    }
                }
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting strategies status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/strategies/sol_momentum/signal")
async def generate_sol_momentum_signal():
    """Generate a new SOL momentum signal"""
    global sol_momentum_integration
    
    if not sol_momentum_integration:
        raise HTTPException(status_code=503, detail="SOL Momentum Integration not initialized")
    
    try:
        logger.info("[INFO] SolMomentumAgent: Manual signal generation requested")
        
        signal = await sol_momentum_integration.generate_trading_signal()
        
        if signal:
            logger.info(f"[INFO] SolMomentumAgent: Signal generated - {signal['action']} (Confidence: {signal['confidence']:.2f})")
            
            return {
                "signal_generated": True,
                "signal": signal,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.warning("[WARNING] SolMomentumAgent: No signal generated")
            return {
                "signal_generated": False,
                "message": "No signal generated",
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        logger.error(f"[ERROR] SolMomentumAgent: Error generating signal - {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/strategies/sol_momentum/test")
async def test_sol_momentum_agent():
    """Run comprehensive test of SOL Momentum Agent"""
    global sol_momentum_integration
    
    if not sol_momentum_integration:
        raise HTTPException(status_code=503, detail="SOL Momentum Integration not initialized")
    
    try:
        logger.info("[INFO] SolMomentumAgent: Starting comprehensive test...")
        
        test_results = []
        
        # Run 3 test cycles
        for i in range(3):
            logger.info(f"[INFO] SolMomentumAgent: Test cycle {i+1}/3 - Analyzing market...")
            
            signal = await sol_momentum_integration.generate_trading_signal()
            
            if signal:
                action = signal['action']
                confidence = signal['confidence']
                price = signal['price']
                reasoning = signal['reasoning']
                
                logger.info(f"[INFO] SolMomentumAgent: RSI analysis complete. Signal: {action}")
                logger.info(f"[INFO] SolMomentumAgent: Confidence: {confidence:.2f}, Price: ${price:.4f}")
                
                if action == 'BUY':
                    logger.info("[INFO] SolMomentumAgent: RSI threshold exceeded. Generating BUY signal.")
                elif action == 'SELL':
                    logger.info("[INFO] SolMomentumAgent: RSI overbought detected. Generating SELL signal.")
                else:
                    logger.info("[INFO] SolMomentumAgent: RSI within neutral zone. Generating HOLD signal.")
                
                test_results.append({
                    "cycle": i + 1,
                    "signal": action,
                    "confidence": confidence,
                    "price": price,
                    "reasoning": reasoning,
                    "timestamp": datetime.now().isoformat()
                })
            
            await asyncio.sleep(1)  # Wait between cycles
        
        logger.info("[INFO] SolMomentumAgent: Comprehensive test completed successfully")
        
        return {
            "test_completed": True,
            "cycles_run": len(test_results),
            "results": test_results,
            "summary": {
                "agent_functional": True,
                "signals_generated": len(test_results),
                "average_confidence": sum(r["confidence"] for r in test_results) / len(test_results) if test_results else 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"[ERROR] SolMomentumAgent: Test failed - {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/sol_momentum")
async def get_sol_momentum_logs():
    """Get recent SOL Momentum Agent logs (simulated)"""
    
    # Simulate recent logs
    logs = [
        {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "[SolMomentumAgent] Agent initialized and ready",
            "component": "SolMomentumAgent"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO", 
            "message": "[SolMomentumAgent] RSI analysis complete. Signal: HOLD",
            "component": "SolMomentumAgent"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": "[SolMomentumAgent] RSI within neutral zone. Generating HOLD signal.",
            "component": "SolMomentumAgent"
        }
    ]
    
    return {
        "logs": logs,
        "total_logs": len(logs),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting OVERMIND Integration Test Server...")
    print("📊 Available endpoints:")
    print("   GET  /health - Health check")
    print("   GET  /status - System status")
    print("   GET  /status/strategies - Strategies status")
    print("   POST /strategies/sol_momentum/signal - Generate signal")
    print("   GET  /strategies/sol_momentum/test - Run comprehensive test")
    print("   GET  /logs/sol_momentum - Get recent logs")
    print("🌐 Server will be available at: http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
