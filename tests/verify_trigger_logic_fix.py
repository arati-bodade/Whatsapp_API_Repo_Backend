import logging
from unittest.mock import MagicMock

# Config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_trigger_match_logic():
    print("Testing Trigger Match Logic...")
    
    # Simulation inputs
    trigger_value = "Send"
    
    test_cases = [
        {"status": "Send", "expect": True},
        {"status": "send", "expect": True},
        {"status": "SEND ", "expect": True}, # Trailing space
        {"status": "Pending", "expect": False},
        {"status": "", "expect": False},
        {"status": "Sent", "expect": False}, # Already sent
    ]
    
    target_value = trigger_value.strip().lower()
    
    for case in test_cases:
        current_status = str(case["status"]).strip().lower()
        is_match = (current_status == target_value)
        
        result_icon = "✅" if is_match == case["expect"] else "❌"
        print(f"{result_icon} Status '{case['status']}' -> Match? {is_match} (Expected: {case['expect']})")
        
        if is_match != case["expect"]:
            print("   FAILED TEST CASE!")
            exit(1)

    print("\n✅ All trigger logic checks passed!")

if __name__ == "__main__":
    test_trigger_match_logic()
