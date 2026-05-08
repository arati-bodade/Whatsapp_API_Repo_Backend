#!/usr/bin/env python3
"""
Analyze the actual filename format to fix the regex
"""

import re

def analyze_filename():
    """Analyze the filename format"""
    
    print("=== Analyzing Filename Format ===")
    
    filename = "trigger_33496d04-29aa-4770-a9f3-4c7294ed5746.jpg"
    
    print(f"Original filename: {filename}")
    print(f"Length: {len(filename)}")
    
    # Break down the filename
    if filename.startswith("trigger_"):
        uuid_part = filename[8:]  # Remove "trigger_"
        uuid_part = uuid_part.rsplit(".", 1)[0]  # Remove extension
        print(f"UUID part: {uuid_part}")
        print(f"UUID length: {len(uuid_part)}")
    
    # Test different patterns
    patterns = [
        r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-.*?[0-9a-f]{12}_',
        r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_',
        r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        r'^trigger_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        r'^trigger_.*?\.jpg$',
        r'^trigger_.*?_',
    ]
    
    print("\nTesting patterns:")
    for i, pattern in enumerate(patterns, 1):
        match = re.match(pattern, filename)
        if match:
            result = re.sub(pattern, '', filename)
            print(f"Pattern {i}: MATCH -> '{result}'")
        else:
            print(f"Pattern {i}: NO MATCH")
    
    # Test character by character
    print(f"\nCharacter analysis:")
    for i, char in enumerate(filename):
        if i < 50:  # Limit output
            print(f"  {i:2d}: '{char}'")

if __name__ == "__main__":
    analyze_filename()
