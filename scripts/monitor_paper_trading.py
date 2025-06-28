#!/usr/bin/env python3
"""
Monitor Paper Trading Session
Monitor and analyze ongoing paper trading sessions
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add brain module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'brain', 'src'))

class PaperTradingMonitor:
    """Monitor paper trading sessions"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'brain', 'src', 'live_trading_data')
    
    def list_sessions(self) -> List[str]:
        """List all available trading sessions"""
        if not os.path.exists(self.data_dir):
            return []
        
        sessions = []
        for file in os.listdir(self.data_dir):
            if file.endswith('.json') and not file.endswith('_final_report.txt'):
                if '_day_' not in file:  # Skip daily report files
                    sessions.append(file.replace('.json', ''))
        
        return sorted(sessions)
    
    def load_session_data(self, session_id: str) -> Dict[str, Any]:
        """Load session data"""
        session_file = os.path.join(self.data_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            raise FileNotFoundError(f"Session {session_id} not found")
        
        with open(session_file, 'r') as f:
            return json.load(f)
    
    def display_session_summary(self, session_id: str):
        """Display session summary"""
        try:
            data = self.load_session_data(session_id)
            session = data['session']
            daily_reports = data['daily_reports']
            
            print(f"📊 SESSION SUMMARY: {session_id}")
            print("=" * 60)
            
            # Basic info
            print(f"Start Date: {session['start_date']}")
            print(f"Status: {session['status']}")
            print(f"Duration: {session['completed_days']}/{session['total_days']} days")
            print(f"Initial Balance: ${session['initial_balance']:,.2f}")
            print(f"Current Balance: ${session['current_balance']:,.2f}")
            
            if daily_reports:
                latest = daily_reports[-1]
                total_return = latest['total_pnl']
                total_return_pct = latest['total_pnl_pct']
                
                print(f"Total Return: ${total_return:,.2f} ({total_return_pct:+.2f}%)")
                print(f"Total Trades: {latest['total_trades']}")
                
                # Daily performance
                print(f"\n📅 DAILY PERFORMANCE:")
                print("-" * 40)
                for report in daily_reports[-7:]:  # Last 7 days
                    print(f"{report['date']}: ${report['portfolio_value']:,.2f} "
                          f"({report['daily_pnl_pct']:+.2f}%) - {report['trades_today']} trades")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error loading session: {e}")
    
    def display_performance_chart(self, session_id: str):
        """Display simple ASCII performance chart"""
        try:
            data = self.load_session_data(session_id)
            daily_reports = data['daily_reports']
            
            if not daily_reports:
                print("No daily reports available")
                return
            
            print(f"📈 PERFORMANCE CHART: {session_id}")
            print("-" * 60)
            
            # Get portfolio values
            values = [report['portfolio_value'] for report in daily_reports]
            dates = [report['date'] for report in daily_reports]
            
            # Simple ASCII chart
            min_val = min(values)
            max_val = max(values)
            range_val = max_val - min_val if max_val > min_val else 1
            
            chart_height = 10
            
            for i in range(chart_height, -1, -1):
                line = ""
                threshold = min_val + (range_val * i / chart_height)
                
                for value in values:
                    if value >= threshold:
                        line += "█"
                    else:
                        line += " "
                
                print(f"{threshold:8.0f} |{line}")
            
            # X-axis
            print("         " + "-" * len(values))
            print("         " + "".join([str(i % 10) for i in range(len(values))]))
            
            print(f"\nRange: ${min_val:,.0f} - ${max_val:,.0f}")
            
        except Exception as e:
            print(f"❌ Error generating chart: {e}")
    
    def display_trading_stats(self, session_id: str):
        """Display detailed trading statistics"""
        try:
            data = self.load_session_data(session_id)
            daily_reports = data['daily_reports']
            
            if not daily_reports:
                print("No trading data available")
                return
            
            print(f"📊 TRADING STATISTICS: {session_id}")
            print("-" * 60)
            
            # Aggregate statistics
            total_signals = sum(report['signals_generated'] for report in daily_reports)
            total_executed = sum(report['signals_executed'] for report in daily_reports)
            total_trades = daily_reports[-1]['total_trades'] if daily_reports else 0
            
            execution_rate = (total_executed / total_signals * 100) if total_signals > 0 else 0
            avg_trades_per_day = total_executed / len(daily_reports) if daily_reports else 0
            
            print(f"Total Signals Generated: {total_signals}")
            print(f"Total Signals Executed: {total_executed}")
            print(f"Execution Rate: {execution_rate:.1f}%")
            print(f"Average Trades per Day: {avg_trades_per_day:.1f}")
            print(f"Total Completed Trades: {total_trades}")
            
            # Daily breakdown
            print(f"\n📅 DAILY BREAKDOWN:")
            print("-" * 40)
            print("Date       | Signals | Executed | P&L")
            print("-" * 40)
            
            for report in daily_reports:
                print(f"{report['date']} |    {report['signals_generated']:2d}   |    {report['signals_executed']:2d}    | {report['daily_pnl_pct']:+6.2f}%")
            
        except Exception as e:
            print(f"❌ Error loading trading stats: {e}")

def main():
    """Main monitoring interface"""
    monitor = PaperTradingMonitor()
    
    if len(sys.argv) < 2:
        # List available sessions
        sessions = monitor.list_sessions()
        
        if not sessions:
            print("❌ No trading sessions found")
            print("Start a session with: python scripts/start_14day_paper_trading.py")
            return
        
        print("📊 Available Trading Sessions:")
        print("-" * 40)
        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session}")
        
        print("\nUsage:")
        print("  python scripts/monitor_paper_trading.py <session_id>")
        print("  python scripts/monitor_paper_trading.py <session_id> chart")
        print("  python scripts/monitor_paper_trading.py <session_id> stats")
        return
    
    session_id = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "summary"
    
    try:
        if command == "chart":
            monitor.display_performance_chart(session_id)
        elif command == "stats":
            monitor.display_trading_stats(session_id)
        else:
            monitor.display_session_summary(session_id)
    
    except FileNotFoundError:
        print(f"❌ Session '{session_id}' not found")
        print("\nAvailable sessions:")
        sessions = monitor.list_sessions()
        for session in sessions:
            print(f"  - {session}")

if __name__ == "__main__":
    main()
