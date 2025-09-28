#!/usr/bin/env python3
"""
LiveKit Worker for the Voice AI Agent
This script runs the LiveKit worker that handles room connections and agent sessions.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

print("Starting LiveKit worker...")
print("Environment variables loaded:")
print(f"LIVEKIT_API_KEY: {'set' if os.getenv('LIVEKIT_API_KEY') else 'not set'}")
print(f"GOOGLE_API_KEY: {'set' if os.getenv('GOOGLE_API_KEY') else 'not set'}")
print(f"DEEPGRAM_API_KEY: {'set' if os.getenv('DEEPGRAM_API_KEY') else 'not set'}")
print(f"CARTESIA_API_KEY: {'set' if os.getenv('CARTESIA_API_KEY') else 'not set'}")

# Check if required environment variables are set
required_vars = ['LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET', 'LIVEKIT_URL', 'GOOGLE_API_KEY', 'DEEPGRAM_API_KEY', 'CARTESIA_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"WARNING: Missing required environment variables: {missing_vars}")
    print("Please set these variables in your .env file")
else:
    print("All required environment variables are set")

from livekit import agents
print("Imported livekit agents")

try:
    from agent.enhanced_agent import enhanced_entrypoint
    print("Imported enhanced_entrypoint")
except Exception as e:
    print(f"Error importing enhanced_entrypoint: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    print("Running LiveKit worker with enhanced agent")
    try:
        # Run the LiveKit worker with the enhanced agent
        agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=enhanced_entrypoint))
    except Exception as e:
        print(f"Error running LiveKit worker: {e}")
        import traceback
        traceback.print_exc()