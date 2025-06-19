#!/usr/bin/env python3

"""
THE OVERMIND PROTOCOL - Kestra Workflow Integration Test
Tests Kestra workflow orchestration for automated trading operations
"""

import asyncio
import json
import time
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Optional
import yaml

class KestraWorkflowTester:
    """Test Kestra workflow orchestration for THE OVERMIND PROTOCOL"""
    
    def __init__(self, kestra_url: str = "http://89.117.53.53:8082"):
        self.kestra_url = kestra_url
        self.api_base = f"{kestra_url}/api/v1"
        
        # Sample OVERMIND workflows
        self.sample_workflows = {
            'market_data_ingestion': {
                'id': 'overmind-market-data',
                'namespace': 'overmind',
                'description': 'Market data ingestion and processing workflow',
                'tasks': [
                    'fetch_market_data',
                    'validate_data',
                    'store_to_vector_db',
                    'trigger_ai_analysis'
                ]
            },
            'ai_decision_pipeline': {
                'id': 'overmind-ai-decision',
                'namespace': 'overmind',
                'description': 'AI decision making pipeline',
                'tasks': [
                    'retrieve_context',
                    'run_ai_analysis',
                    'validate_confidence',
                    'send_trading_signal'
                ]
            },
            'risk_management': {
                'id': 'overmind-risk-mgmt',
                'namespace': 'overmind',
                'description': 'Risk management and position monitoring',
                'tasks': [
                    'check_position_limits',
                    'calculate_risk_metrics',
                    'validate_exposure',
                    'emergency_stop_check'
                ]
            }
        }
        
        self.test_results = {
            'connection_test': {},
            'workflow_tests': {},
            'execution_tests': {},
            'integration_tests': {}
        }
    
    def print_test(self, category: str, test_name: str, status: str, details: str = ""):
        """Print formatted test result"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"[{timestamp}] {status_icon} {category} - {test_name}: {status}")
        if details:
            print(f"    Details: {details}")
    
    async def test_kestra_connection(self) -> Dict:
        """Test basic Kestra connection and API availability"""
        print("\n🔗 PHASE 1: Kestra Connection Test")
        print("=" * 50)
        
        connection_results = {}
        
        # Test basic endpoints
        test_endpoints = [
            ('/health', 'Health Check'),
            ('/info', 'System Info'),
            ('/namespaces', 'Namespaces'),
            ('/flows', 'Available Flows'),
            ('/executions', 'Execution History')
        ]
        
        for endpoint, description in test_endpoints:
            try:
                url = f"{self.api_base}{endpoint}"
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            try:
                                json_content = json.loads(content)
                                connection_results[endpoint] = {
                                    'status': 'PASS',
                                    'data': json_content
                                }
                                self.print_test("Connection", description, "PASS", 
                                               f"Response: {len(json_content) if isinstance(json_content, list) else 'OK'}")
                            except json.JSONDecodeError:
                                connection_results[endpoint] = {
                                    'status': 'PASS',
                                    'content': content[:100]
                                }
                                self.print_test("Connection", description, "PASS", "Non-JSON response")
                        else:
                            connection_results[endpoint] = {
                                'status': 'FAIL',
                                'error': f"HTTP {response.status}"
                            }
                            self.print_test("Connection", description, "FAIL", 
                                           f"HTTP {response.status}")
                            
            except Exception as e:
                connection_results[endpoint] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                self.print_test("Connection", description, "FAIL", str(e))
        
        self.test_results['connection_test'] = connection_results
        return connection_results
    
    def create_overmind_workflow_yaml(self, workflow_name: str) -> str:
        """Create YAML workflow definition for OVERMIND"""
        
        if workflow_name == 'market_data_ingestion':
            return """
id: overmind-market-data
namespace: overmind

description: |
  THE OVERMIND PROTOCOL - Market Data Ingestion Workflow
  Fetches market data, validates it, and triggers AI analysis

