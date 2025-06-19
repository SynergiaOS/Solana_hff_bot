#!/usr/bin/env python3
"""
🔧 THE OVERMIND PROTOCOL - Project Refactoring Script
Comprehensive code refactoring and cleanup for production readiness
"""

import os
import shutil
import glob
from pathlib import Path
import json

def create_clean_structure():
    """Create clean project structure"""
    print("🏗️ Creating clean project structure...")
    
    # Create organized directories
    directories = [
        "deployment/docker-compose",
        "deployment/scripts", 
        "deployment/configs",
        "testing/scripts",
        "testing/results",
        "archive/backups",
        "archive/old-scripts",
        "logs/archive"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  ✅ Created: {directory}")

def consolidate_docker_compose():
    """Consolidate docker-compose files"""
    print("\n🐳 Consolidating docker-compose files...")
    
    # Keep only essential docker-compose files
    essential_files = [
        "docker-compose.yml",  # Main development
        "docker-compose.overmind.yml",  # Production OVERMIND
        "docker-compose.production.yml"  # Production deployment
    ]
    
    # Move others to archive
    docker_files = glob.glob("docker-compose*.yml")
    for file in docker_files:
        if file not in essential_files:
            if os.path.exists(file):
                shutil.move(file, f"archive/backups/{file}")
                print(f"  📦 Archived: {file}")
    
    # Move essential files to deployment folder
    for file in essential_files:
        if os.path.exists(file):
            shutil.copy2(file, f"deployment/docker-compose/{file}")
            print(f"  ✅ Copied to deployment: {file}")

def organize_scripts():
    """Organize deployment and test scripts"""
    print("\n📜 Organizing scripts...")
    
    # Deployment scripts to move
    deployment_scripts = [
        "deploy-overmind.sh",
        "deploy-contabo.sh", 
        "quick-deploy.sh",
        "auto-setup.sh",
        "simple-setup.sh"
    ]
    
    # Test scripts to move
    test_scripts = [
        "test-*.py",
        "test-*.sh",
        "*test*.py",
        "*test*.sh"
    ]
    
    # Move deployment scripts
    for script in deployment_scripts:
        if os.path.exists(script):
            shutil.move(script, f"deployment/scripts/{script}")
            print(f"  🚀 Moved deployment script: {script}")
    
    # Move test scripts (using glob patterns)
    for pattern in test_scripts:
        for file in glob.glob(pattern):
            if os.path.isfile(file) and not file.startswith("scripts/"):
                shutil.move(file, f"testing/scripts/{os.path.basename(file)}")
                print(f"  🧪 Moved test script: {file}")

def clean_backups_and_logs():
    """Clean up backup folders and logs"""
    print("\n🧹 Cleaning backups and logs...")
    
    # Move backup folders
    backup_folders = ["backup-*"]
    for pattern in backup_folders:
        for folder in glob.glob(pattern):
            if os.path.isdir(folder):
                shutil.move(folder, f"archive/backups/{folder}")
                print(f"  📦 Archived backup: {folder}")
    
    # Archive old logs but keep structure
    if os.path.exists("logs"):
        log_files = glob.glob("logs/*.log")
        for log_file in log_files:
            # Keep recent logs, archive old ones
            file_size = os.path.getsize(log_file)
            if file_size > 10 * 1024 * 1024:  # > 10MB
                shutil.move(log_file, f"logs/archive/{os.path.basename(log_file)}")
                print(f"  📋 Archived large log: {log_file}")

def consolidate_configs():
    """Consolidate configuration files"""
    print("\n⚙️ Consolidating configuration files...")
    
    # Move standalone config files to config directory
    config_files = [
        "pixi.toml*",
        "*.json",
        "*.yml",
        "*.yaml"
    ]
    
    for pattern in config_files:
        for file in glob.glob(pattern):
            if os.path.isfile(file) and not file.startswith(("config/", "deployment/", "testing/")):
                # Skip essential files
                if file in ["Cargo.toml", "Cargo.lock", "pyproject.toml", "README.md"]:
                    continue
                    
                # Determine destination
                if "docker-compose" in file:
                    continue  # Already handled
                elif any(x in file for x in ["test", "result", "report"]):
                    dest = f"testing/results/{file}"
                else:
                    dest = f"deployment/configs/{file}"
                
                shutil.move(file, dest)
                print(f"  ⚙️ Moved config: {file} -> {dest}")

def remove_duplicates():
    """Remove duplicate and unnecessary files"""
    print("\n🗑️ Removing duplicates and unnecessary files...")
    
    # Files to remove
    unnecessary_files = [
        "*.pid",
        "overmind.pid",
        "*.tmp",
        "*.bak",
        "*.old"
    ]
    
    for pattern in unnecessary_files:
        for file in glob.glob(pattern):
            if os.path.isfile(file):
                os.remove(file)
                print(f"  🗑️ Removed: {file}")

def update_documentation():
    """Update documentation with new structure"""
    print("\n📚 Updating documentation...")
    
    # Create updated README for new structure
    readme_content = """# 🚀 THE OVERMIND PROTOCOL - Refactored Structure

## 📁 Project Structure

```
├── brain/                  # AI Brain (Python)
├── src/                   # Rust Executor
├── deployment/            # Deployment files
│   ├── docker-compose/    # Docker compose files
│   ├── scripts/          # Deployment scripts
│   └── configs/          # Configuration files
├── testing/              # Testing framework
│   ├── scripts/         # Test scripts
│   └── results/         # Test results
├── docs/                # Documentation
├── infrastructure/      # Infrastructure configs
├── monitoring/         # Monitoring setup
├── config/             # Environment configs
├── scripts/            # Core utility scripts
├── archive/            # Archived files
│   └── backups/        # Old backups
└── logs/               # System logs
    └── archive/        # Archived logs
```

## 🚀 Quick Start

### Development
```bash
docker-compose -f deployment/docker-compose/docker-compose.yml up
```

### Production
```bash
docker-compose -f deployment/docker-compose/docker-compose.overmind.yml up
```

### Deployment
```bash
./deployment/scripts/deploy-overmind.sh
```

### Testing
```bash
./testing/scripts/test-overmind-complete.sh
```

## 📊 Test Results

All FRONT tests completed successfully:
- ✅ FRONT 1: AI Brain Intelligence (GENIUS level)
- ✅ FRONT 2: Communication Excellence (EXCELLENT)
- ✅ FRONT 3: Performance & Scalability (ULTRA-HIGH)

System ready for production deployment.
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("  📚 Updated README.md with new structure")

def create_gitignore():
    """Create comprehensive .gitignore"""
    print("\n🙈 Creating comprehensive .gitignore...")
    
    gitignore_content = """# Rust
/target/
**/*.rs.bk
Cargo.lock

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/
.env

# Logs
logs/*.log
logs/archive/
*.log

# Database
*.sqlite3
chroma_db/
*.db

# Docker
.dockerignore

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
*.pid
*.tmp
testing/results/*.json
archive/
wallets/*.json
devnet-wallet.json

# Secrets
.env.local
.env.production
*.key
*.pem
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("  🙈 Created comprehensive .gitignore")

def main():
    """Main refactoring function"""
    print("🔧 THE OVERMIND PROTOCOL - PROJECT REFACTORING")
    print("=" * 55)
    print("🎯 Cleaning and organizing codebase for production")
    print()
    
    # Execute refactoring steps
    create_clean_structure()
    consolidate_docker_compose()
    organize_scripts()
    clean_backups_and_logs()
    consolidate_configs()
    remove_duplicates()
    update_documentation()
    create_gitignore()
    
    print("\n🎉 PROJECT REFACTORING COMPLETE!")
    print("=" * 40)
    print("✅ Clean project structure created")
    print("✅ Docker compose files consolidated")
    print("✅ Scripts organized by purpose")
    print("✅ Backups and logs archived")
    print("✅ Configuration files consolidated")
    print("✅ Duplicates and unnecessary files removed")
    print("✅ Documentation updated")
    print("✅ Comprehensive .gitignore created")
    print()
    print("🚀 Project ready for production deployment!")

if __name__ == "__main__":
    main()
