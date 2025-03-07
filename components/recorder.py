import streamlit as st
import os
import logging
import tempfile
from uuid import uuid4
from utils.whisper_stt import whisper_stt
from utils.audio import save_audio_file, cleanup_old_audio_files

def record_audio_component():
    """
    Streamlit component for recording audio using streamlit-mic-recorder
    
    Returns:
        tuple: (audio_file_path, should_process)
    """
    # Create a container for the audio recording components
    st.subheader("🎙️ Record or Upload Audio")
    
    # Create tabs for recording options
    tab1, tab2 = st.tabs(["Record Audio", "Upload File"])
    
    audio_file_path = None
    should_process = False
    
    with tab1:
        st.markdown("""
        ### Audio Recorder
        Click the button below to record audio using your microphone.
        """)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Display information about the recording
            st.markdown("""
            - Click **Start recording** to begin.
            - Speak clearly into your microphone.
            - Click **Stop recording** when finished.
            - The transcription will start automatically.
            """)
            
            # Use the whisper_stt function to record and transcribe
            transcript, audio_path = whisper_stt(
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                start_prompt="Start recording",
                stop_prompt="Stop recording",
                just_once=True,
                use_container_width=True,
                language='en',
                key="meeting_recorder"
            )
            
            # If we have an audio path, set it for processing
            if audio_path:
                audio_file_path = audio_path
                should_process = True
                st.success("Recording captured successfully!")
                
                # Show recording details if we have a path
                if os.path.exists(audio_file_path):
                    file_size = os.path.getsize(audio_file_path) / (1024 * 1024)  # Size in MB
                    st.info(f"Recording size: {file_size:.2f} MB")
            
            # Display transcript preview if available
            if transcript:
                with st.expander("Transcript Preview", expanded=False):
                    st.write(transcript[:500] + "..." if len(transcript) > 500 else transcript)
        
    with tab2:
        st.markdown("""
        ### Upload Audio File
        You can upload an existing audio file instead of recording.
        """)
        
        uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "m4a", "ogg", "webm"])
        
        if uploaded_file is not None:
            # Save the uploaded file
            audio_file_path = save_audio_file(uploaded_file.read())
            if audio_file_path:
                st.success("File uploaded successfully! Click 'Process Recording' below.")
                
                # Indicate upload is ready for processing
                should_process = True
                
                # Show file details
                file_size = os.path.getsize(audio_file_path) / (1024 * 1024)  # Size in MB
                st.info(f"File size: {file_size:.2f} MB")
            else:
                st.error("Error saving uploaded file")
    
    # Clean up old audio files to prevent disk space issues
    cleanup_old_audio_files()
    
    # Add a warning if no audio is provided but should_process is True
    if audio_file_path is None and should_process:
        st.warning("Please record or upload audio first")
        should_process = False
    
    return audio_file_path, should_process