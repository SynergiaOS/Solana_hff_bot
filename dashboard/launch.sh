#!/bin/bash

# THE OVERMIND PROTOCOL - Dashboard Launcher
# Quick launcher script for the comprehensive monitoring dashboard

echo "🧠 THE OVERMIND PROTOCOL - Dashboard Launcher"
echo "=============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "comprehensive_overmind_dashboard.py" ]; then
    echo "❌ Please run this script from the dashboard directory."
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing/updating dependencies..."
    pip3 install -r requirements.txt
fi

# Set default environment variables if not set
export DASHBOARD_HOST=${DASHBOARD_HOST:-"0.0.0.0"}
export DASHBOARD_PORT=${DASHBOARD_PORT:-"8501"}
export REDIS_HOST=${REDIS_HOST:-"localhost"}
export REDIS_PORT=${REDIS_PORT:-"6379"}
export BRAIN_API_URL=${BRAIN_API_URL:-"http://localhost:8001"}
export EXECUTOR_API_URL=${EXECUTOR_API_URL:-"http://localhost:8080"}

echo "🚀 Starting THE OVERMIND PROTOCOL Dashboard..."
echo "📊 Dashboard will be available at: http://localhost:${DASHBOARD_PORT}"
echo "🔄 Use Ctrl+C to stop the dashboard"
echo ""

# Start the dashboard
python3 start_dashboard.py
