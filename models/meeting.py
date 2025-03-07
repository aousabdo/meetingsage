import datetime
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ActionItem:
    description: str
    assigned_to: Optional[str] = None
    due_date: Optional[datetime.datetime] = None
    status: str = "pending"
    
    def to_dict(self):
        return {
            "description": self.description,
            "assigned_to": self.assigned_to,
            "due_date": self.due_date,
            "status": self.status
        }


@dataclass
class Meeting:
    title: str
    user_id: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    audio_file: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    action_items: List[ActionItem] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    duration: Optional[float] = None
    id: Optional[str] = None
    
    def to_dict(self):
        return {
            "title": self.title,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "audio_file": self.audio_file,
            "transcript": self.transcript,
            "summary": self.summary,
            "action_items": [item.to_dict() for item in self.action_items],
            "participants": self.participants,
            "duration": self.duration,
            "id": self.id
        }
    
    @classmethod
    def from_dict(cls, data):
        action_items = [
            ActionItem(**item) for item in data.get("action_items", [])
        ]
        
        meeting = cls(
            title=data["title"],
            user_id=data["user_id"],
            created_at=data.get("created_at", datetime.datetime.now()),
            updated_at=data.get("updated_at", datetime.datetime.now()),
            audio_file=data.get("audio_file"),
            transcript=data.get("transcript"),
            summary=data.get("summary"),
            action_items=action_items,
            participants=data.get("participants", []),
            duration=data.get("duration")
        )
        
        if "_id" in data:
            meeting.id = str(data["_id"])
        elif "id" in data:
            meeting.id = data["id"]
            
        return meeting