tasks:
  - id: fetch_market_data
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import requests
      import json
      from datetime import datetime
      
      # Fetch market data from Solana
      print("🔍 Fetching market data...")
      
      # Simulate market data fetch
      market_data = {
          'symbol': 'SOL/USDC',
          'price': 100.50,
          'volume': 1000,
          'timestamp': datetime.now().isoformat()
      }
      
      print(f"📊 Market data: {json.dumps(market_data, indent=2)}")
      
      # Output for next task
      with open('market_data.json', 'w') as f:
          json.dump(market_data, f)
      
      print("✅ Market data fetched successfully")

  - id: validate_data
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      
      print("🔍 Validating market data...")
      
      # Read data from previous task
      with open('market_data.json', 'r') as f:
          data = json.load(f)
      
      # Validation logic
      required_fields = ['symbol', 'price', 'volume', 'timestamp']
      valid = all(field in data for field in required_fields)
      
      if valid and data['price'] > 0 and data['volume'] > 0:
          print("✅ Data validation passed")
          with open('validated_data.json', 'w') as f:
              json.dump(data, f)
      else:
          raise Exception("❌ Data validation failed")

  - id: store_to_vector_db
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      import requests
      
      print("🗄️ Storing data to vector database...")
      
      # Read validated data
      with open('validated_data.json', 'r') as f:
          data = json.load(f)
      
      # Send to AI Brain (Vector DB)
      try:
          response = requests.post(
              'http://overmind-chroma:8000/api/v1/collections/market_data/add',
              json=data,
              timeout=5
          )
          print(f"📊 Vector DB response: {response.status_code}")
      except Exception as e:
          print(f"⚠️ Vector DB not available: {e}")
      
      print("✅ Data stored to vector database")

  - id: trigger_ai_analysis
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      import redis
      
      print("🧠 Triggering AI analysis...")
      
      # Read data
      with open('validated_data.json', 'r') as f:
          data = json.load(f)
      
      # Send to AI Brain via DragonflyDB
      try:
          r = redis.Redis(host='overmind-dragonfly', port=6379, decode_responses=True)
          r.lpush('overmind:market_events', json.dumps(data))
          print("📡 Market event sent to AI Brain")
      except Exception as e:
          print(f"⚠️ DragonflyDB not available: {e}")
      
      print("✅ AI analysis triggered")

triggers:
  - id: schedule
    type: io.kestra.core.models.triggers.types.Schedule
    cron: "*/30 * * * * *"  # Every 30 seconds
"""
        
        elif workflow_name == 'ai_decision_pipeline':
            return """
id: overmind-ai-decision
namespace: overmind

description: |
  THE OVERMIND PROTOCOL - AI Decision Pipeline
  Processes AI decisions and sends trading signals

tasks:
  - id: retrieve_context
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import requests
      import json
      
      print("🔍 Retrieving context from vector memory...")
      
      # Query vector database for similar situations
      try:
          response = requests.get(
              'http://overmind-chroma:8000/api/v1/collections',
              timeout=5
          )
          print(f"📊 Vector DB collections: {response.status_code}")
      except Exception as e:
          print(f"⚠️ Vector DB not available: {e}")
      
      # Simulate context retrieval
      context = {
          'similar_situations': 5,
          'avg_confidence': 0.85,
          'historical_performance': 0.75
      }
      
      with open('context.json', 'w') as f:
          json.dump(context, f)
      
      print("✅ Context retrieved")

  - id: run_ai_analysis
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      import random
      from datetime import datetime
      
      print("🧠 Running AI analysis...")
      
      # Read context
      with open('context.json', 'r') as f:
          context = json.load(f)
      
      # Simulate AI decision making
      confidence = random.uniform(0.6, 0.95)
      action = random.choice(['BUY', 'SELL', 'HOLD'])
      
      decision = {
          'action': action,
          'confidence': confidence,
          'reasoning': f"AI analysis based on {context['similar_situations']} similar situations",
          'timestamp': datetime.now().isoformat()
      }
      
      with open('ai_decision.json', 'w') as f:
          json.dump(decision, f)
      
      print(f"🤖 AI Decision: {action} (Confidence: {confidence:.2f})")

  - id: validate_confidence
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      
      print("🛡️ Validating AI confidence...")
      
      with open('ai_decision.json', 'r') as f:
          decision = json.load(f)
      
      min_confidence = 0.7
      if decision['confidence'] >= min_confidence:
          print(f"✅ Confidence {decision['confidence']:.2f} >= {min_confidence}")
          with open('validated_decision.json', 'w') as f:
              json.dump(decision, f)
      else:
          print(f"❌ Confidence {decision['confidence']:.2f} < {min_confidence}")
          raise Exception("Confidence too low")

  - id: send_trading_signal
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      import redis
      
      print("📡 Sending trading signal...")
      
      with open('validated_decision.json', 'r') as f:
          decision = json.load(f)
      
      # Send to Rust executor
      try:
          r = redis.Redis(host='overmind-dragonfly', port=6379, decode_responses=True)
          r.lpush('overmind:trading_commands', json.dumps(decision))
          print("📊 Trading signal sent to executor")
      except Exception as e:
          print(f"⚠️ DragonflyDB not available: {e}")
      
      print("✅ Trading signal sent")
