import streamlit as st
import av
import numpy as np
import queue
import threading
import time
import logging
import io
import os
import tempfile
from datetime import datetime
import soundfile as sf
import sounddevice as sd
from pydub import AudioSegment
from streamlit_webrtc import WebRtcMode, webrtc_streamer
from aiortc.contrib.media import MediaRecorder
import matplotlib.pyplot as plt

# Import our helper functions
from utils.audio import save_audio_from_array, save_audio_file, cleanup_old_audio_files

class AudioProcessor:
    """
    Processes audio frames from WebRTC stream
    """
    def __init__(self):
        self.audio_chunks = []
        self.sample_rate = 16000  # Default to 16kHz
        self.recording = False
        self.frame_queue = queue.Queue()
        self.frame_count = 0
        self.processing_thread = None
        self.last_update_time = time.time()
        self.debug_info = {"frames_processed": 0, "queue_size": 0}
        logging.info(f"AudioProcessor initialized")
    
    def start_recording(self):
        """Start recording audio"""
        self.audio_chunks = []
        self.recording = True
        self.frame_count = 0
        self.frame_queue = queue.Queue()
        self.last_update_time = time.time()
        
        # Start the processing thread
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.processing_thread = threading.Thread(target=self._process_frames)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
        logging.info("Started recording audio")
    
    def stop_recording(self):
        """Stop recording audio and return the processed audio"""
        logging.info("Stopping recording and processing audio...")
        self.recording = False
        
        # Wait for the processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            logging.info("Waiting for processing thread to complete...")
            self.processing_thread.join(timeout=5.0)  # Increased timeout
        
        # Log recording results
        logging.info(f"Stopped recording audio. Processed {self.frame_count} frames")
        
        if not self.audio_chunks:
            logging.warning("No audio data was recorded")
            return None
            
        # Concatenate audio chunks
        try:
            logging.info(f"Concatenating {len(self.audio_chunks)} audio chunks")
            audio_data = np.concatenate(self.audio_chunks, axis=0)
            
            # Log audio data details
            recording_duration = len(audio_data) / self.sample_rate if self.sample_rate else 0
            logging.info(f"Audio recording complete: {recording_duration:.2f} seconds, {len(audio_data)} samples")
            
            if len(audio_data) == 0:
                logging.warning("Empty audio data after concatenation")
                return None
                
            return audio_data, self.sample_rate
        except Exception as e:
            logging.error(f"Error concatenating audio chunks: {e}")
            if len(self.audio_chunks) > 0:
                # Try to return just the first chunk if concatenation fails
                logging.info("Attempting to return first audio chunk as fallback")
                return self.audio_chunks[0], self.sample_rate
            return None
    
    def _process_frames(self):
        """Process frames from the queue in a separate thread"""
        batch_size = 10  # Process frames in batches for efficiency
        last_log_time = time.time()
        temp_chunks = []
        
        while self.recording or not self.frame_queue.empty():
            try:
                frames_processed = 0
                # Process up to batch_size frames at once
                for _ in range(batch_size):
                    if not self.frame_queue.empty():
                        frame = self.frame_queue.get(block=False)
                        audio_data = frame.to_ndarray()
                        self.sample_rate = frame.sample_rate
                        temp_chunks.append(audio_data)
                        frames_processed += 1
                    else:
                        break
                
                # If we processed any frames, add them to audio_chunks
                if frames_processed > 0:
                    self.frame_count += frames_processed
                    
                    # Update debug info periodically (no more than once per second)
                    current_time = time.time()
                    if current_time - last_log_time > 1.0:
                        self.debug_info = {
                            "frames_processed": self.frame_count,
                            "queue_size": self.frame_queue.qsize(),
                            "audio_chunks": len(self.audio_chunks) + len(temp_chunks),
                            "sample_rate": self.sample_rate,
                            "recording_duration": self.frame_count / self.sample_rate if self.sample_rate else 0
                        }
                        last_log_time = current_time
                        
                        # Every few seconds, consolidate chunks to prevent memory issues
                        if len(temp_chunks) > 50:
                            if temp_chunks:
                                combined = np.concatenate(temp_chunks, axis=0)
                                self.audio_chunks.append(combined)
                                temp_chunks = []
                                logging.info(f"Consolidated audio chunks. Total frames: {self.frame_count}")
                else:
                    # No frames to process, sleep briefly
                    time.sleep(0.01)
                    
            except Exception as e:
                logging.error(f"Error processing audio frame batch: {e}")
                time.sleep(0.01)  # Brief pause on error
                
        # Final consolidation of any remaining chunks
        if temp_chunks:
            try:
                combined = np.concatenate(temp_chunks, axis=0)
                self.audio_chunks.append(combined)
                logging.info(f"Final audio chunk consolidation. Total frames: {self.frame_count}")
            except Exception as e:
                logging.error(f"Error in final audio chunk consolidation: {e}")
    
    def process_frame(self, frame):
        """Add a frame to the processing queue"""
        if self.recording:
            self.frame_queue.put(frame)
            return frame
        return frame


