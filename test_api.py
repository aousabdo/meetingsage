import os
import mimetypes
from pathlib import Path
from openai import OpenAI
from config import OPENAI_API_KEY, WHISPER_MODEL

# Initialize client with API key from config
client = OpenAI(api_key=OPENAI_API_KEY)

# File path - now using the converted MP3 file
audio_file_path = "/Users/aousabdo/Downloads/Meeting_with_Doug_March_6_2025_converted.mp3"

# Debug file info
file_path = Path(audio_file_path)
print(f"File exists: {file_path.exists()}")
print(f"File size: {file_path.stat().st_size / (1024*1024):.2f} MB")
print(f"MIME type: {mimetypes.guess_type(audio_file_path)[0]}")
print(f"File extension: {file_path.suffix}")

# Check file extension
if not audio_file_path.lower().endswith(('.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.wav', '.webm')):
    print(f"Warning: File extension {Path(audio_file_path).suffix} may not be supported")

try:
    # Let's try to open a small test WAV file first to check API connection
    print("\nAttempting to transcribe the audio file...")
    
    with open(audio_file_path, "rb") as audio_file:
        # Correct API call without the filename parameter
        transcription = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=audio_file,
            response_format="text"
        )
    
    # Print the result
    print("\nTranscription successful:")
    print(transcription)
    
except Exception as e:
    print(f"\nError during transcription: {e}")
    
    print("\nLet's try to get more information about the file...")
    
    # Run system command to get more file info
    import subprocess
    try:
        result = subprocess.run(['file', audio_file_path], capture_output=True, text=True)
        print(f"\nFile command output: {result.stdout}")
    except Exception as file_error:
        print(f"Error getting file info: {file_error}")
    
    # Suggest potential fixes
    print("\nPossible solutions to try:")
    print("1. The file might be in an unsupported format despite having a supported extension")
    print("2. Try converting the file to a different format using:")
    print(f"   ffmpeg -i \"{audio_file_path}\" -ar 16000 converted_audio.mp3")
    print("3. Check that your API key has access to the Audio API")
    print("4. Try a smaller audio file first to test the API connection")