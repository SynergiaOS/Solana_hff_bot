#!/usr/bin/env python3
"""
Simple QuickNode Mainnet Test
Quick validation that Mainnet endpoint is working
"""

import os
import asyncio
import aiohttp

async def test_mainnet():
    """Test QuickNode Mainnet endpoint"""
    print("🚀 QuickNode Mainnet Simple Test")
    print("=" * 40)
    
    # Load .env manually
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    # Get Mainnet URL
    mainnet_rpc = os.getenv('QUICKNODE_MAINNET_RPC_URL')
    mainnet_ws = os.getenv('QUICKNODE_MAINNET_WS_URL')
    
    print(f"RPC URL: {mainnet_rpc[:50]}...")
    print(f"WS URL: {mainnet_ws[:50]}...")
    
    # Test RPC connection
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: getVersion
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getVersion"
            }
            
            async with session.post(mainnet_rpc, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    version = data['result']['solana-core']
                    print(f"✅ Solana Core: {version}")
                else:
                    print(f"❌ HTTP {response.status}")
                    return False
            
            # Test 2: getSlot
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "getSlot"
            }
            
            async with session.post(mainnet_rpc, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    slot = data['result']
                    print(f"✅ Current Slot: {slot:,}")
                else:
                    print(f"❌ HTTP {response.status}")
                    return False
            
            # Test 3: getBalance for a known account
            payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "getBalance",
                "params": ["11111111111111111111111111111111"]  # System Program
            }
            
            async with session.post(mainnet_rpc, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    balance = data['result']['value']
                    print(f"✅ System Program Balance: {balance} lamports")
                else:
                    print(f"❌ HTTP {response.status}")
                    return False
            
            print("\n🎉 ALL TESTS PASSED!")
            print("QuickNode Mainnet endpoint is ready for trading!")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mainnet())
    if success:
        print("\n✅ TASK COMPLETE: Configure QuickNode Mainnet Endpoint")
        print("🎯 Ready for next task: Implement SOL Momentum Strategy")
    else:
        print("\n❌ TASK FAILED: Please check configuration")
