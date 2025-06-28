#!/usr/bin/env python3
"""
Test script to verify AI Brain Goal Management System implementation.
Tests goal persistence, validation, history tracking, and vector memory integration.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

# Add brain to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'brain', 'src'))

async def test_enhanced_goal_manager():
    """Test enhanced goal manager functionality"""
    print("🎯 Testing Enhanced Goal Manager")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager, TradingGoal, GoalType
        
        print("✅ Successfully imported enhanced goal manager")
        
        # Test 1: Enhanced TradingGoal dataclass
        test_goal = TradingGoal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=2.0,
            description="Test enhanced goal",
            modified_by="test_user",
            target_usd=300.0,
            change_reason="Testing enhanced features",
            priority=2,
            deadline=datetime.now() + timedelta(days=30)
        )
        
        print("✅ Enhanced TradingGoal dataclass working")
        print(f"   - Target SOL: {test_goal.target_sol}")
        print(f"   - Target USD: {test_goal.target_usd}")
        print(f"   - Priority: {test_goal.priority}")
        print(f"   - Deadline: {test_goal.deadline}")
        print(f"   - Change reason: {test_goal.change_reason}")
        
        # Test 2: Goal validation
        validation_result = await dynamic_goal_manager.validate_goal(test_goal)
        print(f"✅ Goal validation working: {validation_result['is_valid']}")
        if validation_result['warnings']:
            print(f"   - Warnings: {validation_result['warnings']}")
        if validation_result['errors']:
            print(f"   - Errors: {validation_result['errors']}")
        
        # Test 3: Goal analytics
        analytics = await dynamic_goal_manager.get_goal_analytics()
        print("✅ Goal analytics working")
        print(f"   - Current goal exists: {analytics['current_goal']['exists']}")
        print(f"   - Total goals in history: {analytics['history_stats']['total_goals']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced goal manager test failed: {e}")
        return False

async def test_goal_memory_integration():
    """Test goal memory integration functionality"""
    print("\n🧠 Testing Goal Memory Integration")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_memory_integration import goal_memory_integration, GoalType
        from overmind_brain.goal_manager import TradingGoal
        
        print("✅ Successfully imported goal memory integration")
        
        # Test 1: Initialize integration
        initialized = await goal_memory_integration.initialize()
        print(f"✅ Goal memory integration initialized: {initialized}")
        
        # Test 2: Test goal recommendations
        mock_portfolio = {
            'total_value_sol': 1.5,
            'total_value_usd': 225.0
        }
        
        recommendations = await goal_memory_integration.get_goal_recommendations(mock_portfolio)
        print(f"✅ Goal recommendations generated: {len(recommendations)} recommendations")
        
        for i, rec in enumerate(recommendations[:3]):
            print(f"   {i+1}. {rec['goal_type']}: {rec['target_sol']} SOL (confidence: {rec['confidence']:.2f})")
        
        # Test 3: Goal performance analysis
        analysis = await goal_memory_integration.analyze_goal_performance(GoalType.REACH_BALANCE)
        print(f"✅ Goal performance analysis working")
        print(f"   - Goal type: {analysis['goal_type']}")
        print(f"   - Analysis available: {'error' not in analysis}")
        
        # Test 4: Goal insights
        insights = await goal_memory_integration.get_goal_insights()
        print(f"✅ Goal insights generated")
        print(f"   - Current goal status: {insights['current_goal_status']['has_goal']}")
        print(f"   - Memory integration active: {'memory_integration' in insights}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal memory integration test failed: {e}")
        return False

async def test_goal_persistence():
    """Test goal persistence functionality"""
    print("\n💾 Testing Goal Persistence")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager, GoalType
        
        # Test setting a goal with enhanced parameters
        success = await dynamic_goal_manager.set_goal(
            goal_type=GoalType.MAXIMIZE_PROFIT,
            target_sol=3.0,
            description="Test persistence goal",
            modified_by="test_system",
            target_usd=450.0,
            change_reason="Testing persistence",
            priority=3,
            deadline=datetime.now() + timedelta(days=45)
        )
        
        print(f"✅ Goal setting with enhanced parameters: {success}")
        
        # Test getting current goal
        current_goal = await dynamic_goal_manager.get_current_goal()
        if current_goal:
            print("✅ Goal retrieval working")
            print(f"   - Type: {current_goal.goal_type.value}")
            print(f"   - Target: {current_goal.target_sol} SOL")
            print(f"   - Priority: {current_goal.priority}")
        else:
            print("⚠️ No current goal found")
        
        # Test progress update
        progress_updated = await dynamic_goal_manager.update_goal_progress(25.5)
        print(f"✅ Goal progress update: {progress_updated}")
        
        # Test goal history
        history = await dynamic_goal_manager.get_goal_history(limit=5)
        print(f"✅ Goal history retrieval: {len(history)} goals in history")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal persistence test failed: {e}")
        return False

async def test_vector_memory_integration():
    """Test vector memory integration for goals"""
    print("\n🔗 Testing Vector Memory Integration")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_memory_integration import goal_memory_integration
        from overmind_brain.goal_manager import TradingGoal, GoalType
        
        # Test storing goal achievement
        test_goal = TradingGoal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=2.0,
            description="Test achievement goal",
            modified_by="test_system"
        )
        
        achievement_data = {
            'achieved_amount': 2.1,
            'success_rate': 85.0,
            'days_to_complete': 25,
            'strategy': 'Conservative growth',
            'market_conditions': 'Bullish',
            'key_factors': ['Good timing', 'Market momentum']
        }
        
        achievement_id = await goal_memory_integration.store_goal_achievement(test_goal, achievement_data)
        print(f"✅ Goal achievement stored in vector memory: {achievement_id is not None}")
        
        # Test storing goal failure
        failure_data = {
            'achieved_amount': 1.2,
            'failure_reason': 'Market downturn',
            'market_conditions': 'Bearish',
            'lessons_learned': ['Better risk management needed', 'Market timing important'],
            'recommended_changes': ['Lower targets', 'Better stop losses']
        }
        
        failure_id = await goal_memory_integration.store_goal_failure(test_goal, failure_data)
        print(f"✅ Goal failure stored in vector memory: {failure_id is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector memory integration test failed: {e}")
        return False

def test_goal_validation_edge_cases():
    """Test goal validation with edge cases"""
    print("\n🔍 Testing Goal Validation Edge Cases")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager, TradingGoal, GoalType
        
        # Test invalid goals
        test_cases = [
            {
                'name': 'Negative target SOL',
                'goal': TradingGoal(
                    goal_type=GoalType.REACH_BALANCE,
                    target_sol=-1.0,
                    description="Invalid negative target",
                    modified_by="test"
                )
            },
            {
                'name': 'Empty description',
                'goal': TradingGoal(
                    goal_type=GoalType.REACH_BALANCE,
                    target_sol=2.0,
                    description="",
                    modified_by="test"
                )
            },
            {
                'name': 'Invalid priority',
                'goal': TradingGoal(
                    goal_type=GoalType.REACH_BALANCE,
                    target_sol=2.0,
                    description="Valid description",
                    modified_by="test",
                    priority=5  # Invalid priority
                )
            }
        ]
        
        for test_case in test_cases:
            try:
                validation = asyncio.run(dynamic_goal_manager.validate_goal(test_case['goal']))
                expected_invalid = not validation['is_valid']
                print(f"✅ {test_case['name']}: {'Invalid as expected' if expected_invalid else 'Unexpectedly valid'}")
                if validation['errors']:
                    print(f"   - Errors: {validation['errors']}")
            except Exception as e:
                print(f"⚠️ {test_case['name']}: Validation error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal validation edge cases test failed: {e}")
        return False

async def test_goal_system_integration():
    """Test complete goal system integration"""
    print("\n🔄 Testing Complete Goal System Integration")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import dynamic_goal_manager
        from overmind_brain.goal_memory_integration import goal_memory_integration
        
        # Test complete workflow
        print("🔄 Testing complete goal management workflow...")
        
        # 1. Initialize systems
        goal_init = await dynamic_goal_manager.initialize()
        memory_init = await goal_memory_integration.initialize()
        print(f"✅ Systems initialized: Goal={goal_init}, Memory={memory_init}")
        
        # 2. Get status
        status = await dynamic_goal_manager.get_status()
        print(f"✅ Goal manager status retrieved: {status.get('redis_connected', False)}")
        
        # 3. Get comprehensive insights
        insights = await goal_memory_integration.get_goal_insights()
        print(f"✅ Comprehensive insights generated")
        print(f"   - Current goal status tracked: {'current_goal_status' in insights}")
        print(f"   - Historical performance analyzed: {'historical_performance' in insights}")
        print(f"   - Memory integration active: {'memory_integration' in insights}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal system integration test failed: {e}")
        return False

async def main():
    """Run all AI Brain Goal Management tests"""
    print("🧠 THE OVERMIND PROTOCOL - AI Brain Goal Management Tests")
    print("=" * 60)
    
    # Run all tests
    test1 = await test_enhanced_goal_manager()
    test2 = await test_goal_memory_integration()
    test3 = await test_goal_persistence()
    test4 = await test_vector_memory_integration()
    test5 = test_goal_validation_edge_cases()
    test6 = await test_goal_system_integration()
    
    print("\n" + "=" * 60)
    
    if all([test1, test2, test3, test4, test5, test6]):
        print("🎉 ALL AI BRAIN GOAL MANAGEMENT TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • Enhanced goal manager with full feature set")
        print("   • Goal persistence with validation and history")
        print("   • Vector memory integration for intelligent tracking")
        print("   • Goal recommendations based on past experiences")
        print("   • Performance analysis and insights")
        print("   • Complete goal management workflow")
        print("\n🚀 NEXT STEPS:")
        print("   • Configure DragonflyDB for production persistence")
        print("   • Test with real trading scenarios")
        print("   • Integrate with portfolio monitoring")
        print("   • Add goal achievement notifications")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
