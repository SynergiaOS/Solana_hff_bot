#!/usr/bin/env python3
"""
THE OVERMIND PROTOCOL - Real-time Trading Dashboard
Advanced monitoring and visualization system
"""

import asyncio
import json
import time
import redis
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OvermindDashboard:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6380, decode_responses=True)
        
        # Dashboard configuration
        st.set_page_config(
            page_title="THE OVERMIND PROTOCOL",
            page_icon="🧠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #FF6B35;
            text-align: center;
            margin-bottom: 2rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem;
            border-radius: 10px;
            color: white;
            margin: 0.5rem 0;
        }
        .status-online {
            color: #00FF00;
            font-weight: bold;
        }
        .status-offline {
            color: #FF0000;
            font-weight: bold;
        }
        .status-warning {
            color: #FFA500;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            # Check main components
            status = {
                'rust_executor': self.check_process_status('snipercor'),
                'post_trade_intelligence': self.check_redis_activity('overmind:post_trade_intelligence'),
                'add_to_winner': self.check_redis_activity('overmind:scaling_events'),
                'drawdown_guard': self.check_redis_activity('overmind:drawdown_metrics'),
                'feedback_scorer': self.check_redis_activity('overmind:ai_feedback'),
                'last_update': time.time()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting system status: {e}")
            return {'error': str(e)}
    
    def check_process_status(self, process_name: str) -> str:
        """Check if a process is running"""
        try:
            # This would normally check actual processes
            # For demo, we'll check Redis activity
            return "ONLINE" if self.redis_client.ping() else "OFFLINE"
        except:
            return "OFFLINE"
    
    def check_redis_activity(self, key: str) -> str:
        """Check Redis key activity"""
        try:
            length = self.redis_client.llen(key)
            return "ACTIVE" if length > 0 else "IDLE"
        except:
            return "ERROR"
    
    def get_portfolio_metrics(self) -> Dict:
        """Get current portfolio metrics"""
        try:
            position_updates = self.redis_client.lrange('overmind:position_updates', 0, 0)
            if not position_updates:
                return {}
            
            latest_update = json.loads(position_updates[0])
            return latest_update.get('portfolio_metrics', {})
            
        except Exception as e:
            logger.error(f"❌ Error getting portfolio metrics: {e}")
            return {}
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trading activity"""
        try:
            results = self.redis_client.lrange('overmind:execution_results', 0, limit-1)
            trades = []
            
            for result_str in results:
                result = json.loads(result_str)
                trades.append({
                    'timestamp': result.get('timestamp', time.time()),
                    'symbol': result.get('symbol', 'N/A'),
                    'action': result.get('action', 'N/A'),
                    'quantity': result.get('quantity', 0),
                    'status': result.get('status', 'N/A'),
                    'pnl': result.get('estimated_profit', 0)
                })
            
            return trades
            
        except Exception as e:
            logger.error(f"❌ Error getting recent trades: {e}")
            return []
    
    def get_performance_history(self) -> pd.DataFrame:
        """Get performance history for charts"""
        try:
            # Get drawdown metrics for performance tracking
            metrics = self.redis_client.lrange('overmind:drawdown_metrics', 0, 99)
            
            data = []
            for metric_str in metrics:
                metric = json.loads(metric_str)
                data.append({
                    'timestamp': pd.to_datetime(metric['timestamp'], unit='s'),
                    'portfolio_value': metric.get('portfolio_value', 0),
                    'daily_pnl': metric.get('daily_pnl', 0),
                    'drawdown': metric.get('drawdown', 0) * 100,  # Convert to percentage
                    'risk_level': metric.get('risk_level', 'LOW')
                })
            
            return pd.DataFrame(data).sort_values('timestamp')
            
        except Exception as e:
            logger.error(f"❌ Error getting performance history: {e}")
            return pd.DataFrame()
    
    def render_header(self):
        """Render dashboard header"""
        st.markdown('<h1 class="main-header">🧠 THE OVERMIND PROTOCOL v2.3.0</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Advanced AI Trading System - Live Dashboard</p>', unsafe_allow_html=True)
    
    def render_system_status(self):
        """Render system status section"""
        st.header("🔥 System Status")

        status = self.get_system_status()

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            rust_status = status.get('rust_executor', 'UNKNOWN')
            status_class = 'status-online' if rust_status == 'ONLINE' else 'status-offline'
            st.markdown(f'<div class="metric-card">🚀 Rust Executor<br><span class="{status_class}">{rust_status}</span></div>', unsafe_allow_html=True)

        with col2:
            intel_status = status.get('post_trade_intelligence', 'UNKNOWN')
            status_class = 'status-online' if intel_status == 'ACTIVE' else 'status-warning'
            st.markdown(f'<div class="metric-card">🧠 Post-Trade Intel<br><span class="{status_class}">{intel_status}</span></div>', unsafe_allow_html=True)

        with col3:
            winner_status = status.get('add_to_winner', 'UNKNOWN')
            status_class = 'status-online' if winner_status == 'ACTIVE' else 'status-warning'
            st.markdown(f'<div class="metric-card">📈 Add to Winner<br><span class="{status_class}">{winner_status}</span></div>', unsafe_allow_html=True)

        with col4:
            guard_status = status.get('drawdown_guard', 'UNKNOWN')
            status_class = 'status-online' if guard_status == 'ACTIVE' else 'status-warning'
            st.markdown(f'<div class="metric-card">🛡️ Drawdown Guard<br><span class="{status_class}">{guard_status}</span></div>', unsafe_allow_html=True)

        with col5:
            feedback_status = status.get('feedback_scorer', 'UNKNOWN')
            status_class = 'status-online' if feedback_status == 'ACTIVE' else 'status-warning'
            st.markdown(f'<div class="metric-card">🧠 AI Feedback<br><span class="{status_class}">{feedback_status}</span></div>', unsafe_allow_html=True)
    
    def render_portfolio_overview(self):
        """Render portfolio overview section"""
        st.header("💰 Portfolio Overview")
        
        metrics = self.get_portfolio_metrics()
        
        if metrics:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_value = metrics.get('total_portfolio_value', 0)
                st.metric("Total Portfolio Value", f"${total_value:.6f}")
            
            with col2:
                daily_pnl = metrics.get('daily_pnl', 0)
                daily_pnl_pct = metrics.get('daily_pnl_percentage', 0)
                st.metric("Daily P&L", f"${daily_pnl:.6f}", f"{daily_pnl_pct:.2f}%")
            
            with col3:
                total_pnl = metrics.get('total_unrealized_pnl', 0)
                st.metric("Unrealized P&L", f"${total_pnl:.6f}")
            
            with col4:
                portfolio_return = metrics.get('portfolio_return_pct', 0)
                st.metric("Portfolio Return", f"{portfolio_return:.2f}%")
        else:
            st.warning("No portfolio data available")
    
    def render_performance_charts(self):
        """Render performance charts"""
        st.header("📈 Performance Analytics")
        
        df = self.get_performance_history()
        
        if not df.empty:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Portfolio Value', 'Daily P&L', 'Drawdown', 'Risk Level'),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Portfolio value chart
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['portfolio_value'], 
                          name='Portfolio Value', line=dict(color='#00FF00')),
                row=1, col=1
            )
            
            # Daily P&L chart
            colors = ['red' if x < 0 else 'green' for x in df['daily_pnl']]
            fig.add_trace(
                go.Bar(x=df['timestamp'], y=df['daily_pnl'], 
                       name='Daily P&L', marker_color=colors),
                row=1, col=2
            )
            
            # Drawdown chart
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['drawdown'], 
                          name='Drawdown %', line=dict(color='#FF6B35'), fill='tonexty'),
                row=2, col=1
            )
            
            # Risk level chart
            risk_mapping = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'EMERGENCY': 4}
            df['risk_numeric'] = df['risk_level'].map(risk_mapping)
            
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['risk_numeric'], 
                          name='Risk Level', line=dict(color='#FFA500')),
                row=2, col=2
            )
            
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available yet")
    
    def render_recent_activity(self):
        """Render recent trading activity"""
        st.header("🔄 Recent Trading Activity")
        
        trades = self.get_recent_trades()
        
        if trades:
            df_trades = pd.DataFrame(trades)
            df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'], unit='s')
            df_trades['time'] = df_trades['timestamp'].dt.strftime('%H:%M:%S')
            
            # Style the dataframe
            def style_pnl(val):
                color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
                return f'color: {color}'
            
            styled_df = df_trades[['time', 'symbol', 'action', 'quantity', 'status', 'pnl']].style.applymap(
                style_pnl, subset=['pnl']
            )
            
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("No recent trading activity")

    def render_advanced_features_metrics(self):
        """Render advanced features metrics section"""
        st.header("🚀 Advanced Features Metrics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("📈 Add to Winner")
            try:
                scaling_events = self.redis_client.lrange('overmind:scaling_events', 0, 4)
                if scaling_events:
                    st.success(f"✅ {len(scaling_events)} recent scaling events")
                    for event_str in scaling_events:
                        event = json.loads(event_str)
                        symbol = event.get('symbol', 'N/A')
                        scale_factor = event.get('scale_factor', 1.0)
                        st.text(f"📈 {symbol}: {scale_factor:.2f}x")
                else:
                    st.info("No scaling events yet")
            except:
                st.warning("Add to Winner data unavailable")

        with col2:
            st.subheader("🛡️ Drawdown Protection")
            try:
                drawdown_metrics = self.redis_client.lrange('overmind:drawdown_metrics', 0, 0)
                if drawdown_metrics:
                    metrics = json.loads(drawdown_metrics[0])
                    drawdown = metrics.get('drawdown', 0) * 100
                    risk_level = metrics.get('risk_level', 'UNKNOWN')

                    if risk_level == 'EMERGENCY':
                        st.error(f"🚨 EMERGENCY: {drawdown:.1f}% drawdown")
                    elif risk_level == 'HIGH':
                        st.warning(f"⚠️ HIGH RISK: {drawdown:.1f}% drawdown")
                    elif risk_level == 'MEDIUM':
                        st.warning(f"⚠️ MEDIUM: {drawdown:.1f}% drawdown")
                    else:
                        st.success(f"✅ LOW RISK: {drawdown:.1f}% drawdown")
                else:
                    st.info("No drawdown data yet")
            except:
                st.warning("Drawdown data unavailable")

        with col3:
            st.subheader("🧠 AI Feedback")
            try:
                feedback_data = self.redis_client.lrange('overmind:ai_feedback', 0, 4)
                if feedback_data:
                    total_score = 0
                    count = 0
                    for feedback_str in feedback_data:
                        feedback = json.loads(feedback_str)
                        score = feedback.get('outcome_score', 0)
                        total_score += score
                        count += 1

                    avg_score = total_score / count if count > 0 else 0

                    if avg_score > 0.8:
                        st.success(f"🎯 Excellent: {avg_score:.2f}")
                    elif avg_score > 0.6:
                        st.success(f"✅ Good: {avg_score:.2f}")
                    elif avg_score > 0.4:
                        st.warning(f"⚠️ Fair: {avg_score:.2f}")
                    else:
                        st.error(f"❌ Poor: {avg_score:.2f}")

                    st.text(f"📊 {count} recent decisions analyzed")
                else:
                    st.info("No feedback data yet")
            except:
                st.warning("Feedback data unavailable")

    def render_control_panel(self):
        """Render advanced mission control panel"""
        st.sidebar.header("🎮 MISSION CONTROL")

        # System status overview
        st.sidebar.subheader("🔥 System Status")
        emergency_stop = self.redis_client.get('overmind:emergency_stop')
        if emergency_stop == 'true':
            st.sidebar.error("🚨 EMERGENCY STOP ACTIVE")
        else:
            st.sidebar.success("✅ SYSTEM OPERATIONAL")

        # Critical controls
        st.sidebar.subheader("🚨 Critical Controls")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🛑 EMERGENCY STOP", type="primary"):
                self.redis_client.set('overmind:emergency_stop', 'true')
                st.sidebar.error("Emergency stop activated!")

        with col2:
            if st.button("▶️ RESUME"):
                self.redis_client.delete('overmind:emergency_stop')
                st.sidebar.success("Trading resumed!")

        # Advanced feature controls
        st.sidebar.subheader("🚀 Feature Controls")

        if st.sidebar.button("📈 Force Add to Winner"):
            command = {'action': 'start', 'feature': 'add_to_winner', 'timestamp': time.time()}
            self.redis_client.lpush('overmind:orchestrator_commands', json.dumps(command))
            st.sidebar.success("Add to Winner activated!")

        if st.sidebar.button("🛡️ Test Drawdown Protection"):
            command = {'action': 'test_drawdown', 'timestamp': time.time()}
            self.redis_client.lpush('overmind:orchestrator_commands', json.dumps(command))
            st.sidebar.success("Drawdown protection tested!")

        if st.sidebar.button("🧠 Trigger AI Analysis"):
            command = {'action': 'analyze', 'timestamp': time.time()}
            self.redis_client.lpush('overmind:analytics_commands', json.dumps(command))
            st.sidebar.success("AI analysis triggered!")

        # Real-time alerts
        st.sidebar.subheader("🚨 Active Alerts")
        alerts = self.redis_client.lrange('overmind:alerts', 0, 4)

        if alerts:
            for alert_str in alerts:
                alert = json.loads(alert_str)
                if not alert.get('acknowledged', False):
                    level = alert.get('level', 'INFO')
                    title = alert.get('title', 'Unknown')

                    if level == 'EMERGENCY':
                        st.sidebar.error(f"🆘 {title}")
                    elif level == 'CRITICAL':
                        st.sidebar.error(f"🚨 {title}")
                    elif level == 'WARNING':
                        st.sidebar.warning(f"⚠️ {title}")
                    else:
                        st.sidebar.info(f"ℹ️ {title}")
        else:
            st.sidebar.success("✅ No active alerts")

        # Settings
        st.sidebar.subheader("⚙️ Settings")
        auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=True)
        show_debug = st.sidebar.checkbox("Debug Mode", value=False)

        if show_debug:
            st.sidebar.subheader("🔧 Debug Info")
            redis_info = self.redis_client.info()
            st.sidebar.text(f"Redis: {redis_info.get('connected_clients', 0)} clients")
            st.sidebar.text(f"Memory: {redis_info.get('used_memory_human', 'N/A')}")

        if auto_refresh:
            time.sleep(30)
            st.rerun()
    
    def run_dashboard(self):
        """Main dashboard rendering"""
        self.render_header()
        self.render_control_panel()
        self.render_system_status()
        self.render_portfolio_overview()
        self.render_advanced_features_metrics()
        self.render_performance_charts()
        self.render_recent_activity()
        
        # Footer
        st.markdown("---")
        st.markdown(f"<p style='text-align: center; color: #666;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)

def main():
    dashboard = OvermindDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
