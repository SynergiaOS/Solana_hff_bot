#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Position Sizing Calculator for 0.343 SOL Portfolio
=========================================================================

Calculates optimal position sizes based on current balance and risk parameters.
"""

import json
import math
from typing import Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class RiskProfile(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    BLITZKRIEG = "blitzkrieg"

@dataclass
class PortfolioConfig:
    current_balance: float = 0.343
    target_balance: float = 2.0
    risk_profile: RiskProfile = RiskProfile.BLITZKRIEG
    
class PositionSizingCalculator:
    """Calculate position sizes for THE OVERMIND PROTOCOL"""
    
    def __init__(self, portfolio_config: PortfolioConfig):
        self.config = portfolio_config
        self.risk_params = self._get_risk_parameters()
    
    def _get_risk_parameters(self) -> Dict:
        """Get risk parameters based on profile"""
        params = {
            RiskProfile.CONSERVATIVE: {
                "max_position_pct": 5.0,
                "max_daily_loss_pct": 3.0,
                "stop_loss_pct": 2.0,
                "take_profit_pct": 8.0,
                "risk_per_trade_pct": 1.0
            },
            RiskProfile.BALANCED: {
                "max_position_pct": 10.0,
                "max_daily_loss_pct": 8.0,
                "stop_loss_pct": 5.0,
                "take_profit_pct": 15.0,
                "risk_per_trade_pct": 2.0
            },
            RiskProfile.AGGRESSIVE: {
                "max_position_pct": 20.0,
                "max_daily_loss_pct": 15.0,
                "stop_loss_pct": 8.0,
                "take_profit_pct": 25.0,
                "risk_per_trade_pct": 5.0
            },
            RiskProfile.BLITZKRIEG: {
                "max_position_pct": 25.0,
                "max_daily_loss_pct": 15.0,
                "stop_loss_pct": 8.0,
                "take_profit_pct": 100.0,  # 100x target for memecoins
                "risk_per_trade_pct": 5.0
            }
        }
        return params[self.config.risk_profile]
    
    def calculate_position_size(self, strategy: str, confidence: float = 0.8) -> Dict:
        """Calculate position size for a specific strategy"""
        
        # Base position size
        base_size_pct = self.risk_params["max_position_pct"]
        base_size_sol = self.config.current_balance * (base_size_pct / 100)
        
        # Strategy-specific adjustments
        strategy_multipliers = {
            "memecoin_hunter": 1.0,      # Full size for high-reward memecoins
            "mev_opportunities": 0.5,    # Half size for MEV (lower risk)
            "arbitrage": 0.3,            # Conservative for arbitrage
            "soul_meteor": 0.8,          # High confidence strategy
            "developer_tracking": 0.6,   # Medium confidence
            "sol_momentum": 0.4          # Conservative momentum
        }
        
        multiplier = strategy_multipliers.get(strategy, 0.5)
        
        # Confidence adjustment
        confidence_multiplier = confidence
        
        # Final position size
        final_size_sol = base_size_sol * multiplier * confidence_multiplier
        final_size_pct = (final_size_sol / self.config.current_balance) * 100
        
        # Risk calculations
        stop_loss_amount = final_size_sol * (self.risk_params["stop_loss_pct"] / 100)
        take_profit_amount = final_size_sol * (self.risk_params["take_profit_pct"] / 100)
        
        return {
            "strategy": strategy,
            "position_size_sol": round(final_size_sol, 6),
            "position_size_pct": round(final_size_pct, 2),
            "stop_loss_amount": round(stop_loss_amount, 6),
            "take_profit_amount": round(take_profit_amount, 6),
            "risk_reward_ratio": round(take_profit_amount / stop_loss_amount, 2),
            "confidence_used": confidence,
            "strategy_multiplier": multiplier
        }
    
    def get_portfolio_limits(self) -> Dict:
        """Get all portfolio limits in SOL"""
        balance = self.config.current_balance
        
        return {
            "current_balance": balance,
            "max_daily_loss": round(balance * (self.risk_params["max_daily_loss_pct"] / 100), 6),
            "max_position_size": round(balance * (self.risk_params["max_position_pct"] / 100), 6),
            "risk_per_trade": round(balance * (self.risk_params["risk_per_trade_pct"] / 100), 6),
            "emergency_threshold": round(balance * 0.20, 6),  # 20% emergency threshold
            "hourly_loss_limit": round(balance * 0.05, 6),   # 5% hourly limit
            "remaining_balance_after_max_loss": round(balance * (1 - self.risk_params["max_daily_loss_pct"] / 100), 6)
        }
    
    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly Criterion for optimal position sizing"""
        if avg_loss <= 0:
            return 0.0
        
        win_loss_ratio = avg_win / avg_loss
        kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Cap Kelly at max position size
        max_kelly = self.risk_params["max_position_pct"] / 100
        return min(max(kelly_pct, 0), max_kelly)
    
    def generate_position_plan(self) -> Dict:
        """Generate complete position sizing plan"""
        strategies = [
            "memecoin_hunter",
            "mev_opportunities", 
            "arbitrage",
            "soul_meteor",
            "developer_tracking",
            "sol_momentum"
        ]
        
        plan = {
            "portfolio_config": {
                "current_balance": self.config.current_balance,
                "target_balance": self.config.target_balance,
                "risk_profile": self.config.risk_profile.value
            },
            "portfolio_limits": self.get_portfolio_limits(),
            "strategy_positions": {},
            "total_allocated": 0.0,
            "remaining_balance": self.config.current_balance
        }
        
        total_allocated = 0.0
        
        for strategy in strategies:
            # Use different confidence levels for different strategies
            confidence_levels = {
                "memecoin_hunter": 0.9,    # High confidence in memecoin hunting
                "mev_opportunities": 0.8,  # Good confidence in MEV
                "arbitrage": 0.7,          # Moderate confidence
                "soul_meteor": 0.8,        # Good strategy
                "developer_tracking": 0.6, # Lower confidence
                "sol_momentum": 0.5        # Conservative
            }
            
            confidence = confidence_levels.get(strategy, 0.7)
            position = self.calculate_position_size(strategy, confidence)
            
            # Check if we have enough balance
            if total_allocated + position["position_size_sol"] <= self.config.current_balance:
                plan["strategy_positions"][strategy] = position
                total_allocated += position["position_size_sol"]
        
        plan["total_allocated"] = round(total_allocated, 6)
        plan["remaining_balance"] = round(self.config.current_balance - total_allocated, 6)
        plan["allocation_percentage"] = round((total_allocated / self.config.current_balance) * 100, 2)
        
        return plan

