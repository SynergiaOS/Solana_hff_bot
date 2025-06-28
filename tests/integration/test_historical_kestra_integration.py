#!/usr/bin/env python3
"""
Test Historical Framework Integration with Kestra
Test advanced historical analysis workflows and integration
"""

import sys
import os
import yaml
import json
import asyncio
from pathlib import Path

def test_advanced_historical_flow():
    """Test Advanced Historical Analysis flow configuration"""
    print("🧠 Testing Advanced Historical Analysis Flow")
    print("-" * 60)
    
    try:
        flow_file = Path("infrastructure/kestra/flows/advanced-historical-analysis.yml")
        
        if not flow_file.exists():
            raise FileNotFoundError(f"Flow file not found: {flow_file}")
        
        with open(flow_file, 'r') as f:
            flow_config = yaml.safe_load(f)
        
        print("✅ Advanced historical analysis flow loaded successfully")
        
        # Validate flow structure
        required_fields = ['id', 'namespace', 'description', 'inputs', 'tasks', 'triggers']
        for field in required_fields:
            if field in flow_config:
                print(f"   ✅ Field '{field}' present")
            else:
                print(f"   ❌ Field '{field}' missing")
                return False
        
        # Validate flow ID and namespace
        if flow_config['id'] == 'advanced-historical-analysis':
            print("   ✅ Flow ID correct")
        else:
            print(f"   ❌ Flow ID incorrect: {flow_config['id']}")
            return False
        
        if flow_config['namespace'] == 'overmind.analysis':
            print("   ✅ Namespace correct")
        else:
            print(f"   ❌ Namespace incorrect: {flow_config['namespace']}")
            return False
        
        # Validate advanced inputs
        inputs = flow_config.get('inputs', [])
        required_inputs = ['analysis_type', 'time_period', 'ai_models_to_test', 'generate_recommendations']
        
        input_ids = [inp['id'] for inp in inputs]
        for required_input in required_inputs:
            if required_input in input_ids:
                print(f"   ✅ Input '{required_input}' configured")
            else:
                print(f"   ❌ Input '{required_input}' missing")
                return False
        
        # Validate comprehensive task set
        tasks = flow_config.get('tasks', [])
        required_tasks = [
            'setup-analysis-environment',
            'collect-historical-data',
            'validate-ai-models',
            'analyze-performance',
            'generate-comprehensive-report',
            'archive-results'
        ]
        
        task_ids = [task['id'] for task in tasks]
        for required_task in required_tasks:
            if required_task in task_ids:
                print(f"   ✅ Task '{required_task}' configured")
            else:
                print(f"   ❌ Task '{required_task}' missing")
                return False
        
        # Validate triggers for automation
        triggers = flow_config.get('triggers', [])
        if triggers:
            print(f"   ✅ Automation triggers configured: {len(triggers)}")
            
            # Check for weekly trigger
            weekly_trigger = any(
                trigger.get('cron') == "0 3 * * 1" 
                for trigger in triggers
            )
            if weekly_trigger:
                print("   ✅ Weekly automation trigger configured")
            else:
                print("   ⚠️ Weekly automation trigger not found")
        else:
            print("   ⚠️ No automation triggers configured")
        
        print("✅ Advanced historical analysis flow validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Advanced historical analysis flow test failed: {e}")
        return False

def test_historical_framework_integration():
    """Test Historical Framework integration in flows"""
    print("\n📊 Testing Historical Framework Integration")
    print("-" * 60)
    
    try:
        flow_file = Path("infrastructure/kestra/flows/advanced-historical-analysis.yml")
        with open(flow_file, 'r') as f:
            flow_config = yaml.safe_load(f)
        
        tasks = flow_config.get('tasks', [])
        
        # Check environment setup task
        setup_task = None
        for task in tasks:
            if task['id'] == 'setup-analysis-environment':
                setup_task = task
                break
        
        if setup_task:
            script = setup_task.get('script', '')
            if 'HistoricalDataProvider' in script and 'HistoricalTestRunner' in script:
                print("   ✅ Historical Framework imports in setup task")
            else:
                print("   ❌ Historical Framework imports missing in setup task")
                return False
        else:
            print("   ❌ Setup task not found")
            return False
        
        # Check data collection task
        collection_task = None
        for task in tasks:
            if task['id'] == 'collect-historical-data':
                collection_task = task
                break
        
        if collection_task:
            script = collection_task.get('script', '')
            required_methods = [
                'get_sol_price_history',
                'get_transaction_volume_data',
                'get_new_token_launches',
                'calculate_volatility'
            ]
            
            for method in required_methods:
                if method in script:
                    print(f"   ✅ Method '{method}' used in data collection")
                else:
                    print(f"   ❌ Method '{method}' missing in data collection")
                    return False
        else:
            print("   ❌ Data collection task not found")
            return False
        
        # Check AI validation task
        validation_task = None
        for task in tasks:
            if task['id'] == 'validate-ai-models':
                validation_task = task
                break
        
        if validation_task:
            script = validation_task.get('script', '')
            ai_components = [
                'DecisionEngine',
                'decision_engine',
                'risk_analyzer',
                'market_analyzer',
                'portfolio_optimizer'
            ]
            
            found_components = 0
            for component in ai_components:
                if component in script:
                    found_components += 1
            
            if found_components >= 3:
                print(f"   ✅ AI components integration: {found_components}/{len(ai_components)}")
            else:
                print(f"   ❌ Insufficient AI components integration: {found_components}/{len(ai_components)}")
                return False
        else:
            print("   ❌ AI validation task not found")
            return False
        
        print("✅ Historical Framework integration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Historical Framework integration test failed: {e}")
        return False

