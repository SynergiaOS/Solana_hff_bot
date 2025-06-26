#!/usr/bin/env python3
"""
Diagnostic script to check the structure of the overmind_brain package
"""

import os
import sys
import importlib
import pkgutil

def check_module_exists(module_name):
    """Check if a module exists and can be imported"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        return False, str(e)

def find_module_file(module_name):
    """Try to find the file for a module"""
    try:
        module = importlib.import_module(module_name)
        return module.__file__
    except (ImportError, AttributeError):
        return None

def check_package_structure(package_name):
    """Check the structure of a package"""
    try:
        package = importlib.import_module(package_name)
        print(f"✅ Package '{package_name}' exists at {package.__file__}")
        
        # Check for __init__.py
        package_dir = os.path.dirname(package.__file__)
        if os.path.exists(os.path.join(package_dir, "__init__.py")):
            print(f"✅ __init__.py exists in {package_dir}")
        else:
            print(f"❌ __init__.py missing in {package_dir}")
        
        # List all modules in the package
        print(f"\nModules in {package_name}:")
        for _, name, ispkg in pkgutil.iter_modules([package_dir]):
            if ispkg:
                print(f"📦 {name} (subpackage)")
            else:
                print(f"📄 {name}")
                
        return True
    except ImportError as e:
        print(f"❌ Package '{package_name}' cannot be imported: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🔍 OVERMIND Brain Package Diagnostic\n")
    
    # Add brain/src to path if it exists
    brain_src = os.path.join(os.getcwd(), "brain", "src")
    if os.path.exists(brain_src):
        sys.path.insert(0, brain_src)
        print(f"✅ Added {brain_src} to Python path")
    else:
        print(f"❌ Directory not found: {brain_src}")
    
    # Check Python path
    print("\n📋 Python Path:")
    for path in sys.path:
        print(f"  - {path}")
    
    # Check overmind_brain package
    print("\n📦 Checking overmind_brain package:")
    if check_package_structure("overmind_brain"):
        # Check specific modules
        modules_to_check = [
            "overmind_brain.goal_manager",
            "overmind_brain.overmind_brain_manager",
            "overmind_brain.portfolio_monitor",
            "overmind_brain.strategy_mapper"
        ]
        
        print("\n📄 Checking specific modules:")
        for module in modules_to_check:
            result = check_module_exists(module)
            if result is True:
                file_path = find_module_file(module)
                print(f"✅ Module '{module}' exists at {file_path}")
            else:
                print(f"❌ Module '{module}' cannot be imported: {result[1]}")
    
    print("\n🔍 Diagnostic complete")

if __name__ == "__main__":
    main()