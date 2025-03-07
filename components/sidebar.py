import streamlit as st
import logging
from config import APP_NAME
from models.meeting import Meeting

def sidebar():
    """Render the sidebar"""
    st.sidebar.title(f"🎙️ {APP_NAME}")
    
    # Check if we're using mock database
    using_mock_db = 'mock_database' in str(type(st.session_state.get('db', {})))
    
    # Show database connection status
    if using_mock_db:
        st.sidebar.warning("Using local file storage (MongoDB connection failed)")
    else:
        st.sidebar.success("Connected to MongoDB database")
    
    # New meeting button
    if st.sidebar.button("➕ New Meeting", use_container_width=True):
        st.session_state.current_meeting = None
        st.rerun()
    
    st.sidebar.divider()
    
    # Load user's meetings
    try:
        from utils.database import get_all_meetings
        
        if not st.session_state.get('meetings'):
            # Get all meetings for the current user
            user_id = st.session_state.get('user_id', 'personal_user')
            meetings = get_all_meetings(user_id)
            if meetings:
                st.session_state.meetings = meetings
                
        # Display meeting list
        st.sidebar.subheader("Previous Meetings")
        
        if not st.session_state.get('meetings'):
            st.sidebar.info("No previous meetings found.")
        else:
            for meeting in st.session_state.meetings:
                if isinstance(meeting, dict):
                    meeting_obj = Meeting.from_dict(meeting)
                else:
                    meeting_obj = meeting
                    
                meeting_date = meeting_obj.created_at.strftime("%b %d, %Y")
                
                # Create a button for each meeting
                if st.sidebar.button(
                    f"{meeting_obj.title} ({meeting_date})",
                    key=f"meeting_{meeting_obj.id}",
                    use_container_width=True
                ):
                    st.session_state.current_meeting = meeting_obj
                    st.rerun()
    
    except Exception as e:
        st.sidebar.error(f"Error loading meetings: {e}")
        logging.error(f"Error loading meetings: {e}")
    
    st.sidebar.divider()
    st.sidebar.info(
        "MeetingSage helps you record, transcribe, and extract insights from your meetings."
    ) 