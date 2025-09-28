# Enterprise Voice AI Conversational Agent with Custom UI Integration

An enterprise-grade voice AI conversational agent built with LiveKit, FastAPI, and React. This solution provides real-time, natural voice conversations with an AI assistant, suitable for customer support, virtual assistants, and other enterprise applications. It has been enhanced with custom UI components for a travel assistant application.

## Features

### 🎤 Voice-First Experience
- Real-time speech-to-text (STT) with Deepgram
- Natural language processing with Google Gemini
- High-quality text-to-speech (TTS) with Cartesia
- Advanced voice activity detection (VAD) with Silero
- Multilingual turn detection

### ⚡ Enterprise Performance
- Low-latency architecture optimized for real-time conversations
- Connection pooling for efficient resource utilization
- Performance monitoring and metrics tracking
- Scalable FastAPI backend with WebSocket support
- Docker-ready deployment

### 🔧 Professional Features
- Session management with backend persistence
- Comprehensive error handling and logging
- Professional UI/UX with React and Tailwind CSS
- Mute/deafen controls for participants
- Conversation transcript display
- Connection status monitoring

### 🎨 Custom UI Integration
- **Travel Assistant UI**: Custom-designed components for travel planning
- **Voice Assistant Modal**: Integrated LiveKit voice room in a modal
- **Component Gallery**: Showcase of custom UI components
- **Unified Experience**: Seamless transition between custom UI and voice assistant

### 🛡️ Enterprise Security
- Environment-based configuration management
- Secure WebSocket connections
- Session isolation and cleanup
- Input validation and sanitization

## Architecture

```
┌─────────────────┐    ┌────────────────────┐    ┌──────────────────┐
│   React Frontend│────│  FastAPI Backend   │────│  LiveKit Server  │
│                 │    │                    │    │                  │
│ - Custom UI     │    │ - Session Mgmt     │    │ - STT/TTS        │
│ - Voice Modal   │    │ - REST API         │    │ - LLM Processing │
│ - Real-time     │    │ - Auth             │    │ - Media Routing  │
│   Updates       │    │ - Logging          │    │                  │
└─────────────────┘    └────────────────────┘    └──────────────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │   AI Services      │
                    │                    │
                    │ - Google Gemini    │
                    │ - Deepgram STT     │
                    │ - Cartesia TTS     │
                    │ - Pinecone (opt)   │
                    └────────────────────┘
```

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **LiveKit Agents**: Real-time voice AI framework
- **Google Gemini**: Large language model for conversation
- **Deepgram**: Speech-to-text processing
- **Cartesia**: Text-to-speech synthesis
- **Silero**: Voice activity detection
- **Pinecone** (optional): Vector database for knowledge base

### Frontend
- **React 18+**: Modern UI library
- **Next.js 15**: React framework with SSR
- **LiveKit Components**: Pre-built voice/video components
- **Tailwind CSS**: Utility-first CSS framework
- **Motion**: Animation library
- **Custom Travel Assistant UI**: Specialized components for travel planning

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- LiveKit account and project
- Google Cloud account with Gemini API access
- Deepgram API key
- Cartesia API key

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

5. Run the LiveKit worker (in a separate terminal):
```bash
python run_worker.py
```

6. Run the backend server (in another terminal):
```bash
uvicorn main:app --reload
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd agent-starter-react
```

2. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

3. Create a `.env.local` file:
```bash
cp .env.example .env.local
# Edit .env.local with your LiveKit credentials
```

4. Run the frontend:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

## API Endpoints

### Session Management
- `POST /sessions` - Create a new conversation session
- `GET /sessions/{session_id}` - Get session information
- `DELETE /sessions/{session_id}` - End a session

### WebSocket Communication
- `WS /ws/{session_id}` - Real-time voice communication

### Health Check
- `GET /health` - Backend health status

## Configuration

### Environment Variables

Backend `.env`:
```env
# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=False

# LiveKit settings
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your_livekit_url

# Google settings
GOOGLE_API_KEY=your_google_api_key

# Deepgram settings
DEEPGRAM_API_KEY=your_deepgram_api_key

# Cartesia settings
CARTESIA_API_KEY=your_cartesia_api_key

# Pinecone settings (optional)
PINECONE_API_KEY=your_pinecone_api_key
ASSISTANT_NAME=your_assistant_name
```

Frontend `.env.local`:
```env
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=/api/connection-details
NEXT_PUBLIC_APP_CONFIG_ENDPOINT=/api/app-config
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your_livekit_url
```

## Custom UI Integration

This project integrates custom UI components with the LiveKit voice assistant:

1. **Custom Landing Page**: The main page uses your custom UI components
2. **Voice Assistant Modal**: Clicking the "Voice Assistant" button opens the LiveKit voice room in a modal
3. **Component Gallery**: Visit `/components` to see a gallery of your custom UI components

For detailed information about the integration, see:
- [INTEGRATION_GUIDE.md](./agent-starter-react/INTEGRATION_GUIDE.md)
- [SETUP_INSTRUCTIONS.md](./SETUP_INSTRUCTIONS.md)

## Deployment

### Docker Deployment