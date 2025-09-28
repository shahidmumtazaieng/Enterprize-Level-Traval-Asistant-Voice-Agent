// Simple test to verify microphone access
console.log('Testing microphone access...');

const testMicrophoneAccess = async () => {
  try {
    console.log('Requesting microphone access...');
    
    // Request microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log('Microphone access granted!');
    
    // Create audio context
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    console.log('Audio context created');
    
    // Create media recorder
    const mediaRecorder = new MediaRecorder(stream, {
      mimeType: 'audio/webm;codecs=opus'
    });
    console.log('MediaRecorder created');
    
    // Set up data handling
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        console.log('Audio data available:', event.data.size, 'bytes');
      }
    };
    
    // Start recording
    mediaRecorder.start(1000); // Send data every 1000ms
    console.log('Started recording');
    
    // Stop after 5 seconds
    setTimeout(() => {
      mediaRecorder.stop();
      stream.getTracks().forEach(track => track.stop());
      console.log('Stopped recording and released microphone');
    }, 5000);
    
  } catch (err) {
    console.error('Error accessing microphone:', err);
  }
};

// Run the test
testMicrophoneAccess();