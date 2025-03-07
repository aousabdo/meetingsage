import os
import logging
from config import OPENAI_API_KEY, WHISPER_MODEL

def transcribe_audio(audio_file_path):
    """
    Transcribe an audio file using OpenAI's Whisper API
    
    Args:
        audio_file_path (str): Path to the audio file to transcribe
        
    Returns:
        str: The transcribed text
    """
    try:
        if not os.path.exists(audio_file_path):
            logging.error(f"Audio file not found: {audio_file_path}")
            return None, None, None
        
        # Check file size - Whisper has a 25MB limit
        file_size_mb = os.path.getsize(audio_file_path) / (1024 * 1024)
        if file_size_mb > 25:
            logging.error(f"Audio file too large: {file_size_mb:.2f}MB (max 25MB)")
            return None, None, None
        
        # Skip checking for small files - our audio.py module now ensures valid audio files
        
        # Check if API key is set
        if not OPENAI_API_KEY:
            logging.error("OpenAI API key is not set in environment variables")
            return None, None, None
        
        logging.info(f"Transcribing audio file: {audio_file_path} (size: {file_size_mb:.2f}MB)")
        
        # Import OpenAI here to handle potential import errors
        import openai
        import datetime
        
        # Use only the new OpenAI client API (v1.0+)
        try:
            # Log the API key being used (partially obscured for security)
            if OPENAI_API_KEY:
                key_start = OPENAI_API_KEY[:10]
                key_end = OPENAI_API_KEY[-5:]
                logging.info(f"Using OpenAI API key: {key_start}...{key_end}")
            else:
                logging.error("No OpenAI API key available")
                return None, None, None
                
            logging.info("Creating a fresh OpenAI client API v1.0+")
            # Force a fresh client each time by explicitly passing the API key
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            try:
                # Ensure the file is open in binary mode
                with open(audio_file_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model=WHISPER_MODEL,
                        file=audio_file
                    )
                    
                transcript = response.text
                    
                if not transcript:
                    logging.error("Transcription completed but returned empty text")
                    return None, None, None
                    
                logging.info(f"Transcription completed. Length: {len(transcript)} characters")
                # Return the transcript and the current timestamp
                return transcript, datetime.datetime.now(), None
                
            except Exception as e:
                error_str = str(e)
                logging.error(f"Error with OpenAI API v1.0+ client: {error_str}")
                logging.error("If you're using an older version of OpenAI, please upgrade with: pip install --upgrade openai")
                
                # Check for quota issues
                if 'insufficient_quota' in error_str or 'exceeded your current quota' in error_str:
                    return None, None, "QUOTA_EXCEEDED"
                return None, None, None
        
        except Exception as e:
            logging.error(f"Error transcribing audio: {str(e)}")
            # Print more detailed error information
            import traceback
            logging.error(traceback.format_exc())
            return None, None, None
    
    except Exception as e:
        logging.error(f"Error transcribing audio: {str(e)}")
        # Print more detailed error information
        import traceback
        logging.error(traceback.format_exc())
        return None, None, None