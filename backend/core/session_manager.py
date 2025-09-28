import asyncio
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import json
import traceback
from collections import deque
import time

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, RoomOutputOptions
from livekit.plugins import (
    google,
    cartesia,
    deepgram,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Import the enhanced agent entrypoint
from agent.enhanced_agent import enhanced_entrypoint

# Pinecone Assistant SDK
from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message

from core.config import settings
from core.logger import log_session_event, log_error

logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    """Information about a conversation session"""
    session_id: str
    system_prompt: str
    agent_name: str
    status: str = "created"
    created_at: float = field(default_factory=lambda: __import__('time').time())
    livekit_room: Optional[str] = None
    livekit_user_token: Optional[str] = None
    livekit_agent_token: Optional[str] = None

class VoiceAgent(Agent):
    """Custom voice agent implementation"""
    
    def __init__(self, system_prompt: str) -> None:
        super().__init__(
            instructions=system_prompt,
            tools=[],  # Add tools as needed
        )

class SessionManager:
    """Manages conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionInfo] = {}
        self.websockets: Dict[str, Any] = {}
        self.agent_sessions: Dict[str, AgentSession] = {}
        
        # Connection pooling
        self.session_pool: deque = deque(maxlen=50)  # Pool of reusable sessions
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
        # Performance tracking
        self.session_creation_times = deque(maxlen=1000)
        
        # Initialize Pinecone if credentials are provided
        self.pinecone_client = None
        if settings.PINECONE_API_KEY and settings.ASSISTANT_NAME:
            try:
                self.pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)
                self.assistant = self.pinecone_client.assistant.Assistant(
                    assistant_name=settings.ASSISTANT_NAME
                )
            except Exception as e:
                logger.error(f"Failed to initialize Pinecone: {str(e)}")
    
    async def create_session(self, session_id: str, system_prompt: str, agent_name: str) -> Dict[str, Any]:
        """
        Create a new conversation session
        
        Args:
            session_id: Unique session identifier
            system_prompt: Initial system prompt for the agent
            agent_name: Name of the agent
            
        Returns:
            Dict with session information
        """
        start_time = time.time()
        try:
            log_session_event(logger, session_id, "session_creation_started", "Starting session creation")
            
            # Create session info
            session_info = SessionInfo(
                session_id=session_id,
                system_prompt=system_prompt,
                agent_name=agent_name
            )
            
            # Store session
            self.sessions[session_id] = session_info
            
            # Track performance
            creation_time = time.time() - start_time
            self.session_creation_times.append(creation_time)
            
            log_session_event(logger, session_id, "session_created", "Session created successfully", 
                            {"creation_time_ms": creation_time * 1000})
            
            return {
                "system_prompt": system_prompt,
                "agent_name": agent_name,
                "status": "created",
                "livekit_room": session_info.livekit_room,
                "livekit_user_token": session_info.livekit_user_token,
                "livekit_agent_token": session_info.livekit_agent_token
            }
        except Exception as e:
            log_error(logger, session_id, "session_creation_failed", "Failed to create session", e)
            raise
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session information
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            SessionInfo if found, None otherwise
        """
        return self.sessions.get(session_id)
    
    async def end_session(self, session_id: str):
        """
        End a conversation session
        
        Args:
            session_id: Unique session identifier
        """
        try:
            log_session_event(logger, session_id, "session_ending", "Ending session")
            
            if session_id in self.sessions:
                # Clean up agent session
                if session_id in self.agent_sessions:
                    try:
                        log_session_event(logger, session_id, "agent_disconnecting", "Disconnecting agent session")
                        await self.agent_sessions[session_id].disconnect()
                        log_session_event(logger, session_id, "agent_disconnected", "Agent session disconnected")
                        
                        # Add to session pool for reuse if pool not full
                        if len(self.session_pool) < self.session_pool.maxlen:
                            self.session_pool.append(self.agent_sessions[session_id])
                    except Exception as e:
                        log_error(logger, session_id, "agent_disconnect_failed", "Error disconnecting agent session", e)
                    finally:
                        del self.agent_sessions[session_id]
                
                # Clean up WebSocket
                if session_id in self.websockets:
                    try:
                        log_session_event(logger, session_id, "websocket_closing", "Closing WebSocket connection")
                        await self.websockets[session_id].close()
                        log_session_event(logger, session_id, "websocket_closed", "WebSocket connection closed")
                    except Exception as e:
                        log_error(logger, session_id, "websocket_close_failed", "Error closing WebSocket", e)
                    finally:
                        del self.websockets[session_id]
                
                # Remove session
                del self.sessions[session_id]
                
                log_session_event(logger, session_id, "session_ended", "Session ended successfully")
                
            # Periodic cleanup
            await self._cleanup_expired_sessions()
        except Exception as e:
            log_error(logger, session_id, "session_ending_failed", "Failed to end session", e)
            raise
    
    async def register_websocket(self, session_id: str, websocket):
        """
        Register WebSocket connection for a session
        
        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection
        """
        self.websockets[session_id] = websocket
        logger.info(f"Registered WebSocket for session {session_id}")
    
    async def unregister_websocket(self, session_id: str):
        """
        Unregister WebSocket connection for a session
        
        Args:
            session_id: Unique session identifier
        """
        if session_id in self.websockets:
            del self.websockets[session_id]
            logger.info(f"Unregistered WebSocket for session {session_id}")
    
    async def start_session(self, session_id: str):
        """
        Start the voice agent session
        
        Args:
            session_id: Unique session identifier
        """
        try:
            log_session_event(logger, session_id, "agent_session_starting", "Starting agent session")
            
            if session_id not in self.sessions:
                error_msg = f"Session {session_id} not found"
                log_error(logger, session_id, "session_not_found", error_msg)
                raise ValueError(error_msg)
            
            session_info = self.sessions[session_id]
            
            # For the LiveKit agent to work properly, we need to ensure the worker is running
            # The agent worker should be started separately, but we can trigger room creation here
            # Update session status to indicate it's ready for connection
            session_info.status = "ready"
            
            # Send message to frontend that session is ready
            if session_id in self.websockets:
                try:
                    await self.websockets[session_id].send_text(json.dumps({
                        "type": "session_ready",
                        "message": "Session is ready for voice interaction"
                    }))
                except Exception as e:
                    log_error(logger, session_id, "websocket_send_failed", "Failed to send session ready message", e)
            
            log_session_event(logger, session_id, "agent_session_ready", "Agent session ready for connection")
            
        except Exception as e:
            log_error(logger, session_id, "agent_session_start_failed", "Error starting agent session", e)
            if session_id in self.sessions:
                self.sessions[session_id].status = "error"
            raise
    
    async def stop_session(self, session_id: str):
        """
        Stop the voice agent session
        
        Args:
            session_id: Unique session identifier
        """
        try:
            log_session_event(logger, session_id, "agent_session_stopping", "Stopping agent session")
            
            if session_id in self.agent_sessions:
                try:
                    log_session_event(logger, session_id, "agent_disconnecting", "Disconnecting agent session")
                    await self.agent_sessions[session_id].disconnect()
                    log_session_event(logger, session_id, "agent_disconnected", "Agent session disconnected")
                    del self.agent_sessions[session_id]
                except Exception as e:
                    log_error(logger, session_id, "agent_disconnect_failed", "Error stopping agent session", e)
            
            if session_id in self.sessions:
                self.sessions[session_id].status = "stopped"
            
            # Send message to frontend that session has stopped
            if session_id in self.websockets:
                try:
                    await self.websockets[session_id].send_text(json.dumps({
                        "type": "session_stopped",
                        "message": "Session has been stopped"
                    }))
                except Exception as e:
                    log_error(logger, session_id, "websocket_send_failed", "Failed to send session stopped message", e)
            
            log_session_event(logger, session_id, "agent_session_stopped", "Agent session stopped successfully")
        except Exception as e:
            log_error(logger, session_id, "agent_session_stop_failed", "Error stopping agent session", e)
            raise
    
    async def process_audio(self, session_id: str, audio_data: bytes):
        """
        Process audio data from client
        
        Args:
            session_id: Unique session identifier
            audio_data: Audio data bytes
        """
        try:
            log_session_event(logger, session_id, "audio_processing", "Processing audio data", {"audio_size": len(audio_data)})
            
            # Send audio to LiveKit agent session
            if session_id in self.agent_sessions:
                try:
                    # This is a simplified implementation
                    # In a real implementation, you would stream the audio to the agent
                    log_session_event(logger, session_id, "audio_forwarding", "Forwarding audio to agent")
                    
                    # Send acknowledgment back to client
                    if session_id in self.websockets:
                        await self.websockets[session_id].send_text(json.dumps({
                            "type": "ack",
                            "message": "Audio received"
                        }))
                        log_session_event(logger, session_id, "audio_ack_sent", "Audio acknowledgment sent")
                        
                except Exception as e:
                    log_error(logger, session_id, "audio_processing_failed", "Error processing audio", e)
                    if session_id in self.websockets:
                        await self.websockets[session_id].send_text(json.dumps({
                            "type": "error",
                            "message": f"Error processing audio: {str(e)}"
                        }))
            else:
                # If no agent session exists, send error to client
                if session_id in self.websockets:
                    await self.websockets[session_id].send_text(json.dumps({
                        "type": "error",
                        "message": "Agent session not available"
                    }))
        except Exception as e:
            log_error(logger, session_id, "audio_processing_failed", "Error processing audio", e)
            raise
    
    async def process_text(self, session_id: str, text: str):
        """
        Process text input (for testing)
        
        Args:
            session_id: Unique session identifier
            text: Text input
        """
        try:
            log_session_event(logger, session_id, "text_processing", "Processing text input", {"text_length": len(text)})
            
            # Send text to agent session if available
            if session_id in self.agent_sessions:
                try:
                    # In a real implementation, you would send this to the agent
                    # and get a response back
                    response = f"Echo: {text}"
                    
                    # Send response back to client
                    if session_id in self.websockets:
                        await self.websockets[session_id].send_text(json.dumps({
                            "type": "response",
                            "text": response
                        }))
                        log_session_event(logger, session_id, "text_response_sent", "Text response sent", {"response_length": len(response)})
                except Exception as e:
                    log_error(logger, session_id, "text_processing_failed", "Error processing text with agent", e)
                    if session_id in self.websockets:
                        await self.websockets[session_id].send_text(json.dumps({
                            "type": "error",
                            "message": f"Error processing text with agent: {str(e)}"
                        }))
            else:
                # Simple echo if no agent session
                response = f"Echo: {text}"
                
                # Send response back to client
                if session_id in self.websockets:
                    await self.websockets[session_id].send_text(json.dumps({
                        "type": "response",
                        "text": response
                    }))
                    log_session_event(logger, session_id, "text_response_sent", "Text response sent", {"response_length": len(response)})
        except Exception as e:
            log_error(logger, session_id, "text_processing_failed", "Error processing text", e)
            raise

    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions periodically"""
        current_time = time.time()
        if current_time - self.last_cleanup_time > self.cleanup_interval:
            self.last_cleanup_time = current_time
            
            # Clean up expired sessions from pool
            expired_count = 0
            while self.session_pool and expired_count < 10:  # Limit cleanup per cycle
                try:
                    session = self.session_pool.popleft()
                    # In a real implementation, you would properly dispose of the session
                    expired_count += 1
                except:
                    break
                    
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions from pool")