def record_audio_with_sounddevice():
    """Record audio using sounddevice directly"""
    st.subheader("Direct Microphone Recording")
    
    # Parameters for recording
    duration = st.slider("Recording Duration (seconds)", 5, 120, 30)
    sample_rate = 16000  # Standard rate for speech
    
    col1, col2 = st.columns(2)
    with col1:
        record_button = st.button("Start Recording (Direct Mic)")
    with col2:
        if "audio_data" in st.session_state:
            play_button = st.button("Play Recorded Audio")
    
    status_placeholder = st.empty()
    
    if record_button:
        try:
            # Show recording in progress
            status_placeholder.info(f"Recording for {duration} seconds...")
            
            # Play a beep sound to indicate recording has started
            # Generate a short beep
            beep_duration = 0.3
            beep_frequency = 440  # A4 note
            t = np.linspace(0, beep_duration, int(beep_duration * sample_rate), endpoint=False)
            beep_data = 0.5 * np.sin(2 * np.pi * beep_frequency * t)
            
            # Play the beep
            sd.play(beep_data, sample_rate)
            sd.wait()  # Wait for the beep to finish
            
            # Record audio from microphone
            audio_data = sd.rec(int(duration * sample_rate), 
                               samplerate=sample_rate, 
                               channels=1, 
                               dtype='float32')
            
            # Show a progress bar
            progress_bar = st.progress(0)
            for i in range(duration):
                time.sleep(1)
                progress_bar.progress((i + 1) / duration)
            
            sd.wait()  # Wait until recording is finished
            
            # Play another beep to indicate recording has ended
            t = np.linspace(0, beep_duration, int(beep_duration * sample_rate), endpoint=False)
            beep_data = 0.5 * np.sin(2 * np.pi * beep_frequency * 1.5 * t)  # Higher pitch
            sd.play(beep_data, sample_rate)
            sd.wait()
            
            # Log audio statistics to help debug
            logging.info(f"Recorded audio: shape={audio_data.shape}, min={np.min(audio_data)}, max={np.max(audio_data)}, mean={np.mean(audio_data)}")
            
            # Check if the audio is silent
            if np.max(np.abs(audio_data)) < 0.01:
                logging.warning("Audio recording appears to be silent or very quiet")
                status_placeholder.warning("Recording seems very quiet. Please make sure your microphone is working and try again.")
            
            # Store the recording in session state
            st.session_state.audio_data = audio_data
            st.session_state.sample_rate = sample_rate
            
            # Save to a temporary file
            audio_file_path = save_audio_from_array(audio_data, sample_rate)
            st.session_state.audio_file_path = audio_file_path
            
            status_placeholder.success(f"Recording complete! {len(audio_data)/sample_rate:.1f} seconds recorded")
            
            # Rerun to update UI
            st.experimental_rerun()
            
        except Exception as e:
            status_placeholder.error(f"Error recording audio: {str(e)}")
            logging.error(f"Error in sounddevice recording: {str(e)}")
            return None, False
    
    if "audio_data" in st.session_state and "audio_file_path" in st.session_state:
        # Show audio waveform visualization
        audio_data = st.session_state.audio_data
        if len(audio_data) > 0:
            # Plot waveform
            fig, ax = plt.subplots(figsize=(10, 2))
            ax.plot(np.linspace(0, len(audio_data)/sample_rate, len(audio_data)), audio_data)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Amplitude')
            ax.set_title('Audio Waveform')
            st.pyplot(fig)
        
        # Play audio using st.audio
        st.audio(st.session_state.audio_file_path)
        
        if st.button("Process This Recording"):
            return st.session_state.audio_file_path, True
    
    return None, False


