import streamlit as st
import datetime
from models.meeting import ActionItem


def add_action_item_component(meeting_id=None):
    """
    Component for manually adding new action items
    
    Args:
        meeting_id (str, optional): The ID of the meeting to add the action item to
        
    Returns:
        ActionItem or None: The new action item if created, otherwise None
    """
    st.subheader("Add Action Item")
    
    with st.form("add_action_item_form"):
        description = st.text_area("Task Description", placeholder="Describe the action item...")
        
        col1, col2 = st.columns(2)
        
        with col1:
            assigned_to = st.text_input("Assigned To", placeholder="Person responsible (optional)")
        
        with col2:
            due_date = st.date_input(
                "Due Date",
                value=None,
                min_value=datetime.date.today(),
                format="YYYY-MM-DD"
            )
        
        status = st.selectbox(
            "Status",
            options=["pending", "in progress", "completed"],
            index=0
        )
        
        submitted = st.form_submit_button("Add Action Item")
        
        if submitted and description:
            # Convert due_date from date to datetime if it exists
            due_datetime = None
            if due_date is not None:
                due_datetime = datetime.datetime.combine(due_date, datetime.time())
            
            new_action_item = ActionItem(
                description=description,
                assigned_to=assigned_to if assigned_to else None,
                due_date=due_datetime,
                status=status
            )
            
            # If meeting_id is provided, we can add this to the database
            if meeting_id:
                try:
                    from utils.database import db
                    
                    # Get the current meeting
                    meeting = db.get_meeting(meeting_id)
                    
                    if meeting:
                        # Get current action items
                        action_items = meeting.get("action_items", [])
                        
                        # Add the new one
                        action_items.append(new_action_item.to_dict())
                        
                        # Update the meeting
                        db.update_meeting(meeting_id, action_items=action_items)
                        
                        st.success("Action item added successfully!")
                except Exception as e:
                    st.error(f"Error adding action item: {e}")
            
            return new_action_item
    
    return None


def edit_action_items(action_items, meeting_id=None):
    """
    Component for editing existing action items
    
    Args:
        action_items (list): List of ActionItem objects
        meeting_id (str, optional): The ID of the meeting
        
    Returns:
        list: Updated list of ActionItem objects
    """
    st.subheader("Edit Action Items")
    
    updated_items = []
    
    for i, item in enumerate(action_items):
        with st.expander(f"Action Item {i+1}: {item.description[:50]}..."):
            description = st.text_area(
                "Description",
                value=item.description,
                key=f"edit_desc_{i}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                assigned_to = st.text_input(
                    "Assigned To",
                    value=item.assigned_to or "",
                    key=f"edit_assigned_{i}"
                )
            
            with col2:
                # Get current due date or today
                current_date = item.due_date.date() if item.due_date else None
                
                due_date = st.date_input(
                    "Due Date",
                    value=current_date,
                    key=f"edit_date_{i}",
                    format="YYYY-MM-DD"
                )
            
            status = st.selectbox(
                "Status",
                options=["pending", "in progress", "completed"],
                index=["pending", "in progress", "completed"].index(item.status),
                key=f"edit_status_{i}"
            )
            
            if st.button("Delete Item", key=f"delete_{i}"):
                # Skip this item by not adding it to updated_items
                st.success("Item deleted!")
                continue
            
            # Convert due_date from date to datetime if it exists
            due_datetime = None
            if due_date is not None:
                due_datetime = datetime.datetime.combine(due_date, datetime.time())
            
            # Create updated item
            updated_item = ActionItem(
                description=description,
                assigned_to=assigned_to if assigned_to else None,
                due_date=due_datetime,
                status=status
            )
            
            updated_items.append(updated_item)
    
    # Add button to save changes to database
    if meeting_id and st.button("Save All Changes"):
        try:
            from utils.database import db
            
            # Convert action items to dict for storage
            action_items_dict = [item.to_dict() for item in updated_items]
            
            # Update the meeting
            db.update_meeting(meeting_id, action_items=action_items_dict)
            
            st.success("Changes saved successfully!")
        except Exception as e:
            st.error(f"Error saving changes: {e}")
    
    return updated_items