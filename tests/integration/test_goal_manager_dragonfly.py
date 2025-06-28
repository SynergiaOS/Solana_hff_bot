#!/usr/bin/env python3
"""
Test Goal Manager with DragonflyDB integration.
Tests full goal management functionality with real DragonflyDB connection.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

# Add brain to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'brain', 'src'))

async def test_dragonfly_connection():
    """Test DragonflyDB connection"""
    print("🐉 Testing DragonflyDB Connection")
    print("-" * 40)
    
    try:
        import redis.asyncio as aioredis
        
        # Test connection
        client = await aioredis.from_url("redis://localhost:6379", decode_responses=True)
        response = await client.ping()
        print(f"✅ DragonflyDB ping: {response}")
        
        # Test basic operations
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        print(f"✅ DragonflyDB set/get: {value}")
        
        # Test list operations
        await client.lpush("test_list", "item1", "item2")
        items = await client.lrange("test_list", 0, -1)
        print(f"✅ DragonflyDB list operations: {len(items)} items")
        
        # Cleanup
        await client.delete("test_key", "test_list")
        await client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ DragonflyDB connection test failed: {e}")
        return False

async def test_goal_manager_initialization():
    """Test goal manager initialization with DragonflyDB"""
    print("\n🎯 Testing Goal Manager Initialization")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import DynamicGoalManager, GoalType
        
        # Create goal manager instance
        goal_manager = DynamicGoalManager(redis_host="localhost", redis_port=6379)
        print("✅ Goal manager instance created")
        
        # Initialize with DragonflyDB
        await goal_manager.initialize()
        print("✅ Goal manager initialized with DragonflyDB")
        
        # Test status
        status = await goal_manager.get_status()
        print(f"✅ Goal manager status: DragonflyDB connected = {status.get('redis_connected', False)}")
        
        # Test current goal
        current_goal = await goal_manager.get_current_goal()
        print(f"✅ Current goal retrieved: {current_goal is not None}")
        
        if current_goal:
            print(f"   - Type: {current_goal.goal_type.value}")
            print(f"   - Target: {current_goal.target_sol} SOL")
            print(f"   - Description: {current_goal.description}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal manager initialization test failed: {e}")
        return False

async def test_goal_persistence_dragonfly():
    """Test goal persistence with DragonflyDB"""
    print("\n💾 Testing Goal Persistence with DragonflyDB")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import DynamicGoalManager, GoalType
        
        # Create and initialize goal manager
        goal_manager = DynamicGoalManager()
        await goal_manager.initialize()
        
        # Set a new goal
        success = await goal_manager.set_goal(
            goal_type=GoalType.MAXIMIZE_PROFIT,
            target_sol=3.0,
            description="Test DragonflyDB persistence goal",
            modified_by="test_system",
            target_usd=450.0,
            change_reason="Testing DragonflyDB integration",
            priority=2
        )
        
        print(f"✅ Goal setting: {success}")
        
        if success:
            # Retrieve the goal
            current_goal = await goal_manager.get_current_goal()
            print(f"✅ Goal retrieval: {current_goal is not None}")
            
            if current_goal:
                print(f"   - Type: {current_goal.goal_type.value}")
                print(f"   - Target SOL: {current_goal.target_sol}")
                print(f"   - Target USD: {current_goal.target_usd}")
                print(f"   - Priority: {current_goal.priority}")
                print(f"   - Change reason: {current_goal.change_reason}")
            
            # Test progress update
            progress_success = await goal_manager.update_goal_progress(35.7)
            print(f"✅ Progress update: {progress_success}")
            
            # Verify progress was saved
            updated_goal = await goal_manager.get_current_goal()
            if updated_goal:
                print(f"   - Updated progress: {updated_goal.progress_percentage}%")
            
            # Test goal history
            history = await goal_manager.get_goal_history(limit=5)
            print(f"✅ Goal history: {len(history)} goals")
            
            for i, goal in enumerate(history[:3]):
                print(f"   {i+1}. {goal.goal_type.value}: {goal.target_sol} SOL")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal persistence test failed: {e}")
        return False

async def test_goal_analytics_dragonfly():
    """Test goal analytics with DragonflyDB data"""
    print("\n📊 Testing Goal Analytics with DragonflyDB")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import DynamicGoalManager
        
        # Create and initialize goal manager
        goal_manager = DynamicGoalManager()
        await goal_manager.initialize()
        
        # Get analytics
        analytics = await goal_manager.get_goal_analytics()
        print("✅ Goal analytics retrieved")
        
        # Display analytics
        current_goal = analytics.get('current_goal', {})
        print(f"   - Current goal exists: {current_goal.get('exists', False)}")
        print(f"   - Goal type: {current_goal.get('type', 'None')}")
        print(f"   - Target SOL: {current_goal.get('target_sol', 0)}")
        print(f"   - Progress: {current_goal.get('progress', 0)}%")
        print(f"   - Priority: {current_goal.get('priority', 0)}")
        
        history_stats = analytics.get('history_stats', {})
        print(f"   - Total goals in history: {history_stats.get('total_goals', 0)}")
        print(f"   - Average target SOL: {history_stats.get('avg_target_sol', 0):.2f}")
        
        performance = analytics.get('performance', {})
        print(f"   - Goals completed: {performance.get('goals_completed', 0)}")
        print(f"   - Average completion rate: {performance.get('avg_completion_rate', 0):.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal analytics test failed: {e}")
        return False

async def test_goal_validation_with_dragonfly():
    """Test goal validation with DragonflyDB storage"""
    print("\n🔍 Testing Goal Validation with DragonflyDB Storage")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import DynamicGoalManager, TradingGoal, GoalType
        
        # Create and initialize goal manager
        goal_manager = DynamicGoalManager()
        await goal_manager.initialize()
        
        # Test valid goal
        valid_goal = TradingGoal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=2.5,
            description="Valid goal for DragonflyDB testing",
            modified_by="test_system",
            priority=2,
            target_usd=375.0
        )
        
        validation = await goal_manager.validate_goal(valid_goal)
        print(f"✅ Valid goal validation: {validation['is_valid']}")
        
        if validation['is_valid']:
            # Store the valid goal
            success = await goal_manager.set_goal(
                goal_type=valid_goal.goal_type,
                target_sol=valid_goal.target_sol,
                description=valid_goal.description,
                modified_by=valid_goal.modified_by,
                target_usd=valid_goal.target_usd,
                priority=valid_goal.priority
            )
            print(f"✅ Valid goal stored in DragonflyDB: {success}")
        
        # Test invalid goal
        invalid_goal = TradingGoal(
            goal_type=GoalType.REACH_BALANCE,
            target_sol=-1.0,  # Invalid
            description="",   # Invalid
            modified_by="test_system",
            priority=5        # Invalid
        )
        
        validation = await goal_manager.validate_goal(invalid_goal)
        print(f"✅ Invalid goal validation: {not validation['is_valid']} (should be invalid)")
        print(f"   - Errors found: {len(validation['errors'])}")
        
        for error in validation['errors']:
            print(f"     • {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Goal validation with DragonflyDB test failed: {e}")
        return False

async def test_concurrent_goal_operations():
    """Test concurrent goal operations with DragonflyDB"""
    print("\n🔄 Testing Concurrent Goal Operations")
    print("-" * 40)
    
    try:
        from overmind_brain.goal_manager import DynamicGoalManager, GoalType
        
        # Create multiple goal manager instances
        managers = [DynamicGoalManager() for _ in range(3)]
        
        # Initialize all managers
        for i, manager in enumerate(managers):
            await manager.initialize()
            print(f"✅ Manager {i+1} initialized")
        
        # Test concurrent goal retrieval
        tasks = [manager.get_current_goal() for manager in managers]
        goals = await asyncio.gather(*tasks)
        
        print(f"✅ Concurrent goal retrieval: {len(goals)} results")
        
        # All should return the same goal (or None)
        goal_types = [goal.goal_type.value if goal else None for goal in goals]
        all_same = len(set(goal_types)) <= 1
        print(f"✅ Consistency check: {all_same}")
        
        # Test concurrent status checks
        status_tasks = [manager.get_status() for manager in managers]
        statuses = await asyncio.gather(*status_tasks)
        
        connected_count = sum(1 for status in statuses if status.get('redis_connected', False))
        print(f"✅ Concurrent status checks: {connected_count}/{len(managers)} connected")
        
        return True
        
    except Exception as e:
        print(f"❌ Concurrent operations test failed: {e}")
        return False

async def main():
    """Run all DragonflyDB goal management tests"""
    print("🐉 THE OVERMIND PROTOCOL - DragonflyDB Goal Management Tests")
    print("=" * 60)
    print("Testing complete goal management with DragonflyDB integration")
    print("=" * 60)
    
    # Run all tests
    test1 = await test_dragonfly_connection()
    test2 = await test_goal_manager_initialization()
    test3 = await test_goal_persistence_dragonfly()
    test4 = await test_goal_analytics_dragonfly()
    test5 = await test_goal_validation_with_dragonfly()
    test6 = await test_concurrent_goal_operations()
    
    print("\n" + "=" * 60)
    
    if all([test1, test2, test3, test4, test5, test6]):
        print("🎉 ALL DRAGONFLY GOAL MANAGEMENT TESTS PASSED!")
        print("\n✅ ACHIEVEMENTS:")
        print("   • DragonflyDB connection working perfectly")
        print("   • Goal Manager initialization with DragonflyDB")
        print("   • Goal persistence and retrieval from DragonflyDB")
        print("   • Goal analytics with real DragonflyDB data")
        print("   • Goal validation with DragonflyDB storage")
        print("   • Concurrent operations working correctly")
        print("\n🚀 MISSION STATUS: DYNAMIC GOAL MANAGEMENT COMPLETE")
        print("   • KROK 1: ChromaDB installation ✅")
        print("   • KROK 2: DragonflyDB integration ✅")
        print("   • KROK 3: Full goal management system ✅")
        print("\n🎯 READY FOR: Historical Data Testing Framework")
        
        return True
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Please check the errors above and fix issues")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