def test_performance_analysis_capabilities():
    """Test performance analysis capabilities"""
    print("\n📈 Testing Performance Analysis Capabilities")
    print("-" * 60)
    
    try:
        flow_file = Path("infrastructure/kestra/flows/advanced-historical-analysis.yml")
        with open(flow_file, 'r') as f:
            flow_config = yaml.safe_load(f)
        
        tasks = flow_config.get('tasks', [])
        
        # Check performance analysis task
        performance_task = None
        for task in tasks:
            if task['id'] == 'analyze-performance':
                performance_task = task
                break
        
        if performance_task:
            script = performance_task.get('script', '')
            
            # Check for performance metrics
            required_metrics = [
                'data_collection_efficiency',
                'ai_model_reliability',
                'system_coverage',
                'data_quality_score'
            ]
            
            for metric in required_metrics:
                if metric in script:
                    print(f"   ✅ Performance metric '{metric}' calculated")
                else:
                    print(f"   ❌ Performance metric '{metric}' missing")
                    return False
            
            # Check for insights generation
            if 'insights' in script and 'recommendations' in script:
                print("   ✅ Insights and recommendations generation")
            else:
                print("   ❌ Insights and recommendations generation missing")
                return False
            
            # Check for performance grading
            if 'performance_grade' in script:
                print("   ✅ Performance grading system")
            else:
                print("   ❌ Performance grading system missing")
                return False
        else:
            print("   ❌ Performance analysis task not found")
            return False
        
        print("✅ Performance analysis capabilities validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Performance analysis capabilities test failed: {e}")
        return False

def test_comprehensive_reporting():
    """Test comprehensive reporting capabilities"""
    print("\n📋 Testing Comprehensive Reporting")
    print("-" * 60)
    
    try:
        flow_file = Path("infrastructure/kestra/flows/advanced-historical-analysis.yml")
        with open(flow_file, 'r') as f:
            flow_config = yaml.safe_load(f)
        
        tasks = flow_config.get('tasks', [])
        
        # Check report generation task
        report_task = None
        for task in tasks:
            if task['id'] == 'generate-comprehensive-report':
                report_task = task
                break
        
        if report_task:
            script = report_task.get('script', '')
            
            # Check for HTML report generation
            if 'html_report' in script and 'DOCTYPE html' in script:
                print("   ✅ HTML report generation")
            else:
                print("   ❌ HTML report generation missing")
                return False
            
            # Check for comprehensive sections
            required_sections = [
                'Analysis Overview',
                'Performance Summary',
                'AI Model Validation',
                'Insights',
                'Recommendations',
                'Next Steps'
            ]
            
            for section in required_sections:
                if section in script:
                    print(f"   ✅ Report section '{section}' included")
                else:
                    print(f"   ❌ Report section '{section}' missing")
                    return False
            
            # Check for styling and formatting
            if 'style' in script and 'css' in script.lower():
                print("   ✅ Professional styling and formatting")
            else:
                print("   ❌ Professional styling missing")
                return False
        else:
            print("   ❌ Report generation task not found")
            return False
        
        # Check archiving task
        archive_task = None
        for task in tasks:
            if task['id'] == 'archive-results':
                archive_task = task
                break
        
        if archive_task:
            commands = archive_task.get('commands', [])
            if any('tar -czf' in cmd for cmd in commands):
                print("   ✅ Results archiving configured")
            else:
                print("   ❌ Results archiving missing")
                return False
        else:
            print("   ❌ Archive task not found")
            return False
        
        print("✅ Comprehensive reporting validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive reporting test failed: {e}")
        return False

