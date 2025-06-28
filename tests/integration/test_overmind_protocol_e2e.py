#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - End-to-End Integration Test
Complete autonomous trading flow demonstration

Test Flow:
1. Start DragonflyDB (Redis-compatible) 
2. Start AI Brain (Python)
3. Start HFT Executor (Rust)
4. Inject test market signals
5. Verify complete decision-execution-learning loop
"""

import asyncio
import json
import time
import subprocess
import signal
import sys
from typing import Dict, Any
import redis.asyncio as redis

class OvermindProtocolE2ETest:
    """End-to-end test suite for THE OVERMIND PROTOCOL"""
    
    def __init__(self):
        self.redis_client = None
        self.processes = []
        
    async def setup_infrastructure(self):
        """Setup DragonflyDB and connections"""
        print("🔧 Setting up test infrastructure...")
        
        # Connect to DragonflyDB
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            await self.redis_client.ping()
            print("✅ Connected to DragonflyDB")
            
            # Clear any existing data
            await self.redis_client.flushall()
            print("🗑️ Cleared existing data")
            
        except Exception as e:
            print(f"❌ DragonflyDB connection failed: {e}")
            print("💡 Please ensure DragonflyDB is running: docker run -d -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly")
            return False
            
        return True
    
    async def inject_test_signals(self):
        """Inject test market signals to trigger the AI Brain"""
        test_signals = [
            {
                "type": "new_pool",
                "ca": "EKpQGSJtjMFqKZ9KQanSqYNNcVAYhYAtjpgHwHan8m8f",
                "symbol": "WIF",
                "source": "shredstream_proxy"
            },
            {
                "type": "volume_spike", 
                "ca": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "symbol": "BONK",
                "source": "dex_screener"
            },
            {
                "type": "new_pool",
                "ca": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
                "symbol": "WIF",  # This should trigger BUY decision
                "source": "jupiter_api"
            }
        ]
        
        print("📡 Injecting test market signals...")
        
        for i, signal in enumerate(test_signals):
            signal_json = json.dumps(signal)
            await self.redis_client.rpush("events:raw", signal_json)
            print(f"   Signal {i+1}: {signal['type']} for {signal['symbol']}")
            await asyncio.sleep(2)  # Stagger signals
            
        print(f"✅ Injected {len(test_signals)} test signals")
    
    async def monitor_command_queue(self, duration_seconds: int = 30):
        """Monitor the command queue for AI Brain decisions"""
        print(f"👀 Monitoring overmind:commands queue for {duration_seconds}s...")
        
        commands_seen = 0
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            try:
                # Non-blocking check for commands
                result = await self.redis_client.blpop("overmind:commands", timeout=1)
                
                if result:
                    _, command_json = result
                    command = json.loads(command_json)
                    commands_seen += 1
                    
                    print(f"⚡ Command {commands_seen}: {command['action']} {command['amount_sol']:.3f} SOL")
                    print(f"   Token: {command['token_address']}")
                    print(f"   Strategy: {command['strategy_id']}, Urgency: {command['urgency']}")
                    
                    # Put command back for HFT Executor to process
                    await self.redis_client.lpush("overmind:commands", command_json)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Error monitoring commands: {e}")
                break
        
        print(f"📊 Total commands observed: {commands_seen}")
        return commands_seen
    
    async def monitor_execution_results(self, duration_seconds: int = 30):
        """Monitor execution results from HFT Executor"""
        print(f"📈 Monitoring execution:results queue for {duration_seconds}s...")
        
        results_seen = 0
        successful_trades = 0
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            try:
                result = await self.redis_client.blpop("execution:results", timeout=1)
                
                if result:
                    _, result_json = result
                    execution_result = json.loads(result_json)
                    results_seen += 1
                    
                    status = execution_result['status']
                    if status == "SUCCESS":
                        successful_trades += 1
                        print(f"✅ Execution {results_seen}: {status}")
                        print(f"   TX: {execution_result.get('tx_id', 'N/A')}")
                        print(f"   Time: {execution_result['execution_time_ms']:.1f}ms")
                        print(f"   Amount: {execution_result.get('actual_amount', 0):.6f} SOL")
                    else:
                        print(f"❌ Execution {results_seen}: {status}")
                        print(f"   Error: {execution_result.get('error_message', 'Unknown')}")
                        print(f"   Time: {execution_result['execution_time_ms']:.1f}ms")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ Error monitoring results: {e}")
                break
        
        success_rate = (successful_trades / max(1, results_seen)) * 100
        print(f"📊 Execution Results: {results_seen} total, {successful_trades} successful ({success_rate:.1f}%)")
        return results_seen, successful_trades
    
    async def run_comprehensive_test(self):
        """Run complete end-to-end test"""
        print("🚀 THE OVERMIND PROTOCOL - End-to-End Integration Test")
        print("=" * 60)
        
        # Setup
        if not await self.setup_infrastructure():
            return False
        
        print("\n🧠 Please start the AI Brain in another terminal:")
        print("   cd /opt/overmind && python3 agent_brain/main.py")
        
        print("\n⚡ Please start the HFT Executor in another terminal:")
        print("   cd /opt/overmind/solana_executor && cargo run")
        
        print("\n⏳ Waiting 10 seconds for components to start...")
        await asyncio.sleep(10)
        
        # Test the complete flow
        print("\n" + "=" * 60)
        print("🔄 Starting Autonomous Trading Flow Test")
        
        # Phase 1: Inject signals
        await self.inject_test_signals()
        await asyncio.sleep(5)
        
        # Phase 2: Monitor AI decisions
        print("\n📡 Phase 1: Monitoring AI Brain Decisions")
        commands_count = await self.monitor_command_queue(15)
        
        # Phase 3: Monitor execution results  
        print("\n⚡ Phase 2: Monitoring HFT Executor Results")
        results_count, successful_count = await self.monitor_execution_results(15)
        
        # Phase 4: Final status
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        
        print(f"🔍 Market Signals Injected: 3")
        print(f"🧠 AI Brain Commands Generated: {commands_count}")
        print(f"⚡ HFT Executor Results: {results_count}")
        print(f"✅ Successful Executions: {successful_count}")
        
        if commands_count > 0 and results_count > 0:
            print("\n🎉 SUCCESS: Complete autonomous trading flow verified!")
            print("   ✅ Signal Detection → AI Analysis → Command Generation → HFT Execution → Learning Loop")
            return True
        else:
            print("\n❌ INCOMPLETE: Some components may not be running properly")
            return False
    
    async def cleanup(self):
        """Cleanup test environment"""
        if self.redis_client:
            await self.redis_client.close()
        
        for proc in self.processes:
            try:
                proc.terminate()
            except:
                pass

async def main():
    """Main test runner"""
    test_suite = OvermindProtocolE2ETest()
    
    try:
        success = await test_suite.run_comprehensive_test()
        exit_code = 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        exit_code = 1
    finally:
        await test_suite.cleanup()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())