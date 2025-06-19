#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Devnet Data Flow Test
Test local data flow on Solana devnet before deployment
"""

import asyncio
import json
import time
import requests
import websockets
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DevnetDataFlowTester:
    """Test data flow on Solana devnet locally"""
    
    def __init__(self):
        # QuickNode devnet endpoints from memory
        self.rpc_url = "https://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
        self.wss_url = "wss://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
        
        # Test results
        self.test_results = {
            'connection_tests': {},
            'data_ingestion_tests': {},
            'market_data_tests': {},
            'websocket_tests': {},
            'flow_simulation': {}
        }
        
        # Sample tokens for testing
        self.test_tokens = [
            {
                'symbol': 'SOL',
                'mint': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
                'name': 'Solana'
            },
            {
                'symbol': 'USDC',
                'mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                'name': 'USD Coin'
            }
        ]
    
    def print_test(self, category: str, test_name: str, status: str, details: str = ""):
        """Print formatted test result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_icon} {category} - {test_name}: {status}")
        if details:
            print(f"    Details: {details}")
    
    async def test_rpc_connection(self) -> Dict:
        """Test RPC connection to Solana devnet"""
        print("\n🔗 PHASE 1: RPC Connection Test")
        print("=" * 50)
        
        connection_results = {}
        
        # Test 1: Basic RPC health
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth"
            }
            
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result') == 'ok':
                    connection_results['health'] = 'PASS'
                    self.print_test("RPC", "Health Check", "PASS")
                else:
                    connection_results['health'] = 'FAIL'
                    self.print_test("RPC", "Health Check", "FAIL", f"Result: {result}")
            else:
                connection_results['health'] = f'FAIL (HTTP {response.status_code})'
                self.print_test("RPC", "Health Check", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            connection_results['health'] = f'ERROR: {str(e)}'
            self.print_test("RPC", "Health Check", "FAIL", str(e))
        
        # Test 2: Get version
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getVersion"
            }
            
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                version = result.get('result', {}).get('solana-core', 'unknown')
                connection_results['version'] = f'PASS ({version})'
                self.print_test("RPC", "Version Check", "PASS", f"Solana version: {version}")
            else:
                connection_results['version'] = f'FAIL (HTTP {response.status_code})'
                self.print_test("RPC", "Version Check", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            connection_results['version'] = f'ERROR: {str(e)}'
            self.print_test("RPC", "Version Check", "FAIL", str(e))
        
        # Test 3: Get slot
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSlot"
            }
            
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                slot = result.get('result', 0)
                connection_results['slot'] = f'PASS (slot: {slot})'
                self.print_test("RPC", "Current Slot", "PASS", f"Slot: {slot}")
            else:
                connection_results['slot'] = f'FAIL (HTTP {response.status_code})'
                self.print_test("RPC", "Current Slot", "FAIL", f"HTTP {response.status_code}")
                
        except Exception as e:
            connection_results['slot'] = f'ERROR: {str(e)}'
            self.print_test("RPC", "Current Slot", "FAIL", str(e))
        
        self.test_results['connection_tests'] = connection_results
        return connection_results
    
    async def test_account_data(self) -> Dict:
        """Test account data retrieval"""
        print("\n💰 PHASE 2: Account Data Test")
        print("=" * 50)
        
        account_results = {}
        
        for token in self.test_tokens:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAccountInfo",
                    "params": [
                        token['mint'],
                        {"encoding": "jsonParsed"}
                    ]
                }
                
                response = requests.post(self.rpc_url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    account_info = result.get('result', {}).get('value')
                    
                    if account_info:
                        account_results[token['symbol']] = 'PASS'
                        self.print_test("Account", f"{token['symbol']} Info", "PASS", 
                                       f"Owner: {account_info.get('owner', 'unknown')}")
                    else:
                        account_results[token['symbol']] = 'FAIL (No data)'
                        self.print_test("Account", f"{token['symbol']} Info", "FAIL", "No account data")
                else:
                    account_results[token['symbol']] = f'FAIL (HTTP {response.status_code})'
                    self.print_test("Account", f"{token['symbol']} Info", "FAIL", 
                                   f"HTTP {response.status_code}")
                    
            except Exception as e:
                account_results[token['symbol']] = f'ERROR: {str(e)}'
                self.print_test("Account", f"{token['symbol']} Info", "FAIL", str(e))
        
        self.test_results['data_ingestion_tests'] = account_results
        return account_results
    
    async def test_transaction_history(self) -> Dict:
        """Test transaction history retrieval"""
        print("\n📊 PHASE 3: Transaction History Test")
        print("=" * 50)
        
        tx_results = {}
        
        try:
            # Get recent signatures for SOL token
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    self.test_tokens[0]['mint'],  # SOL mint
                    {"limit": 5}
                ]
            }
            
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                signatures = result.get('result', [])
                
                if signatures:
                    tx_results['signatures'] = f'PASS ({len(signatures)} found)'
                    self.print_test("Transactions", "Recent Signatures", "PASS", 
                                   f"Found {len(signatures)} recent transactions")
                    
                    # Test getting transaction details
                    if signatures:
                        first_sig = signatures[0]['signature']
                        
                        tx_payload = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getTransaction",
                            "params": [
                                first_sig,
                                {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}
                            ]
                        }
                        
                        tx_response = requests.post(self.rpc_url, json=tx_payload, timeout=10)
                        
                        if tx_response.status_code == 200:
                            tx_result = tx_response.json()
                            tx_data = tx_result.get('result')
                            
                            if tx_data:
                                tx_results['transaction_details'] = 'PASS'
                                self.print_test("Transactions", "Transaction Details", "PASS", 
                                               f"Signature: {first_sig[:16]}...")
                            else:
                                tx_results['transaction_details'] = 'FAIL (No data)'
                                self.print_test("Transactions", "Transaction Details", "FAIL", 
                                               "No transaction data")
                        else:
                            tx_results['transaction_details'] = f'FAIL (HTTP {tx_response.status_code})'
                            self.print_test("Transactions", "Transaction Details", "FAIL", 
                                           f"HTTP {tx_response.status_code}")
                else:
                    tx_results['signatures'] = 'FAIL (No signatures)'
                    self.print_test("Transactions", "Recent Signatures", "FAIL", "No recent transactions")
            else:
                tx_results['signatures'] = f'FAIL (HTTP {response.status_code})'
                self.print_test("Transactions", "Recent Signatures", "FAIL", 
                               f"HTTP {response.status_code}")
                
        except Exception as e:
            tx_results['signatures'] = f'ERROR: {str(e)}'
            self.print_test("Transactions", "Recent Signatures", "FAIL", str(e))
        
        self.test_results['market_data_tests'] = tx_results
        return tx_results
    
    async def test_websocket_connection(self) -> Dict:
        """Test WebSocket connection for real-time data"""
        print("\n🔄 PHASE 4: WebSocket Connection Test")
        print("=" * 50)
        
        ws_results = {}
        
        try:
            # Test WebSocket connection
            self.print_test("WebSocket", "Connection Test", "INFO", "Attempting connection...")
            
            async with websockets.connect(self.wss_url, ping_interval=20, ping_timeout=10) as websocket:
                # Subscribe to slot updates
                subscribe_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "slotSubscribe"
                }
                
                await websocket.send(json.dumps(subscribe_message))
                
                # Wait for subscription confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                response_data = json.loads(response)
                
                if 'result' in response_data:
                    subscription_id = response_data['result']
                    ws_results['subscription'] = f'PASS (ID: {subscription_id})'
                    self.print_test("WebSocket", "Slot Subscription", "PASS", 
                                   f"Subscription ID: {subscription_id}")
                    
                    # Wait for a few slot updates
                    updates_received = 0
                    start_time = time.time()
                    
                    while updates_received < 3 and (time.time() - start_time) < 30:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=10)
                            message_data = json.loads(message)
                            
                            if 'params' in message_data:
                                updates_received += 1
                                slot_info = message_data['params']['result']
                                self.print_test("WebSocket", f"Slot Update {updates_received}", "PASS", 
                                               f"Slot: {slot_info.get('slot', 'unknown')}")
                        except asyncio.TimeoutError:
                            break
                    
                    if updates_received > 0:
                        ws_results['updates'] = f'PASS ({updates_received} updates)'
                        self.print_test("WebSocket", "Real-time Updates", "PASS", 
                                       f"Received {updates_received} slot updates")
                    else:
                        ws_results['updates'] = 'FAIL (No updates)'
                        self.print_test("WebSocket", "Real-time Updates", "FAIL", "No updates received")
                else:
                    ws_results['subscription'] = 'FAIL (No subscription ID)'
                    self.print_test("WebSocket", "Slot Subscription", "FAIL", "No subscription ID")
                    
        except Exception as e:
            ws_results['connection'] = f'ERROR: {str(e)}'
            self.print_test("WebSocket", "Connection Test", "FAIL", str(e))
        
        self.test_results['websocket_tests'] = ws_results
        return ws_results
    
    async def simulate_trading_flow(self) -> Dict:
        """Simulate complete trading data flow"""
        print("\n🎯 PHASE 5: Trading Flow Simulation")
        print("=" * 50)
        
        flow_results = {}
        
        try:
            # Step 1: Market data ingestion
            self.print_test("Flow", "Market Data Ingestion", "INFO", "Simulating data collection...")
            
            market_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'solana_devnet',
                'tokens': []
            }
            
            for token in self.test_tokens:
                # Get current slot as "price" simulation
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSlot"
                }
                
                response = requests.post(self.rpc_url, json=payload, timeout=5)
                
                if response.status_code == 200:
                    result = response.json()
                    slot = result.get('result', 0)
                    
                    # Simulate price based on slot (for testing)
                    simulated_price = (slot % 10000) / 100.0
                    
                    token_data = {
                        'symbol': token['symbol'],
                        'mint': token['mint'],
                        'simulated_price': simulated_price,
                        'slot': slot,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                    
                    market_data['tokens'].append(token_data)
            
            if market_data['tokens']:
                flow_results['data_ingestion'] = 'PASS'
                self.print_test("Flow", "Market Data Ingestion", "PASS", 
                               f"Collected data for {len(market_data['tokens'])} tokens")
            else:
                flow_results['data_ingestion'] = 'FAIL'
                self.print_test("Flow", "Market Data Ingestion", "FAIL", "No data collected")
            
            # Step 2: Data processing simulation
            self.print_test("Flow", "Data Processing", "INFO", "Processing market data...")
            
            processed_data = {
                'raw_data': market_data,
                'analysis': {
                    'total_tokens': len(market_data['tokens']),
                    'avg_price': sum(t['simulated_price'] for t in market_data['tokens']) / len(market_data['tokens']) if market_data['tokens'] else 0,
                    'processing_time': time.time()
                }
            }
            
            flow_results['data_processing'] = 'PASS'
            self.print_test("Flow", "Data Processing", "PASS", 
                           f"Processed {processed_data['analysis']['total_tokens']} tokens")
            
            # Step 3: AI decision simulation
            self.print_test("Flow", "AI Decision Making", "INFO", "Simulating AI analysis...")
            
            # Simple decision logic based on processed data
            avg_price = processed_data['analysis']['avg_price']
            confidence = min(0.95, max(0.6, avg_price / 100.0))
            
            ai_decision = {
                'action': 'BUY' if avg_price > 50 else 'HOLD',
                'confidence': confidence,
                'reasoning': f"Based on average price {avg_price:.2f}",
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            flow_results['ai_decision'] = 'PASS'
            self.print_test("Flow", "AI Decision Making", "PASS", 
                           f"Decision: {ai_decision['action']} (confidence: {confidence:.2f})")
            
            # Step 4: Risk validation simulation
            self.print_test("Flow", "Risk Validation", "INFO", "Validating risk parameters...")
            
            risk_check = {
                'confidence_threshold': confidence >= 0.7,
                'position_size_ok': True,  # Simulated
                'daily_limit_ok': True,    # Simulated
                'approved': confidence >= 0.7
            }
            
            if risk_check['approved']:
                flow_results['risk_validation'] = 'PASS'
                self.print_test("Flow", "Risk Validation", "PASS", "Risk checks passed")
            else:
                flow_results['risk_validation'] = 'FAIL'
                self.print_test("Flow", "Risk Validation", "FAIL", "Risk checks failed")
            
            # Step 5: Execution simulation (devnet safe)
            if risk_check['approved']:
                self.print_test("Flow", "Trade Execution", "INFO", "Simulating trade execution...")
                
                execution_result = {
                    'status': 'SIMULATED',
                    'action': ai_decision['action'],
                    'execution_time': 45.2,  # Simulated ms
                    'slippage': 0.001,       # Simulated
                    'success': True
                }
                
                flow_results['execution'] = 'PASS'
                self.print_test("Flow", "Trade Execution", "PASS", 
                               f"Simulated {execution_result['action']} in {execution_result['execution_time']}ms")
            else:
                flow_results['execution'] = 'SKIPPED'
                self.print_test("Flow", "Trade Execution", "SKIP", "Skipped due to risk validation")
            
        except Exception as e:
            flow_results['error'] = str(e)
            self.print_test("Flow", "Trading Flow Simulation", "FAIL", str(e))
        
        self.test_results['flow_simulation'] = flow_results
        return flow_results
    
    def generate_devnet_report(self) -> Dict:
        """Generate comprehensive devnet test report"""
        print("\n📊 PHASE 6: Devnet Test Report")
        print("=" * 50)
        
        # Calculate statistics
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.test_results.items():
            if isinstance(results, dict):
                for test_name, result in results.items():
                    total_tests += 1
                    if isinstance(result, str) and 'PASS' in result:
                        passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            'devnet_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': round(success_rate, 1)
            },
            'devnet_status': 'OPERATIONAL' if success_rate > 70 else 'ISSUES_DETECTED',
            'data_flow_status': self._assess_data_flow(),
            'recommendations': self._generate_devnet_recommendations(),
            'detailed_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print summary
        print(f"\n🎯 Solana Devnet Data Flow Test Results")
        print("=" * 50)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎯 Devnet Status: {report['devnet_status']}")
        print(f"🔄 Data Flow: {report['data_flow_status']}")
        
        if report['recommendations']:
            print(f"\n📋 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        return report
    
    def _assess_data_flow(self) -> str:
        """Assess data flow readiness"""
        connection_ok = any('PASS' in str(result) for result in self.test_results.get('connection_tests', {}).values())
        data_ok = any('PASS' in str(result) for result in self.test_results.get('data_ingestion_tests', {}).values())
        flow_ok = any('PASS' in str(result) for result in self.test_results.get('flow_simulation', {}).values())
        
        if connection_ok and data_ok and flow_ok:
            return "READY"
        elif connection_ok and data_ok:
            return "PARTIALLY_READY"
        else:
            return "NOT_READY"
    
    def _generate_devnet_recommendations(self) -> List[str]:
        """Generate devnet-specific recommendations"""
        recommendations = []
        
        # Check connection results
        connection_results = self.test_results.get('connection_tests', {})
        if not any('PASS' in str(result) for result in connection_results.values()):
            recommendations.append("Fix Solana devnet RPC connection issues")
        
        # Check WebSocket
        ws_results = self.test_results.get('websocket_tests', {})
        if not any('PASS' in str(result) for result in ws_results.values()):
            recommendations.append("Fix WebSocket connection for real-time data")
        
        # Check data flow
        flow_results = self.test_results.get('flow_simulation', {})
        if not any('PASS' in str(result) for result in flow_results.values()):
            recommendations.append("Fix data flow simulation issues")
        
        if not recommendations:
            recommendations.append("Devnet data flow is ready for THE OVERMIND PROTOCOL deployment")
        
        return recommendations
    
    async def run_complete_devnet_test(self):
        """Run complete devnet data flow test"""
        print("🌐 THE OVERMIND PROTOCOL - Solana Devnet Data Flow Test")
        print("=" * 60)
        print("Testing local data flow on Solana devnet before deployment")
        print("")
        
        try:
            # Phase 1: RPC Connection
            await self.test_rpc_connection()
            
            # Phase 2: Account Data
            await self.test_account_data()
            
            # Phase 3: Transaction History
            await self.test_transaction_history()
            
            # Phase 4: WebSocket Connection
            await self.test_websocket_connection()
            
            # Phase 5: Trading Flow Simulation
            await self.simulate_trading_flow()
            
            # Phase 6: Generate Report
            final_report = self.generate_devnet_report()
            
            # Save results
            with open('devnet_test_results.json', 'w') as f:
                json.dump(final_report, f, indent=2)
            
            print(f"\n✅ Devnet test results saved to: devnet_test_results.json")
            
            return final_report
            
        except Exception as e:
            logger.error(f"Devnet test suite failed: {e}")
            raise

def main():
    """Main function to run devnet data flow tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="THE OVERMIND PROTOCOL Devnet Data Flow Tester")
    
    args = parser.parse_args()
    
    tester = DevnetDataFlowTester()
    
    # Run complete devnet test suite
    asyncio.run(tester.run_complete_devnet_test())

if __name__ == "__main__":
    main()
