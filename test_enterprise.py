#!/usr/bin/env python3
"""
Test script for the Enterprise Voice AI solution
"""
import asyncio
import aiohttp
import json
import websockets
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnterpriseVoiceAITest:
    """Test client for the Enterprise Voice AI solution"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.session_id = None
        self.websocket = None
        
    async def create_session(self):
        """Create a new conversation session"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "system_prompt": "You are a helpful AI assistant for testing purposes.",
                    "agent_name": "TestAssistant"
                }
                
                async with session.post(
                    f"{self.backend_url}/sessions",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.session_id = data["session_id"]
                        logger.info(f"Session created successfully: {self.session_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create session: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            return False
    
    async def get_session_info(self):
        """Get session information"""
        if not self.session_id:
            logger.error("No session ID available")
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/sessions/{self.session_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Session info: {data}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get session info: {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Error getting session info: {str(e)}")
            return None
    
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        if not self.session_id:
            logger.error("No session ID available")
            return False
            
        try:
            # Connect to WebSocket
            ws_url = f"ws://localhost:8000/ws/{self.session_id}"
            self.websocket = await websockets.connect(ws_url)
            logger.info("WebSocket connection established")
            
            # Send a test message
            test_message = {
                "type": "text",
                "text": "Hello, this is a test message"
            }
            await self.websocket.send(json.dumps(test_message))
            logger.info("Test message sent")
            
            # Wait for response (timeout after 10 seconds)
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                logger.info(f"Received response: {response}")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return False
                
        except Exception as e:
            logger.error(f"WebSocket test failed: {str(e)}")
            return False
        finally:
            if self.websocket:
                await self.websocket.close()
                logger.info("WebSocket connection closed")
    
    async def end_session(self):
        """End the conversation session"""
        if not self.session_id:
            logger.error("No session ID available")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.backend_url}/sessions/{self.session_id}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Session ended: {data}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to end session: {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            return False
    
    async def run_comprehensive_test(self):
        """Run a comprehensive test of the enterprise solution"""
        logger.info("Starting comprehensive test of Enterprise Voice AI solution")
        
        start_time = time.time()
        
        # Test 1: Create session
        logger.info("Test 1: Creating session")
        if not await self.create_session():
            logger.error("Test 1 failed: Could not create session")
            return False
        
        # Test 2: Get session info
        logger.info("Test 2: Getting session info")
        session_info = await self.get_session_info()
        if not session_info:
            logger.error("Test 2 failed: Could not get session info")
            return False
        
        # Test 3: WebSocket connection
        logger.info("Test 3: Testing WebSocket connection")
        if not await self.test_websocket_connection():
            logger.error("Test 3 failed: WebSocket test failed")
            return False
        
        # Test 4: End session
        logger.info("Test 4: Ending session")
        if not await self.end_session():
            logger.error("Test 4 failed: Could not end session")
            return False
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"All tests completed successfully in {total_time:.2f} seconds")
        return True

async def main():
    """Main test function"""
    tester = EnterpriseVoiceAITest()
    
    try:
        success = await tester.run_comprehensive_test()
        if success:
            logger.info("🎉 All tests passed! Enterprise Voice AI solution is working correctly.")
        else:
            logger.error("❌ Some tests failed. Please check the logs above.")
    except Exception as e:
        logger.error(f"Test suite failed with exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())