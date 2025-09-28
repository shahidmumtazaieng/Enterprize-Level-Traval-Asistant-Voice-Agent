#!/usr/bin/env python3
"""
Direct test of the backend FastAPI application
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import the FastAPI app
try:
    from backend.main import app
    from fastapi.testclient import TestClient
    
    # Create a test client
    client = TestClient(app)
    
    def test_health():
        """Test the health endpoint"""
        print("Testing health endpoint...")
        response = client.get("/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    
    def test_session_creation():
        """Test session creation"""
        print("\nTesting session creation...")
        session_data = {
            "system_prompt": "You are a friendly travel assistant.",
            "agent_name": "TravelAssistant"
        }
        response = client.post("/sessions", json=session_data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Response: {response.text}")
            return False
    
    def test_get_session():
        """Test getting a session (this should fail since we don't have a real session ID)"""
        print("\nTesting get session (expected to fail)...")
        response = client.get("/sessions/nonexistent-session")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 404
    
    if __name__ == "__main__":
        print("=== Backend Direct Test ===")
        
        # Test health endpoint
        if test_health():
            print("✓ Health endpoint working")
        else:
            print("✗ Health endpoint failed")
        
        # Test session creation
        if test_session_creation():
            print("✓ Session creation working")
        else:
            print("✗ Session creation failed")
        
        # Test get session
        if test_get_session():
            print("✓ Get session correctly returns 404 for non-existent session")
        else:
            print("✗ Get session test failed")
        
        print("\n=== Backend Test Complete ===")
        
except Exception as e:
    print(f"Error importing backend: {e}")
    import traceback
    traceback.print_exc()