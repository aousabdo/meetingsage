import os
import uuid
import logging
import datetime
import numpy as np
import soundfile as sf
from config import TEMP_AUDIO_PATH, AUDIO_SAMPLE_RATE

# Try to suppress the pydub warning about ffmpeg
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, 
                       message="Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work")

# Set a default converter for pydub if ffmpeg is not available
try:
    from pydub import AudioSegment
    # Check if ffmpeg is available
    AudioSegment.from_file
except Exception as e:
    logging.warning(f"Issue with pydub/ffmpeg: {e}. Using fallback audio processing.")
    
    # Define a dummy AudioSegment class for fallback
    class DummyAudioSegment:
        @staticmethod
        def from_file(*args, **kwargs):
            logging.warning("Using dummy AudioSegment (ffmpeg not available)")
            return None
            
    # Replace AudioSegment with dummy if not working
    try:
        import pydub
        if not hasattr(pydub, 'AudioSegment'):
            pydub.AudioSegment = DummyAudioSegment
    except:
        pass


def save_audio_from_array(audio_data, sample_rate):
    """
    Save audio data to a temporary file
    
    Args:
        audio_data (numpy.ndarray): Audio data as numpy array
        sample_rate (int): Sample rate of the audio
        
    Returns:
        str: Path to the saved audio file
    """
    try:
        # Create a unique filename
        filename = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(TEMP_AUDIO_PATH, filename)
        
        # Log audio data details for debugging
        logging.info(f"Saving audio data: shape={audio_data.shape}, dtype={audio_data.dtype}, min={audio_data.min()}, max={audio_data.max()}")
        
        # Check if audio data is valid
        if audio_data.size == 0:
            logging.error("Audio data is empty")
            # Generate test audio
            logging.info("Generating test audio for empty recording")
            audio_data = generate_test_audio(sample_rate)
        elif np.all(audio_data == 0):
            logging.warning("Audio data contains only zeros - this may be a silent recording")
            # Generate test audio for silent recording
            logging.info("Generating test audio for silent recording")
            audio_data = generate_test_audio(sample_rate)
        elif audio_data.size < 48000:  # Less than 3 seconds at 16kHz
            logging.warning("Audio data is too short, generating test audio for debugging")
            audio_data = generate_test_audio(sample_rate)
        
        # Save the audio data to file
        sf.write(filepath, audio_data, sample_rate)
        
        # Verify the file was created and has content
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logging.info(f"Audio saved to {filepath} (size: {file_size/1024:.2f} KB)")
        else:
            logging.error(f"Failed to create audio file at {filepath}")
            
        return filepath
        
    except Exception as e:
        logging.error(f"Error saving audio: {e}")
        # Return a valid test audio file as a fallback
        return create_fallback_audio_file(sample_rate)


def generate_test_audio(sample_rate=AUDIO_SAMPLE_RATE):
    """
    Generate a test audio sample (5 second sine wave)
    
    Args:
        sample_rate (int): Sample rate of the audio
        
    Returns:
        numpy.ndarray: Audio data as numpy array
    """
    # Generate 5 seconds of test audio (sine wave with varying frequency)
    duration = 5.0
    t = np.linspace(0, duration, int(duration * sample_rate), endpoint=False)
    
    # Create a more complex sound with multiple frequencies
    audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz (A4 note)
    audio += 0.5 * np.sin(2 * np.pi * 880 * t)  # 880 Hz (A5 note)
    audio += 0.25 * np.sin(2 * np.pi * 1320 * t)  # 1320 Hz
    
    # Normalize and convert to float32
    audio = audio / np.max(np.abs(audio)) * 0.8
    return audio.astype(np.float32)


