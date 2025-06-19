#!/bin/bash

# THE OVERMIND PROTOCOL - Pre-Deployment Checklist
# Quick verification before Contabo VDS deployment

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_ok() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo -e "${BLUE}🔍 THE OVERMIND PROTOCOL - Pre-Deployment Checklist${NC}"
echo "=================================================="

# Check 1: SSH Connection
print_check "Testing SSH connection to Contabo VDS..."
if ssh -o ConnectTimeout=5 marcin@89.117.53.53 "echo 'SSH OK'" > /dev/null 2>&1; then
    print_ok "SSH connection to 89.117.53.53 working"
else
    print_error "SSH connection failed - check your connection"
    exit 1
fi

# Check 2: Local files
print_check "Checking local project files..."
required_files=(
    "reorganize-project.sh"
    "deploy-contabo.sh"
    "monitoring-setup.sh"
    "src/main.rs"
    "Cargo.toml"
    "pixi.toml"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -eq 0 ]]; then
    print_ok "All required files present"
else
    print_error "Missing files: ${missing_files[*]}"
    exit 1
fi

# Check 3: Environment template
print_check "Checking environment configuration..."
if [[ -f ".env.example" ]]; then
    print_ok ".env.example found"
else
    print_warning ".env.example not found - creating basic template"
    cat > .env.example << 'EOF'
# THE OVERMIND PROTOCOL - Environment Configuration
OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key
MISTRAL_API_KEY=your-mistral-api-key
FINANCIAL_DATASETS_API_KEY=your-financial-datasets-api-key
HELIUS_API_KEY=your-helius-api-key
QUICKNODE_API_KEY=your-quicknode-api-key
SOLANA_WALLET_PRIVATE_KEY=your-wallet-private-key
EOF
    print_ok "Created .env.example template"
fi

# Check 4: Docker availability locally (for testing)
print_check "Checking Docker availability..."
if command -v docker &> /dev/null; then
    print_ok "Docker available locally"
else
    print_warning "Docker not available locally (will be installed on server)"
fi

# Check 5: Required tools
print_check "Checking required tools..."
required_tools=("ssh" "rsync" "curl")
missing_tools=()

for tool in "${required_tools[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        missing_tools+=("$tool")
    fi
done

if [[ ${#missing_tools[@]} -eq 0 ]]; then
    print_ok "All required tools available"
else
    print_error "Missing tools: ${missing_tools[*]}"
    exit 1
fi

# Check 6: Server resources
print_check "Checking Contabo VDS resources..."
server_info=$(ssh marcin@89.117.53.53 "echo 'RAM:' && free -h | grep Mem | awk '{print \$2}' && echo 'CPU:' && nproc && echo 'Disk:' && df -h / | tail -1 | awk '{print \$4}'" 2>/dev/null)

if [[ -n "$server_info" ]]; then
    print_ok "Server resources check:"
    echo "$server_info" | while read line; do
        echo "    $line"
    done
else
    print_warning "Could not check server resources"
fi

echo ""
echo -e "${GREEN}✅ Pre-deployment checklist completed!${NC}"
echo ""
echo -e "${YELLOW}📋 Ready for deployment:${NC}"
echo "1. Run: ./reorganize-project.sh"
echo "2. Run: ./monitoring-setup.sh"
echo "3. Run: ./deploy-contabo.sh"
echo ""
echo -e "${YELLOW}⚠️  Remember to set your API keys after deployment!${NC}"
