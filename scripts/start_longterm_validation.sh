#!/bin/bash

# THE OVERMIND PROTOCOL - 48-Hour Long-term Validation
# Extended stability and performance validation

set -e

echo "📊 THE OVERMIND PROTOCOL - 48-Hour Long-term Validation"
echo "======================================================="

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

# Configuration
VALIDATION_DURATION=172800  # 48 hours in seconds
CHECK_INTERVAL=300          # 5 minutes
LOG_DIR="./logs/validation"
METRICS_FILE="$LOG_DIR/validation_metrics.json"

# Create log directory
mkdir -p "$LOG_DIR"

# Initialize validation
initialize_validation() {
    log "Initializing 48-hour validation..."
    
    # Create initial metrics file
    cat > "$METRICS_FILE" << EOF
{
    "validation_start": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "duration_hours": 48,
    "checks": [],
    "summary": {
        "total_checks": 0,
        "successful_checks": 0,
        "failed_checks": 0,
        "uptime_percentage": 0.0
    }
}
EOF
    
    success "Validation initialized"
    echo "Metrics file: $METRICS_FILE"
    echo "Log directory: $LOG_DIR"
}

# Health check function
perform_health_check() {
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    local check_result="success"
    local issues=()
    
    # Check AI Brain
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        check_result="failed"
        issues+=("AI Brain not responding")
    fi
    
    # Check DragonflyDB
    if ! redis-cli ping > /dev/null 2>&1; then
        check_result="failed"
        issues+=("DragonflyDB not responding")
    fi
    
    # Check memory usage
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$memory_usage > 90.0" | bc -l) )); then
        check_result="warning"
        issues+=("High memory usage: ${memory_usage}%")
    fi
    
    # Check disk space
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        check_result="warning"
        issues+=("High disk usage: ${disk_usage}%")
    fi
    
    # Log check result
    local check_entry="{
        \"timestamp\": \"$timestamp\",
        \"status\": \"$check_result\",
        \"memory_usage\": $memory_usage,
        \"disk_usage\": $disk_usage,
        \"issues\": [$(printf '\"%s\",' "${issues[@]}" | sed 's/,$//')]
    }"
    
    # Update metrics file
    local temp_file=$(mktemp)
    jq ".checks += [$check_entry] | .summary.total_checks += 1 | 
        if \"$check_result\" == \"success\" then .summary.successful_checks += 1 
        else .summary.failed_checks += 1 end" "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    # Display status
    if [ "$check_result" = "success" ]; then
        success "Health check passed"
    elif [ "$check_result" = "warning" ]; then
        warning "Health check passed with warnings: ${issues[*]}"
    else
        error "Health check failed: ${issues[*]}"
    fi
    
    return 0
}

# Generate test signals periodically
generate_test_signals() {
    log "Generating periodic test signals..."
    
    # Generate random market signals every hour
    while true; do
        sleep 3600  # 1 hour
        
        local signal="{
            \"type\": \"market_update\",
            \"symbol\": \"SOL/USDT\",
            \"price\": $(echo "scale=2; 90 + $RANDOM % 20" | bc),
            \"volume\": $(echo "$RANDOM * 1000" | bc),
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
            \"source\": \"validation_test\"
        }"
        
        redis-cli lpush overmind:market_events "$signal" > /dev/null 2>&1 || true
        log "Generated test signal"
    done &
    
    echo $! > "$LOG_DIR/signal_generator.pid"
}

# Monitor system metrics
monitor_metrics() {
    log "Starting metrics monitoring..."
    
    while true; do
        # Collect system metrics
        local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
        local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
        local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
        
        # Log metrics
        echo "$timestamp,CPU:$cpu_usage,Memory:$memory_usage,Load:$load_avg" >> "$LOG_DIR/system_metrics.csv"
        
        sleep 60  # Log every minute
    done &
    
    echo $! > "$LOG_DIR/metrics_monitor.pid"
}

# Main validation loop
run_validation() {
    log "Starting 48-hour validation loop..."
    
    local start_time=$(date +%s)
    local end_time=$((start_time + VALIDATION_DURATION))
    local check_count=0
    
    # Start background processes
    generate_test_signals
    monitor_metrics
    
    while [ $(date +%s) -lt $end_time ]; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        local remaining=$((end_time - current_time))
        
        # Perform health check
        perform_health_check
        check_count=$((check_count + 1))
        
        # Display progress
        local hours_elapsed=$((elapsed / 3600))
        local hours_remaining=$((remaining / 3600))
        log "Validation progress: ${hours_elapsed}h elapsed, ${hours_remaining}h remaining (Check #$check_count)"
        
        # Sleep until next check
        sleep $CHECK_INTERVAL
    done
    
    success "48-hour validation completed!"
}

