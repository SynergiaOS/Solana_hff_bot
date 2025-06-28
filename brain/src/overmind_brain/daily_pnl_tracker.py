#!/usr/bin/env python3
"""
Daily P&L Tracker
Comprehensive daily profit and loss tracking with automated reporting
"""

import asyncio
import logging
import json
import os
import csv
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import statistics
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

@dataclass
class DailyPnLRecord:
    """Daily P&L record"""
    date: str
    opening_balance: float
    closing_balance: float
    daily_pnl: float
    daily_pnl_pct: float
    total_pnl: float
    total_pnl_pct: float
    trades_count: int
    winning_trades: int
    losing_trades: int
    largest_win: float
    largest_loss: float
    total_fees: float
    sharpe_ratio_daily: float
    max_drawdown: float
    positions_held: Dict[str, Any]
    notes: str

@dataclass
class WeeklyPnLSummary:
    """Weekly P&L summary"""
    week_start: str
    week_end: str
    weekly_pnl: float
    weekly_pnl_pct: float
    best_day: str
    worst_day: str
    avg_daily_pnl: float
    volatility: float
    win_rate: float
    total_trades: int

class DailyPnLTracker:
    """
    Daily P&L Tracking System for THE OVERMIND PROTOCOL
    
    Features:
    - Automated daily P&L calculation
    - Historical tracking and analysis
    - Performance metrics calculation
    - Automated reporting (email, CSV, JSON)
    - Risk alerts and notifications
    """
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.data_dir = "pnl_tracking_data"
        self.ensure_data_directory()
        
        # Tracking data
        self.daily_records: List[DailyPnLRecord] = []
        self.current_balance = initial_balance
        
        # Alert thresholds
        self.daily_loss_alert = 0.05  # 5% daily loss alert
        self.weekly_loss_alert = 0.10  # 10% weekly loss alert
        self.drawdown_alert = 0.15  # 15% drawdown alert
        
        # Reporting settings
        self.auto_report_time = time(23, 30)  # 11:30 PM daily report
        self.weekly_report_day = 6  # Sunday (0=Monday, 6=Sunday)
        
        logger.info("📊 Daily P&L Tracker initialized")
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def calculate_daily_pnl(self, 
                           opening_balance: float,
                           closing_balance: float,
                           trades_data: List[Dict[str, Any]],
                           positions: Dict[str, Any]) -> DailyPnLRecord:
        """Calculate comprehensive daily P&L"""
        
        # Basic P&L calculations
        daily_pnl = closing_balance - opening_balance
        daily_pnl_pct = (daily_pnl / opening_balance) * 100
        total_pnl = closing_balance - self.initial_balance
        total_pnl_pct = (total_pnl / self.initial_balance) * 100
        
        # Trade analysis
        trades_count = len(trades_data)
        winning_trades = len([t for t in trades_data if t.get('pnl', 0) > 0])
        losing_trades = len([t for t in trades_data if t.get('pnl', 0) < 0])
        
        trade_pnls = [t.get('pnl', 0) for t in trades_data]
        largest_win = max(trade_pnls) if trade_pnls else 0
        largest_loss = min(trade_pnls) if trade_pnls else 0
        
        # Fees calculation
        total_fees = sum(t.get('fees', 0) for t in trades_data)
        
        # Risk metrics
        daily_returns = [r.daily_pnl_pct for r in self.daily_records[-30:]]  # Last 30 days
        if len(daily_returns) > 1:
            sharpe_ratio_daily = self._calculate_sharpe_ratio(daily_returns)
        else:
            sharpe_ratio_daily = 0.0
        
        max_drawdown = self._calculate_max_drawdown()
        
        return DailyPnLRecord(
            date=datetime.now().strftime('%Y-%m-%d'),
            opening_balance=opening_balance,
            closing_balance=closing_balance,
            daily_pnl=daily_pnl,
            daily_pnl_pct=daily_pnl_pct,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            trades_count=trades_count,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            largest_win=largest_win,
            largest_loss=largest_loss,
            total_fees=total_fees,
            sharpe_ratio_daily=sharpe_ratio_daily,
            max_drawdown=max_drawdown,
            positions_held=positions,
            notes=""
        )
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio from daily returns"""
        if len(returns) < 2:
            return 0.0
        
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        if std_return == 0:
            return 0.0
        
        # Annualized Sharpe ratio (assuming 252 trading days)
        risk_free_rate = 0.02 / 252  # 2% annual risk-free rate
        return (avg_return - risk_free_rate) / std_return * (252 ** 0.5)
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from historical data"""
        if not self.daily_records:
            return 0.0
        
        peak = self.initial_balance
        max_drawdown = 0.0
        
        for record in self.daily_records:
            if record.closing_balance > peak:
                peak = record.closing_balance
            
            drawdown = (peak - record.closing_balance) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def add_daily_record(self, record: DailyPnLRecord):
        """Add daily record and save to file"""
        self.daily_records.append(record)
        self.current_balance = record.closing_balance
        
        # Save to CSV
        self._save_to_csv(record)
        
        # Save to JSON
        self._save_to_json()
        
        # Check for alerts
        self._check_alerts(record)
        
        logger.info(f"📊 Daily P&L recorded: {record.daily_pnl:+.2f} ({record.daily_pnl_pct:+.2f}%)")
    
    def _save_to_csv(self, record: DailyPnLRecord):
        """Save record to CSV file"""
        csv_file = os.path.join(self.data_dir, "daily_pnl.csv")
        
        # Check if file exists to write header
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                # Write header
                writer.writerow([
                    'Date', 'Opening Balance', 'Closing Balance', 'Daily P&L', 'Daily P&L %',
                    'Total P&L', 'Total P&L %', 'Trades Count', 'Winning Trades', 'Losing Trades',
                    'Largest Win', 'Largest Loss', 'Total Fees', 'Sharpe Ratio', 'Max Drawdown'
                ])
            
            # Write data
            writer.writerow([
                record.date, record.opening_balance, record.closing_balance,
                record.daily_pnl, record.daily_pnl_pct, record.total_pnl, record.total_pnl_pct,
                record.trades_count, record.winning_trades, record.losing_trades,
                record.largest_win, record.largest_loss, record.total_fees,
                record.sharpe_ratio_daily, record.max_drawdown
            ])
    
    def _save_to_json(self):
        """Save all records to JSON file"""
        json_file = os.path.join(self.data_dir, "daily_pnl.json")
        
        data = {
            "initial_balance": self.initial_balance,
            "current_balance": self.current_balance,
            "records": [asdict(record) for record in self.daily_records],
            "last_updated": datetime.now().isoformat()
        }
        
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _check_alerts(self, record: DailyPnLRecord):
        """Check for risk alerts and send notifications"""
        alerts = []
        
        # Daily loss alert
        if record.daily_pnl_pct <= -self.daily_loss_alert * 100:
            alerts.append(f"🚨 DAILY LOSS ALERT: {record.daily_pnl_pct:.2f}% loss today")
        
        # Drawdown alert
        if record.max_drawdown >= self.drawdown_alert:
            alerts.append(f"🚨 DRAWDOWN ALERT: {record.max_drawdown*100:.2f}% maximum drawdown")
        
        # Weekly loss check
        if len(self.daily_records) >= 7:
            weekly_pnl = sum(r.daily_pnl for r in self.daily_records[-7:])
            weekly_pnl_pct = (weekly_pnl / self.daily_records[-7].opening_balance) * 100
            
            if weekly_pnl_pct <= -self.weekly_loss_alert * 100:
                alerts.append(f"🚨 WEEKLY LOSS ALERT: {weekly_pnl_pct:.2f}% loss this week")
        
        # Send alerts if any
        if alerts:
            self._send_alerts(alerts, record)
    
    def _send_alerts(self, alerts: List[str], record: DailyPnLRecord):
        """Send risk alerts"""
        alert_message = f"""
🚨 RISK ALERT - THE OVERMIND PROTOCOL
Date: {record.date}

ALERTS:
{chr(10).join(alerts)}

Current Status:
- Portfolio Value: ${record.closing_balance:,.2f}
- Daily P&L: ${record.daily_pnl:+,.2f} ({record.daily_pnl_pct:+.2f}%)
- Total P&L: ${record.total_pnl:+,.2f} ({record.total_pnl_pct:+.2f}%)
- Max Drawdown: {record.max_drawdown*100:.2f}%

Immediate action may be required.
"""
        
        logger.warning(alert_message)
        
        # Save alert to file
        alert_file = os.path.join(self.data_dir, f"alert_{record.date}.txt")
        with open(alert_file, 'w') as f:
            f.write(alert_message)
    
    def generate_daily_report(self, record: DailyPnLRecord) -> str:
        """Generate comprehensive daily report"""
        
        # Calculate additional metrics
        if len(self.daily_records) > 1:
            prev_record = self.daily_records[-2]
            balance_change = record.closing_balance - prev_record.closing_balance
        else:
            balance_change = record.daily_pnl
        
        win_rate = (record.winning_trades / record.trades_count * 100) if record.trades_count > 0 else 0
        
        report = f"""
📊 DAILY P&L REPORT - THE OVERMIND PROTOCOL
Date: {record.date}
{'='*60}

💰 PERFORMANCE SUMMARY
   Opening Balance: ${record.opening_balance:,.2f}
   Closing Balance: ${record.closing_balance:,.2f}
   Daily P&L: ${record.daily_pnl:+,.2f} ({record.daily_pnl_pct:+.2f}%)
   Total P&L: ${record.total_pnl:+,.2f} ({record.total_pnl_pct:+.2f}%)

📈 TRADING ACTIVITY
   Total Trades: {record.trades_count}
   Winning Trades: {record.winning_trades}
   Losing Trades: {record.losing_trades}
   Win Rate: {win_rate:.1f}%
   Largest Win: ${record.largest_win:+,.2f}
   Largest Loss: ${record.largest_loss:+,.2f}
   Total Fees: ${record.total_fees:,.2f}

🛡️ RISK METRICS
   Sharpe Ratio (30d): {record.sharpe_ratio_daily:.2f}
   Max Drawdown: {record.max_drawdown*100:.2f}%
   
📋 POSITIONS HELD
{json.dumps(record.positions_held, indent=2) if record.positions_held else "   No positions"}

{'='*60}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def save_daily_report(self, record: DailyPnLRecord):
        """Save daily report to file"""
        report = self.generate_daily_report(record)
        
        report_file = os.path.join(self.data_dir, f"daily_report_{record.date}.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"📋 Daily report saved: {report_file}")
        return report
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary for specified period"""
        if not self.daily_records:
            return {}
        
        recent_records = self.daily_records[-days:] if len(self.daily_records) >= days else self.daily_records
        
        if not recent_records:
            return {}
        
        # Calculate metrics
        total_pnl = sum(r.daily_pnl for r in recent_records)
        daily_returns = [r.daily_pnl_pct for r in recent_records]
        
        return {
            "period_days": len(recent_records),
            "total_pnl": total_pnl,
            "avg_daily_pnl": total_pnl / len(recent_records),
            "best_day": max(daily_returns),
            "worst_day": min(daily_returns),
            "volatility": statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0,
            "win_rate": len([r for r in daily_returns if r > 0]) / len(daily_returns) * 100,
            "sharpe_ratio": self._calculate_sharpe_ratio(daily_returns),
            "max_drawdown": max(r.max_drawdown for r in recent_records),
            "total_trades": sum(r.trades_count for r in recent_records)
        }

