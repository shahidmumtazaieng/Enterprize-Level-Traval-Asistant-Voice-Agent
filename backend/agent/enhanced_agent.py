import os
import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import json

from livekit import agents
from livekit.agents import AgentSession, Agent, JobContext, RoomInputOptions, RoomOutputOptions
from livekit.plugins import (
    google,
    cartesia,
    deepgram,
    silero,
    anam,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.llm import ChatMessage, ChatContext
from PIL import Image

# Configure logging
try:
    from core.logger import setup_logger, log_session_event, log_error
    from core.optimizer import get_optimizer
    logger = setup_logger("voice_agent", level=logging.INFO)
    optimizer = get_optimizer()
    print("Successfully imported core modules")
except Exception as e:
    print(f"Error importing core modules: {e}")
    # Fallback to basic logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("voice_agent")
    def log_session_event(*args, **kwargs):
        pass
    def log_error(*args, **kwargs):
        pass
    class MockOptimizer:
        def record_request_start(self, *args):
            return None
        def record_request_end(self, *args, **kwargs):
            pass
    optimizer = MockOptimizer()

print("Enhanced agent module loaded")

@dataclass
class AgentConfig:
    """Configuration for the enhanced voice agent"""
    system_prompt: str = "You are a friendly travel assistant."
    stt_model: str = "nova-3"
    llm_model: str = "gemini-1.5-flash"
    tts_model: str = "sonic-2"
    tts_voice: str = "f786b574-daa5-4673-aa0c-cbe3e8534c02"
    language: str = "multi"
    temperature: float = 0.7
    max_tokens: int = 1000

class EnhancedVoiceAgent(Agent):
    """Enhanced voice agent with sophisticated turn-taking logic and error handling"""
    
    def __init__(self, config: AgentConfig) -> None:
        super().__init__(
            instructions=config.system_prompt,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        self.config = config
        self.is_speaking = False
        self.is_listening = False
        self.turn_active = False
        self.session_id = None
        self.conversation_history = []
        
        # Set up event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Set up event handlers for the agent"""
        pass  # Event handlers are set up in the session

    async def on_turn_started(self):
        """Called when a turn starts"""
        self.turn_active = True
        logger.info(f"Agent turn started for session {self.session_id}")
        
    async def on_turn_ended(self):
        """Called when a turn ends"""
        self.turn_active = False
        logger.info(f"Agent turn ended for session {self.session_id}")
        
    async def on_speaking_started(self):
        """Called when agent starts speaking"""
        self.is_speaking = True
        logger.info(f"Agent started speaking for session {self.session_id}")
        
    async def on_speaking_ended(self):
        """Called when agent stops speaking"""
        self.is_speaking = False
        logger.info(f"Agent stopped speaking for session {self.session_id}")
        
    async def on_user_speaking_started(self):
        """Called when user starts speaking"""
        self.is_listening = True
        logger.info(f"User started speaking for session {self.session_id}")
        
    async def on_user_speaking_ended(self):
        """Called when user stops speaking"""
        self.is_listening = False
        logger.info(f"User stopped speaking for session {self.session_id}")

async def create_enhanced_agent_session(
    config: AgentConfig,
    session_id: str = None
) -> AgentSession:
    """
    Create an enhanced LiveKit agent session with proper turn-taking logic
    
    Args:
        config: Agent configuration
        session_id: Optional session identifier
        
    Returns:
        AgentSession: Configured agent session
    """
    logger.info(f"Creating enhanced agent session {session_id}")
    
    # Create the agent session with all components
    # Optimize for low latency by using appropriate settings
    session = AgentSession(
        stt=deepgram.STT(
            model=config.stt_model,
            language=config.language,
            # Lower latency settings
            endpointing=200,  # ms
            sample_rate=16000,
            num_channels=1
        ),
        llm=google.LLM(
            model=config.llm_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            # Optimize for speed
            timeout=30.0  # seconds
        ),
        tts=cartesia.TTS(
            model=config.tts_model,
            voice=config.tts_voice,
            # Optimize for low latency
            speed=1.1,  # Slightly faster than normal
            latency_optimizations=True
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        # Add session-level timeout settings
        timeout=45.0  # Overall session timeout
    )
    
    return session

async def run_enhanced_agent_session(
    ctx: JobContext,
    config: AgentConfig,
    session_id: str = None
) -> None:
    """
    Run the enhanced agent session with proper error handling and turn-taking logic
    
    Args:
        ctx: Job context from LiveKit
        config: Agent configuration
        session_id: Optional session identifier
    """
    session = None
    avatar = None
    try:
        log_session_event(logger, session_id or "unknown", "agent_session_starting", "Starting enhanced agent session")
        
        # Create agent session
        session = await create_enhanced_agent_session(config, session_id)
        
        # Create voice agent
        agent = EnhancedVoiceAgent(config)
        agent.session_id = session_id
        
        # Set up avatar if avatar image path is provided
        avatar_image_path = os.getenv("AVATAR_IMAGE_PATH")
        if avatar_image_path and os.path.exists(avatar_image_path):
            try:
                # For anam, we need to configure persona instead of using image directly
                avatar = anam.AvatarSession(
                    persona_config=anam.PersonaConfig(
                        name="Mia",  # Name of the avatar to use.
                        avatarId="dd861b5f-b674-4488-a15f-a602d81acb9f",  # ID of the avatar to use. See "Avatar setup" for details.
                    ),
                )
                # Start avatar with timeout
                try:
                    await asyncio.wait_for(
                        avatar.start(session, room=ctx.room),
                        timeout=10.0  # 10 second timeout for avatar start
                    )
                    log_session_event(logger, session_id or "unknown", "avatar_started", "Avatar session started successfully")
                except asyncio.TimeoutError:
                    log_error(logger, session_id or "unknown", "avatar_start_timeout", "Avatar start timed out", None)
                    # Clean up avatar session
                    if avatar:
                        try:
                            await avatar.close()
                        except:
                            pass
                    avatar = None  # Disable avatar if it fails to start
                except Exception as e:
                    log_error(logger, session_id or "unknown", "avatar_start_failed", "Failed to start avatar session", e)
                    # Clean up avatar session
                    if avatar:
                        try:
                            await avatar.close()
                        except:
                            pass
                    avatar = None  # Disable avatar if it fails to start
            except Exception as e:
                log_error(logger, session_id or "unknown", "avatar_setup_failed", "Failed to set up avatar session", e)
                avatar = None  # Disable avatar if setup fails
        else:
            log_session_event(logger, session_id or "unknown", "avatar_not_configured", "Avatar not configured or image not found")
        
        # Set up room options
        room_input_options = RoomInputOptions(
            close_on_disconnect=False,
        )
        
        # If avatar is enabled, audio is handled by avatar
        room_output_options = RoomOutputOptions(
            audio_enabled=avatar is None,  # Avatar handles audio if present
        )
        
        # Set up event handlers
        def on_agent_speaking_started():
            asyncio.create_task(agent.on_speaking_started())
            
        def on_agent_speaking_ended():
            asyncio.create_task(agent.on_speaking_ended())
            
        def on_user_speaking_started():
            asyncio.create_task(agent.on_user_speaking_started())
            
        def on_user_speaking_ended():
            asyncio.create_task(agent.on_user_speaking_ended())
        
        # Register event handlers
        session.on("agent_speaking_started", on_agent_speaking_started)
        session.on("agent_speaking_ended", on_agent_speaking_ended)
        session.on("user_speaking_started", on_user_speaking_started)
        session.on("user_speaking_ended", on_user_speaking_ended)
        
        # Start the session with explicit timeout handling
        try:
            await asyncio.wait_for(
                session.start(
                    room=ctx.room,
                    agent=agent,
                    room_input_options=room_input_options,
                    room_output_options=room_output_options,
                ),
                timeout=30.0  # 30 second timeout for connection
            )
            log_session_event(logger, session_id or "unknown", "agent_session_started", "Agent session started successfully")
        except asyncio.TimeoutError:
            log_error(logger, session_id or "unknown", "agent_session_timeout", "Agent session start timed out", None)
            raise Exception("Agent session failed to start within timeout period")
        
        # Generate initial greeting with timeout
        try:
            await asyncio.wait_for(
                session.generate_reply(
                    instructions=f"Greet the user with a friendly welcome message. {config.system_prompt}"
                ),
                timeout=15.0  # 15 second timeout for initial greeting
            )
            log_session_event(logger, session_id or "unknown", "initial_greeting_sent", "Initial greeting sent")
        except asyncio.TimeoutError:
            log_error(logger, session_id or "unknown", "greeting_timeout", "Initial greeting timed out", None)
            raise Exception("Failed to generate initial greeting within timeout period")
        
        # Keep the session alive
        await session.wait_for_completion()
        
    except Exception as e:
        log_error(logger, session_id or "unknown", "agent_session_failed", "Error in enhanced agent session", e)
        # Send error message to client if possible
        if session:
            try:
                await session.generate_reply(
                    instructions=f"An error occurred: {str(e)}. Please try again."
                )
            except Exception as reply_error:
                log_error(logger, session_id or "unknown", "error_reply_failed", "Failed to send error reply to client", reply_error)
        raise
    finally:
        if session:
            try:
                await session.disconnect()
                log_session_event(logger, session_id or "unknown", "agent_session_disconnected", "Disconnected enhanced agent session")
            except Exception as e:
                log_error(logger, session_id or "unknown", "agent_session_disconnect_failed", "Error disconnecting enhanced agent session", e)
        if avatar:
            try:
                await avatar.close()
                log_session_event(logger, session_id or "unknown", "avatar_stopped", "Avatar session stopped successfully")
            except Exception as e:
                log_error(logger, session_id or "unknown", "avatar_stop_failed", "Error stopping avatar session", e)

async def enhanced_entrypoint(ctx: JobContext):
    """
    Enhanced entrypoint for the LiveKit agent
    
    Args:
        ctx: Job context from LiveKit
    """
    session_id = None
    try:
        print("Enhanced entrypoint called")
        log_session_event(logger, "unknown", "agent_entrypoint_started", "Agent entrypoint called")
        
        # Get configuration from environment variables
        print("Loading configuration from environment variables...")
        config = AgentConfig(
            system_prompt=os.getenv("SYSTEM_PROMPT", "You are a friendly travel assistant."),
            stt_model=os.getenv("STT_MODEL", "nova-3"),
            llm_model=os.getenv("LLM_MODEL", "gemini-1.5-flash"),
            tts_model=os.getenv("TTS_MODEL", "sonic-2"),
            tts_voice=os.getenv("TTS_VOICE", "f786b574-daa5-4673-aa0c-cbe3e8534c02"),
            language=os.getenv("LANGUAGE", "multi"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_TOKENS", "1000"))
        )
        print(f"Configuration loaded: {config}")
        
        # Get session ID from metadata if available
        if ctx.job and ctx.job.metadata:
            try:
                metadata = json.loads(ctx.job.metadata)
                session_id = metadata.get("session_id")
                print(f"Session ID extracted from metadata: {session_id}")
                log_session_event(logger, session_id or "unknown", "session_id_extracted", "Session ID extracted from metadata")
            except Exception as e:
                print(f"Failed to extract session ID from metadata: {e}")
                log_error(logger, "unknown", "session_id_extraction_failed", "Failed to extract session ID from metadata", e)
        
        print("Running enhanced agent session...")
        await run_enhanced_agent_session(ctx, config, session_id)
        print("Enhanced agent session completed")
        
    except Exception as e:
        print(f"Error in agent entrypoint: {e}")
        log_error(logger, session_id or "unknown", "agent_entrypoint_failed", "Error in agent entrypoint", e)
        raise

if __name__ == "__main__":
    # Run the enhanced LiveKit agent
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=enhanced_entrypoint))