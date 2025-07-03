#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Strategy Activation
Sends strategy configuration to AI Brain
"""

import json
import redis
import time
from datetime import datetime

def activate_strategies():
    """Activate optimal trading strategies"""
    
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6380, decode_responses=True)
    
    # Load strategy configuration
    with open('config/optimal_strategy_config.json', 'r') as f:
        strategy_config = json.load(f)
    
    print("🎯 Activating THE OVERMIND PROTOCOL Strategies...")
    
    # Send strategy activation command
    activation_command = {
        "command_type": "strategy_activation",
        "timestamp": datetime.utcnow().isoformat(),
        "config": strategy_config,
        "mode": "live_trading",
        "priority": "high"
    }
    
    # Send to AI Brain
    r.lpush("overmind:strategy_commands", json.dumps(activation_command))
    
    print("✅ Strategy activation command sent to AI Brain")
    
    # Send test trading signal to verify system
    test_signal = {
        "action": "BUY",
        "symbol": "SOL/USDC",
        "quantity": 0.001,
        "strategy": "TokenSniping",
        "confidence": 0.85,
        "force_real_mode": True,
        "wallet_preference": "primary_wallet",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    r.lpush("overmind:commands", json.dumps(test_signal))
    
    print("🚀 Test trading signal sent")
    print("📊 Strategy activation complete!")
    
    # Display active strategies
    print("\n🎯 ACTIVE STRATEGIES:")
    for strategy, config in strategy_config["strategy_configuration"]["primary_strategies"].items():
        if config["enabled"]:
            print(f"  ✅ {strategy.upper()}: {config['allocation_percentage']}% allocation")
    
    print("\n🏦 WALLET ALLOCATION:")
    for wallet, config in strategy_config["strategy_configuration"]["wallet_strategy_mapping"].items():
        print(f"  💼 {wallet}: {int(config['allocation']*100)}% ({config['risk_profile']} risk)")

if __name__ == "__main__":
    activate_strategies()
