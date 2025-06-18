#!/bin/bash

# THE OVERMIND PROTOCOL - Environment Setup Script
# Automated setup of environment configuration

set -e

echo "🚀 THE OVERMIND PROTOCOL - Environment Setup"
echo "============================================="

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

# Check if .env exists
check_env_file() {
    if [ -f ".env" ]; then
        warning ".env file already exists"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Keeping existing .env file"
            return 1
        fi
    fi
    return 0
}

# Interactive configuration
configure_environment() {
    log "Starting interactive environment configuration..."
    
    # Environment type
    echo
    echo "🌍 Environment Configuration:"
    echo "1) Development (devnet, paper trading, debug mode)"
    echo "2) Production (mainnet, live trading, optimized)"
    echo "3) Testing (devnet, mock trading, verbose logging)"
    read -p "Select environment type (1-3): " env_type
    
    case $env_type in
        1)
            ENV_TYPE="development"
            TRADING_MODE="paper"
            NETWORK="devnet"
            DEBUG_MODE="true"
            ;;
        2)
            ENV_TYPE="production"
            TRADING_MODE="live"
            NETWORK="mainnet"
            DEBUG_MODE="false"
            ;;
        3)
            ENV_TYPE="testing"
            TRADING_MODE="mock"
            NETWORK="devnet"
            DEBUG_MODE="true"
            ;;
        *)
            ENV_TYPE="development"
            TRADING_MODE="paper"
            NETWORK="devnet"
            DEBUG_MODE="true"
            ;;
    esac
    
    # API Keys
    echo
    echo "🔑 API Key Configuration:"
    read -p "Enter your OpenAI API key (required): " openai_key
    read -p "Enter your QuickNode RPC URL (optional): " quicknode_rpc
    read -p "Enter your QuickNode WebSocket URL (optional): " quicknode_ws
    
    # Trading Configuration
    echo
    echo "💰 Trading Configuration:"
    read -p "Maximum position size in SOL (default: 0.1): " max_position
    max_position=${max_position:-0.1}
    
    read -p "Maximum daily loss in SOL (default: 1.0): " max_daily_loss
    max_daily_loss=${max_daily_loss:-1.0}
    
    read -p "Risk percentage (default: 2.0): " risk_percentage
    risk_percentage=${risk_percentage:-2.0}
    
    # Monitoring
    echo
    echo "📊 Monitoring Configuration:"
    read -p "Enable alerts? (y/N): " enable_alerts
    if [[ $enable_alerts =~ ^[Yy]$ ]]; then
        read -p "Alert email address: " alert_email
        ENABLE_ALERTS="true"
    else
        alert_email=""
        ENABLE_ALERTS="false"
    fi
    
    # Generate .env file
    generate_env_file
}

# Generate .env file based on configuration
generate_env_file() {
    log "Generating .env file..."
    
    cat > .env << EOF
# THE OVERMIND PROTOCOL - Environment Configuration
# Generated on $(date)
# Environment: $ENV_TYPE

# =================================================
# 🔑 API KEYS & AUTHENTICATION
# =================================================

OPENAI_API_KEY=$openai_key
MISTRAL_API_KEY=
GOOGLE_API_KEY=
PERPLEXITY_API_KEY=

# =================================================
# 🌐 SOLANA NETWORK CONFIGURATION
# =================================================

EOF

    if [ "$NETWORK" = "mainnet" ]; then
        cat >> .env << EOF
# Mainnet Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WS_URL=wss://api.mainnet-beta.solana.com
EOF
        if [ -n "$quicknode_rpc" ]; then
            cat >> .env << EOF
QUICKNODE_RPC_URL=$quicknode_rpc
QUICKNODE_WS_URL=$quicknode_ws
EOF
        fi
    else
        cat >> .env << EOF
# Devnet Configuration
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WS_URL=wss://api.devnet.solana.com
QUICKNODE_DEVNET_RPC_URL=https://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580
QUICKNODE_DEVNET_WS_URL=wss://distinguished-blue-glade.solana-devnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580
EOF
    fi

    cat >> .env << EOF

# =================================================
# 🧠 AI BRAIN CONFIGURATION
# =================================================

BRAIN_HOST=localhost
BRAIN_PORT=8000
BRAIN_LOG_LEVEL=INFO
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=overmind_memory
EMBEDDING_MODEL=all-MiniLM-L6-v2
DECISION_CONFIDENCE_THRESHOLD=0.6
MAX_PORTFOLIO_RISK_PERCENTAGE=$risk_percentage

# =================================================
# 🐉 DRAGONFLY DB CONFIGURATION
# =================================================

DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
DRAGONFLY_PASSWORD=
OVERMIND_MARKET_EVENTS_QUEUE=overmind:market_events
OVERMIND_TRADING_COMMANDS_QUEUE=overmind:trading_commands
OVERMIND_EXECUTION_RESULTS_QUEUE=overmind:execution_results

# =================================================
# ⚡ RUST EXECUTOR CONFIGURATION
# =================================================

SNIPER_TRADING_MODE=$TRADING_MODE
SNIPER_ENVIRONMENT=$NETWORK
SNIPER_MAX_POSITION_SIZE=$max_position
SNIPER_MAX_DAILY_LOSS=$max_daily_loss
SNIPER_MAX_SLIPPAGE_BPS=100
SNIPER_EXECUTION_TIMEOUT_MS=5000

# =================================================
# 📊 MONITORING & LOGGING
# =================================================

LOG_LEVEL=INFO
LOG_FORMAT=json
ENABLE_FILE_LOGGING=true
ENABLE_CONSOLE_LOGGING=true
ENABLE_ALERTS=$ENABLE_ALERTS
ALERT_EMAIL=$alert_email

# =================================================
# 🔒 SECURITY CONFIGURATION
# =================================================

WALLET_PATH=./wallets/trading-wallet.json
BACKUP_WALLET_PATH=./wallets/backup-wallet.json
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=100

# =================================================
# 🌍 ENVIRONMENT SETTINGS
# =================================================

NODE_ENV=$ENV_TYPE
ENVIRONMENT=$ENV_TYPE
DEBUG_MODE=$DEBUG_MODE
TZ=UTC

# =================================================
# 🎯 PERFORMANCE SETTINGS
# =================================================

MAX_CONCURRENT_TRADES=5
MAX_CONCURRENT_ANALYSIS=10
ENABLE_CACHING=true
CACHE_TTL_SECONDS=300

EOF

    success ".env file generated successfully"
}

