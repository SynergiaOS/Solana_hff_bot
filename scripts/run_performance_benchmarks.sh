#!/bin/bash

# THE OVERMIND PROTOCOL Performance Benchmark Runner
# Comprehensive performance testing suite with detailed reporting

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BENCHMARK_DIR="target/criterion"
REPORT_DIR="performance_reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="${REPORT_DIR}/performance_report_${TIMESTAMP}.md"

# Create directories
mkdir -p "$REPORT_DIR"
mkdir -p logs

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "logs/benchmark_${TIMESTAMP}.log"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1" | tee -a "logs/benchmark_${TIMESTAMP}.log"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1" | tee -a "logs/benchmark_${TIMESTAMP}.log"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1" | tee -a "logs/benchmark_${TIMESTAMP}.log"
}

print_header() {
    echo -e "\n${PURPLE}================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================${NC}\n"
}

# System information gathering
gather_system_info() {
    log "Gathering system information..."
    
    cat > "${REPORT_DIR}/system_info_${TIMESTAMP}.txt" << EOF
THE OVERMIND PROTOCOL Performance Benchmark Report
Generated: $(date)
System Information:
==================

CPU Information:
$(lscpu 2>/dev/null || echo "lscpu not available")

Memory Information:
$(free -h 2>/dev/null || echo "free not available")

Disk Information:
$(df -h 2>/dev/null || echo "df not available")

Rust Version:
$(rustc --version 2>/dev/null || echo "rustc not available")

Cargo Version:
$(cargo --version 2>/dev/null || echo "cargo not available")

Git Commit:
$(git rev-parse HEAD 2>/dev/null || echo "Not a git repository")

EOF
    
    log_success "System information gathered"
}

# Pre-benchmark system optimization
optimize_system() {
    log "Optimizing system for benchmarking..."
    
    # Set CPU governor to performance (if available)
    if command -v cpupower >/dev/null 2>&1; then
        sudo cpupower frequency-set -g performance 2>/dev/null || log_warning "Could not set CPU governor to performance"
    fi
    
    # Disable CPU frequency scaling (if available)
    if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
        echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || log_warning "Could not disable CPU frequency scaling"
    fi
    
    # Set process priority
    renice -n -10 $$ 2>/dev/null || log_warning "Could not set process priority"
    
    log_success "System optimization completed"
}

# Run individual benchmark
run_benchmark() {
    local benchmark_name=$1
    local benchmark_file=$2
    
    print_header "Running $benchmark_name Benchmark"
    
    log "Starting $benchmark_name benchmark..."
    
    # Run the benchmark with detailed output
    if cargo bench --bench "$benchmark_file" -- --output-format html 2>&1 | tee "logs/${benchmark_file}_${TIMESTAMP}.log"; then
        log_success "$benchmark_name benchmark completed successfully"
        return 0
    else
        log_error "$benchmark_name benchmark failed"
        return 1
    fi
}