# Generate final report
generate_final_report() {
    log "Generating final validation report..."
    
    local report_file="$LOG_DIR/final_validation_report.md"
    local end_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    # Calculate final metrics
    local temp_file=$(mktemp)
    jq ".validation_end = \"$end_time\" | 
        .summary.uptime_percentage = (.summary.successful_checks / .summary.total_checks * 100)" \
        "$METRICS_FILE" > "$temp_file"
    mv "$temp_file" "$METRICS_FILE"
    
    # Generate report
    cat > "$report_file" << EOF
# THE OVERMIND PROTOCOL - 48-Hour Validation Report

**Validation Period:** $(jq -r '.validation_start' "$METRICS_FILE") to $end_time  
**Duration:** 48 hours  
**Status:** COMPLETED  

## Summary

- **Total Health Checks:** $(jq -r '.summary.total_checks' "$METRICS_FILE")
- **Successful Checks:** $(jq -r '.summary.successful_checks' "$METRICS_FILE")
- **Failed Checks:** $(jq -r '.summary.failed_checks' "$METRICS_FILE")
- **Uptime Percentage:** $(jq -r '.summary.uptime_percentage' "$METRICS_FILE")%

## System Performance

$(if [ -f "$LOG_DIR/system_metrics.csv" ]; then
    echo "### Resource Usage"
    echo "- Average CPU Usage: $(awk -F'CPU:' '{sum+=$2; count++} END {printf "%.1f%%", sum/count}' "$LOG_DIR/system_metrics.csv")"
    echo "- Average Memory Usage: $(awk -F'Memory:' '{sum+=$2; count++} END {printf "%.1f%%", sum/count}' "$LOG_DIR/system_metrics.csv")"
    echo "- Peak Load Average: $(awk -F'Load:' '{if($2>max) max=$2} END {print max}' "$LOG_DIR/system_metrics.csv")"
fi)

## Issues Encountered

$(jq -r '.checks[] | select(.status != "success") | "- \(.timestamp): \(.issues | join(", "))"' "$METRICS_FILE")

## Recommendations

$(local uptime=$(jq -r '.summary.uptime_percentage' "$METRICS_FILE")
if (( $(echo "$uptime >= 99.0" | bc -l) )); then
    echo "✅ **EXCELLENT:** System demonstrated high stability (${uptime}% uptime)"
    echo "✅ **RECOMMENDATION:** System is ready for production deployment"
elif (( $(echo "$uptime >= 95.0" | bc -l) )); then
    echo "⚠️ **GOOD:** System showed acceptable stability (${uptime}% uptime)"
    echo "⚠️ **RECOMMENDATION:** Address minor issues before production"
else
    echo "❌ **POOR:** System stability below acceptable threshold (${uptime}% uptime)"
    echo "❌ **RECOMMENDATION:** Investigate and fix stability issues"
fi)

## Next Steps

1. Review detailed metrics in: $METRICS_FILE
2. Analyze system performance logs
3. Address any identified issues
4. Proceed with production deployment (if stability is acceptable)

---
**Generated:** $end_time
EOF
    
    success "Final report generated: $report_file"
    
    # Display summary
    echo
    echo "================================================="
    echo "📊 48-HOUR VALIDATION SUMMARY"
    echo "================================================="
    cat "$report_file" | grep -A 10 "## Summary"
    echo "================================================="
}

# Cleanup function
cleanup() {
    log "Cleaning up validation processes..."
    
    # Kill background processes
    if [ -f "$LOG_DIR/signal_generator.pid" ]; then
        kill $(cat "$LOG_DIR/signal_generator.pid") 2>/dev/null || true
        rm -f "$LOG_DIR/signal_generator.pid"
    fi
    
    if [ -f "$LOG_DIR/metrics_monitor.pid" ]; then
        kill $(cat "$LOG_DIR/metrics_monitor.pid") 2>/dev/null || true
        rm -f "$LOG_DIR/metrics_monitor.pid"
    fi
}

# Main execution
main() {
    echo
    log "Starting THE OVERMIND PROTOCOL 48-hour validation..."
    echo
    
    # Check if jq and bc are available
    if ! command -v jq > /dev/null 2>&1; then
        error "jq is required but not installed. Please install jq."
        exit 1
    fi
    
    if ! command -v bc > /dev/null 2>&1; then
        error "bc is required but not installed. Please install bc."
        exit 1
    fi
    
    # Initialize validation
    initialize_validation
    
    # Run validation
    run_validation
    
    # Generate final report
    generate_final_report
    
    success "🎉 48-HOUR VALIDATION COMPLETED SUCCESSFULLY!"
    echo
    echo "Check the final report at: $LOG_DIR/final_validation_report.md"
}

# Set trap for cleanup
trap cleanup EXIT

# Check if running in background mode
if [ "$1" = "--background" ]; then
    log "Starting validation in background mode..."
    nohup "$0" > "$LOG_DIR/validation.log" 2>&1 &
    echo $! > "$LOG_DIR/validation.pid"
    success "Validation started in background (PID: $!)"
    echo "Monitor progress: tail -f $LOG_DIR/validation.log"
    exit 0
fi

# Run main validation
main "$@"