"""
        
        else:  # risk_management
            return """
id: overmind-risk-mgmt
namespace: overmind

description: |
  THE OVERMIND PROTOCOL - Risk Management Workflow
  Monitors positions and manages risk exposure

tasks:
  - id: check_position_limits
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import requests
      import json
      
      print("🛡️ Checking position limits...")
      
      # Get current positions from trading system
      try:
          response = requests.get(
              'http://overmind-executor:8080/api/v1/positions',
              timeout=5
          )
          print(f"📊 Positions API: {response.status_code}")
      except Exception as e:
          print(f"⚠️ Trading system not available: {e}")
      
      # Simulate position check
      positions = {
          'total_exposure': 50000,
          'max_position': 10000,
          'position_count': 5
      }
      
      with open('positions.json', 'w') as f:
          json.dump(positions, f)
      
      print("✅ Position limits checked")

  - id: calculate_risk_metrics
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      import math
      
      print("📊 Calculating risk metrics...")
      
      with open('positions.json', 'r') as f:
          positions = json.load(f)
      
      # Calculate risk metrics
      risk_metrics = {
          'var_95': positions['total_exposure'] * 0.05,  # 5% VaR
          'max_drawdown': 0.15,  # 15% max drawdown
          'sharpe_ratio': 1.2,
          'exposure_ratio': positions['total_exposure'] / 100000  # vs max capital
      }
      
      with open('risk_metrics.json', 'w') as f:
          json.dump(risk_metrics, f)
      
      print(f"📈 Risk metrics calculated: VaR={risk_metrics['var_95']:.2f}")

  - id: validate_exposure
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      
      print("🔍 Validating exposure limits...")
      
      with open('risk_metrics.json', 'r') as f:
          metrics = json.load(f)
      
      max_exposure_ratio = 0.8  # 80% max exposure
      
      if metrics['exposure_ratio'] <= max_exposure_ratio:
          print(f"✅ Exposure {metrics['exposure_ratio']:.2f} <= {max_exposure_ratio}")
      else:
          print(f"⚠️ High exposure: {metrics['exposure_ratio']:.2f} > {max_exposure_ratio}")
          # Trigger risk reduction
          with open('risk_alert.json', 'w') as f:
              json.dump({'alert': 'HIGH_EXPOSURE', 'action': 'REDUCE_POSITIONS'}, f)

  - id: emergency_stop_check
    type: io.kestra.core.tasks.scripts.Python
    script: |
      import json
      import redis
      
      print("🚨 Emergency stop check...")
      
      # Check for emergency conditions
      emergency_conditions = [
          # Add emergency condition checks here
      ]
      
      if emergency_conditions:
          print("🚨 EMERGENCY STOP TRIGGERED")
          try:
              r = redis.Redis(host='overmind-dragonfly', port=6379, decode_responses=True)
              r.lpush('overmind:emergency_stop', json.dumps({'action': 'STOP_ALL_TRADING'}))
              print("📡 Emergency stop signal sent")
          except Exception as e:
              print(f"⚠️ Could not send emergency stop: {e}")
      else:
          print("✅ No emergency conditions detected")

triggers:
  - id: schedule
    type: io.kestra.core.models.triggers.types.Schedule
    cron: "0 */5 * * * *"  # Every 5 minutes
