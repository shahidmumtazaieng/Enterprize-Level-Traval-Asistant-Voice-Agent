# Integration Guide: Custom UI with LiveKit Voice Assistant

This guide explains how to use the integrated system that combines your custom UI with the LiveKit voice assistant.

## Project Structure

The project now has a unified structure where:

1. **Custom UI Components** - Located in `src/components/`
2. **LiveKit Integration** - Located in `components/enterprise-app.tsx`
3. **Unified Landing Page** - Located in `components/custom-landing-page.tsx`

## How It Works

1. The main landing page uses your custom UI components
2. A "Voice Assistant" button opens the LiveKit voice room in a modal
3. Users can interact with both the custom UI and the voice assistant

## Key Components

### Custom Landing Page (`components/custom-landing-page.tsx`)
- Displays your custom UI components
- Contains a modal for the LiveKit voice assistant
- Handles the integration between both systems

### Voice Assistant Modal (`components/voice-assistant-modal.tsx`)
- Displays the LiveKit voice room in a modal
- Provides a close button to return to the custom UI
- Handles keyboard shortcuts (Escape to close)

### Custom Components Wrapper (`components/custom-components-wrapper.tsx`)
- Dynamically imports your custom components
- Avoids SSR issues with client-side dependencies
- Passes the voice assistant callback to the HeroSection

## Adding New Components

To add new components from your custom UI:

1. Add the component to `components/custom-components-wrapper.tsx`:
   ```typescript
   const NewComponent = dynamic(() => import('@src/components/NewComponent'), { ssr: false });
   ```

2. Use it in `CustomComponentsWrapper`:
   ```jsx
   <NewComponent onVoiceAssistantClick={onVoiceAssistantClick} />
   ```

3. Make sure the component accepts the `onVoiceAssistantClick` prop and calls it when needed

## Customizing the Integration

### Changing the Trigger
To change how the voice assistant is triggered:

1. Modify `src/components/HeroSection.jsx` to call `onVoiceAssistantClick` from a different element
2. You can add voice assistant buttons to other components as well

### Styling the Modal
To customize the voice assistant modal:

1. Edit `components/voice-assistant-modal.tsx`
2. Modify the modal size, animations, or styling

### Adding Navigation
To add more navigation options:

1. Edit `app/(app)/layout.tsx` to add new navigation links
2. Create new pages in the `app/` directory

## Running the Application

1. Start the backend services:
   ```bash
   cd backend
   python run_worker.py  # In one terminal
   uvicorn main:app --reload  # In another terminal
   ```

2. Start the frontend:
   ```bash
   cd agent-starter-react
   npm run dev
   ```

3. Visit `http://localhost:3000` to see the integrated application

## API Routes

The application includes API routes for:

- `/api/connection-details` - LiveKit connection details
- `/api/custom-ui` - Information about custom UI components

## Troubleshooting

### Voice Assistant Not Working
1. Ensure the backend worker is running
2. Check that all environment variables are set correctly
3. Verify that the LiveKit credentials are valid

### Custom Components Not Loading
1. Check that the component paths in `custom-components-wrapper.tsx` are correct
2. Ensure components are exported properly
3. Verify that client-side dependencies are handled correctly

### Styling Issues
1. Check the Tailwind CSS configuration
2. Ensure all CSS classes are properly applied
3. Verify that the dark mode classes are correct

## Extending the Integration

You can extend this integration by:

1. Adding voice assistant buttons to other pages
2. Creating a persistent voice assistant that doesn't require a modal
3. Adding voice commands to control the custom UI
4. Implementing voice-driven navigation between sections