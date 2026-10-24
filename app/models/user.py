from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from flask_login import UserMixin


@dataclass
class User(UserMixin):
    id: str = ''
    email: str = ''
    password_hash: str = ''
    role: str = 'candidate'
    full_name: str = ''
    phone: str = ''
    location: str = ''
    skills: list[str] = field(default_factory=list)
    experience: str = ''
    summary: str = ''
    resume_filename: str = ''
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'User':
        return User(
            id=str(data.get('id') or data.get('_id') or ''),
            email=data.get('email', ''),
            password_hash=data.get('password_hash', ''),
            role=data.get('role', 'candidate'),
            full_name=data.get('full_name', ''),
            phone=data.get('phone', ''),
            location=data.get('location', ''),
            skills=data.get('skills', []),
            experience=data.get('experience', ''),
            summary=data.get('summary', ''),
            resume_filename=data.get('resume_filename', ''),
            created_at=data.get('created_at', datetime.now(timezone.utc).isoformat()),
        )

    def get_id(self):
        return str(self.id)
