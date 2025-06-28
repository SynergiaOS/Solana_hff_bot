#!/usr/bin/env python3
"""
Live Paper Trading System
14-day live paper trading with real-time monitoring for THE OVERMIND PROTOCOL
"""

import asyncio
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import signal
import sys

try:
    from .paper_trading_integration import PaperTradingIntegration
    from .performance_analytics import PerformanceAnalyzer
    from .benchmark_comparison import BenchmarkComparator
except ImportError:
    # Direct import for testing
    sys.path.insert(0, os.path.dirname(__file__))
    from paper_trading_integration import PaperTradingIntegration
    from performance_analytics import PerformanceAnalyzer
    from benchmark_comparison import BenchmarkComparator

logger = logging.getLogger(__name__)

@dataclass
class DailyReport:
    """Daily trading report"""
    date: str
    portfolio_value: float
    daily_pnl: float
    daily_pnl_pct: float
    total_pnl: float
    total_pnl_pct: float
    trades_today: int
    total_trades: int
    cash_balance: float
    positions: Dict[str, Any]
    signals_generated: int
    signals_executed: int

@dataclass
class LiveTradingSession:
    """Live trading session data"""
    session_id: str
    start_date: datetime
    end_date: Optional[datetime]
    initial_balance: float
    current_balance: float
    total_days: int
    completed_days: int
    daily_reports: List[DailyReport]
    status: str  # "running", "completed", "stopped"

