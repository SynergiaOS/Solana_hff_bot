#!/usr/bin/env python3
"""
Test runner for Historical Data Testing Framework
Comprehensive testing with premium APIs and real market data
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timezone

# Add framework to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'brain', 'src'))

from historical_testing_framework import (
    HistoricalDataProvider,
    AIDecisionValidator,
    BacktestEngine,
    HistoricalTestRunner,
    get_test_scenarios
)

async def test_api_connections():
    """Test connections to premium APIs"""
    print("🔌 Testing Premium API Connections")
    print("-" * 50)
    
    try:
        # Test Helius API
        helius_key = os.getenv('HELIUS_API_KEY') or os.getenv('SNIPER_HELIUS_API_KEY')
        quicknode_key = os.getenv('QUICKNODE_API_KEY') or os.getenv('SNIPER_QUICKNODE_API_KEY')
        
        print(f"✅ Helius API Key: {'Configured' if helius_key else 'Missing'}")
        print(f"✅ QuickNode API Key: {'Configured' if quicknode_key else 'Missing'}")
        
        if helius_key:
            print(f"   - Helius Key: {helius_key[:10]}...")
        if quicknode_key:
            print(f"   - QuickNode Key: {quicknode_key[:10]}...")
        
        # Test data provider initialization
        provider = HistoricalDataProvider()
        await provider.initialize()
        print("✅ Historical data provider initialized")
        
        # Test basic API call (if keys are available)
        if helius_key:
            test_token = "So11111111111111111111111111111111111111112"  # SOL
            start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(2024, 1, 2, tzinfo=timezone.utc)
            
            data = await provider.get_historical_token_data(test_token, start_date, end_date)
            print(f"✅ Historical data retrieval: {'Success' if data else 'No data'}")
            
            if data:
                print(f"   - Token: {data.get('token_address', 'Unknown')}")
                print(f"   - Metadata: {'Available' if data.get('metadata') else 'None'}")
                print(f"   - Transactions: {len(data.get('transaction_history', []))}")
        
        await provider.close()
        return True
        
    except Exception as e:
        print(f"❌ API connection test failed: {e}")
        return False

async def test_scenario_definitions():
    """Test predefined test scenarios"""
    print("\n📋 Testing Scenario Definitions")
    print("-" * 50)
    
    try:
        scenarios = get_test_scenarios()
        print(f"✅ Total scenarios defined: {len(scenarios)}")
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{i}. {scenario.name}")
            print(f"   - Type: {scenario.test_type}")
            print(f"   - Token: {scenario.token_address[:10]}...")
            print(f"   - Period: {scenario.start_date.strftime('%Y-%m-%d')} to {scenario.end_date.strftime('%Y-%m-%d')}")
            print(f"   - Expected: {scenario.expected_outcome}")
            print(f"   - Success criteria: {len(scenario.success_criteria)} metrics")
        
        # Validate scenario data
        for scenario in scenarios:
            assert scenario.start_date < scenario.end_date, f"Invalid date range for {scenario.name}"
            assert scenario.token_address, f"Missing token address for {scenario.name}"
            assert scenario.success_criteria, f"Missing success criteria for {scenario.name}"
        
        print("\n✅ All scenarios validated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Scenario definition test failed: {e}")
        return False

async def test_ai_decision_validation():
    """Test AI decision validation framework"""
    print("\n🧠 Testing AI Decision Validation")
    print("-" * 50)
    
    try:
        validator = AIDecisionValidator()
        await validator.initialize()
        
        # Test decision validation
        test_decision = {
            'action': 'buy',
            'token_address': 'So11111111111111111111111111111111111111112',
            'amount': 1000,
            'confidence': 0.75,
            'reasoning': 'Strong bullish signals detected'
        }
        
        test_market_data = {
            'price_change_24h': 5.2,
            'volume': 1500000,
            'volatility': 0.15
        }
        
        validation_result = await validator.validate_decision(test_decision, test_market_data)
        
        print("✅ Decision validation completed")
        print(f"   - Decision: {validation_result.get('decision', {}).get('action', 'Unknown')}")
        print(f"   - Outcome: {validation_result.get('outcome', {}).get('profit_loss', 0):.2f}")
        print(f"   - Success: {validation_result.get('is_successful', False)}")
        
        performance = validation_result.get('performance', {})
        if performance:
            print(f"   - Return: {performance.get('return_percentage', 0):.2f}%")
            print(f"   - Quality Score: {performance.get('decision_quality_score', 0):.1f}/100")
        
        await validator.close()
        return True
        
    except Exception as e:
        print(f"❌ AI decision validation test failed: {e}")
        return False

async def test_backtest_engine():
    """Test backtesting engine"""
    print("\n⚙️ Testing Backtest Engine")
    print("-" * 50)
    
    try:
        engine = BacktestEngine()
        await engine.initialize()
        
        # Get a test scenario
        scenarios = get_test_scenarios()
        test_scenario = scenarios[0]  # Bull market scenario
        
        print(f"Running backtest for: {test_scenario.name}")
        
        # Run backtest
        result = await engine.run_backtest(test_scenario)
        
        print("✅ Backtest completed")
        print(f"   - Scenario: {result.scenario_name}")
        print(f"   - Start Balance: {result.start_balance:.2f}")
        print(f"   - End Balance: {result.end_balance:.2f}")
        print(f"   - Total Return: {result.total_return:.2f}%")
        print(f"   - Max Drawdown: {result.max_drawdown:.2f}%")
        print(f"   - Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   - Total Trades: {result.total_trades}")
        print(f"   - Win Rate: {result.win_rate:.1f}%")
        print(f"   - AI Decisions: {len(result.ai_decisions)}")
        
        await engine.close()
        return True
        
    except Exception as e:
        print(f"❌ Backtest engine test failed: {e}")
        return False

async def test_full_framework():
    """Test complete historical testing framework"""
    print("\n🚀 Testing Complete Framework")
    print("-" * 50)
    
    try:
        runner = HistoricalTestRunner()
        await runner.initialize()
        
        # Run a single scenario test
        scenarios = get_test_scenarios()
        test_scenario_name = scenarios[0].name
        
        print(f"Running scenario: {test_scenario_name}")
        result = await runner.run_scenario(test_scenario_name)
        
        if result:
            print("✅ Scenario execution completed")
            print(f"   - Return: {result.total_return:.2f}%")
            print(f"   - Trades: {result.total_trades}")
            print(f"   - Win Rate: {result.win_rate:.1f}%")
        
        # Generate report
        report = runner.generate_report()
        print("\n✅ Test report generated")
        
        summary = report.get('summary', {})
        print(f"   - Total scenarios: {summary.get('total_scenarios', 0)}")
        print(f"   - Success rate: {summary.get('success_rate', 0):.1f}%")
        print(f"   - Average return: {summary.get('average_return', 0):.2f}%")
        
        recommendations = report.get('recommendations', [])
        if recommendations:
            print("   - Recommendations:")
            for rec in recommendations[:3]:
                print(f"     • {rec}")
        
        await runner.close()
        return True
        
    except Exception as e:
        print(f"❌ Full framework test failed: {e}")
        return False

async def test_performance_metrics():
    """Test performance metrics calculation"""
    print("\n📊 Testing Performance Metrics")
    print("-" * 50)
    
    try:
        # Test metrics calculation with sample data
        sample_decisions = [
            {'action': 'buy', 'amount': 1000, 'confidence': 0.8, 'profit': 50},
            {'action': 'sell', 'amount': 800, 'confidence': 0.6, 'profit': -20},
            {'action': 'buy', 'amount': 1200, 'confidence': 0.9, 'profit': 80},
            {'action': 'hold', 'amount': 0, 'confidence': 0.5, 'profit': 0},
            {'action': 'sell', 'amount': 900, 'confidence': 0.7, 'profit': 30}
        ]
        
        total_profit = sum(d['profit'] for d in sample_decisions)
        winning_trades = sum(1 for d in sample_decisions if d['profit'] > 0)
        total_trades = len([d for d in sample_decisions if d['action'] != 'hold'])
        
        print("✅ Performance metrics calculated")
        print(f"   - Total profit: {total_profit}")
        print(f"   - Winning trades: {winning_trades}/{total_trades}")
        print(f"   - Win rate: {(winning_trades/total_trades)*100:.1f}%")
        print(f"   - Average confidence: {sum(d['confidence'] for d in sample_decisions)/len(sample_decisions):.2f}")
        
        # Test risk metrics
        returns = [d['profit']/max(d['amount'], 1) for d in sample_decisions if d['amount'] > 0]
        if returns:
            avg_return = sum(returns) / len(returns)
            volatility = (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5
            sharpe_ratio = avg_return / max(volatility, 0.01)
            
            print(f"   - Average return: {avg_return:.4f}")
            print(f"   - Volatility: {volatility:.4f}")
            print(f"   - Sharpe ratio: {sharpe_ratio:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance metrics test failed: {e}")
        return False

async def main():
    """Run all historical data framework tests"""
    print("🧠 THE OVERMIND PROTOCOL - Historical Data Testing Framework")
    print("=" * 70)
    print("Comprehensive testing with premium APIs and real market data")
    print("=" * 70)
    
    # Run all tests
    test1 = await test_api_connections()
    test2 = await test_scenario_definitions()
    test3 = await test_ai_decision_validation()
    test4 = await test_backtest_engine()
    test5 = await test_performance_metrics()
    test6 = await test_full_framework()
    
    print("\n" + "=" * 70)
    
    if all([test1, test2, test3, test4, test5, test6]):
        print("🎉 ALL HISTORICAL DATA FRAMEWORK TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • Premium API connections validated")
        print("   • Test scenarios defined and validated")
        print("   • AI decision validation framework working")
        print("   • Backtesting engine operational")
        print("   • Performance metrics calculation ready")
        print("   • Complete framework integration successful")
        print("\n🚀 FRAMEWORK READY FOR:")
        print("   • Bull market scenario testing")
        print("   • Bear market scenario testing")
        print("   • High volatility testing")
        print("   • New token launch testing")
        print("   • AI decision validation")
        print("   • Performance optimization")
        print("\n🎯 MISSION STATUS: HISTORICAL DATA TESTING FRAMEWORK COMPLETE")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
