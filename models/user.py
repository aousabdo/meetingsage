import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    username: str
    email: str
    password_hash: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    last_login: Optional[datetime.datetime] = None
    id: Optional[str] = None
    
    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "id": self.id
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls(
            username=data["username"],
            email=data["email"],
            password_hash=data["password_hash"],
            created_at=data.get("created_at", datetime.datetime.now()),
            updated_at=data.get("updated_at", datetime.datetime.now()),
            last_login=data.get("last_login")
        )
        
        if "_id" in data:
            user.id = str(data["_id"])
        elif "id" in data:
            user.id = data["id"]
            
        return user