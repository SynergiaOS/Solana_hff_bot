#!/usr/bin/env python3
"""THE OVERMIND PROTOCOL - QuickNode Endpoints Test
Test script to verify QuickNode mainnet endpoints are working correctly.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any
import httpx
import websockets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# QuickNode Mainnet Endpoints
QUICKNODE_RPC_URL = "https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
QUICKNODE_WSS_URL = "wss://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"

async def test_rpc_endpoint():
    """Test the QuickNode RPC endpoint"""
    logger.info("🔍 Testing QuickNode RPC endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test 1: Get version
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getVersion"
            }
            
            start_time = time.time()
            response = await client.post(QUICKNODE_RPC_URL, json=payload)
            latency = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            data = response.json()
            
            if "result" in data:
                version = data["result"]
                logger.info(f"✅ RPC Version: {version}")
                logger.info(f"⚡ RPC Latency: {latency:.2f}ms")
            else:
                logger.error(f"❌ RPC Error: {data}")
                return False
            
            # Test 2: Get slot
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "getSlot"
            }
            
            start_time = time.time()
            response = await client.post(QUICKNODE_RPC_URL, json=payload)
            latency = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            data = response.json()
            
            if "result" in data:
                slot = data["result"]
                logger.info(f"✅ Current Slot: {slot}")
                logger.info(f"⚡ Slot Query Latency: {latency:.2f}ms")
            else:
                logger.error(f"❌ Slot Error: {data}")
                return False
            
            # Test 3: Get recent blockhash
            payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "getLatestBlockhash"
            }
            
            start_time = time.time()
            response = await client.post(QUICKNODE_RPC_URL, json=payload)
            latency = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            data = response.json()
            
            if "result" in data:
                blockhash = data["result"]["value"]["blockhash"]
                logger.info(f"✅ Latest Blockhash: {blockhash[:16]}...")
                logger.info(f"⚡ Blockhash Query Latency: {latency:.2f}ms")
            else:
                logger.error(f"❌ Blockhash Error: {data}")
                return False
            
            logger.info("✅ RPC endpoint test completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ RPC endpoint test failed: {e}")
        return False

async def test_websocket_endpoint():
    """Test the QuickNode WebSocket endpoint"""
    logger.info("🔍 Testing QuickNode WebSocket endpoint...")
    
    try:
        # Connect to WebSocket
        async with websockets.connect(QUICKNODE_WSS_URL) as websocket:
            logger.info("✅ WebSocket connection established")
            
            # Subscribe to slot updates
            subscription_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "slotSubscribe"
            }
            
            await websocket.send(json.dumps(subscription_request))
            logger.info("📡 Subscribed to slot updates")
            
            # Wait for subscription confirmation
            response = await websocket.recv()
            data = json.loads(response)
            
            if "result" in data:
                subscription_id = data["result"]
                logger.info(f"✅ Subscription ID: {subscription_id}")
            else:
                logger.error(f"❌ Subscription Error: {data}")
                return False
            
            # Listen for a few slot updates
            logger.info("👂 Listening for slot updates...")
            for i in range(3):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    
                    if "params" in data and "result" in data["params"]:
                        slot_info = data["params"]["result"]
                        logger.info(f"📊 Slot Update {i+1}: {slot_info}")
                    else:
                        logger.warning(f"⚠️ Unexpected message: {data}")
                        
                except asyncio.TimeoutError:
                    logger.warning(f"⏰ Timeout waiting for slot update {i+1}")
                    break
            
            # Unsubscribe
            unsubscribe_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "slotUnsubscribe",
                "params": [subscription_id]
            }
            
            await websocket.send(json.dumps(unsubscribe_request))
            response = await websocket.recv()
            data = json.loads(response)
            
            if "result" in data and data["result"]:
                logger.info("✅ Successfully unsubscribed")
            else:
                logger.warning(f"⚠️ Unsubscribe response: {data}")
            
            logger.info("✅ WebSocket endpoint test completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ WebSocket endpoint test failed: {e}")
        return False

async def test_performance_metrics():
    """Test performance metrics of the endpoints"""
    logger.info("🔍 Testing performance metrics...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test multiple requests to measure average latency
            latencies = []
            
            for i in range(10):
                payload = {
                    "jsonrpc": "2.0",
                    "id": i,
                    "method": "getSlot"
                }
                
                start_time = time.time()
                response = await client.post(QUICKNODE_RPC_URL, json=payload)
                latency = (time.time() - start_time) * 1000
                
                response.raise_for_status()
                data = response.json()
                
                if "result" in data:
                    latencies.append(latency)
                else:
                    logger.warning(f"⚠️ Request {i} failed: {data}")
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                
                logger.info(f"📊 Performance Metrics:")
                logger.info(f"   Average Latency: {avg_latency:.2f}ms")
                logger.info(f"   Min Latency: {min_latency:.2f}ms")
                logger.info(f"   Max Latency: {max_latency:.2f}ms")
                logger.info(f"   Successful Requests: {len(latencies)}/10")
                
                # Performance assessment
                if avg_latency < 50:
                    logger.info("🚀 EXCELLENT: Ultra-low latency suitable for HFT")
                elif avg_latency < 100:
                    logger.info("✅ GOOD: Low latency suitable for trading")
                elif avg_latency < 200:
                    logger.info("⚠️ MODERATE: Acceptable for most trading strategies")
                else:
                    logger.warning("🐌 HIGH: May not be suitable for latency-sensitive strategies")
                
                return True
            else:
                logger.error("❌ No successful requests for performance testing")
                return False
                
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 THE OVERMIND PROTOCOL - QuickNode Endpoints Testing")
    logger.info("🎯 Testing production-ready Solana mainnet endpoints")
    
    print("\n" + "="*80)
    print("QUICKNODE MAINNET ENDPOINTS TESTING")
    print("="*80)
    print(f"RPC URL: {QUICKNODE_RPC_URL}")
    print(f"WSS URL: {QUICKNODE_WSS_URL}")
    print("="*80)
    
    # Test results
    results = {}
    
    # Test 1: RPC Endpoint
    print("\n🔍 TEST 1: RPC Endpoint")
    print("-" * 40)
    results["rpc"] = await test_rpc_endpoint()
    
    # Test 2: WebSocket Endpoint
    print("\n🔍 TEST 2: WebSocket Endpoint")
    print("-" * 40)
    results["websocket"] = await test_websocket_endpoint()
    
    # Test 3: Performance Metrics
    print("\n🔍 TEST 3: Performance Metrics")
    print("-" * 40)
    results["performance"] = await test_performance_metrics()
    
    # Summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.upper()}: {status}")
        if not result:
            all_passed = False
    
    print("="*80)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("🚀 QuickNode endpoints are ready for THE OVERMIND PROTOCOL!")
        print("💡 You can now enable live trading with confidence")
    else:
        print("⚠️ SOME TESTS FAILED!")
        print("🔧 Please check the endpoints and try again")
        print("📞 Contact QuickNode support if issues persist")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
