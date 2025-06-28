#!/bin/bash
# THE OVERMIND PROTOCOL - Project Structure Cleanup Script
# Automated cleanup and reorganization of project files

set -e  # Exit on any error

echo "🧹 THE OVERMIND PROTOCOL - Project Structure Cleanup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_info() {
    echo -e "${BLUE}📁${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Create backup directory
BACKUP_DIR="archive/cleanup_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
print_info "Created backup directory: $BACKUP_DIR"

# Step 1: Create new organized directory structure
print_info "Creating new directory structure..."

mkdir -p tests/{unit/{rust,python},integration/{api,components,workflows},historical_data/{backtests,performance,scenarios},fixtures/{market_data,api_responses,configurations},utils}
mkdir -p docs/{api,architecture,deployment,development,user_guides,reports}
mkdir -p scripts/{deployment,development,maintenance,testing,utilities}
mkdir -p config/{environments,docker,monitoring}

print_status "New directory structure created"

# Step 2: Move test files to proper locations
print_info "Reorganizing test files..."

# Move Python test files from root to tests/integration/
if ls test_*.py 1> /dev/null 2>&1; then
    for file in test_*.py; do
        if [ -f "$file" ]; then
            mv "$file" tests/integration/
            print_status "Moved $file to tests/integration/"
        fi
    done
fi

# Move additional test files
if ls *_test.py 1> /dev/null 2>&1; then
    for file in *_test.py; do
        if [ -f "$file" ]; then
            mv "$file" tests/integration/
            print_status "Moved $file to tests/integration/"
        fi
    done
fi

# Move Rust tests to unit tests directory
if [ -d "tests" ]; then
    for file in tests/*_tests.rs; do
        if [ -f "$file" ]; then
            mv "$file" tests/unit/rust/
            print_status "Moved $(basename $file) to tests/unit/rust/"
        fi
    done
fi

# Move Python tests from tests/ to unit tests
if [ -d "tests" ]; then
    for file in tests/test_*.py; do
        if [ -f "$file" ]; then
            mv "$file" tests/unit/python/
            print_status "Moved $(basename $file) to tests/unit/python/"
        fi
    done
fi

# Step 3: Move documentation files
print_info "Organizing documentation..."

# Move reports to docs/reports/
for file in *_REPORT.md *_SUMMARY.md *_STATUS.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/reports/
        print_status "Moved $file to docs/reports/"
    fi
done

# Move implementation guides
for file in *_IMPLEMENTATION*.md *_GUIDE*.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/development/
        print_status "Moved $file to docs/development/"
    fi
done

# Move analysis files
for file in ANALIZA*.md BENCHMARK*.md HONEST*.md VALIDATION*.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/reports/
        print_status "Moved $file to docs/reports/"
    fi
done

# Step 4: Move utility scripts
print_info "Organizing scripts..."

# Move collector and fetcher scripts
for file in *_collector.py *_fetcher.py *_exporter.py; do
    if [ -f "$file" ]; then
        mv "$file" scripts/utilities/
        print_status "Moved $file to scripts/utilities/"
    fi
done

# Move deployment scripts
for file in deploy*.sh *deploy*.sh; do
    if [ -f "$file" ]; then
        mv "$file" scripts/deployment/
        print_status "Moved $file to scripts/deployment/"
    fi
done

# Move monitoring scripts
for file in *monitoring*.py *monitoring*.sh; do
    if [ -f "$file" ]; then
        mv "$file" scripts/maintenance/
        print_status "Moved $file to scripts/maintenance/"
    fi
done

# Step 5: Remove redundant files
print_info "Removing redundant files..."

# Backup before removing
redundant_files=(
    "CLAUDE.md"
    "enhanced_trading_bot.py"
    "continuous_trading_test.py"
    "demo_overmind_protocol.sh"
    "fix_monitoring_access.sh"
)

for file in "${redundant_files[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
        rm "$file"
        print_status "Removed redundant file: $file (backed up)"
    fi
done

# Step 6: Consolidate configuration files
print_info "Consolidating configuration files..."

# Move Docker configurations
if [ -f "docker-compose.devnet.yml" ]; then
    mv docker-compose.devnet.yml config/docker/
    print_status "Moved docker-compose.devnet.yml to config/docker/"
fi

if [ -f "docker-compose.local.yml" ]; then
    mv docker-compose.local.yml config/docker/
    print_status "Moved docker-compose.local.yml to config/docker/"
fi

if [ -f "docker-compose.production.yml" ]; then
    mv docker-compose.production.yml config/docker/
    print_status "Moved docker-compose.production.yml to config/docker/"
fi

# Move monitoring configs
if [ -f "fix_prometheus_config.yml" ]; then
    mv fix_prometheus_config.yml config/monitoring/
    print_status "Moved fix_prometheus_config.yml to config/monitoring/"
fi

# Step 7: Clean up empty directories
print_info "Cleaning up empty directories..."

find . -type d -empty -delete 2>/dev/null || true
print_status "Removed empty directories"

# Step 8: Update .gitignore if needed
print_info "Updating .gitignore..."

if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Build artifacts
target/
*.exe
*.dll
*.so
*.dylib

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
.venv/
env/
.env

# Environment files
.env.*
!.env.example
!.env.template

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/*.log
*.log

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
*.tmp
*.temp
.DS_Store
Thumbs.db

# Backup files
*.backup
*.bak
archive/cleanup_backup_*/
EOF
    print_status "Created .gitignore file"
