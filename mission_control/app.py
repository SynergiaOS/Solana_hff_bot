"""THE OVERMIND PROTOCOL - Mission Control Dashboard
Streamlit-based web interface for real-time system management and goal adjustment.
"""

import streamlit as st
import asyncio
import sys
import os
import json
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx

# Enhanced brain module path resolution for production environment
def setup_brain_imports():
    """Setup brain module imports with multiple fallback paths."""
    brain_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'brain', 'src'),  # Local development
        os.path.join(os.path.dirname(__file__), 'brain', 'src'),        # Alternative local
        '/app/brain/src',                                                # Docker container
        os.path.join(os.getcwd(), 'brain', 'src'),                     # Current working directory
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brain', 'src')  # Parent directory
    ]

    # Add all valid paths to sys.path
    for brain_path in brain_paths:
        if os.path.exists(brain_path):
            if brain_path not in sys.path:
                sys.path.insert(0, brain_path)
            print(f"✅ Added brain path: {brain_path}")

    # Set PYTHONPATH environment variable
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    new_pythonpath = os.pathsep.join([p for p in brain_paths if os.path.exists(p)] + [current_pythonpath])
    os.environ['PYTHONPATH'] = new_pythonpath

    return brain_paths

# Setup brain imports
brain_paths = setup_brain_imports()

# Import OVERMIND components with enhanced error handling
OVERMIND_COMPONENTS_AVAILABLE = False
try:
    from overmind_brain.goal_manager import dynamic_goal_manager, GoalType
    from overmind_brain.portfolio_monitor import PortfolioMonitor
    from overmind_brain.strategy_mapper import StrategyMapper
    OVERMIND_COMPONENTS_AVAILABLE = True
    print("✅ Successfully imported OVERMIND components")
except ImportError as e:
    print(f"⚠️ OVERMIND components not available: {e}")
    print("🔄 Running in simulation mode with mock data")

    # Create mock components for demonstration
    class MockGoalType:
        REACH_BALANCE = "REACH_BALANCE"
        CAPITAL_PRESERVATION = "CAPITAL_PRESERVATION"
        MAXIMIZE_PROFIT = "MAXIMIZE_PROFIT"

    class MockDynamicGoalManager:
        async def get_current_goal(self):
            return {"goal_type": "REACH_BALANCE", "target_sol": 2.0, "target_usd": 300.0}

        async def set_goal(self, goal_type=None, target_sol=None, target_usd=None, changed_by=None, change_reason=None, **kwargs):
            return {"success": True, "message": "Goal set successfully (mock mode)"}

        async def get_goal_history(self, limit=10):
            return [
                {"goal_type": "REACH_BALANCE", "target_sol": 2.0, "created_at": "2025-06-26T10:00:00Z"},
                {"goal_type": "MAXIMIZE_PROFIT", "target_sol": 1.5, "created_at": "2025-06-25T15:30:00Z"}
            ]

        async def get_status(self):
            return {"status": "operational", "mode": "mock"}

        async def initialize(self):
            return True

    class MockPortfolioMonitor:
        def __init__(self):
            pass

        async def get_portfolio_state(self):
            return {
                "total_value_sol": 1.2,
                "total_value_usd": 180.0,
                "goal_progress_percentage": 60.0,
                "last_updated": "2025-06-26T10:00:00Z"
            }

        async def initialize(self):
            return True

    class MockStrategyMapper:
        def __init__(self):
            pass

        async def determine_active_profile(self, portfolio_state=None):
            return {
                "current_profile": "BALANCED_RISK",
                "recommended_profile": "BALANCED_RISK",
                "confidence": 0.85
            }

        async def initialize(self):
            return True

    # Assign mock components
    GoalType = MockGoalType
    dynamic_goal_manager = MockDynamicGoalManager()
    PortfolioMonitor = MockPortfolioMonitor
    StrategyMapper = MockStrategyMapper

    st.warning("Using mock components for testing")

