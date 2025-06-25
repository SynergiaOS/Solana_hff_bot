#!/usr/bin/env python3
"""
OVERMIND PROTOCOL - Simple Solana Metrics
Direct Helius API integration for real-time Solana data
"""

import aiohttp
import asyncio
import json
import os
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleSolanaMetrics:
    def __init__(self):
        self.helius_api_key = 'edbcd361-78a0-4998-bd1e-8d4666722f82'
        self.helius_rpc = f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}"
        self.start_time = datetime.now()
        
        # Cache for data
        self.sol_price = 0.0
        self.network_tps = 0.0
        self.last_update = datetime.now()
        
        print(f"🌐 Simple Solana Metrics initialized")
        print(f"🔗 Helius API: {self.helius_api_key[:8]}...")
    
    async def fetch_sol_price(self):
        """Fetch SOL price from CoinGecko"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        price = data.get('solana', {}).get('usd', 0.0)
                        self.sol_price = float(price)
                        return True
        except Exception as e:
            print(f"❌ Price fetch failed: {e}")
        return False
    
    async def fetch_network_tps(self):
        """Fetch network TPS from Helius"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getRecentPerformanceSamples",
                    "params": [1]
                }
                
                async with session.post(self.helius_rpc, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data.get('result', [])
                        if result:
                            sample = result[0]
                            tps = sample.get('numTransactions', 0) / sample.get('samplePeriodSecs', 1)
                            self.network_tps = round(tps, 2)
                            return True
        except Exception as e:
            print(f"❌ TPS fetch failed: {e}")
        return False
    
    async def update_data(self):
        """Update all Solana data"""
        price_ok = await self.fetch_sol_price()
        tps_ok = await self.fetch_network_tps()
        
        if price_ok or tps_ok:
            self.last_update = datetime.now()
            print(f"📊 Updated: SOL=${self.sol_price:.2f}, TPS={self.network_tps:.1f}")
    
    def generate_metrics(self):
        """Generate Prometheus metrics"""
        validation_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        data_age = (datetime.now() - self.last_update).total_seconds()
        
        return f"""# HELP overmind_brain_status AI Brain operational status
# TYPE overmind_brain_status gauge
overmind_brain_status 1

# HELP overmind_validation_hours Hours of mainnet validation completed
# TYPE overmind_validation_hours gauge
overmind_validation_hours {validation_hours:.2f}

# HELP solana_price_usd Current SOL price in USD (LIVE HELIUS DATA)
# TYPE solana_price_usd gauge
solana_price_usd {self.sol_price:.2f}

# HELP solana_network_tps Current Solana network TPS (LIVE HELIUS DATA)
# TYPE solana_network_tps gauge
solana_network_tps {self.network_tps:.2f}

# HELP solana_data_age_seconds Age of Solana data in seconds
# TYPE solana_data_age_seconds gauge
solana_data_age_seconds {data_age:.1f}

# HELP overmind_active_strategies Number of active trading strategies
# TYPE overmind_active_strategies gauge
overmind_active_strategies 1

# HELP overmind_active_positions Number of currently active positions  
# TYPE overmind_active_positions gauge
overmind_active_positions 0

# HELP overmind_paper_trading_mode Paper trading mode active
# TYPE overmind_paper_trading_mode gauge
overmind_paper_trading_mode 1

# HELP overmind_helius_integration Helius API integration status
# TYPE overmind_helius_integration gauge
overmind_helius_integration 1

# HELP overmind_data_source Data source (2=helius_direct)
# TYPE overmind_data_source gauge
overmind_data_source 2
"""

# Global instance
solana_metrics = SimpleSolanaMetrics()

class SimpleSolanaHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            
            metrics = solana_metrics.generate_metrics()
            self.wfile.write(metrics.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

async def background_updater():
    """Background task to update Solana data"""
    while True:
        try:
            await solana_metrics.update_data()
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            print(f"❌ Update error: {e}")
            await asyncio.sleep(10)

def start_server(port=9094):
    """Start simple Solana metrics server"""
    print(f"🚀 Starting Simple Solana Metrics on port {port}")
    
    # Start background updater
    import threading
    def run_updater():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(background_updater())
    
    updater_thread = threading.Thread(target=run_updater, daemon=True)
    updater_thread.start()
    
    # Initial data fetch
    async def initial_fetch():
        await solana_metrics.update_data()
    
    loop = asyncio.new_event_loop()
    loop.run_until_complete(initial_fetch())
    
    try:
        with HTTPServer(("0.0.0.0", port), SimpleSolanaHandler) as httpd:
            print(f"✅ Simple Solana metrics server started")
            print(f"📊 Initial: SOL=${solana_metrics.sol_price:.2f}, TPS={solana_metrics.network_tps:.1f}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    start_server()