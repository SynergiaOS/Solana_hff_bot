#!/bin/bash
# Generate test report for Adaptive Cortex validation

REPORT_FILE="reports/adaptive_cortex_test_report.md"
LOG_FILE="logs/adaptive-cortex-test.log"
BRAIN_LOG="logs/ai-brain.log"

mkdir -p reports
touch $REPORT_FILE

echo "# Adaptive Cortex Test Report" > $REPORT_FILE
echo "**Date:** $(date)" >> $REPORT_FILE
echo "**Environment:** Solana Devnet" >> $REPORT_FILE
echo "**System:** THE OVERMIND PROTOCOL" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "## Test Results Summary" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Check AGGRESSIVE_GROWTH profile activation
if grep -q "Activating AGGRESSIVE_GROWTH profile" $BRAIN_LOG; then
  echo "✅ **PHASE 1:** AGGRESSIVE_GROWTH profile activated successfully" >> $REPORT_FILE
else
  echo "❌ **PHASE 1:** AGGRESSIVE_GROWTH profile activation failed" >> $REPORT_FILE
fi

# Check memecoin signal processing in AGGRESSIVE_GROWTH
if grep -q "Processing 'memecoin_launch' signal" $BRAIN_LOG; then
  echo "✅ **PHASE 1:** Memecoin signal processed correctly in AGGRESSIVE_GROWTH" >> $REPORT_FILE
else
  echo "❌ **PHASE 1:** Memecoin signal processing failed in AGGRESSIVE_GROWTH" >> $REPORT_FILE
fi

# Check arbitrage signal filtering in AGGRESSIVE_GROWTH
if grep -q "Ignoring 'arbitrage' signal" $BRAIN_LOG; then
  echo "✅ **PHASE 1:** Arbitrage signal correctly filtered in AGGRESSIVE_GROWTH" >> $REPORT_FILE
else
  echo "❌ **PHASE 1:** Arbitrage signal filtering failed in AGGRESSIVE_GROWTH" >> $REPORT_FILE
fi

# Check BALANCED_RISK profile switch
if grep -q "Switching to BALANCED_RISK profile" $BRAIN_LOG; then
  echo "✅ **PHASE 2:** BALANCED_RISK profile switch successful" >> $REPORT_FILE
else
  echo "❌ **PHASE 2:** BALANCED_RISK profile switch failed" >> $REPORT_FILE
fi

# Check signal filtering after switch
if grep -q "Ignoring 'memecoin_hunter' signal.*BALANCED_RISK" $BRAIN_LOG; then
  echo "✅ **PHASE 2:** Memecoin signal correctly filtered in BALANCED_RISK" >> $REPORT_FILE
else
  echo "❌ **PHASE 2:** Memecoin signal filtering failed in BALANCED_RISK" >> $REPORT_FILE
fi

if grep -q "Processing 'arbitrage_opportunity' signal" $BRAIN_LOG; then
  echo "✅ **PHASE 2:** Arbitrage signal processed correctly in BALANCED_RISK" >> $REPORT_FILE
else
  echo "❌ **PHASE 2:** Arbitrage signal processing failed in BALANCED_RISK" >> $REPORT_FILE
fi

# Check CAPITAL_PRESERVATION profile switch
if grep -q "Target goal.*reached.*Switching to CAPITAL_PRESERVATION" $BRAIN_LOG; then
  echo "✅ **PHASE 3:** CAPITAL_PRESERVATION profile switch successful" >> $REPORT_FILE
else
  echo "❌ **PHASE 3:** CAPITAL_PRESERVATION profile switch failed" >> $REPORT_FILE
fi

# Check risky signal filtering in preservation mode
if grep -q "Ignoring.*risky.*CAPITAL_PRESERVATION" $BRAIN_LOG; then
  echo "✅ **PHASE 3:** Risky signal correctly filtered in CAPITAL_PRESERVATION" >> $REPORT_FILE
else
  echo "❌ **PHASE 3:** Risky signal filtering failed in CAPITAL_PRESERVATION" >> $REPORT_FILE
fi

echo "" >> $REPORT_FILE
echo "## Detailed Log Excerpts" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "### PHASE 1: AGGRESSIVE_GROWTH" >> $REPORT_FILE
echo '```' >> $REPORT_FILE
grep -A 5 "PHASE 1" $LOG_FILE >> $REPORT_FILE
echo '```' >> $REPORT_FILE

echo "" >> $REPORT_FILE
echo "### PHASE 2: BALANCED_RISK" >> $REPORT_FILE
echo '```' >> $REPORT_FILE
grep -A 5 "PHASE 2" $LOG_FILE >> $REPORT_FILE
echo '```' >> $REPORT_FILE

echo "" >> $REPORT_FILE
echo "### PHASE 3: CAPITAL_PRESERVATION" >> $REPORT_FILE
echo '```' >> $REPORT_FILE
grep -A 5 "PHASE 3" $LOG_FILE >> $REPORT_FILE
echo '```' >> $REPORT_FILE

echo "" >> $REPORT_FILE
echo "## Conclusion" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Count successes
SUCCESS_COUNT=$(grep -c "✅" $REPORT_FILE)
TOTAL_TESTS=8

if [ $SUCCESS_COUNT -eq $TOTAL_TESTS ]; then
  echo "🎯 **TEST PASSED:** All $TOTAL_TESTS test criteria were met successfully." >> $REPORT_FILE
  echo "" >> $REPORT_FILE
  echo "The Adaptive Cortex system correctly implemented dynamic strategy switching based on portfolio balance changes. The system properly activated different profiles at appropriate thresholds and correctly filtered trading signals according to the active profile rules." >> $REPORT_FILE
else
  echo "⚠️ **PARTIAL SUCCESS:** $SUCCESS_COUNT out of $TOTAL_TESTS test criteria were met." >> $REPORT_FILE
  echo "" >> $REPORT_FILE
  echo "Some aspects of the Adaptive Cortex system require further investigation. See the detailed results above to identify specific issues." >> $REPORT_FILE
fi

echo "" >> $REPORT_FILE
echo "## Next Steps" >> $REPORT_FILE
echo "" >> $REPORT_FILE
echo "1. Address any failed test criteria" >> $REPORT_FILE
echo "2. Proceed with long-term validation on Mainnet in paper trading mode" >> $REPORT_FILE
echo "3. Monitor system behavior over extended periods" >> $REPORT_FILE
echo "4. Fine-tune threshold values based on real-world performance" >> $REPORT_FILE

echo "Test report generated: $REPORT_FILE"