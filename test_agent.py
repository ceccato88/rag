#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# Add paths
sys.path.append('/workspaces/rag')
sys.path.append('/workspaces/rag/multi-agent-researcher')

print(f"🐍 Python version: {sys.version}")
print(f"📁 Current directory: {os.getcwd()}")
print()

try:
    print("🔍 Testing environment loading...")
    from dotenv import load_dotenv, find_dotenv
    
    env_file = find_dotenv()
    if env_file:
        load_dotenv(env_file)
        print(f"✅ Loaded .env from: {env_file}")
        print(f"🔑 OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
        print(f"🤖 MULTIAGENT_MODEL: {os.getenv('MULTIAGENT_MODEL')}")
    
    print("\n🔍 Testing OpenAI agent import...")
    # Change working directory to multi-agent-researcher
    os.chdir('/workspaces/rag/multi-agent-researcher')
    sys.path.insert(0, '/workspaces/rag/multi-agent-researcher')
    
    from src.researcher.agents.openai_lead import OpenAILeadResearcher, OpenAILeadConfig
    print("✅ OpenAI agent imported successfully")
    
    print("\n🔍 Testing config creation...")
    config = OpenAILeadConfig.from_env()
    print(f"✅ Config created: {config}")
    
    print("\n🔍 Testing agent creation...")
    agent = OpenAILeadResearcher(
        agent_id="test-agent",
        name="Test Agent",
        config=config
    )
    print("✅ Agent created successfully")
    print(f"Agent state: {agent.state}")
    print(f"Agent name: {agent.name}")
    print(f"Agent ID: {agent.agent_id}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