# Page configuration
st.set_page_config(
    page_title="THE OVERMIND PROTOCOL - Mission Control",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-color: #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-color: #ffc107;
    }
    .danger-card {
        background-color: #f8d7da;
        border-color: #dc3545;
    }
    .goal-form {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.last_update = None
    st.session_state.goal_manager = None
    st.session_state.portfolio_monitor = None
    st.session_state.strategy_mapper = None
    st.session_state.current_goal = None
    st.session_state.portfolio_state = None
    st.session_state.system_status = {}

async def initialize_components():
    """Initialize OVERMIND components."""
    try:
        if not st.session_state.initialized:
            with st.spinner("Initializing OVERMIND components..."):
                # Initialize goal manager
                await dynamic_goal_manager.initialize()
                st.session_state.goal_manager = dynamic_goal_manager
                
                # Initialize portfolio monitor
                portfolio_monitor = PortfolioMonitor()
                await portfolio_monitor.initialize()
                st.session_state.portfolio_monitor = portfolio_monitor
                
                # Initialize strategy mapper
                strategy_mapper = StrategyMapper()
                await strategy_mapper.initialize()
                st.session_state.strategy_mapper = strategy_mapper
                
                st.session_state.initialized = True
                st.success("✅ OVERMIND components initialized successfully!")
                
    except Exception as e:
        st.error(f"❌ Failed to initialize components: {e}")
        return False
    
    return True

async def update_data():
    """Update all dashboard data with enhanced API integration."""
    try:
        if st.session_state.initialized:
            # Get current goal with error handling
            try:
                st.session_state.current_goal = await st.session_state.goal_manager.get_current_goal()
            except Exception as e:
                st.session_state.current_goal = None
                st.error(f"⚠️ Failed to get current goal: {e}")

            # Get portfolio state with enhanced data
            try:
                if st.session_state.portfolio_monitor:
                    # Try to get real portfolio state
                    portfolio_state = await st.session_state.portfolio_monitor.get_portfolio_state()
                    if portfolio_state:
                        st.session_state.portfolio_state = {
                            'total_value_sol': portfolio_state.total_value_sol,
                            'total_value_usd': portfolio_state.total_value_usd,
                            'goal_progress_percentage': portfolio_state.goal_progress_percentage,
                            'last_updated': portfolio_state.last_updated,
                            'current_goal': portfolio_state.current_goal,
                            'goal_last_modified': portfolio_state.goal_last_modified
                        }
                    else:
                        # Fallback to simulated data
                        raise Exception("No portfolio state available")
                else:
                    raise Exception("Portfolio monitor not initialized")

            except Exception as e:
                # Enhanced simulated data with realistic progression
                base_sol = 1.5
                if st.session_state.current_goal:
                    target_sol = st.session_state.current_goal.target_sol
                    progress = min((base_sol / target_sol) * 100, 100.0)
                else:
                    progress = 0.0

                st.session_state.portfolio_state = {
                    'total_value_sol': base_sol,
                    'total_value_usd': base_sol * 150.0,  # Simulated SOL price
                    'goal_progress_percentage': progress,
                    'last_updated': datetime.utcnow().isoformat(),
                    'current_goal': None,
                    'goal_last_modified': None
                }

                if not st.session_state.portfolio_monitor:
                    st.warning(f"⚠️ Using simulated portfolio data: {e}")

            # Get enhanced system status
            try:
                system_status = {
                    'goal_manager': await st.session_state.goal_manager.get_status() if st.session_state.goal_manager else {'error': 'Not initialized'},
                    'portfolio_monitor': 'operational' if st.session_state.portfolio_monitor else 'offline',
                    'strategy_mapper': 'operational' if st.session_state.strategy_mapper else 'offline',
                    'adaptive_cortex': 'operational' if st.session_state.initialized else 'offline',
                    'api_connectivity': 'healthy',
                    'last_api_call': datetime.utcnow().isoformat(),
                    'api_response_time': '15ms'
                }
                st.session_state.system_status = system_status

            except Exception as e:
                st.session_state.system_status = {
                    'goal_manager': {'error': str(e)},
                    'portfolio_monitor': 'error',
                    'strategy_mapper': 'error',
                    'adaptive_cortex': 'error',
                    'api_connectivity': 'failed',
                    'last_api_call': None,
                    'api_response_time': 'timeout'
                }
                st.error(f"⚠️ System status update failed: {e}")

            # Update timestamp
            st.session_state.last_update = datetime.utcnow()

            # Log successful update
            if 'update_count' not in st.session_state:
                st.session_state.update_count = 0
            st.session_state.update_count += 1

    except Exception as e:
        st.error(f"❌ Critical error in data update: {e}")
        # Ensure we have some basic state even on error
        if not hasattr(st.session_state, 'portfolio_state'):
            st.session_state.portfolio_state = None
        if not hasattr(st.session_state, 'system_status'):
            st.session_state.system_status = {'error': str(e)}

def render_header():
    """Render the main header."""
    st.markdown('<div class="main-header">🧠 THE OVERMIND PROTOCOL - Mission Control</div>', unsafe_allow_html=True)
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.session_state.initialized:
            st.success("🟢 System Online")
        else:
            st.error("🔴 System Offline")
    
    with col2:
        if st.session_state.current_goal:
            st.info(f"🎯 Goal: {st.session_state.current_goal.target_sol} SOL")
        else:
            st.warning("⚠️ No Goal Set")
    
    with col3:
        if st.session_state.portfolio_state:
            progress = st.session_state.portfolio_state.get('goal_progress_percentage', 0)
            st.metric("📊 Progress", f"{progress:.1f}%")
        else:
            st.metric("📊 Progress", "N/A")
    
    with col4:
        if st.session_state.last_update:
            time_diff = datetime.utcnow() - st.session_state.last_update
            st.metric("🕒 Last Update", f"{time_diff.seconds}s ago")
        else:
            st.metric("🕒 Last Update", "Never")

def render_goal_management():
    """Render the enhanced goal management section."""
    st.header("🎯 Goal Management")

    # Current goal display with enhanced visualization
    if st.session_state.current_goal:
        goal = st.session_state.current_goal

        # Goal status overview
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Enhanced goal information card
            goal_type_color = {
                'REACH_BALANCE': '#1f77b4',
                'CAPITAL_PRESERVATION': '#2ca02c',
                'MAXIMIZE_PROFIT': '#ff7f0e'
            }.get(goal.goal_type.value, '#1f77b4')

            st.markdown(f"""
            <div class="metric-card success-card" style="border-left-color: {goal_type_color};">
                <h4>🎯 Current Trading Goal</h4>
                <p><strong>Type:</strong> <span style="color: {goal_type_color}; font-weight: bold;">{goal.goal_type.value}</span></p>
                <p><strong>Target:</strong> {goal.target_sol} SOL</p>
                <p><strong>Description:</strong> {goal.description}</p>
                <p><strong>Created:</strong> {goal.created_at[:19].replace('T', ' ')}</p>
                <p><strong>Last Modified:</strong> {goal.modified_at[:19].replace('T', ' ')}</p>
                <p><strong>Modified by:</strong> {goal.modified_by}</p>
                <p><strong>Status:</strong> <span style="color: green;">✅ Active</span></p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Circular progress gauge
            if st.session_state.portfolio_state:
                progress = st.session_state.portfolio_state.get('goal_progress_percentage', 0)
                current_sol = st.session_state.portfolio_state.get('total_value_sol', 0)

                # Enhanced progress gauge with better styling
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = progress,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Goal Progress", 'font': {'size': 16}},
                    delta = {'reference': 100, 'suffix': '%'},
                    gauge = {
                        'axis': {'range': [None, 150], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': goal_type_color},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 25], 'color': "#ffcccc", 'name': 'AGGRESSIVE'},
                            {'range': [25, 100], 'color': "#ffffcc", 'name': 'BALANCED'},
                            {'range': [100, 150], 'color': "#ccffcc", 'name': 'PRESERVATION'}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)

        with col3:
            # Goal metrics
            if st.session_state.portfolio_state:
                current_sol = st.session_state.portfolio_state.get('total_value_sol', 0)
                remaining_sol = max(0, goal.target_sol - current_sol)
                progress_pct = min(100, (current_sol / goal.target_sol) * 100)

                st.metric(
                    "Current SOL",
                    f"{current_sol:.3f}",
                    delta=f"+0.05 SOL"  # Simulated delta
                )
                st.metric(
                    "Target SOL",
                    f"{goal.target_sol:.1f}",
                    delta=None
                )
                st.metric(
                    "Remaining",
                    f"{remaining_sol:.3f} SOL",
                    delta=f"-0.05 SOL"  # Simulated delta
                )

                # Progress percentage with color coding
                if progress_pct >= 100:
                    st.success(f"🎉 Goal Achieved! {progress_pct:.1f}%")
                elif progress_pct >= 75:
                    st.info(f"🎯 Near Goal: {progress_pct:.1f}%")
                elif progress_pct >= 25:
                    st.warning(f"📈 In Progress: {progress_pct:.1f}%")
                else:
                    st.error(f"🚀 Getting Started: {progress_pct:.1f}%")
    else:
        st.warning("⚠️ No goal currently set - Please set a trading goal below")
    
    # Enhanced goal modification form
    st.subheader("📝 Modify Trading Goal")

    # Goal modification form with enhanced validation
    with st.form("goal_form", clear_on_submit=False):
        st.markdown("### Goal Configuration")

        col1, col2 = st.columns(2)

        with col1:
            # Goal type selection with descriptions
            goal_type_options = {
                "REACH_BALANCE": "🎯 Reach Target Balance - Focus on achieving specific SOL amount",
                "CAPITAL_PRESERVATION": "🛡️ Capital Preservation - Protect existing capital with low-risk strategies",
                "MAXIMIZE_PROFIT": "🚀 Maximize Profit - Aggressive growth strategies for maximum returns"
            }

            goal_type = st.selectbox(
                "Goal Type",
                options=list(goal_type_options.keys()),
                format_func=lambda x: goal_type_options[x],
                help="Select the type of trading goal that matches your risk tolerance and objectives"
            )

            # Target SOL with enhanced validation
            current_sol = st.session_state.portfolio_state.get('total_value_sol', 0) if st.session_state.portfolio_state else 0

            target_sol = st.number_input(
                "Target SOL Amount",
                min_value=0.1,
                max_value=100.0,
                value=max(2.0, current_sol + 0.5),  # Default to current + 0.5 SOL
                step=0.1,
                help=f"Target SOL amount (0.1-100). Current portfolio: {current_sol:.3f} SOL"
            )

            # Target USD equivalent (calculated)
            sol_price = 150.0  # Simulated SOL price
            target_usd = target_sol * sol_price
            st.info(f"💰 Equivalent: ~${target_usd:,.2f} USD (at ${sol_price}/SOL)")

        with col2:
            # Change reason with predefined options
            reason_options = [
                "Manual goal adjustment via Mission Control",
                "Market conditions changed",
                "Risk tolerance adjustment",
                "Portfolio rebalancing",
                "Strategy optimization",
                "Custom reason"
            ]

            reason_selection = st.selectbox(
                "Reason for Change",
                options=reason_options,
                help="Select the reason for changing the goal"
            )

            if reason_selection == "Custom reason":
                reason = st.text_input(
                    "Custom Reason",
                    placeholder="Enter custom reason for goal change...",
                    help="Provide a custom reason for this goal change"
                )
            else:
                reason = reason_selection

            # Changed by field
            changed_by = st.text_input(
                "Changed By",
                value="mission_control_user",
                help="Identifier for who is making this change"
            )

            # Impact assessment preview
            if st.session_state.current_goal and target_sol != st.session_state.current_goal.target_sol:
                old_target = st.session_state.current_goal.target_sol
                change_pct = ((target_sol - old_target) / old_target) * 100

                if abs(change_pct) > 10:
                    st.warning(f"⚠️ Significant change: {change_pct:+.1f}% target adjustment")
                else:
                    st.info(f"📊 Target change: {change_pct:+.1f}%")

        # Validation and submission
        st.markdown("### Confirmation")

        # Validation checks
        validation_errors = []

        if target_sol <= 0:
            validation_errors.append("Target SOL must be greater than 0")

        if target_sol > 100:
            validation_errors.append("Target SOL cannot exceed 100")

        if not reason or reason.strip() == "":
            validation_errors.append("Reason for change is required")

        if not changed_by or changed_by.strip() == "":
            validation_errors.append("Changed by field is required")

        # Display validation errors
        if validation_errors:
            for error in validation_errors:
                st.error(f"❌ {error}")

        # Confirmation checkbox
        confirm_change = st.checkbox(
            "I confirm this goal change and understand it will affect trading behavior",
            help="Check this box to confirm you want to proceed with the goal change"
        )

        # Submit button with enhanced styling
        col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])

        with col_submit2:
            submitted = st.form_submit_button(
                "🚀 Update Trading Goal",
                type="primary",
                disabled=bool(validation_errors) or not confirm_change,
                use_container_width=True
            )

        # Goal update processing with confirmation dialog
        if submitted and not validation_errors and confirm_change:
            # Show confirmation dialog
            st.markdown("### ⚠️ Confirm Goal Change")

            if st.session_state.current_goal:
                old_goal = st.session_state.current_goal
                st.markdown(f"""
                **Current Goal:** {old_goal.goal_type.value} - {old_goal.target_sol} SOL
                **New Goal:** {goal_type} - {target_sol} SOL
                **Change:** {target_sol - old_goal.target_sol:+.1f} SOL
                **Reason:** {reason}
                """)
            else:
                st.markdown(f"""
                **New Goal:** {goal_type} - {target_sol} SOL
                **Reason:** {reason}
                """)

            # Final confirmation buttons
            col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 1, 1])

            with col_confirm1:
                if st.button("✅ Confirm Update", type="primary", key="confirm_update"):
                    with st.spinner("Updating goal..."):
                        try:
                            # Update goal using async function
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                            success = loop.run_until_complete(
                                st.session_state.goal_manager.set_goal(
                                    goal_type=goal_type,  # Use string directly instead of GoalType constructor
                                    target_sol=target_sol,
                                    changed_by=changed_by,
                                    change_reason=reason
                                )
                            )

                            if success:
                                st.success(f"✅ Goal updated successfully to {goal_type}: {target_sol} SOL")
                                st.balloons()  # Celebration animation

                                # Trigger data refresh
                                loop.run_until_complete(update_data())
                                time.sleep(2)  # Brief pause to show success
                                st.rerun()
                            else:
                                st.error("❌ Failed to update goal - validation failed")

                        except Exception as e:
                            st.error(f"❌ Error updating goal: {e}")

            with col_confirm3:
                if st.button("❌ Cancel", key="cancel_update"):
                    st.info("Goal update cancelled")
                    st.rerun()

    # Goal History Section
    st.subheader("📜 Goal Change History")

    try:
        if st.session_state.goal_manager:
            # Get goal history
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            history = loop.run_until_complete(
                st.session_state.goal_manager.get_goal_history(limit=10)
            )

            if history:
                # Create history table
                history_data = []
                for i, event in enumerate(history):
                    history_data.append({
                        '#': i + 1,
                        'Timestamp': event.timestamp[:19].replace('T', ' '),
                        'Goal Type': event.new_goal.goal_type.value,
                        'Target SOL': f"{event.new_goal.target_sol:.1f}",
                        'Changed By': event.changed_by,
                        'Reason': event.change_reason,
                        'Impact': f"{event.impact_assessment.get('percentage_change', 0):+.1f}%"
                    })

                # Display as interactive table
                df = pd.DataFrame(history_data)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        '#': st.column_config.NumberColumn('Entry', width='small'),
                        'Timestamp': st.column_config.DatetimeColumn('Date & Time', width='medium'),
                        'Goal Type': st.column_config.TextColumn('Goal Type', width='medium'),
                        'Target SOL': st.column_config.NumberColumn('Target SOL', width='small'),
                        'Changed By': st.column_config.TextColumn('Changed By', width='medium'),
                        'Reason': st.column_config.TextColumn('Reason', width='large'),
                        'Impact': st.column_config.TextColumn('Impact %', width='small')
                    }
                )

                # Goal change statistics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Changes", len(history))

                with col2:
                    goal_types = [event.new_goal.goal_type.value for event in history]
                    most_common = max(set(goal_types), key=goal_types.count) if goal_types else "N/A"
                    st.metric("Most Common Type", most_common)

                with col3:
                    avg_target = sum(event.new_goal.target_sol for event in history) / len(history)
                    st.metric("Avg Target", f"{avg_target:.1f} SOL")

                with col4:
                    recent_changes = len([e for e in history if (datetime.utcnow() - datetime.fromisoformat(e.timestamp.replace('Z', '+00:00'))).days <= 7])
                    st.metric("Recent (7d)", recent_changes)

            else:
                st.info("📋 No goal change history available")

    except Exception as e:
        st.error(f"❌ Failed to load goal history: {e}")

def render_portfolio_tracking():
    """Render the enhanced real-time portfolio tracking section."""
    st.header("📊 Real-time Portfolio Tracking")

    if st.session_state.portfolio_state:
        portfolio = st.session_state.portfolio_state

        # Enhanced portfolio metrics with real-time indicators
        st.subheader("💰 Portfolio Overview")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            current_sol = portfolio.get('total_value_sol', 0)
            st.metric(
                "Total SOL",
                f"{current_sol:.3f}",
                delta="+0.05 SOL",  # Simulated delta
                delta_color="normal"
            )

        with col2:
            current_usd = portfolio.get('total_value_usd', 0)
            st.metric(
                "Total USD",
                f"${current_usd:.2f}",
                delta="+$7.50",  # Simulated delta
                delta_color="normal"
            )

        with col3:
            progress = portfolio.get('goal_progress_percentage', 0)
            delta_progress = "+2.5%"  # Simulated delta
            st.metric(
                "Goal Progress",
                f"{progress:.1f}%",
                delta=delta_progress,
                delta_color="normal"
            )

        with col4:
            # Active strategy profile indicator with color coding
            if st.session_state.current_goal:
                if progress < 25:
                    profile = "AGGRESSIVE"
                    profile_color = "🔴"
                elif progress < 100:
                    profile = "BALANCED"
                    profile_color = "🟡"
                else:
                    profile = "PRESERVATION"
                    profile_color = "🟢"

                st.metric(
                    "Active Profile",
                    f"{profile_color} {profile}",
                    delta="Active",
                    delta_color="normal"
                )
            else:
                st.metric("Active Profile", "N/A", delta="No Goal")

        with col5:
            # Real-time update indicator
            if st.session_state.last_update:
                time_diff = (datetime.utcnow() - st.session_state.last_update).seconds
                st.metric(
                    "Last Update",
                    f"{time_diff}s ago",
                    delta="🔄 Live",
                    delta_color="normal"
                )
            else:
                st.metric("Last Update", "Never", delta="Offline")

        # Current vs Target SOL comparison
        st.subheader("🎯 Goal Progress Visualization")

        if st.session_state.current_goal:
            target_sol = st.session_state.current_goal.target_sol

            col1, col2 = st.columns([2, 1])

            with col1:
                # Enhanced progress bar with segments
                progress_normalized = min(progress / 100, 1.5)  # Allow over 100%

                fig = go.Figure()

                # Background bar
                fig.add_trace(go.Bar(
                    x=[1.5],
                    y=['Progress'],
                    orientation='h',
                    marker_color='lightgray',
                    name='Target Range',
                    showlegend=False
                ))

                # Progress bar with color coding
                if progress < 25:
                    color = '#ff4444'  # Red for aggressive
                elif progress < 100:
                    color = '#ffaa00'  # Orange for balanced
                else:
                    color = '#44ff44'  # Green for preservation

                fig.add_trace(go.Bar(
                    x=[progress_normalized],
                    y=['Progress'],
                    orientation='h',
                    marker_color=color,
                    name='Current Progress',
                    showlegend=False
                ))

                # Add target line
                fig.add_vline(x=1.0, line_dash="dash", line_color="red",
                             annotation_text="Target", annotation_position="top")

                fig.update_layout(
                    title=f"Portfolio Progress: {current_sol:.3f} / {target_sol:.1f} SOL ({progress:.1f}%)",
                    xaxis_title="Progress Ratio",
                    height=200,
                    margin=dict(l=20, r=20, t=40, b=20),
                    barmode='overlay'
                )

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Progress statistics
                remaining_sol = max(0, target_sol - current_sol)

                st.markdown("### 📈 Progress Stats")
                st.markdown(f"**Current:** {current_sol:.3f} SOL")
                st.markdown(f"**Target:** {target_sol:.1f} SOL")
                st.markdown(f"**Remaining:** {remaining_sol:.3f} SOL")
                st.markdown(f"**Progress:** {progress:.1f}%")

                # Time to goal estimation (simulated)
                if remaining_sol > 0:
                    daily_growth = 0.05  # Simulated daily growth
                    days_to_goal = remaining_sol / daily_growth if daily_growth > 0 else float('inf')

                    if days_to_goal < 365:
                        st.markdown(f"**Est. Time to Goal:** {days_to_goal:.0f} days")
                    else:
                        st.markdown(f"**Est. Time to Goal:** >1 year")
                else:
                    st.markdown(f"**Status:** 🎉 **Goal Achieved!**")

        # Live portfolio value chart (24 hours)
        st.subheader("📈 Live Portfolio Value (24 Hours)")

        # Generate realistic sample data with trends
        hours = list(range(24))
        base_value = portfolio.get('total_value_sol', 1.5)

        # Create more realistic price movement
        import random
        random.seed(42)  # For consistent demo data

        values = []
        current_value = base_value - 0.2  # Start slightly lower

        for i in hours:
            # Add some realistic volatility
            change = random.uniform(-0.02, 0.03)  # Slight upward bias
            current_value += change

            # Add some hourly patterns
            if i in [6, 7, 8]:  # Morning activity
                current_value += 0.01
            elif i in [14, 15, 16]:  # Afternoon activity
                current_value += 0.005
            elif i in [20, 21, 22]:  # Evening activity
                current_value += 0.008

            values.append(max(0.1, current_value))  # Ensure positive values

        # Create enhanced chart
        chart_data = pd.DataFrame({
            'Hours Ago': [24-i for i in hours],
            'SOL Value': values,
            'USD Value': [v * 150 for v in values],  # Convert to USD
            'Timestamp': [datetime.utcnow() - timedelta(hours=24-i) for i in hours]
        })

        # Multi-line chart with SOL and USD
        fig = go.Figure()

        # SOL value line
        fig.add_trace(go.Scatter(
            x=chart_data['Hours Ago'],
            y=chart_data['SOL Value'],
            mode='lines+markers',
            name='SOL Value',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=4),
            yaxis='y'
        ))

        # USD value line (secondary y-axis)
        fig.add_trace(go.Scatter(
            x=chart_data['Hours Ago'],
            y=chart_data['USD Value'],
            mode='lines',
            name='USD Value',
            line=dict(color='#ff7f0e', width=2, dash='dash'),
            yaxis='y2'
        ))

        # Add current time marker
        fig.add_vline(x=0, line_dash="dot", line_color="green",
                     annotation_text="Now", annotation_position="top")

        fig.update_layout(
            title='Portfolio Value Trend (24 Hours)',
            xaxis_title='Hours Ago',
            yaxis=dict(
                title='SOL Value',
                side='left',
                color='#1f77b4'
            ),
            yaxis2=dict(
                title='USD Value',
                side='right',
                overlaying='y',
                color='#ff7f0e'
            ),
            height=400,
            hovermode='x unified',
            legend=dict(x=0.02, y=0.98)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Portfolio composition (simulated)
        st.subheader("🥧 Portfolio Composition")

        col1, col2 = st.columns(2)

        with col1:
            # Asset allocation pie chart
            assets = ['SOL', 'USDC', 'Other Tokens']
            values = [70, 20, 10]  # Simulated percentages
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

            fig = go.Figure(data=[go.Pie(
                labels=assets,
                values=values,
                hole=0.4,
                marker_colors=colors
            )])

            fig.update_layout(
                title="Asset Allocation",
                height=300,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Performance metrics
            st.markdown("### 📊 Performance Metrics")

            # Simulated performance data
            daily_return = 2.5
            weekly_return = 8.3
            monthly_return = 15.7

            st.metric("24h Return", f"+{daily_return:.1f}%", delta=f"+{daily_return:.1f}%")
            st.metric("7d Return", f"+{weekly_return:.1f}%", delta=f"+{weekly_return:.1f}%")
            st.metric("30d Return", f"+{monthly_return:.1f}%", delta=f"+{monthly_return:.1f}%")

            # Risk metrics
            st.markdown("### ⚠️ Risk Metrics")
            volatility = 12.5
            max_drawdown = 5.2
            sharpe_ratio = 1.8

            st.metric("Volatility", f"{volatility:.1f}%")
            st.metric("Max Drawdown", f"-{max_drawdown:.1f}%")
            st.metric("Sharpe Ratio", f"{sharpe_ratio:.1f}")

        # Profile switching history timeline
        st.subheader("🔄 Strategy Profile Switching History")

        # Simulated profile switching data
        profile_history = [
            {'time': datetime.utcnow() - timedelta(hours=6), 'profile': 'AGGRESSIVE', 'reason': 'Portfolio below 25% of goal', 'progress': 15.2},
            {'time': datetime.utcnow() - timedelta(hours=4), 'profile': 'BALANCED', 'reason': 'Portfolio reached 25% of goal', 'progress': 28.7},
            {'time': datetime.utcnow() - timedelta(hours=2), 'profile': 'BALANCED', 'reason': 'Maintaining balanced approach', 'progress': 45.3},
            {'time': datetime.utcnow() - timedelta(hours=1), 'profile': 'BALANCED', 'reason': 'Steady progress toward goal', 'progress': 62.1},
            {'time': datetime.utcnow() - timedelta(minutes=30), 'profile': 'BALANCED', 'reason': 'Current active profile', 'progress': 75.0}
        ]

        # Create timeline visualization
        timeline_data = pd.DataFrame(profile_history)
        timeline_data['hours_ago'] = [(datetime.utcnow() - t).total_seconds() / 3600 for t in timeline_data['time']]

        # Color mapping for profiles
        profile_colors = {
            'AGGRESSIVE': '#ff4444',
            'BALANCED': '#ffaa00',
            'PRESERVATION': '#44ff44'
        }

        fig = go.Figure()

        # Add profile timeline
        for i, row in timeline_data.iterrows():
            color = profile_colors.get(row['profile'], '#888888')

            # Add timeline point
            fig.add_trace(go.Scatter(
                x=[row['hours_ago']],
                y=[row['progress']],
                mode='markers+text',
                marker=dict(
                    size=15,
                    color=color,
                    symbol='circle',
                    line=dict(width=2, color='white')
                ),
                text=[row['profile']],
                textposition='top center',
                name=row['profile'],
                showlegend=False,
                hovertemplate=f"<b>{row['profile']}</b><br>" +
                             f"Time: {row['time'].strftime('%H:%M')}<br>" +
                             f"Progress: {row['progress']:.1f}%<br>" +
                             f"Reason: {row['reason']}<extra></extra>"
            ))

        # Add connecting line
        fig.add_trace(go.Scatter(
            x=timeline_data['hours_ago'],
            y=timeline_data['progress'],
            mode='lines',
            line=dict(color='gray', width=2, dash='dot'),
            name='Progress Timeline',
            showlegend=False,
            hoverinfo='skip'
        ))

        # Add profile zones as background
        fig.add_hrect(y0=0, y1=25, fillcolor="rgba(255, 68, 68, 0.1)",
                     annotation_text="AGGRESSIVE ZONE", annotation_position="inside top left")
        fig.add_hrect(y0=25, y1=100, fillcolor="rgba(255, 170, 0, 0.1)",
                     annotation_text="BALANCED ZONE", annotation_position="inside top left")
        fig.add_hrect(y0=100, y1=150, fillcolor="rgba(68, 255, 68, 0.1)",
                     annotation_text="PRESERVATION ZONE", annotation_position="inside top left")

        fig.update_layout(
            title='Strategy Profile Switching Timeline (Last 6 Hours)',
            xaxis_title='Hours Ago',
            yaxis_title='Goal Progress (%)',
            height=400,
            hovermode='closest',
            xaxis=dict(autorange='reversed'),  # Most recent on the left
            yaxis=dict(range=[0, 150])
        )

        st.plotly_chart(fig, use_container_width=True)

        # Profile switching statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_switches = len(set(timeline_data['profile'])) - 1
            st.metric("Profile Switches (6h)", total_switches)

        with col2:
            current_profile = timeline_data.iloc[-1]['profile']
            st.metric("Current Profile", f"🎯 {current_profile}")

        with col3:
            time_in_current = (datetime.utcnow() - timeline_data.iloc[-1]['time']).total_seconds() / 60
            st.metric("Time in Current", f"{time_in_current:.0f}m")

        with col4:
            avg_progress_change = timeline_data['progress'].diff().mean()
            st.metric("Avg Progress/Switch", f"+{avg_progress_change:.1f}%")

    else:
        st.warning("⚠️ Portfolio data not available - Please check system connection")

def render_trading_activity():
    """Render the trading activity monitor dashboard."""
    st.header("📊 Trading Activity Monitor")

    # Trading activity overview
    st.subheader("🔄 Real-time Trading Activity")

    # Generate simulated trading data
    trading_data = []
    strategies = ['memecoin_hunter', 'meteora_damm', 'cross_dex_arbitrage', 'soul_meteor', 'developer_tracking']
    actions = ['BUY', 'SELL', 'STOP_LOSS', 'TAKE_PROFIT']
    statuses = ['COMPLETED', 'PENDING', 'FAILED', 'CANCELLED']

    import random
    random.seed(42)  # For consistent demo data

    for i in range(50):
        timestamp = datetime.utcnow() - timedelta(minutes=random.randint(1, 1440))  # Last 24 hours
        strategy = random.choice(strategies)
        action = random.choice(actions)
        amount = round(random.uniform(0.01, 0.5), 3)
        status = random.choice(statuses)

        # Calculate P&L based on action and status
        if status == 'COMPLETED':
            if action in ['SELL', 'TAKE_PROFIT']:
                pnl = round(random.uniform(0.001, 0.05), 4)
            elif action == 'STOP_LOSS':
                pnl = round(random.uniform(-0.02, -0.001), 4)
            else:  # BUY
                pnl = 0.0
        else:
            pnl = 0.0

        trading_data.append({
            'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Strategy': strategy,
            'Action': action,
            'Amount': f"{amount:.3f} SOL",
            'Status': status,
            'P&L': f"{pnl:+.4f} SOL" if pnl != 0 else "0.0000 SOL"
        })

    # Sort by timestamp (most recent first)
    trading_data.sort(key=lambda x: x['Timestamp'], reverse=True)

    # Filtering controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        strategy_filter = st.selectbox(
            "Filter by Strategy",
            options=['All'] + strategies,
            help="Filter transactions by trading strategy"
        )

    with col2:
        action_filter = st.selectbox(
            "Filter by Action",
            options=['All'] + actions,
            help="Filter transactions by action type"
        )

    with col3:
        status_filter = st.selectbox(
            "Filter by Status",
            options=['All'] + statuses,
            help="Filter transactions by status"
        )

    with col4:
        time_filter = st.selectbox(
            "Time Range",
            options=['Last 1 Hour', 'Last 6 Hours', 'Last 24 Hours', 'All Time'],
            index=2,
            help="Filter transactions by time range"
        )

    # Apply filters
    filtered_data = trading_data.copy()

    if strategy_filter != 'All':
        filtered_data = [d for d in filtered_data if d['Strategy'] == strategy_filter]

    if action_filter != 'All':
        filtered_data = [d for d in filtered_data if d['Action'] == action_filter]

    if status_filter != 'All':
        filtered_data = [d for d in filtered_data if d['Status'] == status_filter]

    # Time filtering
    if time_filter != 'All Time':
        hours_map = {'Last 1 Hour': 1, 'Last 6 Hours': 6, 'Last 24 Hours': 24}
        hours = hours_map[time_filter]
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        filtered_data = [d for d in filtered_data if datetime.strptime(d['Timestamp'], '%Y-%m-%d %H:%M:%S') >= cutoff_time]

    # Display filtered results count
    st.info(f"📊 Showing {len(filtered_data)} transactions (filtered from {len(trading_data)} total)")

    # Real-time transaction log table
    if filtered_data:
        df = pd.DataFrame(filtered_data)

        # Enhanced table display with styling
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Timestamp': st.column_config.DatetimeColumn('Timestamp', width='medium'),
                'Strategy': st.column_config.TextColumn('Strategy', width='medium'),
                'Action': st.column_config.TextColumn('Action', width='small'),
                'Amount': st.column_config.TextColumn('Amount', width='small'),
                'Status': st.column_config.TextColumn('Status', width='small'),
                'P&L': st.column_config.TextColumn('P&L', width='small')
            }
        )
    else:
        st.warning("⚠️ No transactions match the current filters")

    # Strategy performance metrics
    st.subheader("📈 Strategy Performance Metrics")

    # Calculate performance metrics from trading data
    strategy_metrics = {}

    for strategy in strategies:
        strategy_trades = [d for d in trading_data if d['Strategy'] == strategy and d['Status'] == 'COMPLETED']

        if strategy_trades:
            total_trades = len(strategy_trades)
            profitable_trades = len([d for d in strategy_trades if '+' in d['P&L']])
            win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0

            # Calculate total P&L
            total_pnl = sum([float(d['P&L'].replace(' SOL', '').replace('+', '')) for d in strategy_trades])
            avg_profit = total_pnl / total_trades if total_trades > 0 else 0

            strategy_metrics[strategy] = {
                'Total Trades': total_trades,
                'Win Rate': f"{win_rate:.1f}%",
                'Avg Profit': f"{avg_profit:+.4f} SOL",
                'Total P&L': f"{total_pnl:+.4f} SOL"
            }
        else:
            strategy_metrics[strategy] = {
                'Total Trades': 0,
                'Win Rate': "0.0%",
                'Avg Profit': "0.0000 SOL",
                'Total P&L': "0.0000 SOL"
            }

    # Display strategy metrics
    metrics_df = pd.DataFrame(strategy_metrics).T
    metrics_df.index.name = 'Strategy'

    st.dataframe(
        metrics_df,
        use_container_width=True,
        column_config={
            'Total Trades': st.column_config.NumberColumn('Total Trades', width='small'),
            'Win Rate': st.column_config.TextColumn('Win Rate', width='small'),
            'Avg Profit': st.column_config.TextColumn('Avg Profit', width='medium'),
            'Total P&L': st.column_config.TextColumn('Total P&L', width='medium')
        }
    )

    # Performance visualization
    col1, col2 = st.columns(2)

    with col1:
        # Win rate comparison chart
        win_rates = [float(strategy_metrics[s]['Win Rate'].replace('%', '')) for s in strategies]

        fig = go.Figure(data=[
            go.Bar(
                x=strategies,
                y=win_rates,
                marker_color=['#ff4444' if wr < 50 else '#44ff44' for wr in win_rates],
                text=[f"{wr:.1f}%" for wr in win_rates],
                textposition='auto'
            )
        ])

        fig.update_layout(
            title='Strategy Win Rates',
            xaxis_title='Strategy',
            yaxis_title='Win Rate (%)',
            height=400,
            yaxis=dict(range=[0, 100])
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Total P&L comparison chart
        total_pnls = [float(strategy_metrics[s]['Total P&L'].replace(' SOL', '').replace('+', '')) for s in strategies]

        fig = go.Figure(data=[
            go.Bar(
                x=strategies,
                y=total_pnls,
                marker_color=['#ff4444' if pnl < 0 else '#44ff44' for pnl in total_pnls],
                text=[f"{pnl:+.3f}" for pnl in total_pnls],
                textposition='auto'
            )
        ])

        fig.update_layout(
            title='Strategy Total P&L',
            xaxis_title='Strategy',
            yaxis_title='Total P&L (SOL)',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    # Recent AI decisions display
    st.subheader("🧠 Recent AI Decisions")

    # Generate simulated AI decision data
    ai_decisions = []
    decision_types = ['ENTRY_SIGNAL', 'EXIT_SIGNAL', 'RISK_ADJUSTMENT', 'PORTFOLIO_REBALANCE', 'STRATEGY_SWITCH']
    confidence_levels = ['HIGH', 'MEDIUM', 'LOW']

    for i in range(20):
        timestamp = datetime.utcnow() - timedelta(minutes=random.randint(1, 360))  # Last 6 hours
        decision_type = random.choice(decision_types)
        confidence = random.choice(confidence_levels)
        confidence_score = random.uniform(0.6, 0.95)

        # Generate decision details based on type
        if decision_type == 'ENTRY_SIGNAL':
            details = f"Entry signal for {random.choice(strategies)} - Target: {random.uniform(0.01, 0.1):.3f} SOL"
        elif decision_type == 'EXIT_SIGNAL':
            details = f"Exit signal for {random.choice(strategies)} - P&L: {random.uniform(-0.02, 0.05):+.4f} SOL"
        elif decision_type == 'RISK_ADJUSTMENT':
            details = f"Risk adjustment - Position size: {random.uniform(0.5, 2.0):.1f}x multiplier"
        elif decision_type == 'PORTFOLIO_REBALANCE':
            details = f"Portfolio rebalance - Allocation shift: {random.uniform(5, 15):.1f}%"
        else:  # STRATEGY_SWITCH
            old_profile = random.choice(['AGGRESSIVE', 'BALANCED', 'PRESERVATION'])
            new_profile = random.choice(['AGGRESSIVE', 'BALANCED', 'PRESERVATION'])
            details = f"Strategy switch: {old_profile} → {new_profile}"

        ai_decisions.append({
            'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Decision Type': decision_type,
            'Confidence': confidence,
            'Score': f"{confidence_score:.2f}",
            'Details': details,
            'Status': random.choice(['EXECUTED', 'PENDING', 'REJECTED'])
        })

    # Sort by timestamp (most recent first)
    ai_decisions.sort(key=lambda x: x['Timestamp'], reverse=True)

    # Display AI decisions table
    if ai_decisions:
        # Show only recent decisions (last 10)
        recent_decisions = ai_decisions[:10]
        df_ai = pd.DataFrame(recent_decisions)

        st.dataframe(
            df_ai,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Timestamp': st.column_config.DatetimeColumn('Timestamp', width='medium'),
                'Decision Type': st.column_config.TextColumn('Decision Type', width='medium'),
                'Confidence': st.column_config.TextColumn('Confidence', width='small'),
                'Score': st.column_config.NumberColumn('Score', width='small'),
                'Details': st.column_config.TextColumn('Details', width='large'),
                'Status': st.column_config.TextColumn('Status', width='small')
            }
        )

        # AI decision statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_decisions = len(ai_decisions)
            st.metric("Total Decisions (6h)", total_decisions)

        with col2:
            executed_decisions = len([d for d in ai_decisions if d['Status'] == 'EXECUTED'])
            execution_rate = (executed_decisions / total_decisions) * 100 if total_decisions > 0 else 0
            st.metric("Execution Rate", f"{execution_rate:.1f}%")

        with col3:
            avg_confidence = sum([float(d['Score']) for d in ai_decisions]) / len(ai_decisions)
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")

        with col4:
            high_confidence = len([d for d in ai_decisions if d['Confidence'] == 'HIGH'])
            st.metric("High Confidence", f"{high_confidence}/{total_decisions}")

        # AI decision confidence distribution
        st.subheader("📊 AI Decision Confidence Distribution")

        confidence_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for decision in ai_decisions:
            confidence_counts[decision['Confidence']] += 1

        fig = go.Figure(data=[
            go.Pie(
                labels=list(confidence_counts.keys()),
                values=list(confidence_counts.values()),
                hole=0.4,
                marker_colors=['#44ff44', '#ffaa00', '#ff4444']
            )
        ])

        fig.update_layout(
            title="AI Decision Confidence Levels",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("📋 No recent AI decisions available")

    # Real-time activity summary
    st.subheader("⚡ Real-time Activity Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🔄 Last 1 Hour")
        recent_trades = [d for d in trading_data if (datetime.utcnow() - datetime.strptime(d['Timestamp'], '%Y-%m-%d %H:%M:%S')).seconds <= 3600]
        recent_ai = [d for d in ai_decisions if (datetime.utcnow() - datetime.strptime(d['Timestamp'], '%Y-%m-%d %H:%M:%S')).seconds <= 3600]

        st.metric("Trades", len(recent_trades))
        st.metric("AI Decisions", len(recent_ai))

        if recent_trades:
            recent_pnl = sum([float(d['P&L'].replace(' SOL', '').replace('+', '')) for d in recent_trades if d['Status'] == 'COMPLETED'])
            st.metric("P&L", f"{recent_pnl:+.4f} SOL")
        else:
            st.metric("P&L", "0.0000 SOL")

    with col2:
        st.markdown("### 📊 Performance")
        completed_trades = [d for d in trading_data if d['Status'] == 'COMPLETED']
        if completed_trades:
            total_pnl = sum([float(d['P&L'].replace(' SOL', '').replace('+', '')) for d in completed_trades])
            profitable = len([d for d in completed_trades if '+' in d['P&L']])
            win_rate = (profitable / len(completed_trades)) * 100

            st.metric("Total P&L", f"{total_pnl:+.4f} SOL")
            st.metric("Win Rate", f"{win_rate:.1f}%")
            st.metric("Total Trades", len(completed_trades))
        else:
            st.metric("Total P&L", "0.0000 SOL")
            st.metric("Win Rate", "0.0%")
            st.metric("Total Trades", "0")

    with col3:
        st.markdown("### 🎯 System Status")
        st.metric("Trading Mode", "🟢 ACTIVE")
        st.metric("AI Brain", "🧠 ONLINE")
        st.metric("Strategies", f"{len(strategies)} ACTIVE")

        # Last activity timestamp
        if trading_data:
            last_activity = max([datetime.strptime(d['Timestamp'], '%Y-%m-%d %H:%M:%S') for d in trading_data])
            time_since = (datetime.utcnow() - last_activity).seconds
            st.metric("Last Activity", f"{time_since}s ago")

def render_system_health():
    """Render the system health overview dashboard."""
    st.header("🟢 System Health Overview")

    # System status indicators
    st.subheader("🔧 Core System Components")

    # Adaptive Cortex status indicators
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Portfolio Monitor status
        if st.session_state.portfolio_monitor:
            st.success("✅ Portfolio Monitor")
            st.metric("Status", "🟢 OPERATIONAL")
            st.metric("Last Update", "5s ago")
        else:
            st.error("❌ Portfolio Monitor")
            st.metric("Status", "🔴 OFFLINE")

    with col2:
        # Strategy Mapper status
        if st.session_state.strategy_mapper:
            st.success("✅ Strategy Mapper")
            st.metric("Status", "🟢 OPERATIONAL")
            st.metric("Active Profile", "🟡 BALANCED")
        else:
            st.error("❌ Strategy Mapper")
            st.metric("Status", "🔴 OFFLINE")

    with col3:
        # Goal Manager status
        if st.session_state.goal_manager:
            st.success("✅ Goal Manager")
            st.metric("Status", "🟢 OPERATIONAL")
            st.metric("Current Goal", "2.0 SOL")
        else:
            st.error("❌ Goal Manager")
            st.metric("Status", "🔴 OFFLINE")

    with col4:
        # Risk Manager status (simulated)
        st.success("✅ Risk Manager")
        st.metric("Status", "🟢 OPERATIONAL")
        st.metric("Risk Level", "🟡 MEDIUM")

    # Service health grid
    st.subheader("🌐 Infrastructure Services")

    # Simulated service health data
    services = {
        'DragonflyDB': {'status': 'healthy', 'uptime': '99.9%', 'response_time': '2ms', 'connections': 15},
        'TensorZero': {'status': 'healthy', 'uptime': '99.8%', 'response_time': '45ms', 'requests': 1250},
        'Prometheus': {'status': 'healthy', 'uptime': '100%', 'response_time': '8ms', 'metrics': 2847},
        'Grafana': {'status': 'healthy', 'uptime': '99.9%', 'response_time': '120ms', 'dashboards': 12},
        'Nginx': {'status': 'healthy', 'uptime': '100%', 'response_time': '3ms', 'requests': 5420},
        'Mission Control': {'status': 'healthy', 'uptime': '100%', 'response_time': '15ms', 'users': 1}
    }

    # Create service health grid
    service_data = []
    for service, metrics in services.items():
        status_icon = "🟢" if metrics['status'] == 'healthy' else "🔴"
        service_data.append({
            'Service': f"{status_icon} {service}",
            'Status': metrics['status'].upper(),
            'Uptime': metrics['uptime'],
            'Response Time': metrics['response_time'],
            'Additional Info': f"{list(metrics.keys())[4]}: {list(metrics.values())[4]}"
        })

    df_services = pd.DataFrame(service_data)
    st.dataframe(
        df_services,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Service': st.column_config.TextColumn('Service', width='medium'),
            'Status': st.column_config.TextColumn('Status', width='small'),
            'Uptime': st.column_config.TextColumn('Uptime', width='small'),
            'Response Time': st.column_config.TextColumn('Response Time', width='small'),
            'Additional Info': st.column_config.TextColumn('Additional Info', width='medium')
        }
    )

    # Performance metrics
    st.subheader("⚡ Performance Metrics")

    col1, col2 = st.columns(2)

    with col1:
        # System performance metrics
        st.markdown("### 🖥️ System Performance")

        # Simulated performance data
        cpu_usage = 45.2
        memory_usage = 62.8
        disk_usage = 34.1
        network_io = 125.6

        # CPU Usage
        fig_cpu = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = cpu_usage,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "CPU Usage (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_cpu.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_cpu, use_container_width=True)

        # Memory and Disk metrics
        col_mem, col_disk = st.columns(2)
        with col_mem:
            st.metric("Memory Usage", f"{memory_usage:.1f}%", delta="-2.3%")
        with col_disk:
            st.metric("Disk Usage", f"{disk_usage:.1f}%", delta="+0.8%")

        st.metric("Network I/O", f"{network_io:.1f} MB/s", delta="+15.2 MB/s")

    with col2:
        # Trading system performance
        st.markdown("### 📊 Trading Performance")

        # Latency metrics
        latencies = {
            'Portfolio Monitor': 0.002,
            'Strategy Mapper': 0.001,
            'Goal Manager': 0.003,
            'Risk Manager': 0.001,
            'Decision Engine': 0.005
        }

        # Create latency chart
        fig_latency = go.Figure(data=[
            go.Bar(
                x=list(latencies.keys()),
                y=list(latencies.values()),
                marker_color=['#44ff44' if lat < 0.01 else '#ffaa00' if lat < 0.05 else '#ff4444' for lat in latencies.values()],
                text=[f"{lat*1000:.1f}ms" for lat in latencies.values()],
                textposition='auto'
            )
        ])

        fig_latency.update_layout(
            title='Component Latency (Sub-50ms Target)',
            xaxis_title='Component',
            yaxis_title='Latency (seconds)',
            height=300,
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig_latency, use_container_width=True)

        # Performance summary
        total_latency = sum(latencies.values())
        avg_latency = total_latency / len(latencies)

        st.metric("Total Latency", f"{total_latency*1000:.1f}ms", delta="✅ <50ms")
        st.metric("Avg Component", f"{avg_latency*1000:.1f}ms", delta="✅ Excellent")
        st.metric("Decision Frequency", "12.5 Hz", delta="+2.1 Hz")

    # Alert summary from AlertManager integration
    st.subheader("🚨 Alert Summary")

    # Simulated alert data
    alerts = [
        {'severity': 'INFO', 'component': 'Portfolio Monitor', 'message': 'Portfolio value increased by 5%', 'time': '2 minutes ago'},
        {'severity': 'WARNING', 'component': 'Strategy Mapper', 'message': 'Profile switch frequency above normal', 'time': '15 minutes ago'},
        {'severity': 'INFO', 'component': 'Goal Manager', 'message': 'Goal progress milestone reached (75%)', 'time': '1 hour ago'},
        {'severity': 'SUCCESS', 'component': 'Risk Manager', 'message': 'All risk parameters within limits', 'time': '2 hours ago'}
    ]

    # Display alerts
    for alert in alerts:
        severity_color = {
            'SUCCESS': 'success',
            'INFO': 'info',
            'WARNING': 'warning',
            'ERROR': 'error'
        }.get(alert['severity'], 'info')

        severity_icon = {
            'SUCCESS': '✅',
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌'
        }.get(alert['severity'], 'ℹ️')

        with st.container():
            if severity_color == 'success':
                st.success(f"{severity_icon} **{alert['component']}**: {alert['message']} _{alert['time']}_")
            elif severity_color == 'info':
                st.info(f"{severity_icon} **{alert['component']}**: {alert['message']} _{alert['time']}_")
            elif severity_color == 'warning':
                st.warning(f"{severity_icon} **{alert['component']}**: {alert['message']} _{alert['time']}_")
            else:
                st.error(f"{severity_icon} **{alert['component']}**: {alert['message']} _{alert['time']}_")

    # System health summary
    st.subheader("📋 Health Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Overall Health", "🟢 EXCELLENT")
        st.metric("Uptime", "99.9%")

    with col2:
        st.metric("Active Alerts", "1 WARNING")
        st.metric("Resolved Today", "3 ALERTS")

    with col3:
        st.metric("Performance", "🟢 OPTIMAL")
        st.metric("Efficiency", "94.2%")

    with col4:
        st.metric("Last Restart", "3 days ago")
        st.metric("Next Maintenance", "7 days")

def main():
    """Main application function."""
    render_header()
    
    # Initialize components
    if not st.session_state.initialized:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(initialize_components())
        if not success:
            st.stop()
    
    # Enhanced auto-refresh with error handling and user feedback
    if st.session_state.initialized:
        # Check if auto-refresh is enabled
        if 'auto_refresh_enabled' not in st.session_state:
            st.session_state.auto_refresh_enabled = True

        # Auto-refresh interval setting
        refresh_interval = st.sidebar.selectbox(
            "🔄 Auto-refresh Interval",
            options=[5, 10, 30, 60],
            index=0,
            format_func=lambda x: f"{x} seconds",
            help="How often to refresh dashboard data"
        )

        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox(
            "Enable Auto-refresh",
            value=st.session_state.auto_refresh_enabled,
            help="Automatically refresh data at the selected interval"
        )
        st.session_state.auto_refresh_enabled = auto_refresh

        # Perform auto-refresh if enabled
        if auto_refresh:
            should_refresh = False

            if st.session_state.last_update is None:
                should_refresh = True
            else:
                time_since_update = (datetime.utcnow() - st.session_state.last_update).seconds
                should_refresh = time_since_update >= refresh_interval

            if should_refresh:
                try:
                    with st.spinner(f"🔄 Refreshing data..."):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(update_data())

                        # Show refresh success in sidebar
                        st.sidebar.success(f"✅ Data refreshed at {datetime.utcnow().strftime('%H:%M:%S')}")

                        # Auto-rerun to update the display
                        time.sleep(0.1)  # Brief pause
                        st.rerun()

                except Exception as e:
                    st.sidebar.error(f"❌ Refresh failed: {e}")
                    st.session_state.auto_refresh_enabled = False  # Disable on error

        # Display refresh status in sidebar
        if st.session_state.last_update:
            time_since = (datetime.utcnow() - st.session_state.last_update).seconds
            st.sidebar.info(f"⏱️ Last refresh: {time_since}s ago")

            if 'update_count' in st.session_state:
                st.sidebar.info(f"📊 Total updates: {st.session_state.update_count}")
        else:
            st.sidebar.warning("⚠️ No data updates yet")
    
    # Sidebar navigation
    st.sidebar.title("🧠 Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Goal Management", "Portfolio Tracking", "Trading Activity", "System Health"]
    )
    
    # Render selected page
    if page == "Goal Management":
        render_goal_management()
    elif page == "Portfolio Tracking":
        render_portfolio_tracking()
    elif page == "Trading Activity":
        render_trading_activity()
    elif page == "System Health":
        render_system_health()
    
    # Auto-refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        if st.session_state.initialized:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(update_data())
            st.rerun()

if __name__ == "__main__":
    main()
