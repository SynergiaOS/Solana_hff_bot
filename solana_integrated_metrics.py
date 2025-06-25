#!/usr/bin/env python3
"""
OVERMIND PROTOCOL - Solana Integrated Metrics Server
Real-time metrics with LIVE Solana blockchain data from Helius API
"""

import asyncio
import time
import sys
import os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Add brain modules
sys.path.insert(0, os.path.join(os.getcwd(), 'brain/src'))

class SolanaIntegratedMetrics:
    def __init__(self):
        self.start_time = datetime.now()
        
        # Trading metrics (real when available)
        self.metrics_data = {
            'signals_processed': 0,
            'strategies_qualified': 0,
            'buy_decisions': 0,
            'sell_decisions': 0,
            'hold_decisions': 0,
            'take_profit_exits': 0,
            'stop_loss_exits': 0,
            'time_based_exits': 0,
            'risk_management_exits': 0,
            'total_pnl': 0.0,
            'active_positions': 0,
            'win_count': 0,
            'loss_count': 0
        }
        
        # Solana real-time data
        self.solana_data = {
            'sol_price': 0.0,
            'network_tps': 0.0,
            'total_transactions': 0,
            'new_tokens_detected': 0,
            'volume_24h': 0.0,
            'last_update': datetime.now()
        }
        
        # Try to initialize components
        self.brain_available = False
        self.solana_available = False
        
        self._init_brain_components()
        self._init_solana_collector()
        
    def _init_brain_components(self):
        """Initialize OVERMIND Brain components"""
        try:
            from overmind_brain.strategy_manager import StrategyManager
            from overmind_brain.exit_strategy_manager import ExitStrategyManager
            
            self.strategy_manager = StrategyManager()
            self.exit_manager = ExitStrategyManager()
            self.brain_available = True
            
            print("✅ OVERMIND Brain components loaded")
            
        except Exception as e:
            print(f"⚠️ OVERMIND Brain not available: {e}")
    
    def _init_solana_collector(self):
        """Initialize Solana data collector"""
        try:
            from solana_realtime_collector import solana_collector
            self.solana_collector = solana_collector
            self.solana_available = True
            
            print("✅ Solana real-time collector loaded")
            
        except Exception as e:
            print(f"⚠️ Solana collector not available: {e}")
    
    async def update_solana_data(self):
        """Update Solana blockchain data"""
        if not self.solana_available:
            return
        
        try:
            # Get fresh data from Solana collector
            summary = self.solana_collector.get_market_summary()
            
            self.solana_data.update({
                'sol_price': summary.get('sol_price_usd', 0.0),
                'network_tps': summary.get('network_tps', 0.0),
                'total_transactions': summary.get('total_transactions', 0),
                'new_tokens_detected': summary.get('new_tokens_detected', 0),
                'volume_24h': summary.get('sol_volume_24h_usd', 0.0),
                'last_update': datetime.now()
            })
            
            print(f"📊 Solana data updated: SOL=${self.solana_data['sol_price']:.2f}, TPS={self.solana_data['network_tps']:.1f}")
            
        except Exception as e:
            print(f"❌ Error updating Solana data: {e}")
    
    def get_brain_data(self):
        """Get real data from OVERMIND Brain"""
        if not self.brain_available:
            return {'active_strategies': 1, 'active_positions': 0, 'total_pnl': 0.0}
        
        try:
            config = self.strategy_manager.get_strategy_summary()
            positions = self.exit_manager.get_position_summary()
            
            return {
                'active_strategies': len(config.get("enabled_strategies", [])),
                'active_positions': positions.get("total_positions", 0),
                'total_pnl': positions.get("total_unrealized_pnl", 0.0),
                'enabled_strategies': config.get("enabled_strategies", [])
            }
            
        except Exception as e:
            print(f"❌ Error getting brain data: {e}")
            return {'active_strategies': 1, 'active_positions': 0, 'total_pnl': 0.0}
    
    def generate_prometheus_metrics(self):
        """Generate Prometheus metrics with REAL Solana data"""
        
        # Calculate validation time
        validation_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        # Get real brain data
        brain_data = self.get_brain_data()
        
        # Calculate performance metrics
        total_trades = self.metrics_data['win_count'] + self.metrics_data['loss_count']
        win_rate = self.metrics_data['win_count'] / total_trades if total_trades > 0 else 0.0
        
        # Solana data freshness
        data_age = (datetime.now() - self.solana_data['last_update']).total_seconds()
        
        metrics = f"""# HELP overmind_brain_status AI Brain operational status
# TYPE overmind_brain_status gauge
overmind_brain_status {1 if self.brain_available else 0}

# HELP overmind_solana_connection Solana blockchain connection status
# TYPE overmind_solana_connection gauge
overmind_solana_connection {1 if self.solana_available else 0}

# HELP overmind_validation_hours Hours of mainnet validation completed
# TYPE overmind_validation_hours gauge
overmind_validation_hours {validation_hours:.2f}

# HELP overmind_active_strategies Number of active trading strategies
# TYPE overmind_active_strategies gauge
overmind_active_strategies {brain_data['active_strategies']}

# HELP overmind_active_positions Number of currently active positions
# TYPE overmind_active_positions gauge
overmind_active_positions {brain_data['active_positions']}

# HELP overmind_total_pnl Total unrealized P&L in USD
# TYPE overmind_total_pnl gauge
overmind_total_pnl {brain_data['total_pnl']:.2f}

# HELP overmind_win_rate Current win rate percentage
# TYPE overmind_win_rate gauge
overmind_win_rate {win_rate:.3f}

# HELP solana_price_usd Current SOL price in USD (LIVE DATA)
# TYPE solana_price_usd gauge
solana_price_usd {self.solana_data['sol_price']:.2f}

# HELP solana_network_tps Current Solana network TPS (LIVE DATA)
# TYPE solana_network_tps gauge
solana_network_tps {self.solana_data['network_tps']:.2f}

# HELP solana_total_transactions Recent transaction count (LIVE DATA)
# TYPE solana_total_transactions gauge
solana_total_transactions {self.solana_data['total_transactions']}

# HELP solana_new_tokens_detected New tokens detected in recent period
# TYPE solana_new_tokens_detected gauge
solana_new_tokens_detected {self.solana_data['new_tokens_detected']}

# HELP solana_volume_24h_usd Estimated 24h volume in USD
# TYPE solana_volume_24h_usd gauge
solana_volume_24h_usd {self.solana_data['volume_24h']:.2f}

# HELP solana_data_age_seconds Age of Solana data in seconds
# TYPE solana_data_age_seconds gauge
solana_data_age_seconds {data_age:.1f}

# HELP overmind_signals_processed_total Total market signals processed
# TYPE overmind_signals_processed_total counter
overmind_signals_processed_total {self.metrics_data['signals_processed']}

# HELP overmind_strategies_qualified_total Total strategies qualified
# TYPE overmind_strategies_qualified_total counter
overmind_strategies_qualified_total {self.metrics_data['strategies_qualified']}

# HELP overmind_trading_decisions_total Trading decisions by action
# TYPE overmind_trading_decisions_total counter
overmind_trading_decisions_total{{action="BUY"}} {self.metrics_data['buy_decisions']}
overmind_trading_decisions_total{{action="SELL"}} {self.metrics_data['sell_decisions']}
overmind_trading_decisions_total{{action="HOLD"}} {self.metrics_data['hold_decisions']}

# HELP overmind_exit_triggers_total Exit triggers by type (v2.0)
# TYPE overmind_exit_triggers_total counter
overmind_exit_triggers_total{{exit_type="take_profit"}} {self.metrics_data['take_profit_exits']}
overmind_exit_triggers_total{{exit_type="stop_loss"}} {self.metrics_data['stop_loss_exits']}
overmind_exit_triggers_total{{exit_type="time_based"}} {self.metrics_data['time_based_exits']}
overmind_exit_triggers_total{{exit_type="risk_management"}} {self.metrics_data['risk_management_exits']}

# HELP overmind_paper_trading_mode Paper trading mode (1=paper, 0=live)
# TYPE overmind_paper_trading_mode gauge
overmind_paper_trading_mode 1

# HELP overmind_data_source Data source type (1=real+solana, 0=simulated)
# TYPE overmind_data_source gauge
overmind_data_source {1 if (self.brain_available and self.solana_available) else 0}
"""
        
        return metrics

