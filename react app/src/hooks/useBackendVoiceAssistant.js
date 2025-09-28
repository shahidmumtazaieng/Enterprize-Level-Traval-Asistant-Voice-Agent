import { useState, useEffect, useRef } from 'react'

// Import LiveKit components
import {
  Room,
  RoomEvent,
  RemoteParticipant,
  RemoteTrackPublication,
  RemoteTrack,
  LocalTrackPublication,
  LocalAudioTrack,
  Track,
  ConnectionState
} from 'livekit-client'

export const useBackendVoiceAssistant = () => {
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [messages, setMessages] = useState([])
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [sessionData, setSessionData] = useState(null)
  
  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioContextRef = useRef(null)
  const audioStreamRef = useRef(null)
  const roomRef = useRef(null)  // LiveKit room reference
  const analyserRef = useRef(null)  // For voice activity detection
  const animationFrameRef = useRef(null)  // For animation loop

  // Create session with backend
  const createSession = async () => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      console.log('Creating session with backend:', `${API_URL}/sessions`)
      
      const sessionResponse = await fetch(`${API_URL}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          system_prompt: "You are a friendly travel assistant.",
          agent_name: "TravelAssistant"
        })
      })
      
      console.log('Session response status:', sessionResponse.status)
      
      if (!sessionResponse.ok) {
        const errorText = await sessionResponse.text()
        console.error('Session creation failed:', errorText)
        throw new Error(`Failed to create session: ${sessionResponse.status} ${sessionResponse.statusText} - ${errorText}`)
      }
      
      const sessionData = await sessionResponse.json()
      console.log('Session created successfully:', sessionData)
      setSessionId(sessionData.session_id)
      setSessionData(sessionData)
      return sessionData
    } catch (err) {
      console.error('Error creating session:', err)
      throw err
    }
  }

  // Request microphone access with better error handling
  const requestMicrophoneAccess = async () => {
    try {
      console.log('Requesting microphone access...')
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioStreamRef.current = stream
      console.log('Microphone access granted')
      setError(null) // Clear any previous errors
      return stream
    } catch (err) {
      console.error('Error accessing microphone:', err)
      let errorMessage = 'Microphone access denied. Please allow microphone access in your browser settings.'
      
      // Provide more specific error messages
      if (err.name === 'NotAllowedError') {
        errorMessage = 'Microphone access was denied. Please click the microphone button again and allow access when prompted.'
      } else if (err.name === 'NotFoundError') {
        errorMessage = 'No microphone found. Please connect a microphone and try again.'
      } else if (err.name === 'NotReadableError') {
        errorMessage = 'Microphone is being used by another application. Please close other applications and try again.'
      }
      
      setError(errorMessage)
      // Dispatch a custom event for microphone error
      window.dispatchEvent(new CustomEvent('microphoneError', { detail: errorMessage }))
      throw err
    }
  }

  // Initialize audio context and media recorder
  const initializeAudio = async () => {
    try {
      // Request microphone access
      const stream = await requestMicrophoneAccess()
      
      // Create audio context
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
      
      // Create media recorder
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      // Set up audio analysis for voice activity detection
      const analyser = audioContextRef.current.createAnalyser()
      analyserRef.current = analyser
      analyser.fftSize = 256
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyser)
      
      // Set up data handling
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && roomRef.current && roomRef.current.state === ConnectionState.Connected) {
          // Send audio data directly to LiveKit room
          const reader = new FileReader()
          reader.onload = () => {
            const arrayBuffer = reader.result
            // Send as binary data through WebSocket to backend for forwarding to LiveKit
            if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
              wsRef.current.send(arrayBuffer)
            }
          }
          reader.readAsArrayBuffer(event.data)
        }
      }
      
      // Set up recording intervals
      mediaRecorderRef.current.onstart = () => {
        console.log('MediaRecorder started')
        // Start voice activity detection
        startVoiceActivityDetection()
      }
      
      mediaRecorderRef.current.onstop = () => {
        console.log('MediaRecorder stopped')
        // Stop voice activity detection
        stopVoiceActivityDetection()
      }
      
      console.log('Audio initialized successfully')
      return true
    } catch (err) {
      console.error('Error initializing audio:', err)
      setError('Failed to initialize audio: ' + err.message)
      return false
    }
  }

  // Voice activity detection
  const startVoiceActivityDetection = () => {
    if (!analyserRef.current) return
    
    // Store voice activity history
    const activityHistory = []
    const maxHistoryLength = 50 // Store last 50 samples
    
    // Configurable sensitivity (lower values = more sensitive)
    const sensitivity = 30
    
    const detectVoiceActivity = () => {
      if (!analyserRef.current) return
      
      const bufferLength = analyserRef.current.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      analyserRef.current.getByteFrequencyData(dataArray)
      
      // Calculate average volume
      let sum = 0
      for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i]
      }
      const average = sum / bufferLength
      
      // Fine-tune sensitivity - adjustable normalization
      const normalizedVolume = Math.min(1, average / sensitivity)
      
      // Frequency analysis - split into low, mid, high frequencies
      const lowFreq = 0, midFreq = Math.floor(bufferLength/3), highFreq = Math.floor(2*bufferLength/3)
      
      let lowSum = 0, midSum = 0, highSum = 0
      for (let i = 0; i < bufferLength; i++) {
        if (i < midFreq) lowSum += dataArray[i]
        else if (i < highFreq) midSum += dataArray[i]
        else highSum += dataArray[i]
      }
      
      const lowAvg = lowSum / midFreq
      const midAvg = midSum / (highFreq - midFreq)
      const highAvg = highSum / (bufferLength - highFreq)
      
      // Normalize frequency values
      const normalizedLow = Math.min(1, lowAvg / sensitivity)
      const normalizedMid = Math.min(1, midAvg / sensitivity)
      const normalizedHigh = Math.min(1, highAvg / sensitivity)
      
      // Add to history
      activityHistory.push({
        timestamp: Date.now(),
        overall: normalizedVolume,
        low: normalizedLow,
        mid: normalizedMid,
        high: normalizedHigh
      })
      
      // Keep only the last maxHistoryLength entries
      if (activityHistory.length > maxHistoryLength) {
        activityHistory.shift()
      }
      
      // Send voice activity data to parent component
      window.dispatchEvent(new CustomEvent('voiceActivity', { 
        detail: {
          current: normalizedVolume,
          frequencies: {
            low: normalizedLow,
            mid: normalizedMid,
            high: normalizedHigh
          },
          history: [...activityHistory] // Send a copy of the history
        }
      }))
      
      // Continue detection loop
      animationFrameRef.current = requestAnimationFrame(detectVoiceActivity)
    }
    
    detectVoiceActivity()
  }

  // Stop voice activity detection
  const stopVoiceActivityDetection = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    // Reset voice activity
    window.dispatchEvent(new CustomEvent('voiceActivity', { detail: 0 }))
  }

  // Connect to LiveKit room
  const connectToLiveKitRoom = async (roomName, token) => {
    try {
      console.log('Connecting to LiveKit room:', roomName)
      
      // Create LiveKit room
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
        videoCaptureDefaults: {
          resolution: {
            width: 1280,
            height: 720,
          },
        },
      })
      
      roomRef.current = room
      
      // Set up room event listeners
      room.on(RoomEvent.TrackSubscribed, handleTrackSubscribed)
      room.on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed)
      room.on(RoomEvent.DataReceived, handleDataReceived)
      room.on(RoomEvent.Disconnected, handleRoomDisconnected)
      room.on(RoomEvent.ParticipantConnected, (participant) => {
        console.log('Participant connected:', participant.identity)
      })
      room.on(RoomEvent.ParticipantDisconnected, (participant) => {
        console.log('Participant disconnected:', participant.identity)
      })
      
      // Connect to room
      await room.connect(import.meta.env.VITE_LIVEKIT_URL, token)
      console.log('Connected to LiveKit room')
      
      // Publish local audio track
      if (audioStreamRef.current) {
        const localAudioTrack = new LocalAudioTrack(audioStreamRef.current.getAudioTracks()[0])
        await room.localParticipant.publishTrack(localAudioTrack)
        console.log('Published local audio track')
      }
      
      return room
    } catch (err) {
      console.error('Error connecting to LiveKit room:', err)
      setError('Failed to connect to voice service: ' + err.message)
      throw err
    }
  }

  // Handle subscribed tracks
  const handleTrackSubscribed = (track, publication, participant) => {
    console.log('Track subscribed:', track.kind, 'from', participant.identity)
    
    if (track.kind === Track.Kind.Audio) {
      // Audio track from agent
      const element = track.attach()
      document.body.appendChild(element)
      setIsSpeaking(true)
    }
  }

  // Handle unsubscribed tracks
  const handleTrackUnsubscribed = (track, publication, participant) => {
    console.log('Track unsubscribed:', track.kind, 'from', participant.identity)
    
    if (track.kind === Track.Kind.Audio) {
      // Audio track from agent
      track.detach()
      setIsSpeaking(false)
    }
  }

  // Handle data received from room
  const handleDataReceived = (payload, participant) => {
    try {
      const data = JSON.parse(new TextDecoder().decode(payload))
      console.log('Data received from room:', data, 'from', participant?.identity)
      
      // Handle different message types
      switch (data.type) {
        case 'user_transcript':
          const userMessage = { type: 'user', content: data.transcript }
          setMessages(prev => [...prev, userMessage])
          break
        case 'ai_response':
          const aiMessage = { type: 'assistant', content: data.text }
          setMessages(prev => [...prev, aiMessage])
          break
        case 'listening_started':
          setIsListening(true)
          setIsSpeaking(false)
          break
        case 'listening_stopped':
          setIsListening(false)
          break
        case 'processing_started':
          setIsListening(false)
          setIsSpeaking(true)
          break
        case 'processing_stopped':
          setIsSpeaking(false)
          break
        default:
          console.log('Unknown data type:', data.type)
      }
    } catch (err) {
      console.error('Error parsing data received from room:', err)
    }
  }

  // Handle room disconnection
  const handleRoomDisconnected = () => {
    console.log('Disconnected from LiveKit room')
    setIsConnected(false)
    setConnectionStatus('disconnected')
    
    // Clean up audio resources
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(track => track.stop())
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
  }

  // Connect to backend WebSocket
  const connectToVoiceService = async () => {
    try {
      setConnectionStatus('connecting')
      setError(null)
      
      // Get API URL from environment variable
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      // Create session if not already created
      let sessionDataToUse = sessionData
      if (!sessionDataToUse) {
        console.log('No existing session, creating new one...')
        sessionDataToUse = await createSession()
      } else {
        console.log('Using existing session:', sessionDataToUse.session_id)
      }
      
      // Connect to backend WebSocket endpoint
      const wsUrl = `${API_URL.replace('http', 'ws')}/ws/${sessionDataToUse.session_id}`
      console.log('Connecting to backend WebSocket:', wsUrl)
      
      wsRef.current = new WebSocket(wsUrl)
      
      wsRef.current.onopen = async () => {
        console.log('Connected to backend WebSocket')
        
        // Initialize audio after connection
        await initializeAudio()
        
        // Connect to LiveKit room using the token from session data
        if (sessionDataToUse.livekit_user_token && sessionDataToUse.livekit_room) {
          try {
            await connectToLiveKitRoom(sessionDataToUse.livekit_room, sessionDataToUse.livekit_user_token)
            setIsConnected(true)
            setConnectionStatus('connected')
            setError(null)
          } catch (err) {
            console.error('Failed to connect to LiveKit room:', err)
            setError('Failed to connect to voice service: ' + err.message)
            setConnectionStatus('error')
            return
          }
        } else {
          console.warn('LiveKit room info not available in session data')
          // Fallback to just WebSocket connection
          setIsConnected(true)
          setConnectionStatus('connected')
          setError(null)
        }
        
        // Add initial welcome message
        setMessages(prev => [
          ...prev,
          {
            type: 'assistant',
            content: 'Hello! I\'m your Enterprise Travel Assistant. How can I help you plan your next trip?'
          }
        ])
      }
      
      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('Received message from backend:', data)
          handleMessageFromBackend(data)
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
          setError('Error processing response from voice service')
        }
      }
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        const errorMessage = error.message || error.toString()
        setError('Connection error: ' + errorMessage)
        setConnectionStatus('error')
      }
      
      wsRef.current.onclose = (event) => {
        console.log('Disconnected from backend WebSocket', event.reason, 'Code:', event.code)
        setIsConnected(false)
        // Stop media recorder and release audio resources
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
          mediaRecorderRef.current.stop()
        }
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach(track => track.stop())
        }
        if (audioContextRef.current) {
          audioContextRef.current.close()
        }
        if (roomRef.current) {
          roomRef.current.disconnect()
        }
        if (event.code !== 1000) { // Not a normal closure
          setError(`Connection closed: ${event.reason || 'Unknown reason'} (Code: ${event.code})`)
          setConnectionStatus('error')
        } else {
          setConnectionStatus('disconnected')
        }
      }
    } catch (err) {
      console.error('Error connecting to voice service:', err)
      setError(err.message || 'Failed to connect to voice service')
      setConnectionStatus('error')
    }
  }

  // Handle messages from backend
  const handleMessageFromBackend = (data) => {
    console.log('Handling message from backend:', data);
    switch (data.type) {
      case 'user_transcript':
        const userMessage = { type: 'user', content: data.transcript }
        setMessages(prev => [...prev, userMessage])
        break
      case 'ai_response':
        const aiMessage = { type: 'assistant', content: data.text }
        setMessages(prev => [...prev, aiMessage])
        setIsSpeaking(true)
        // Reset speaking state after a delay
        setTimeout(() => setIsSpeaking(false), 2000)
        break
      case 'listening_started':
        setIsListening(true)
        setIsSpeaking(false)
        break
      case 'listening_stopped':
        setIsListening(false)
        break
      case 'processing_started':
        setIsListening(false)
        setIsSpeaking(true)
        break
      case 'processing_stopped':
        setIsSpeaking(false)
        break
      case 'session_ready':
        console.log('Session is ready for voice interaction')
        break
      case 'session_stopped':
        console.log('Session has been stopped')
        break
      case 'connection_established':
        console.log('Connection established with voice service')
        break
      case 'error':
        setError(data.message || 'Unknown error from backend')
        break
      default:
        console.log('Unknown message type:', data.type, data)
    }
  }

  // Start listening for user speech
  const startListening = async () => {
    if (!isConnected) {
      await connectToVoiceService()
      // Wait a bit for connection to establish
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    try {
      // Send start listening message to backend
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ 
          type: 'control',
          action: 'start'
        }))
      }
      
      // Start recording audio if media recorder is available
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
        mediaRecorderRef.current.start(1000) // Send data every 1000ms
        console.log('Started recording audio')
      }
    } catch (err) {
      console.error('Error starting listening:', err)
      setError('Failed to start listening: ' + err.message)
    }
  }

  // Stop listening for user speech
  const stopListening = () => {
    try {
      // Send stop listening message to backend
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ 
          type: 'control',
          action: 'stop'
        }))
      }
      
      // Stop recording audio if media recorder is active
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop()
        console.log('Stopped recording audio')
      }
    } catch (err) {
      console.error('Error stopping listening:', err)
      setError('Failed to stop listening: ' + err.message)
    }
  }

  // Toggle listening state
  const toggleListening = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Stop media recorder and release audio resources
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop())
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (roomRef.current) {
        roomRef.current.disconnect()
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [])

  return {
    isConnected,
    isListening,
    isSpeaking,
    messages,
    connectionStatus,
    error,
    sessionId,
    sessionData,
    connectToVoiceService,
    startListening,
    stopListening,
    toggleListening
  }
}