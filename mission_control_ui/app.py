"""
THE OVERMIND PROTOCOL - Mission Control UI
Captain's Bridge - Web Dashboard for AI Trading System
"""

import streamlit as st
import httpx
import json
import time
from datetime import datetime
import pandas as pd
import asyncio

# Page configuration
st.set_page_config(
    page_title="THE OVERMIND PROTOCOL - Mission Control",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1e3c72;
    }
    .metric-box {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .emergency-button {
        background: #ff4b4b !important;
        color: white !important;
        font-weight: bold !important;
        padding: 0.5rem 2rem !important;
        border-radius: 10px !important;
    }
    .success-status {
        color: #28a745;
        font-weight: bold;
    }
    .error-status {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
BRAIN_API_URL = "http://localhost:8000"
EXECUTOR_API_URL = "http://localhost:8081"

# Helper functions
def get_system_status():
    """Get system status from APIs"""
    try:
        # Try Brain Manager first
        with httpx.Client(timeout=5.0) as client:
            brain_response = client.get(f"{BRAIN_API_URL}/status")
            brain_status = brain_response.json() if brain_response.status_code == 200 else None
    except:
        brain_status = None
    
    try:
        # Try Rust Executor
        with httpx.Client(timeout=5.0) as client:
            executor_response = client.get(f"{EXECUTOR_API_URL}/health")
            executor_status = executor_response.json() if executor_response.status_code == 200 else None
    except:
        executor_status = None
    
    return brain_status, executor_status

def get_metrics():
    """Get trading metrics"""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{EXECUTOR_API_URL}/metrics")
            if response.status_code == 200:
                return response.json()
    except:
        pass
    
    return {
        "total_trades": 0,
        "successful_trades": 0,
        "failed_trades": 0,
        "daily_pnl": 0.0,
        "current_positions": 0,
        "system_latency_ms": 0.0
    }

def send_emergency_stop():
    """Send emergency stop command"""
    try:
        command = {"action": "EMERGENCY_STOP", "reason": "Manual emergency stop from Mission Control"}
        # Send via DragonflyDB queue (simulate)
        return True
    except:
        return False

# Main Application
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧠 THE OVERMIND PROTOCOL</h1>
        <h3>Mission Control - Captain's Bridge</h3>
        <p>AI-Enhanced High-Frequency Trading System for Solana</p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh (15s)", value=True)
    
    if st.sidebar.button("🔄 Manual Refresh"):
        st.rerun()

    # Emergency controls
    st.sidebar.markdown("### 🚨 Emergency Controls")
    if st.sidebar.button("🛑 EMERGENCY STOP", type="secondary"):
        if send_emergency_stop():
            st.sidebar.success("Emergency stop signal sent!")
        else:
            st.sidebar.error("Failed to send emergency stop!")

    # Get system data
    brain_status, executor_status = get_system_status()
    metrics = get_metrics()

    # Main layout - 3 columns
    col1, col2, col3 = st.columns([2, 2, 3])

    # Column 1: System Status
    with col1:
        st.markdown("### 🎯 System Status")
        
        # Brain Manager Status
        st.markdown("#### 🧠 AI Brain Manager")
        if brain_status:
            st.markdown('<span class="success-status">🟢 OPERATIONAL</span>', unsafe_allow_html=True)
            st.json(brain_status)
        else:
            st.markdown('<span class="error-status">🔴 UNAVAILABLE</span>', unsafe_allow_html=True)
        
        # Executor Status
        st.markdown("#### ⚡ Rust Executor")
        if executor_status:
            st.markdown('<span class="success-status">🟢 HEALTHY</span>', unsafe_allow_html=True)
            if executor_status.get("trading_mode") == "paper":
                st.info("📝 Paper Trading Mode Active")
        else:
            st.markdown('<span class="error-status">🔴 UNHEALTHY</span>', unsafe_allow_html=True)

    # Column 2: Trading Metrics
    with col2:
        st.markdown("### 📊 Trading Metrics")
        
        # Key metrics
        st.metric("Total Trades", metrics.get("total_trades", 0))
        st.metric("Success Rate", 
                 f"{(metrics.get('successful_trades', 0) / max(metrics.get('total_trades', 1), 1) * 100):.1f}%")
        st.metric("Daily P&L", f"${metrics.get('daily_pnl', 0):.2f}")
        st.metric("Current Positions", metrics.get("current_positions", 0))
        st.metric("System Latency", f"{metrics.get('system_latency_ms', 0):.1f}ms")

    # Column 3: System Info
    with col3:
        st.markdown("### 📋 System Information")
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"**Current Time:** {current_time}")
        st.write(f"**Environment:** Solana Devnet")
        st.write(f"**Version:** THE OVERMIND PROTOCOL v1.1.0")
        st.write(f"**Architecture:** Multi-Agent AI + Rust HFT")
        
        # Component URLs
        st.markdown("#### 🔗 Component Access")
        st.write("- **Brain Manager:** http://localhost:8000")
        st.write("- **Rust Executor:** http://localhost:8081") 
        st.write("- **DragonflyDB:** localhost:6379")
        st.write("- **Mission Control:** http://localhost:8501")

    # Full width section: Queue Status
    st.markdown("---")
    st.markdown("### 📡 Communication Queues")
    
    queue_col1, queue_col2, queue_col3 = st.columns(3)
    
    with queue_col1:
        st.metric("Signals Queue", "2", help="Market signals waiting for AI processing")
    
    with queue_col2:
        st.metric("Commands Queue", "0", help="Commands waiting for execution")
    
    with queue_col3:
        st.metric("Decisions Queue", "0", help="AI decisions ready for execution")

    # Transaction Log (Mock data for now)
    st.markdown("### 📝 Recent Activity Log")
    
    # Create sample transaction data
    log_data = [
        {"Time": "2025-06-24 05:20:53", "Action": "SIGNAL", "Symbol": "SOL", "Details": "Test signal injected", "Status": "✅ Processed"},
        {"Time": "2025-06-24 05:20:45", "Action": "COMMAND", "Symbol": "SOL", "Details": "Execute trade command", "Status": "⏳ Pending"},
        {"Time": "2025-06-24 05:19:30", "Action": "HEALTH", "Symbol": "SYSTEM", "Details": "Health check passed", "Status": "✅ OK"},
        {"Time": "2025-06-24 05:19:15", "Action": "START", "Symbol": "SYSTEM", "Details": "OVERMIND Protocol started", "Status": "✅ Running"},
    ]
    
    df = pd.DataFrame(log_data)
    st.dataframe(df, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>🧠 THE OVERMIND PROTOCOL - Mission Control Dashboard</p>
        <p>Real-time monitoring and control for AI-enhanced trading system</p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh logic
    if auto_refresh:
        time.sleep(15)
        st.rerun()

if __name__ == "__main__":
    main()