#!/usr/bin/env python3

import os
import sys
from pathlib import Path

print(f"🐍 Python version: {sys.version}")
print(f"📁 Current directory: {os.getcwd()}")
print(f"📂 Script location: {Path(__file__).absolute()}")
print()

try:
    print("🔍 Testing dotenv import...")
    from dotenv import load_dotenv, find_dotenv
    print("✅ dotenv imported successfully")
    
    print("\n🔍 Searching for .env file...")
    env_file = find_dotenv()
    print(f"📂 Found .env file: {env_file}")
    
    if env_file:
        print(f"\n📂 Loading .env from: {env_file}")
        result = load_dotenv(env_file)
        print(f"✅ Load result: {result}")
        
        # Test some key variables
        openai_key = os.getenv('OPENAI_API_KEY')
        model = os.getenv('MULTIAGENT_MODEL')
        
        print(f"\n🔑 OPENAI_API_KEY present: {bool(openai_key)}")
        if openai_key:
            print(f"🔑 OPENAI_API_KEY starts with: {openai_key[:10]}...")
        
        print(f"🤖 MULTIAGENT_MODEL: {model}")
        
    else:
        print("❌ No .env file found")
        
    print("\n✅ Test completed successfully")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
