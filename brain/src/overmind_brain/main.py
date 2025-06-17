"""THE OVERMIND PROTOCOL - Python AI Brain Main Entry Point"""
import asyncio
import logging
from fastapi import FastAPI
from .brain import OVERMINDBrain

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="OVERMIND Brain", version="1.0.0")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "overmind-brain"}

async def main():
    logger.info("🧠 THE OVERMIND PROTOCOL Python Brain starting...")
    
    brain = OVERMINDBrain()
    await brain.start()

if __name__ == "__main__":
    asyncio.run(main())
