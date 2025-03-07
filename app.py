import streamlit as st
import os
import logging
import datetime
import time
from config import APP_NAME, DEBUG
import openai
import tempfile
import uuid
import json
from flask import Flask, request, jsonify
import threading
import base64
import socket

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import MongoDB database first
# Only show one connection error instead of multiple
try:
    from utils.database import db as mongodb_db
    db_connected = mongodb_db.ensure_connected()
    if not db_connected:
        logging.error("MongoDB connection failed. Using local storage instead.")
        from utils.mock_database import db
    else:
        db = mongodb_db
        logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Error with MongoDB: {e}")
    from utils.mock_database import db

from utils.audio import get_audio_duration, save_audio_file
from utils.transcription import transcribe_audio
from utils.analysis import analyze_transcript, extract_participants
from models.meeting import Meeting, ActionItem
from components.recorder import record_audio_component
from components.transcript_view import display_transcript, display_summary, display_action_items
from components.action_items import add_action_item_component, edit_action_items
from components.sidebar import sidebar
from components.meeting_list import display_meeting_list
from utils.summarization import summarize_transcript
from utils.database import (
    initialize_db,
    save_meeting,
    get_all_meetings,
    get_meeting_by_id,
    delete_meeting
)
from config import OPENAI_API_KEY

# Flag to indicate if we're using mock database
using_mock_db = 'mock_database' in str(type(db))

# Initialize OpenAI API key
openai.api_key = OPENAI_API_KEY

# Initialize MongoDB connection
db = initialize_db()

# Create a Flask app for handling background API requests
flask_app = Flask(__name__)

# Create a global variable to store the flask server thread
flask_thread = None

def initialize_session_state():
    """Initialize session state variables"""
    if 'user_id' not in st.session_state:
        # For simplicity in personal version, use a fixed user ID
        st.session_state.user_id = "personal_user"
        
    if 'current_meeting' not in st.session_state:
        st.session_state.current_meeting = None
        
    if 'meetings' not in st.session_state:
        st.session_state.meetings = []
        

def new_meeting_view():
    """Render the new meeting creation view"""
    st.title("New Meeting")
    
    # Meeting title input
    meeting_title = st.text_input("Meeting Title", placeholder="Enter a title for this meeting")
    
    # Record or upload audio
    audio_file_path, should_process = record_audio_component()
    
    # Process recording based on the should_process flag or button click
    if audio_file_path and meeting_title:
        if should_process or st.button("Process Recording", type="primary", key="main_process_button"):
            process_meeting_recording(audio_file_path, meeting_title)
    elif audio_file_path:
        st.warning("Please enter a meeting title before processing.")
    elif should_process:
        st.warning("Please record or upload audio and enter a title before processing.")


def process_meeting_recording(audio_file_path, meeting_title):
    """Process a meeting recording"""
    try:
        logging.info(f"Processing meeting recording: {audio_file_path}")
        
        # 1. Transcribe the audio file
        transcript_text, timestamp, error_code = transcribe_audio(audio_file_path)
        
        if not transcript_text:
            if error_code == "QUOTA_EXCEEDED":
                st.error("OpenAI API quota exceeded. Please check your billing details at https://platform.openai.com/account/billing.")
            else:
                st.error("Transcription failed. Please check the logs for details.")
            return False
            
        logging.info(f"Transcription complete: {len(transcript_text)} characters")
        
        # 2. Summarize the transcript
        summary = summarize_transcript(transcript_text)
        
        if not summary:
            st.error("Summarization failed. Please check the logs for details.")
            return False
            
        logging.info("Summarization complete")
        
        # 3. Save to database
        meeting_data = {
            "title": meeting_title,
            "transcript": transcript_text,
            "summary": summary,
            "timestamp": timestamp,
            "audio_path": audio_file_path
        }
        
        meeting_id = save_meeting(meeting_data)
        
        if not meeting_id:
            st.error("Failed to save meeting data to database.")
            return False
            
        logging.info(f"Meeting saved with ID: {meeting_id}")
        
        # Set the current meeting in session state to view details
        st.session_state.current_meeting = get_meeting_by_id(meeting_id)
        st.success("Meeting processed successfully! View the details below.")
        
        # Force a rerun to show meeting details
        st.experimental_rerun()
        
        return True
        
    except Exception as e:
        logging.error(f"Error processing meeting recording: {str(e)}")
        st.error(f"An error occurred while processing the recording: {str(e)}")
        return False


def meeting_detail_view(meeting):
    """Render the meeting detail view"""
    st.title(meeting.title)
    
    # Meeting metadata
    col1, col2, col3 = st.columns(3)
    col1.metric("Date", meeting.created_at.strftime("%b %d, %Y"))
    
    duration_text = "Unknown"
    if meeting.duration:
        mins = int(meeting.duration // 60)
        secs = int(meeting.duration % 60)
        duration_text = f"{mins}m {secs}s"
    col2.metric("Duration", duration_text)
    
    participants_text = ", ".join(meeting.participants) if meeting.participants else "Unknown"
    col3.metric("Participants", participants_text)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Summary & Actions", "Full Transcript", "Edit Actions"])
    
    with tab1:
        # Meeting summary
        display_summary(meeting.summary)
        st.divider()
        
        # Action items
        display_action_items(meeting.action_items)
        
        # Add new action item
        new_item = add_action_item_component(meeting.id)
        if new_item:
            # Update the meeting object
            meeting.action_items.append(new_item)
    
    with tab2:
        # Full transcript
        display_transcript(meeting.transcript)
    
    with tab3:
        # Edit action items
        updated_items = edit_action_items(meeting.action_items, meeting.id)
        
        # Update meeting object if items changed
        if updated_items:
            meeting.action_items = updated_items


def main():
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    sidebar()
    
    # Main content area
    if st.session_state.current_meeting:
        meeting_detail_view(st.session_state.current_meeting)
    else:
        new_meeting_view()


# Define the upload route for the JavaScript recorder
@flask_app.route('/upload_audio', methods=['POST'])
def upload_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file found"}), 400
            
        audio_file = request.files['audio']
        audio_bytes = audio_file.read()
        
        # Save the audio bytes to a file
        audio_file_path = save_audio_file(audio_bytes)
        
        if not audio_file_path:
            return jsonify({"error": "Failed to save audio file"}), 500
            
        logging.info(f"Audio file saved at: {audio_file_path}")
        
        return jsonify({"file_path": audio_file_path, "success": True}), 200
    except Exception as e:
        logging.error(f"Error in /upload_audio: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Start the Flask server in a separate thread
def start_flask_server():
    from waitress import serve
    
    # Function to check if port is in use
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0
    
    # Check if port 5000 is already in use
    if is_port_in_use(5000):
        logging.info("Port 5000 is already in use, Flask server may already be running")
        return
    
    try:
        logging.info("Starting Flask server for background API requests...")
        serve(flask_app, host="127.0.0.1", port=5000)
    except Exception as e:
        logging.error(f"Failed to start Flask server: {e}")

# Use session state to ensure Flask server starts only once
if 'flask_server_started' not in st.session_state:
    st.session_state.flask_server_started = True
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    logging.info("Flask server thread started")


if __name__ == "__main__":
    main()