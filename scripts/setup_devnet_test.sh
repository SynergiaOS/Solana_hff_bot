#!/bin/bash
# Setup script for Adaptive Cortex testing on Devnet

# Set required environment variables
export SNIPER_TRADING_MODE=paper
export OVERMIND_MODE=enabled
export ADAPTIVE_CORTEX_ENABLED=true
export OVERMIND_AI_MODE=enabled
export ENVIRONMENT=devnet

# Configure logging
mkdir -p logs
touch logs/ai-brain.log
touch logs/adaptive-cortex-test.log

echo "Environment configured for Adaptive Cortex testing"