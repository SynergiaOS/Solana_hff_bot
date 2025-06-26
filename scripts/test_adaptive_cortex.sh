#!/bin/bash
# Test script for Adaptive Cortex validation

LOG_FILE="logs/adaptive-cortex-test.log"

echo "=== ADAPTIVE CORTEX TEST STARTED ===" | tee -a $LOG_FILE
date | tee -a $LOG_FILE

# FAZA 1: Test profilu AGGRESSIVE_GROWTH
echo "=== PHASE 1: AGGRESSIVE_GROWTH PROFILE TEST ===" | tee -a $LOG_FILE

# Set initial balance to 0.4 SOL (below 25% threshold)
echo "Setting initial balance to 0.4 SOL..." | tee -a $LOG_FILE
solana -u devnet transfer $DEVNET_WALLET 0.4 --allow-unfunded-recipient

# Wait for system to detect balance
echo "Waiting for system to detect balance (30s)..." | tee -a $LOG_FILE
sleep 30

# Check for profile activation in logs
echo "Checking for AGGRESSIVE_GROWTH profile activation..." | tee -a $LOG_FILE
grep "Activating AGGRESSIVE_GROWTH profile" logs/ai-brain.log | tail -1 | tee -a $LOG_FILE

# Test signal filtering - memecoin
echo "Sending memecoin signal..." | tee -a $LOG_FILE
redis-cli -h localhost -p 6379 LPUSH overmind:market_events '{"type":"memecoin_launch","symbol":"TEST","ca":"11111111111111111111111111111111","price":0.00001,"volume":50000}'
sleep 10

# Test signal filtering - arbitrage
echo "Sending arbitrage signal..." | tee -a $LOG_FILE
redis-cli -h localhost -p 6379 LPUSH overmind:market_events '{"type":"arbitrage_opportunity","symbol":"SOL/USDC","dex1":"Raydium","dex2":"Orca","price_diff_pct":1.2}'
sleep 10

# Check signal processing results
echo "Checking signal processing results..." | tee -a $LOG_FILE
grep "memecoin" logs/ai-brain.log | tail -3 | tee -a $LOG_FILE
grep "arbitrage" logs/ai-brain.log | tail -3 | tee -a $LOG_FILE

# FAZA 2: Test przełączenia na BALANCED_RISK
echo "=== PHASE 2: BALANCED_RISK PROFILE SWITCH TEST ===" | tee -a $LOG_FILE

# Increase balance to 1.0 SOL (25-100% threshold)
echo "Increasing balance to 1.0 SOL..." | tee -a $LOG_FILE
solana -u devnet transfer $DEVNET_WALLET 0.6 --allow-unfunded-recipient

# Wait for system to detect balance change
echo "Waiting for system to detect balance change (60s)..." | tee -a $LOG_FILE
sleep 60

# Check for profile switch in logs
echo "Checking for BALANCED_RISK profile switch..." | tee -a $LOG_FILE
grep "Switching to BALANCED_RISK profile" logs/ai-brain.log | tail -1 | tee -a $LOG_FILE

# Test signal filtering after switch
echo "Re-sending test signals..." | tee -a $LOG_FILE
redis-cli -h localhost -p 6379 LPUSH overmind:market_events '{"type":"memecoin_launch","symbol":"TEST","ca":"11111111111111111111111111111111","price":0.00001,"volume":50000}'
sleep 10
redis-cli -h localhost -p 6379 LPUSH overmind:market_events '{"type":"arbitrage_opportunity","symbol":"SOL/USDC","dex1":"Raydium","dex2":"Orca","price_diff_pct":1.2}'
sleep 10

# Check signal processing results after switch
echo "Checking signal processing results after switch..." | tee -a $LOG_FILE
grep "memecoin" logs/ai-brain.log | tail -3 | tee -a $LOG_FILE
grep "arbitrage" logs/ai-brain.log | tail -3 | tee -a $LOG_FILE

# FAZA 3: Test przełączenia na CAPITAL_PRESERVATION
echo "=== PHASE 3: CAPITAL_PRESERVATION PROFILE SWITCH TEST ===" | tee -a $LOG_FILE

# Increase balance to 2.1 SOL (>100% threshold)
echo "Increasing balance to 2.1 SOL..." | tee -a $LOG_FILE
solana -u devnet transfer $DEVNET_WALLET 1.1 --allow-unfunded-recipient

# Wait for system to detect goal achievement
echo "Waiting for system to detect goal achievement (60s)..." | tee -a $LOG_FILE
sleep 60

# Check for profile switch in logs
echo "Checking for CAPITAL_PRESERVATION profile switch..." | tee -a $LOG_FILE
grep "Target goal.*reached" logs/ai-brain.log | tail -1 | tee -a $LOG_FILE

# Test risky signal filtering
echo "Sending risky signal..." | tee -a $LOG_FILE
redis-cli -h localhost -p 6379 LPUSH overmind:market_events '{"type":"memecoin_launch","symbol":"TEST","ca":"11111111111111111111111111111111","price":0.00001,"volume":50000}'
sleep 10

# Check signal processing results in preservation mode
echo "Checking signal processing in preservation mode..." | tee -a $LOG_FILE
grep "Ignoring.*risky.*CAPITAL_PRESERVATION" logs/ai-brain.log | tail -3 | tee -a $LOG_FILE

echo "=== ADAPTIVE CORTEX TEST COMPLETED ===" | tee -a $LOG_FILE
date | tee -a $LOG_FILE