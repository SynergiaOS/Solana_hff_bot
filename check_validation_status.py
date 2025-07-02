#!/usr/bin/env python3
"""
Quick validation status checker for 48H Final Validation
"""

import redis
import json
import time

def main():
    r = redis.Redis(host='localhost', port=6380, decode_responses=True)
    
    print('🔥 THE OVERMIND PROTOCOL v2.3.0 - 48H VALIDATION STATUS')
    print('=' * 70)
    
    # Check validation snapshots
    snapshots = r.lrange('overmind:validation_snapshots', 0, 2)
    print(f'📊 Validation Snapshots: {len(snapshots)}')
    
    # Check baseline
    baseline = r.lrange('overmind:validation_baseline', 0, 0)
    print(f'📋 Baseline Captured: {len(baseline) > 0}')
    
    # Check system components
    position_updates = r.llen('overmind:position_updates')
    exit_signals = r.llen('overmind:exit_signals')
    intelligence_updates = r.llen('overmind:post_trade_intelligence')
    
    print(f'📈 Position Updates: {position_updates}')
    print(f'🎯 Exit Signals: {exit_signals}')
    print(f'🧠 Intelligence Updates: {intelligence_updates}')
    
    # Show latest snapshot if available
    if snapshots:
        latest = json.loads(snapshots[0])
        progress = latest.get('validation_progress', 0)
        remaining = latest.get('remaining_time', 0) / 3600
        
        print(f'\n⏱️  VALIDATION PROGRESS: {progress:.1f}%')
        print(f'⏰ Time Remaining: {remaining:.1f} hours')
        
        lifecycle = latest.get('lifecycle_analysis', {})
        if lifecycle:
            print(f'💰 Current P&L: ${lifecycle.get("current_pnl", 0):.6f}')
            print(f'📊 Portfolio Return: {lifecycle.get("portfolio_return", 0):.2f}%')
            print(f'🏥 Position Health: {lifecycle.get("position_health", "UNKNOWN")}')
        
        intelligence = latest.get('intelligence_analysis', {})
        if intelligence:
            print(f'🧠 System Health: {intelligence.get("system_health", 0):.1%}')
            print(f'⚙️  Active Components: {intelligence.get("active_components", 0)}/{intelligence.get("total_components", 0)}')
        
        exit_analysis = latest.get('exit_analysis', {})
        if exit_analysis:
            print(f'🎯 Exit Signals Generated: {exit_analysis.get("total_exit_signals", 0)}')
            print(f'🎲 Average Confidence: {exit_analysis.get("avg_confidence", 0):.2f}')
    
    else:
        print('\n⚠️  No validation snapshots yet - system starting up')
    
    print(f'\n🔄 Status Check Time: {time.strftime("%Y-%m-%d %H:%M:%S")}')

if __name__ == "__main__":
    main()