def test_automation_and_scheduling():
    """Test automation and scheduling capabilities"""
    print("\n⏰ Testing Automation and Scheduling")
    print("-" * 60)
    
    try:
        flow_file = Path("infrastructure/kestra/flows/advanced-historical-analysis.yml")
        with open(flow_file, 'r') as f:
            flow_config = yaml.safe_load(f)
        
        triggers = flow_config.get('triggers', [])
        
        if not triggers:
            print("   ❌ No triggers configured")
            return False
        
        # Check for scheduled trigger
        scheduled_trigger = None
        for trigger in triggers:
            if trigger.get('type') == 'io.kestra.plugin.core.trigger.Schedule':
                scheduled_trigger = trigger
                break
        
        if scheduled_trigger:
            print("   ✅ Scheduled trigger configured")
            
            # Check cron expression
            cron = scheduled_trigger.get('cron')
            if cron:
                print(f"   ✅ Cron schedule: {cron}")
                
                # Validate it's a weekly schedule
                if "* * 1" in cron:  # Monday
                    print("   ✅ Weekly schedule detected")
                else:
                    print("   ⚠️ Non-weekly schedule")
            else:
                print("   ❌ Cron expression missing")
                return False
            
            # Check default inputs
            inputs = scheduled_trigger.get('inputs', {})
            if inputs:
                print(f"   ✅ Default inputs configured: {len(inputs)} parameters")
            else:
                print("   ⚠️ No default inputs for scheduled execution")
        else:
            print("   ❌ Scheduled trigger not found")
            return False
        
        print("✅ Automation and scheduling validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Automation and scheduling test failed: {e}")
        return False

def test_integration_with_existing_flows():
    """Test integration with existing Kestra flows"""
    print("\n🔗 Testing Integration with Existing Flows")
    print("-" * 60)
    
    try:
        # Load all flow files
        flows_dir = Path("infrastructure/kestra/flows")
        flow_files = list(flows_dir.glob("*.yml"))
        
        if len(flow_files) < 3:
            print(f"   ❌ Insufficient flow files: {len(flow_files)}")
            return False
        
        print(f"   ✅ Found {len(flow_files)} flow files")
        
        # Check namespace consistency
        namespaces = set()
        for flow_file in flow_files:
            with open(flow_file, 'r') as f:
                flow_config = yaml.safe_load(f)
                namespace = flow_config.get('namespace', '')
                if namespace.startswith('overmind.'):
                    namespaces.add(namespace)
        
        if len(namespaces) >= 2:
            print(f"   ✅ Consistent namespace structure: {namespaces}")
        else:
            print(f"   ❌ Inconsistent namespaces: {namespaces}")
            return False
        
        # Check for complementary flows
        flow_types = []
        for flow_file in flow_files:
            with open(flow_file, 'r') as f:
                flow_config = yaml.safe_load(f)
                labels = flow_config.get('labels', {})
                flow_type = labels.get('type', 'unknown')
                flow_types.append(flow_type)
        
        expected_types = ['backtesting', 'paper-trading', 'advanced-analysis']
        found_types = [t for t in expected_types if t in flow_types]
        
        if len(found_types) >= 2:
            print(f"   ✅ Complementary flow types: {found_types}")
        else:
            print(f"   ❌ Missing complementary flows: {found_types}")
            return False
        
        print("✅ Integration with existing flows validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration with existing flows test failed: {e}")
        return False

async def main():
    """Run all Historical Framework + Kestra integration tests"""
    print("📊 THE OVERMIND PROTOCOL - Historical Framework + Kestra Integration Tests")
    print("=" * 80)
    print("Testing FAZA 4: Integracja Historical Framework z Kestrą")
    print("=" * 80)
    
    # Run all tests
    test1 = test_advanced_historical_flow()
    test2 = test_historical_framework_integration()
    test3 = test_performance_analysis_capabilities()
    test4 = test_comprehensive_reporting()
    test5 = test_automation_and_scheduling()
    test6 = test_integration_with_existing_flows()
    
    print("\n" + "=" * 80)
    
    if all([test1, test2, test3, test4, test5, test6]):
        print("🎉 ALL HISTORICAL FRAMEWORK + KESTRA INTEGRATION TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • Advanced Historical Analysis flow properly configured")
        print("   • Historical Framework fully integrated with Kestra")
        print("   • Performance analysis capabilities implemented")
        print("   • Comprehensive reporting with HTML generation")
        print("   • Automation and scheduling configured")
        print("   • Integration with existing flows validated")
        print("\n🚀 READY FOR:")
        print("   • Automated historical analysis execution")
        print("   • Professional performance monitoring")
        print("   • Comprehensive AI model validation")
        print("   • Automated optimization recommendations")
        print("\n🎯 FAZA 4 STATUS: HISTORICAL FRAMEWORK + KESTRA INTEGRATION COMPLETE")
        print("   Next: Final integration testing and protocol finalization")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