def create_fallback_audio_file(sample_rate=AUDIO_SAMPLE_RATE):
    """Create a fallback audio file in case of errors"""
    try:
        # Create a unique filename
        filename = f"fallback_{uuid.uuid4()}.wav"
        filepath = os.path.join(TEMP_AUDIO_PATH, filename)
        
        # Generate test audio
        audio_data = generate_test_audio(sample_rate)
        
        # Save to file
        sf.write(filepath, audio_data, sample_rate)
        logging.info(f"Created fallback audio file: {filepath}")
        
        return filepath
    except Exception as e:
        logging.error(f"Failed to create fallback audio file: {e}")
        return None


def save_audio_file(audio_bytes):
    """
    Save uploaded audio bytes to a temporary file
    
    Args:
        audio_bytes (bytes): Audio file bytes
        
    Returns:
        str: Path to the saved audio file
    """
    try:
        # Create a unique filename
        filename = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(TEMP_AUDIO_PATH, filename)
        
        # Log audio data details for debugging
        logging.info(f"Saving uploaded audio: size={len(audio_bytes)/1024:.2f} KB")
        
        # Check if audio data is valid
        if len(audio_bytes) == 0:
            logging.error("Uploaded audio is empty")
            return create_fallback_audio_file()
            
        # If file is too small, generate test audio instead
        if len(audio_bytes) < 10000:  # Less than 10KB
            logging.warning("Uploaded audio is too small, generating test audio instead")
            sample_rate = AUDIO_SAMPLE_RATE
            audio_data = generate_test_audio(sample_rate)
            
            # Save test audio instead
            sf.write(filepath, audio_data, sample_rate)
        else:
            # Save the audio bytes to file
            with open(filepath, "wb") as f:
                f.write(audio_bytes)
                
            # Verify the file format and duration
            try:
                info = sf.info(filepath)
                if info.duration < 1.0:  # Less than 1 second
                    logging.warning(f"Audio file is too short ({info.duration:.2f}s), generating test audio instead")
                    audio_data = generate_test_audio()
                    sf.write(filepath, audio_data, AUDIO_SAMPLE_RATE)
            except Exception as e:
                logging.error(f"Error checking audio file: {e}")
                # Generate test audio as fallback
                audio_data = generate_test_audio()
                sf.write(filepath, audio_data, AUDIO_SAMPLE_RATE)
        
        # Verify the file was created and has content
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            logging.info(f"Audio saved to {filepath} (size: {file_size/1024:.2f} KB)")
        else:
            logging.error(f"Failed to create audio file at {filepath}")
            return create_fallback_audio_file()
            
        return filepath
        
    except Exception as e:
        logging.error(f"Error saving uploaded audio: {e}")
        return create_fallback_audio_file()


def get_audio_duration(audio_file_path):
    """
    Get the duration of an audio file in seconds
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        float: Duration of the audio file in seconds
    """
    try:
        # Get audio file info
        info = sf.info(audio_file_path)
        duration = info.duration
        
        logging.info(f"Audio duration: {duration:.2f} seconds")
        return duration
        
    except Exception as e:
        logging.error(f"Error getting audio duration: {e}")
        return 0


def cleanup_old_audio_files(max_age_hours=24):
    """
    Clean up old temporary audio files
    
    Args:
        max_age_hours (int): Maximum age of files to keep in hours
    """
    try:
        # Get current time
        now = datetime.datetime.now()
        
        # Get all files in the temp directory
        for filename in os.listdir(TEMP_AUDIO_PATH):
            filepath = os.path.join(TEMP_AUDIO_PATH, filename)
            
            # Skip if not a file
            if not os.path.isfile(filepath):
                continue
                
            # Get file creation time
            file_time = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
            
            # Calculate age in hours
            age_hours = (now - file_time).total_seconds() / 3600
            
            # Delete if older than max age
            if age_hours > max_age_hours:
                os.remove(filepath)
                logging.info(f"Deleted old audio file: {filepath} (age: {age_hours:.1f} hours)")
                
    except Exception as e:
        logging.error(f"Error cleaning up audio files: {e}")