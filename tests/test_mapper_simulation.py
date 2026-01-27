
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import keyboard_mapper
from keyboard_mapper import KEY_MAP

# Mock write_report
sent_reports = []

def mock_write_report(report):
    # Only capture key down events (non-zero reports)
    # Report is bytearray, check if any byte in it is non-zero
    if any(report):
        sent_reports.append(report)

keyboard_mapper.write_report = mock_write_report

# Reverse map for verification
REVERSE_MAP = {v: k for k, v in KEY_MAP.items()}
# Handle duplicates in reverse map (e.g. if any) - strictly speaking we want to look up (mod, code)
REVERSE_MAP_TUPLE = {v: k for k, v in KEY_MAP.items()}

def decode_report(report):
    mod = report[0]
    code = report[2]
    
    # Check if we have a mapping for this
    if (mod, code) in REVERSE_MAP_TUPLE:
        return REVERSE_MAP_TUPLE[(mod, code)]
    return f"UNKNOWN({mod}, {code:02x})"

def test_string(text):
    global sent_reports
    sent_reports = []
    
    print(f"Testing string: '{text}'")
    keyboard_mapper.type_string(text)
    
    decoded_str = ""
    for report in sent_reports:
        decoded_str += decode_report(report)
        
    print(f"Decoded:      '{decoded_str}'")
    
    if text == decoded_str:
        print("MATCH")
    else:
        print("MISMATCH")
        # Find differences
        for i, (a, b) in enumerate(zip(text, decoded_str)):
            if a != b:
                print(f"  Diff at index {i}: Expected '{a}' (ord {ord(a)}), Got '{b}' (ord {ord(b)})")
        if len(decoded_str) < len(text):
             print(f"  Missing characters starting at index {len(decoded_str)}: '{text[len(decoded_str):]}'")

if __name__ == "__main__":
    # Test 1: Basic sentence with comma
    test_string("Hello, World!")
    
    # Test 2: Standard Punctuation
    test_string(".,!?;:'\"-=_+[]{}|/<>\\")
    
    # Test 3: Numbers
    test_string("1234567890")
    
    # Test 4: Newlines and Tabs
    test_string("\n\t ")

    # Test 5: Potential problematic example
    test_string("This is a sentence, with a clause.")

    # Test 6: Smart Punctuation (Simulating LLM output)
    test_string("Hello, “World”! It’s me—the AI.")

