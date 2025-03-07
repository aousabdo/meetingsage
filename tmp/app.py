import streamlit as st
from whisper_stt import whisper_stt
import os

st.title("Whisper Speech-to-Text Application")

text = whisper_stt(
    openai_api_key=os.getenv('OPENAI_API_KEY'),  # Uses the OPENAI_API_KEY environment variable
    language='en'         # Specify the language code as needed
)

if text:
    st.write("Transcription:")
    st.write(text)
