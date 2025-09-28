import { useState, useEffect, useRef } from 'react'

const ChatInterface = ({ messages, isListening, isSpeaking, isConnected, voiceActivity, onToggleListening, onSendMessage }) => {
  const [isTyping, setIsTyping] = useState(false)
  const [microphoneError, setMicrophoneError] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Listen for microphone errors
  useEffect(() => {
    const handleMicrophoneError = (event) => {
      setMicrophoneError(event.detail)
      // Clear error after 5 seconds
      setTimeout(() => setMicrophoneError(null), 5000)
    }

    window.addEventListener('microphoneError', handleMicrophoneError)
    
    return () => {
      window.removeEventListener('microphoneError', handleMicrophoneError)
    }
  }, [])

  // Enhanced Bar Visualizer Component with frequency visualization
  const BarVisualizer = ({ state, barCount = 7, voiceData }) => {
    // Determine if the visualizer should be active based on state
    const isActive = state === 'listening' || state === 'speaking'
    
    // Use voice activity data when available
    const activityLevel = isActive ? 
      (voiceData?.current * 100 || (voiceActivity * 100)) : 
      (state === 'speaking' ? 60 : 20)
    
    // Get frequency data if available
    const frequencies = voiceData?.frequencies || { low: 0, mid: 0, high: 0 }
    
    return (
      <div className="flex flex-col items-center">
        {/* Frequency visualization - show different colors for different frequencies */}
        <div className="flex items-end justify-center h-16 gap-1 mb-2 w-full">
          {Array.from({ length: barCount }).map((_, index) => {
            // Distribute bars among frequency ranges
            const freqRange = index % 3
            let freqValue = 0
            let barColor = ''
            
            switch(freqRange) {
              case 0: // Low frequency
                freqValue = frequencies.low
                barColor = 'bg-red-500'
                break
              case 1: // Mid frequency
                freqValue = frequencies.mid
                barColor = 'bg-yellow-500'
                break
              case 2: // High frequency
                freqValue = frequencies.high
                barColor = 'bg-blue-500'
                break
            }
            
            const height = isActive ? 
              `${20 + (freqValue * 60)}%` : 
              '20%'
            
            return (
              <div
                key={`freq-${index}`}
                className={`w-2 rounded-t ${isActive ? barColor : 'bg-gray-300'}`}
                style={{
                  height,
                  transition: 'height 0.1s ease-out'
                }}
              />
            )
          })}
        </div>
        
        {/* Main activity visualization */}
        <div className="flex items-end justify-center h-32 gap-2">
          {Array.from({ length: barCount }).map((_, index) => (
            <div
              key={index}
              className={`w-4 rounded-t transition-all duration-100 ${
                isActive 
                  ? 'bg-gradient-to-t from-blue-500 to-purple-500' 
                  : 'bg-gray-300'
              }`}
              style={{
                height: `${20 + (activityLevel * 0.6 * (0.7 + 0.3 * Math.sin(index)))}%`,
                transition: 'height 0.1s ease-out'
              }}
            />
          ))}
        </div>
        
        {/* Voice activity history visualization */}
        {voiceData?.history && (
          <div className="flex items-end justify-center h-16 gap-1 mt-2 w-full">
            {voiceData.history.slice(-barCount).map((entry, index) => (
              <div
                key={`history-${index}`}
                className="w-2 rounded-t bg-green-400"
                style={{
                  height: `${10 + (entry.overall * 90)}%`,
                  transition: 'height 0.1s ease-out'
                }}
              />
            ))}
          </div>
        )}
      </div>
    )
  }

  // Custom Voice Control Component
  const VoiceControlBar = ({ isListening, onToggle }) => {
    return (
      <div className="flex justify-center">
        <button
          onClick={onToggle}
          disabled={!isConnected} // Disable button when not connected
          className={`w-16 h-16 rounded-full text-white text-2xl transition-all duration-300 transform hover:scale-110 ${
            !isConnected 
              ? 'bg-gray-400 cursor-not-allowed' // Gray when disconnected
              : isListening 
                ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600'
          }`}
        >
          {isListening ? '⏹️' : '🎤'}
        </button>
      </div>
    )
  }

  // Determine the current state for the visualizer
  const getVisualizerState = () => {
    if (isListening) return 'listening'
    if (isSpeaking) return 'speaking'
    if (isConnected) return 'connected'
    return 'disconnected'
  }

  return (
    <div className="voice-interface rounded-3xl p-8 h-full">
      {/* Assistant Introduction with Customer Support Image */}
      <div className="text-center mb-8">
        <div className="assistant-avatar w-48 h-48 mx-auto mb-4 rounded-full overflow-hidden border-4 border-blue-100">
          {/* Customer Support Representative Image */}
          <div className="w-full h-full bg-gradient-to-br from-blue-200 to-purple-200 flex items-center justify-center">
            <span className="text-6xl">👩‍💼</span>
          </div>
        </div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Hello! I'm your Business Travel Assistant</h2>
        <p className="text-gray-600">I'm here to help you with all your business travel needs. Just click the microphone and start talking!</p>
      </div>

      {/* Microphone error display */}
      {microphoneError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <strong>Microphone Error:</strong> {microphoneError}
        </div>
      )}

      {/* Voice Assistant Visualization */}
      <div className="mb-8">
        <div className="visualizer-container bg-gray-50 rounded-2xl p-6 mb-6">
          <BarVisualizer 
            state={getVisualizerState()} 
            barCount={7} 
            voiceData={typeof voiceActivity === 'object' ? voiceActivity : null}
          />
        </div>
        
        {/* Voice Assistant Controls */}
        <div className="control-section text-center mb-6">
          <VoiceControlBar 
            isListening={isListening}
            onToggle={onToggleListening}
          />
          <p className="text-gray-600 mt-4">
            {!isConnected 
              ? 'Connecting to voice service...' 
              : isListening 
                ? 'Listening... Click to stop' 
                : 'Click to start speaking'
            }
          </p>
        </div>
        
        {/* Conversation History */}
        <div className="conversation bg-gray-50 rounded-2xl p-4 h-64 overflow-y-auto mb-4">
          {messages.map((msg, index) => (
            <div key={index} className="message mb-3 p-3 rounded-lg bg-white shadow-sm">
              <strong className={`message-${msg.type} ${msg.type === 'assistant' ? 'text-blue-600' : 'text-green-600'}`}>
                {msg.type === 'assistant' ? 'Assistant: ' : 'You: '}
              </strong>
              <span className="message-text">{msg.content}</span>
            </div>
          ))}
          {isTyping && (
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <span className="ml-2 text-sm text-gray-500">Assistant is typing...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Quick Commands */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Try saying:</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          <button 
            onClick={() => onSendMessage('Book a flight to New York next week')}
            className="command-button px-4 py-3 rounded-xl text-left bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            ✈️ Book a flight to New York next week
          </button>
          <button 
            onClick={() => onSendMessage('Find business hotels in London')}
            className="command-button px-4 py-3 rounded-xl text-left bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            🏨 Find business hotels in London
          </button>
          <button 
            onClick={() => onSendMessage('What documents do I need for Japan?')}
            className="command-button px-4 py-3 rounded-xl text-left bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            📋 What documents do I need for Japan?
          </button>
          <button 
            onClick={() => onSendMessage('Schedule a meeting in Tokyo')}
            className="command-button px-4 py-3 rounded-xl text-left bg-white border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            📅 Schedule a meeting in Tokyo
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface