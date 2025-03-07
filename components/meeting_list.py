import streamlit as st
import pandas as pd
import datetime
from models.meeting import Meeting

def display_meeting_list():
    """Display a list of meetings and allow selection
    
    Returns:
        Meeting: The selected meeting or None
    """
    # Get meeting data from session state
    try:
        from utils.database import get_all_meetings
        
        # Get user meetings
        user_id = st.session_state.get('user_id', 'personal_user')
        meetings = get_all_meetings(user_id)
        
        if not meetings:
            st.info("No meetings found. Record a new meeting to get started!")
            return None
        
        # Convert to list of Meeting objects
        meeting_objects = []
        for meeting in meetings:
            if isinstance(meeting, dict):
                meeting_obj = Meeting.from_dict(meeting)
            else:
                meeting_obj = meeting
                
            meeting_objects.append(meeting_obj)
        
        # Create a dataframe for display
        meeting_data = []
        for meeting in meeting_objects:
            meeting_duration = "Unknown"
            if meeting.duration:
                # Check if duration is valid
                if isinstance(meeting.duration, (int, float)) and meeting.duration > 0:
                    mins = int(meeting.duration // 60)
                    secs = int(meeting.duration % 60)
                    meeting_duration = f"{mins}m {secs}s"
                
            participants = ", ".join(meeting.participants) if meeting.participants else "Unknown"
            
            meeting_data.append({
                "ID": meeting.id,
                "Title": meeting.title,
                "Date": meeting.created_at.strftime("%b %d, %Y") if meeting.created_at else "Unknown",
                "Duration": meeting_duration,
                "Participants": participants[:50] + "..." if len(participants) > 50 else participants,
                "Object": meeting
            })
        
        # Create a DataFrame for display
        df = pd.DataFrame(meeting_data)
        
        # Display meetings in a table
        st.subheader("Your Meetings")
        
        # Create columns for each meeting card
        cols = st.columns(3)
        selected_meeting = None
        
        # Show meeting cards
        for i, row in enumerate(meeting_data):
            col = cols[i % 3]
            with col:
                with st.container(border=True):
                    st.markdown(f"### {row['Title']}")
                    st.text(f"Date: {row['Date']}")
                    st.text(f"Duration: {row['Duration']}")
                    
                    if st.button("View Details", key=f"view_{row['ID']}", use_container_width=True):
                        selected_meeting = row["Object"]
        
        return selected_meeting
        
    except Exception as e:
        st.error(f"Error loading meetings: {str(e)}")
        st.exception(e)
        return None 