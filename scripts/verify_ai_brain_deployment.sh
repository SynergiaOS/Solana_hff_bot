#!/bin/bash

# THE OVERMIND PROTOCOL - AI Brain Deployment Verification
# Quick verification that AI Brain is ready for integration

set -e

echo "🧠 THE OVERMIND PROTOCOL - AI Brain Deployment Verification"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verification functions
verify_brain_structure() {
    log "Verifying AI Brain project structure..."
    
    local required_files=(
        "brain/src/overmind_brain/brain.py"
        "brain/src/overmind_brain/vector_memory.py"
        "brain/src/overmind_brain/decision_engine.py"
        "brain/src/overmind_brain/risk_analyzer.py"
        "brain/src/overmind_brain/market_analyzer.py"
        "brain/src/overmind_brain/main.py"
        "brain/pyproject.toml"
        "brain/README.md"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        success "All required AI Brain files present"
        return 0
    else
        error "Missing files: ${missing_files[*]}"
        return 1
    fi
}

verify_brain_imports() {
    log "Verifying AI Brain component imports..."
    
    cd brain
    
    python -c "
import sys
sys.path.insert(0, 'src')

components = [
    ('Vector Memory', 'overmind_brain.vector_memory', 'VectorMemory'),
    ('Decision Engine', 'overmind_brain.decision_engine', 'DecisionEngine'),
    ('Risk Analyzer', 'overmind_brain.risk_analyzer', 'RiskAnalyzer'),
    ('Market Analyzer', 'overmind_brain.market_analyzer', 'MarketAnalyzer'),
    ('OVERMIND Brain', 'overmind_brain.brain', 'OVERMINDBrain')
]

all_success = True

for name, module, class_name in components:
    try:
        exec(f'from {module} import {class_name}')
        print(f'✅ {name}: {class_name}')
    except Exception as e:
        print(f'❌ {name}: Failed - {e}')
        all_success = False

if all_success:
    print('🎯 All AI Brain components import successfully!')
    exit(0)
else:
    print('❌ Some components failed to import')
    exit(1)
" 2>/dev/null
    
    local result=$?
    cd ..
    
    if [ $result -eq 0 ]; then
        success "All AI Brain components import successfully"
        return 0
    else
        error "Some AI Brain components failed to import"
        return 1
    fi
}

verify_dependencies() {
    log "Verifying AI Brain dependencies..."
    
    cd brain
    
    local required_packages=(
        "openai"
        "chromadb"
        "fastapi"
        "redis"
        "pandas"
        "numpy"
        "sentence-transformers"
    )
    
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! python -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    cd ..
    
    if [ ${#missing_packages[@]} -eq 0 ]; then
        success "All required dependencies installed"
        return 0
    else
        warning "Missing packages: ${missing_packages[*]}"
        log "Run: cd brain && pip install -e ."
        return 1
    fi
}

verify_configuration() {
    log "Verifying AI Brain configuration..."
    
    local config_files=(
        "config/environments/.env.brain.template"
        "config/environments/.env.brain.development"
    )
    
    local missing_configs=()
    
    for config in "${config_files[@]}"; do
        if [ ! -f "$config" ]; then
            missing_configs+=("$config")
        fi
    done
    
    if [ ${#missing_configs[@]} -eq 0 ]; then
        success "Configuration files present"
        return 0
    else
        error "Missing configuration files: ${missing_configs[*]}"
        return 1
    fi
}

verify_documentation() {
    log "Verifying AI Brain documentation..."
    
    local doc_files=(
        "docs/implementation/AI_BRAIN_IMPLEMENTATION_REPORT.md"
        "docs/evaluation/FINAL_AI_BRAIN_EVALUATION.md"
        "docs/testing/INTEGRATION_TEST_PLAN.md"
        "brain/README.md"
    )
    
    local missing_docs=()
    
    for doc in "${doc_files[@]}"; do
        if [ ! -f "$doc" ]; then
            missing_docs+=("$doc")
        fi
    done
    
    if [ ${#missing_docs[@]} -eq 0 ]; then
        success "Documentation complete"
        return 0
    else
        error "Missing documentation: ${missing_docs[*]}"
        return 1
    fi
}

verify_test_scripts() {
    log "Verifying test scripts..."
    
    local test_scripts=(
        "scripts/test_communication.sh"
        "brain/tests/test_vector_memory.py"
        "brain/tests/test_decision_engine.py"
        "brain/tests/test_integration.py"
    )
    
    local missing_tests=()
    
    for test in "${test_scripts[@]}"; do
        if [ ! -f "$test" ]; then
            missing_tests+=("$test")
        fi
    done
    
    if [ ${#missing_tests[@]} -eq 0 ]; then
        success "Test scripts present"
        return 0
    else
        error "Missing test scripts: ${missing_tests[*]}"
        return 1
    fi
}

# Main verification
main() {
    echo
    log "Starting AI Brain deployment verification..."
    echo
    
    local verification_results=()
    
    # Verify project structure
    if verify_brain_structure; then
        verification_results+=("✅ Project Structure")
    else
        verification_results+=("❌ Project Structure")
    fi
    
    # Verify component imports
    if verify_brain_imports; then
        verification_results+=("✅ Component Imports")
    else
        verification_results+=("❌ Component Imports")
    fi
    
    # Verify dependencies
    if verify_dependencies; then
        verification_results+=("✅ Dependencies")
    else
        verification_results+=("⚠️ Dependencies")
    fi
    
    # Verify configuration
    if verify_configuration; then
        verification_results+=("✅ Configuration")
    else
        verification_results+=("❌ Configuration")
    fi
    
    # Verify documentation
    if verify_documentation; then
        verification_results+=("✅ Documentation")
    else
        verification_results+=("❌ Documentation")
    fi
    
    # Verify test scripts
    if verify_test_scripts; then
        verification_results+=("✅ Test Scripts")
    else
        verification_results+=("❌ Test Scripts")
    fi
    
    # Display results
    echo
    echo "=========================================================="
    echo "🧠 AI BRAIN DEPLOYMENT VERIFICATION RESULTS"
    echo "=========================================================="
    
    local passed=0
    local total=${#verification_results[@]}
    
    for result in "${verification_results[@]}"; do
        echo "$result"
        if [[ $result == *"✅"* ]]; then
            ((passed++))
        fi
    done
    
    echo
    echo "Summary: $passed/$total verifications passed"
    
    if [ $passed -eq $total ]; then
        success "🎉 AI BRAIN DEPLOYMENT VERIFICATION PASSED!"
        echo
        echo "✅ THE OVERMIND PROTOCOL AI Brain is ready for integration"
        echo "✅ All components implemented and verified"
        echo "✅ Ready to proceed with communication testing"
        echo
        echo "Next steps:"
        echo "1. Run communication test: ./scripts/test_communication.sh"
        echo "2. Start AI Brain server: cd brain && python -m overmind_brain.main server"
        echo "3. Begin integration with Rust Executor"
        exit 0
    else
        error "❌ Some verifications failed. Please address the issues above."
        exit 1
    fi
}

# Run verification
main "$@"
