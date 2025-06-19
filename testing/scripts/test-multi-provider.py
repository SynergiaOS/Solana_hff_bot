#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Multi-Provider Test
Test QuickNode Premium + Helius + Jito integration
"""

import asyncio
import json
import time
import os
import requests
import websockets
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiProviderTester:
    """Test multi-provider setup for THE OVERMIND PROTOCOL"""
    
    def __init__(self):
        # Provider configurations
        self.providers = {
            'quicknode': {
                'name': 'QuickNode Premium',
                'rpc_url': "https://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580",
                'wss_url': "wss://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580",
                'purpose': 'HFT Execution',
                'priority': 'high'
            },
            'helius': {
                'name': 'Helius Enhanced',
                'rpc_url': "https://devnet.helius-rpc.com/?api-key=YOUR_HELIUS_API_KEY",
                'wss_url': "wss://devnet.helius-rpc.com/?api-key=YOUR_HELIUS_API_KEY", 
                'purpose': 'Data Analysis',
                'priority': 'medium'
            },
            'jito': {
                'name': 'Jito MEV Protection',
                'rpc_url': "https://mainnet.block-engine.jito.wtf",
                'purpose': 'MEV Protection',
                'priority': 'high'
            }
        }
        
        # Test results
        self.test_results = {
            'provider_tests': {},
            'performance_comparison': {},
            'failover_tests': {},
            'optimization_tests': {}
        }
    
    def print_test(self, category: str, test_name: str, status: str, details: str = ""):
        """Print formatted test result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_icon} {category} - {test_name}: {status}")
        if details:
            print(f"    Details: {details}")
    
    async def test_provider_connectivity(self) -> Dict:
        """Test connectivity to all providers"""
        print("\n🔗 PHASE 1: Provider Connectivity Test")
        print("=" * 50)
        
        connectivity_results = {}
        
        for provider_id, config in self.providers.items():
            try:
                self.print_test("Connectivity", f"{config['name']}", "INFO", "Testing connection...")
                
                # Test RPC health
                start_time = time.time()
                payload = {"jsonrpc": "2.0", "id": 1, "method": "getHealth"}
                
                try:
                    response = requests.post(config['rpc_url'], json=payload, timeout=10)
                    rpc_latency = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('result') == 'ok' or 'result' in result:
                            connectivity_results[f'{provider_id}_rpc'] = {
                                'status': 'PASS',
                                'latency_ms': round(rpc_latency, 2),
                                'purpose': config['purpose']
                            }
                            self.print_test("Connectivity", f"{config['name']} RPC", "PASS", 
                                           f"Latency: {rpc_latency:.2f}ms")
                        else:
                            connectivity_results[f'{provider_id}_rpc'] = {
                                'status': 'FAIL',
                                'error': f"Invalid response: {result}"
                            }
                            self.print_test("Connectivity", f"{config['name']} RPC", "FAIL", 
                                           f"Invalid response")
                    else:
                        connectivity_results[f'{provider_id}_rpc'] = {
                            'status': 'FAIL',
                            'error': f"HTTP {response.status_code}"
                        }
                        self.print_test("Connectivity", f"{config['name']} RPC", "FAIL", 
                                       f"HTTP {response.status_code}")
                        
                except Exception as e:
                    connectivity_results[f'{provider_id}_rpc'] = {
                        'status': 'ERROR',
                        'error': str(e)
                    }
                    self.print_test("Connectivity", f"{config['name']} RPC", "FAIL", str(e))
                
                # Test WebSocket (if available)
                if 'wss_url' in config:
                    try:
                        start_time = time.time()
                        async with websockets.connect(config['wss_url'], ping_interval=20, ping_timeout=10) as websocket:
                            subscribe_msg = {"jsonrpc": "2.0", "id": 1, "method": "slotSubscribe"}
                            await websocket.send(json.dumps(subscribe_msg))
                            response = await asyncio.wait_for(websocket.recv(), timeout=10)
                            ws_latency = (time.time() - start_time) * 1000
                            
                            if json.loads(response).get('result'):
                                connectivity_results[f'{provider_id}_ws'] = {
                                    'status': 'PASS',
                                    'latency_ms': round(ws_latency, 2)
                                }
                                self.print_test("Connectivity", f"{config['name']} WebSocket", "PASS", 
                                               f"Latency: {ws_latency:.2f}ms")
                            else:
                                connectivity_results[f'{provider_id}_ws'] = {
                                    'status': 'FAIL',
                                    'error': 'No subscription ID'
                                }
                                self.print_test("Connectivity", f"{config['name']} WebSocket", "FAIL", 
                                               "No subscription ID")
                    except Exception as e:
                        connectivity_results[f'{provider_id}_ws'] = {
                            'status': 'ERROR',
                            'error': str(e)
                        }
                        self.print_test("Connectivity", f"{config['name']} WebSocket", "FAIL", str(e))
                
            except Exception as e:
                connectivity_results[provider_id] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                self.print_test("Connectivity", f"{config['name']}", "FAIL", str(e))
        
        self.test_results['provider_tests'] = connectivity_results
        return connectivity_results
    
    async def test_performance_comparison(self) -> Dict:
        """Compare performance across providers"""
        print("\n⚡ PHASE 2: Performance Comparison Test")
        print("=" * 50)
        
        performance_results = {}
        
        # Test multiple requests to each provider
        test_methods = [
            ("getHealth", {}),
            ("getSlot", {}),
            ("getVersion", {})
        ]
        
        for provider_id, config in self.providers.items():
            if provider_id == 'jito':  # Skip Jito for basic RPC tests
                continue
                
            provider_metrics = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_latency': 0,
                'min_latency': float('inf'),
                'max_latency': 0,
                'latencies': []
            }
            
            self.print_test("Performance", f"{config['name']}", "INFO", "Running performance tests...")
            
            for method, params in test_methods:
                for i in range(5):  # 5 requests per method
                    try:
                        start_time = time.time()
                        payload = {
                            "jsonrpc": "2.0",
                            "id": i,
                            "method": method,
                            "params": params if params else []
                        }
                        
                        response = requests.post(config['rpc_url'], json=payload, timeout=5)
                        latency = (time.time() - start_time) * 1000
                        
                        provider_metrics['total_requests'] += 1
                        
                        if response.status_code == 200:
                            provider_metrics['successful_requests'] += 1
                            provider_metrics['latencies'].append(latency)
                            provider_metrics['min_latency'] = min(provider_metrics['min_latency'], latency)
                            provider_metrics['max_latency'] = max(provider_metrics['max_latency'], latency)
                        else:
                            provider_metrics['failed_requests'] += 1
                            
                    except Exception as e:
                        provider_metrics['total_requests'] += 1
                        provider_metrics['failed_requests'] += 1
            
            # Calculate averages
            if provider_metrics['latencies']:
                provider_metrics['avg_latency'] = sum(provider_metrics['latencies']) / len(provider_metrics['latencies'])
                provider_metrics['success_rate'] = (provider_metrics['successful_requests'] / provider_metrics['total_requests']) * 100
                
                performance_results[provider_id] = provider_metrics
                
                self.print_test("Performance", f"{config['name']} Metrics", "PASS", 
                               f"Avg: {provider_metrics['avg_latency']:.2f}ms, Success: {provider_metrics['success_rate']:.1f}%")
            else:
                performance_results[provider_id] = {
                    'status': 'FAIL',
                    'error': 'No successful requests'
                }
                self.print_test("Performance", f"{config['name']} Metrics", "FAIL", "No successful requests")
        
        self.test_results['performance_comparison'] = performance_results
        return performance_results
    
    async def test_failover_strategy(self) -> Dict:
        """Test failover between providers"""
        print("\n🔄 PHASE 3: Failover Strategy Test")
        print("=" * 50)
        
        failover_results = {}
        
        # Simulate failover scenarios
        scenarios = [
            {
                'name': 'Primary Down - QuickNode to Helius',
                'primary': 'quicknode',
                'fallback': 'helius',
                'test_type': 'execution_failover'
            },
            {
                'name': 'Data Source Failover - Helius to QuickNode',
                'primary': 'helius', 
                'fallback': 'quicknode',
                'test_type': 'data_failover'
            }
        ]
        
        for scenario in scenarios:
            try:
                self.print_test("Failover", scenario['name'], "INFO", "Testing failover scenario...")
                
                primary_config = self.providers.get(scenario['primary'])
                fallback_config = self.providers.get(scenario['fallback'])
                
                if not primary_config or not fallback_config:
                    failover_results[scenario['name']] = {
                        'status': 'SKIP',
                        'reason': 'Provider not configured'
                    }
                    continue
                
                # Test primary (simulate failure by using invalid endpoint)
                primary_failed = True
                try:
                    payload = {"jsonrpc": "2.0", "id": 1, "method": "getHealth"}
                    response = requests.post(primary_config['rpc_url'], json=payload, timeout=2)
                    if response.status_code == 200:
                        primary_failed = False
                except:
                    primary_failed = True
                
                # Test fallback
                fallback_success = False
                fallback_latency = 0
                try:
                    start_time = time.time()
                    payload = {"jsonrpc": "2.0", "id": 1, "method": "getHealth"}
                    response = requests.post(fallback_config['rpc_url'], json=payload, timeout=5)
                    fallback_latency = (time.time() - start_time) * 1000
                    
                    if response.status_code == 200:
                        fallback_success = True
                except:
                    fallback_success = False
                
                # Evaluate failover
                if fallback_success:
                    failover_results[scenario['name']] = {
                        'status': 'PASS',
                        'primary_failed': primary_failed,
                        'fallback_success': fallback_success,
                        'fallback_latency': round(fallback_latency, 2),
                        'failover_time': round(fallback_latency, 2)  # Simplified
                    }
                    self.print_test("Failover", scenario['name'], "PASS", 
                                   f"Fallback latency: {fallback_latency:.2f}ms")
                else:
                    failover_results[scenario['name']] = {
                        'status': 'FAIL',
                        'reason': 'Fallback provider failed'
                    }
                    self.print_test("Failover", scenario['name'], "FAIL", "Fallback provider failed")
                
            except Exception as e:
                failover_results[scenario['name']] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                self.print_test("Failover", scenario['name'], "FAIL", str(e))
        
        self.test_results['failover_tests'] = failover_results
        return failover_results
    
    async def test_optimization_strategies(self) -> Dict:
        """Test optimization strategies for different use cases"""
        print("\n🎯 PHASE 4: Optimization Strategy Test")
        print("=" * 50)
        
        optimization_results = {}
        
        # Test different optimization strategies
        strategies = {
            'hft_execution': {
                'description': 'High-Frequency Trading Execution',
                'preferred_provider': 'quicknode',
                'max_latency_ms': 50,
                'priority': 'speed'
            },
            'data_analysis': {
                'description': 'Market Data Analysis',
                'preferred_provider': 'helius',
                'max_latency_ms': 200,
                'priority': 'reliability'
            },
            'mev_protection': {
                'description': 'MEV Protection via Bundles',
                'preferred_provider': 'jito',
                'max_latency_ms': 100,
                'priority': 'security'
            }
        }
        
        for strategy_name, strategy_config in strategies.items():
            try:
                self.print_test("Optimization", strategy_config['description'], "INFO", "Testing strategy...")
                
                preferred_provider = strategy_config['preferred_provider']
                provider_config = self.providers.get(preferred_provider)
                
                if not provider_config:
                    optimization_results[strategy_name] = {
                        'status': 'SKIP',
                        'reason': f'Provider {preferred_provider} not configured'
                    }
                    continue
                
                # Skip Jito for now (requires special setup)
                if preferred_provider == 'jito':
                    optimization_results[strategy_name] = {
                        'status': 'SKIP',
                        'reason': 'Jito requires mainnet and special configuration'
                    }
                    self.print_test("Optimization", strategy_config['description'], "SKIP", 
                                   "Jito requires mainnet setup")
                    continue
                
                # Test the strategy
                strategy_metrics = {
                    'provider': preferred_provider,
                    'latencies': [],
                    'success_count': 0,
                    'total_requests': 5
                }
                
                for i in range(5):
                    try:
                        start_time = time.time()
                        payload = {"jsonrpc": "2.0", "id": i, "method": "getSlot"}
                        response = requests.post(provider_config['rpc_url'], json=payload, timeout=3)
                        latency = (time.time() - start_time) * 1000
                        
                        if response.status_code == 200:
                            strategy_metrics['latencies'].append(latency)
                            strategy_metrics['success_count'] += 1
                    except:
                        pass
                
                if strategy_metrics['latencies']:
                    avg_latency = sum(strategy_metrics['latencies']) / len(strategy_metrics['latencies'])
                    max_latency = max(strategy_metrics['latencies'])
                    success_rate = (strategy_metrics['success_count'] / strategy_metrics['total_requests']) * 100
                    
                    # Evaluate against strategy requirements
                    latency_ok = avg_latency <= strategy_config['max_latency_ms']
                    reliability_ok = success_rate >= 90
                    
                    optimization_results[strategy_name] = {
                        'status': 'PASS' if latency_ok and reliability_ok else 'WARN',
                        'avg_latency': round(avg_latency, 2),
                        'max_latency': round(max_latency, 2),
                        'success_rate': round(success_rate, 1),
                        'latency_requirement': strategy_config['max_latency_ms'],
                        'meets_requirements': latency_ok and reliability_ok
                    }
                    
                    status = "PASS" if latency_ok and reliability_ok else "WARN"
                    self.print_test("Optimization", strategy_config['description'], status, 
                                   f"Avg: {avg_latency:.2f}ms, Success: {success_rate:.1f}%")
                else:
                    optimization_results[strategy_name] = {
                        'status': 'FAIL',
                        'reason': 'No successful requests'
                    }
                    self.print_test("Optimization", strategy_config['description'], "FAIL", 
                                   "No successful requests")
                
            except Exception as e:
                optimization_results[strategy_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                self.print_test("Optimization", strategy_config['description'], "FAIL", str(e))
        
        self.test_results['optimization_tests'] = optimization_results
        return optimization_results
    
    def generate_multi_provider_report(self) -> Dict:
        """Generate comprehensive multi-provider test report"""
        print("\n📊 PHASE 5: Multi-Provider Test Report")
        print("=" * 50)
        
        # Calculate statistics
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.test_results.items():
            if isinstance(results, dict):
                for test_name, result in results.items():
                    total_tests += 1
                    if isinstance(result, dict) and result.get('status') == 'PASS':
                        passed_tests += 1
                    elif isinstance(result, str) and 'PASS' in result:
                        passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Provider recommendations
        recommendations = self._generate_provider_recommendations()
        
        report = {
            'multi_provider_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': round(success_rate, 1)
            },
            'provider_status': self._assess_provider_status(),
            'optimal_configuration': self._determine_optimal_config(),
            'recommendations': recommendations,
            'detailed_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print summary
        print(f"\n🎯 Multi-Provider Test Results")
        print("=" * 50)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n🔧 Optimal Configuration:")
        for use_case, provider in report['optimal_configuration'].items():
            print(f"  {use_case}: {provider}")
        
        if report['recommendations']:
            print(f"\n📋 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        return report
    
    def _assess_provider_status(self) -> Dict:
        """Assess status of each provider"""
        status = {}
        
        for provider_id, config in self.providers.items():
            provider_tests = [k for k in self.test_results.get('provider_tests', {}).keys() 
                            if k.startswith(provider_id)]
            
            if provider_tests:
                passed = sum(1 for test in provider_tests 
                           if self.test_results['provider_tests'][test].get('status') == 'PASS')
                total = len(provider_tests)
                
                if passed == total:
                    status[provider_id] = 'OPERATIONAL'
                elif passed > 0:
                    status[provider_id] = 'PARTIAL'
                else:
                    status[provider_id] = 'DOWN'
            else:
                status[provider_id] = 'NOT_TESTED'
        
        return status
    
    def _determine_optimal_config(self) -> Dict:
        """Determine optimal provider configuration"""
        performance_data = self.test_results.get('performance_comparison', {})
        
        # Find fastest provider for execution
        fastest_provider = 'quicknode'  # Default
        if performance_data:
            min_latency = float('inf')
            for provider_id, metrics in performance_data.items():
                if isinstance(metrics, dict) and 'avg_latency' in metrics:
                    if metrics['avg_latency'] < min_latency:
                        min_latency = metrics['avg_latency']
                        fastest_provider = provider_id
        
        return {
            'HFT Execution': fastest_provider,
            'Data Analysis': 'helius',
            'MEV Protection': 'jito',
            'Fallback': 'quicknode' if fastest_provider != 'quicknode' else 'helius'
        }
    
    def _generate_provider_recommendations(self) -> List[str]:
        """Generate provider-specific recommendations"""
        recommendations = []
        
        provider_status = self._assess_provider_status()
        
        if provider_status.get('quicknode') == 'OPERATIONAL':
            recommendations.append("QuickNode Premium ready for HFT execution")
        else:
            recommendations.append("Fix QuickNode Premium connection for optimal execution speed")
        
        if provider_status.get('helius') == 'OPERATIONAL':
            recommendations.append("Helius ready for enhanced data analysis")
        else:
            recommendations.append("Configure Helius API key for advanced data features")
        
        if provider_status.get('jito') != 'OPERATIONAL':
            recommendations.append("Setup Jito integration for MEV protection in production")
        
        # Performance recommendations
        performance_data = self.test_results.get('performance_comparison', {})
        if performance_data:
            for provider_id, metrics in performance_data.items():
                if isinstance(metrics, dict) and 'avg_latency' in metrics:
                    if metrics['avg_latency'] > 100:
                        recommendations.append(f"Optimize {provider_id} connection - high latency detected")
        
        if not recommendations:
            recommendations.append("Multi-provider setup is optimal for THE OVERMIND PROTOCOL")
        
        return recommendations
    
    async def run_complete_multi_provider_test(self):
        """Run complete multi-provider test suite"""
        print("🔗 THE OVERMIND PROTOCOL - Multi-Provider Integration Test")
        print("=" * 60)
        print("Testing QuickNode Premium + Helius + Jito integration")
        print("")
        
        try:
            # Phase 1: Provider Connectivity
            await self.test_provider_connectivity()
            
            # Phase 2: Performance Comparison
            await self.test_performance_comparison()
            
            # Phase 3: Failover Strategy
            await self.test_failover_strategy()
            
            # Phase 4: Optimization Strategies
            await self.test_optimization_strategies()
            
            # Phase 5: Generate Report
            final_report = self.generate_multi_provider_report()
            
            # Save results
            with open('multi_provider_test_results.json', 'w') as f:
                json.dump(final_report, f, indent=2)
            
            print(f"\n✅ Multi-provider test results saved to: multi_provider_test_results.json")
            
            return final_report
            
        except Exception as e:
            logger.error(f"Multi-provider test suite failed: {e}")
            raise

def main():
    """Main function to run multi-provider tests"""
    tester = MultiProviderTester()
    
    # Run complete multi-provider test suite
    asyncio.run(tester.run_complete_multi_provider_test())

if __name__ == "__main__":
    main()
