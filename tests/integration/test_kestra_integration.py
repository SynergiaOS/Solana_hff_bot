#!/usr/bin/env python3
"""
Test Kestra Integration
Test Kestra workflows and configuration without actually starting services
"""

import sys
import os
import yaml
import json
from pathlib import Path

def test_kestra_docker_compose():
    """Test Kestra Docker Compose configuration"""
    print("🐳 Testing Kestra Docker Compose Configuration")
    print("-" * 60)
    
    try:
        compose_file = Path("infrastructure/kestra/docker-compose.kestra.yml")
        
        if not compose_file.exists():
            raise FileNotFoundError(f"Docker Compose file not found: {compose_file}")
        
        with open(compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        print("✅ Docker Compose file loaded successfully")
        
        # Validate services
        required_services = ['kestra-postgres', 'kestra', 'kestra-worker']
        services = compose_config.get('services', {})
        
        for service in required_services:
            if service in services:
                print(f"   ✅ Service '{service}' configured")
            else:
                print(f"   ❌ Service '{service}' missing")
                return False
        
        # Validate networks
        networks = compose_config.get('networks', {})
        if 'overmind-kestra' in networks and 'overmind-network' in networks:
            print("   ✅ Networks configured correctly")
        else:
            print("   ❌ Network configuration incomplete")
            return False
        
        # Validate volumes
        volumes = compose_config.get('volumes', {})
        required_volumes = ['kestra_postgres_data', 'kestra_data', 'kestra_logs']
        
        for volume in required_volumes:
            if volume in volumes:
                print(f"   ✅ Volume '{volume}' configured")
            else:
                print(f"   ❌ Volume '{volume}' missing")
                return False
        
        # Validate Kestra configuration
        kestra_service = services.get('kestra', {})
        kestra_env = kestra_service.get('environment', {})
        
        if 'KESTRA_CONFIGURATION' in kestra_env:
            print("   ✅ Kestra configuration present")
        else:
            print("   ❌ Kestra configuration missing")
            return False
        
        print("✅ Docker Compose configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Docker Compose configuration test failed: {e}")
        return False

def test_historical_backtest_flow():
    """Test Historical Backtest flow configuration"""
    print("\n📊 Testing Historical Backtest Flow")
    print("-" * 60)
    
    try:
        flow_file = Path("infrastructure/kestra/flows/historical-backtest.yml")
        
        if not flow_file.exists():
            raise FileNotFoundError(f"Flow file not found: {flow_file}")
        
        with open(flow_file, 'r') as f:
            flow_config = yaml.safe_load(f)
        
        print("✅ Historical backtest flow loaded successfully")
        
        # Validate flow structure
        required_fields = ['id', 'namespace', 'description', 'inputs', 'tasks']
        for field in required_fields:
            if field in flow_config:
                print(f"   ✅ Field '{field}' present")
            else:
                print(f"   ❌ Field '{field}' missing")
                return False
        
        # Validate flow ID and namespace
        if flow_config['id'] == 'historical-backtest':
            print("   ✅ Flow ID correct")
        else:
            print(f"   ❌ Flow ID incorrect: {flow_config['id']}")
            return False
        
        if flow_config['namespace'] == 'overmind.testing':
            print("   ✅ Namespace correct")
        else:
            print(f"   ❌ Namespace incorrect: {flow_config['namespace']}")
            return False
        
        # Validate inputs
        inputs = flow_config.get('inputs', [])
        required_inputs = ['app_env', 'scenarios', 'notification_email']
        
        input_ids = [inp['id'] for inp in inputs]
        for required_input in required_inputs:
            if required_input in input_ids:
                print(f"   ✅ Input '{required_input}' configured")
            else:
                print(f"   ❌ Input '{required_input}' missing")
                return False
        
        # Validate tasks
        tasks = flow_config.get('tasks', [])
        required_tasks = [
            'setup-environment',
            'validate-configuration', 
            'test-api-connectivity',
            'run-backtest',
            'generate-report',
            'send-notification'
        ]
        
        task_ids = [task['id'] for task in tasks]
        for required_task in required_tasks:
            if required_task in task_ids:
                print(f"   ✅ Task '{required_task}' configured")
            else:
                print(f"   ❌ Task '{required_task}' missing")
                return False
        
        # Validate triggers
        triggers = flow_config.get('triggers', [])
        if triggers:
            print(f"   ✅ Triggers configured: {len(triggers)}")
        else:
            print("   ⚠️ No triggers configured (manual execution only)")
        
        print("✅ Historical backtest flow validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Historical backtest flow test failed: {e}")
        return False

def test_mainnet_paper_trading_flow():
    """Test Mainnet Paper Trading flow configuration"""
    print("\n🚀 Testing Mainnet Paper Trading Flow")
    print("-" * 60)
    
    try:
        flow_file = Path("infrastructure/kestra/flows/mainnet-paper-trading.yml")
        
        if not flow_file.exists():
            raise FileNotFoundError(f"Flow file not found: {flow_file}")
        
        with open(flow_file, 'r') as f:
            flow_config = yaml.safe_load(f)
        
        print("✅ Mainnet paper trading flow loaded successfully")
        
        # Validate flow structure
        if flow_config['id'] == 'mainnet-paper-trading':
            print("   ✅ Flow ID correct")
        else:
            print(f"   ❌ Flow ID incorrect: {flow_config['id']}")
            return False
        
        if flow_config['namespace'] == 'overmind.trading':
            print("   ✅ Namespace correct")
        else:
            print(f"   ❌ Namespace incorrect: {flow_config['namespace']}")
            return False
        
        # Validate safety labels
        labels = flow_config.get('labels', {})
        if labels.get('environment') == 'production' and labels.get('network') == 'mainnet':
            print("   ✅ Safety labels configured correctly")
        else:
            print("   ❌ Safety labels missing or incorrect")
            return False
        
        # Validate inputs
        inputs = flow_config.get('inputs', [])
        required_inputs = ['duration_hours', 'max_position_size', 'monitoring_interval', 'notification_email']
        
        input_ids = [inp['id'] for inp in inputs]
        for required_input in required_inputs:
            if required_input in input_ids:
                print(f"   ✅ Input '{required_input}' configured")
            else:
                print(f"   ❌ Input '{required_input}' missing")
                return False
        
        # Validate critical safety tasks
        tasks = flow_config.get('tasks', [])
        safety_tasks = [
            'preflight-validation',
            'validate-mainnet-config',
            'test-mainnet-apis',
            'health-check'
        ]
        
        task_ids = [task['id'] for task in tasks]
        for safety_task in safety_tasks:
            if safety_task in task_ids:
                print(f"   ✅ Safety task '{safety_task}' configured")
            else:
                print(f"   ❌ Safety task '{safety_task}' missing")
                return False
        
        # Validate no automatic triggers (safety)
        triggers = flow_config.get('triggers', [])
        if not triggers:
            print("   ✅ No automatic triggers (manual execution only - SAFE)")
        else:
            print("   ⚠️ Automatic triggers present - review for safety")
        
        print("✅ Mainnet paper trading flow validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Mainnet paper trading flow test failed: {e}")
        return False

def test_kestra_startup_script():
    """Test Kestra startup script"""
    print("\n🔧 Testing Kestra Startup Script")
    print("-" * 60)
    
    try:
        script_file = Path("scripts/start_kestra.sh")
        
        if not script_file.exists():
            raise FileNotFoundError(f"Startup script not found: {script_file}")
        
        # Check if script is executable
        if os.access(script_file, os.X_OK):
            print("   ✅ Script is executable")
        else:
            print("   ❌ Script is not executable")
            return False
        
        # Read script content
        with open(script_file, 'r') as f:
            script_content = f.read()
        
        print("✅ Startup script loaded successfully")
        
        # Validate script structure
        required_functions = [
            'check_prerequisites',
            'create_network',
            'setup_directories',
            'start_kestra',
            'check_service_health'
        ]
        
        for function in required_functions:
            if function in script_content:
                print(f"   ✅ Function '{function}' present")
            else:
                print(f"   ❌ Function '{function}' missing")
                return False
        
        # Validate commands
        required_commands = ['start', 'stop', 'restart', 'logs', 'status', 'cleanup', 'help']
        
        for command in required_commands:
            if command == 'help':
                # Special case for help command which has multiple patterns
                if '"help"|"-h"|"--help")' in script_content:
                    print(f"   ✅ Command '{command}' implemented")
                else:
                    print(f"   ❌ Command '{command}' missing")
                    return False
            else:
                if f'"{command}")' in script_content:
                    print(f"   ✅ Command '{command}' implemented")
                else:
                    print(f"   ❌ Command '{command}' missing")
                    return False
        
        # Check for safety features
        if 'trap cleanup EXIT' in script_content:
            print("   ✅ Cleanup trap configured")
        else:
            print("   ❌ Cleanup trap missing")
            return False
        
        print("✅ Startup script validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Startup script test failed: {e}")
        return False

def test_flow_integration_with_overmind():
    """Test flow integration with OVERMIND components"""
    print("\n🔗 Testing Flow Integration with OVERMIND")
    print("-" * 60)
    
    try:
        # Test historical backtest flow integration
        flow_file = Path("infrastructure/kestra/flows/historical-backtest.yml")
        with open(flow_file, 'r') as f:
            backtest_flow = yaml.safe_load(f)
        
        # Check environment loader integration
        tasks = backtest_flow.get('tasks', [])
        config_task = None
        
        for task in tasks:
            if task['id'] == 'validate-configuration':
                config_task = task
                break
        
        if config_task and 'environment_loader' in config_task.get('script', ''):
            print("   ✅ Environment loader integration in backtest flow")
        else:
            print("   ❌ Environment loader integration missing")
            return False
        
        # Check historical framework integration
        backtest_task = None
        for task in tasks:
            if task['id'] == 'run-backtest':
                backtest_task = task
                break
        
        if backtest_task and 'HistoricalTestRunner' in backtest_task.get('script', ''):
            print("   ✅ Historical framework integration in backtest flow")
        else:
            print("   ❌ Historical framework integration missing")
            return False
        
        # Test mainnet flow integration
        mainnet_file = Path("infrastructure/kestra/flows/mainnet-paper-trading.yml")
        with open(mainnet_file, 'r') as f:
            mainnet_flow = yaml.safe_load(f)
        
        # Check OVERMIND stack integration
        mainnet_tasks = mainnet_flow.get('tasks', [])
        stack_task = None
        
        for task in mainnet_tasks:
            if task['id'] == 'start-overmind-stack':
                stack_task = task
                break
        
        if stack_task and 'docker-compose.overmind.yml' in str(stack_task.get('commands', [])):
            print("   ✅ OVERMIND stack integration in mainnet flow")
        else:
            print("   ❌ OVERMIND stack integration missing")
            return False
        
        print("✅ Flow integration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Flow integration test failed: {e}")
        return False

def test_kestra_configuration_consistency():
    """Test configuration consistency across Kestra components"""
    print("\n⚙️ Testing Configuration Consistency")
    print("-" * 60)
    
    try:
        # Load all configurations
        compose_file = Path("infrastructure/kestra/docker-compose.kestra.yml")
        with open(compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        backtest_file = Path("infrastructure/kestra/flows/historical-backtest.yml")
        with open(backtest_file, 'r') as f:
            backtest_config = yaml.safe_load(f)
        
        mainnet_file = Path("infrastructure/kestra/flows/mainnet-paper-trading.yml")
        with open(mainnet_file, 'r') as f:
            mainnet_config = yaml.safe_load(f)
        
        print("✅ All configuration files loaded")
        
        # Check namespace consistency
        backtest_namespace = backtest_config.get('namespace')
        mainnet_namespace = mainnet_config.get('namespace')
        
        if backtest_namespace.startswith('overmind.') and mainnet_namespace.startswith('overmind.'):
            print("   ✅ Namespace consistency maintained")
        else:
            print("   ❌ Namespace inconsistency detected")
            return False
        
        # Check network configuration
        networks = compose_config.get('networks', {})
        if 'overmind-network' in networks:
            print("   ✅ OVERMIND network integration configured")
        else:
            print("   ❌ OVERMIND network integration missing")
            return False
        
        # Check workspace mounting
        kestra_service = compose_config.get('services', {}).get('kestra', {})
        volumes = kestra_service.get('volumes', [])
        
        workspace_mounted = any('/workspace' in volume for volume in volumes)
        if workspace_mounted:
            print("   ✅ Workspace mounting configured")
        else:
            print("   ❌ Workspace mounting missing")
            return False
        
        print("✅ Configuration consistency validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration consistency test failed: {e}")
        return False

async def main():
    """Run all Kestra integration tests"""
    print("🚀 THE OVERMIND PROTOCOL - Kestra Integration Tests")
    print("=" * 70)
    print("Testing FAZA 3: Implementacja Kestry jako Orkiestratora")
    print("=" * 70)
    
    # Run all tests
    test1 = test_kestra_docker_compose()
    test2 = test_historical_backtest_flow()
    test3 = test_mainnet_paper_trading_flow()
    test4 = test_kestra_startup_script()
    test5 = test_flow_integration_with_overmind()
    test6 = test_kestra_configuration_consistency()
    
    print("\n" + "=" * 70)
    
    if all([test1, test2, test3, test4, test5, test6]):
        print("🎉 ALL KESTRA INTEGRATION TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • Kestra Docker Compose configuration validated")
        print("   • Historical Backtest flow properly configured")
        print("   • Mainnet Paper Trading flow with safety measures")
        print("   • Startup script with all management commands")
        print("   • Integration with OVERMIND components verified")
        print("   • Configuration consistency maintained")
        print("\n🚀 READY FOR:")
        print("   • Kestra deployment and testing")
        print("   • Automated workflow execution")
        print("   • Professional orchestration of OVERMIND")
        print("\n🎯 FAZA 3 STATUS: KESTRA ORCHESTRATION READY")
        print("   Next: Deploy and test workflows")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix issues")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
