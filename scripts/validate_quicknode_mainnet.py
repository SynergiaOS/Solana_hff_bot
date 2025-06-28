#!/usr/bin/env python3
"""
QuickNode Mainnet Endpoint Validation Script
Validates that the newly created Mainnet endpoint is working correctly
"""

import os
import sys
import asyncio
import aiohttp
import json
from datetime import datetime

# Add config to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

async def validate_quicknode_mainnet():
    """Validate QuickNode Mainnet endpoint configuration"""
    print("🚀 QuickNode Mainnet Endpoint Validation")
    print("=" * 50)
    
    # Load environment variables
    from environment_loader import initialize_environment
    
    try:
        # Initialize environment for production (Mainnet)
        os.environ['APP_ENV'] = 'production'
        loader = initialize_environment()
        config = loader.get_config()
        
        print(f"Environment: {loader.get_environment().value}")
        print(f"Network: {config.network_name}")
        print(f"Is Mainnet: {config.is_mainnet}")
        
        if not config.is_mainnet:
            print("❌ Expected Mainnet configuration, got Devnet")
            return False
        
        # Get Mainnet URLs
        mainnet_rpc = config.quicknode_rpc_url
        mainnet_ws = config.quicknode_ws_url
        
        print(f"\n🔗 Testing Mainnet Endpoints:")
        print(f"RPC URL: {mainnet_rpc[:50]}...")
        print(f"WS URL: {mainnet_ws[:50]}...")
        
        # Validate URLs are not placeholder
        if 'your-mainnet-endpoint' in mainnet_rpc:
            print("❌ Mainnet RPC URL is still placeholder")
            print("Please update QUICKNODE_MAINNET_RPC_URL in .env")
            return False
        
        if 'your-mainnet-endpoint' in mainnet_ws:
            print("❌ Mainnet WS URL is still placeholder")
            print("Please update QUICKNODE_MAINNET_WS_URL in .env")
            return False
        
        # Test RPC connection
        print(f"\n🧪 Testing RPC Connection...")
        success = await test_rpc_connection(mainnet_rpc)
        
        if success:
            print("✅ QuickNode Mainnet endpoint validation PASSED")
            print("\n🎯 Next Steps:")
            print("1. Endpoint is ready for SOL Momentum Strategy")
            print("2. Can proceed to implement trading strategy")
            print("3. Paper trading infrastructure can use this endpoint")
            return True
        else:
            print("❌ QuickNode Mainnet endpoint validation FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

async def test_rpc_connection(rpc_url):
    """Test RPC connection with basic Solana calls"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: getVersion
            print("  Testing getVersion...")
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getVersion"
            }
            
            async with session.post(rpc_url, json=payload, timeout=10) as response:
                if response.status != 200:
                    print(f"    ❌ HTTP {response.status}")
                    return False
                
                data = await response.json()
                if 'result' not in data:
                    print(f"    ❌ Invalid response: {data}")
                    return False
                
                version = data['result']['solana-core']
                print(f"    ✅ Solana version: {version}")
            
            # Test 2: getSlot
            print("  Testing getSlot...")
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "getSlot"
            }
            
            async with session.post(rpc_url, json=payload, timeout=10) as response:
                if response.status != 200:
                    print(f"    ❌ HTTP {response.status}")
                    return False
                
                data = await response.json()
                if 'result' not in data:
                    print(f"    ❌ Invalid response: {data}")
                    return False
                
                slot = data['result']
                print(f"    ✅ Current slot: {slot}")
            
            # Test 3: getAccountInfo for SOL token
            print("  Testing getAccountInfo...")
            sol_mint = "So11111111111111111111111111111111111111112"  # Wrapped SOL
            payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "getAccountInfo",
                "params": [sol_mint, {"encoding": "base64"}]
            }
            
            async with session.post(rpc_url, json=payload, timeout=10) as response:
                if response.status != 200:
                    print(f"    ❌ HTTP {response.status}")
                    return False
                
                data = await response.json()
                if 'result' not in data:
                    print(f"    ❌ Invalid response: {data}")
                    return False
                
                account_info = data['result']
                if account_info and account_info['value']:
                    print(f"    ✅ SOL account info retrieved")
                else:
                    print(f"    ⚠️ SOL account info empty (might be normal)")
            
            # Test 4: Check rate limits
            print("  Testing rate limits...")
            start_time = datetime.now()
            
            # Make 5 quick requests
            for i in range(5):
                payload = {
                    "jsonrpc": "2.0",
                    "id": f"rate_test_{i}",
                    "method": "getSlot"
                }
                async with session.post(rpc_url, json=payload, timeout=5) as response:
                    if response.status == 429:
                        print(f"    ⚠️ Rate limit hit on request {i+1}")
                        break
                    elif response.status != 200:
                        print(f"    ❌ HTTP {response.status} on request {i+1}")
                        return False
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"    ✅ 5 requests completed in {duration:.2f}s")
            
            return True
            
    except asyncio.TimeoutError:
        print("    ❌ Connection timeout")
        return False
    except Exception as e:
        print(f"    ❌ Connection error: {e}")
        return False

def print_configuration_template():
    """Print template for .env configuration"""
    print("\n📋 Configuration Template for .env:")
    print("-" * 40)
    print("# Replace these with your actual Mainnet endpoint URLs:")
    print("QUICKNODE_MAINNET_RPC_URL=https://your-mainnet-name.solana-mainnet.quiknode.pro/YOUR_MAINNET_KEY")
    print("QUICKNODE_MAINNET_WS_URL=wss://your-mainnet-name.solana-mainnet.quiknode.pro/YOUR_MAINNET_KEY")
    print("\n# Your Mainnet endpoint should look similar to your Devnet:")
    print("# Devnet: distinguished-blue-glade.solana-devnet.quiknode.pro")
    print("# Mainnet: your-mainnet-name.solana-mainnet.quiknode.pro")

async def main():
    """Main validation function"""
    print("Starting QuickNode Mainnet validation...")

    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded")
    except ImportError:
        print("⚠️ python-dotenv not available, trying manual load...")
        # Manual .env loading
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
            print("✅ .env file loaded manually")

    # Check if .env is configured (after loading)
    mainnet_rpc = os.getenv('QUICKNODE_MAINNET_RPC_URL', '')

    print(f"DEBUG: mainnet_rpc = '{mainnet_rpc}'")
    print(f"DEBUG: contains placeholder = {'your-mainnet-endpoint' in mainnet_rpc}")

    if not mainnet_rpc or 'your-mainnet-endpoint' in mainnet_rpc:
        print("⚠️ Mainnet endpoint not configured yet")
        print_configuration_template()
        print("\n🎯 Action Required:")
        print("1. Create Mainnet endpoint in QuickNode dashboard")
        print("2. Update .env with actual URLs")
        print("3. Run this script again to validate")
        return False
    
    # Run validation
    success = await validate_quicknode_mainnet()
    
    if success:
        print("\n🎉 VALIDATION COMPLETE!")
        print("QuickNode Mainnet endpoint is ready for trading!")
    else:
        print("\n❌ VALIDATION FAILED!")
        print("Please check the errors above and fix configuration")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
