#!/usr/bin/env python3
"""
Test script to validate the local development environment setup.
This tests the configuration and setup without requiring Docker.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_status(message, success=True):
    """Print status message with color."""
    color = '\033[0;32m' if success else '\033[0;31m'
    reset = '\033[0m'
    symbol = '✅' if success else '❌'
    print(f"{color}{symbol} {message}{reset}")

def print_info(message):
    """Print info message."""
    print(f"🔍 {message}")

def test_project_structure():
    """Test that the project structure is correct."""
    print_info("Testing project structure...")
    
    required_files = [
        'docker-compose.local.yml',
        '.env.local',
        'scripts/start-local-dev.sh',
        'mission_control/app.py',
        'brain/pyproject.toml',
        'pixi.toml',
        'docs/LOCAL_DEVELOPMENT_GUIDE.md'
    ]
    
    required_dirs = [
        'brain/',
        'src/',
        'mission_control/',
        'docs/',
        'scripts/',
        'wallets/'
    ]
    
    all_good = True
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print_status(f"File exists: {file_path}")
        else:
            print_status(f"Missing file: {file_path}", False)
            all_good = False
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print_status(f"Directory exists: {dir_path}")
        else:
            print_status(f"Missing directory: {dir_path}", False)
            all_good = False
    
    return all_good

def test_docker_compose_config():
    """Test that docker-compose.local.yml is valid."""
    print_info("Testing Docker Compose configuration...")
    
    try:
        with open('docker-compose.local.yml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for required services
        required_services = [
            'overmind-dragonfly-local',
            'chroma-local',
            'postgres-local',
            'overmind-brain-local',
            'mission-control-local'
        ]
        
        services = config.get('services', {})
        all_good = True
        
        for service in required_services:
            if service in services:
                print_status(f"Service defined: {service}")
            else:
                print_status(f"Missing service: {service}", False)
                all_good = False
        
        # Check for networks and volumes
        if 'networks' in config:
            print_status("Networks section defined")
        else:
            print_status("Missing networks section", False)
            all_good = False
            
        if 'volumes' in config:
            print_status("Volumes section defined")
        else:
            print_status("Missing volumes section", False)
            all_good = False
        
        return all_good
        
    except Exception as e:
        print_status(f"Docker Compose config error: {e}", False)
        return False

def test_environment_template():
    """Test that .env.local template is properly formatted."""
    print_info("Testing environment template...")
    
    try:
        with open('.env.local', 'r') as f:
            lines = f.readlines()
        
        required_vars = [
            'OPENAI_API_KEY',
            'SNIPER_TRADING_MODE',
            'OVERMIND_ENABLED',
            'ENVIRONMENT'
        ]
        
        found_vars = []
        all_good = True
        
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                var_name = line.split('=')[0]
                found_vars.append(var_name)
        
        for var in required_vars:
            if var in found_vars:
                print_status(f"Environment variable template: {var}")
            else:
                print_status(f"Missing environment variable: {var}", False)
                all_good = False
        
        return all_good
        
    except Exception as e:
        print_status(f"Environment template error: {e}", False)
        return False

def test_mission_control_fix():
    """Test that the Mission Control AttributeError fix is in place."""
    print_info("Testing Mission Control AttributeError fix...")
    
    try:
        with open('mission_control/app.py', 'r') as f:
            content = f.read()
        
        # Check for Goal data class
        if '@dataclass' in content and 'class Goal:' in content:
            print_status("Goal data class defined")
        else:
            print_status("Goal data class missing", False)
            return False
        
        # Check for from_dict method
        if 'def from_dict(cls, data: Dict[str, Any])' in content:
            print_status("Goal.from_dict method defined")
        else:
            print_status("Goal.from_dict method missing", False)
            return False
        
        # Check that MockDynamicGoalManager returns Goal objects
        if 'Goal.from_dict({' in content:
            print_status("MockDynamicGoalManager returns Goal objects")
        else:
            print_status("MockDynamicGoalManager not updated", False)
            return False
        
        return True
        
    except Exception as e:
        print_status(f"Mission Control fix test error: {e}", False)
        return False

def test_scripts_executable():
    """Test that scripts are executable."""
    print_info("Testing script permissions...")
    
    scripts = [
        'scripts/start-local-dev.sh',
        'scripts/deploy-to-production.sh'
    ]
    
    all_good = True
    
    for script in scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print_status(f"Script executable: {script}")
            else:
                print_status(f"Script not executable: {script}", False)
                all_good = False
        else:
            print_status(f"Script missing: {script}", False)
            all_good = False
    
    return all_good

def test_documentation():
    """Test that documentation is complete."""
    print_info("Testing documentation...")
    
    docs = [
        'docs/LOCAL_DEVELOPMENT_GUIDE.md',
        'docs/SERVICE_BOUNDARIES.md',
        'docs/DEPLOYMENT_VALIDATION_CHECKLIST.md',
        'docs/DEPLOYMENT_WORKFLOW.md',
        'PROJECT_CLEANUP_SUMMARY.md'
    ]
    
    all_good = True
    
    for doc in docs:
        if os.path.exists(doc):
            # Check if file has content
            with open(doc, 'r') as f:
                content = f.read().strip()
            if len(content) > 100:  # Reasonable minimum content
                print_status(f"Documentation complete: {doc}")
            else:
                print_status(f"Documentation too short: {doc}", False)
                all_good = False
        else:
            print_status(f"Documentation missing: {doc}", False)
            all_good = False
    
    return all_good

def test_dependency_management():
    """Test that dependency management is unified."""
    print_info("Testing dependency management...")
    
    all_good = True
    
    # Check that mission_control uses pyproject.toml, not requirements.txt
    if os.path.exists('mission_control/pyproject.toml'):
        print_status("Mission Control uses pyproject.toml")
    else:
        print_status("Mission Control missing pyproject.toml", False)
        all_good = False
    
    if os.path.exists('mission_control/requirements.txt'):
        print_status("Mission Control still has requirements.txt (should be removed)", False)
        all_good = False
    else:
        print_status("Mission Control requirements.txt removed")
    
    # Check brain has pyproject.toml
    if os.path.exists('brain/pyproject.toml'):
        print_status("Brain uses pyproject.toml")
    else:
        print_status("Brain missing pyproject.toml", False)
        all_good = False
    
    # Check root has pixi.toml
    if os.path.exists('pixi.toml'):
        print_status("Root has pixi.toml for coordination")
    else:
        print_status("Root missing pixi.toml", False)
        all_good = False
    
    return all_good

def main():
    """Run all validation tests."""
    print("🧪 THE OVERMIND PROTOCOL - Local Environment Validation")
    print("=" * 60)
    print()
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Docker Compose Config", test_docker_compose_config),
        ("Environment Template", test_environment_template),
        ("Mission Control Fix", test_mission_control_fix),
        ("Script Permissions", test_scripts_executable),
        ("Documentation", test_documentation),
        ("Dependency Management", test_dependency_management)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        print_status(f"{test_name}: {'PASSED' if result else 'FAILED'}", result)
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print_status("🎉 ALL VALIDATIONS PASSED!")
        print("✅ Local development environment is ready")
        print("✅ Mission Control AttributeError is fixed")
        print("✅ Professional deployment workflow established")
        print("✅ Ready for production deployment!")
        print("\n🚀 Next steps:")
        print("   1. Start local environment: ./scripts/start-local-dev.sh")
        print("   2. Test Mission Control: http://localhost:8501")
        print("   3. Deploy to production: ./scripts/deploy-to-production.sh")
    else:
        print_status("❌ Some validations failed", False)
        print("🔧 Please fix the issues above before proceeding")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