# Generate performance report
generate_report() {
    log "Generating performance report..."
    
    cat > "$REPORT_FILE" << EOF
# THE OVERMIND PROTOCOL Performance Benchmark Report

**Generated:** $(date)  
**System:** $(uname -a)  
**Rust Version:** $(rustc --version)  
**Git Commit:** $(git rev-parse HEAD 2>/dev/null || echo "Unknown")

## Executive Summary

This report contains comprehensive performance benchmarks for THE OVERMIND PROTOCOL,
focusing on ultra-low latency execution, high throughput processing, and system scalability.

## Benchmark Categories

### 1. 🚀 Ultra-Low Latency Benchmarks
- **Target:** Sub-millisecond execution times
- **Focus:** Critical path operations, memory access patterns, atomic operations
- **Results:** See \`latency_benchmarks\` section below

### 2. 📈 Throughput Benchmarks  
- **Target:** High transactions per second (TPS)
- **Focus:** Batch processing, concurrent operations, data aggregation
- **Results:** See \`throughput_benchmarks\` section below

### 3. 🎯 Overall Performance Benchmarks
- **Target:** End-to-end system performance
- **Focus:** Configuration creation, signal processing, AI decisions
- **Results:** See \`overmind_performance_benchmarks\` section below

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Order Processing Latency | < 500μs | ⏳ Testing |
| Market Data Processing | > 100k updates/sec | ⏳ Testing |
| AI Decision Latency | < 25ms | ⏳ Testing |
| Memory Allocation | < 100μs | ⏳ Testing |
| Network Simulation | < 1ms | ⏳ Testing |

## Detailed Results

EOF

    # Add benchmark results if available
    if [ -d "$BENCHMARK_DIR" ]; then
        echo "### Benchmark Results Directory Structure" >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        find "$BENCHMARK_DIR" -type f -name "*.html" | head -20 >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
    fi
    
    # Add system information
    echo "## System Information" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    cat "${REPORT_DIR}/system_info_${TIMESTAMP}.txt" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    
    log_success "Performance report generated: $REPORT_FILE"
}

# Analyze benchmark results
analyze_results() {
    log "Analyzing benchmark results..."
    
    local analysis_file="${REPORT_DIR}/analysis_${TIMESTAMP}.txt"
    
    cat > "$analysis_file" << EOF
THE OVERMIND PROTOCOL Benchmark Analysis
=======================================

Analysis performed: $(date)

Performance Analysis:
EOF
    
    # Check if criterion results exist
    if [ -d "$BENCHMARK_DIR" ]; then
        echo "Criterion benchmark results found in: $BENCHMARK_DIR" >> "$analysis_file"
        
        # Count benchmark files
        local html_count=$(find "$BENCHMARK_DIR" -name "*.html" | wc -l)
        echo "HTML reports generated: $html_count" >> "$analysis_file"
        
        # List benchmark categories
        echo "" >> "$analysis_file"
        echo "Benchmark Categories:" >> "$analysis_file"
        find "$BENCHMARK_DIR" -name "report" -type d | while read -r dir; do
            echo "  - $(basename "$(dirname "$dir")")" >> "$analysis_file"
        done
    else
        echo "No criterion results found. Benchmarks may have failed." >> "$analysis_file"
    fi
    
    log_success "Benchmark analysis completed: $analysis_file"
}

# Main execution
main() {
    print_header "THE OVERMIND PROTOCOL Performance Benchmark Suite"
    
    log "Starting comprehensive performance benchmarking..."
    
    # Gather system information
    gather_system_info
    
    # Optimize system for benchmarking
    optimize_system
    
    # Build the project first
    log "Building project in release mode..."
    if cargo build --release; then
        log_success "Project built successfully"
    else
        log_error "Project build failed"
        exit 1
    fi
    
    # Run benchmarks
    local failed_benchmarks=0
    
    # 1. Overall performance benchmarks
    if ! run_benchmark "Overall Performance" "overmind_performance_benchmarks"; then
        ((failed_benchmarks++))
    fi
    
    # 2. Latency benchmarks
    if ! run_benchmark "Ultra-Low Latency" "latency_benchmarks"; then
        ((failed_benchmarks++))
    fi
    
    # 3. Throughput benchmarks  
    if ! run_benchmark "High Throughput" "throughput_benchmarks"; then
        ((failed_benchmarks++))
    fi
    
    # Generate reports
    generate_report
    analyze_results
    
    # Summary
    print_header "Benchmark Summary"
    
    if [ $failed_benchmarks -eq 0 ]; then
        log_success "All benchmarks completed successfully! 🎉"
        log "📊 Reports available in: $REPORT_DIR"
        log "📈 Criterion HTML reports: $BENCHMARK_DIR"
        log "📋 Detailed logs: logs/"
    else
        log_warning "$failed_benchmarks benchmark(s) failed"
        log "Check logs for details: logs/"
    fi
    
    # Open results if on desktop
    if command -v xdg-open >/dev/null 2>&1; then
        log "Opening benchmark results..."
        xdg-open "$BENCHMARK_DIR" 2>/dev/null || true
    fi
    
    log "Performance benchmarking completed!"
}

# Handle interrupts
trap 'log_error "Benchmark interrupted by user"; exit 130' INT TERM

# Run main function
main "$@"
