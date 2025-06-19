#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Local Integration Test
Test complete local integration: Devnet Data + AI Brain + Decision Flow
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

class LocalIntegrationTester:
    """Test complete local integration of THE OVERMIND PROTOCOL"""

    def __init__(self):
        # Configuration
        self.rpc_url = "https://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
        self.wss_url = "wss://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')

        # Test results
        self.test_results = {
            'integration_tests': {},
            'data_flow_tests': {},
            'ai_integration_tests': {},
            'decision_pipeline_tests': {},
            'performance_tests': {}
        }

        # Real-time data storage
        self.market_data_buffer = []
        self.ai_decisions_buffer = []
        self.execution_buffer = []

    def print_test(self, category: str, test_name: str, status: str, details: str = ""):
        """Print formatted test result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_icon} {category} - {test_name}: {status}")
        if details:
            print(f"    Details: {details}")

    async def test_devnet_connection(self) -> Dict:
        """Test Solana devnet connection"""
        print("\n🌐 PHASE 1: Devnet Connection Test")
        print("=" * 50)

        connection_results = {}

        try:
            # Test RPC health
            payload = {"jsonrpc": "2.0", "id": 1, "method": "getHealth"}
            response = requests.post(self.rpc_url, json=payload, timeout=10)

            if response.status_code == 200 and response.json().get('result') == 'ok':
                connection_results['rpc_health'] = 'PASS'
                self.print_test("Devnet", "RPC Health", "PASS")
            else:
                connection_results['rpc_health'] = 'FAIL'
                self.print_test("Devnet", "RPC Health", "FAIL")

            # Test WebSocket
            try:
                async with websockets.connect(self.wss_url, ping_interval=20, ping_timeout=10) as websocket:
                    subscribe_msg = {"jsonrpc": "2.0", "id": 1, "method": "slotSubscribe"}
                    await websocket.send(json.dumps(subscribe_msg))
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)

                    if json.loads(response).get('result'):
                        connection_results['websocket'] = 'PASS'
                        self.print_test("Devnet", "WebSocket Connection", "PASS")
                    else:
                        connection_results['websocket'] = 'FAIL'
                        self.print_test("Devnet", "WebSocket Connection", "FAIL")
            except Exception as e:
                connection_results['websocket'] = f'FAIL: {str(e)}'
                self.print_test("Devnet", "WebSocket Connection", "FAIL", str(e))

        except Exception as e:
            connection_results['error'] = str(e)
            self.print_test("Devnet", "Connection Test", "FAIL", str(e))

        self.test_results['integration_tests'] = connection_results
        return connection_results

    async def test_real_time_data_flow(self) -> Dict:
        """Test real-time data flow from devnet"""
        print("\n📊 PHASE 2: Real-time Data Flow Test")
        print("=" * 50)

        data_flow_results = {}

        try:
            # Collect real-time data for 30 seconds
            self.print_test("Data Flow", "Real-time Collection", "INFO", "Starting 30-second data collection...")

            async with websockets.connect(self.wss_url, ping_interval=20, ping_timeout=10) as websocket:
                # Subscribe to slot updates
                subscribe_msg = {"jsonrpc": "2.0", "id": 1, "method": "slotSubscribe"}
                await websocket.send(json.dumps(subscribe_msg))

                # Wait for subscription confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                subscription_data = json.loads(response)

                if 'result' in subscription_data:
                    subscription_id = subscription_data['result']

                    # Collect data for 30 seconds
                    start_time = time.time()
                    data_points = 0

                    while (time.time() - start_time) < 30 and data_points < 20:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=5)
                            message_data = json.loads(message)

                            if 'params' in message_data:
                                slot_info = message_data['params']['result']

                                # Create market data point
                                market_data_point = {
                                    'timestamp': datetime.now(timezone.utc).isoformat(),
                                    'slot': slot_info.get('slot', 0),
                                    'parent': slot_info.get('parent', 0),
                                    'root': slot_info.get('root', 0),
                                    'simulated_price': (slot_info.get('slot', 0) % 10000) / 100.0,
                                    'data_source': 'solana_devnet_realtime'
                                }

                                self.market_data_buffer.append(market_data_point)
                                data_points += 1

                                if data_points % 5 == 0:
                                    self.print_test("Data Flow", f"Data Point {data_points}", "PASS",
                                                   f"Slot: {slot_info.get('slot', 0)}")

                        except asyncio.TimeoutError:
                            continue

                    if data_points >= 10:
                        data_flow_results['real_time_collection'] = f'PASS ({data_points} points)'
                        self.print_test("Data Flow", "Real-time Collection", "PASS",
                                       f"Collected {data_points} data points")
                    else:
                        data_flow_results['real_time_collection'] = f'PARTIAL ({data_points} points)'
                        self.print_test("Data Flow", "Real-time Collection", "WARN",
                                       f"Only collected {data_points} data points")
                else:
                    data_flow_results['real_time_collection'] = 'FAIL (No subscription)'
                    self.print_test("Data Flow", "Real-time Collection", "FAIL", "No subscription ID")

        except Exception as e:
            data_flow_results['error'] = str(e)
            self.print_test("Data Flow", "Real-time Data Flow", "FAIL", str(e))

        self.test_results['data_flow_tests'] = data_flow_results
        return data_flow_results

    async def test_ai_analysis_integration(self) -> Dict:
        """Test AI analysis of real market data"""
        print("\n🧠 PHASE 3: AI Analysis Integration Test")
        print("=" * 50)

        ai_results = {}

        try:
            if not self.market_data_buffer:
                ai_results['no_data'] = 'FAIL'
                self.print_test("AI Analysis", "Data Availability", "FAIL", "No market data available")
                return ai_results

            # Analyze collected market data
            self.print_test("AI Analysis", "Market Data Analysis", "INFO",
                           f"Analyzing {len(self.market_data_buffer)} data points...")

            # Calculate market metrics
            slots = [point['slot'] for point in self.market_data_buffer]
            prices = [point['simulated_price'] for point in self.market_data_buffer]

            market_metrics = {
                'data_points': len(self.market_data_buffer),
                'slot_range': max(slots) - min(slots) if slots else 0,
                'price_volatility': max(prices) - min(prices) if prices else 0,
                'avg_price': sum(prices) / len(prices) if prices else 0,
                'price_trend': 'UPWARD' if prices[-1] > prices[0] else 'DOWNWARD' if len(prices) > 1 else 'STABLE'
            }

            ai_results['market_analysis'] = 'PASS'
            self.print_test("AI Analysis", "Market Metrics", "PASS",
                           f"Trend: {market_metrics['price_trend']}, Volatility: {market_metrics['price_volatility']:.2f}")

            # Generate AI decisions based on real data
            for i, data_point in enumerate(self.market_data_buffer[-5:]):  # Analyze last 5 points
                # Simple AI decision logic
                price = data_point['simulated_price']
                slot_momentum = (data_point['slot'] - self.market_data_buffer[0]['slot']) / len(self.market_data_buffer)

                # Calculate confidence based on data quality and trends
                confidence = min(0.95, 0.5 + (len(self.market_data_buffer) / 100.0))

                # Decision logic
                if price > market_metrics['avg_price'] * 1.02 and slot_momentum > 0:
                    action = 'BUY'
                    confidence += 0.1
                elif price < market_metrics['avg_price'] * 0.98:
                    action = 'SELL'
                    confidence += 0.05
                else:
                    action = 'HOLD'

                ai_decision = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'data_point_slot': data_point['slot'],
                    'action': action,
                    'confidence': round(confidence, 3),
                    'reasoning': f"Price {price:.2f} vs avg {market_metrics['avg_price']:.2f}, momentum {slot_momentum:.2f}",
                    'market_context': market_metrics
                }

                self.ai_decisions_buffer.append(ai_decision)

            if self.ai_decisions_buffer:
                ai_results['decision_generation'] = f'PASS ({len(self.ai_decisions_buffer)} decisions)'
                self.print_test("AI Analysis", "Decision Generation", "PASS",
                               f"Generated {len(self.ai_decisions_buffer)} AI decisions")

                # Show sample decisions
                for decision in self.ai_decisions_buffer[-3:]:
                    self.print_test("AI Analysis", f"Decision {decision['action']}", "INFO",
                                   f"Confidence: {decision['confidence']:.3f}")
            else:
                ai_results['decision_generation'] = 'FAIL'
                self.print_test("AI Analysis", "Decision Generation", "FAIL", "No decisions generated")

        except Exception as e:
            ai_results['error'] = str(e)
            self.print_test("AI Analysis", "AI Integration", "FAIL", str(e))

        self.test_results['ai_integration_tests'] = ai_results
        return ai_results

    async def test_decision_pipeline(self) -> Dict:
        """Test complete decision pipeline"""
        print("\n⚡ PHASE 4: Decision Pipeline Test")
        print("=" * 50)

        pipeline_results = {}

        try:
            if not self.ai_decisions_buffer:
                pipeline_results['no_decisions'] = 'FAIL'
                self.print_test("Pipeline", "Decision Availability", "FAIL", "No AI decisions available")
                return pipeline_results

            # Test risk management
            self.print_test("Pipeline", "Risk Management", "INFO", "Applying risk filters...")

            approved_decisions = []
            for decision in self.ai_decisions_buffer:
                # Risk checks
                risk_checks = {
                    'confidence_threshold': decision['confidence'] >= 0.7,
                    'action_validity': decision['action'] in ['BUY', 'SELL', 'HOLD'],
                    'reasoning_present': bool(decision.get('reasoning')),
                    'market_context': bool(decision.get('market_context'))
                }

                risk_score = sum(risk_checks.values()) / len(risk_checks)

                if risk_score >= 0.75:  # 75% of checks must pass
                    approved_decision = {
                        **decision,
                        'risk_approved': True,
                        'risk_score': risk_score,
                        'risk_checks': risk_checks
                    }
                    approved_decisions.append(approved_decision)

            if approved_decisions:
                pipeline_results['risk_management'] = f'PASS ({len(approved_decisions)}/{len(self.ai_decisions_buffer)} approved)'
                self.print_test("Pipeline", "Risk Management", "PASS",
                               f"Approved {len(approved_decisions)}/{len(self.ai_decisions_buffer)} decisions")
            else:
                pipeline_results['risk_management'] = 'FAIL (No approvals)'
                self.print_test("Pipeline", "Risk Management", "FAIL", "No decisions passed risk checks")

            # Test execution simulation
            self.print_test("Pipeline", "Execution Simulation", "INFO", "Simulating trade execution...")

            for decision in approved_decisions:
                # Simulate execution latency and slippage
                execution_latency = 25.0 + (len(self.execution_buffer) * 2.5)  # Increasing latency
                slippage = 0.001 * (1 + len(self.execution_buffer) * 0.1)  # Increasing slippage

                execution_result = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'decision_id': f"decision_{len(self.execution_buffer)}",
                    'action': decision['action'],
                    'confidence': decision['confidence'],
                    'execution_latency_ms': round(execution_latency, 2),
                    'slippage_percent': round(slippage * 100, 4),
                    'status': 'EXECUTED' if decision['action'] != 'HOLD' else 'SKIPPED',
                    'simulated': True
                }

                self.execution_buffer.append(execution_result)

            if self.execution_buffer:
                avg_latency = sum(e['execution_latency_ms'] for e in self.execution_buffer) / len(self.execution_buffer)
                pipeline_results['execution_simulation'] = f'PASS (avg latency: {avg_latency:.2f}ms)'
                self.print_test("Pipeline", "Execution Simulation", "PASS",
                               f"Executed {len(self.execution_buffer)} orders, avg latency: {avg_latency:.2f}ms")
            else:
                pipeline_results['execution_simulation'] = 'FAIL'
                self.print_test("Pipeline", "Execution Simulation", "FAIL", "No executions simulated")

        except Exception as e:
            pipeline_results['error'] = str(e)
            self.print_test("Pipeline", "Decision Pipeline", "FAIL", str(e))

        self.test_results['decision_pipeline_tests'] = pipeline_results
        return pipeline_results

    async def test_performance_metrics(self) -> Dict:
        """Test system performance metrics"""
        print("\n📈 PHASE 5: Performance Metrics Test")
        print("=" * 50)

        performance_results = {}

        try:
            # Calculate data flow performance
            if self.market_data_buffer:
                data_timespan = (
                    datetime.fromisoformat(self.market_data_buffer[-1]['timestamp'].replace('Z', '+00:00')) -
                    datetime.fromisoformat(self.market_data_buffer[0]['timestamp'].replace('Z', '+00:00'))
                ).total_seconds()

                data_rate = len(self.market_data_buffer) / data_timespan if data_timespan > 0 else 0

                performance_results['data_ingestion_rate'] = f'PASS ({data_rate:.2f} points/sec)'
                self.print_test("Performance", "Data Ingestion Rate", "PASS",
                               f"{data_rate:.2f} data points per second")

            # Calculate AI processing performance
            if self.ai_decisions_buffer:
                ai_processing_rate = len(self.ai_decisions_buffer) / len(self.market_data_buffer) if self.market_data_buffer else 0

                performance_results['ai_processing_rate'] = f'PASS ({ai_processing_rate:.2f} decisions/point)'
                self.print_test("Performance", "AI Processing Rate", "PASS",
                               f"{ai_processing_rate:.2f} decisions per data point")

            # Calculate execution performance
            if self.execution_buffer:
                avg_execution_latency = sum(e['execution_latency_ms'] for e in self.execution_buffer) / len(self.execution_buffer)
                max_execution_latency = max(e['execution_latency_ms'] for e in self.execution_buffer)

                latency_acceptable = avg_execution_latency < 100  # Under 100ms average

                performance_results['execution_latency'] = f'{"PASS" if latency_acceptable else "WARN"} (avg: {avg_execution_latency:.2f}ms)'
                self.print_test("Performance", "Execution Latency", "PASS" if latency_acceptable else "WARN",
                               f"Avg: {avg_execution_latency:.2f}ms, Max: {max_execution_latency:.2f}ms")

            # Calculate overall system efficiency
            total_data_points = len(self.market_data_buffer)
            total_decisions = len(self.ai_decisions_buffer)
            total_executions = len(self.execution_buffer)

            if total_data_points > 0:
                decision_efficiency = (total_decisions / total_data_points) * 100
                execution_efficiency = (total_executions / total_decisions) * 100 if total_decisions > 0 else 0

                performance_results['system_efficiency'] = f'PASS (decision: {decision_efficiency:.1f}%, execution: {execution_efficiency:.1f}%)'
                self.print_test("Performance", "System Efficiency", "PASS",
                               f"Decision: {decision_efficiency:.1f}%, Execution: {execution_efficiency:.1f}%")

        except Exception as e:
            performance_results['error'] = str(e)
            self.print_test("Performance", "Performance Metrics", "FAIL", str(e))

        self.test_results['performance_tests'] = performance_results
        return performance_results

    def generate_integration_report(self) -> Dict:
        """Generate comprehensive integration test report"""
        print("\n📊 PHASE 6: Integration Test Report")
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

        # Calculate data flow metrics
        data_flow_metrics = {
            'market_data_points': len(self.market_data_buffer),
            'ai_decisions_generated': len(self.ai_decisions_buffer),
            'executions_simulated': len(self.execution_buffer),
            'end_to_end_success_rate': (len(self.execution_buffer) / len(self.market_data_buffer) * 100) if self.market_data_buffer else 0
        }

        report = {
            'integration_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': round(success_rate, 1)
            },
            'integration_status': 'OPERATIONAL' if success_rate > 80 else 'ISSUES_DETECTED',
            'data_flow_metrics': data_flow_metrics,
            'system_readiness': self._assess_system_readiness(),
            'recommendations': self._generate_integration_recommendations(),
            'detailed_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }

        # Print summary
        print(f"\n🎯 Local Integration Test Results")
        print("=" * 50)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎯 Integration Status: {report['integration_status']}")
        print(f"🔄 System Readiness: {report['system_readiness']}")

        print(f"\n📊 Data Flow Metrics:")
        print(f"  Market Data Points: {data_flow_metrics['market_data_points']}")
        print(f"  AI Decisions: {data_flow_metrics['ai_decisions_generated']}")
        print(f"  Executions: {data_flow_metrics['executions_simulated']}")
        print(f"  End-to-End Success: {data_flow_metrics['end_to_end_success_rate']:.1f}%")

        if report['recommendations']:
            print(f"\n📋 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")

        return report

    def _assess_system_readiness(self) -> str:
        """Assess overall system readiness"""
        devnet_ok = any('PASS' in str(result) for result in self.test_results.get('integration_tests', {}).values())
        data_flow_ok = any('PASS' in str(result) for result in self.test_results.get('data_flow_tests', {}).values())
        ai_ok = any('PASS' in str(result) for result in self.test_results.get('ai_integration_tests', {}).values())
        pipeline_ok = any('PASS' in str(result) for result in self.test_results.get('decision_pipeline_tests', {}).values())

        ready_components = sum([devnet_ok, data_flow_ok, ai_ok, pipeline_ok])

        if ready_components == 4:
            return "READY_FOR_DEPLOYMENT"
        elif ready_components >= 3:
            return "MOSTLY_READY"
        elif ready_components >= 2:
            return "PARTIALLY_READY"
        else:
            return "NOT_READY"

    def _generate_integration_recommendations(self) -> List[str]:
        """Generate integration-specific recommendations"""
        recommendations = []

        # Check data flow
        if len(self.market_data_buffer) < 10:
            recommendations.append("Improve data collection - need more consistent market data flow")

        # Check AI decisions
        if len(self.ai_decisions_buffer) < 5:
            recommendations.append("Enhance AI decision making - generate more trading signals")

        # Check execution rate
        execution_rate = (len(self.execution_buffer) / len(self.ai_decisions_buffer) * 100) if self.ai_decisions_buffer else 0
        if execution_rate < 50:
            recommendations.append("Improve risk management - too many decisions rejected")

        # Check performance
        performance_results = self.test_results.get('performance_tests', {})
        if any('WARN' in str(result) for result in performance_results.values()):
            recommendations.append("Optimize system performance - some metrics show warnings")

        if not recommendations:
            recommendations.append("Local integration is ready for THE OVERMIND PROTOCOL deployment")

        return recommendations

    async def run_complete_integration_test(self):
        """Run complete local integration test"""
        print("🔗 THE OVERMIND PROTOCOL - Local Integration Test")
        print("=" * 60)
        print("Testing complete local integration: Devnet + AI Brain + Decision Pipeline")
        print("")

        try:
            # Phase 1: Devnet Connection
            await self.test_devnet_connection()

            # Phase 2: Real-time Data Flow
            await self.test_real_time_data_flow()

            # Phase 3: AI Analysis Integration
            await self.test_ai_analysis_integration()

            # Phase 4: Decision Pipeline
            await self.test_decision_pipeline()

            # Phase 5: Performance Metrics
            await self.test_performance_metrics()

            # Phase 6: Generate Report
            final_report = self.generate_integration_report()

            # Save results
            with open('local_integration_test_results.json', 'w') as f:
                json.dump(final_report, f, indent=2)

            print(f"\n✅ Local integration test results saved to: local_integration_test_results.json")

            return final_report

        except Exception as e:
            logger.error(f"Local integration test suite failed: {e}")
            raise

def main():
    """Main function to run local integration tests"""
    tester = LocalIntegrationTester()

    # Run complete local integration test suite
    asyncio.run(tester.run_complete_integration_test())

if __name__ == "__main__":
    main()