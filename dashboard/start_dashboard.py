#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Dashboard Startup Script
Launches the comprehensive monitoring dashboard
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'plotly',
        'pandas',
        'numpy',
        'redis',
        'httpx'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Install missing packages with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_system_components():
    """Check if OVERMIND system components are running"""
    components = {
        "Redis/DragonflyDB": ("localhost", 6379),
        "OVERMIND Brain": ("localhost", 8001),
        "Rust Executor": ("localhost", 8080)
    }
    
    import socket
    
    for component, (host, port) in components.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logger.info(f"✅ {component} is running on {host}:{port}")
            else:
                logger.warning(f"⚠️ {component} is not accessible on {host}:{port}")
        except Exception as e:
            logger.warning(f"⚠️ Could not check {component}: {e}")

def start_dashboard():
    """Start the comprehensive OVERMIND dashboard"""
    logger.info("🧠 Starting THE OVERMIND PROTOCOL Comprehensive Dashboard")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Missing dependencies. Please install required packages.")
        return False
    
    # Check system components
    check_system_components()
    
    # Get dashboard file path
    dashboard_file = Path(__file__).parent / "comprehensive_overmind_dashboard.py"
    
    if not dashboard_file.exists():
        logger.error(f"❌ Dashboard file not found: {dashboard_file}")
        return False
    
    # Start Streamlit dashboard
    try:
        logger.info("🚀 Launching dashboard...")
        logger.info("📊 Dashboard will be available at: http://localhost:8501")
        logger.info("🔄 Use Ctrl+C to stop the dashboard")
        
        # Run streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_file),
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        logger.info("🛑 Dashboard stopped by user")
    except Exception as e:
        logger.error(f"❌ Error starting dashboard: {e}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("""
    🧠 THE OVERMIND PROTOCOL
    ========================
    Comprehensive Monitoring Dashboard
    
    Features:
    - Real-time system monitoring
    - Strategy performance heat maps
    - Risk management dashboard
    - Correlation analysis
    - Performance analytics
    - Intelligence layer metrics
    
    """)
    
    start_dashboard()

if __name__ == "__main__":
    main()
