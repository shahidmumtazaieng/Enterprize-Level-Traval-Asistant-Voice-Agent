from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import uuid
import json
from dotenv import load_dotenv
import asyncio

from livekit import api

from core.config import settings
from core.session_manager import SessionManager
from core.logger import setup_logger, log_session_event, log_error
from core.optimizer import get_optimizer
from schemas.session import SessionCreate, SessionResponse
from schemas.conversation import ConversationMessage

// Import WebSocket handling utilities
import base64

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logger("voice_ai_backend", level=settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else 20)

# Initialize FastAPI app
app = FastAPI(
    title="Enterprise Voice AI Conversational Agent",
    description="A professional voice AI agent using LiveKit with FastAPI backend",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  // In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

// Store active room connections
active_rooms: Dict[str, Dict] = {}

// Initialize session manager
session_manager = SessionManager()

// Initialize optimizer
optimizer = get_optimizer()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Enterprise Voice AI Conversational Agent API"}

@app.post("/sessions", response_model=SessionResponse)
async def create_session(session_data: SessionCreate):
    """
    Create a new conversation session
    
    Args:
        session_data: Session creation parameters
        
    Returns:
        SessionResponse: Created session information
    """
    start_time = optimizer.record_request_start("create_session")
    try:
        session_id = str(uuid.uuid4())
        log_session_event(logger, session_id, "session_creation_started", "Creating new session")
        
        session_info = await session_manager.create_session(
            session_id=session_id,
            system_prompt=session_data.system_prompt,
            agent_name=session_data.agent_name
        )
        
        // Generate LiveKit token for the session
        try:
            // Create a unique room name for this session
            room_name = f"travel-session-{session_id[:8]}"
            
            // Create access token for the user
            user_identity = f"user-{session_id}"
            user_token = api.AccessToken(
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET
            ).with_identity(user_identity).with_name("Web User").with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True
                )
            ).to_jwt()
            
            // Create access token for the agent
            agent_identity = f"agent-{session_id}"
            agent_token = api.AccessToken(
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET
            ).with_identity(agent_identity).with_name("Travel Assistant").with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                    can_publish_data=True
                )
            ).to_jwt()
            
            // Update session info with LiveKit details
            session_info["livekit_room"] = room_name
            session_info["livekit_user_token"] = user_token
            session_info["livekit_agent_token"] = agent_token
            
            // Store room info for WebSocket connection
            active_rooms[session_id] = {
                "room_name": room_name,
                "user_identity": user_identity,
                "agent_identity": agent_identity
            }
            
        except Exception as token_error:
            log_error(logger, session_id, "token_generation_failed", "Failed to generate LiveKit tokens", token_error)
            // Continue without tokens - session can still be created
        
        log_session_event(logger, session_id, "session_created", "Session created successfully")
        
        optimizer.record_request_end("create_session", start_time, success=True)
        
        return SessionResponse(
            session_id=session_id,
            **session_info
        )
    except Exception as e:
        optimizer.record_request_end("create_session", start_time, success=False)
        log_error(logger, "unknown", "session_creation_failed", "Failed to create session", e)
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get session information
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        dict: Session information
    """
    log_session_event(logger, session_id, "session_retrieval", "Retrieving session information")
    session = session_manager.get_session(session_id)
    if not session:
        log_error(logger, session_id, "session_not_found", "Session not found")
        raise HTTPException(status_code=404, detail="Session not found")
    log_session_event(logger, session_id, "session_retrieved", "Session information retrieved")
    return session

@app.delete("/sessions/{session_id}")
async def end_session(session_id: str):
    """
    End a conversation session
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        dict: Success message
    """
    try:
        log_session_event(logger, session_id, "session_ending", "Ending session")
        await session_manager.end_session(session_id)
        
        // Clean up active room info
        if session_id in active_rooms:
            del active_rooms[session_id]
            
        log_session_event(logger, session_id, "session_ended", "Session ended successfully")
        return {"message": f"Session {session_id} ended successfully"}
    except Exception as e:
        log_error(logger, session_id, "session_ending_failed", "Failed to end session", e)
        raise HTTPException(status_code=500, detail=f"Failed to end session: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice communication
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
    """
    try:
        log_session_event(logger, session_id, "websocket_connection", "WebSocket connection attempt")
        
        // Accept the WebSocket connection
        await websocket.accept()
        
        // Check if session exists
        session = session_manager.get_session(session_id)
        if not session:
            log_error(logger, session_id, "session_not_found", "Session not found during WebSocket connection")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Session not found"
            }))
            await websocket.close()
            return
        
        // Check if room info exists
        if session_id not in active_rooms:
            log_error(logger, session_id, "room_not_found", "Room info not found for session")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Room configuration not found"
            }))
            await websocket.close()
            return
        
        room_info = active_rooms[session_id]
        room_name = room_info["room_name"]
        
        log_session_event(logger, session_id, "websocket_connected", "WebSocket connection established")
        
        // Register WebSocket connection with session manager
        await session_manager.register_websocket(session_id, websocket)
        
        // Start the session with the LiveKit agent
        await session_manager.start_session(session_id)
        
        // Send connection confirmation to frontend with room info
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to voice service",
            "room_name": room_name,
            "room_info": room_info
        }))
        
        // Listen for messages
        while True:
            // Receive either text or bytes
            try:
                // Try to receive as text first
                data = await websocket.receive_text()
                message = json.loads(data)
                
                log_session_event(logger, session_id, "message_received", "Message received via WebSocket", {"message_type": message.get("type")})
                
                // Process different message types
                if message["type"] == "audio":
                    // Handle audio data
                    await session_manager.process_audio(session_id, message["data"])
                elif message["type"] == "text":
                    // Handle text input (for testing)
                    await session_manager.process_text(session_id, message["text"])
                elif message["type"] == "control":
                    // Handle control messages
                    if message["action"] == "start":
                        // Send listening started message to frontend
                        await websocket.send_text(json.dumps({
                            "type": "listening_started",
                            "message": "Listening started"
                        }))
                        await session_manager.start_session(session_id)
                    elif message["action"] == "stop":
                        // Send listening stopped message to frontend
                        await websocket.send_text(json.dumps({
                            "type": "listening_stopped",
                            "message": "Listening stopped"
                        }))
                        await session_manager.stop_session(session_id)
            except:
                // If text fails, try to receive as bytes (audio data)
                try:
                    audio_data = await websocket.receive_bytes()
                    log_session_event(logger, session_id, "audio_received", "Audio data received via WebSocket", {"audio_size": len(audio_data)})
                    // Process audio data
                    await session_manager.process_audio(session_id, audio_data)
                except Exception as audio_error:
                    log_error(logger, session_id, "audio_receive_failed", "Failed to receive audio data", audio_error)
                    raise audio_error
                
    except Exception as e:
        log_error(logger, session_id, "websocket_error", "WebSocket error occurred", e)
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"WebSocket error: {str(e)}"
            }))
        except:
            pass
        await websocket.close()
    finally:
        // Clean up session on disconnect
        await session_manager.unregister_websocket(session_id)
        log_session_event(logger, session_id, "websocket_disconnected", "WebSocket connection closed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/token")
async def create_token():
    """
    Create a LiveKit token for connecting to a room
    """
    try:
        // Generate a unique identity for the participant
        identity = f"user-{uuid.uuid4()}"
        
        // Create access token with appropriate grants
        token = api.AccessToken(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET
        ).with_identity(identity).with_name("Web User").with_grants(
            api.VideoGrants(
                room_join=True,
                room="travel-assistant-room",  // Default room name
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True
            )
        ).to_jwt()
        
        return {"token": token, "identity": identity}
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate token: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )