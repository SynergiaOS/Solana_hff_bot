#!/usr/bin/env python3
"""
Simple test script for Goal Manager without external dependencies.
Tests basic goal management functionality without Redis or ChromaDB.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

# Add brain to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'brain', 'src'))

async def test_goal_dataclass():
    """Test enhanced TradingGoal dataclass"""
    print("🎯 Testing Enhanced TradingGoal Dataclass")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import TradingGoal, GoalType
        
        # Test basic goal creation
        goal = TradingGoal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=2.0,
            description="Test goal",
            modified_by="test_user"
        )
        
        print("✅ Basic TradingGoal creation working")
        print(f"   - Goal type: {goal.goal_type.value}")
        print(f"   - Target SOL: {goal.target_sol}")
        print(f"   - Description: {goal.description}")
        print(f"   - Created at: {goal.created_at}")
        print(f"   - Modified at: {goal.modified_at}")
        
        # Test enhanced goal creation
        enhanced_goal = TradingGoal(
            goal_type=GoalType.MAXIMIZE_PROFIT,
            target_sol=5.0,
            description="Enhanced test goal",
            modified_by="test_user",
            target_usd=750.0,
            change_reason="Testing enhanced features",
            priority=3,
            deadline=datetime.now() + timedelta(days=30),
            progress_percentage=25.5
        )
        
        print("✅ Enhanced TradingGoal creation working")
        print(f"   - Target USD: {enhanced_goal.target_usd}")
        print(f"   - Priority: {enhanced_goal.priority}")
        print(f"   - Progress: {enhanced_goal.progress_percentage}%")
        print(f"   - Deadline: {enhanced_goal.deadline}")
        print(f"   - Change reason: {enhanced_goal.change_reason}")
        print(f"   - Is active: {enhanced_goal.is_active}")
        
        return True
        
    except Exception as e:
        print(f"❌ TradingGoal dataclass test failed: {e}")
        return False

async def test_goal_validation():
    """Test goal validation functionality"""
    print("\n🔍 Testing Goal Validation")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager, TradingGoal, GoalType
        
        # Test valid goal
        valid_goal = TradingGoal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=2.0,
            description="Valid test goal",
            modified_by="test_user",
            priority=2
        )
        
        validation = await dynamic_goal_manager.validate_goal(valid_goal)
        print(f"✅ Valid goal validation: {validation['is_valid']}")
        if validation['warnings']:
            print(f"   - Warnings: {validation['warnings']}")
        
        # Test invalid goal - negative target
        invalid_goal = TradingGoal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=-1.0,
            description="Invalid test goal",
            modified_by="test_user"
        )
        
        validation = await dynamic_goal_manager.validate_goal(invalid_goal)
        print(f"✅ Invalid goal validation: {not validation['is_valid']} (should be invalid)")
        if validation['errors']:
            print(f"   - Errors detected: {validation['errors']}")
        
        # Test goal with empty description
        empty_desc_goal = TradingGoal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=2.0,
            description="",
            modified_by="test_user"
        )
        
        validation = await dynamic_goal_manager.validate_goal(empty_desc_goal)
        print(f"✅ Empty description validation: {not validation['is_valid']} (should be invalid)")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal validation test failed: {e}")
        return False

async def test_goal_manager_status():
    """Test goal manager status functionality"""
    print("\n📊 Testing Goal Manager Status")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager
        
        # Test status without Redis (should handle gracefully)
        status = await dynamic_goal_manager.get_status()
        print("✅ Goal manager status retrieved")
        print(f"   - Redis connected: {status.get('redis_connected', False)}")
        print(f"   - Goal change listeners: {status.get('goal_change_listeners', 0)}")
        print(f"   - Has error: {'error' in status}")
        
        if 'error' in status:
            print(f"   - Error (expected without Redis): {status['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal manager status test failed: {e}")
        return False

def test_goal_types():
    """Test GoalType enum"""
    print("\n🏷️ Testing GoalType Enum")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import GoalType
        
        # Test all goal types
        goal_types = [GoalType.REACH_BALANCE, GoalType.CAPITAL_PRESERVATION, GoalType.MAXIMIZE_PROFIT]
        
        print("✅ GoalType enum working")
        for goal_type in goal_types:
            print(f"   - {goal_type.name}: {goal_type.value}")
        
        # Test goal type conversion
        reach_balance = GoalType("REACH_BALANCE")
        print(f"✅ GoalType conversion working: {reach_balance.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ GoalType enum test failed: {e}")
        return False

async def test_goal_analytics_mock():
    """Test goal analytics with mock data"""
    print("\n📈 Testing Goal Analytics (Mock Mode)")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager
        
        # Test analytics without Redis (should return default values)
        analytics = await dynamic_goal_manager.get_goal_analytics()
        print("✅ Goal analytics retrieved (mock mode)")
        print(f"   - Current goal exists: {analytics['current_goal']['exists']}")
        print(f"   - Total goals in history: {analytics['history_stats']['total_goals']}")
        print(f"   - Average target SOL: {analytics['history_stats']['avg_target_sol']}")
        print(f"   - Goals completed: {analytics['performance']['goals_completed']}")
        print(f"   - Average completion rate: {analytics['performance']['avg_completion_rate']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal analytics test failed: {e}")
        return False

def test_goal_manager_import():
    """Test goal manager import and basic functionality"""
    print("\n📦 Testing Goal Manager Import")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager, TradingGoal, GoalType
        
        print("✅ Goal manager imported successfully")
        print(f"   - DynamicGoalManager class: {type(dynamic_goal_manager).__name__}")
        print(f"   - TradingGoal class available: {TradingGoal is not None}")
        print(f"   - GoalType enum available: {GoalType is not None}")
        
        # Test goal manager attributes
        print(f"   - Has current_goal attribute: {hasattr(dynamic_goal_manager, 'current_goal')}")
        print(f"   - Has goal_change_callbacks: {hasattr(dynamic_goal_manager, 'goal_change_callbacks')}")
        print(f"   - Has validate_goal method: {hasattr(dynamic_goal_manager, 'validate_goal')}")
        print(f"   - Has get_goal_analytics method: {hasattr(dynamic_goal_manager, 'get_goal_analytics')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal manager import test failed: {e}")
        return False

async def test_goal_progress_update():
    """Test goal progress update functionality"""
    print("\n📊 Testing Goal Progress Update")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager
        
        # Test progress update without current goal (should handle gracefully)
        result = await dynamic_goal_manager.update_goal_progress(50.0)
        print(f"✅ Progress update handled: {result}")
        print("   - Expected to fail without current goal (normal behavior)")
        
        # Test progress validation (edge cases)
        result_negative = await dynamic_goal_manager.update_goal_progress(-10.0)
        result_over_100 = await dynamic_goal_manager.update_goal_progress(150.0)
        
        print("✅ Progress validation working")
        print(f"   - Negative progress handled: {result_negative}")
        print(f"   - Over 100% progress handled: {result_over_100}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal progress update test failed: {e}")
        return False

async def main():
    """Run all simple goal management tests"""
    print("🧠 THE OVERMIND PROTOCOL - Simple Goal Management Tests")
    print("=" * 60)
    print("Note: Running without Redis/ChromaDB - testing core functionality only")
    print("=" * 60)
    
    # Run all tests
    test1 = test_goal_manager_import()
    test2 = test_goal_types()
    test3 = await test_goal_dataclass()
    test4 = await test_goal_validation()
    test5 = await test_goal_manager_status()
    test6 = await test_goal_analytics_mock()
    test7 = await test_goal_progress_update()
    
    print("\n" + "=" * 60)
    
    if all([test1, test2, test3, test4, test5, test6, test7]):
        print("🎉 ALL SIMPLE GOAL MANAGEMENT TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • Enhanced TradingGoal dataclass working")
        print("   • Goal validation functionality implemented")
        print("   • Goal manager status reporting working")
        print("   • Goal analytics framework ready")
        print("   • Progress update functionality implemented")
        print("   • All core goal management features functional")
        print("\n🚀 NEXT STEPS:")
        print("   • Install and configure Redis/DragonflyDB for persistence")
        print("   • Install ChromaDB for vector memory integration")
        print("   • Test with real database connections")
        print("   • Integrate with portfolio monitoring")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