fi

# Step 9: Create README for new structure
print_info "Creating structure documentation..."

cat > STRUCTURE_GUIDE.md << EOF
# THE OVERMIND PROTOCOL - Project Structure Guide

## 📁 **Organized Directory Structure**

\`\`\`
THE_OVERMIND_PROTOCOL/
├── 📁 src/                          # Rust source code
├── 📁 brain/                        # Python AI Brain
├── 📁 mission_control/              # Dashboard
├── 📁 tests/                        # Organized test suite
│   ├── unit/                        # Unit tests
│   │   ├── rust/                    # Rust unit tests
│   │   └── python/                  # Python unit tests
│   ├── integration/                 # Integration tests
│   │   ├── api/                     # API integration
│   │   ├── components/              # Component integration
│   │   └── workflows/               # End-to-end workflows
│   ├── historical_data/             # Historical data tests
│   │   ├── backtests/               # Strategy backtests
│   │   ├── performance/             # Performance validation
│   │   └── scenarios/               # Test scenarios
│   ├── fixtures/                    # Test data
│   └── utils/                       # Test utilities
├── 📁 docs/                         # Organized documentation
│   ├── api/                         # API documentation
│   ├── architecture/                # System architecture
│   ├── deployment/                  # Deployment guides
│   ├── development/                 # Development guides
│   ├── user_guides/                 # User documentation
│   └── reports/                     # Analysis reports
├── 📁 scripts/                      # Utility scripts
│   ├── deployment/                  # Deployment scripts
│   ├── development/                 # Development utilities
│   ├── maintenance/                 # Maintenance scripts
│   ├── testing/                     # Testing utilities
│   └── utilities/                   # General utilities
├── 📁 config/                       # Configuration files
│   ├── environments/                # Environment configs
│   ├── docker/                      # Docker configurations
│   └── monitoring/                  # Monitoring configs
└── 📁 infrastructure/               # Infrastructure code
\`\`\`

## 🎯 **Benefits of New Structure**

- **Clear Separation**: Tests, docs, and scripts properly organized
- **Easy Navigation**: Logical grouping of related files
- **Professional Layout**: Industry-standard project structure
- **Maintainability**: Easier to find and update files
- **Scalability**: Structure supports project growth

## 📋 **File Locations**

### **Tests**
- Unit tests: \`tests/unit/{rust,python}/\`
- Integration tests: \`tests/integration/\`
- Historical data tests: \`tests/historical_data/\`

### **Documentation**
- API docs: \`docs/api/\`
- Architecture: \`docs/architecture/\`
- User guides: \`docs/user_guides/\`
- Reports: \`docs/reports/\`

### **Scripts**
- Deployment: \`scripts/deployment/\`
- Development: \`scripts/development/\`
- Utilities: \`scripts/utilities/\`

### **Configuration**
- Environment configs: \`config/environments/\`
- Docker configs: \`config/docker/\`
- Monitoring: \`config/monitoring/\`

## 🚀 **Next Steps**

1. Update import paths in code
2. Update CI/CD pipelines
3. Update documentation references
4. Test all functionality
5. Commit organized structure

**✅ Project structure cleanup completed successfully!**
EOF

print_status "Created STRUCTURE_GUIDE.md"

# Final summary
echo ""
echo "=========================================="
print_status "Project structure cleanup completed!"
echo ""
print_info "Summary of changes:"
echo "  • Organized tests into proper directories"
echo "  • Moved documentation to docs/ subdirectories"
echo "  • Reorganized scripts by purpose"
echo "  • Consolidated configuration files"
echo "  • Removed redundant files (backed up)"
echo "  • Created structure documentation"
echo ""
print_info "Backup location: $BACKUP_DIR"
print_info "Structure guide: STRUCTURE_GUIDE.md"
echo ""
print_warning "Next steps:"
echo "  1. Update import paths in code"
echo "  2. Test all functionality"
echo "  3. Update CI/CD configurations"
echo "  4. Commit changes to git"
echo ""
print_status "🎉 THE OVERMIND PROTOCOL structure is now organized!"