# Test function
def test_daily_pnl_tracker():
    """Test the daily P&L tracker"""
    print("🧪 Testing Daily P&L Tracker")
    print("-" * 40)
    
    # Initialize tracker
    tracker = DailyPnLTracker(initial_balance=10000.0)
    
    # Simulate some daily records
    for i in range(5):
        opening = 10000 + i * 100
        closing = opening + ((-1) ** i) * 50  # Alternating gains/losses
        
        # Mock trades data
        trades_data = [
            {"pnl": 25, "fees": 2.5},
            {"pnl": -15, "fees": 1.5}
        ] if i % 2 == 0 else [{"pnl": -30, "fees": 3.0}]
        
        # Mock positions
        positions = {"SOL": {"quantity": 1.5, "value": 150}} if i % 3 == 0 else {}
        
        # Calculate daily record
        record = tracker.calculate_daily_pnl(opening, closing, trades_data, positions)
        record.date = f"2025-06-{27+i:02d}"  # Mock dates
        
        # Add record
        tracker.add_daily_record(record)
        
        print(f"Day {i+1}: ${record.daily_pnl:+.2f} ({record.daily_pnl_pct:+.2f}%)")
    
    # Generate summary
    summary = tracker.get_performance_summary(5)
    print(f"\n📊 5-Day Summary:")
    print(f"   Total P&L: ${summary['total_pnl']:+.2f}")
    print(f"   Avg Daily P&L: ${summary['avg_daily_pnl']:+.2f}")
    print(f"   Win Rate: {summary['win_rate']:.1f}%")
    print(f"   Volatility: {summary['volatility']:.2f}%")
    
    # Generate daily report for last day
    last_record = tracker.daily_records[-1]
    report = tracker.generate_daily_report(last_record)
    print(f"\n📋 Sample Daily Report:")
    print(report[:500] + "..." if len(report) > 500 else report)
    
    return True

if __name__ == "__main__":
    test_daily_pnl_tracker()
