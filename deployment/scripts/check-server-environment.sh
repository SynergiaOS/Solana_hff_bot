#!/bin/bash

# THE OVERMIND PROTOCOL - Server Environment Check
# Check what's available on Contabo VDS and install missing components

echo "🔍 THE OVERMIND PROTOCOL - Server Environment Check"
echo "=================================================="
echo ""

echo "Please run these commands on your Contabo VDS server:"
echo "ssh marcin@89.117.53.53"
echo ""
echo "Then copy and paste the following commands one by one:"
echo ""

cat << 'EOF'
# ============================================================================
# STEP 1: Check current environment
# ============================================================================
echo "🔍 Checking current server environment..."
echo ""

echo "Operating System:"
cat /etc/os-release | grep PRETTY_NAME

echo ""
echo "Available Memory:"
free -h

echo ""
echo "Available Disk Space:"
df -h /

echo ""
echo "CPU Information:"
nproc
cat /proc/cpuinfo | grep "model name" | head -1

echo ""
echo "Current User:"
whoami
pwd

echo ""
echo "Python Status:"
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found: $(python3 --version)"
    echo "Python3 path: $(which python3)"
else
    echo "❌ Python3 not found"
fi

if command -v python &> /dev/null; then
    echo "✅ Python found: $(python --version)"
    echo "Python path: $(which python)"
else
    echo "❌ Python not found"
fi

if command -v pip3 &> /dev/null; then
    echo "✅ pip3 found: $(pip3 --version)"
else
    echo "❌ pip3 not found"
fi

if command -v pip &> /dev/null; then
    echo "✅ pip found: $(pip --version)"
else
    echo "❌ pip not found"
fi

echo ""
echo "Rust Status:"
if command -v rustc &> /dev/null; then
    echo "✅ Rust found: $(rustc --version)"
else
    echo "❌ Rust not found"
fi

if command -v cargo &> /dev/null; then
    echo "✅ Cargo found: $(cargo --version)"
else
    echo "❌ Cargo not found"
fi

echo ""
echo "Docker Status:"
if command -v docker &> /dev/null; then
    echo "✅ Docker found: $(docker --version)"
    echo "Docker status:"
    sudo systemctl status docker --no-pager -l
else
    echo "❌ Docker not found"
fi

if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose found: $(docker-compose --version)"
else
    echo "❌ Docker Compose not found"
fi

echo ""
echo "Network Status:"
echo "External IP:"
curl -s ifconfig.me
echo ""
echo "Open ports:"
sudo netstat -tlnp | grep LISTEN

echo ""
echo "============================================================================"
echo "STEP 2: Install missing components"
echo "============================================================================"

# Update system
echo "📦 Updating system packages..."
sudo apt-get update -y

# Install Python if missing
if ! command -v python3 &> /dev/null; then
    echo "📦 Installing Python3..."
    sudo apt-get install -y python3 python3-pip python3-venv python3-dev
else
    echo "✅ Python3 already installed"
fi

# Install pip if missing
if ! command -v pip3 &> /dev/null; then
    echo "📦 Installing pip3..."
    sudo apt-get install -y python3-pip
else
    echo "✅ pip3 already installed"
fi

# Install essential packages
echo "📦 Installing essential packages..."
sudo apt-get install -y \
    curl \
    wget \
    git \
    htop \
    vim \
    unzip \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker if missing
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed - you may need to logout and login again"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose if missing
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Install Rust if missing (for local compilation if needed)
if ! command -v rustc &> /dev/null; then
    echo "📦 Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
    echo "✅ Rust installed"
else
    echo "✅ Rust already installed"
fi

echo ""
echo "============================================================================"
echo "STEP 3: Verify installation"
echo "============================================================================"

echo "🔍 Verifying installations..."
echo ""

echo "Python3: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "pip3: $(pip3 --version 2>/dev/null || echo 'Not found')"
echo "Docker: $(docker --version 2>/dev/null || echo 'Not found')"
echo "Docker Compose: $(docker-compose --version 2>/dev/null || echo 'Not found')"
echo "Rust: $(rustc --version 2>/dev/null || echo 'Not found')"
echo "Cargo: $(cargo --version 2>/dev/null || echo 'Not found')"

echo ""
echo "🔧 Testing Docker..."
if command -v docker &> /dev/null; then
    if docker run --rm hello-world > /dev/null 2>&1; then
        echo "✅ Docker is working correctly"
    else
        echo "⚠️  Docker installed but may need configuration"
        echo "Try: sudo systemctl start docker"
        echo "Or logout and login again to refresh group membership"
    fi
else
    echo "❌ Docker not available"
fi

echo ""
echo "🔧 Testing Python packages..."
if command -v pip3 &> /dev/null; then
    echo "Installing basic Python packages for THE OVERMIND PROTOCOL..."
    pip3 install --user --upgrade pip setuptools wheel
    echo "✅ Basic Python packages installed"
else
    echo "❌ pip3 not available"
fi

echo ""
echo "============================================================================"
echo "STEP 4: Setup directories"
echo "============================================================================"

echo "📁 Creating project directories..."
mkdir -p /home/marcin/overmind-protocol
mkdir -p /home/marcin/backups/overmind
mkdir -p /home/marcin/logs/overmind

echo "✅ Directories created:"
ls -la /home/marcin/

echo ""
echo "============================================================================"
echo "ENVIRONMENT SETUP COMPLETED!"
echo "============================================================================"
echo ""
echo "✅ Your Contabo VDS is now ready for THE OVERMIND PROTOCOL deployment"
echo ""
echo "Next steps:"
echo "1. Exit this SSH session: exit"
echo "2. Run the deployment script from your local machine"
echo "3. Or manually sync files and continue with Docker deployment"
echo ""
echo "If you had to install Docker, you may need to:"
echo "1. Logout: exit"
echo "2. Login again: ssh marcin@89.117.53.53"
echo "3. Test Docker: docker run --rm hello-world"
EOF