def record_audio_component():
    """
    Streamlit component for recording audio
    
    Returns:
        tuple: (audio_file_path, should_process)
    """
    # Create a container for the audio recording components
    st.subheader("🎙️ Record or Upload Audio")
    
    # Initialize session state variables
    if "audio_processor" not in st.session_state:
        st.session_state.audio_processor = AudioProcessor()
        logging.info("Created new AudioProcessor in session state")
    else:
        logging.info("Using existing AudioProcessor from session state")
    
    # Display the most recent debug info
    if hasattr(st.session_state.audio_processor, "debug_info"):
        debug_info = st.session_state.audio_processor.debug_info
        if debug_info:
            with st.expander("Debug Info", expanded=False):
                for key, value in debug_info.items():
                    st.text(f"{key}: {value}")
    
    # Create tabs for recording options
    tab1, tab2, tab3, tab4 = st.tabs(["Direct Microphone", "Simple Recorder", "WebRTC Recorder", "Upload File"])
    
    audio_file_path = None
    should_process = False
    
    with tab1:
        # The new direct microphone recorder
        mic_path, should_process_mic = record_audio_with_sounddevice()
        if mic_path:
            audio_file_path = mic_path
            should_process = should_process_mic
    
    with tab2:
        st.markdown("""
        ### Simple Audio Recorder
        Click the button below to record audio using your microphone.
        """)
        
        # Add an HTML/JS component for audio recording
        st.markdown("""
        <style>
        .record-button {
            background-color: #FF4B4B;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            border: none;
            cursor: pointer;
            margin: 10px 0;
            font-weight: bold;
        }
        .record-button.recording {
            background-color: #4BB543;
        }
        .timer {
            font-size: 24px;
            margin: 10px 0;
        }
        </style>
        
        <div id="recorder-container">
            <button id="recordButton" class="record-button">Start Recording</button>
            <div id="timer" class="timer">00:00</div>
            <div id="status"></div>
            <audio id="audioPlayback" controls style="display:none;"></audio>
        </div>
        
        <script>
        const recordButton = document.getElementById('recordButton');
        const timer = document.getElementById('timer');
        const status = document.getElementById('status');
        const audioPlayback = document.getElementById('audioPlayback');
        
        let mediaRecorder;
        let audioChunks = [];
        let startTime;
        let timerInterval;
        let isRecording = false;
        let audioUrl;
        
        recordButton.addEventListener('click', () => {
            if (!isRecording) {
                startRecording();
            } else {
                stopRecording();
            }
        });
        
        function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    isRecording = true;
                    recordButton.textContent = 'Stop Recording';
                    recordButton.classList.add('recording');
                    status.textContent = 'Recording...';
                    
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };
                    
                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        audioUrl = URL.createObjectURL(audioBlob);
                        audioPlayback.src = audioUrl;
                        audioPlayback.style.display = 'block';
                        
                        // Create FormData to send
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'recording.wav');
                        
                        // Send data to server
                        fetch('/upload_audio', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            status.textContent = 'Audio uploaded successfully.';
                            // Store the audio file path in a hidden input
                            const hiddenInput = document.createElement('input');
                            hiddenInput.type = 'hidden';
                            hiddenInput.id = 'audioFilePath';
                            hiddenInput.value = data.file_path;
                            document.body.appendChild(hiddenInput);
                            
                            // Create a process button programmatically
                            const processButton = document.createElement('button');
                            processButton.textContent = 'Process Recording';
                            processButton.className = 'stButton';
                            processButton.onclick = () => {
                                // Set a query parameter to trigger processing
                                const params = new URLSearchParams(window.location.search);
                                params.set('process_audio', data.file_path);
                                window.location.search = params.toString();
                            };
                            status.appendChild(document.createElement('br'));
                            status.appendChild(processButton);
                        })
                        .catch(error => {
                            status.textContent = 'Error uploading audio: ' + error.message;
                        });
                    };
                    
                    startTime = Date.now();
                    updateTimer();
                    timerInterval = setInterval(updateTimer, 1000);
                    
                    mediaRecorder.start();
                    audioChunks = [];
                })
                .catch(error => {
                    status.textContent = 'Error accessing microphone: ' + error.message;
                });
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                isRecording = false;
                recordButton.textContent = 'Start Recording';
                recordButton.classList.remove('recording');
                status.textContent = 'Processing audio...';
                
                clearInterval(timerInterval);
                mediaRecorder.stop();
                
                // Stop all tracks
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        }
        
        function updateTimer() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            timer.textContent = `${minutes}:${seconds}`;
        }
        </script>
        """, unsafe_allow_html=True)
        
        # Check if audio data is in query params (from the JavaScript component)
        query_params = st.experimental_get_query_params()
        process_audio = query_params.get("process_audio", [None])[0]
        
        if process_audio:
            try:
                audio_file_path = process_audio
                if os.path.exists(audio_file_path):
                    logging.info(f"Audio recorded via simple recorder: {audio_file_path}")
                    st.success("Audio ready to process!")
                    
                    # Remove the query parameter by navigating back without it
                    st.markdown("""
                    <script>
                    const params = new URLSearchParams(window.location.search);
                    params.delete('process_audio');
                    window.history.replaceState(null, '', '?' + params.toString());
                    </script>
                    """, unsafe_allow_html=True)
                    
                    # Set that the audio is ready for processing
                    should_process = True
            except Exception as e:
                st.error(f"Error processing audio data: {str(e)}")
                logging.error(f"Error processing audio data: {str(e)}")
    
    with tab3:
        st.markdown("""
        ### WebRTC Recorder
        This recorder uses WebRTC for real-time audio streaming.
        """)
        
        # Create two columns for the recorder controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Create the webrtc streamer
            webrtc_ctx = webrtc_streamer(
                key="sendonly-audio",
                mode=WebRtcMode.SENDONLY,
                audio_receiver_size=1024,  # Increased from 256 to handle more frames
                rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
                media_stream_constraints={"video": False, "audio": True},
            )
            
            # Log WebRTC state
            logging.info(f"WebRTC state: playing={webrtc_ctx.state.playing}")
        
        with col2:
            # Recording controls
            if webrtc_ctx.state.playing:
                if st.button("START", key="start_button"):
                    st.session_state.audio_processor.start_recording()
                    st.session_state.recording_started = True
                    st.info("Recording... Press STOP when done.")
                
                if st.button("STOP", key="stop_button") and st.session_state.get("recording_started", False):
                    audio_data = st.session_state.audio_processor.stop_recording()
                    if audio_data:
                        audio_array, sample_rate = audio_data
                        audio_file_path = save_audio_from_array(audio_array, sample_rate)
                        if audio_file_path:
                            st.success("Recording saved! Click 'Process Recording' below.")
                            st.session_state.audio_file_path = audio_file_path
                            st.session_state.recording_started = False
                    else:
                        st.error("No audio was recorded. Please try again.")
            else:
                st.warning("Please start the WebRTC stream first.")
        
        # Use the audio processor to receive and process audio frames
        if webrtc_ctx.state.playing and webrtc_ctx.audio_receiver:
            
            # Process incoming audio frames
            try:
                # Process frames in larger batches to prevent queue overflow
                audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=0.1)
                if audio_frames and len(audio_frames) > 0:
                    for audio_frame in audio_frames:
                        st.session_state.audio_processor.process_frame(audio_frame)
                    logging.info(f"Processed {len(audio_frames)} audio frames in batch")

            except queue.Empty:
                # No frames received
                pass
            except Exception as e:
                logging.error(f"Error receiving audio frames: {e}")
        
        # Display recording progress if recording is in progress
        if st.session_state.get("recording_started", False) and webrtc_ctx.state.playing:
            frames_processed = st.session_state.audio_processor.frame_count
            recording_time = frames_processed / 16000  # Assuming 16kHz sample rate
            
            # Show progress bar
            st.progress(min(recording_time / 120, 1.0))  # Max 2 minutes
            st.text(f"Recording: {int(recording_time)} seconds ({frames_processed} frames)")
        
        # Set path from session state if available
        if "audio_file_path" in st.session_state:
            audio_file_path = st.session_state.audio_file_path
            # Indicate audio is ready for processing
            st.success("Recording ready. Enter a title and click Process Recording above.")
    
    with tab4:
        st.markdown("""
        ### Upload Audio File
        You can upload an existing audio file instead of recording.
        """)
        
        uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg"])
        
        if uploaded_file is not None:
            # Save the uploaded file
            audio_file_path = save_audio_file(uploaded_file.read())
            if audio_file_path:
                st.success("File uploaded successfully! Click 'Process Upload' below.")
                
                # Indicate upload is ready for processing
                should_process = True
            else:
                st.error("Error saving uploaded file")
    
    # Add a warning if no audio is provided
    if audio_file_path is None and should_process:
        st.warning("Please record or upload audio first")
        should_process = False
    
    return audio_file_path, should_process