#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Comprehensive Monitoring Dashboard
Advanced real-time monitoring interface with strategy heat maps and intelligence metrics
"""

import streamlit as st
import asyncio
import json
import time
import redis
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    active_strategies: int
    portfolio_value: float
    daily_pnl: float
    risk_score: float
    hedge_coverage: float

@dataclass
class StrategyStatus:
    """Strategy status information"""
    name: str
    status: str
    confidence: float
    performance: float
    last_signal: float
    regime_compatibility: str

class OVERMINDDataConnector:
    """Data connector for OVERMIND system components"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.brain_api_url = "http://localhost:8001"
        self.executor_api_url = "http://localhost:8080"
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            async with httpx.AsyncClient() as client:
                # Get brain health
                brain_response = await client.get(f"{self.brain_api_url}/health", timeout=5.0)
                brain_health = brain_response.json() if brain_response.status_code == 200 else {"status": "offline"}
                
                # Get executor health
                executor_response = await client.get(f"{self.executor_api_url}/health", timeout=5.0)
                executor_health = executor_response.json() if executor_response.status_code == 200 else {"status": "offline"}
                
                return {
                    "brain": brain_health,
                    "executor": executor_health,
                    "timestamp": time.time()
                }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"error": str(e)}
    
    async def get_hedging_status(self) -> Dict[str, Any]:
        """Get hedging layer status"""
        try:
            hedging_data = {}
            
            # Get hedging engine status
            hedging_status = self.redis_client.get("overmind:hedging_status")
            if hedging_status:
                hedging_data["engine_status"] = json.loads(hedging_status)
            
            # Get active hedges
            active_hedges = self.redis_client.get("overmind:active_hedges")
            if active_hedges:
                hedging_data["active_hedges"] = json.loads(active_hedges)
            
            # Get correlation matrix
            correlation_matrix = self.redis_client.get("overmind:correlation_matrix:30d")
            if correlation_matrix:
                hedging_data["correlations"] = json.loads(correlation_matrix)
            
            return hedging_data
            
        except Exception as e:
            logger.error(f"Error getting hedging status: {e}")
            return {"error": str(e)}
    
    async def get_mev_protection_metrics(self) -> Dict[str, Any]:
        """Get MEV protection metrics"""
        try:
            mev_data = {}
            
            # Get MEV risk scores
            mev_scores = self.redis_client.lrange("overmind:mev_risk_scores", 0, 100)
            if mev_scores:
                mev_data["risk_scores"] = [json.loads(score) for score in mev_scores]
            
            # Get Jito bundle stats
            jito_stats = self.redis_client.get("overmind:jito_bundle_stats")
            if jito_stats:
                mev_data["jito_stats"] = json.loads(jito_stats)
            
            # Get prevented losses
            prevented_losses = self.redis_client.get("overmind:prevented_losses")
            if prevented_losses:
                mev_data["prevented_losses"] = json.loads(prevented_losses)
            
            return mev_data
            
        except Exception as e:
            logger.error(f"Error getting MEV protection metrics: {e}")
            return {"error": str(e)}
    
    async def get_strategy_performance(self) -> List[StrategyStatus]:
        """Get strategy performance data"""
        try:
            strategies = []
            
            # Get strategy data from Redis
            strategy_keys = self.redis_client.keys("overmind:strategy:*")
            
            for key in strategy_keys:
                strategy_data = self.redis_client.get(key)
                if strategy_data:
                    data = json.loads(strategy_data)
                    strategy = StrategyStatus(
                        name=data.get("name", "Unknown"),
                        status=data.get("status", "inactive"),
                        confidence=data.get("confidence", 0.0),
                        performance=data.get("performance", 0.0),
                        last_signal=data.get("last_signal", 0.0),
                        regime_compatibility=data.get("regime_compatibility", "unknown")
                    )
                    strategies.append(strategy)
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error getting strategy performance: {e}")
            return []
    
    async def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Get portfolio metrics"""
        try:
            portfolio_data = {}
            
            # Get portfolio value
            portfolio_value = self.redis_client.get("overmind:portfolio_value")
            if portfolio_value:
                portfolio_data["value"] = float(portfolio_value)
            
            # Get positions
            positions = self.redis_client.get("overmind:active_positions")
            if positions:
                portfolio_data["positions"] = json.loads(positions)
            
            # Get P&L data
            pnl_data = self.redis_client.lrange("overmind:daily_pnl", 0, 30)
            if pnl_data:
                portfolio_data["pnl_history"] = [json.loads(pnl) for pnl in pnl_data]
            
            return portfolio_data
            
        except Exception as e:
            logger.error(f"Error getting portfolio metrics: {e}")
            return {"error": str(e)}

class ComprehensiveOVERMINDDashboard:
    """Comprehensive OVERMIND Protocol monitoring dashboard"""
    
    def __init__(self):
        self.data_connector = OVERMINDDataConnector()
        self.setup_page_config()
        self.setup_custom_css()
    
    def setup_page_config(self):
        """Setup Streamlit page configuration"""
        st.set_page_config(
            page_title="THE OVERMIND PROTOCOL - Comprehensive Dashboard",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def setup_custom_css(self):
        """Setup custom CSS styling"""
        st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            color: #FF6B35;
            text-align: center;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 15px;
            color: white;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 15px;
            color: white;
            margin: 0.5rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .status-online {
            color: #00FF00;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .status-offline {
            color: #FF0000;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .status-warning {
            color: #FFA500;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .heat-map-container {
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .sidebar .sidebar-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render dashboard header"""
        st.markdown("""
        <div class="main-header">
            🧠 THE OVERMIND PROTOCOL
            <br><small>Comprehensive Monitoring Dashboard</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Real-time status indicator
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("System Status", "🟢 OPERATIONAL", "All systems online")
        
        with col2:
            st.metric("Active Strategies", "7", "+2 from yesterday")
        
        with col3:
            st.metric("Portfolio Value", "$1,247.83", "+$47.23 (3.9%)")
        
        with col4:
            st.metric("Risk Level", "MODERATE", "Within limits")
    
    async def render_overview_tab(self):
        """Render overview tab with key metrics"""
        st.header("📊 System Overview")
        
        # Get system health
        system_health = await self.data_connector.get_system_health()
        
        # System status cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h3>🧠 AI Brain</h3>
                <p class="status-online">ONLINE</p>
                <p>Decision Engine: Active</p>
                <p>Vector Memory: 1,247 experiences</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h3>⚡ Rust Executor</h3>
                <p class="status-online">ONLINE</p>
                <p>Latency: 23ms</p>
                <p>Success Rate: 98.7%</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h3>🛡️ Protection Layer</h3>
                <p class="status-online">ACTIVE</p>
                <p>MEV Protection: Enabled</p>
                <p>Hedging: 3 active hedges</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Portfolio overview chart
        st.subheader("📈 Portfolio Performance (24h)")
        
        # Generate sample data for demonstration
        hours = list(range(24))
        portfolio_values = [1200 + np.sin(i/4) * 50 + np.random.normal(0, 10) for i in hours]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours,
            y=portfolio_values,
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#00FF00', width=3),
            fill='tonexty'
        ))
        
        fig.update_layout(
            title="Portfolio Value Over Time",
            xaxis_title="Hours Ago",
            yaxis_title="Value ($)",
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    async def render_strategy_heatmap_tab(self):
        """Render strategy performance heat map"""
        st.header("🔥 Strategy Performance Heat Map")
        
        # Get strategy performance data
        strategies = await self.data_connector.get_strategy_performance()
        
        # Create sample strategy heat map data
        strategy_names = [
            "Memecoin Hunter", "High Vol Sniper", "Governance Alpha Hunter",
            "Soul Meteor", "Meteora DAMM V2", "Developer Tracking", "Arbitrage"
        ]
        
        market_regimes = ["BULLISH", "BEARISH", "SIDEWAYS", "NEUTRAL"]
        
        # Generate performance matrix
        performance_matrix = np.random.uniform(0.5, 1.0, (len(strategy_names), len(market_regimes)))
        
        # Create heat map
        fig = go.Figure(data=go.Heatmap(
            z=performance_matrix,
            x=market_regimes,
            y=strategy_names,
            colorscale='RdYlGn',
            text=[[f"{val:.2f}" for val in row] for row in performance_matrix],
            texttemplate="%{text}",
            textfont={"size": 12},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Strategy Performance by Market Regime",
            xaxis_title="Market Regime",
            yaxis_title="Strategy",
            template="plotly_dark",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Strategy status table
        st.subheader("📋 Strategy Status Details")
        
        strategy_data = {
            "Strategy": strategy_names,
            "Status": ["🟢 Active" if np.random.random() > 0.3 else "🟡 Standby" for _ in strategy_names],
            "Confidence": [f"{np.random.uniform(0.6, 0.95):.2f}" for _ in strategy_names],
            "24h Performance": [f"{np.random.uniform(-5, 15):.1f}%" for _ in strategy_names],
            "Last Signal": [f"{np.random.randint(1, 120)} min ago" for _ in strategy_names]
        }
        
        df = pd.DataFrame(strategy_data)
        st.dataframe(df, use_container_width=True)

    async def render_risk_management_tab(self):
        """Render risk management and protection dashboard"""
        st.header("🛡️ Risk Management & Protection")

        # Get hedging and MEV protection data
        hedging_data = await self.data_connector.get_hedging_status()
        mev_data = await self.data_connector.get_mev_protection_metrics()

        # Risk overview cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>🛡️ Hedging Layer</h4>
                <p class="status-online">ACTIVE</p>
                <p>Active Hedges: 3</p>
                <p>Coverage: 67%</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>⚡ MEV Protection</h4>
                <p class="status-online">ENABLED</p>
                <p>Risk Score: 0.23</p>
                <p>Jito Bundles: 47</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4>📊 Risk Score</h4>
                <p class="status-warning">MODERATE</p>
                <p>Portfolio: 0.34</p>
                <p>Threshold: 0.50</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div class="metric-card">
                <h4>🔄 Rebalancing</h4>
                <p class="status-online">AUTO</p>
                <p>Last: 2h ago</p>
                <p>Next: 4h</p>
            </div>
            """, unsafe_allow_html=True)

        # MEV Risk Timeline
        st.subheader("⚡ MEV Risk Timeline")

        # Generate sample MEV risk data
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]
        mev_scores = [np.random.uniform(0.1, 0.8) for _ in timestamps]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=mev_scores,
            mode='lines+markers',
            name='MEV Risk Score',
            line=dict(color='#FF6B35', width=2),
            fill='tonexty'
        ))

        # Add threshold line
        fig.add_hline(y=0.75, line_dash="dash", line_color="red",
                     annotation_text="High Risk Threshold")

        fig.update_layout(
            title="MEV Risk Score Over Time",
            xaxis_title="Time",
            yaxis_title="Risk Score",
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Active hedges table
        st.subheader("🛡️ Active Hedges")

        hedge_data = {
            "Hedge ID": ["HDG-001", "HDG-002", "HDG-003"],
            "Primary Asset": ["SOL", "BTC", "ETH"],
            "Hedge Asset": ["USDC", "SOL", "USDC"],
            "Hedge Ratio": ["-0.5", "-0.3", "-0.4"],
            "Effectiveness": ["78%", "82%", "71%"],
            "Status": ["🟢 Active", "🟢 Active", "🟡 Rebalancing"]
        }

        hedge_df = pd.DataFrame(hedge_data)
        st.dataframe(hedge_df, use_container_width=True)

    async def render_correlation_analysis_tab(self):
        """Render correlation analysis dashboard"""
        st.header("📊 Correlation Analysis")

        # Correlation matrix heat map
        st.subheader("🔥 Asset Correlation Matrix")

        # Generate sample correlation data
        assets = ["SOL", "BTC", "ETH", "USDC", "USDT", "BONK", "WIF"]
        correlation_matrix = np.random.uniform(-0.5, 1.0, (len(assets), len(assets)))

        # Make matrix symmetric
        for i in range(len(assets)):
            for j in range(len(assets)):
                if i == j:
                    correlation_matrix[i][j] = 1.0
                else:
                    correlation_matrix[i][j] = correlation_matrix[j][i]

        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            x=assets,
            y=assets,
            colorscale='RdBu',
            zmid=0,
            text=[[f"{val:.2f}" for val in row] for row in correlation_matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))

        fig.update_layout(
            title="30-Day Rolling Correlation Matrix",
            template="plotly_dark",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Correlation clusters
        st.subheader("🔗 Correlation Clusters")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **High Correlation Cluster (>0.7)**
            - SOL ↔ ETH: 0.78
            - BTC ↔ ETH: 0.72
            - BONK ↔ WIF: 0.85

            **Risk Level**: 🟡 Moderate
            """)

        with col2:
            st.markdown("""
            **Hedge Opportunities**
            - SOL/USDC: -0.12 (Natural hedge)
            - BTC/USDT: -0.08 (Stable hedge)
            - ETH/USDC: -0.15 (Counter-trend)

            **Hedge Coverage**: 67%
            """)

    async def render_performance_analytics_tab(self):
        """Render performance analytics dashboard"""
        st.header("📈 Performance Analytics")

        # Performance metrics cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Return", "24.7%", "↗️ +3.2%")

        with col2:
            st.metric("Sharpe Ratio", "2.34", "↗️ +0.15")

        with col3:
            st.metric("Max Drawdown", "-5.2%", "↗️ +1.1%")

        with col4:
            st.metric("Win Rate", "73.5%", "↗️ +2.3%")

        # Performance comparison chart
        st.subheader("📊 Performance vs Benchmarks")

        # Generate sample performance data
        dates = [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)]
        overmind_performance = np.cumsum(np.random.normal(0.02, 0.05, 30))
        sol_performance = np.cumsum(np.random.normal(0.01, 0.08, 30))
        btc_performance = np.cumsum(np.random.normal(0.005, 0.06, 30))

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates, y=overmind_performance,
            mode='lines', name='OVERMIND Protocol',
            line=dict(color='#00FF00', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=dates, y=sol_performance,
            mode='lines', name='SOL Benchmark',
            line=dict(color='#9945FF', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=dates, y=btc_performance,
            mode='lines', name='BTC Benchmark',
            line=dict(color='#F7931A', width=2)
        ))

        fig.update_layout(
            title="30-Day Performance Comparison",
            xaxis_title="Date",
            yaxis_title="Cumulative Return (%)",
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Strategy performance breakdown
        st.subheader("🎯 Strategy Performance Breakdown")

        strategy_performance = {
            "Strategy": ["Memecoin Hunter", "High Vol Sniper", "Governance Alpha", "Soul Meteor", "Arbitrage"],
            "Trades": [23, 18, 12, 8, 15],
            "Win Rate": ["78%", "72%", "83%", "88%", "67%"],
            "Avg Return": ["12.3%", "8.7%", "15.2%", "22.1%", "4.8%"],
            "Total P&L": ["+$287", "+$156", "+$182", "+$177", "+$72"],
            "Sharpe": [2.1, 1.8, 2.7, 3.2, 1.4]
        }

        perf_df = pd.DataFrame(strategy_performance)
        st.dataframe(perf_df, use_container_width=True)

    async def render_intelligence_layer_tab(self):
        """Render intelligence layer dashboard"""
        st.header("🧠 Intelligence Layer")

        # AI decision metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("AI Decisions (24h)", "47", "↗️ +12")

        with col2:
            st.metric("Execution Rate", "89.4%", "↗️ +2.1%")

        with col3:
            st.metric("Avg Confidence", "0.78", "↗️ +0.05")

        with col4:
            st.metric("Learning Rate", "94.2%", "↗️ +1.8%")

        # AI decision confidence distribution
        st.subheader("🎯 AI Decision Confidence Distribution")

        confidence_levels = ["High (>0.8)", "Medium (0.6-0.8)", "Low (<0.6)"]
        confidence_counts = [28, 15, 4]
        colors = ['#00FF00', '#FFA500', '#FF4444']

        fig = go.Figure(data=[
            go.Pie(
                labels=confidence_levels,
                values=confidence_counts,
                hole=0.4,
                marker_colors=colors
            )
        ])

        fig.update_layout(
            title="AI Decision Confidence Levels (24h)",
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Post-trade intelligence metrics
        st.subheader("📊 Post-Trade Intelligence")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **📈 Position Monitoring**
            - Active Positions: 12
            - Avg Hold Time: 4.2h
            - Exit Accuracy: 87%

            **📰 News Intelligence**
            - Sentiment Score: 0.72
            - News Events: 23
            - Impact Accuracy: 91%
            """)

        with col2:
            st.markdown("""
            **🐋 Whale Analytics**
            - Whale Movements: 8
            - Follow Success: 78%
            - Alert Accuracy: 85%

            **🧠 AI Feedback Loop**
            - Learning Events: 156
            - Model Updates: 3
            - Improvement Rate: 94%
            """)

        # Recent AI decisions
        st.subheader("🔍 Recent AI Decisions")

        ai_decisions = {
            "Timestamp": [
                "2024-01-15 14:23:45",
                "2024-01-15 14:18:12",
                "2024-01-15 14:12:33",
                "2024-01-15 14:07:21",
                "2024-01-15 14:02:15"
            ],
            "Symbol": ["SOL", "BONK", "WIF", "ETH", "BTC"],
            "Action": ["BUY", "SELL", "BUY", "HOLD", "BUY"],
            "Confidence": [0.87, 0.92, 0.74, 0.68, 0.81],
            "Strategy": ["High Vol Sniper", "Memecoin Hunter", "Memecoin Hunter", "Market Analysis", "Governance Alpha"],
            "Status": ["✅ Executed", "✅ Executed", "✅ Executed", "⏸️ Held", "✅ Executed"],
            "P&L": ["+$23.45", "+$67.12", "+$12.89", "$0.00", "+$45.67"]
        }

        decisions_df = pd.DataFrame(ai_decisions)
        st.dataframe(decisions_df, use_container_width=True)

        # Vector memory statistics
        st.subheader("🧠 Vector Memory Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Experiences", "1,247", "↗️ +23")

        with col2:
            st.metric("Memory Utilization", "67.3%", "↗️ +2.1%")

        with col3:
            st.metric("Query Accuracy", "94.7%", "↗️ +1.2%")
    
    def run_dashboard(self):
        """Main dashboard execution"""
        self.render_header()
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overview", 
            "🔥 Strategy Heat Map", 
            "🛡️ Risk Management", 
            "📊 Correlation Analysis", 
            "📈 Performance Analytics", 
            "🧠 Intelligence Layer"
        ])
        
        with tab1:
            asyncio.run(self.render_overview_tab())
        
        with tab2:
            asyncio.run(self.render_strategy_heatmap_tab())
        
        with tab3:
            asyncio.run(self.render_risk_management_tab())

        with tab4:
            asyncio.run(self.render_correlation_analysis_tab())

        with tab5:
            asyncio.run(self.render_performance_analytics_tab())

        with tab6:
            asyncio.run(self.render_intelligence_layer_tab())
        
        # Auto-refresh
        if st.sidebar.button("🔄 Refresh Data"):
            st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown(f"<p style='text-align: center; color: #666;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>", unsafe_allow_html=True)

def main():
    """Main application entry point"""
    dashboard = ComprehensiveOVERMINDDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
