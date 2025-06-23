#!/usr/bin/env python3
"""THE OVERMIND PROTOCOL - Simple QuickNode Test
Simple test script using basic libraries to verify QuickNode endpoints.
"""

import json
import time
import urllib.request
import urllib.parse
import urllib.error

# QuickNode Mainnet Endpoints
QUICKNODE_RPC_URL = "https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"

def test_rpc_endpoint():
    """Test the QuickNode RPC endpoint using urllib"""
    print("🔍 Testing QuickNode RPC endpoint...")
    
    try:
        # Test 1: Get version
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getVersion"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            QUICKNODE_RPC_URL,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as response:
            latency = (time.time() - start_time) * 1000
            result = json.loads(response.read().decode('utf-8'))
        
        if "result" in result:
            version = result["result"]
            print(f"✅ RPC Version: {version}")
            print(f"⚡ RPC Latency: {latency:.2f}ms")
        else:
            print(f"❌ RPC Error: {result}")
            return False
        
        # Test 2: Get slot
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "getSlot"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            QUICKNODE_RPC_URL,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as response:
            latency = (time.time() - start_time) * 1000
            result = json.loads(response.read().decode('utf-8'))
        
        if "result" in result:
            slot = result["result"]
            print(f"✅ Current Slot: {slot}")
            print(f"⚡ Slot Query Latency: {latency:.2f}ms")
        else:
            print(f"❌ Slot Error: {result}")
            return False
        
        # Test 3: Get recent blockhash
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "getLatestBlockhash"
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            QUICKNODE_RPC_URL,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=30) as response:
            latency = (time.time() - start_time) * 1000
            result = json.loads(response.read().decode('utf-8'))
        
        if "result" in result:
            blockhash = result["result"]["value"]["blockhash"]
            print(f"✅ Latest Blockhash: {blockhash[:16]}...")
            print(f"⚡ Blockhash Query Latency: {latency:.2f}ms")
        else:
            print(f"❌ Blockhash Error: {result}")
            return False
        
        print("✅ RPC endpoint test completed successfully")
        return True
        
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ RPC endpoint test failed: {e}")
        return False

def test_performance_metrics():
    """Test performance metrics of the endpoint"""
    print("🔍 Testing performance metrics...")
    
    try:
        latencies = []
        
        for i in range(5):  # Reduced to 5 requests for faster testing
            payload = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "getSlot"
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                QUICKNODE_RPC_URL,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            start_time = time.time()
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    latency = (time.time() - start_time) * 1000
                    result = json.loads(response.read().decode('utf-8'))
                
                if "result" in result:
                    latencies.append(latency)
                    print(f"   Request {i+1}: {latency:.2f}ms")
                else:
                    print(f"⚠️ Request {i+1} failed: {result}")
            except Exception as e:
                print(f"⚠️ Request {i+1} error: {e}")
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"📊 Performance Metrics:")
            print(f"   Average Latency: {avg_latency:.2f}ms")
            print(f"   Min Latency: {min_latency:.2f}ms")
            print(f"   Max Latency: {max_latency:.2f}ms")
            print(f"   Successful Requests: {len(latencies)}/5")
            
            # Performance assessment
            if avg_latency < 50:
                print("🚀 EXCELLENT: Ultra-low latency suitable for HFT")
            elif avg_latency < 100:
                print("✅ GOOD: Low latency suitable for trading")
            elif avg_latency < 200:
                print("⚠️ MODERATE: Acceptable for most trading strategies")
            else:
                print("🐌 HIGH: May not be suitable for latency-sensitive strategies")
            
            return True
        else:
            print("❌ No successful requests for performance testing")
            return False
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 THE OVERMIND PROTOCOL - QuickNode Endpoints Testing")
    print("🎯 Testing production-ready Solana mainnet endpoints")
    
    print("\n" + "="*80)
    print("QUICKNODE MAINNET ENDPOINTS TESTING")
    print("="*80)
    print(f"RPC URL: {QUICKNODE_RPC_URL}")
    print("="*80)
    
    # Test results
    results = {}
    
    # Test 1: RPC Endpoint
    print("\n🔍 TEST 1: RPC Endpoint")
    print("-" * 40)
    results["rpc"] = test_rpc_endpoint()
    
    # Test 2: Performance Metrics
    print("\n🔍 TEST 2: Performance Metrics")
    print("-" * 40)
    results["performance"] = test_performance_metrics()
    
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
        print("")
        print("📋 NEXT STEPS:")
        print("1. Update SNIPER_TRADING_MODE=live in .env.overmind")
        print("2. Configure your Solana wallet private key")
        print("3. Set appropriate position sizes and risk limits")
        print("4. Deploy THE OVERMIND PROTOCOL to production")
    else:
        print("⚠️ SOME TESTS FAILED!")
        print("🔧 Please check the endpoints and try again")
        print("📞 Contact QuickNode support if issues persist")
    
    print("="*80)

if __name__ == "__main__":
    main()
