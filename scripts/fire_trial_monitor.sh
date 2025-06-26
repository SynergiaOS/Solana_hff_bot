#!/bin/bash
# THE OVERMIND PROTOCOL - Fire Trial Monitoring Script
# Automated monitoring for 48-hour mainnet paper trading validation

# Configuration
TRIAL_START_TIME=$(date +%s)
TRIAL_DURATION=172800  # 48 hours in seconds
LOG_FILE="fire-trial-monitor.log"
ALERT_FILE="fire-trial-alerts.log"
STATUS_FILE="fire-trial-status.json"
CHECK_INTERVAL=300     # 5 minutes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize log files
echo "🔥 Fire Trial Protocol Monitoring Started: $(date)" | tee $LOG_FILE
echo "[]" > $STATUS_FILE

# Function to log with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Function to send alert
send_alert() {
    local severity=$1
    local message=$2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$severity] $message" | tee -a $ALERT_FILE
    log_message "ALERT [$severity]: $message"
}

# Function to check system health
check_system_health() {
    local status="HEALTHY"
    local issues=()
    
    # Check OVERMIND process
    if ! pgrep -f "overmind_hft_executor" > /dev/null; then
        issues+=("OVERMIND process not running")
        status="CRITICAL"
    fi
    
    # Check Docker services
    local docker_count=$(docker ps --filter "status=running" | grep -c -E "(mission-control|dragonfly|prometheus|grafana)")
    if [ $docker_count -lt 3 ]; then
        issues+=("Docker services down (only $docker_count running)")
        status="CRITICAL"
    fi
    
    # Check paper trading mode
    if ! grep -q "PAPER_TRADING_MODE=true" .env 2>/dev/null; then
        issues+=("Paper trading mode not confirmed")
        status="CRITICAL"
    fi
    
    # Check Mission Control accessibility
    if ! curl -s -f http://localhost:8501/health > /dev/null 2>&1; then
        issues+=("Mission Control not accessible")
        status="WARNING"
    fi
    
    # Check DragonflyDB
    if ! echo "PING" | nc -w 2 localhost 6379 | grep -q "PONG" 2>/dev/null; then
        issues+=("DragonflyDB not responding")
        status="WARNING"
    fi
    
    # Check disk space
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $disk_usage -gt 90 ]; then
        issues+=("Disk usage critical: ${disk_usage}%")
        status="CRITICAL"
    elif [ $disk_usage -gt 80 ]; then
        issues+=("Disk usage high: ${disk_usage}%")
        if [ "$status" = "HEALTHY" ]; then status="WARNING"; fi
    fi
    
    # Check memory usage
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [ $mem_usage -gt 95 ]; then
        issues+=("Memory usage critical: ${mem_usage}%")
        status="CRITICAL"
    elif [ $mem_usage -gt 85 ]; then
        issues+=("Memory usage high: ${mem_usage}%")
        if [ "$status" = "HEALTHY" ]; then status="WARNING"; fi
    fi
    
    echo "$status|${issues[*]}"
}

# Function to check trading activity
check_trading_activity() {
    local activity_status="NORMAL"
    local notes=()
    
    # Check for recent log activity
    if [ -f "logs/overmind.log" ]; then
        local recent_trades=$(tail -100 logs/overmind.log | grep -c "TRADE\|POSITION" 2>/dev/null || echo "0")
        notes+=("Recent trading activity: $recent_trades events")
        
        # Check for errors
        local recent_errors=$(tail -100 logs/overmind.log | grep -c "ERROR" 2>/dev/null || echo "0")
        if [ $recent_errors -gt 5 ]; then
            notes+=("High error rate: $recent_errors errors in last 100 lines")
            activity_status="WARNING"
        fi
    else
        notes+=("No trading log found")
        activity_status="WARNING"
    fi
    
    echo "$activity_status|${notes[*]}"
}

# Function to get performance metrics
get_performance_metrics() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local mem_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    echo "CPU:${cpu_usage}%|Load:${load_avg}|Memory:${mem_usage}%|Disk:${disk_usage}%"
}

