import streamlit as st
import re


def display_transcript(transcript):
    """
    Display the meeting transcript with formatting
    
    Args:
        transcript (str): The meeting transcript text
    """
    if not transcript:
        st.info("No transcript available.")
        return
    
    st.subheader("Meeting Transcript")
    
    # Create an expandable container for the transcript
    with st.expander("Show full transcript", expanded=False):
        # Try to detect speaker changes in the transcript
        try:
            # Look for common speaker patterns like "John: Hello" or "[John]: Hello"
            speaker_pattern = re.compile(r'(?:\[?([A-Z][a-zA-Z\s]*):|\(?([A-Z][a-zA-Z\s]*)\)?:)')
            formatted_transcript = transcript
            
            # If we detect speaker patterns, add some formatting
            if speaker_pattern.search(transcript):
                # Replace speaker patterns with markdown bold formatting
                formatted_transcript = speaker_pattern.sub(r'**\1\2:**', transcript)
                
            # Display the formatted transcript
            st.markdown(formatted_transcript)
            
        except Exception:
            # If there's any issue with the regex, just show the plain transcript
            st.text_area("Transcript", transcript, height=400)
    
    # Add a download button for the transcript
    st.download_button(
        label="Download Transcript",
        data=transcript,
        file_name="meeting_transcript.txt",
        mime="text/plain"
    )


def display_summary(summary):
    """
    Display the meeting summary
    
    Args:
        summary (str): The meeting summary text
    """
    if not summary:
        st.info("No summary available.")
        return
    
    st.subheader("Meeting Summary")
    st.write(summary)
    

def display_action_items(action_items):
    """
    Display the action items from the meeting
    
    Args:
        action_items (list): List of ActionItem objects
    """
    if not action_items:
        st.info("No action items identified.")
        return
    
    st.subheader("Action Items")
    
    # Create a table for action items
    columns = st.columns([3, 1, 1, 1])
    columns[0].write("**Task**")
    columns[1].write("**Assigned To**")
    columns[2].write("**Due Date**")
    columns[3].write("**Status**")
    
    st.divider()
    
    for item in action_items:
        cols = st.columns([3, 1, 1, 1])
        
        # Task description
        cols[0].write(item.description)
        
        # Assigned person
        cols[1].write(item.assigned_to if item.assigned_to else "—")
        
        # Due date
        if item.due_date:
            cols[2].write(item.due_date.strftime("%Y-%m-%d"))
        else:
            cols[2].write("—")
        
        # Status with selectbox for changing
        status_options = ["pending", "in progress", "completed"]
        current_index = status_options.index(item.status) if item.status in status_options else 0
        new_status = cols[3].selectbox(
            "Status",
            options=status_options,
            index=current_index,
            key=f"status_{id(item)}",
            label_visibility="collapsed"
        )
        
        # Update the status if changed
        if new_status != item.status:
            item.status = new_status
            
        st.divider()
    
    # Add an export button for action items
    export_action_items(action_items)


def export_action_items(action_items):
    """
    Create export options for action items
    
    Args:
        action_items (list): List of ActionItem objects
    """
    # Format as CSV
    csv_content = "Task,Assigned To,Due Date,Status\n"
    for item in action_items:
        due_date = item.due_date.strftime("%Y-%m-%d") if item.due_date else ""
        csv_content += f"\"{item.description}\",\"{item.assigned_to or ''}\",{due_date},{item.status}\n"
    
    # Format as plain text
    text_content = "Action Items:\n\n"
    for i, item in enumerate(action_items, 1):
        assigned = f" (Assigned to: {item.assigned_to})" if item.assigned_to else ""
        due = f" (Due: {item.due_date.strftime('%Y-%m-%d')})" if item.due_date else ""
        status = f" [{item.status}]"
        text_content += f"{i}. {item.description}{assigned}{due}{status}\n"
    
    # Download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="Export as CSV",
            data=csv_content,
            file_name="action_items.csv",
            mime="text/csv"
        )
    
    with col2:
        st.download_button(
            label="Export as Text",
            data=text_content,
            file_name="action_items.txt",
            mime="text/plain"
        )