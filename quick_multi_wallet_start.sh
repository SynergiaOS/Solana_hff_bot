#!/bin/bash

# 🏦 THE OVERMIND PROTOCOL - Quick Multi-Wallet Start
# Simple startup without environment parsing issues

echo "🏦 Starting THE OVERMIND PROTOCOL - Multi-Wallet System"

# Check Redis
if ! docker ps | grep overmind-redis-live > /dev/null; then
    echo "🚀 Starting Redis..."
    docker run -d --name overmind-redis-live -p 6380:6379 --restart unless-stopped redis:alpine redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
    sleep 2
fi

echo "🏦 Multi-Wallet Configuration Active"
echo "🚀 Starting THE OVERMIND PROTOCOL..."

# Set environment variables directly
export SNIPER_TRADING_MODE=live
export PAPER_TRADING_MODE=false
export SNIPER_FORCE_REAL_MODE=true
export OVERMIND_MULTI_WALLET_ENABLED=true
export OVERMIND_DEFAULT_WALLET=primary_wallet
export SNIPER_MAX_POSITION_SIZE=0.25
export SNIPER_MAX_DAILY_LOSS=0.15
export SNIPER_AI_CONFIDENCE_THRESHOLD=0.50
export SNIPER_AI_MAX_TRADES_PER_HOUR=30
export SNIPER_SOLANA_RPC_URL="https://distinguished-blue-glade.solana-mainnet.quiknode.pro/a10fad0f63cdfe46533f1892ac720517b08fe580"
export SNIPER_WALLET_PRIVATE_KEY="[4,72,104,80,115,72,122,99,111,106,111,114,55,120,66,76,111,107,68,57,119,55,84,54,106,72,70,88,118,86,70,107,67,115,107,78,56,104,71,83,78,75,51,54,67,122,78,80,72,120,82,82,106,53,68,103,54,82,67,99,103,55,57,83,83,87,109,89,118,87,69,119,83,119,107,49,50,67,111,82,120,118,50,87,53,57]"
export OVERMIND_AI_ENABLED=true
export DRAGONFLY_URL="redis://127.0.0.1:6380"
export SNIPER_SERVER_PORT=8082
export SNIPER_LOG_LEVEL=info

# Start THE OVERMIND PROTOCOL
cargo run --release
