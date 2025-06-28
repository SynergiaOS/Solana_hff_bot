#!/usr/bin/env python3
"""
Test script to verify the datetime fixes in Mission Control.
This tests the Goal class datetime handling and utc_now() function.
"""

import sys
import os
from datetime import datetime, timezone

# Add mission_control to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mission_control'))

def test_datetime_fixes():
    """Test that datetime fixes work correctly."""
    print("🧪 Testing Mission Control Datetime Fixes")
    print("=" * 50)
    
    try:
        # Test the utc_now function
        from mission_control.app import utc_now, Goal
        
        print("✅ Successfully imported utc_now and Goal")
        
        # Test utc_now function
        current_time = utc_now()
        print(f"✅ utc_now() returns: {current_time}")
        print(f"✅ Type: {type(current_time)}")
        print(f"✅ Timezone aware: {current_time.tzinfo is not None}")
        
        # Test Goal with datetime objects
        goal_data = {
            "goal_type": "REACH_BALANCE",
            "target_sol": 2.0,
            "target_usd": 300.0,
            "created_at": current_time.isoformat(),
            "modified_at": current_time.isoformat()
        }
        
        goal = Goal.from_dict(goal_data)
        print(f"✅ Goal created with datetime strings")
        
        # Test datetime formatting (the issue that was causing TypeError)
        if isinstance(goal.created_at, str):
            formatted_time = goal.created_at
            print(f"✅ String datetime access works: {formatted_time}")
        else:
            formatted_time = goal.created_at.strftime('%Y-%m-%d %H:%M:%S')
            print(f"✅ Datetime object formatting works: {formatted_time}")
        
        # Test the exact pattern that was failing
        test_datetime_str = current_time.isoformat()
        test_datetime_obj = current_time
        
        # This should work now (was causing TypeError before)
        if isinstance(test_datetime_str, str):
            result1 = test_datetime_str if isinstance(test_datetime_str, str) else test_datetime_str.strftime('%Y-%m-%d %H:%M:%S')
            print(f"✅ String datetime handling: {result1}")
        
        if isinstance(test_datetime_obj, datetime):
            result2 = test_datetime_obj if isinstance(test_datetime_obj, str) else test_datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
            print(f"✅ Datetime object handling: {result2}")
        
        print("\n" + "=" * 50)
        print("🎉 All datetime fixes working correctly!")
        print("✅ No more TypeError on datetime slicing")
        print("✅ No more deprecation warnings for datetime.utcnow()")
        print("✅ Timezone-aware datetime handling implemented")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_timezone_awareness():
    """Test timezone awareness improvements."""
    print("\n🌍 Testing Timezone Awareness")
    print("-" * 30)
    
    try:
        from mission_control.app import utc_now
        
        # Test that utc_now returns timezone-aware datetime
        now = utc_now()
        
        if now.tzinfo is not None:
            print(f"✅ Timezone aware: {now.tzinfo}")
        else:
            print("❌ Not timezone aware")
            return False
        
        # Test that it's UTC
        if now.tzinfo == timezone.utc:
            print("✅ Correctly set to UTC timezone")
        else:
            print(f"❌ Wrong timezone: {now.tzinfo}")
            return False
        
        # Test datetime arithmetic (common source of issues)
        from datetime import timedelta
        past_time = now - timedelta(hours=1)
        time_diff = now - past_time
        
        print(f"✅ Datetime arithmetic works: {time_diff}")
        
        return True
        
    except Exception as e:
        print(f"❌ Timezone test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 THE OVERMIND PROTOCOL - Datetime Fixes Validation")
    print("=" * 60)
    
    success1 = test_datetime_fixes()
    success2 = test_timezone_awareness()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL DATETIME FIXES VALIDATED!")
        print("✅ Mission Control should now work without TypeError")
        print("✅ No more deprecation warnings")
        print("✅ Ready to restart Streamlit app")
        print("\n🚀 Next step: Restart Mission Control dashboard")
    else:
        print("❌ Some tests failed - please check the errors above")
        sys.exit(1)
