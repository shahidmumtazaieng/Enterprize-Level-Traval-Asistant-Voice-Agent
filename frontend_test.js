// Simple test to verify frontend components are working
console.log('Testing frontend components...');

// Test that the environment variables are loaded correctly
console.log('API URL:', import.meta.env.VITE_API_URL);
console.log('LiveKit URL:', import.meta.env.VITE_LIVEKIT_URL);

// Test WebSocket connection
const testWebSocketConnection = async () => {
  try {
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    console.log('Testing connection to:', API_URL);
    
    // Test health endpoint
    const healthResponse = await fetch(`${API_URL}/health`);
    console.log('Health endpoint status:', healthResponse.status);
    
    if (healthResponse.ok) {
      const healthData = await healthResponse.json();
      console.log('Health endpoint response:', healthData);
    }
    
    // Test session creation
    const sessionResponse = await fetch(`${API_URL}/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        system_prompt: "Test assistant",
        agent_name: "TestAssistant"
      })
    });
    
    console.log('Session creation status:', sessionResponse.status);
    
    if (sessionResponse.ok) {
      const sessionData = await sessionResponse.json();
      console.log('Session created:', sessionData.session_id);
      
      // Test WebSocket connection
      const wsUrl = `${API_URL.replace('http', 'ws')}/ws/${sessionData.session_id}`;
      console.log('WebSocket URL:', wsUrl);
      
      // Try to connect to WebSocket (but don't keep it open)
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected successfully');
        ws.close(); // Close immediately after testing
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      // Set a timeout to close the test
      setTimeout(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      }, 5000);
      
    } else {
      console.error('Session creation failed');
    }
  } catch (error) {
    console.error('Test failed:', error);
  }
};

// Run the test
testWebSocketConnection();