def main():
    """Main function to demonstrate position sizing"""
    
    # Initialize calculator for 0.343 SOL portfolio
    config = PortfolioConfig(
        current_balance=0.343,
        target_balance=2.0,
        risk_profile=RiskProfile.BLITZKRIEG
    )
    
    calculator = PositionSizingCalculator(config)
    
    print("🛡️ THE OVERMIND PROTOCOL - Position Sizing Calculator")
    print("=" * 60)
    print(f"Portfolio: {config.current_balance} SOL → {config.target_balance} SOL")
    print(f"Risk Profile: {config.risk_profile.value.upper()}")
    print()
    
    # Generate complete plan
    plan = calculator.generate_position_plan()
    
    # Display portfolio limits
    print("📊 PORTFOLIO LIMITS:")
    limits = plan["portfolio_limits"]
    for key, value in limits.items():
        print(f"  {key.replace('_', ' ').title()}: {value} SOL")
    print()
    
    # Display strategy positions
    print("🎯 STRATEGY POSITION SIZES:")
    for strategy, position in plan["strategy_positions"].items():
        print(f"  {strategy.replace('_', ' ').title()}:")
        print(f"    Position: {position['position_size_sol']} SOL ({position['position_size_pct']}%)")
        print(f"    Stop Loss: {position['stop_loss_amount']} SOL")
        print(f"    Take Profit: {position['take_profit_amount']} SOL")
        print(f"    Risk/Reward: 1:{position['risk_reward_ratio']}")
        print()
    
    # Display summary
    print("📈 ALLOCATION SUMMARY:")
    print(f"  Total Allocated: {plan['total_allocated']} SOL ({plan['allocation_percentage']}%)")
    print(f"  Remaining Balance: {plan['remaining_balance']} SOL")
    print()
    
    # Save plan to file
    with open("config/current_position_plan.json", "w") as f:
        json.dump(plan, f, indent=2, default=str)
    
    print("💾 Position plan saved to: config/current_position_plan.json")

if __name__ == "__main__":
    main()