# Global metrics instance
integrated_metrics = SolanaIntegratedMetrics()

class SolanaMetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            
            metrics = integrated_metrics.generate_prometheus_metrics()
            self.wfile.write(metrics.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

async def update_solana_data_loop():
    """Background task to update Solana data"""
    while True:
        try:
            await integrated_metrics.update_solana_data()
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            print(f"❌ Solana update error: {e}")
            await asyncio.sleep(10)

def start_solana_metrics_server(port=9093):
    """Start integrated metrics server with Solana data"""
    print(f"🌐 Starting OVERMIND + Solana integrated metrics server on port {port}")
    print(f"🔗 Endpoint: http://localhost:{port}/metrics")
    print(f"📊 Brain: {'✅' if integrated_metrics.brain_available else '❌'}")
    print(f"🌐 Solana: {'✅' if integrated_metrics.solana_available else '❌'}")
    
    # Start background Solana data updates
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    def run_async_loop():
        loop.run_until_complete(update_solana_data_loop())
    
    bg_thread = threading.Thread(target=run_async_loop, daemon=True)
    bg_thread.start()
    
    try:
        with HTTPServer(("0.0.0.0", port), SolanaMetricsHandler) as httpd:
            print(f"✅ OVERMIND + Solana metrics server started successfully")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Solana metrics server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9093
    start_solana_metrics_server(port)