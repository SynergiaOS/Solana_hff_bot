#!/bin/bash

# ============================================================================
# THE OVERMIND PROTOCOL - 48-Hour Validation Monitoring Script
# ============================================================================
# This script monitors THE OVERMIND PROTOCOL during validation period

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/overmind"
LOG_DIR="$PROJECT_DIR/logs"
VALIDATION_START_FILE="$PROJECT_DIR/.validation_start"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

# ============================================================================
# VALIDATION TRACKING
# ============================================================================

start_validation() {
    echo "$(date +%s)" > "$VALIDATION_START_FILE"
    log "🎯 48-hour validation period started"
}

get_validation_progress() {
    if [ ! -f "$VALIDATION_START_FILE" ]; then
        echo "0"
        return
    fi
    
    start_time=$(cat "$VALIDATION_START_FILE")
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    # 48 hours = 172800 seconds
    progress=$((elapsed * 100 / 172800))
    
    if [ $progress -gt 100 ]; then
        progress=100
    fi
    
    echo "$progress"
}

get_time_remaining() {
    if [ ! -f "$VALIDATION_START_FILE" ]; then
        echo "48:00:00"
        return
    fi
    
    start_time=$(cat "$VALIDATION_START_FILE")
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    # 48 hours = 172800 seconds
    remaining=$((172800 - elapsed))
    
    if [ $remaining -le 0 ]; then
        echo "00:00:00"
        return
    fi
    
    hours=$((remaining / 3600))
    minutes=$(((remaining % 3600) / 60))
    seconds=$((remaining % 60))
    
    printf "%02d:%02d:%02d" $hours $minutes $seconds
}

# ============================================================================
# SYSTEM HEALTH CHECKS
# ============================================================================

check_container_health() {
    log "🔍 Checking container health..."
    
    # Get container status
    containers=$(docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Status}}")
    
    echo "$containers" | while IFS=$'\t' read -r name state status; do
        if [ "$name" = "Name" ]; then
            continue
        fi
        
        if [[ "$state" == *"Up"* ]]; then
            success "✅ $name: $status"
        else
            error "❌ $name: $state - $status"
        fi
    done
}

check_api_endpoints() {
    log "🌐 Checking API endpoints..."
    
    # Trading System
    if curl -f -s http://localhost:8080/health > /dev/null; then
        success "✅ Trading System API (8080)"
    else
        error "❌ Trading System API (8080)"
    fi
    
    # Grafana
    if curl -f -s http://localhost:3001 > /dev/null; then
        success "✅ Grafana Dashboard (3001)"
    else
        error "❌ Grafana Dashboard (3001)"
    fi
    
    # Prometheus
    if curl -f -s http://localhost:9090 > /dev/null; then
        success "✅ Prometheus Metrics (9090)"
    else
        error "❌ Prometheus Metrics (9090)"
    fi
    
    # Chroma Vector DB
    if curl -f -s http://localhost:8000/api/v1/heartbeat > /dev/null; then
        success "✅ Chroma Vector DB (8000)"
    else
        error "❌ Chroma Vector DB (8000)"
    fi
}

