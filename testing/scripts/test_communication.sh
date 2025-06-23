#!/bin/bash

# Test script for Python-Rust communication via DragonflyDB
# This script tests the existing implementation rather than creating a new one

set -e

echo "🧪 Testing THE OVERMIND PROTOCOL communication..."

# Ensure DragonflyDB is running
if ! redis-cli ping > /dev/null; then
  echo "❌ DragonflyDB not running. Starting container..."
  docker run -d --name dragonfly -p 6379:6379 docker.dragonflydb.io/dragonflydb/dragonfly
  sleep 2
fi

echo "✅ DragonflyDB is running"

# Prepare test market data
test_data='{
  "event_id": "test-event-123",
  "symbol": "SOL/USDT",
  "price": 100.0,
  "volume": 1000000,
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
  "event_type": "PRICE_UPDATE",
  "metadata": {
    "trend": "bullish",
    "volatility": 0.02,
    "test_mode": true
  }
}'

# Send test market event
echo "📤 Sending test market event to DragonflyDB..."
redis-cli LPUSH overmind:market_events "$test_data"

echo "⏳ Waiting for AI Brain to process..."
sleep 2

# Check if AI Brain responded
response=$(redis-cli LRANGE overmind:trading_commands 0 -1)
if [ -z "$response" ]; then
  echo "❌ No response received from AI Brain"
  exit 1
else
  echo "✅ Received response from AI Brain:"
  echo "$response"
fi

echo "🎉 Communication test completed successfully!"