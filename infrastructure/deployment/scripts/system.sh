#!/bin/bash

# SNIPERCOR System Setup Script
# Automates installation of Rust, Docker, and system configuration for optimal HFT performance

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y curl wget git build-essential pkg-config libssl-dev
    log_success "System packages updated"
}

# Install Rust with nightly toolchain
install_rust() {
    log_info "Installing Rust..."
    
    if command -v rustc &> /dev/null; then
        log_warning "Rust is already installed. Updating..."
        rustup update
    else
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source ~/.cargo/env
    fi
    
    # Install nightly toolchain
    rustup toolchain install nightly
    rustup component add rustfmt clippy
    
    # Verify installation
    rustc --version
    cargo --version
    
    log_success "Rust installed successfully"
}

# Install Docker and Docker Compose
install_docker() {
    log_info "Installing Docker..."
    
    if command -v docker &> /dev/null; then
        log_warning "Docker is already installed"
    else
        # Add Docker's official GPG key
        sudo apt update
        sudo apt install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        
        # Add Docker repository
        echo \
          "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
          "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
          sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
        
        # Add user to docker group
        sudo usermod -aG docker $USER
        
        log_success "Docker installed successfully"
        log_warning "Please log out and log back in for Docker group changes to take effect"
    fi
}

# Configure system for HFT performance
configure_system() {
    log_info "Configuring system for HFT performance..."
    
    # Set CPU governor to performance mode
    echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils
    
    # Optimize network settings
    sudo tee /etc/sysctl.d/99-snipercor.conf > /dev/null <<EOF
# Network optimizations for HFT
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr

# Memory optimizations
vm.swappiness = 1
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File descriptor limits
fs.file-max = 2097152
EOF
    
    # Apply sysctl settings
    sudo sysctl -p /etc/sysctl.d/99-snipercor.conf
    
    # Set ulimits for the user
    sudo tee -a /etc/security/limits.conf > /dev/null <<EOF
$USER soft nofile 65536
$USER hard nofile 65536
$USER soft nproc 32768
$USER hard nproc 32768
EOF
    
    log_success "System configured for HFT performance"
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    
    # Install ufw if not present
    sudo apt install -y ufw
    
    # Reset firewall rules
    sudo ufw --force reset
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (adjust port if needed)
    sudo ufw allow 22/tcp
    
    # Allow SNIPERCOR API port
    sudo ufw allow 8080/tcp
    
    # Allow Docker networks
    sudo ufw allow from 172.16.0.0/12
    
    # Enable firewall
    sudo ufw --force enable
    
    log_success "Firewall configured"
}

# Create environment file template
create_env_template() {
    log_info "Creating environment file template..."
    
    cat > .env.example <<EOF
# SNIPERCOR Configuration Template
# Copy this file to .env and fill in your actual values

# Trading Configuration
SNIPER_TRADING_MODE=paper
SNIPER_MAX_POSITION_SIZE=1000
SNIPER_MAX_DAILY_LOSS=500

# Solana Configuration
SNIPER_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SNIPER_WALLET_PRIVATE_KEY=your_wallet_private_key_here

# API Keys
SNIPER_HELIUS_API_KEY=your_helius_api_key_here
SNIPER_QUICKNODE_API_KEY=your_quicknode_api_key_here

# Database
SNIPER_DATABASE_URL=postgresql://sniper:password@localhost:5432/snipercor

# Server
SNIPER_SERVER_PORT=8080

# Logging
RUST_LOG=info
SNIPER_LOG_LEVEL=info
EOF
    
    log_success "Environment template created (.env.example)"
    log_warning "Remember to copy .env.example to .env and configure your actual values"
}

# Install additional tools
install_tools() {
    log_info "Installing additional development tools..."
    
    # Install PostgreSQL client
    sudo apt install -y postgresql-client
    
    # Install monitoring tools
    sudo apt install -y htop iotop nethogs
    
    # Install Rust tools
    cargo install cargo-watch cargo-audit cargo-outdated
    
    log_success "Additional tools installed"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Check Rust
    if command -v rustc &> /dev/null; then
        log_success "Rust: $(rustc --version)"
    else
        log_error "Rust installation failed"
        exit 1
    fi
    
    # Check Docker
    if command -v docker &> /dev/null; then
        log_success "Docker: $(docker --version)"
    else
        log_error "Docker installation failed"
        exit 1
    fi
    
    # Check system configuration
    if [[ -f /etc/sysctl.d/99-snipercor.conf ]]; then
        log_success "System configuration applied"
    else
        log_error "System configuration failed"
        exit 1
    fi
    
    log_success "All components verified successfully"
}

# Main execution
main() {
    log_info "Starting SNIPERCOR system setup..."
    
    check_root
    update_system
    install_rust
    install_docker
    configure_system
    configure_firewall
    create_env_template
    install_tools
    verify_installation
    
    log_success "SNIPERCOR system setup completed successfully!"
    log_info "Next steps:"
    echo "  1. Log out and log back in (for Docker group changes)"
    echo "  2. Copy .env.example to .env and configure your values"
    echo "  3. Run 'cargo build' to build the project"
    echo "  4. Run 'SNIPER_TRADING_MODE=paper cargo run' to start in paper trading mode"
}

# Run main function
main "$@"
