"""
Whisper speech-to-text integration using streamlit-mic-recorder.
This module provides a simplified and reliable way to record audio and
transcribe it using OpenAI Whisper.
"""

from streamlit_mic_recorder import mic_recorder
import streamlit as st
import io
from openai import OpenAI
import os
import logging
import tempfile
from uuid import uuid4


def whisper_stt(openai_api_key=None, start_prompt="Start recording", stop_prompt="Stop recording", 
                just_once=False, use_container_width=False, language=None, callback=None, 
                args=(), kwargs=None, key=None):
    """
    Record audio from the microphone and transcribe it using OpenAI's Whisper API.
    
    Args:
        openai_api_key (str, optional): OpenAI API key. If None, uses environment variable.
        start_prompt (str, optional): Text for the start recording button.
        stop_prompt (str, optional): Text for the stop recording button.
        just_once (bool, optional): If True, only record once.
        use_container_width (bool, optional): If True, use the full container width.
        language (str, optional): Language code for transcription.
        callback (callable, optional): Function to call after transcription.
        args (tuple, optional): Arguments for the callback function.
        kwargs (dict, optional): Keyword arguments for the callback function.
        key (str, optional): Unique key for the component.
    
    Returns:
        str: Transcribed text or None if no recording was made.
    """
    logging.info("Initializing Whisper STT component")
    
    # Initialize OpenAI client
    if 'openai_client' not in st.session_state:
        st.session_state.openai_client = OpenAI(api_key=openai_api_key or os.getenv('OPENAI_API_KEY'))
    
    # Initialize session state variables
    if '_last_speech_to_text_transcript_id' not in st.session_state:
        st.session_state._last_speech_to_text_transcript_id = 0
    if '_last_speech_to_text_transcript' not in st.session_state:
        st.session_state._last_speech_to_text_transcript = None
    if key and key + '_output' not in st.session_state:
        st.session_state[key + '_output'] = None
    
    # Record audio using streamlit-mic-recorder
    audio = mic_recorder(
        start_prompt=start_prompt, 
        stop_prompt=stop_prompt, 
        just_once=just_once,
        use_container_width=use_container_width,
        format="webm", 
        key=key
    )
    
    new_output = False
    output = None
    audio_file_path = None
    
    if audio is not None:
        id = audio['id']
        new_output = (id > st.session_state._last_speech_to_text_transcript_id)
        
        if new_output:
            output = None
            st.session_state._last_speech_to_text_transcript_id = id
            audio_bio = io.BytesIO(audio['bytes'])
            audio_bio.name = 'audio.webm'
            
            # Save audio file for processing
            temp_dir = tempfile.gettempdir()
            audio_file_path = os.path.join(temp_dir, f"recording_{uuid4()}.webm")
            
            with open(audio_file_path, 'wb') as f:
                f.write(audio['bytes'])
            
            logging.info(f"Audio saved to temporary file: {audio_file_path}")
            
            # Transcribe using OpenAI Whisper
            success = False
            err = 0
            while not success and err < 3:  # Retry up to 3 times in case of OpenAI server error
                try:
                    logging.info("Sending audio to OpenAI Whisper for transcription")
                    transcript = st.session_state.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_bio,
                        language=language
                    )
                except Exception as e:
                    logging.error(f"Whisper transcription error: {str(e)}")
                    err += 1
                else:
                    success = True
                    output = transcript.text
                    st.session_state._last_speech_to_text_transcript = output
                    logging.info(f"Transcription successful: {len(output)} characters")
        elif not just_once:
            output = st.session_state._last_speech_to_text_transcript
    
    # Update session state and call callback if needed
    if key:
        st.session_state[key + '_output'] = output
    if new_output and callback:
        callback(*args, **(kwargs or {}))
    
    return output, audio_file_path