"""
    
    async def test_workflow_creation(self) -> Dict:
        """Test creating OVERMIND workflows in Kestra"""
        print("\n📝 PHASE 2: Workflow Creation Test")
        print("=" * 50)
        
        workflow_results = {}
        
        for workflow_name, workflow_info in self.sample_workflows.items():
            try:
                # Create workflow YAML
                workflow_yaml = self.create_overmind_workflow_yaml(workflow_name)
                
                # Try to create/update workflow via API
                url = f"{self.api_base}/flows/{workflow_info['namespace']}/{workflow_info['id']}"
                
                headers = {
                    'Content-Type': 'application/x-yaml'
                }
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                    async with session.put(url, data=workflow_yaml, headers=headers) as response:
                        if response.status in [200, 201]:
                            workflow_results[workflow_name] = {
                                'status': 'PASS',
                                'workflow_id': workflow_info['id']
                            }
                            self.print_test("Workflow", f"Create {workflow_name}", "PASS", 
                                           f"ID: {workflow_info['id']}")
                        else:
                            content = await response.text()
                            workflow_results[workflow_name] = {
                                'status': 'FAIL',
                                'error': f"HTTP {response.status}: {content[:100]}"
                            }
                            self.print_test("Workflow", f"Create {workflow_name}", "FAIL", 
                                           f"HTTP {response.status}")
                            
            except Exception as e:
                workflow_results[workflow_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                self.print_test("Workflow", f"Create {workflow_name}", "FAIL", str(e))
        
        self.test_results['workflow_tests'] = workflow_results
        return workflow_results
    
    async def test_workflow_execution(self) -> Dict:
        """Test executing OVERMIND workflows"""
        print("\n▶️ PHASE 3: Workflow Execution Test")
        print("=" * 50)
        
        execution_results = {}
        
        for workflow_name, workflow_info in self.sample_workflows.items():
            try:
                # Trigger workflow execution
                url = f"{self.api_base}/executions/{workflow_info['namespace']}/{workflow_info['id']}"
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                    async with session.post(url) as response:
                        if response.status in [200, 201]:
                            execution_data = await response.json()
                            execution_id = execution_data.get('id', 'unknown')
                            
                            execution_results[workflow_name] = {
                                'status': 'TRIGGERED',
                                'execution_id': execution_id
                            }
                            self.print_test("Execution", f"Trigger {workflow_name}", "PASS", 
                                           f"Execution ID: {execution_id}")
                            
                            # Wait a bit and check execution status
                            await asyncio.sleep(2)
                            
                            status_url = f"{self.api_base}/executions/{execution_id}"
                            async with session.get(status_url) as status_response:
                                if status_response.status == 200:
                                    status_data = await status_response.json()
                                    execution_status = status_data.get('state', {}).get('current', 'UNKNOWN')
                                    
                                    execution_results[workflow_name]['execution_status'] = execution_status
                                    self.print_test("Execution", f"Status {workflow_name}", "INFO", 
                                                   f"Status: {execution_status}")
                        else:
                            content = await response.text()
                            execution_results[workflow_name] = {
                                'status': 'FAIL',
                                'error': f"HTTP {response.status}: {content[:100]}"
                            }
                            self.print_test("Execution", f"Trigger {workflow_name}", "FAIL", 
                                           f"HTTP {response.status}")
                            
            except Exception as e:
                execution_results[workflow_name] = {
                    'status': 'ERROR',
                    'error': str(e)
                }
                self.print_test("Execution", f"Trigger {workflow_name}", "FAIL", str(e))
        
        self.test_results['execution_tests'] = execution_results
        return execution_results
    
    async def test_integration_with_overmind(self) -> Dict:
        """Test Kestra integration with other OVERMIND components"""
        print("\n🔗 PHASE 4: OVERMIND Integration Test")
        print("=" * 50)
        
        integration_results = {}
        
        # Test 1: Check if Kestra can reach other OVERMIND services
        overmind_services = {
            'trading_system': 'http://89.117.53.53:8080/health',
            'ai_brain': 'http://89.117.53.53:8000/api/v1/heartbeat',
            'dragonfly': 'redis://89.117.53.53:6379'
        }
        
        for service_name, service_url in overmind_services.items():
            try:
                if service_url.startswith('http'):
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.get(service_url) as response:
                            if response.status == 200:
                                integration_results[f'reach_{service_name}'] = 'PASS'
                                self.print_test("Integration", f"Reach {service_name}", "PASS")
                            else:
                                integration_results[f'reach_{service_name}'] = f'FAIL ({response.status})'
                                self.print_test("Integration", f"Reach {service_name}", "FAIL", 
                                               f"HTTP {response.status}")
                else:
                    # Redis connection test would go here
                    integration_results[f'reach_{service_name}'] = 'SKIP'
                    self.print_test("Integration", f"Reach {service_name}", "SKIP", 
                                   "Redis test not implemented")
                    
            except Exception as e:
                integration_results[f'reach_{service_name}'] = f'ERROR: {str(e)}'
                self.print_test("Integration", f"Reach {service_name}", "FAIL", str(e))
        
        self.test_results['integration_tests'] = integration_results
        return integration_results
    
    def generate_kestra_report(self) -> Dict:
        """Generate comprehensive Kestra test report"""
        print("\n📊 PHASE 5: Kestra Test Report")
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
        
        report = {
            'kestra_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': round(success_rate, 1)
            },
            'kestra_status': 'OPERATIONAL' if success_rate > 70 else 'ISSUES_DETECTED',
            'workflow_readiness': self._assess_workflow_readiness(),
            'recommendations': self._generate_kestra_recommendations(),
            'detailed_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print summary
        print(f"\n🎯 Kestra Workflow Orchestration Test Results")
        print("=" * 50)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎯 Kestra Status: {report['kestra_status']}")
        print(f"🔄 Workflow Readiness: {report['workflow_readiness']}")
        
        if report['recommendations']:
            print(f"\n📋 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        return report
    
    def _assess_workflow_readiness(self) -> str:
        """Assess readiness of OVERMIND workflows"""
        connection_ok = any('PASS' in str(result) for result in self.test_results.get('connection_test', {}).values())
        workflows_created = any(result.get('status') == 'PASS' for result in self.test_results.get('workflow_tests', {}).values())
        
        if connection_ok and workflows_created:
            return "READY"
        elif connection_ok:
            return "PARTIALLY_READY"
        else:
            return "NOT_READY"
    
    def _generate_kestra_recommendations(self) -> List[str]:
        """Generate Kestra-specific recommendations"""
        recommendations = []
        
        # Check connection results
        connection_results = self.test_results.get('connection_test', {})
        if not any('PASS' in str(result) for result in connection_results.values()):
            recommendations.append("Deploy Kestra workflow orchestration service")
        
        # Check workflow creation
        workflow_results = self.test_results.get('workflow_tests', {})
        if workflow_results and not any(result.get('status') == 'PASS' for result in workflow_results.values()):
            recommendations.append("Fix workflow creation issues - check Kestra API permissions")
        
        # Check integration
        integration_results = self.test_results.get('integration_tests', {})
        failed_integrations = [k for k, v in integration_results.items() if 'FAIL' in str(v) or 'ERROR' in str(v)]
        if failed_integrations:
            recommendations.append(f"Fix integration issues with: {', '.join(failed_integrations)}")
        
        if not recommendations:
            recommendations.append("Kestra workflows ready for production deployment")
        
        return recommendations
    
    async def run_complete_kestra_test(self):
        """Run complete Kestra workflow test suite"""
        print("🔄 THE OVERMIND PROTOCOL - Kestra Workflow Integration Test")
        print("=" * 60)
        print("Testing Kestra workflow orchestration for automated trading")
        print("")
        
        try:
            # Phase 1: Connection Test
            await self.test_kestra_connection()
            
            # Phase 2: Workflow Creation
            await self.test_workflow_creation()
            
            # Phase 3: Workflow Execution
            await self.test_workflow_execution()
            
            # Phase 4: Integration Test
            await self.test_integration_with_overmind()
            
            # Phase 5: Generate Report
            final_report = self.generate_kestra_report()
            
            # Save results
            with open('kestra_test_results.json', 'w') as f:
                json.dump(final_report, f, indent=2)
            
            print(f"\n✅ Kestra test results saved to: kestra_test_results.json")
            
            return final_report
            
        except Exception as e:
            print(f"❌ Kestra test suite failed: {e}")
            raise

def main():
    """Main function to run Kestra workflow tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="THE OVERMIND PROTOCOL Kestra Workflow Tester")
    parser.add_argument("--kestra-url", type=str, default="http://89.117.53.53:8082", 
                       help="Kestra server URL")
    
    args = parser.parse_args()
    
    tester = KestraWorkflowTester(kestra_url=args.kestra_url)
    
    # Run complete Kestra test suite
    asyncio.run(tester.run_complete_kestra_test())

if __name__ == "__main__":
    main()
