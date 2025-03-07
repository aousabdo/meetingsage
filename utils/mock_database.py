import os
import json
import logging
import datetime
import uuid
from pathlib import Path

class MockDatabase:
    """
    A simple file-based mock database implementation that mimics the MongoDB Database class
    for development or when MongoDB is unavailable
    """
    def __init__(self):
        self.data_dir = Path("mock_db")
        self.meetings_file = self.data_dir / "meetings.json"
        self.users_file = self.data_dir / "users.json"
        self.ensure_data_files()
        self.meetings = []
        self.users = []
        self.load_data()
        logging.info("Initialized mock database")

    def ensure_data_files(self):
        """Ensure data directory and files exist"""
        # Create directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create meetings file if it doesn't exist
        if not self.meetings_file.exists():
            with open(self.meetings_file, 'w') as f:
                json.dump([], f)
        
        # Create users file if it doesn't exist
        if not self.users_file.exists():
            with open(self.users_file, 'w') as f:
                json.dump([], f)

    def load_data(self):
        """Load data from files"""
        try:
            with open(self.meetings_file, 'r') as f:
                self.meetings = json.load(f)
            
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        except Exception as e:
            logging.error(f"Error loading mock database data: {e}")

    def save_data(self):
        """Save data to files"""
        try:
            with open(self.meetings_file, 'w') as f:
                json.dump(self.meetings, f, default=self._datetime_serializer)
            
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, default=self._datetime_serializer)
        except Exception as e:
            logging.error(f"Error saving mock database data: {e}")

    def _datetime_serializer(self, obj):
        """Helper to serialize datetime objects to JSON"""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def _datetime_deserializer(self, d):
        """Convert string dates back to datetime objects"""
        for k, v in d.items():
            if k in ["created_at", "updated_at", "last_login"] and v:
                try:
                    d[k] = datetime.datetime.fromisoformat(v)
                except:
                    pass
        return d

    def ensure_connected(self):
        """Mock connection always succeeds"""
        return True

    def connect(self):
        """Mock connection always succeeds"""
        return True

    def close(self):
        """Save data before closing"""
        self.save_data()

    # User operations
    def create_user(self, username, email, password_hash):
        """Create a new user"""
        user_id = str(uuid.uuid4())
        user = {
            "_id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "last_login": None
        }
        self.users.append(user)
        self.save_data()
        return user_id

    def get_user(self, username=None, user_id=None, email=None):
        """Retrieve user by username, id or email"""
        for user in self.users:
            if username and user.get("username") == username:
                return self._datetime_deserializer(user)
            elif user_id and user.get("_id") == user_id:
                return self._datetime_deserializer(user)
            elif email and user.get("email") == email:
                return self._datetime_deserializer(user)
        return None

    def update_user_login(self, user_id):
        """Update user's last login time"""
        for user in self.users:
            if user.get("_id") == user_id:
                user["last_login"] = datetime.datetime.now()
                self.save_data()
                break

    # Meeting operations
    def save_meeting(self, title, user_id, audio_file=None, transcript=None, summary=None, 
                    action_items=None, participants=None, duration=None):
        """Save a new meeting"""
        meeting_id = str(uuid.uuid4())
        meeting = {
            "_id": meeting_id,
            "title": title,
            "user_id": user_id,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "audio_file": audio_file,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_items or [],
            "participants": participants or [],
            "duration": duration
        }
        self.meetings.append(meeting)
        self.save_data()
        return meeting_id

    def update_meeting(self, meeting_id, **kwargs):
        """Update meeting fields"""
        for meeting in self.meetings:
            if meeting.get("_id") == meeting_id:
                kwargs["updated_at"] = datetime.datetime.now()
                meeting.update(kwargs)
                self.save_data()
                break

    def get_meeting(self, meeting_id):
        """Get a meeting by ID"""
        for meeting in self.meetings:
            if meeting.get("_id") == meeting_id:
                return self._datetime_deserializer(meeting.copy())
        return None

    def get_user_meetings(self, user_id):
        """Get all meetings for a user"""
        user_meetings = [self._datetime_deserializer(m.copy()) for m in self.meetings if m.get("user_id") == user_id]
        return sorted(user_meetings, key=lambda x: x.get("created_at", datetime.datetime.min), reverse=True)

    def delete_meeting(self, meeting_id):
        """Delete a meeting"""
        self.meetings = [m for m in self.meetings if m.get("_id") != meeting_id]
        self.save_data()

# Create a singleton instance
db = MockDatabase() 