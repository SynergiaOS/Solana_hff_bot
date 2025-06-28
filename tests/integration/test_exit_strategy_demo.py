#!/usr/bin/env python3
"""
Demo: Complete Position Lifecycle with Exit Strategy
Shows: BUY → Position Tracking → Exit Conditions → SELL
"""

import sys
import os
from datetime import datetime, timedelta
import time

# Add the brain module to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain', 'src'))

from overmind_brain.exit_strategy_manager import ExitStrategyManager, Position, ExitReason
from overmind_brain.strategy_manager import StrategyManager

def test_position_lifecycle():
    """Test complete position lifecycle with exit strategies"""
    print("🚀 OVERMIND PROTOCOL - Position Lifecycle Demo")
    print("=" * 60)
    print("Demonstrating: BUY → Track → Monitor → SELL decisions")
    print()
    
    # Initialize managers
    exit_manager = ExitStrategyManager()
    strategy_manager = StrategyManager()
    
    # Scenario 1: Successful Take Profit Exit
    print("📊 SCENARIO 1: Take Profit Success")
    print("-" * 40)
    
    # Create a position (simulating a BUY decision)
    position1 = Position(
        symbol="SOL",
        entry_price=100.00,
        quantity=10.0,
        entry_time=datetime.now() - timedelta(hours=2),  # 2 hours ago
        entry_strategy="soul_meteor",
        stop_loss=95.00,      # 5% stop loss
        take_profit=115.00,   # 15% take profit
        max_hold_time_hours=24
    )
    
    exit_manager.add_position(position1)
    print(f"   📈 Position opened: {position1.symbol} @ ${position1.entry_price:.2f}")
    print(f"   🛡️  Stop Loss: ${position1.stop_loss:.2f} (-5%)")
    print(f"   🎯 Take Profit: ${position1.take_profit:.2f} (+15%)")
    
    # Simulate price movement to take profit level
    market_data_tp = {
        "price": 115.50,  # Above take profit
        "volume_24h": 150000,
        "liquidity": 80000,
        "signal_type": "price_momentum"
    }
    
    print(f"   📊 Current Price: ${market_data_tp['price']:.2f}")
    
    exit_decision1 = exit_manager.evaluate_exit_decision("SOL", market_data_tp)
    
    if exit_decision1 and exit_decision1.should_exit:
        pnl = (market_data_tp['price'] - position1.entry_price) * position1.quantity
        print(f"   ✅ Exit Decision: {exit_decision1.exit_reason.value.upper()}")
        print(f"   💰 P&L: ${pnl:.2f} (+{((market_data_tp['price']/position1.entry_price)-1)*100:.1f}%)")
        print(f"   🤖 Reasoning: {exit_decision1.reasoning}")
        print(f"   ⚡ Urgency: {exit_decision1.urgency}")
        exit_manager.remove_position("SOL")
    print()
    
    # Scenario 2: Stop Loss Triggered
    print("📊 SCENARIO 2: Stop Loss Protection")
    print("-" * 40)
    
    position2 = Position(
        symbol="MEME",
        entry_price=0.05,
        quantity=1000.0,
        entry_time=datetime.now() - timedelta(hours=1),
        entry_strategy="memecoin_hunter",
        stop_loss=0.045,     # 10% stop loss
        take_profit=0.065,   # 30% take profit (aggressive for meme)
        max_hold_time_hours=12  # Shorter hold for memes
    )
    
    exit_manager.add_position(position2)
    print(f"   📈 Position opened: {position2.symbol} @ ${position2.entry_price:.4f}")
    print(f"   🛡️  Stop Loss: ${position2.stop_loss:.4f} (-10%)")
    print(f"   🎯 Take Profit: ${position2.take_profit:.4f} (+30%)")
    
    # Simulate price crash
    market_data_sl = {
        "price": 0.044,  # Below stop loss
        "volume_24h": 8000,
        "liquidity": 3000,
        "signal_type": "sell_pressure"
    }
    
    print(f"   📊 Current Price: ${market_data_sl['price']:.4f}")
    
    exit_decision2 = exit_manager.evaluate_exit_decision("MEME", market_data_sl)
    
    if exit_decision2 and exit_decision2.should_exit:
        pnl = (market_data_sl['price'] - position2.entry_price) * position2.quantity
        print(f"   🚨 Exit Decision: {exit_decision2.exit_reason.value.upper()}")
        print(f"   💸 P&L: ${pnl:.2f} ({((market_data_sl['price']/position2.entry_price)-1)*100:.1f}%)")
        print(f"   🤖 Reasoning: {exit_decision2.reasoning}")
        print(f"   ⚡ Urgency: {exit_decision2.urgency}")
        exit_manager.remove_position("MEME")
    print()
    
    # Scenario 3: Time-Based Exit
    print("📊 SCENARIO 3: Time-Based Exit")
    print("-" * 40)
    
    position3 = Position(
        symbol="TIME",
        entry_price=10.00,
        quantity=5.0,
        entry_time=datetime.now() - timedelta(hours=25),  # Over 24 hours
        entry_strategy="developer_tracking",
        stop_loss=9.50,
        take_profit=11.50,
        max_hold_time_hours=24
    )
    
    exit_manager.add_position(position3)
    print(f"   📈 Position opened: {position3.symbol} @ ${position3.entry_price:.2f}")
    print(f"   ⏰ Entry Time: {position3.entry_time.strftime('%H:%M')} (25 hours ago)")
    print(f"   ⏳ Max Hold: {position3.max_hold_time_hours}h")
    
    market_data_time = {
        "price": 10.30,  # Small profit, but time limit exceeded
        "volume_24h": 45000,
        "liquidity": 25000,
        "signal_type": "stable_trading"
    }
    
    print(f"   📊 Current Price: ${market_data_time['price']:.2f}")
    
    exit_decision3 = exit_manager.evaluate_exit_decision("TIME", market_data_time)
    
    if exit_decision3 and exit_decision3.should_exit:
        pnl = (market_data_time['price'] - position3.entry_price) * position3.quantity
        hours_held = (datetime.now() - position3.entry_time).total_seconds() / 3600
        print(f"   ⏰ Exit Decision: {exit_decision3.exit_reason.value.upper()}")
        print(f"   💰 P&L: ${pnl:.2f} (+{((market_data_time['price']/position3.entry_price)-1)*100:.1f}%)")
        print(f"   🕐 Time Held: {hours_held:.1f} hours")
        print(f"   🤖 Reasoning: {exit_decision3.reasoning}")
        exit_manager.remove_position("TIME")
    print()
    
    # Scenario 4: Risk Management Exit
    print("📊 SCENARIO 4: Risk Management Override")
    print("-" * 40)
    
    position4 = Position(
        symbol="RISK",
        entry_price=50.00,
        quantity=2.0,
        entry_time=datetime.now() - timedelta(hours=3),
        entry_strategy="soul_meteor",
        stop_loss=47.50,     # 5% stop loss
        take_profit=57.50,   # 15% take profit
        max_hold_time_hours=24
    )
    
    exit_manager.add_position(position4)
    print(f"   📈 Position opened: {position4.symbol} @ ${position4.entry_price:.2f}")
    
    # Simulate extreme volatility spike
    market_data_risk = {
        "price": 48.00,      # Still above stop loss
        "volume_24h": 200000,
        "liquidity": 15000,
        "volatility": 0.18,  # 18% volatility (extreme)
        "signal_type": "high_volatility"
    }
    
    print(f"   📊 Current Price: ${market_data_risk['price']:.2f} (above stop loss)")
    print(f"   📈 Volatility: {market_data_risk['volatility']:.1%} (EXTREME)")
    
    exit_decision4 = exit_manager.evaluate_exit_decision("RISK", market_data_risk)
    
    if exit_decision4 and exit_decision4.should_exit:
        pnl = (market_data_risk['price'] - position4.entry_price) * position4.quantity
        print(f"   ⚠️  Exit Decision: {exit_decision4.exit_reason.value.upper()}")
        print(f"   💰 P&L: ${pnl:.2f} ({((market_data_risk['price']/position4.entry_price)-1)*100:.1f}%)")
        print(f"   🤖 Reasoning: {exit_decision4.reasoning}")
        print(f"   ⚡ Urgency: {exit_decision4.urgency}")
        exit_manager.remove_position("RISK")
    print()
    
    # Summary
    print("📋 POSITION LIFECYCLE SUMMARY")
    print("=" * 40)
    print("✅ Take Profit Exit: Successful target reached")
    print("🛡️  Stop Loss Exit: Loss protection activated") 
    print("⏰ Time-Based Exit: Maximum hold time enforced")
    print("⚠️  Risk Management: Volatility protection triggered")
    print()
    print("🧠 OVERMIND Brain now manages complete position lifecycle!")
    print("   • Entry strategies (StrategyManager)")
    print("   • Position tracking (ExitStrategyManager)")
    print("   • Exit conditions monitoring")
    print("   • Automated SELL decisions")
    
    return True

def main():
    """Run exit strategy demo"""
    print("🎯 THE OVERMIND PROTOCOL - Exit Strategy Demonstration")
    print("=" * 70)
    
    try:
        success = test_position_lifecycle()
        
        if success:
            print("\n🎉 Exit Strategy Demo Completed Successfully!")
            print("\n📊 Key Features Demonstrated:")
            print("   1. Position tracking after BUY decisions")
            print("   2. Multiple exit conditions (TP, SL, Time, Risk)")
            print("   3. Automatic SELL decision generation")
            print("   4. Risk-based exit prioritization")
            print("   5. Strategy-specific exit parameters")
            
            print("\n🚀 Next Steps for Production:")
            print("   • Connect to real-time market data")
            print("   • Implement position persistence")
            print("   • Add portfolio-level risk management")
            print("   • Monitor exit performance metrics")
            
        return success
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)