# Copy environment file to brain directory
setup_brain_env() {
    log "Setting up AI Brain environment..."
    
    if [ -f "brain/.env" ]; then
        warning "brain/.env already exists"
        return 0
    fi
    
    # Extract relevant variables for brain
    cat > brain/.env << EOF
# THE OVERMIND PROTOCOL - AI Brain Environment
# Generated from main .env file

OPENAI_API_KEY=$openai_key
BRAIN_HOST=localhost
BRAIN_PORT=8000
BRAIN_LOG_LEVEL=INFO
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=overmind_memory
EMBEDDING_MODEL=all-MiniLM-L6-v2
DECISION_CONFIDENCE_THRESHOLD=0.6
MAX_PORTFOLIO_RISK_PERCENTAGE=$risk_percentage
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
ENVIRONMENT=$ENV_TYPE
DEBUG_MODE=$DEBUG_MODE
EOF

    success "AI Brain .env file created"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    directories=(
        "logs"
        "data"
        "data/chroma"
        "wallets"
        "backups"
        "config/environments"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            success "Created directory: $dir"
        fi
    done
}

# Validate configuration
validate_configuration() {
    log "Validating configuration..."
    
    # Check OpenAI API key format
    if [[ ! $openai_key =~ ^sk-[a-zA-Z0-9]{48,}$ ]]; then
        warning "OpenAI API key format may be incorrect"
    fi
    
    # Check if required files exist
    if [ ! -f ".env" ]; then
        error ".env file not found"
        return 1
    fi
    
    if [ ! -f "brain/.env" ]; then
        error "brain/.env file not found"
        return 1
    fi
    
    success "Configuration validation passed"
}

# Display next steps
show_next_steps() {
    echo
    echo "🎉 Environment setup completed successfully!"
    echo "=========================================="
    echo
    echo "📋 Next steps:"
    echo "1. Review and edit .env file if needed"
    echo "2. Create trading wallet: solana-keygen new --outfile wallets/trading-wallet.json"
    echo "3. Fund your wallet with SOL for trading"
    echo "4. Start DragonflyDB: docker run -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly"
    echo "5. Start AI Brain: cd brain && python -m overmind_brain.main server"
    echo "6. Start Rust Executor: cargo run --release"
    echo
    echo "🧪 Testing:"
    echo "- Run communication test: ./scripts/test_communication.sh"
    echo "- Run end-to-end test: ./scripts/test_e2e_devnet.sh"
    echo
    echo "📚 Documentation:"
    echo "- Check docs/ directory for detailed guides"
    echo "- Review configuration in .env and brain/.env"
    echo
    echo "⚠️ Security reminders:"
    echo "- Never commit .env files to version control"
    echo "- Keep your API keys secure"
    echo "- Start with paper trading mode"
    echo "- Test thoroughly before live trading"
}

# Main execution
main() {
    echo
    log "Starting THE OVERMIND PROTOCOL environment setup..."
    echo
    
    # Check if we should proceed with .env creation
    if ! check_env_file; then
        log "Skipping .env file creation"
        exit 0
    fi
    
    # Run interactive configuration
    configure_environment
    
    # Setup brain environment
    setup_brain_env
    
    # Create necessary directories
    create_directories
    
    # Validate configuration
    validate_configuration
    
    # Show next steps
    show_next_steps
}

# Run main function
main "$@"
