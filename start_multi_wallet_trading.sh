#!/bin/bash

echo "🏦 Starting THE OVERMIND PROTOCOL - Multi-Wallet System"

# Load multi-wallet environment (filter out comments)
export $(cat .env.multi-wallet | grep -v '^#' | grep -v '^$' | xargs)

# Check Redis
if ! docker ps | grep overmind-redis-live > /dev/null; then
    echo "🚀 Starting Redis..."
    docker run -d --name overmind-redis-live -p 6380:6379 --restart unless-stopped redis:alpine redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
    sleep 2
fi

echo "🏦 Multi-Wallet Configuration:"
echo "  - Primary Wallet: 40% allocation"
echo "  - HFT Wallet: 30% allocation (high-frequency)"
echo "  - Conservative Wallet: 20% allocation (low-risk)"
echo "  - Experimental Wallet: 10% allocation (testing)"

echo ""
echo "🎯 Enhanced Features:"
echo "  - Intelligent wallet routing"
echo "  - Strategy-specific allocation"
echo "  - Advanced risk management"
echo "  - Portfolio diversification"

echo ""
echo "🚀 Starting THE OVERMIND PROTOCOL with Multi-Wallet System..."

# Start with multi-wallet configuration
cargo run --release
