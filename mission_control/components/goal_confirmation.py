"""THE OVERMIND PROTOCOL - Goal Change Confirmation Component
Enhanced confirmation dialogs with impact assessment for goal changes.
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime

def render_goal_change_confirmation(
    old_goal: Optional[Dict[str, Any]], 
    new_goal: Dict[str, Any],
    impact_assessment: Dict[str, Any]
) -> bool:
    """Render goal change confirmation dialog with impact assessment.
    
    Args:
        old_goal: Current goal information (None if no current goal)
        new_goal: Proposed new goal information
        impact_assessment: Impact assessment data
        
    Returns:
        bool: True if user confirms the change, False otherwise
    """
    
    st.markdown("### ⚠️ Confirm Goal Change")
    st.markdown("Please review the proposed changes and their potential impact:")
    
    # Goal comparison table
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Current Goal")
        if old_goal:
            st.markdown(f"""
            - **Type:** {old_goal.get('goal_type', 'N/A')}
            - **Target:** {old_goal.get('target_sol', 0):.1f} SOL
            - **Target USD:** ${old_goal.get('target_usd', 0):,.2f} (est.)
            - **Created:** {old_goal.get('created_at', 'Unknown')[:19].replace('T', ' ')}
            - **Modified:** {old_goal.get('modified_at', 'Unknown')[:19].replace('T', ' ')}
            """)
        else:
            st.markdown("*No current goal set*")
    
    with col2:
        st.markdown("#### 🎯 Proposed Goal")
        st.markdown(f"""
        - **Type:** {new_goal.get('goal_type', 'N/A')}
        - **Target:** {new_goal.get('target_sol', 0):.1f} SOL
        - **Target USD:** ${new_goal.get('target_usd', 0):,.2f} (est.)
        - **Reason:** {new_goal.get('reason', 'No reason provided')}
        - **Changed by:** {new_goal.get('changed_by', 'Unknown')}
        """)
    
    # Impact assessment
    st.markdown("#### 📈 Impact Assessment")
    
    if impact_assessment:
        # Create impact visualization
        col1, col2, col3 = st.columns(3)
        
        with col1:
            goal_type_changed = impact_assessment.get('goal_type_changed', False)
            if goal_type_changed:
                st.warning("⚠️ **Goal Type Change**")
                st.markdown("Trading strategy will be modified")
            else:
                st.success("✅ **Goal Type Unchanged**")
                st.markdown("Trading strategy remains consistent")
        
        with col2:
            percentage_change = impact_assessment.get('percentage_change', 0)
            if abs(percentage_change) > 20:
                st.error(f"🔴 **Significant Change**")
                st.markdown(f"Target change: {percentage_change:+.1f}%")
            elif abs(percentage_change) > 10:
                st.warning(f"🟡 **Moderate Change**")
                st.markdown(f"Target change: {percentage_change:+.1f}%")
            else:
                st.success(f"🟢 **Minor Change**")
                st.markdown(f"Target change: {percentage_change:+.1f}%")
        
        with col3:
            profile_change_likely = impact_assessment.get('profile_change_likely', False)
            if profile_change_likely:
                st.warning("⚠️ **Profile Switch Expected**")
                st.markdown("Strategy profile may change")
            else:
                st.success("✅ **Profile Stable**")
                st.markdown("Current profile likely maintained")
        
        # Risk level assessment
        risk_change = impact_assessment.get('risk_level_change', 'none')
        if risk_change == 'increased':
            st.error("🔴 **Risk Level: INCREASED** - More aggressive trading strategies may be employed")
        elif risk_change == 'decreased':
            st.success("🟢 **Risk Level: DECREASED** - More conservative trading strategies will be used")
        elif risk_change == 'modified':
            st.warning("🟡 **Risk Level: MODIFIED** - Risk profile will be adjusted based on new goal type")
        else:
            st.info("🔵 **Risk Level: UNCHANGED** - Current risk parameters will be maintained")
    
    # Confirmation checkboxes
    st.markdown("#### ✅ Confirmation Requirements")
    
    understanding_checked = st.checkbox(
        "I understand that this goal change will affect the AI trading behavior",
        help="The Adaptive Cortex will adjust trading strategies based on the new goal"
    )
    
    impact_acknowledged = st.checkbox(
        "I acknowledge the potential impact on portfolio progression and risk levels",
        help="Goal changes can affect how aggressively or conservatively the system trades"
    )
    
    responsibility_accepted = st.checkbox(
        "I accept responsibility for this goal change and its consequences",
        help="You are responsible for the trading decisions resulting from this goal change"
    )
    
    # Final confirmation buttons
    st.markdown("#### 🚀 Final Confirmation")
    
    all_confirmed = understanding_checked and impact_acknowledged and responsibility_accepted
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button(
            "✅ Confirm Goal Change", 
            type="primary",
            disabled=not all_confirmed,
            use_container_width=True,
            help="Proceed with the goal change" if all_confirmed else "Please check all confirmation boxes"
        ):
            if all_confirmed:
                return True
    
    with col3:
        if st.button(
            "❌ Cancel Change",
            use_container_width=True,
            help="Cancel the goal change and return to current settings"
        ):
            return False
    
    return None  # No decision made yet

def calculate_goal_impact_assessment(old_goal: Optional[Dict[str, Any]], new_goal: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate impact assessment for goal change.
    
    Args:
        old_goal: Current goal information
        new_goal: Proposed new goal information
        
    Returns:
        Dict containing impact assessment data
    """
    
    impact = {
        'goal_type_changed': False,
        'target_increased': False,
        'target_decreased': False,
        'percentage_change': 0.0,
        'profile_change_likely': False,
        'risk_level_change': 'none',
        'estimated_time_to_goal': None,
        'strategy_adjustments': []
    }
    
    if old_goal:
        # Check goal type change
        old_type = old_goal.get('goal_type', '')
        new_type = new_goal.get('goal_type', '')
        impact['goal_type_changed'] = old_type != new_type
        
        # Check target change
        old_target = old_goal.get('target_sol', 0)
        new_target = new_goal.get('target_sol', 0)
        
        if new_target > old_target:
            impact['target_increased'] = True
            impact['percentage_change'] = ((new_target - old_target) / old_target) * 100
        elif new_target < old_target:
            impact['target_decreased'] = True
            impact['percentage_change'] = ((new_target - old_target) / old_target) * 100
        
        # Assess profile change likelihood
        impact['profile_change_likely'] = abs(impact['percentage_change']) > 10
        
        # Assess risk level change
        risk_mapping = {
            'REACH_BALANCE': 'moderate',
            'CAPITAL_PRESERVATION': 'low',
            'MAXIMIZE_PROFIT': 'high'
        }
        
        old_risk = risk_mapping.get(old_type, 'moderate')
        new_risk = risk_mapping.get(new_type, 'moderate')
        
        if new_risk == 'high' and old_risk != 'high':
            impact['risk_level_change'] = 'increased'
        elif new_risk == 'low' and old_risk != 'low':
            impact['risk_level_change'] = 'decreased'
        elif new_risk != old_risk:
            impact['risk_level_change'] = 'modified'
        
        # Strategy adjustments
        if impact['goal_type_changed']:
            if new_type == 'MAXIMIZE_PROFIT':
                impact['strategy_adjustments'].append('Enable aggressive growth strategies')
                impact['strategy_adjustments'].append('Increase position sizes')
                impact['strategy_adjustments'].append('Higher risk tolerance')
            elif new_type == 'CAPITAL_PRESERVATION':
                impact['strategy_adjustments'].append('Enable conservative strategies')
                impact['strategy_adjustments'].append('Reduce position sizes')
                impact['strategy_adjustments'].append('Lower risk tolerance')
            else:  # REACH_BALANCE
                impact['strategy_adjustments'].append('Balanced strategy approach')
                impact['strategy_adjustments'].append('Moderate position sizing')
                impact['strategy_adjustments'].append('Standard risk parameters')
    
    return impact

def render_goal_change_success(goal_info: Dict[str, Any]):
    """Render success message after goal change.
    
    Args:
        goal_info: Information about the successfully changed goal
    """
    
    st.success("🎉 **Goal Successfully Updated!**")
    
    st.markdown(f"""
    ### ✅ New Goal Active
    
    **Goal Type:** {goal_info.get('goal_type', 'Unknown')}  
    **Target:** {goal_info.get('target_sol', 0):.1f} SOL  
    **Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  
    
    The Adaptive Cortex is now adjusting trading behavior based on your new goal.
    You can monitor the progress in the Portfolio Tracking section.
    """)
    
    # Show balloons animation
    st.balloons()
    
    # Auto-redirect suggestion
    st.info("💡 **Tip:** Check the Portfolio Tracking page to see how your new goal affects trading behavior!")
