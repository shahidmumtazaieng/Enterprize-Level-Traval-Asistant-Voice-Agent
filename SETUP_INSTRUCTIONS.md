# Setup Instructions

This document provides step-by-step instructions for setting up and running the integrated application.

## Prerequisites

1. Node.js (version 16 or higher)
2. Python (version 3.8 or higher)
3. LiveKit account with API credentials
4. Google Cloud account with Gemini API access
5. Deepgram account with API credentials
6. Cartesia account with API credentials

## Backend Setup

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
   ```

5. Edit `.env` with your actual API keys:
   - LIVEKIT_API_KEY and LIVEKIT_API_SECRET from your LiveKit account
   - GOOGLE_API_KEY from your Google Cloud account
   - DEEPGRAM_API_KEY from your Deepgram account
   - CARTESIA_API_KEY from your Cartesia account

## Frontend Setup

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
   ```

4. Edit `.env.local` with your LiveKit credentials:
   - LIVEKIT_API_KEY
   - LIVEKIT_API_SECRET
   - LIVEKIT_URL

## Running the Application

To run the complete application, you need to start three processes:

### 1. Start the LiveKit Worker (in a separate terminal):
```bash
cd backend
python run_worker.py
```

### 2. Start the FastAPI Backend Server (in another terminal):
```bash
cd backend
uvicorn main:app --reload
```

### 3. Start the Next.js Frontend (in another terminal):
```bash
cd agent-starter-react
npm run dev
```

## Accessing the Application

Once all services are running:

1. Open your browser and navigate to `http://localhost:3000`
2. You should see the custom landing page with your UI components
3. Click the "Try Voice Assistant" button to open the LiveKit voice room

## Troubleshooting

### Common Issues

1. **"PublishTrackError: publishing rejected as engine not connected within timeout"**
   - Ensure the LiveKit worker is running
   - Check that all API credentials are correct
   - Verify network connectivity to LiveKit servers

2. **Voice assistant modal not opening**
   - Check browser console for JavaScript errors
   - Ensure all dependencies are installed correctly
   - Verify that the backend services are running

3. **Custom components not loading**
   - Check that the component paths in `custom-components-wrapper.tsx` are correct
   - Ensure components are exported properly
   - Verify that client-side dependencies are handled correctly

### Logs and Debugging

1. **Backend logs**: Check the terminal where you started the FastAPI server
2. **Frontend logs**: Check the browser developer console
3. **LiveKit worker logs**: Check the terminal where you started the worker

### Environment Variables

Make sure all required environment variables are set:

**Backend `.env`**:
- LIVEKIT_API_KEY
- LIVEKIT_API_SECRET
- LIVEKIT_URL
- GOOGLE_API_KEY
- DEEPGRAM_API_KEY
- CARTESIA_API_KEY

**Frontend `.env.local`**:
- LIVEKIT_API_KEY
- LIVEKIT_API_SECRET
- LIVEKIT_URL

## Customization

### Adding New Components

To add new components from your custom UI:

1. Add the component to `components/custom-components-wrapper.tsx`
2. Use it in `CustomComponentsWrapper`
3. Make sure the component accepts the `onVoiceAssistantClick` prop

### Modifying the Integration

To change how the voice assistant is triggered:

1. Modify `src/components/HeroSection.jsx` to call `onVoiceAssistantClick` from a different element
2. You can add voice assistant buttons to other components as well

### Styling

To customize the look and feel:

1. Edit the Tailwind CSS classes in the components
2. Modify the global styles in `app/globals.css`
3. Update the color scheme in `app-config.ts`

## Additional Resources

- [LiveKit Documentation](https://docs.livekit.io/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Integration Guide](./INTEGRATION_GUIDE.md)