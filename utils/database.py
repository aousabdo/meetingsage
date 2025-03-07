from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import datetime
import logging
import urllib.parse
from config import MONGODB_URI, MONGODB_DB_NAME, MEETINGS_COLLECTION, USERS_COLLECTION

class Database:
    def __init__(self, auto_connect=False):
        self.client = None
        self.db = None
        self.meetings = None
        self.users = None
        if auto_connect:
            self.connect()

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            # Parse the URI to properly encode username and password
            if MONGODB_URI and MONGODB_URI.startswith('mongodb'):
                parts = MONGODB_URI.split('://')
                if len(parts) == 2 and '@' in parts[1]:
                    prefix = parts[0] + '://'
                    auth_host = parts[1].split('@', 1)
                    if ':' in auth_host[0]:
                        user_pass = auth_host[0].split(':', 1)
                        encoded_uri = f"{prefix}{urllib.parse.quote_plus(user_pass[0])}:{urllib.parse.quote_plus(user_pass[1])}@{auth_host[1]}"
                    else:
                        encoded_uri = MONGODB_URI
                else:
                    encoded_uri = MONGODB_URI
            else:
                encoded_uri = MONGODB_URI
                
            # Connect with the encoded URI
            self.client = MongoClient(encoded_uri)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[MONGODB_DB_NAME]
            self.meetings = self.db[MEETINGS_COLLECTION]
            self.users = self.db[USERS_COLLECTION]
            logging.info("Connected to MongoDB successfully")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            return False

    def ensure_connected(self):
        """Ensure database is connected before operations"""
        if self.client is None:
            return self.connect()
        return True

    def close(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            logging.info("Closed MongoDB connection")

    # User operations
    def create_user(self, username, email, password_hash):
        """Create a new user"""
        if not self.ensure_connected():
            raise ConnectionFailure("Database connection failed")
            
        user = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.datetime.now(),
            "updated_at": datetime.datetime.now(),
            "last_login": None
        }
        result = self.users.insert_one(user)
        return str(result.inserted_id)

    def get_user(self, username=None, user_id=None, email=None):
        """Retrieve user by username, id or email"""
        if not self.ensure_connected():
            raise ConnectionFailure("Database connection failed")
            
        if username:
            return self.users.find_one({"username": username})
        elif user_id:
            from bson.objectid import ObjectId
            return self.users.find_one({"_id": ObjectId(user_id)})
        elif email:
            return self.users.find_one({"email": email})
        return None

    def update_user_login(self, user_id):
        """Update user's last login time"""
        if not self.ensure_connected():
            raise ConnectionFailure("Database connection failed")
            
        from bson.objectid import ObjectId
        self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.datetime.now()}}
        )

    # Meeting operations
    def save_meeting(self, title, user_id, audio_file=None, transcript=None, summary=None, 
                    action_items=None, participants=None, duration=None):
        """Save a new meeting"""
        if not self.ensure_connected():
            raise ConnectionFailure("Database connection failed")
            
        meeting = {
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
        result = self.meetings.insert_one(meeting)
        return str(result.inserted_id)

    def update_meeting(self, meeting_id, **kwargs):
        """Update meeting fields"""
        if not self.ensure_connected():
            raise ConnectionFailure("Database connection failed")
            
        from bson.objectid import ObjectId
        kwargs["updated_at"] = datetime.datetime.now()
        self.meetings.update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": kwargs}
        )
        
    def get_meeting(self, meeting_id):
        """Get a meeting by ID"""
        if not self.ensure_connected():
            raise ConnectionFailure("Database connection failed")
            
        from bson.objectid import ObjectId
        return self.meetings.find_one({"_id": ObjectId(meeting_id)})
        
    def get_user_meetings(self, user_id):
        """Get all meetings for a user"""
        if not self.ensure_connected():
            raise ConnectionFailure("Database connection failed")
            
        return list(self.meetings.find({"user_id": user_id}).sort("created_at", -1))
        
    def delete_meeting(self, meeting_id):
        """Delete a meeting"""
        if not self.ensure_connected():
            raise ConnectionFailure("Database connection failed")
            
        from bson.objectid import ObjectId
        self.meetings.delete_one({"_id": ObjectId(meeting_id)})

# Create a singleton instance without auto-connecting
db = Database(auto_connect=False)

def get_all_meetings(user_id):
    """Get all meetings for a user"""
    return db.get_user_meetings(user_id)

def initialize_db():
    """Initialize the database connection"""
    success = db.ensure_connected()
    if not success:
        logging.warning("Could not connect to MongoDB, using mock database")
        from utils.mock_database import db as mock_db
        return mock_db
    return db

def save_meeting(meeting_data):
    """Save a meeting with the provided data"""
    if isinstance(meeting_data, dict):
        return db.save_meeting(
            title=meeting_data.get('title'),
            user_id=meeting_data.get('user_id'),
            audio_file=meeting_data.get('audio_file'),
            transcript=meeting_data.get('transcript'),
            summary=meeting_data.get('summary'),
            action_items=meeting_data.get('action_items'),
            participants=meeting_data.get('participants'),
            duration=meeting_data.get('duration')
        )
    else:
        # Assume it's a Meeting object
        return db.save_meeting(
            title=meeting_data.title,
            user_id=meeting_data.user_id,
            audio_file=meeting_data.audio_file,
            transcript=meeting_data.transcript,
            summary=meeting_data.summary,
            action_items=[item.to_dict() for item in meeting_data.action_items] if meeting_data.action_items else [],
            participants=meeting_data.participants,
            duration=meeting_data.duration
        )

def get_meeting_by_id(meeting_id):
    """Get a meeting by ID"""
    from models.meeting import Meeting
    meeting_data = db.get_meeting(meeting_id)
    if meeting_data:
        return Meeting.from_dict(meeting_data)
    return None

def delete_meeting(meeting_id):
    """Delete a meeting"""
    return db.delete_meeting(meeting_id)