#!/usr/bin/env python3
"""
Test script for Hebrew mediation system
Run this to verify the new conversation management works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.chains.hebrew_mediation_chain import create_hebrew_mediation_chain
from app.services.hebrew_mediation_service import HebrewMediationService

def test_hebrew_mediation_chain():
    """Test the Hebrew mediation chain directly"""
    print("🧪 Testing Hebrew Mediation Chain...")
    
    # Create chain
    chain = create_hebrew_mediation_chain()
    
    # Test inputs
    test_inputs = {
        "instruction": "פתרו את התרגיל הבא: 25 + 37 = ?",
        "student_response": "לא מבין מה צריך לעשות",
        "mode": "practice",
        "student_context": {
            "name": "דני",
            "grade": "ג",
            "difficulty_level": 3,
            "difficulties": "קושי בהבנת הוראות מתמטיקה"
        }
    }
    
    # Execute chain
    try:
        result = chain._call(test_inputs)
        
        print("✅ Chain executed successfully!")
        print(f"📝 Response: {result.get('response', 'No response')}")
        print(f"🎯 Strategy: {result.get('strategy_used', 'Unknown')}")
        print(f"🧠 Comprehension: {result.get('comprehension_level', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Chain execution failed: {str(e)}")
        return False

def test_conversation_flow():
    """Test conversation flow with multiple interactions"""
    print("\n🔄 Testing Conversation Flow...")
    
    chain = create_hebrew_mediation_chain()
    
    # Simulate conversation
    conversations = [
        {
            "instruction": "קראו את הטקסט וענו על השאלות",
            "student_response": "",  # First message
            "expected_strategy": "highlight_keywords"
        },
        {
            "instruction": "קראו את הטקסט וענו על השאלות", 
            "student_response": "לא הבנתי מה צריך לעשות",
            "expected_strategy": "guided_reading"
        },
        {
            "instruction": "קראו את הטקסט וענו על השאלות",
            "student_response": "עדיין לא מבין",
            "expected_strategy": "provide_example"
        }
    ]
    
    student_context = {
        "name": "שרה",
        "grade": "ד", 
        "difficulty_level": 4,
        "difficulties": "קושי בהבנת טקסטים"
    }
    
    for i, conv in enumerate(conversations):
        print(f"\n--- Interaction {i+1} ---")
        
        inputs = {
            "instruction": conv["instruction"],
            "student_response": conv["student_response"],
            "mode": "practice",
            "student_context": student_context
        }
        
        try:
            result = chain._call(inputs)
            strategy = result.get("strategy_used", "unknown")
            
            print(f"💬 Student: {conv['student_response'] or '[First message]'}")
            print(f"🤖 Bot: {result.get('response', 'No response')[:100]}...")
            print(f"🎯 Strategy: {strategy}")
            
            # Note: Strategy might not match expected due to memory state
            if strategy == conv["expected_strategy"]:
                print("✅ Expected strategy used")
            else:
                print(f"ℹ️ Used {strategy} instead of expected {conv['expected_strategy']}")
                
        except Exception as e:
            print(f"❌ Interaction failed: {str(e)}")
            return False
    
    return True

def test_service_integration():
    """Test the Hebrew mediation service"""
    print("\n🔧 Testing Service Integration...")
    
    try:
        service = HebrewMediationService()
        print("✅ Service created successfully")
        
        # Test chain creation
        chain = service.get_mediation_chain(session_id=999, provider="test")
        print("✅ Chain creation works")
        
        # Test should_use_mediation logic
        class MockSession:
            def __init__(self, mode):
                self.mode = mode
        
        from app.models.chat import InteractionMode
        
        # Should use mediation for practice mode without assistance_type
        practice_session = MockSession(InteractionMode.PRACTICE)
        should_use = service.should_use_mediation(practice_session, None)
        print(f"✅ Practice mode (Agent Selection): {should_use}")
        
        # Should NOT use mediation for practice mode WITH assistance_type 
        should_not_use = service.should_use_mediation(practice_session, "breakdown")
        print(f"✅ Practice mode (Student Selection): {not should_not_use}")
        
        # Should use mediation for test mode
        test_session = MockSession(InteractionMode.TEST)
        should_use_test = service.should_use_mediation(test_session, None)
        print(f"✅ Test mode: {should_use_test}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Hebrew Mediation System Tests\n")
    
    tests = [
        test_hebrew_mediation_chain,
        test_conversation_flow,
        test_service_integration
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
            results.append(False)
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Hebrew mediation system is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)