check_trading_metrics() {
    log "📊 Checking trading metrics..."
    
    # Get trading system metrics
    metrics=$(curl -s http://localhost:8080/metrics 2>/dev/null || echo "")
    
    if [ -n "$metrics" ]; then
        # Extract key metrics
        signals_processed=$(echo "$metrics" | grep "signals_processed" | tail -1 | awk '{print $2}' || echo "0")
        decisions_made=$(echo "$metrics" | grep "decisions_made" | tail -1 | awk '{print $2}' || echo "0")
        paper_trades=$(echo "$metrics" | grep "paper_trades" | tail -1 | awk '{print $2}' || echo "0")
        
        info "📈 Signals Processed: $signals_processed"
        info "🧠 AI Decisions Made: $decisions_made"
        info "📝 Paper Trades: $paper_trades"
    else
        warning "⚠️ Could not retrieve trading metrics"
    fi
}

check_system_resources() {
    log "💻 Checking system resources..."
    
    # CPU Usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    info "🖥️ CPU Usage: ${cpu_usage}%"
    
    # Memory Usage
    memory_info=$(free -h | grep "Mem:")
    memory_used=$(echo $memory_info | awk '{print $3}')
    memory_total=$(echo $memory_info | awk '{print $2}')
    info "💾 Memory Usage: $memory_used / $memory_total"
    
    # Disk Usage
    disk_usage=$(df -h / | tail -1 | awk '{print $5}')
    info "💿 Disk Usage: $disk_usage"
    
    # Docker Stats
    info "🐳 Docker Container Resources:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -6
}

# ============================================================================
# LOG ANALYSIS
# ============================================================================

analyze_recent_logs() {
    log "📋 Analyzing recent logs..."
    
    # Check for errors in the last hour
    error_count=$(docker-compose logs --since=1h 2>/dev/null | grep -i "error" | wc -l)
    warning_count=$(docker-compose logs --since=1h 2>/dev/null | grep -i "warning" | wc -l)
    
    if [ $error_count -gt 0 ]; then
        warning "⚠️ Found $error_count errors in the last hour"
        echo "Recent errors:"
        docker-compose logs --since=1h 2>/dev/null | grep -i "error" | tail -5
    else
        success "✅ No errors in the last hour"
    fi
    
    if [ $warning_count -gt 0 ]; then
        info "ℹ️ Found $warning_count warnings in the last hour"
    fi
}

show_recent_trading_activity() {
    log "💹 Recent trading activity..."
    
    # Show last 10 trading decisions from logs
    echo "Last 10 AI trading decisions:"
    docker-compose logs overmind-trading 2>/dev/null | grep -i "decision\|trade\|signal" | tail -10 || echo "No recent trading activity found"
}

# ============================================================================
# MAIN MONITORING FUNCTIONS
# ============================================================================

show_validation_status() {
    clear
    echo "============================================================================"
    echo "🎯 THE OVERMIND PROTOCOL - 48-Hour Validation Monitor"
    echo "============================================================================"
    echo
    
    progress=$(get_validation_progress)
    remaining=$(get_time_remaining)
    
    echo "📅 Validation Progress: $progress% complete"
    echo "⏰ Time Remaining: $remaining"
    echo
    
    # Progress bar
    bar_length=50
    filled_length=$((progress * bar_length / 100))
    bar=$(printf "%*s" $filled_length | tr ' ' '█')
    empty=$(printf "%*s" $((bar_length - filled_length)) | tr ' ' '░')
    echo "Progress: [$bar$empty] $progress%"
    echo
}

run_full_health_check() {
    show_validation_status
    check_container_health
    echo
    check_api_endpoints
    echo
    check_trading_metrics
    echo
    check_system_resources
    echo
    analyze_recent_logs
    echo
    show_recent_trading_activity
    echo
    echo "============================================================================"
    echo "Next check in 5 minutes... (Ctrl+C to exit)"
    echo "============================================================================"
}

# ============================================================================
# INTERACTIVE MENU
# ============================================================================

show_menu() {
    clear
    show_validation_status
    echo
    echo "🎛️ Monitoring Options:"
    echo "1) Full Health Check"
    echo "2) View Live Logs"
    echo "3) Check Trading Metrics"
    echo "4) System Resources"
    echo "5) Start Validation Timer"
    echo "6) Continuous Monitoring (5min intervals)"
    echo "7) Emergency Stop"
    echo "8) Exit"
    echo
    read -p "Select option (1-8): " choice
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    cd "$PROJECT_DIR" || exit 1
    
    case "${1:-menu}" in
        "start")
            start_validation
            ;;
        "status")
            show_validation_status
            ;;
        "health")
            run_full_health_check
            ;;
        "continuous")
            log "🔄 Starting continuous monitoring (5-minute intervals)"
            while true; do
                run_full_health_check
                sleep 300  # 5 minutes
            done
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "stop")
            warning "🛑 Emergency stop requested"
            docker-compose down
            success "System stopped"
            ;;
        "menu"|*)
            while true; do
                show_menu
                case $choice in
                    1)
                        run_full_health_check
                        read -p "Press Enter to continue..."
                        ;;
                    2)
                        docker-compose logs -f
                        ;;
                    3)
                        check_trading_metrics
                        read -p "Press Enter to continue..."
                        ;;
                    4)
                        check_system_resources
                        read -p "Press Enter to continue..."
                        ;;
                    5)
                        start_validation
                        success "Validation timer started"
                        read -p "Press Enter to continue..."
                        ;;
                    6)
                        log "🔄 Starting continuous monitoring..."
                        while true; do
                            run_full_health_check
                            sleep 300
                        done
                        ;;
                    7)
                        warning "🛑 Emergency stop requested"
                        read -p "Are you sure? (y/N): " -n 1 -r
                        echo
                        if [[ $REPLY =~ ^[Yy]$ ]]; then
                            docker-compose down
                            success "System stopped"
                            exit 0
                        fi
                        ;;
                    8)
                        log "👋 Exiting monitor"
                        exit 0
                        ;;
                    *)
                        error "Invalid option"
                        ;;
                esac
            done
            ;;
    esac
}

# Run main function with all arguments
main "$@"