# Function to update status JSON
update_status() {
    local current_time=$(date +%s)
    local elapsed_time=$((current_time - TRIAL_START_TIME))
    local remaining_time=$((TRIAL_DURATION - elapsed_time))
    local progress=$((elapsed_time * 100 / TRIAL_DURATION))
    
    local system_health=$(check_system_health)
    local health_status=$(echo $system_health | cut -d'|' -f1)
    local health_issues=$(echo $system_health | cut -d'|' -f2)
    
    local trading_activity=$(check_trading_activity)
    local activity_status=$(echo $trading_activity | cut -d'|' -f1)
    local activity_notes=$(echo $trading_activity | cut -d'|' -f2)
    
    local performance=$(get_performance_metrics)
    
    # Create status JSON
    cat > $STATUS_FILE << EOF
{
    "timestamp": "$(date -Iseconds)",
    "trial_start": "$(date -d @$TRIAL_START_TIME -Iseconds)",
    "elapsed_hours": $(echo "scale=1; $elapsed_time / 3600" | bc),
    "remaining_hours": $(echo "scale=1; $remaining_time / 3600" | bc),
    "progress_percent": $progress,
    "system_health": {
        "status": "$health_status",
        "issues": "$health_issues"
    },
    "trading_activity": {
        "status": "$activity_status",
        "notes": "$activity_notes"
    },
    "performance": {
        "metrics": "$performance"
    },
    "services": {
        "mission_control": "$(curl -s -f http://localhost:8501/health > /dev/null 2>&1 && echo 'UP' || echo 'DOWN')",
        "dragonfly": "$(echo 'PING' | nc -w 2 localhost 6379 | grep -q 'PONG' 2>/dev/null && echo 'UP' || echo 'DOWN')",
        "overmind_process": "$(pgrep -f 'overmind_hft_executor' > /dev/null && echo 'UP' || echo 'DOWN')"
    }
}
EOF
}

# Function to display status
display_status() {
    local current_time=$(date +%s)
    local elapsed_time=$((current_time - TRIAL_START_TIME))
    local remaining_time=$((TRIAL_DURATION - elapsed_time))
    local progress=$((elapsed_time * 100 / TRIAL_DURATION))
    
    local system_health=$(check_system_health)
    local health_status=$(echo $system_health | cut -d'|' -f1)
    local health_issues=$(echo $system_health | cut -d'|' -f2)
    
    local performance=$(get_performance_metrics)
    
    echo -e "\n${BLUE}🔥 FIRE TRIAL PROTOCOL STATUS${NC}"
    echo -e "${BLUE}================================${NC}"
    echo -e "Time: $(date)"
    echo -e "Progress: ${progress}% ($(echo "scale=1; $elapsed_time / 3600" | bc)h / 48h)"
    echo -e "Remaining: $(echo "scale=1; $remaining_time / 3600" | bc) hours"
    
    case $health_status in
        "HEALTHY")
            echo -e "System Health: ${GREEN}$health_status${NC}"
            ;;
        "WARNING")
            echo -e "System Health: ${YELLOW}$health_status${NC}"
            ;;
        "CRITICAL")
            echo -e "System Health: ${RED}$health_status${NC}"
            ;;
    esac
    
    if [ -n "$health_issues" ]; then
        echo -e "Issues: $health_issues"
    fi
    
    echo -e "Performance: $performance"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if trial is complete
is_trial_complete() {
    local current_time=$(date +%s)
    local elapsed_time=$((current_time - TRIAL_START_TIME))
    [ $elapsed_time -ge $TRIAL_DURATION ]
}

# Main monitoring loop
main_loop() {
    log_message "Starting Fire Trial monitoring loop"
    
    while ! is_trial_complete; do
        # Update status
        update_status
        
        # Check system health
        local system_health=$(check_system_health)
        local health_status=$(echo $system_health | cut -d'|' -f1)
        local health_issues=$(echo $system_health | cut -d'|' -f2)
        
        # Send alerts for critical issues
        if [ "$health_status" = "CRITICAL" ]; then
            send_alert "CRITICAL" "$health_issues"
        elif [ "$health_status" = "WARNING" ]; then
            send_alert "WARNING" "$health_issues"
        fi
        
        # Display status
        display_status
        
        # Log status
        log_message "Status: $health_status | Performance: $(get_performance_metrics)"
        
        # Wait for next check
        sleep $CHECK_INTERVAL
    done
    
    log_message "Fire Trial monitoring complete - 48 hours elapsed"
    echo -e "\n${GREEN}🎉 FIRE TRIAL PROTOCOL COMPLETE!${NC}"
    echo -e "Total duration: 48 hours"
    echo -e "Final status: $(check_system_health | cut -d'|' -f1)"
    echo -e "Check logs: $LOG_FILE"
    echo -e "Check alerts: $ALERT_FILE"
}

# Handle script termination
cleanup() {
    log_message "Fire Trial monitoring stopped by user"
    echo -e "\n${YELLOW}Fire Trial monitoring stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if running as daemon or interactive
if [ "$1" = "--daemon" ]; then
    log_message "Starting Fire Trial monitoring in daemon mode"
    main_loop > /dev/null 2>&1 &
    echo $! > fire-trial-monitor.pid
    echo "Fire Trial monitoring started in background (PID: $(cat fire-trial-monitor.pid))"
    echo "Monitor logs: tail -f $LOG_FILE"
    echo "Stop monitoring: kill \$(cat fire-trial-monitor.pid)"
else
    echo -e "${GREEN}🔥 THE OVERMIND PROTOCOL - Fire Trial Monitor${NC}"
    echo -e "${GREEN}=============================================${NC}"
    echo "Starting 48-hour monitoring..."
    echo "Press Ctrl+C to stop"
    echo ""
    main_loop
fi
