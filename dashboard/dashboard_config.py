#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Dashboard Configuration
Configuration settings for the comprehensive monitoring dashboard
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import os

@dataclass
class DashboardConfig:
    """Dashboard configuration settings"""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8501
    
    # Redis/DragonflyDB settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # API endpoints
    brain_api_url: str = "http://localhost:8001"
    executor_api_url: str = "http://localhost:8080"
    
    # Refresh settings
    auto_refresh_interval: int = 30  # seconds
    data_cache_ttl: int = 60  # seconds
    
    # Display settings
    max_chart_points: int = 100
    default_timeframe: str = "24h"
    
    # Alert thresholds
    high_risk_threshold: float = 0.75
    low_performance_threshold: float = -0.05
    high_correlation_threshold: float = 0.7
    
    # Strategy settings
    strategy_names: List[str] = None
    market_regimes: List[str] = None
    
    def __post_init__(self):
        """Initialize default values"""
        if self.strategy_names is None:
            self.strategy_names = [
                "Memecoin Hunter",
                "High Vol Sniper", 
                "Governance Alpha Hunter",
                "Soul Meteor",
                "Meteora DAMM V2",
                "Developer Tracking",
                "Arbitrage"
            ]
        
        if self.market_regimes is None:
            self.market_regimes = ["BULLISH", "BEARISH", "SIDEWAYS", "NEUTRAL"]

@dataclass
class VisualizationConfig:
    """Visualization configuration settings"""
    
    # Color schemes
    primary_color: str = "#FF6B35"
    success_color: str = "#00FF00"
    warning_color: str = "#FFA500"
    danger_color: str = "#FF0000"
    
    # Chart settings
    chart_template: str = "plotly_dark"
    chart_height: int = 400
    heatmap_height: int = 500
    
    # Heat map colors
    correlation_colorscale: str = "RdBu"
    performance_colorscale: str = "RdYlGn"
    risk_colorscale: str = "Reds"

@dataclass
class MonitoringConfig:
    """Monitoring configuration settings"""
    
    # System health checks
    health_check_interval: int = 60  # seconds
    component_timeout: int = 5  # seconds
    
    # Performance monitoring
    performance_window: int = 24  # hours
    max_drawdown_alert: float = 0.1  # 10%
    
    # Risk monitoring
    risk_check_interval: int = 300  # 5 minutes
    max_portfolio_risk: float = 0.5  # 50%
    
    # MEV protection monitoring
    mev_risk_threshold: float = 0.75
    jito_bundle_timeout: int = 30  # seconds

def load_config_from_env() -> DashboardConfig:
    """Load configuration from environment variables"""
    config = DashboardConfig()
    
    # Override with environment variables if present
    config.host = os.getenv("DASHBOARD_HOST", config.host)
    config.port = int(os.getenv("DASHBOARD_PORT", config.port))
    config.redis_host = os.getenv("REDIS_HOST", config.redis_host)
    config.redis_port = int(os.getenv("REDIS_PORT", config.redis_port))
    config.brain_api_url = os.getenv("BRAIN_API_URL", config.brain_api_url)
    config.executor_api_url = os.getenv("EXECUTOR_API_URL", config.executor_api_url)
    
    return config

def get_dashboard_config() -> DashboardConfig:
    """Get dashboard configuration"""
    return load_config_from_env()

def get_visualization_config() -> VisualizationConfig:
    """Get visualization configuration"""
    return VisualizationConfig()

def get_monitoring_config() -> MonitoringConfig:
    """Get monitoring configuration"""
    return MonitoringConfig()

# Global configuration instances
DASHBOARD_CONFIG = get_dashboard_config()
VISUALIZATION_CONFIG = get_visualization_config()
MONITORING_CONFIG = get_monitoring_config()

# Dashboard themes
THEMES = {
    "dark": {
        "background_color": "#0E1117",
        "secondary_background": "#262730",
        "text_color": "#FAFAFA",
        "primary_color": "#FF6B35"
    },
    "light": {
        "background_color": "#FFFFFF",
        "secondary_background": "#F0F2F6",
        "text_color": "#262730",
        "primary_color": "#FF6B35"
    }
}

# Metric definitions
METRICS_CONFIG = {
    "portfolio": {
        "value": {"unit": "$", "precision": 2},
        "pnl": {"unit": "$", "precision": 2},
        "return": {"unit": "%", "precision": 1},
        "risk": {"unit": "", "precision": 3}
    },
    "strategy": {
        "confidence": {"unit": "", "precision": 2},
        "performance": {"unit": "%", "precision": 1},
        "win_rate": {"unit": "%", "precision": 1}
    },
    "system": {
        "latency": {"unit": "ms", "precision": 0},
        "cpu": {"unit": "%", "precision": 1},
        "memory": {"unit": "%", "precision": 1}
    }
}

# Dashboard layout configuration
LAYOUT_CONFIG = {
    "sidebar_width": 300,
    "main_content_padding": 20,
    "chart_margin": {"l": 20, "r": 20, "t": 40, "b": 20},
    "metric_card_height": 120,
    "table_page_size": 20
}

# Data refresh intervals (in seconds)
REFRESH_INTERVALS = {
    "real_time": 5,
    "fast": 15,
    "normal": 30,
    "slow": 60,
    "very_slow": 300
}

# Alert configurations
ALERT_CONFIG = {
    "risk_levels": {
        "low": {"threshold": 0.3, "color": "#00FF00"},
        "moderate": {"threshold": 0.6, "color": "#FFA500"},
        "high": {"threshold": 0.8, "color": "#FF4444"},
        "critical": {"threshold": 1.0, "color": "#8B0000"}
    },
    "performance_levels": {
        "excellent": {"threshold": 0.1, "color": "#00FF00"},
        "good": {"threshold": 0.05, "color": "#90EE90"},
        "neutral": {"threshold": -0.02, "color": "#FFA500"},
        "poor": {"threshold": -0.1, "color": "#FF4444"}
    }
}

# Export all configurations
__all__ = [
    "DashboardConfig",
    "VisualizationConfig", 
    "MonitoringConfig",
    "DASHBOARD_CONFIG",
    "VISUALIZATION_CONFIG",
    "MONITORING_CONFIG",
    "THEMES",
    "METRICS_CONFIG",
    "LAYOUT_CONFIG",
    "REFRESH_INTERVALS",
    "ALERT_CONFIG"
]