class LivePaperTradingSystem:
    """
    Live Paper Trading System for 14-day validation
    """
    
    def __init__(self, initial_balance: float = 10000.0, session_duration_days: int = 14):
        self.initial_balance = initial_balance
        self.session_duration_days = session_duration_days
        
        # Components
        self.trading_integration = PaperTradingIntegration(initial_balance)
        self.performance_analyzer = PerformanceAnalyzer()
        self.benchmark_comparator = BenchmarkComparator()
        
        # Session tracking
        self.session: Optional[LiveTradingSession] = None
        self.running = False
        self.daily_reports: List[DailyReport] = []
        
        # Trading parameters
        self.trading_interval = 300  # 5 minutes between cycles
        self.daily_report_time = "23:59"  # Generate daily report at 11:59 PM
        
        # Data persistence
        self.data_dir = "live_trading_data"
        self.ensure_data_directory()
        
        logger.info("🚀 Live Paper Trading System initialized")
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    async def start_live_trading_session(self) -> str:
        """Start a new 14-day live trading session"""
        
        # Initialize trading integration
        success = await self.trading_integration.initialize()
        if not success:
            raise RuntimeError("Failed to initialize trading integration")
        
        # Create new session
        session_id = f"live_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_date = datetime.now()
        end_date = start_date + timedelta(days=self.session_duration_days)
        
        self.session = LiveTradingSession(
            session_id=session_id,
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.initial_balance,
            current_balance=self.initial_balance,
            total_days=self.session_duration_days,
            completed_days=0,
            daily_reports=[],
            status="running"
        )
        
        self.running = True
        
        logger.info(f"🎯 Started live trading session: {session_id}")
        logger.info(f"   Duration: {self.session_duration_days} days")
        logger.info(f"   Start: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   End: {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save session data
        self.save_session_data()
        
        return session_id
    
    async def run_live_trading_loop(self):
        """Main live trading loop"""
        
        if not self.session or not self.running:
            raise RuntimeError("No active trading session")
        
        logger.info("🔄 Starting live trading loop...")
        
        last_daily_report_date = None
        signals_today = 0
        executed_today = 0
        
        try:
            while self.running and datetime.now() < self.session.end_date:
                
                # Run trading cycle
                cycle_result = await self.trading_integration.run_trading_cycle()
                
                if cycle_result["status"] == "success":
                    signal = cycle_result.get("signal")
                    if signal:
                        signals_today += 1
                        if cycle_result.get("executed", False):
                            executed_today += 1
                            logger.info(f"🎯 Trade executed: {signal['action']} SOL")
                
                # Check if we need to generate daily report
                current_date = datetime.now().date()
                if last_daily_report_date != current_date:
                    if last_daily_report_date is not None:  # Skip first day
                        await self.generate_daily_report(signals_today, executed_today)
                        signals_today = 0
                        executed_today = 0
                    
                    last_daily_report_date = current_date
                
                # Update session data
                self.session.current_balance = cycle_result.get("portfolio_value", self.initial_balance)
                self.session.completed_days = (datetime.now() - self.session.start_date).days
                
                # Save session data periodically
                if len(self.daily_reports) % 5 == 0:  # Every 5 cycles
                    self.save_session_data()
                
                # Wait for next cycle
                await asyncio.sleep(self.trading_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Live trading interrupted by user")
            await self.stop_trading_session()
        except Exception as e:
            logger.error(f"❌ Error in live trading loop: {e}")
            await self.stop_trading_session()
    
    async def generate_daily_report(self, signals_generated: int, signals_executed: int):
        """Generate daily trading report"""
        
        try:
            # Get current portfolio status
            portfolio = self.trading_integration.paper_engine.get_portfolio_summary()
            metrics = self.trading_integration.paper_engine.get_performance_metrics()
            
            # Calculate daily P&L
            if self.daily_reports:
                prev_value = self.daily_reports[-1].portfolio_value
                daily_pnl = portfolio.total_value - prev_value
                daily_pnl_pct = (daily_pnl / prev_value) * 100
            else:
                daily_pnl = portfolio.total_value - self.initial_balance
                daily_pnl_pct = (daily_pnl / self.initial_balance) * 100
            
            # Create daily report
            report = DailyReport(
                date=datetime.now().strftime('%Y-%m-%d'),
                portfolio_value=portfolio.total_value,
                daily_pnl=daily_pnl,
                daily_pnl_pct=daily_pnl_pct,
                total_pnl=portfolio.total_pnl,
                total_pnl_pct=(portfolio.total_pnl / self.initial_balance) * 100,
                trades_today=signals_executed,
                total_trades=metrics["total_trades"],
                cash_balance=portfolio.cash_balance,
                positions={symbol: {"quantity": pos.quantity, "value": pos.quantity * pos.current_price} 
                          for symbol, pos in portfolio.positions.items()},
                signals_generated=signals_generated,
                signals_executed=signals_executed
            )
            
            self.daily_reports.append(report)
            
            logger.info(f"📊 Daily Report - Day {len(self.daily_reports)}")
            logger.info(f"   Portfolio Value: ${report.portfolio_value:,.2f}")
            logger.info(f"   Daily P&L: ${report.daily_pnl:,.2f} ({report.daily_pnl_pct:+.2f}%)")
            logger.info(f"   Total P&L: ${report.total_pnl:,.2f} ({report.total_pnl_pct:+.2f}%)")
            logger.info(f"   Trades Today: {report.trades_today}")
            logger.info(f"   Signals: {report.signals_generated} generated, {report.signals_executed} executed")
            
            # Save daily report
            self.save_daily_report(report)
            
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
    
    async def stop_trading_session(self):
        """Stop the current trading session"""
        
        if not self.session:
            return
        
        self.running = False
        self.session.status = "stopped"
        self.session.end_date = datetime.now()
        
        # Generate final report
        await self.generate_final_report()
        
        # Save final session data
        self.save_session_data()
        
        logger.info(f"🏁 Trading session stopped: {self.session.session_id}")
    
    async def generate_final_report(self):
        """Generate comprehensive final report"""
        
        if not self.session or not self.daily_reports:
            return
        
        logger.info("📋 Generating final trading report...")
        
        # Calculate session metrics
        final_balance = self.daily_reports[-1].portfolio_value
        total_return = final_balance - self.initial_balance
        total_return_pct = (total_return / self.initial_balance) * 100
        
        # Daily returns for analysis
        daily_returns = []
        for i in range(1, len(self.daily_reports)):
            prev_val = self.daily_reports[i-1].portfolio_value
            curr_val = self.daily_reports[i].portfolio_value
            daily_return = (curr_val - prev_val) / prev_val
            daily_returns.append(daily_return)
        
        # Performance metrics
        if len(daily_returns) > 1:
            import statistics
            volatility = statistics.stdev(daily_returns) * (252 ** 0.5)  # Annualized
            avg_daily_return = statistics.mean(daily_returns)
            sharpe_ratio = (avg_daily_return * 252 - 0.02) / volatility if volatility > 0 else 0
        else:
            volatility = 0
            sharpe_ratio = 0
        
        # Trading statistics
        total_signals = sum(r.signals_generated for r in self.daily_reports)
        total_executed = sum(r.signals_executed for r in self.daily_reports)
        execution_rate = (total_executed / total_signals) * 100 if total_signals > 0 else 0
        
        # Generate report
        report = f"""
🏁 LIVE PAPER TRADING - FINAL REPORT
{'='*60}

📊 SESSION SUMMARY
   Session ID: {self.session.session_id}
   Duration: {len(self.daily_reports)} days
   Start Date: {self.session.start_date.strftime('%Y-%m-%d')}
   End Date: {datetime.now().strftime('%Y-%m-%d')}

💰 PERFORMANCE SUMMARY
   Initial Balance: ${self.initial_balance:,.2f}
   Final Balance: ${final_balance:,.2f}
   Total Return: ${total_return:,.2f} ({total_return_pct:+.2f}%)
   Volatility: {volatility*100:.2f}%
   Sharpe Ratio: {sharpe_ratio:.2f}

📈 TRADING STATISTICS
   Total Signals Generated: {total_signals}
   Total Signals Executed: {total_executed}
   Execution Rate: {execution_rate:.1f}%
   Average Trades per Day: {total_executed / len(self.daily_reports):.1f}

📅 DAILY PERFORMANCE
"""
        
        for report_data in self.daily_reports:
            report += f"   {report_data.date}: ${report_data.portfolio_value:,.2f} ({report_data.daily_pnl_pct:+.2f}%) - {report_data.trades_today} trades\n"
        
        report += f"\n{'='*60}\n"
        
        # Save final report
        report_file = os.path.join(self.data_dir, f"{self.session.session_id}_final_report.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        logger.info(f"📋 Final report saved to: {report_file}")
    
    def save_session_data(self):
        """Save session data to file"""
        if not self.session:
            return
        
        session_file = os.path.join(self.data_dir, f"{self.session.session_id}.json")
        session_data = {
            "session": asdict(self.session),
            "daily_reports": [asdict(report) for report in self.daily_reports]
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)
    
    def save_daily_report(self, report: DailyReport):
        """Save individual daily report"""
        report_file = os.path.join(self.data_dir, f"{self.session.session_id}_day_{len(self.daily_reports)}.json")
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
    
    def load_session_data(self, session_id: str) -> bool:
        """Load existing session data"""
        session_file = os.path.join(self.data_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            return False
        
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            # Reconstruct session object
            session_data = data["session"]
            self.session = LiveTradingSession(**session_data)
            
            # Reconstruct daily reports
            self.daily_reports = [DailyReport(**report) for report in data["daily_reports"]]
            
            logger.info(f"📂 Loaded session data: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading session data: {e}")
            return False

# Demo function for quick testing
async def demo_live_trading(duration_minutes: int = 5):
    """Demo live trading for testing (short duration)"""
    print("🧪 Demo Live Paper Trading")
    print("=" * 50)
    
    try:
        # Initialize system
        system = LivePaperTradingSystem(initial_balance=1000.0, session_duration_days=1)
        system.trading_interval = 30  # 30 seconds for demo
        
        # Start session
        session_id = await system.start_live_trading_session()
        print(f"✅ Started demo session: {session_id}")
        
        # Run for specified duration
        print(f"🔄 Running for {duration_minutes} minutes...")
        
        # Override end date for demo
        system.session.end_date = datetime.now() + timedelta(minutes=duration_minutes)
        
        # Run trading loop
        await system.run_live_trading_loop()
        
        print("✅ Demo completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_live_trading(duration_minutes=2))
