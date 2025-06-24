"""THE OVERMIND PROTOCOL - MinionAgent Brain Main Entry Point
Standalone entry point for the new MinionAgent-based brain architecture.
"""

import asyncio
import logging
import os
import signal
import sys
from typing import Optional

from .overmind_brain_manager import create_overmind_brain_manager, OVERMINDBrainManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global brain manager instance
brain_manager: Optional[OVERMINDBrainManager] = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"🛑 Received signal {signum}, shutting down...")
    if brain_manager:
        # Create new event loop if needed for shutdown
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(brain_manager.stop())
    sys.exit(0)

async def main():
    """Main entry point for MinionAgent-based OVERMIND Brain"""
    global brain_manager
    
    logger.info("🧠🤖 THE OVERMIND PROTOCOL - MinionAgent Brain Starting...")
    logger.info("=" * 80)
    logger.info("🚀 NEW ARCHITECTURE: Multi-Agent Brain with MinionAgent Framework")
    logger.info("🎯 Specialized Agents: Market Data, Social Sentiment, Risk Analysis, On-Chain")
    logger.info("🧠 Main Brain Manager: OVERMIND_BRAIN coordinates all specialist agents")
    logger.info("⚡ Communication: DragonflyDB for real-time message passing")
    logger.info("🧪 Vector Memory: ChromaDB for experience storage and pattern recognition")
    logger.info("=" * 80)

    try:
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Create brain manager with environment configuration
        brain_manager = create_overmind_brain_manager(
            redis_host=os.getenv("DRAGONFLY_HOST", "localhost"),
            redis_port=int(os.getenv("DRAGONFLY_PORT", "6379")),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        logger.info("🚀 Initializing OVERMIND Brain Manager...")
        
        # Start simple HTTP server on port 8000 for health checks
        import asyncio
        from aiohttp import web
        
        async def health_check(request):
            return web.json_response({
                "status": "running",
                "service": "overmind-brain-manager",
                "version": "2.0-minion-agent",
                "agents": 4
            })
            
        async def status_check(request):
            status = await brain_manager.get_status() if brain_manager else {"status": "initializing"}
            return web.json_response(status)
        
        app = web.Application()
        app.router.add_get('/health', health_check)
        app.router.add_get('/status', status_check)
        
        # Start HTTP server in background
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8000)
        await site.start()
        logger.info("🌐 HTTP server started on http://localhost:8000")
        
        # Start the brain manager (this will run indefinitely)
        await brain_manager.start()

    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Brain Manager execution failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if brain_manager:
            logger.info("🛑 Stopping Brain Manager...")
            await brain_manager.stop()
        logger.info("✅ OVERMIND Brain Manager shutdown complete")

def cli_main():
    """CLI entry point"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown complete")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cli_main()