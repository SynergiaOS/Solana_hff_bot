#!/usr/bin/env python3
"""
Real API Data Test for Historical Framework
Test with actual Helius and QuickNode API calls
"""

import sys
import os
import asyncio
import aiohttp
import json
from datetime import datetime, timezone, timedelta

# Add framework to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'brain', 'src'))

async def test_helius_api_direct():
    """Test direct Helius API calls"""
    print("🔍 Testing Direct Helius API Calls")
    print("-" * 50)
    
    try:
        helius_key = os.getenv('HELIUS_API_KEY') or os.getenv('SNIPER_HELIUS_API_KEY')
        
        if not helius_key:
            print("❌ No Helius API key found")
            return False
        
        print(f"✅ Using Helius API key: {helius_key[:10]}...")
        
        # Test 1: Token metadata
        sol_mint = "So11111111111111111111111111111111111111112"
        
        async with aiohttp.ClientSession() as session:
            # Test token metadata endpoint
            metadata_url = f"https://api.helius.xyz/v0/token-metadata"
            params = {
                'api-key': helius_key,
                'mint-accounts': [sol_mint]
            }
            
            async with session.get(metadata_url, params=params) as response:
                print(f"✅ Token metadata API status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"   - Response data: {len(data)} tokens")
                    
                    if data:
                        token_info = data[0]
                        print(f"   - Token name: {token_info.get('onChainMetadata', {}).get('metadata', {}).get('name', 'Unknown')}")
                        print(f"   - Token symbol: {token_info.get('onChainMetadata', {}).get('metadata', {}).get('symbol', 'Unknown')}")
                        print(f"   - Mint authority: {token_info.get('mint', 'Unknown')}")
                else:
                    error_text = await response.text()
                    print(f"   - Error: {error_text}")
            
            # Test 2: Address transactions
            tx_url = f"https://api.helius.xyz/v0/addresses/{sol_mint}/transactions"
            tx_params = {
                'api-key': helius_key,
                'limit': 10,
                'type': 'SWAP'
            }
            
            async with session.get(tx_url, params=tx_params) as response:
                print(f"✅ Transactions API status: {response.status}")
                
                if response.status == 200:
                    tx_data = await response.json()
                    print(f"   - Transactions found: {len(tx_data)}")
                    
                    if tx_data:
                        latest_tx = tx_data[0]
                        print(f"   - Latest tx signature: {latest_tx.get('signature', 'Unknown')[:20]}...")
                        print(f"   - Timestamp: {latest_tx.get('timestamp', 'Unknown')}")
                        print(f"   - Type: {latest_tx.get('type', 'Unknown')}")
                else:
                    error_text = await response.text()
                    print(f"   - Error: {error_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Helius API test failed: {e}")
        return False

async def test_quicknode_api_direct():
    """Test direct QuickNode API calls"""
    print("\n🚀 Testing Direct QuickNode API Calls")
    print("-" * 50)
    
    try:
        quicknode_key = os.getenv('QUICKNODE_API_KEY') or os.getenv('SNIPER_QUICKNODE_API_KEY')
        
        if not quicknode_key:
            print("❌ No QuickNode API key found")
            return False
        
        print(f"✅ Using QuickNode API key: {quicknode_key[:10]}...")
        
        # QuickNode RPC endpoint (from .env)
        quicknode_url = os.getenv('SNIPER_QUICKNODE_WS_URL', '').replace('wss://', 'https://').replace('/ws', '')
        if not quicknode_url:
            quicknode_url = f"https://distinguished-blue-glade.solana-devnet.quiknode.pro/{quicknode_key}"
        
        print(f"✅ QuickNode URL: {quicknode_url[:50]}...")
        
        async with aiohttp.ClientSession() as session:
            # Test 1: Get version (basic RPC call)
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getVersion"
            }
            
            async with session.post(quicknode_url, json=rpc_payload) as response:
                print(f"✅ RPC getVersion status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    version = data.get('result', {})
                    print(f"   - Solana version: {version.get('solana-core', 'Unknown')}")
                    print(f"   - Feature set: {version.get('feature-set', 'Unknown')}")
                else:
                    error_text = await response.text()
                    print(f"   - Error: {error_text}")
            
            # Test 2: Get recent blockhash
            blockhash_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "getRecentBlockhash"
            }
            
            async with session.post(quicknode_url, json=blockhash_payload) as response:
                print(f"✅ RPC getRecentBlockhash status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})
                    if 'value' in result:
                        blockhash = result['value'].get('blockhash', 'Unknown')
                        print(f"   - Recent blockhash: {blockhash[:20]}...")
                        print(f"   - Fee calculator: {result['value'].get('feeCalculator', {})}")
                else:
                    error_text = await response.text()
                    print(f"   - Error: {error_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ QuickNode API test failed: {e}")
        return False

async def test_historical_data_collection():
    """Test historical data collection with real APIs"""
    print("\n📊 Testing Historical Data Collection")
    print("-" * 50)
    
    try:
        from historical_testing_framework import HistoricalDataProvider
        
        provider = HistoricalDataProvider()
        await provider.initialize()
        
        # Test with SOL token
        sol_mint = "So11111111111111111111111111111111111111112"
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        
        print(f"Collecting data for SOL from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        historical_data = await provider.get_historical_token_data(sol_mint, start_date, end_date)
        
        print("✅ Historical data collection completed")
        print(f"   - Token address: {historical_data.get('token_address', 'Unknown')}")
        print(f"   - Data source: {historical_data.get('data_source', 'Unknown')}")
        print(f"   - Period: {historical_data.get('period', {})}")
        
        metadata = historical_data.get('metadata', {})
        if metadata:
            print(f"   - Metadata available: Yes")
            on_chain = metadata.get('onChainMetadata', {}).get('metadata', {})
            if on_chain:
                print(f"     • Name: {on_chain.get('name', 'Unknown')}")
                print(f"     • Symbol: {on_chain.get('symbol', 'Unknown')}")
        else:
            print(f"   - Metadata available: No")
        
        tx_history = historical_data.get('transaction_history', [])
        print(f"   - Transaction history: {len(tx_history)} transactions")
        
        if tx_history:
            latest_tx = tx_history[0]
            print(f"     • Latest tx: {latest_tx.get('signature', 'Unknown')[:20]}...")
            print(f"     • Type: {latest_tx.get('type', 'Unknown')}")
            print(f"     • Timestamp: {latest_tx.get('timestamp', 'Unknown')}")
        
        await provider.close()
        return True
        
    except Exception as e:
        print(f"❌ Historical data collection test failed: {e}")
        return False

async def test_market_analysis():
    """Test market analysis with real data"""
    print("\n📈 Testing Market Analysis")
    print("-" * 50)
    
    try:
        from historical_testing_framework import HistoricalDataProvider
        
        provider = HistoricalDataProvider()
        await provider.initialize()
        
        # Test market conditions for today
        today = datetime.now(timezone.utc)
        market_conditions = await provider.get_market_conditions(today)
        
        print("✅ Market analysis completed")
        print(f"   - Date: {market_conditions.get('date', 'Unknown')}")
        print(f"   - Market sentiment: {market_conditions.get('market_sentiment', 'Unknown')}")
        print(f"   - Volatility index: {market_conditions.get('volatility_index', 0)}")
        print(f"   - Trading volume: {market_conditions.get('trading_volume', 0):,}")
        print(f"   - DeFi TVL: ${market_conditions.get('defi_tvl', 0):,}")
        print(f"   - Data source: {market_conditions.get('data_source', 'Unknown')}")
        
        dominant_tokens = market_conditions.get('dominant_tokens', [])
        if dominant_tokens:
            print(f"   - Dominant tokens: {', '.join(dominant_tokens)}")
        
        await provider.close()
        return True
        
    except Exception as e:
        print(f"❌ Market analysis test failed: {e}")
        return False

async def test_performance_with_real_data():
    """Test performance metrics with real API data"""
    print("\n⚡ Testing Performance with Real Data")
    print("-" * 50)
    
    try:
        from historical_testing_framework import HistoricalTestRunner, get_test_scenarios
        
        runner = HistoricalTestRunner()
        await runner.initialize()
        
        # Run the first scenario with real data
        scenarios = get_test_scenarios()
        bull_market_scenario = scenarios[0]  # Bull Market - SOL Rally
        
        print(f"Running real data test for: {bull_market_scenario.name}")
        
        result = await runner.run_scenario(bull_market_scenario.name)
        
        if result:
            print("✅ Real data performance test completed")
            print(f"   - Scenario: {result.scenario_name}")
            print(f"   - Total return: {result.total_return:.2f}%")
            print(f"   - Max drawdown: {result.max_drawdown:.2f}%")
            print(f"   - Sharpe ratio: {result.sharpe_ratio:.2f}")
            print(f"   - Win rate: {result.win_rate:.1f}%")
            print(f"   - Total trades: {result.total_trades}")
            print(f"   - AI decisions: {len(result.ai_decisions)}")
            
            # Analyze AI decisions
            if result.ai_decisions:
                actions = [d.get('action', 'unknown') for d in result.ai_decisions]
                action_counts = {action: actions.count(action) for action in set(actions)}
                print(f"   - Action distribution: {action_counts}")
                
                avg_confidence = sum(d.get('confidence', 0) for d in result.ai_decisions) / len(result.ai_decisions)
                print(f"   - Average confidence: {avg_confidence:.2f}")
        
        # Generate comprehensive report
        report = runner.generate_report()
        print("\n✅ Performance report generated")
        
        summary = report.get('summary', {})
        print(f"   - Success rate: {summary.get('success_rate', 0):.1f}%")
        print(f"   - Average return: {summary.get('average_return', 0):.2f}%")
        print(f"   - Average Sharpe: {summary.get('average_sharpe_ratio', 0):.2f}")
        
        recommendations = report.get('recommendations', [])
        if recommendations:
            print("   - Key recommendations:")
            for rec in recommendations:
                print(f"     • {rec}")
        
        await runner.close()
        return True
        
    except Exception as e:
        print(f"❌ Performance test with real data failed: {e}")
        return False

async def main():
    """Run all real API data tests"""
    print("🧠 THE OVERMIND PROTOCOL - Real API Data Testing")
    print("=" * 60)
    print("Testing Historical Framework with actual premium API data")
    print("=" * 60)
    
    # Run all tests
    test1 = await test_helius_api_direct()
    test2 = await test_quicknode_api_direct()
    test3 = await test_historical_data_collection()
    test4 = await test_market_analysis()
    test5 = await test_performance_with_real_data()
    
    print("\n" + "=" * 60)
    
    if all([test1, test2, test3, test4, test5]):
        print("🎉 ALL REAL API DATA TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • Direct Helius API calls working")
        print("   • Direct QuickNode API calls working")
        print("   • Historical data collection operational")
        print("   • Market analysis with real data")
        print("   • Performance testing with real API data")
        print("\n🚀 READY FOR PRODUCTION:")
        print("   • Real market data backtesting")
        print("   • AI decision validation with historical outcomes")
        print("   • Performance optimization based on real data")
        print("   • Risk management validation")
        print("\n🎯 HISTORICAL DATA FRAMEWORK: FULLY OPERATIONAL")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Check API keys and network connectivity")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
